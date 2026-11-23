"""Offline batch/publishing checks; no Spark, real credentials or AWS calls."""
import ast
import io
import json
from pathlib import Path
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import boto3
from botocore.response import StreamingBody
from botocore.stub import Stubber

with patch('dotenv.load_dotenv', return_value=False):
    from athena.create_tables import TABLE_SCHEMAS, create_table_input, validate_manifest, main as publish
    from athena.run_queries import wait_for_query
    from extract.setup_workflow import ensure_workflow

ROOT = Path(__file__).resolve().parents[2]


def manifest():
    return {"version": 1, "run_id": "wr_test", "workflow": "dev-flow", "reports": {
        name: {"location": f"s3://dev-bucket/gold/{name}/runs/wr_test/", "rows": 0,
               "columns": [{"name": col, "type": dtype} for col, dtype in columns]}
        for name, columns in TABLE_SCHEMAS.items()
    }}


def client(service):
    return boto3.client(service, region_name="ap-southeast-1",
                        aws_access_key_id="testing", aws_secret_access_key="testing")


class BatchTests(unittest.TestCase):
    def test_valid_empty_reports_are_publishable_but_never_the_parent_prefix(self):
        data = manifest()
        validate_manifest(data, "wr_test", "dev-flow", "dev-bucket")
        for table, columns in TABLE_SCHEMAS.items():
            result = create_table_input(table, columns, "dev-bucket", "wr_test")
            self.assertTrue(result["StorageDescriptor"]["Location"].endswith("/runs/wr_test/"))
            self.assertEqual(result["Parameters"]["coco_run_id"], "wr_test")

    def test_bad_schema_wrong_bucket_and_incomplete_batches_are_rejected(self):
        name = next(iter(TABLE_SCHEMAS))
        for change in ("schema", "bucket", "missing", "negative", "boolean"):
            data = manifest()
            if change == "schema":
                data["reports"][name]["columns"][0]["type"] = "string"
            elif change == "bucket":
                data["reports"][name]["location"] = "s3://unrelated-bucket/gold/"
            elif change == "missing":
                del data["reports"][name]
            else:
                data["reports"][name]["rows"] = -1 if change == "negative" else True
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_manifest(data, "wr_test", "dev-flow", "dev-bucket")

    def test_extract_writer_uses_unique_run_path_and_refuses_overwrite(self):
        tree = ast.parse((ROOT / "etl/extract/extract_postgres.py").read_text())
        function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "write_raw")

        class Writer:
            def mode(self, value):
                self.mode_value = value
                return self
            def format(self, value):
                return self
            def option(self, *args):
                return self
            def save(self, path):
                self.path = path

        paths = []
        for run in ("wr_first", "wr_second"):
            namespace = {"BUCKET": "dev-bucket", "RAW_PREFIX": "raw", "BATCH_ID": run}
            exec(compile(ast.Module(body=[function], type_ignores=[]), "<extract writer>", "exec"), namespace)
            writer = Writer()
            paths.append(namespace["write_raw"](SimpleNamespace(write=writer), "products"))
            self.assertEqual(writer.mode_value, "errorifexists")
            self.assertIn(f"/runs/{run}/", writer.path)
        self.assertNotEqual(paths[0], paths[1])

    def test_jdbc_connection_is_read_only_and_selects_only_allowlisted_columns(self):
        tree = ast.parse((ROOT / "etl/extract/extract_postgres.py").read_text())
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                     and node.name in {"read_postgres", "build_query"}]

        class Reader:
            def __init__(self):
                self.options = {}
            def format(self, value):
                return self
            def option(self, key, value):
                self.options[key] = value
                return self
            def load(self):
                return self

        reader = Reader()
        namespace = {"spark": SimpleNamespace(read=reader), "JDBC_URL": "jdbc:postgresql://test/db",
                     "SCHEMA": "marketplace", "TABLES": {"products": ["product_id", "price"]}}
        exec(compile(ast.Module(body=functions, type_ignores=[]), "<JDBC read contract>", "exec"), namespace)
        namespace["read_postgres"]("products", "dummy", "test-only-password")
        self.assertEqual(reader.options["readOnly"], "true")
        self.assertEqual(reader.options["readOnlyMode"], "always")
        self.assertEqual(reader.options["dbtable"],
                         '(SELECT "product_id", "price" FROM "marketplace"."products") AS src')

    def test_invalid_manifest_never_updates_catalog(self):
        glue, s3 = client("glue"), client("s3")
        settings = SimpleNamespace(athena_database="dev_analytics", bucket="dev-bucket",
                                   workflow="dev-flow", extract_job="extract", transform_job="transform")
        run = {"Status": "COMPLETED", "Statistics": {"TotalActions": 2, "SucceededActions": 2},
               "Graph": {"Nodes": [{"Type": "JOB", "Name": name,
                          "JobDetails": {"JobRuns": [{"Id": "jr_" + name, "JobRunState": "SUCCEEDED"}]}}
                         for name in ("extract", "transform")]}}
        body = json.dumps({"version": 1, "run_id": "wr_test", "reports": {}}).encode()
        with Stubber(glue) as gs, Stubber(s3) as ss:
            gs.add_response("get_database", {"Database": {"Name": "dev_analytics"}}, {"Name": "dev_analytics"})
            gs.add_response("get_workflow_run", {"Run": run}, {"Name": "dev-flow", "RunId": "wr_test", "IncludeGraph": True})
            ss.add_response("get_object", {"Body": StreamingBody(io.BytesIO(body), len(body))},
                            {"Bucket": "dev-bucket", "Key": "gold/_runs/wr_test.json"})
            with patch("athena.create_tables.AWSClients", return_value=SimpleNamespace(settings=settings, glue=glue, s3=s3)), \
                    patch("sys.argv", ["create_tables", "--run-id", "wr_test"]), self.assertRaises(ValueError):
                publish()
            gs.assert_no_pending_responses()
            ss.assert_no_pending_responses()

    def test_athena_timeout_does_not_cancel_or_repeat_query(self):
        athena = client("athena")
        with Stubber(athena) as stub, patch("athena.run_queries.time.monotonic", side_effect=[0, 2]):
            stub.add_response("get_query_execution", {"QueryExecution": {"Status": {"State": "RUNNING"}}},
                              {"QueryExecutionId": "query-1"})
            with self.assertRaises(TimeoutError):
                wait_for_query(SimpleNamespace(athena=athena), "query-1", timeout_seconds=1)
            stub.assert_no_pending_responses()

    def test_existing_workflow_is_limited_to_one_run(self):
        glue = client("glue")
        with Stubber(glue) as stub:
            stub.add_response("get_workflow", {"Workflow": {"Name": "dev-flow", "MaxConcurrentRuns": 2}}, {"Name": "dev-flow"})
            stub.add_response("update_workflow", {"Name": "dev-flow"}, {"Name": "dev-flow", "MaxConcurrentRuns": 1})
            ensure_workflow(glue, "dev-flow")
            stub.assert_no_pending_responses()


if __name__ == "__main__":
    unittest.main()

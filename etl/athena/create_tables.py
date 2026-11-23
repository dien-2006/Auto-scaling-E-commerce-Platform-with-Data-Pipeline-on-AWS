
import argparse
import json
import re

from common.aws_clients import AWSClients
from extract.run_workflow import validate_success


TABLE_SCHEMAS = {
    "product_category_summary": [
        ("category_id", "bigint"),
        ("category_name", "string"),
        ("product_count", "bigint"),
        ("total_stock", "bigint"),
        ("average_price", "double"),
    ],

    "shop_sales_summary": [
        ("shop_id", "bigint"),
        ("shop_name", "string"),
        ("completed_orders", "bigint"),
        ("total_items_sold", "bigint"),
        ("gross_sales", "decimal(20,2)"),
    ],

    "daily_sales_summary": [
        ("sales_date", "date"),
        ("completed_orders", "bigint"),
        ("gross_sales", "decimal(20,2)"),
    ],
}


def create_table_input(table, columns, bucket, run_id):
    return {
        "Name": table,
        "TableType": "EXTERNAL_TABLE",
        "Parameters": {
            "classification": "parquet",
            "EXTERNAL": "TRUE",
            "coco_run_id": run_id,
        },
        "StorageDescriptor": {
            "Columns": [
                {"Name": name, "Type": dtype}
                for name, dtype in columns
            ],
            "Location": (
                f"s3://{bucket}/gold/{table}/runs/{run_id}/"
            ),
            "InputFormat": (
                "org.apache.hadoop.hive.ql.io.parquet."
                "MapredParquetInputFormat"
            ),
            "OutputFormat": (
                "org.apache.hadoop.hive.ql.io.parquet."
                "MapredParquetOutputFormat"
            ),
            "SerdeInfo": {
                "SerializationLibrary": (
                    "org.apache.hadoop.hive.ql.io.parquet.serde."
                    "ParquetHiveSerDe"
                )
            },
        },
    }


def validate_manifest(manifest, run_id, workflow, bucket):
    if (not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", run_id) or
            manifest.get("version") != 1 or manifest.get("run_id") != run_id or
            manifest.get("workflow") != workflow or
            set(manifest.get("reports", {})) != set(TABLE_SCHEMAS)):
        raise ValueError("Invalid or incomplete Gold manifest")
    for table, columns in TABLE_SCHEMAS.items():
        report = manifest["reports"][table]
        expected = [{"name": name, "type": dtype} for name, dtype in columns]
        if (report.get("location") != f"s3://{bucket}/gold/{table}/runs/{run_id}/" or
                report.get("columns") != expected or
                type(report.get("rows")) is not int or report["rows"] < 0):
            raise ValueError(f"Unexpected Gold location/schema/count for {table}")


def publish_batch(aws, run_id):
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", run_id):
        raise ValueError("Invalid workflow run ID")
    database = aws.settings.athena_database
    bucket = aws.settings.bucket

    # Database must already exist through Terraform.
    aws.glue.get_database(Name=database)
    run = aws.glue.get_workflow_run(Name=aws.settings.workflow, RunId=run_id, IncludeGraph=True)["Run"]
    validate_success(run, [aws.settings.extract_job, aws.settings.transform_job])
    with aws.s3.get_object(Bucket=bucket, Key=f"gold/_runs/{run_id}.json")["Body"] as body:
        manifest = json.loads(body.read(1048576))
    validate_manifest(manifest, run_id, aws.settings.workflow, bucket)
    targets = []

    for table, columns in TABLE_SCHEMAS.items():
        table_input = create_table_input(
            table,
            columns,
            bucket,
            run_id,
        )

        try:
            existing = aws.glue.get_table(
                DatabaseName=database,
                Name=table,
            )["Table"]

        except aws.glue.exceptions.EntityNotFoundException:
            targets.append(("create_table", table_input))
        else:
            location = existing.get("StorageDescriptor", {}).get("Location", "")
            if not location.startswith(f"s3://{bucket}/gold/{table}/"):
                raise RuntimeError(f"Refusing to replace unrelated Catalog table: {database}.{table}")
            targets.append(("update_table", table_input))

    # Validate all three targets before changing the first table. Catalog table
    # updates are not atomic as a group; retry this same run ID after API failure.
    for operation, table_input in targets:
        getattr(aws.glue, operation)(DatabaseName=database, TableInput=table_input)
        print(f"Published {database}.{table_input['Name']} -> batch {run_id}")

    print("Glue Catalog tables are ready.")


def main():
    parser = argparse.ArgumentParser(description="Publish only a successfully completed ETL batch to Glue Catalog")
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", args.run_id):
        parser.error("Invalid workflow run ID")
    publish_batch(AWSClients(), args.run_id)


if __name__ == "__main__":
    main()

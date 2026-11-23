
import sys
import json
import time
import logging
import boto3
import re
from botocore.config import Config

from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("coco-extract")

args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME",
        "AWS_REGION",
        "JDBC_URL",
        "DB_SECRET_ARN",
        "S3_BUCKET",
        "RAW_PREFIX",
        "WORKFLOW_NAME",
        "WORKFLOW_RUN_ID",
    ],
)

REGION = args["AWS_REGION"]
JDBC_URL = args["JDBC_URL"]
SECRET_ARN = args["DB_SECRET_ARN"]
BUCKET = args["S3_BUCKET"]
RAW_PREFIX = args["RAW_PREFIX"].strip("/")
BATCH_ID = args["WORKFLOW_RUN_ID"]
if not re.fullmatch(r"[A-Za-z0-9_-]{1,128}", BATCH_ID):
    raise ValueError("Invalid workflow run ID")

SCHEMA = "marketplace"


# Analytical allowlist matching sql/marketplace_schema.sql.
# Add new tables/columns here only after their migrations exist in the source DB.
TABLES = {
    "shops": [
        "shop_id", "shop_name", "shop_slug",
        "shop_status", "created_at", "updated_at"
    ],
    "categories": [
        "category_id", "parent_category_id",
        "category_name", "category_slug",
        "is_active", "created_at"
    ],
    "products": [
        "product_id", "shop_id", "category_id",
        "sku", "product_name", "price",
        "is_active", "created_at", "updated_at"
    ],
    "product_images": [
        "product_image_id", "product_id",
        "image_key", "is_primary",
        "sort_order", "created_at"
    ],
    "inventory": [
        "product_id", "quantity", "updated_at"
    ],
    "orders": [
        "order_id", "total_amount",
        "payment_method", "created_at"
    ],
    "shop_orders": [
        "shop_order_id", "order_id", "shop_id",
        "order_status", "subtotal",
        "created_at", "updated_at"
    ],
    "order_items": [
        "order_item_id", "shop_order_id",
        "shop_id", "product_id", "product_name",
        "unit_price", "quantity"
    ],
}


sc = SparkContext.getOrCreate()
glue_context = GlueContext(sc)
spark = glue_context.spark_session

# Use UTC for consistent PostgreSQL timestamps.
spark.conf.set("spark.sql.session.timeZone", "UTC")

job = Job(glue_context)
job.init(args["JOB_NAME"], args)


def get_credentials():
    client = boto3.client(
        "secretsmanager",
        region_name=REGION,
        config=Config(retries={"mode": "standard", "total_max_attempts": 4},
                      connect_timeout=10, read_timeout=60),
    )

    response = client.get_secret_value(
        SecretId=SECRET_ARN
    )

    secret = json.loads(response["SecretString"])

    username = secret.get("username")
    password = secret.get("password")

    if not username or not password:
        raise ValueError("PostgreSQL secret is incomplete")

    return username, password


def build_query(table):
    columns = TABLES[table]

    selected = ", ".join(
        f'"{column}"' for column in columns
    )

    return (
        f'(SELECT {selected} '
        f'FROM "{SCHEMA}"."{table}") AS src'
    )


def read_postgres(table, username, password):
    return (
        spark.read
        .format("jdbc")
        .option("url", JDBC_URL)
        .option("dbtable", build_query(table))
        .option("user", username)
        .option("password", password)
        .option("driver", "org.postgresql.Driver")
        .option("fetchsize", "1000")
        .option("readOnly", "true")
        .option("readOnlyMode", "always")
        .option("sessionInitStatement", "SET default_transaction_read_only = on")
        .load()
    )


def write_raw(df, table):
    path = (
        f"s3://{BUCKET}/"
        f"{RAW_PREFIX}/{table}/runs/{BATCH_ID}/"
    )

    (
        df.write
        .mode("errorifexists")
        .format("parquet")
        .option("compression", "snappy")
        .save(path)
    )

    return path


def main():
    logger.info("Starting COCO full snapshot extract")

    username, password = get_credentials()
    tables = {}

    for table in TABLES:
        start = time.perf_counter()

        logger.info("Extracting: %s.%s", SCHEMA, table)

        df = read_postgres(
            table, username, password
        ).persist()
        try:
            rows = df.count()
            path = write_raw(df, table)
            tables[table] = {"location": path, "rows": rows}
        finally:
            df.unpersist()

        logger.info(
            "Extracted %s to %s in %.2fs",
            table,
            path,
            time.perf_counter() - start,
        )

    job.commit()
    s3 = boto3.client("s3", region_name=REGION)
    s3.put_object(
        Bucket=BUCKET, Key=f"{RAW_PREFIX}/_runs/{BATCH_ID}.json",
        Body=json.dumps({"version": 1, "run_id": BATCH_ID,
                         "workflow": args["WORKFLOW_NAME"], "tables": tables}).encode(),
        ContentType="application/json", ServerSideEncryption="AES256",
    )
    logger.info("All extracts succeeded")


if __name__ == "__main__":
    main()

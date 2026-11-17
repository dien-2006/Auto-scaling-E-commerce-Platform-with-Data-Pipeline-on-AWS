
import sys
import logging

from pyspark.context import SparkContext
from pyspark.sql import functions as F

from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("coco-transform")

args = getResolvedOptions(
    sys.argv,
    [
        "JOB_NAME",
        "S3_BUCKET",
        "RAW_PREFIX",
        "SILVER_PREFIX",
        "GOLD_PREFIX",
    ],
)

BUCKET = args["S3_BUCKET"]
RAW = args["RAW_PREFIX"].strip("/")
SILVER = args["SILVER_PREFIX"].strip("/")
GOLD = args["GOLD_PREFIX"].strip("/")

sc = SparkContext.getOrCreate()
glue_context = GlueContext(sc)
spark = glue_context.spark_session
spark.conf.set("spark.sql.session.timeZone", "UTC")

job = Job(glue_context)
job.init(args["JOB_NAME"], args)


# Match the extract allowlist and sql/marketplace_schema.sql.
PRIMARY_KEYS = {
    "shops": "shop_id",
    "categories": "category_id",
    "products": "product_id",
    "product_images": "product_image_id",
    "inventory": "product_id",
    "orders": "order_id",
    "shop_orders": "shop_order_id",
    "order_items": "order_item_id",
}


def s3_path(zone, table):
    return f"s3://{BUCKET}/{zone}/{table}/"


def write_parquet(df, path):
    (
        df.write
        .mode("overwrite")
        .format("parquet")
        .option("compression", "snappy")
        .save(path)
    )


# ==========================================
# 1. RAW -> SILVER
# ==========================================

def build_silver():
    silver_tables = {}

    for table, pk in PRIMARY_KEYS.items():
        logger.info("Cleaning table: %s", table)

        raw_path = s3_path(
            RAW, f"{table}/current"
        )

        df = spark.read.parquet(raw_path)

        if pk not in df.columns:
            raise ValueError(
                f"Missing primary key {pk} in {table}"
            )

        df = (
            df.dropna(subset=[pk])
            .dropDuplicates([pk])
        )

        silver_path = s3_path(SILVER, table)

        write_parquet(df, silver_path)

        silver_tables[table] = df

        logger.info("Silver completed: %s", table)

    return silver_tables


# ==========================================
# 2. GOLD: PRODUCT CATEGORY SUMMARY
# ==========================================

def build_product_category_summary(tables):
    products = (
        tables["products"]
        .filter(F.col("is_active") == True)
        .select(
            "product_id",
            "category_id",
            "price",
        )
    )

    categories = (
        tables["categories"]
        .select("category_id", "category_name")
    )

    inventory = (
        tables["inventory"]
        .select("product_id", "quantity")
    )

    joined = (
        products
        .join(inventory, "product_id", "left")
        .join(categories, "category_id", "left")
    )

    result = (
        joined
        .groupBy("category_id", "category_name")
        .agg(
            F.count("product_id")
             .cast("long")
             .alias("product_count"),

            F.sum(
                F.coalesce(
                    F.col("quantity"),
                    F.lit(0)
                )
            )
             .cast("long")
             .alias("total_stock"),

            F.avg("price")
             .cast("double")
             .alias("average_price"),
        )
    )

    write_parquet(
        result,
        s3_path(GOLD, "product_category_summary"),
    )

    logger.info("Gold product category summary completed")


# ==========================================
# 3. GOLD: SHOP SALES SUMMARY
# ==========================================

def build_shop_sales_summary(tables):
    shops = tables["shops"].select(
        "shop_id",
        "shop_name",
    )

    completed = (
        tables["shop_orders"]
        .filter(
            F.col("order_status") == "COMPLETED"
        )
        .select(
            "shop_order_id",
            "shop_id",
            "subtotal",
        )
    )

    # Financial aggregation:
    # one subtotal per shop_order_id
    sales = (
        completed
        .groupBy("shop_id")
        .agg(
            F.count("shop_order_id")
             .cast("long")
             .alias("completed_orders"),

            F.sum("subtotal")
             .cast("decimal(20,2)")
             .alias("gross_sales"),
        )
    )

    # Item quantity is aggregated separately to
    # avoid multiplying order subtotals in a join.
    sold_items = (
        tables["order_items"]
        .select("shop_order_id", "quantity")
        .join(
            completed.select("shop_order_id"),
            "shop_order_id",
            "inner",
        )
        .groupBy("shop_order_id")
        .agg(
            F.sum("quantity")
             .alias("items_in_order")
        )
    )

    quantities = (
        completed
        .select("shop_order_id", "shop_id")
        .join(sold_items, "shop_order_id", "left")
        .groupBy("shop_id")
        .agg(
            F.sum(
                F.coalesce(
                    F.col("items_in_order"),
                    F.lit(0),
                )
            )
             .cast("long")
             .alias("total_items_sold")
        )
    )

    result = (
        shops
        .join(sales, "shop_id", "left")
        .join(quantities, "shop_id", "left")
        .select(
            "shop_id",
            "shop_name",
            F.coalesce(
                F.col("completed_orders"),
                F.lit(0),
            ).cast("long").alias("completed_orders"),

            F.coalesce(
                F.col("total_items_sold"),
                F.lit(0),
            ).cast("long").alias("total_items_sold"),

            F.coalesce(
                F.col("gross_sales"),
                F.lit(0),
            ).cast("decimal(20,2)").alias("gross_sales"),
        )
    )

    write_parquet(
        result,
        s3_path(GOLD, "shop_sales_summary"),
    )

    logger.info("Gold shop sales summary completed")


# ==========================================
# 4. GOLD: DAILY SALES SUMMARY
# ==========================================

def build_daily_sales_summary(tables):
    orders = (
        tables["orders"]
        .select("order_id", "created_at")
    )

    completed = (
        tables["shop_orders"]
        .filter(
            F.col("order_status") == "COMPLETED"
        )
        .select(
            "order_id",
            "subtotal",
        )
    )

    joined = completed.join(
        orders,
        "order_id",
        "inner",
    )

    result = (
        joined
        .withColumn(
            "sales_date",
            F.to_date("created_at"),
        )
        .groupBy("sales_date")
        .agg(
            F.countDistinct("order_id")
             .cast("long")
             .alias("completed_orders"),

            F.sum("subtotal")
             .cast("decimal(20,2)")
             .alias("gross_sales"),
        )
    )

    write_parquet(
        result,
        s3_path(GOLD, "daily_sales_summary"),
    )

    logger.info("Gold daily sales summary completed")


# ==========================================
# 5. MAIN
# ==========================================

def main():
    logger.info("Starting COCO Transform")

    tables = build_silver()

    build_product_category_summary(tables)
    build_shop_sales_summary(tables)
    build_daily_sales_summary(tables)

    job.commit()

    logger.info("COCO Transform succeeded")


if __name__ == "__main__":
    main()

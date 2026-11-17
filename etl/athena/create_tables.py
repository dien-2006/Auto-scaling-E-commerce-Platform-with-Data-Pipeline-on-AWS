
from common.aws_clients import AWSClients


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


def create_table_input(table, columns, bucket):
    return {
        "Name": table,
        "TableType": "EXTERNAL_TABLE",
        "Parameters": {
            "classification": "parquet",
            "EXTERNAL": "TRUE",
        },
        "StorageDescriptor": {
            "Columns": [
                {"Name": name, "Type": dtype}
                for name, dtype in columns
            ],
            "Location": (
                f"s3://{bucket}/gold/{table}/"
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


def main():
    aws = AWSClients()

    database = aws.settings.athena_database
    bucket = aws.settings.bucket

    # Database must already exist through Terraform.
    aws.glue.get_database(Name=database)

    for table, columns in TABLE_SCHEMAS.items():
        table_input = create_table_input(
            table,
            columns,
            bucket,
        )

        try:
            aws.glue.get_table(
                DatabaseName=database,
                Name=table,
            )

        except aws.glue.exceptions.EntityNotFoundException:
            aws.glue.create_table(
                DatabaseName=database,
                TableInput=table_input,
            )

            print(f"Created: {database}.{table}")

        else:
            aws.glue.update_table(
                DatabaseName=database,
                TableInput=table_input,
            )

            print(f"Updated: {database}.{table}")

    print("Glue Catalog tables are ready.")


if __name__ == "__main__":
    main()

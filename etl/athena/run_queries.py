
import argparse
import time

from common.aws_clients import AWSClients


QUERIES = {
    "categories": """
        SELECT
            category_id,
            category_name,
            product_count,
            total_stock,
            average_price
        FROM product_category_summary
        ORDER BY product_count DESC
        LIMIT 20
    """,

    "shops": """
        SELECT
            shop_id,
            shop_name,
            completed_orders,
            total_items_sold,
            gross_sales
        FROM shop_sales_summary
        ORDER BY gross_sales DESC
        LIMIT 20
    """,

    "daily": """
        SELECT
            sales_date,
            completed_orders,
            gross_sales
        FROM daily_sales_summary
        ORDER BY sales_date DESC
        LIMIT 30
    """,
}


def execute_query(aws, sql):
    settings = aws.settings

    response = aws.athena.start_query_execution(
        QueryString=sql,
        QueryExecutionContext={
            "Database": settings.athena_database,
        },
        WorkGroup=settings.athena_workgroup,
    )

    return response["QueryExecutionId"]


def wait_for_query(aws, execution_id, timeout_seconds=600, poll_seconds=2):
    if timeout_seconds <= 0 or poll_seconds <= 0:
        raise ValueError("Query timeout and poll interval must be positive")
    deadline = time.monotonic() + timeout_seconds
    while True:
        response = aws.athena.get_query_execution(
            QueryExecutionId=execution_id
        )

        status = response["QueryExecution"]["Status"]
        state = status["State"]

        if state == "SUCCEEDED":
            return response["QueryExecution"]

        if state in ("FAILED", "CANCELLED"):
            reason = status.get(
                "StateChangeReason",
                "Unknown error",
            )
            raise RuntimeError(
                f"Athena {state}: {reason}"
            )

        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"Athena query {execution_id} still running; not cancelled automatically")
        time.sleep(min(poll_seconds, remaining))


def print_results(aws, execution_id):
    paginator = aws.athena.get_paginator(
        "get_query_results"
    )

    first_page = True

    for page in paginator.paginate(
        QueryExecutionId=execution_id
    ):
        rows = page["ResultSet"]["Rows"]

        # First row of first page is the header.
        if first_page:
            first_page = False

        for row in rows:
            values = [
                field.get("VarCharValue", "")
                for field in row["Data"]
            ]

            print(" | ".join(values))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout-seconds", type=int, default=600)

    parser.add_argument(
        "--report",
        choices=list(QUERIES),
        default="categories",
    )

    args = parser.parse_args()
    if args.timeout_seconds <= 0:
        parser.error("--timeout-seconds must be positive")

    aws = AWSClients()

    sql = QUERIES[args.report]

    execution_id = execute_query(
        aws, sql
    )

    print(f"Query ID: {execution_id}")

    result = wait_for_query(
        aws, execution_id, timeout_seconds=args.timeout_seconds,
    )
    print(f"Bytes scanned: {result.get('Statistics', {}).get('DataScannedInBytes', 0)}")

    print_results(
        aws, execution_id
    )


if __name__ == "__main__":
    main()

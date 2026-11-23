# Extract và Glue workflow

| File | Chạy ở đâu | Mục đích |
| --- | --- | --- |
| `extract_postgres.py` | AWS Glue Spark runtime | Đọc PostgreSQL, ghi full snapshot vào S3 Raw |
| `setup_workflow.py` | Máy quản trị cục bộ có boto3 | Tạo/cập nhật workflow và trigger |
| `run_workflow.py` | Máy quản trị cục bộ có boto3 | Khởi chạy và theo dõi extract → transform |

## Điều kiện

Hoàn thành [Terraform](../../terraform/README.md), [schema SQL](../../sql/README.md), cấu hình [ETL](../README.md) và [upload hai script](../orchestration/README.md). Glue extract cần connection/SG tới RDS, secret hợp lệ và quyền ghi prefix Raw.

Không chạy `python extract/extract_postgres.py` trực tiếp trên máy chỉ cài `etl/requirements.txt`: job dùng `awsglue`, Spark và các tham số job do Terraform/Glue cung cấp.

## Cấu hình và chạy thủ công

Từ **thư mục `etl/`**, các lệnh sau thao tác lên AWS thật:

```sh
python -m extract.setup_workflow
python -m extract.run_workflow --watch --timeout-seconds 7200
```

Lần đầu chỉ tạo một starting trigger ON_DEMAND; CONDITIONAL trigger chạy transform
sau khi extract thành công. Không tạo cả SCHEDULED và ON_DEMAND trong một workflow.
Nếu còn trigger lịch của setup cũ, chạy từ gốc repo:

```sh
bash scripts/aws/etl-dev.sh setup --replace-start-trigger
```

Chỉ metadata trigger đúng workflow/job được thay sau khi xác minh không có run
đang active. Không xóa workflow/job/data. Không có cờ này thì không tự thay trigger.

`--watch` xác nhận cả hai job thành công, không chỉ nhìn `COMPLETED` của workflow. Hết timeout của trình theo dõi không dừng job AWS. Không truyền `--watch` thì lệnh chỉ khởi chạy và in Run ID.

## Lịch tự động

```sh
python -m extract.setup_workflow --enable-schedule --replace-start-trigger
python -m extract.setup_workflow --disable-schedule --replace-start-trigger
```

Chạy từng lệnh khi cần, không truyền hai cờ cùng lúc. `GLUE_SCHEDULE` dùng UTC:
`cron(0 18 * * ? *)` tương ứng 01:00 sáng ngày hôm sau ở Việt Nam
(Asia/Ho_Chi_Minh). Lịch bật có thể chạy Glue có phí ngay cả khi đóng terminal.

## Kết quả mong đợi

Tám bảng được ghi vào `s3://ETL_BUCKET/raw/<table>/runs/<workflow-run-id>/`, kèm
marker `raw/_runs/<workflow-run-id>.json` khi đủ dữ liệu. Mỗi bảng là full snapshot,
không phải CDC hoặc snapshot giao dịch xuyên bảng. Không overwrite batch cũ. JDBC
dùng read-only; không tạo bảng/seed hoặc ghi PostgreSQL. Hai job phải chạy qua
workflow để nhận cùng WORKFLOW_RUN_ID. Xem [quy trình dev từ gốc repo](../README.md).

Lịch tự động chỉ tạo batch Extract/Transform mới; Catalog/Athena vẫn cần publish
tường minh batch thành công. Không coi bật schedule là tự cập nhật Athena/Grafana.

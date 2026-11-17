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

Lần cấu hình đầu tạo lịch ở trạng thái chưa bật. Nếu lịch đã được bật từ trước, chạy setup không có cờ giữ nguyên trạng thái. Conditional trigger chỉ chạy transform sau khi extract thành công.

`--watch` xác nhận cả hai job thành công, không chỉ nhìn `COMPLETED` của workflow. Hết timeout của trình theo dõi không dừng job AWS. Không truyền `--watch` thì lệnh chỉ khởi chạy và in Run ID.

## Lịch tự động

```sh
python -m extract.setup_workflow --enable-schedule
python -m extract.setup_workflow --disable-schedule
```

Chạy từng lệnh khi cần, không truyền hai cờ cùng lúc. `GLUE_SCHEDULE` dùng UTC; ví dụ `cron(0 1 * * ? *)` là 08:00 Asia/Saigon. Lịch bật có thể chạy Glue có phí ngay cả khi bạn đóng terminal.

## Kết quả mong đợi

Tám bảng trong allowlist hiện tại được ghi vào `s3://ETL_BUCKET/raw/<table>/current/`. Đây là full snapshot và overwrite prefix đang dùng; không phải incremental/CDC. Xem [transform](../transform/README.md) và [Athena](../athena/README.md) để kiểm tra đầu ra tiếp theo.

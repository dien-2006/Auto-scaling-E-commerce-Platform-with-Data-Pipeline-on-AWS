# Cấu hình và AWS client dùng chung

Đây là thư viện nội bộ, không chạy trực tiếp file `config.py` hoặc `aws_clients.py`.

- `get_settings()` đọc biến môi trường và `etl/.env`; không có hàm `load_settings()`.
- `AWSClients()` tự lấy settings, xác minh account qua STS, rồi tạo client S3/Glue/Athena. Khởi tạo class này gọi AWS thật.
- Dùng `aws.settings` để đọc cấu hình, `aws.identity` để đọc identity đã xác minh. Constructor không nhận đối số settings.

Xem [etl/.env.example](../.env.example) và [hướng dẫn ETL](../README.md) để chuẩn bị môi trường. Các thuộc tính Settings dùng trong code là `region`, `account_id`, `bucket`, `extract_job`, `transform_job`, `workflow`, `athena_database`, `athena_workgroup`, `schedule`; `profile` là tùy chọn.

Sau khi đã cấu hình credential và `.env`, từ **thư mục `etl/`** chạy kiểm tra chỉ đọc:

```sh
python check_aws.py
```

Lệnh xác minh account rồi kiểm tra bucket, hai Glue job, Athena workgroup và Catalog database. Nó không tạo tài nguyên, không chứng minh được JDBC tới RDS hoặc logic Spark đã chạy đúng. Nếu account không khớp `AWS_ACCOUNT_ID`, script dừng trước các thao tác khác.

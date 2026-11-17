# Upload script lên S3 cho Glue

Thư mục này có `deploy_scripts.py`. Điều kiện: đã apply Terraform của môi trường tương ứng, hai Glue job tồn tại, credential có quyền đọc định nghĩa job và upload object vào prefix script của bucket đúng môi trường.

Chuẩn bị Python và `.env` theo [hướng dẫn ETL](../README.md). Từ **thư mục `etl/`**:

```sh
python check_aws.py
python -m orchestration.deploy_scripts
```

Lệnh thứ hai thực sự ghi AWS: upload `extract/extract_postgres.py` và `transform/transform.py`. Đích upload được lấy từ `Command.ScriptLocation` của từng Glue job, đồng thời kiểm tra bucket đúng `.env` và key thuộc `scripts/`.

Terraform hiện cấu hình đích `scripts/extract.py` và `scripts/transform.py`. Không cần đổi tên file Python cục bộ. Việc upload có thể tạo phiên bản object mới do S3 bật versioning; không chạy trên prod với `.env` dev hoặc ngược lại.

Khi cả hai upload thành công, bước tiếp theo là [cấu hình và chạy workflow](../extract/README.md). Script upload không tự khởi chạy job.

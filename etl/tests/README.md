# Kiểm tra ETL offline

Cần Python >= 3.11 và các package trong `etl/requirements.txt`. Không cần Spark, Glue runtime, tài khoản AWS hoặc `.env` thật.

Từ **gốc repo**:

```sh
python3 -m venv etl/.venv
. etl/.venv/bin/activate
python -m pip install -r etl/requirements.txt
PYTHONPATH=etl python -m unittest discover -s etl/tests -v
```

Nếu venv đã tồn tại, kích hoạt và dùng lại thay vì tạo lại. Bộ kiểm tra dùng dummy credentials và `botocore.stub.Stubber`; việc import cấu hình được chặn nạp `.env` thật. Không có request AWS được gửi.

Nội dung kiểm tra:

- Bảng/cột extract và khóa transform có trong `sql/marketplace_schema.sql`.
- Account mismatch bị từ chối; `check_aws.py` dùng đúng settings/client API.
- Workflow chỉ thành công khi các action và cả hai job thành công.
- Chờ trigger tạo mới, cập nhật, kích hoạt/vô hiệu hóa; báo lỗi hoặc timeout rõ ràng.
- Timeout theo dõi workflow không gửi lệnh dừng AWS run.

Không dùng `etl/glue_test/` trong bộ kiểm tra này. Kết quả offline không chứng minh được JDBC, IAM hoặc tính đúng của Spark trên dữ liệu live.

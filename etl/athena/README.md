# Tạo bảng và chạy báo cáo Athena

Điều kiện: `.env` và credential đúng môi trường; Glue Catalog database và Athena workgroup do Terraform tạo đã tồn tại; pipeline đã ghi các bảng Gold lên S3. Identity cục bộ cần quyền Catalog/Athena và đọc/ghi các prefix S3 tương ứng.

Từ **thư mục `etl/`**:

```sh
python -m athena.create_tables
python -m athena.run_queries --report categories
python -m athena.run_queries --report shops
python -m athena.run_queries --report daily
```

`create_tables` tạo/cập nhật metadata của ba bảng Parquet trong Glue Catalog; không tạo database, không chạy transform và không tự sinh dữ liệu Gold. `run_queries` gửi query AWS thật và có thể phát sinh phí quét dữ liệu.

| Report | Bảng |
| --- | --- |
| `categories` | `product_category_summary` |
| `shops` | `shop_sales_summary` |
| `daily` | `daily_sales_summary` |

Result output, mã hóa và giới hạn quét lấy từ Athena workgroup Terraform; không cần truyền output bucket qua CLI. Mỗi query in Query ID, chờ hoàn tất và in kết quả.

Nếu báo thiếu bảng, kiểm tra `ATHENA_DATABASE` và chạy bước tạo bảng. Nếu không có dữ liệu hoặc sai schema, kiểm tra workflow/S3 Gold trước khi query lại. Nếu AccessDenied, kiểm tra quyền của credential đang chạy script; role của Glue job không tự cấp quyền cho máy quản trị.

Xem [ETL chung](../README.md) cho cấu hình và thứ tự chạy toàn pipeline.

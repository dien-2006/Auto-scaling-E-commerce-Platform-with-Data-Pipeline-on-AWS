# Tạo bảng và chạy báo cáo Athena

Điều kiện: `.env` và credential đúng môi trường; Glue Catalog database và Athena workgroup do Terraform tạo đã tồn tại; pipeline đã ghi các bảng Gold lên S3. Identity cục bộ cần quyền Catalog/Athena và đọc/ghi các prefix S3 tương ứng.

Từ **thư mục `etl/`**:

```sh
python -m athena.create_tables --run-id RUN_ID_THAT
python -m athena.run_queries --report categories
python -m athena.run_queries --report shops
python -m athena.run_queries --report daily
```

Thay RUN_ID_THAT bằng Workflow Run ID thành công. `create_tables` kiểm tra hai job
và marker/schema/path/count trước khi tạo/cập nhật metadata ba bảng Glue Catalog,
Location trỏ đúng batch. Không tạo database/RDS table hoặc dữ liệu demo.
`run_queries` có phí quét dữ liệu, timeout 600 giây và không tự hủy query khi timeout.

| Report | Bảng |
| --- | --- |
| `categories` | `product_category_summary` |
| `shops` | `shop_sales_summary` |
| `daily` | `daily_sales_summary` |

Result output, mã hóa và giới hạn quét lấy từ Athena workgroup Terraform; không cần truyền output bucket qua CLI. Mỗi query in Query ID, chờ hoàn tất và in kết quả.

Nếu báo thiếu bảng, kiểm tra `ATHENA_DATABASE` và chạy bước tạo bảng. Nếu không có dữ liệu hoặc sai schema, kiểm tra workflow/S3 Gold trước khi query lại. Nếu AccessDenied, kiểm tra quyền của credential đang chạy script; role của Glue job không tự cấp quyền cho máy quản trị.

Xem [ETL chung](../README.md) cho cấu hình và thứ tự chạy toàn pipeline.

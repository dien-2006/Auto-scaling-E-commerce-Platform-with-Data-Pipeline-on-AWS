# Transform Raw → Silver → Gold

`transform.py` chạy trong **AWS Glue Spark runtime**. Không chạy trực tiếp bằng Python cục bộ; `pyspark` và `awsglue` thuộc môi trường Glue.

Điều kiện: extract thành công với dữ liệu Raw đúng schema, job transform có quyền đọc Raw và ghi Silver/Gold, script mới nhất đã được [upload](../orchestration/README.md).

Từ **thư mục `etl/`**, chạy cả pipeline để bảo đảm thứ tự:

```sh
python -m extract.run_workflow --watch --timeout-seconds 7200
```

Không chạy transform đồng thời với một lần extract đang overwrite Raw.

## Đầu ra

- Silver: loại dòng thiếu khóa chính và loại trùng theo khóa của tám bảng hiện tại; ghi Parquet Snappy vào `silver/<table>/`.
- Gold `product_category_summary`: số sản phẩm, tồn kho, giá trung bình theo danh mục.
- Gold `shop_sales_summary`: đơn hàng con `COMPLETED`, lượng bán và tổng subtotal theo shop.
- Gold `daily_sales_summary`: số order có shop order hoàn tất và tổng subtotal theo ngày tạo order, theo UTC.

Ghi đầu ra hiện dùng overwrite. Silver/Gold không được publish thành một transaction nguyên tử chung; không coi báo cáo đọc giữa lúc job đang ghi là snapshot nhất quán.

Sau khi workflow xác nhận extract và transform đều thành công, chạy [tạo bảng/query Athena](../athena/README.md). Không cần thêm crawler để dùng ba bảng Gold đã định nghĩa trong code.

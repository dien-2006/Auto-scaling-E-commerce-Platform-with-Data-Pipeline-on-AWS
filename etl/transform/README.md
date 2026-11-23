# Transform Raw → Silver → Gold

`transform.py` chạy trong **AWS Glue Spark runtime**. Không chạy trực tiếp bằng Python cục bộ; `pyspark` và `awsglue` thuộc môi trường Glue.

Điều kiện: extract thành công với dữ liệu Raw đúng schema, job transform có quyền đọc Raw và ghi Silver/Gold, script mới nhất đã được [upload](../orchestration/README.md).

Từ **thư mục `etl/`**, chạy cả pipeline để bảo đảm thứ tự:

```sh
python -m extract.run_workflow --watch --timeout-seconds 7200
```

Chạy cả hai job qua workflow để nhận cùng WORKFLOW_RUN_ID. Không StartJobRun lẻ.

## Đầu ra

- Silver: kiểm tra count/null/duplicate PK, dừng khi sai, không tự bỏ dòng. Ghi vào
  `silver/<table>/runs/<workflow-run-id>/`.
- Gold `product_category_summary`: số sản phẩm, tồn kho, giá trung bình theo danh mục.
- Gold `shop_sales_summary`: đơn hàng con `COMPLETED`, lượng bán và tổng subtotal theo shop.
- Gold `daily_sales_summary`: số order có shop order hoàn tất và tổng subtotal theo ngày tạo order, theo UTC.

Gold ghi vào `gold/<report>/runs/<workflow-run-id>/`, không overwrite batch cũ.
Chỉ có marker Gold sau khi cả ba báo cáo hoàn tất; publisher kiểm tra marker và
workflow trước khi đổi Catalog. Ba cập nhật Catalog không atomic cùng nhau.

Sau khi workflow xác nhận extract và transform đều thành công, chạy [tạo bảng/query Athena](../athena/README.md). Không cần thêm crawler để dùng ba bảng Gold đã định nghĩa trong code.

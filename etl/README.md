# ETL PostgreSQL → S3 → Athena

Pipeline chính gồm:

```text
RDS PostgreSQL (schema marketplace)
    → Glue extract → raw/<table>/current/
    → Glue transform → silver/<table>/
                     → gold/product_category_summary/
                     → gold/shop_sales_summary/
                     → gold/daily_sales_summary/
    → Glue Catalog tables → Athena
```

`glue_test/` là phần thử nghiệm riêng, không thuộc các bước và bài kiểm tra bên dưới.

## Schema và dữ liệu

`sql/marketplace_schema.sql` là chuẩn hiện tại. Extract và transform cùng dùng tám bảng: `shops`, `categories`, `products`, `product_images`, `inventory`, `orders`, `shop_orders`, `order_items`.

Không yêu cầu các bảng lịch sử, coupon, review, payment hoặc hai cột `orders.discount_amount`, `orders.shipping_fee` chưa được khai báo trong schema này. Đây là thay đổi allowlist xử lý, không xóa bảng hoặc dữ liệu trên PostgreSQL/S3. Khi bổ sung migration, cần cập nhật cả extract, transform và kiểm tra schema.

RDS phải được khởi tạo schema và dữ liệu nguồn trước khi chạy job. Extract vẫn dùng full snapshot và overwrite các prefix hiện tại; lần sửa này không đổi sang CDC, không bổ sung hạ tầng, và không cung cấp snapshot nhất quán xuyên nhiều bảng/ghi dữ liệu theo giao dịch.

## Các hướng dẫn theo bước

- [Kiểm tra cấu hình và client dùng chung](common/README.md)
- [Upload script Glue](orchestration/README.md)
- [Extract và cấu hình/chạy workflow](extract/README.md)
- [Transform Silver/Gold](transform/README.md)
- [Tạo bảng và truy vấn Athena](athena/README.md)
- [Chạy kiểm tra offline](tests/README.md)

## Cấu hình cục bộ

Từ **gốc repo**:

```sh
python3 -m venv etl/.venv
. etl/.venv/bin/activate
python -m pip install -r etl/requirements.txt
```

Nếu chưa có `etl/.env`, sao chép `etl/.env.example` thành `etl/.env` rồi điền giá trị. Giữ nguyên file đang dùng nếu nó đã tồn tại. Việc tạo venv/cài package chỉ tác động môi trường Python cục bộ, có thể cần Internet để tải dependency.


Từ thư mục gốc repo, tạo môi trường Python 3.11+ rồi cài `etl/requirements.txt`. Thư viện `pyspark` và `awsglue` được cung cấp bởi AWS Glue runtime; các script quản trị cục bộ và bài kiểm tra không cần cài chúng.

Sao chép `etl/.env.example` thành `etl/.env`, điền account ID và tên tài nguyên đúng với môi trường Terraform. Không đưa credential hoặc `.env` lên Git. `AWS_PROFILE` là tùy chọn; boto3 có thể dùng credential tạm hoặc role theo cơ chế mặc định.

Đối với prod, đổi đồng bộ `COCO_ENV`, bucket, cả hai job, workflow, Catalog database và Athena workgroup sang prod; đừng chỉ đổi mỗi `COCO_ENV`. `get_settings()` đọc cùng một file `etl/.env` và các biến môi trường shell có sẵn được ưu tiên.

Các tên bucket, job và Catalog phải lấy theo Terraform của môi trường tương ứng. Script `check_aws` xác minh account trước khi kiểm tra tài nguyên; nó không tạo tài nguyên. Tất cả biến trong `.env.example` là cấu hình bắt buộc hiện tại, trừ `AWS_PROFILE`.

## Thứ tự chạy

Các lệnh sau thực sự gọi AWS; chỉ chạy khi đã cấu hình đúng account/environment và chủ động muốn thực hiện thao tác đó. Chạy từ thư mục `etl/`:

```sh
python check_aws.py
python -m orchestration.deploy_scripts
python -m extract.setup_workflow
python -m extract.run_workflow --watch --timeout-seconds 7200
python -m athena.create_tables
python -m athena.run_queries --report categories
```

`deploy_scripts` upload hai script đến đúng `ScriptLocation` lấy từ Glue job. `setup_workflow` tạo/cập nhật workflow và các trigger đã có trong thiết kế; lần đầu lịch tự động chưa được bật. Bật/tắt lịch bằng:

```sh
python -m extract.setup_workflow --enable-schedule
python -m extract.setup_workflow --disable-schedule
```

Không truyền đồng thời hai cờ. Nếu lịch đã được bật từ trước, chạy lại không có cờ sẽ giữ nguyên trạng thái lịch. Thời gian cron dùng UTC.

Trigger được chờ đến trạng thái ổn định và xác nhận đã kích hoạt/vô hiệu hóa; mỗi bước chờ có timeout 180 giây. Lỗi quyền hoặc API khác vẫn được báo lên.

`run_workflow --watch` chỉ báo thành công khi workflow `COMPLETED`, không có action thất bại/timeout/stopped/error, tất cả action thành công, và graph ghi nhận thành công của cả extract lẫn transform. Có timeout theo dõi; hết thời gian chờ không tự dừng job AWS đang chạy. Không truyền `--watch` thì lệnh chỉ gửi yêu cầu khởi chạy và in Run ID, chưa xác nhận kết quả.

## Kiểm tra không gọi AWS

Từ thư mục gốc repo, dùng Python đã cài `etl/requirements.txt`:

```sh
PYTHONPATH=etl python -m unittest discover -s etl/tests -v
```

Các bài kiểm tra dùng dummy credentials và `botocore.stub.Stubber`, không nạp `.env` thật và không gửi request AWS. Chúng kiểm tra giao diện client/settings, account mismatch, bảng/cột với SQL, workflow thất bại một phần, thiếu transform, trạng thái trigger chuyển tiếp và timeout.

Bài kiểm tra không thực thi Spark/Glue và không chứng minh được dữ liệu live, IAM hay kết nối RDS đang hoạt động. Sau khi kiểm tra cục bộ, cần chạy thử trong môi trường dev để xác nhận ba báo cáo Gold và Athena với dữ liệu thực tế.

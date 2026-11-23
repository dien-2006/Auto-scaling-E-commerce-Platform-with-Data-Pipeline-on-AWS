# ETL PostgreSQL → S3 → Athena

Pipeline chính gồm:

```text
RDS PostgreSQL (schema marketplace)
    → Glue extract → raw/<table>/runs/<workflow-run-id>/
    → Glue transform → silver/<table>/runs/<workflow-run-id>/
                     → gold/product_category_summary/runs/<workflow-run-id>/
                     → gold/shop_sales_summary/runs/<workflow-run-id>/
                     → gold/daily_sales_summary/runs/<workflow-run-id>/
    → Glue Catalog tables → Athena
```

`glue_test/` là phần thử nghiệm riêng, không thuộc các bước và bài kiểm tra bên dưới.

## Schema và dữ liệu

`sql/marketplace_schema.sql` là chuẩn hiện tại. Extract và transform cùng dùng tám bảng: `shops`, `categories`, `products`, `product_images`, `inventory`, `orders`, `shop_orders`, `order_items`.

Các bảng lịch sử, coupon, review, payment và cột discount/shipping đã có trong SQL
nhưng chưa thuộc allowlist phân tích này. Không lấy users/password_hash/email hoặc
địa chỉ người mua. Gross sales dùng subtotal, chưa phải doanh thu thuần sau giảm
giá/phí ship/refund. Không thay đổi schema/dữ liệu PostgreSQL hay file `sql/`.

RDS phải có schema và dữ liệu trước khi chạy. Extract là full snapshot từng bảng,
không phải CDC hoặc snapshot giao dịch đồng nhất xuyên tám bảng. JDBC dùng
readOnly/readOnlyMode=always; đây không thay thế quyền SELECT riêng ở DB. Job hiện
đọc secret RDS Terraform cung cấp; không tự tạo DB user hoặc cấp quyền PostgreSQL.

Batch dùng WORKFLOW_RUN_ID chung cho cả hai job và ghi `errorifexists`, không
overwrite batch cũ. Marker Raw chỉ có sau khi đủ tám bảng. Transform kiểm tra row
count/null/duplicate PK, từ chối dữ liệu sai thay vì bỏ dòng, rồi ghi marker Gold
khi đủ ba báo cáo. Batch lỗi có thể để lại prefix riêng nhưng không được publish.
Publisher kiểm tra workflow, marker, schema/path/count của cả ba báo cáo trước khi
đổi Catalog Location sang batch. Ba cập nhật Catalog không atomic; lỗi giữa chừng
thì chạy lại cùng Run ID. Không đọc báo cáo trong lúc publish. Không tự xóa batch
cũ; giữ nhiều batch sẽ tăng dung lượng S3.

## Quy trình dev từ gốc repo qua scripts/

Các lệnh dưới đây do chủ dự án tự chạy; agent chưa chạy test, job, AWS API hoặc SQL.
Không cần build Docker/web lại. Wrapper dùng uv, có thể tải dependency lần đầu.

```sh
bash -n scripts/aws/etl-dev.sh
bash -n scripts/aws/plan-etl-dev.sh
bash scripts/aws/etl-dev.sh test
terraform -chdir=terraform/environments/dev validate
terraform -chdir=terraform/environments/dev test -filter=tests/environment.tftest.hcl
bash scripts/aws/plan-etl-dev.sh
```

Review plan: không RDS change, EC2 update/replacement, delete hoặc tài nguyên không
liên quan. Đây là plan có target, không phải full reconcile. Sau review:

```sh
terraform -chdir=terraform/environments/dev apply etl-dev.tfplan
python3 scripts/aws/prepare-etl-dev.py
bash scripts/aws/etl-dev.sh check
bash scripts/aws/check-etl-iam.sh
bash scripts/aws/etl-dev.sh setup
bash scripts/aws/etl-dev.sh upload
bash scripts/aws/etl-dev.sh run --timeout-seconds 7200
```

Prepare lấy output `etl_config` sau apply, tạo `artifacts/deploy/dev/etl.env` không
có password/AWS keys và giữ nguyên etl/.env. File được wrapper chọn tường minh qua
COCO_ETL_ENV_FILE, ưu tiên hơn biến ETL trong shell; etl/.env mặc định vẫn có hành
vi cũ, shell được ưu tiên. Plan chỉ cập nhật Glue runtime args/TempDir và output
wiring cùng các dependencies cần thiết. Không chạy toàn bộ Terraform apply.

Check chỉ đọc tài nguyên, chưa chứng minh JDBC/IAM của Glue runtime hoạt động.
IAM Policy Autopilot chỉ sinh `artifacts/deploy/dev/etl-iam-baseline.json` từ source
và Terraform dev; không upload/apply policy. Baseline gồm cả quyền job và người
vận hành, phải review tách vai trò; IAM job hiện tại được giữ nguyên trong bản sửa.

Setup tạo/cập nhật workflow/trigger, giới hạn một run, tắt schedule. Upload từ chối
khi job đang active hoặc chưa giới hạn MaxConcurrentRuns=1. Không upload khi đang
chạy ETL. Hai job yêu cầu WORKFLOW_NAME/WORKFLOW_RUN_ID, không StartJobRun lẻ.

Glue chỉ cho một starting trigger/workflow. Setup mặc định chỉ tạo ON_DEMAND để
chạy thủ công, cùng một CONDITIONAL trigger cho transform. Bản setup cũ từng tạo
cả SCHEDULED và ON_DEMAND; nếu còn trigger lịch đã tạo dở, chuyển một lần bằng:

```sh
bash scripts/aws/etl-dev.sh setup --replace-start-trigger
```

Cờ này cho phép thay đúng starting trigger thuộc workflow/job dự kiến. Script từ
chối khi workflow đang RUNNING/STOPPING hoặc trigger thuộc workflow khác; tắt lịch,
kiểm tra lại run, xóa metadata trigger cũ, đợi xóa xong rồi tạo ON_DEMAND. Không xóa
workflow, job, bảng RDS hay dữ liệu S3. Không truyền cờ thì không tự xóa trigger.

Lưu Run ID thật (`wr_...`) được in ra. Hết timeout hoặc mất terminal không dừng job;
không khởi động batch mới chỉ vì chưa xem được kết quả. Dùng lại run cũ:

```sh
bash scripts/aws/etl-dev.sh run --run-id RUN_ID_THAT --timeout-seconds 7200
```

Khi cả extract và transform SUCCEEDED, thay RUN_ID_THAT bằng ID đó:

```sh
bash scripts/aws/etl-dev.sh publish --run-id RUN_ID_THAT
bash scripts/aws/etl-dev.sh report --report categories
bash scripts/aws/etl-dev.sh report --report shops
bash scripts/aws/etl-dev.sh report --report daily
```

Publish tạo/cập nhật ba bảng metadata Glue Catalog/Athena, KHÔNG phải bảng RDS.
Location chỉ trỏ một batch, không trỏ folder cha để tránh cộng trùng nhiều batch.
Không cần crawler. Query có timeout mặc định 600 giây, in Query ID/bytes scanned;
timeout local không tự hủy query AWS.

Nếu nguồn chưa đổi sau seed, tổng product_count là 297 và shop report có ba dòng.
Chưa có shop order COMPLETED thì doanh thu bằng 0, daily có thể rỗng; không tự tạo
đơn giả. Daily tính theo ngày TẠO order (UTC), không phải ngày hoàn tất.

Glue/S3/Athena có phí. Mỗi job dùng hai G.1X, max retries 0, timeout 30 phút/job;
Athena giới hạn quét 1 GiB/query. Chưa bật schedule hằng ngày. Schedule chỉ tạo
batch Raw/Silver/Gold; publish Catalog vẫn do chủ dự án gọi cho Run ID thành công,
không tự refresh Athena. Cấu hình dev là 01:00 sáng Việt Nam hằng ngày, tức
`cron(0 18 * * ? *)` theo UTC. Khi chủ động muốn bật:

```sh
bash scripts/aws/etl-dev.sh enable-schedule --replace-start-trigger
bash scripts/aws/etl-dev.sh disable-schedule --replace-start-trigger
```

Wrapper này dành cho dev. Các hướng dẫn SDK trực tiếp bên dưới dùng cấu hình riêng
cho prod, không trộn tài nguyên dev/prod.

## Các hướng dẫn theo bước

### Nghiệm thu một batch trước khi chuyển sang autoscaling

Từ gốc repo, chạy kiểm tra offline trước; chỉ tiếp tục nếu không có test fail:

```sh
bash scripts/aws/etl-dev.sh test
python3 -m unittest discover -s scripts/tests -p 'test_prepare_etl.py' -v
python3 -m unittest discover -s scripts/tests -p 'test_check_autoscaling.py' -v
```

Sau đó chủ dự án tự chạy các lệnh AWS:

```sh
bash scripts/aws/etl-dev.sh check
bash scripts/aws/etl-dev.sh setup --replace-start-trigger
bash scripts/aws/etl-dev.sh upload
bash scripts/aws/etl-dev.sh finish --timeout-seconds 7200
```

`setup --replace-start-trigger` chuyển starting trigger sang thủ công nếu trước đó
đã bật lịch; sẽ dừng nếu workflow đang chạy hoặc trigger thuộc tài nguyên khác.
`finish` lưu Run ID vào `artifacts/deploy/dev/etl-last-run.json`, chờ cả hai job,
kiểm tra manifest Gold, publish ba bảng Catalog rồi thực thi cả ba query Athena.
Chỉ dòng `ETL acceptance completed` mới xác nhận toàn bộ các bước này thành công.
Không sửa bảng hay dữ liệu RDS; có phí Glue/S3/Athena, có cập nhật Catalog metadata.

Nếu mất kết nối hoặc hết thời gian theo dõi, chạy lại `finish` để tiếp tục batch
đã lưu; không tự tạo job mới. Nếu batch được chạy bởi lệnh `run` cũ hoặc lịch:

```sh
bash scripts/aws/etl-dev.sh finish --run-id RUN_ID_THAT
```

Không chạy song song lệnh publish/report cho các batch khác khi nghiệm thu.
Query Athena bị timeout không bị hủy; chạy lại finish có thể tạo lại query báo cáo
và phát sinh phí quét thêm, nhưng không tự chạy lại Extract/Transform.
Batch thất bại phải đọc lỗi trước. Chỉ dùng `finish --new-run` sau khi đã sửa lỗi
và chủ động muốn tạo batch mới; không ghi đè/xóa các folder batch cũ.

Sau nghiệm thu, bật lại lịch 01:00 Việt Nam bằng lệnh enable-schedule đã nêu trên.
Nếu prepare-etl-dev.py từ chối output lịch cũ, cần tạo/review/apply **plan mới** bằng
scripts/aws/plan-etl-dev.sh rồi tạo lại cấu hình. Script sẽ giữ nguyên etl.env hiện hữu
khi output không đúng giờ. Lịch chạy Glue chưa tự publish Catalog; dùng finish với
Run ID của batch theo lịch khi cần cập nhật báo cáo Athena.

Sau khi có kết quả nghiệm thu, kiểm tra nền tảng worker:

```sh
python3 scripts/aws/check-autoscaling-dev.py
```

Lệnh cuối chỉ đọc AWS/TF output: kiểm tra ASG, discovery tags, launch template thực
sự được ASG tham chiếu, IMDSv2, bootstrap AWS CLI/ECR/provider ID và worker/AZ.
Không sửa EC2/IAM hay desired capacity. Đây là đầu vào bước cài Cluster Autoscaler,
không phải bằng chứng đã autoscale thành công.

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
python -m athena.create_tables --run-id RUN_ID_THAT
python -m athena.run_queries --report categories
```

`deploy_scripts` upload hai script đến đúng `ScriptLocation` lấy từ Glue job.
`setup_workflow` mặc định tạo ON_DEMAND và CONDITIONAL, không tạo đồng thời hai
starting trigger. Chuyển chế độ lịch cần cờ thay metadata trigger tường minh:

```sh
python -m extract.setup_workflow --enable-schedule --replace-start-trigger
python -m extract.setup_workflow --disable-schedule --replace-start-trigger
```

Không truyền enable/disable đồng thời. Để nguyên chế độ lịch hiện hữu, dùng lại
--enable-schedule; setup mặc định là chế độ thủ công, không tự chuyển/xóa trigger
nếu thiếu --replace-start-trigger. Cron dùng UTC. StartWorkflowRun dùng chế độ ON_DEMAND.

Trigger được chờ đến trạng thái ổn định và xác nhận đã kích hoạt/vô hiệu hóa; mỗi bước chờ có timeout 180 giây. Lỗi quyền hoặc API khác vẫn được báo lên.

`run_workflow --watch` chỉ báo thành công khi workflow `COMPLETED`, không có action thất bại/timeout/stopped/error, tất cả action thành công, và graph ghi nhận thành công của cả extract lẫn transform. Có timeout theo dõi; hết thời gian chờ không tự dừng job AWS đang chạy. Không truyền `--watch` thì lệnh chỉ gửi yêu cầu khởi chạy và in Run ID, chưa xác nhận kết quả.

## Kiểm tra không gọi AWS

Từ thư mục gốc repo, dùng Python đã cài `etl/requirements.txt`:

```sh
PYTHONPATH=etl python -m unittest discover -s etl/tests -v
```

Các bài kiểm tra dùng dummy credentials và `botocore.stub.Stubber`, không nạp `.env` thật và không gửi request AWS. Chúng kiểm tra giao diện client/settings, account mismatch, bảng/cột với SQL, workflow thất bại một phần, thiếu transform, trạng thái trigger chuyển tiếp và timeout.

Bài kiểm tra không thực thi Spark/Glue và không chứng minh được dữ liệu live, IAM hay kết nối RDS đang hoạt động. Sau khi kiểm tra cục bộ, cần chạy thử trong môi trường dev để xác nhận ba báo cáo Gold và Athena với dữ liệu thực tế.

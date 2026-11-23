# Xóa và dựng lại dev bằng một lệnh

Chỉ dành cho account `858525799322`, region `ap-southeast-1`, root Terraform
`terraform/environments/dev`, workspace `default`. Chạy từ WSL/local; không chạy
trong phiên EC2 sắp bị xóa. Các script này **chưa được chạy test hoặc xác minh
trên AWS trong lúc viết**. Chủ dự án tự chạy các bước dưới đây.

## Điều được phép xóa và tạo lại

Chủ dự án đã chọn **destroy, không backup**, và cho phép tự nhập schema/demo vào
**RDS mới do script tạo**. Script không chỉnh sửa file `sql/`; không chạy DROP/
TRUNCATE để ép nhập vào DB đang có dữ liệu. RDS cũ, tất cả version ảnh/data lake,
image ECR và dữ liệu CSI monitoring được xóa. Đây không phải tạm dừng EC2.

Không xóa source local, Terraform state/config, `.env`, `data health/`, hoặc cấu
hình/mật khẩu Grafana/SMTP local. Những thứ này là đầu vào để dựng mới, không phải
backup dữ liệu DB. **Đừng xóa thư mục repo hoặc artifacts/deploy/dev sau destroy.**
Đơn hàng/tài khoản/ảnh phát sinh trên AWS không có trong nguồn demo local sẽ mất.

## Chuẩn bị một lần trước khi destroy

Cần AWS CLI có credential còn hạn, Terraform, Python 3 trên Linux/WSL, Docker
(bật daemon khi up), kubectl, Helm 3, uv, PostgreSQL client `psql`, Session Manager
plugin. Port local **15432 phải trống khi up**: đóng tunnel RDS đang chạy trước.
Quyền operator cần đủ các thao tác của Terraform, SSM, Secrets Manager và dọn
bucket version/ECR/Glue/Athena/CSI volume. Script không tự cấp quyền IAM mới.

Đầu vào cần có:

- `.env` có các trường SMTP backend đã dùng với prepare-dev-release.py.
- `artifacts/deploy/dev/alertmanager.yaml` đã điền email/SMTP.
- `artifacts/deploy/dev/monitoring-secrets.json` khớp Alertmanager, có username/
  password Grafana và SMTP password. Nếu chưa có, chuẩn bị bằng script monitoring
  hiện có trước khi destroy; không gửi các file này lên chat/git.
- `sql/marketplace_schema.sql`, `sql/example_data.sql`, ảnh JPG trong
  `data health/ProductImages/` và `data health/logo/1.png`, `2.png`, `3.png`.

Chủ dự án chạy các kiểm tra offline (mock CLI/local code, không triển khai AWS):

```bash
python3 -m unittest discover -s scripts/tests -p 'test_dev_stack.py' -v
python3 -m unittest discover -s scripts/tests -p 'test_prepare_monitoring.py' -v
bash -n scripts/aws/dev-stack.sh scripts/db/init-rds-dev.sh
python3 -m py_compile scripts/aws/dev-stack.py scripts/aws/prepare-monitoring-dev.py etl/orchestration/complete_pipeline.py
```

Kiểm tra đầu vào, account và Docker, chưa ghi AWS hay chạy SQL:

```bash
bash scripts/aws/dev-stack.sh check
```

## Lệnh xóa toàn bộ dev do repo quản lý, không backup

```bash
bash scripts/aws/dev-stack.sh destroy --delete-data
```

Lệnh này kiểm tra đầu vào dựng lại, lập/kiểm tra plan destroy, tắt/xóa trigger và
workflow ETL riêng của dev, từ chối xóa khi job đang chạy, đình chỉ ASG rồi dừng
EC2 để ngăn web/CA ghi thêm trong quá trình dọn dữ liệu. Sau đó xóa mọi object
version/delete marker/multipart upload của đúng hai bucket, xóa manifest ECR,
workgroup Athena và named query, parameter SSM của dev, rồi apply plan destroy mới.
Volume CSI được kiểm tra đúng cluster/namespace và xóa khi đã detach sau terminate.
Không force-detach volume. RDS dev hiện đặt `skip_final_snapshot=true`, không tạo
snapshot cuối. Terraform thông thường vẫn giữ `force_destroy=false` cho S3/ECR/
Athena; chỉ lệnh destroy có `--delete-data` này thực hiện dọn dữ liệu rõ ràng.

Không phải lệnh quét/xóa mọi tài nguyên trong account. Snapshot/backup thủ công
cũ, log group dùng chung hoặc tài nguyên tạo ngoài repo không tự bị xóa. Key KMS
do Terraform quản lý đi vào thời gian chờ xóa (cấu hình hiện tại 30 ngày). Không
cam kết hóa đơn lập tức bằng 0; kiểm tra tài nguyên còn lại trên console sau đó.

Nếu lỗi, **không xóa Terraform state hoặc file tiến độ**. Sửa nguyên nhân rồi chạy
lại cùng lệnh destroy; các bước hoàn tất được bỏ qua. Khi script đã bắt đầu dừng
compute, web sẽ offline kể cả khi bước dọn dữ liệu sau đó chưa xong. Phải hoàn tất
destroy trước up; không dùng up để khôi phục một lần destroy đang dở.

## Một lệnh dựng lại khi cần demo

```bash
bash scripts/aws/dev-stack.sh up
```

Chỉ chạy từ state trống, hoặc tiếp tục đúng generation mà lệnh up này đang dựng.
Không dùng để sửa/nâng cấp một stack đang chạy. Lệnh sẽ:

1. Terraform init/plan/apply toàn bộ dev; chỉ chấp nhận create/no-op, dừng nếu có
   update/delete/replace bất ngờ.
2. Chờ cloud-init control plane, ít nhất hai worker Ready ở hai AZ và CoreDNS.
3. Lấy mật khẩu RDS mới qua Secrets Manager, mở tunnel riêng, nhập SQL nguồn trong
   một transaction có guard schema trống; không hỏi mật khẩu hoặc in credential.
4. Build/push cả hai image với tag mới, render lại ALB/CDN/RDS/Secret, tải lại ảnh
   local và triển khai web/metrics-server qua SSM, chờ từng command Success.
5. Render/cài CSI, Prometheus/Grafana/Alertmanager/dashboards với credential local,
   rồi cài Cluster Autoscaler. Không tự chạy demo worker-pressure hoặc k6 tải lớn.
6. Upload ETL scripts, chạy một batch extract/transform, publish Catalog và kiểm
   tra ba report Athena; sau thành công bật lịch 01:00 giờ Việt Nam (18:00 UTC).
7. Chạy k6 smoke rồi in URL web mới. ALB/CloudFront/EC2/RDS ID có thể đổi; các
   manifest/credential được render lại từ output mới, không dùng manifest cũ.

Lệnh up tạo tài nguyên có phí và chạy một batch Glue/Athena có phí. Một lệnh
không có nghĩa là xong ngay: giữ terminal/mạng và Docker hoạt động, dự trù hơn
một giờ; lần đầu có thể lâu hơn tùy AWS, build và ETL. Chưa có số đo thực tế.
Grafana vẫn private: mở lại hai phiên SSM/port-forward theo monitoring README;
script không mở Grafana ra Internet hoặc duy trì tunnel GUI sau khi kết thúc.

Tiến độ lưu riêng mode 600 trong `artifacts/deploy/dev/stack-lifecycle.json`.
Nếu terminal ngắt/timeout, chạy lại `up` để tiếp tục chờ đúng SSM command/ETL Run
ID. Nếu một SSM command đã Failed, đọc lỗi bằng get-command-invocation và sửa
nguyên nhân trước, rồi chủ dự án mới chạy:

```bash
bash scripts/aws/dev-stack.sh up --retry-failed
```

Flag này chỉ cho phép submit lại SSM task đã terminal Failed/TimedOut/Cancelled;
không bỏ qua task đang chạy. ETL dùng receipt riêng cho từng generation, tránh
nhầm Run ID của workflow cũ đã bị xóa. Retry không khôi phục dữ liệu đã destroy.

Tham chiếu hành vi RDS: [Deleting a DB instance](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_DeleteInstance.html).

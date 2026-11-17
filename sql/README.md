# Khởi tạo schema PostgreSQL cho ứng dụng và ETL

`marketplace_schema.sql` tạo schema `marketplace` và các bảng trong **database đã tồn tại**. Terraform tạo database `coco_marketplace`; chú thích về database Docker trong file SQL không phải cấu hình RDS.

Cần `psql`, endpoint RDS, username/password hợp lệ, và host có đường mạng/được RDS Security Group cho phép truy cập TCP 5432. RDS private không truy cập trực tiếp từ Internet. Ví dụ có thể chạy từ worker được quản trị qua SSM nếu đã có `psql` và quyền phù hợp.

Từ **gốc repo**, điền endpoint của đúng môi trường vào biến `RDS_HOST` trong shell. Sau đó:

```sh
psql "host=$RDS_HOST port=5432 dbname=coco_marketplace user=coco_admin sslmode=require" -W -v ON_ERROR_STOP=1 -f sql/marketplace_schema.sql
psql "host=$RDS_HOST port=5432 dbname=coco_marketplace user=coco_admin sslmode=require" -W -c '\dt marketplace.*'
```

`-W` hỏi mật khẩu tương tác; không đưa mật khẩu vào command hoặc Git. Nếu dùng user riêng, thay `coco_admin` bằng user được cấp quyền tạo schema/bảng.

Script có transaction và không xóa/tạo lại database. Nó không idempotent: nếu bảng đã tồn tại, `CREATE TABLE` sẽ lỗi và transaction rollback; không chạy lại trên database đang có dữ liệu để thay thế cho migration. File này không có dữ liệu seed. Cần dữ liệu demo phù hợp trước khi kiểm tra báo cáo [ETL](../etl/README.md).

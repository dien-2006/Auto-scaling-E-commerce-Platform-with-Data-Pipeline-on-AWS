# P6-02 — Sản phẩm Seller

Ngày 10/11/2026. Trang `/kenh-nguoi-ban/san-pham`, đi từ **Kênh người bán → Sản phẩm của tôi**. Guest đăng nhập với return URL nội bộ; tài khoản ACTIVE có shop APPROVED mới đọc và quản lý sản phẩm. USER/ADMIN đều chỉ thao tác shop của mình. PENDING/REJECTED/LOCKED trả 403; tài nguyên shop khác trả 404 khi người gọi có shop được duyệt.

## API đã triển khai

Prefix `/api/v1`, response `Cache-Control: no-store`. GET dùng READ ONLY; mutation yêu cầu JWT cookie, Origin và CSRF hiện có.

| Method/path | Dữ liệu | Kết quả |
| --- | --- | --- |
| GET /seller/products | q tối đa200, is_active?, page 1..2147483647, page_size 1..100 (mặc định24) | items, total, page, page_size |
| GET /seller/products/{id} | BIGINT dương | data: SellerProduct, kể cả sản phẩm/danh mục đã ẩn |
| POST /seller/products | sku,category_id,product_name,description?,price,initial_quantity | 201; product và inventory cùng transaction |
| PATCH /seller/products/{id} | sku?,category_id?,product_name?,description?,price? | 200; không shop_id/is_active/quantity/initial_quantity |
| POST /seller/products/{id}/hide | Không body | 200; ẩn lại no-op, không xóa lịch sử hoặc đổi tồn |

SKU trim1–64 ký tự, unique từng shop; tên trim1–200; mô tả nullable tối đa5.000. Giá là chuỗi Decimal không âm phù hợp NUMERIC(14,2), không nhận JSON float. Tồn ban đầu integer0..2147483647, không boolean. PATCH phải có trường hợp lệ; chỉ description được null. Extra fields bị từ chối. Category khi tạo/đổi phải nằm trong cây có toàn bộ tổ tiên active nối tới root. Sửa giá/tên/mô tả không tự bật lại hoặc đổi tồn.

SellerProduct mở rộng ProductDetail với is_active,created_at,updated_at. ID/giá là chuỗi, thời gian UTC; không PII hoặc storage key. Ảnh chỉ metadata hiện hữu và URL null tới P6-03. List lấy count/page và metadata ảnh theo tập, không N+1. Tìm parameterized, escape wildcard; sort created_at DESC/product_id DESC; trang quá cuối items rỗng.

## Giao dịch và frontend

WriteAccess giữ khóa user tới COMMIT. Service lấy shared category advisory lock `(731921,1)` trước shop rồi product, cùng thứ tự checkout. Shop/status kiểm dưới khóa; unique SKU là hàng rào cuối. Không commit từng phần hoặc lock trong bộ nhớ. Inventory/COMMIT lỗi rollback toàn bộ; PATCH/hide lỗi rollback thay đổi. SKU trùng409 SKU_EXISTS; category sai422 INVALID_CATEGORY; database lỗi503 đã làm sạch.

Next proxy cố định allowlist query/method/ID, body32KiB, lọc cookie và kiểm Origin/CSRF. Browser không gọi hostname Docker. Client validate/project đúng shop trước hiển thị. Có loading/empty/error/retry/disabled/confirm ẩn/submit guard; không lưu sản phẩm/token vào browser storage. Mất response sau COMMIT phải tải lại và kiểm SKU, không tự gửi mutation lại. Hết phiên hoặc đổi quyền bỏ dữ liệu riêng và kiểm lại session.

## Kiểm chứng và vận hành

- PASS287 backend tests:28 unit validation mới,9 PostgreSQL tests mới cùng regression; PostgreSQL16 tmpfs riêng marketplace_test và audit DB hiện hữu READ ONLY. Bao gồm SKU race hai app, ownership/Admin isolation, shop chưa duyệt/khóa, CSRF, category cha ẩn, rollback inventory/COMMIT, READ ONLY/không N+1. Ruff check/format/lock PASS.
- PASS48 frontend tests, lint/typecheck/production build;3 nhóm mới kiểm projection/query/proxy/CSRF và không tự retry write.
- PASS browser thật Next production→FastAPI→PostgreSQL16 riêng: create/edit/tồn ban đầu và sau sửa/SKU conflict/hide/filter/pagination/mất response sau COMMIT→read recovery/503 retry/expiry privacy. Đã xem desktop/mobile;320/390/768/1440 không overflow/JS errors.
- PASS Docker build/up riêng app `--no-deps`, healthy; live LAN guest401/query400/ID404/hostile403/csrf200/readiness200. Không fixtures/account/shop/product test trên DB thật. PostgreSQL ID/start/mount/config, root.env hash, volume/network giữ nguyên.

Tests nằm tại backend/tests/test_seller_products*.py và frontend/tests/seller-products.test.mjs. DB integration chỉ chạy với MARKETPLACE_TEST_DB_* trỏ PostgreSQL riêng marketplace_test; không dùng volume/DB nghiệp vụ. Browser harness/screenshots lượt này ở `D:/HealthBeauty/.p602-*`, `p602-products-390.png`, `p602-products-1440.png`, `p602-logo.png`; test processes/container đã dọn.

Giữ origin LAN khi cập nhật app:

```powershell
$env:MARKETPLACE_PUBLIC_ORIGIN='http://192.168.110.101:3001'
docker compose build backend frontend
docker compose up -d --no-deps --wait backend frontend
```

## Logo và giới hạn

Ảnh C:/Users/ADMIN/Downloads/loho.png được copy nguyên byte thành frontend/public/images/coco-logo.png. BrandLogo dùng Next Image chung cho header/footer/auth/Seller; favicon cùng asset. Giữ artwork/màu/chữ/nền trắng người dùng cung cấp; không tạo ảnh thay thế hoặc gán vào catalog/S3/DB. Logo được kiểm trên bảy route ở320/390/768/1440.

P6-03 ảnh S3, P6-04 chỉnh tồn và P6-05 đơn Seller chưa triển khai. Chưa có bật lại sản phẩm, phí vận chuyển thật, HTTPS/gateway/load hoặc kiểm điện thoại vật lý trong task này. Không schema/SQL/Compose/.env/dependencies/Terraform changes, không commit/push/AWS. Dừng sau logo và P6-02.

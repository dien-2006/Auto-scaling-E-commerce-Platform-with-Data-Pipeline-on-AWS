# P6-04 — Điều chỉnh tồn kho Seller

Trong `/kenh-nguoi-ban/san-pham`, chọn **Điều chỉnh tồn**, đọc số lượng hiện tại, chọn nhập thêm hoặc xuất bớt, nhập số lượng và kiểm tra thay đổi trước khi xác nhận. Danh sách sản phẩm cập nhật theo kết quả server. Giỏ hàng chưa giữ chỗ; checkout có thể làm thay đổi tồn kho trong lúc Seller mở form.

## API và transaction

- `GET /api/v1/seller/products/{id}/inventory`: envelope `data` gồm `product_id` chuỗi BIGINT, `quantity` nguyên và `updated_at` UTC. Response `no-store`.
- `POST /api/v1/seller/products/{id}/inventory/adjustments`: body chỉ `{ "delta": 2 }`, header `X-Expected-Quantity: 10` cùng cookie và CSRF/Origin hợp lệ. Delta nguyên khác 0 trong khoảng ±2147483647; expected từ 0 đến 2147483647, dạng số thập phân chuẩn. Header thiếu/trùng/sai và body không hợp lệ trả 422.
- Chỉ user ACTIVE sở hữu shop APPROVED được đọc/điều chỉnh. Sản phẩm shop khác trả 404 kể cả Admin; sản phẩm đã ẩn vẫn quản lý tồn mà không bật lại public. Thiếu bản ghi tồn trả 409 `INVENTORY_UNAVAILABLE`, không tự tạo tồn bằng 0.
- Khóa theo user → shared category → shop → product → inventory, tương thích checkout. Kiểm tra expected dưới row lock và conditional UPDATE theo expected, giữ khóa đến COMMIT. Stale trả 409 `STALE_INVENTORY`; kết quả âm/vượt INT_MAX trả 409 `INVALID_STOCK` trước phép cộng SQL. Repository không commit; lỗi COMMIT rollback toàn bộ.

Next proxy giới hạn route/method/query/ID/header/cookie/body, giữ bảo vệ CSRF và Origin. Browser chỉ gửi delta và expected; không cho overwrite quantity trong API sửa sản phẩm. Client kiểm tra identity, số nguyên và kết quả expected + delta trong phản hồi.

## Mất phản hồi và giới hạn

Không tự retry mutation. Sau stale/lỗi/mất phản hồi, form bỏ xác nhận cũ, khóa gửi và yêu cầu tải lại tồn kho rồi xác nhận điều chỉnh mới. Request có thể đã COMMIT trước khi mất phản hồi. API chưa có operation ID persist: expected quantity phát hiện stale thông thường, còn giới hạn ABA khi tồn quay về giá trị cũ; không bảo đảm exactly-once. Đóng trang/hết phiên có thể hủy chờ phản hồi nhưng không hủy transaction đã hoàn tất.

## Kiểm chứng

PASS backend full 344 tests trên PostgreSQL16 tmpfs `marketplace_test` riêng và audit metadata hiện hữu READ ONLY; gồm quyền, validation, stale/bounds/hidden, missing row, rollback, hai điều chỉnh đồng thời và điều chỉnh đua checkout. PASS57 frontend tests, lint/typecheck/production build, Ruff check/format và Docker build.

Browser thật Next → FastAPI → PostgreSQL test PASS nhập/xuất, chặn âm, stale, mất phản hồi sau COMMIT rồi đọc lại không gửi lặp, cập nhật danh sách, hết phiên xóa dữ liệu riêng và responsive 320/390/768/1440. Đã xem ảnh panel mobile. Harness kiểm tra tại `D:/HealthBeauty/.inventory-*`, ảnh `inventory-390.png` và `inventory-1440.png`; tài nguyên test riêng được dọn.

Không đổi schema, dữ liệu nghiệp vụ hoặc root `.env`; không provision S3/AWS. P6-03 còn chờ bucket thật. Chưa kiểm tra điện thoại vật lý/HTTPS/load; P6-05 đơn hàng Seller chưa triển khai.

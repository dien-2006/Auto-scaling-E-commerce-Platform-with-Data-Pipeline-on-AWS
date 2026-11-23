# UI-15 — Đăng ký bán hàng theo ảnh tham chiếu

Header marketplace có link **Kênh người bán** dẫn thẳng `/kenh-nguoi-ban`, thay hộp giới thiệu trung gian. Guest xem ngay form, không phải bấm thêm “Đến Kênh người bán” hoặc qua màn hình “Bán hàng cùng coco”. Nhấn Tiếp tục khi chưa đăng nhập chuyển login với returnTo; backend vẫn bắt buộc JWT/CSRF để tạo shop. Tài khoản đã có shop tiếp tục vào hồ sơ/dashboard hiện có, không form tạo shop thứ hai.

## Giao diện

Header gọn với logo COCO, search sản phẩm thật, thông báo hướng dẫn trạng thái hồ sơ, đăng nhập/đăng ký hoặc tài khoản hiện tại. Nền xanh nhạt, headline và minh họa cửa hàng 3D trái, form trắng bo góc phải, bốn bước hướng dẫn, bốn thông tin hỗ trợ phía dưới. Mobile xếp dọc, không tràn ngang. Đã đối chiếu ảnh desktop1672×941 và mobile390; không tuyên bố trùng pixel với ảnh vì nội dung phải phản ánh chức năng thật.

Hình `frontend/public/images/coco-seller-store.png` được tạo bằng skill imagegen cho UI này, nền trong suốt và đã copy vào repository. Chỉ là minh họa giao diện, không logo/sản phẩm/dữ liệu shop thật; không S3 upload hoặc ảnh catalog giả.

Các khác biệt nghiệp vụ cần thiết so với ảnh:

- Bước2 là **Gửi hồ sơ**, không màn hình cài đặt vận chuyển chưa có API/schema. Bốn bước chỉ mô tả quy trình, không bốn nút hoặc chức năng giả. Submit gửi PENDING thật; chỉ Admin duyệt theo quy trình đã chốt.
- SĐT chỉ đọc từ `auth/me` của tài khoản hiện tại, không xuất hiện trong payload shop và không giả lưu vào shops. Guest để trống; người dùng chưa có phone hiển thị chưa có số điện thoại. Không mở thêm sửa profile, lưu SĐT shop hoặc đổi schema trong task UI.
- Không ghi “tiếp cận triệu khách hàng” hoặc hứa thanh toán/giao vận chưa tích hợp. Copy nói kết nối khách hàng, bảo vệ thông tin, tạo gian hàng và COD mô phỏng theo hệ thống.
- Slug bắt buộc theo API vẫn được gửi: gợi ý từ tên tiếng Việt bỏ dấu, lowercase/alnum/gạch nối, tối đa160 ký tự. Mở **Tùy chỉnh đường dẫn shop** để sửa khi cần hoặc khi trùng slug. Server vẫn là nguồn kiểm tra và ràng buộc unique.

## Code và kết nối

`components/layout/site-header.tsx` thay dropdown seller bằng link thật:

```tsx
<Link href="/kenh-nguoi-ban" className="header-seller-link">
  <HeaderIcon name="seller" /> Kênh người bán
</Link>
```

- `components/seller/seller-header.tsx`, `seller-registration.tsx`, `seller-icon.tsx`: header/form/minh họa/icons và benefits. `site-frame.tsx` chọn header riêng cho route seller; auth và storefront khác giữ layout cũ.
- `components/seller/shop-dashboard.tsx`: guest/no-shop dùng form mới, có shop dùng dashboard cũ; giữ submit ref guard, ownership, status, error/uncertain/GET recovery, account-key và abort cũ.
- `lib/seller-registration.ts`: gợi ý slug có hỗ trợ Đ/đ và dấu tiếng Việt; không đoán ID hoặc tự thay slug sau đăng ký.
- `lib/seller-shop-client.ts` và Next proxy không đổi: Browser→Next same-origin→FastAPI POST/GET/PATCH `/api/v1/seller/shop`→PostgreSQL marketplace, backend trong Docker dùng postgres:5432. Không backend/schema/Compose/env/secret/dependency changes.

Guest không gửi shop POST và không lưu bản nháp/email/phone vào browser storage. Sau login nhập/gửi hồ sơ trong phiên đăng nhập; chỉ server201/200 hợp lệ mới báo thành công. Mất phản hồi sau commit yêu cầu đọc lại shop trước ghi tiếp. Backend vẫn bảo vệ một shop/owner, slug unique và PENDING, không có đường client tự duyệt.

## Kiểm thử và chạy

PASS45 frontend tests, lint/typecheck/production build. Thêm test gợi ý slug tiếng Việt/Đ/emoji/length/bounds; các test proxy/CSRF/ownership/projection/không retry vẫn PASS. Đã sửa dữ liệu test UTF-8 bị hỏng khi tạo qua shell rồi chạy lại45 PASS; source UI tiếng Việt và breadcrumbs được kiểm tra lại.

PASS Chrome E2E Next production→FastAPI→PostgreSQL16 tmpfs riêng: direct header link→form, search thật, guest Continue→login return không POST shop, form sau login có SĐT account readonly nhưng không gửi phone, tên→slug/create PENDING/single POST khi submit đôi, custom slug sau409, owner dashboard/patch, mất phản hồi sau real commit→GET khôi phục,503 không thành no-shop/retry, expiry bỏ dữ liệu riêng. Responsive320/390/768/1100/1440/1672 không tràn/JS errors; đã xem screenshots và chỉnh lại tỷ lệ card/nền. Test process/container đã dọn; không fixtures hoặc mutation trên DB thật.

Backend không thay đổi nên không lặp full250 tests của P6-01; E2E mới dùng backend thật. HTTPS/gateway/load chưa kiểm chứng. Docker frontend build/up --no-deps healthy; live link/form/header/asset/login return/responsive/API401/readiness200 PASS, guest không có shop POST. PostgreSQL ID/start/mount/config, volume/network và root .env hash giữ nguyên. Không sửa Terraform/AWS hoặc commit/push.

Mở http://localhost:3001, nhấn **Kênh người bán**, hoặc vào http://localhost:3001/kenh-nguoi-ban rồi Ctrl+F5. Chưa login thấy form; Tiếp tục dẫn đến đăng nhập. Tài khoản chưa có shop có thể gửi hồ sơ thật, tài khoản có shop thấy hồ sơ hiện tại. Sửa đường dẫn trùng qua Tùy chỉnh đường dẫn shop.

Từ root VS Code Terminal, khi cần chạy lại:

```powershell
docker compose build frontend
docker compose up -d --no-deps --wait frontend
```

Các hướng dẫn API/profile/permission P6-01 vẫn tại [seller-shop.md](seller-shop.md). UI-15 không tự triển khai P6-02 hoặc chức năng vận chuyển/Admin.

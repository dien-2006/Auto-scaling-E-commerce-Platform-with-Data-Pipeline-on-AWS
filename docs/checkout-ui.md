# P5-03 — Giao diện checkout COD

`/gio-hang` → **Tiến hành thanh toán** → `/thanh-toan`. Đây là giao diện dùng API thật, thay toàn bộ preview. Guest đăng nhập rồi quay lại checkout. P5-04 đã bổ sung liên kết Theo dõi đơn hàng trên xác nhận, dẫn đến `/tai-khoan/don-hang/{id}`; xem [đơn Buyer](buyer-orders.md). Không tự xóa intent chưa xác minh chỉ vì mở lịch sử.

## Kết nối và code

Browser gọi Next same-origin `/api/v1/{cart,addresses,orders/checkout}`, Next proxy chuyển cookie/CSRF/Origin đến FastAPI, backend kiểm quyền và transaction trên PostgreSQL `marketplace`. Trong Docker, Next dùng INTERNAL_API_URL backend, backend dùng postgres:5432; browser không biết hostname nội bộ hoặc JWT secret.

- `components/checkout/checkout-panel.tsx`: review địa chỉ/giỏ nhiều shop, COD, submit, recovery và xác nhận từ response server. Default address được chọn trước, nếu không có default thì chọn địa chỉ đầu tiên; vẫn có thể đổi. Chưa có địa chỉ thì liên kết tới quản lý địa chỉ và khóa nút đặt hàng. Cart rỗng/error được phân biệt.
- `lib/checkout-contract.ts`: strict request/intent projection, BIGINT strings, COD/quantity/price validation; kiểm tổng order bằng BigInt cents, unique shop/product/item và enum trạng thái. Response sai shape/tổng không được coi là thành công. `orderFrom` chỉ giữ fields contract; không truyền hash/token/extras vào UI.
- `lib/checkout-client.ts`: lấy CSRF mới trước mỗi lần POST, no-store/same-origin credentials/timeout; không tự retry POST hoặc đổi key. Chỉ200/201 cùng OrderDetail hợp lệ mới hiển thị xác nhận. Lỗi409/404/validation có thể review lại; lỗi mạng/503/response hỏng/phiên hết hạn giữ recovery, chưa tạo yêu cầu mới.
- `lib/auth-proxy.ts` và `app/api/v1/orders/checkout/route.ts`: duy nhất POST checkout, target cố định, validate UUID header, cookie allowlist/CSRF/Origin/no-store/redirect:error, chuyển Idempotency-Key nguyên vẹn. Body streaming limit riêng128KiB để hỗ trợ tối đa1000 dòng backend; các route auth/cart/address vẫn8KiB. Timeout proxy15s, client25s; timeout có thể xảy ra sau commit nên luôn giữ intent.

## Giữ nguyên yêu cầu qua retry/reload

Trước khi POST, UI tạo crypto.randomUUID một lần và ghi lại **intent tối thiểu** vào sessionStorage, theo user ID. Lưu version/user_id/key và payload gồm address_id (chỉ ID tham chiếu), payment_method COD, product IDs/quantity/expected prices. Không lưu JWT, recipient name/phone/địa chỉ nguyên văn/tên sản phẩm/OrderDetail. localStorage không được dùng.

```typescript
saveIntent(sessionStorage, pending);
const result = await submitCheckout(pending);
```

Lưu và đọc lại phải thành công trước khi gửi. Storage bị chặn/đầy thì không POST. Ref guard cùng loading/disable chặn nhấn gửi hai lần; backend unique buyer/key vẫn là bảo vệ chính.

Khi reload thấy intent, UI không coi dữ liệu browser là bằng chứng tạo đơn. Hiện recovery và nút **Gửi lại yêu cầu đặt hàng**. Lần gửi lại dùng đúng key/payload đã lưu; backend trả đơn cũ hoặc thực hiện yêu cầu ban đầu nếu chưa commit. Recovery không phụ thuộc giỏ/địa chỉ hiện tại còn tồn tại hoặc API đọc giỏ đang hoạt động.

Giá/tồn/giỏ đổi được server báo lỗi: người dùng chọn **Tải lại để xác nhận giỏ hàng**, xem dữ liệu mới rồi submit lại rõ ràng. Key vẫn giữ nguyên trong quá trình sửa yêu cầu này; không tự đổi key sau lỗi. Nếu một request cũ đã commit muộn, backend replay đơn đó và UI hiển thị nội dung server trả, không giả thông tin theo payload mới. Thiếu tồn/unavailable/tổng quá NUMERIC hoặc >1000 dòng thì khóa submit, liên kết về sửa giỏ.

Sau200/201 hợp lệ, UI hiện order ID, ngày, snapshot người nhận/địa chỉ/từng sản phẩm, trạng thái đơn shop và tổng tiền thực tế. COD mô phỏng không có trạng thái “đã thanh toán” giả; không thêm phí/discount/voucher. Header giỏ được yêu cầu tải lại API sau success.

Intent vẫn được giữ để reload có thể replay/xác minh lại. Chỉ sau khi đã nhận xác nhận server mới có nút **Bắt đầu lượt thanh toán mới** để xóa intent và tải giỏ hiện tại. Intent tách theo user: hết phiên/logout không làm mất mã yêu cầu đang chờ của user cũ; login lại đúng user phục hồi, user khác không được UI đọc intent đó. JSON storage hỏng thì chặn checkout, không âm thầm xóa/tạo key khác. Đóng tab/xóa sessionStorage làm mất khả năng phục hồi bằng key trong tab đó; task không hứa khôi phục intent đã bị xóa. Lịch sử đơn để đối chiếu sẽ làm ở P5-04.

## Chạy trong VS Code Terminal

Tại root, backend/PostgreSQL hiện hữu đang chạy:

```powershell
docker compose build frontend
docker compose up -d --no-deps --wait frontend
```

Mở http://localhost:3001/gio-hang hoặc http://localhost:3001/thanh-toan; Ctrl+F5. Auth local đã có khóa backend riêng từ FIX-AUTH-01; không đổi env hoặc restart database cho task UI. Schema/dữ liệu/volume/network không thay đổi.

Kiểm thử frontend với Node24:

```powershell
cd frontend
npm run lint
npm run typecheck
npm test
npm run build
```

Unit tests trong `tests/checkout.test.mjs` kiểm request/response arithmetic/projection, intent persistence/account isolation/storage failure, proxy key/method/source/body limits và client uncertain/repairable results. Kiểm thử browser task này dùng Next production→proxy→FastAPI→PostgreSQL16 tmpfs riêng; test data/đơn/tồn chỉ nằm trong database marketplace_test, không seed hoặc đặt đơn thử trên DB hiện hữu.

## Kiểm tra thủ công

1. Đăng nhập, tạo địa chỉ ở `/tai-khoan/dia-chi` nếu chưa có; thêm sản phẩm hợp lệ vào giỏ. Catalog chưa có hàng thì vẫn có empty state thật, không tự sinh sản phẩm.
2. Vào checkout, đổi địa chỉ, kiểm tra nhóm shop/giá/lượng/tổng tiền/COD. Không có địa chỉ hoặc sản phẩm không mua được thì nút disabled.
3. Bấm **Đặt hàng COD** sẽ tạo đơn và trừ tồn thật trong môi trường đang dùng. Chỉ kiểm thử tự động hoặc mô phỏng lỗi trên DB test riêng. Thành công phải có OrderDetail từ backend, không chỉ đổi giao diện.
4. Sau success, reload hiện recovery; gửi lại xác minh vẫn cùng order và không trừ tồn lần nữa. Chưa rõ kết quả thì không xóa storage/tạo key mới. Đổi giá/tồn cần xác nhận lại thông tin từ server.
5. Nếu hết phiên, đăng nhập lại bằng liên kết trên trang rồi quay lại checkout. Mã yêu cầu cũ vẫn giữ trong cùng tab/user.

Swagger http://localhost:8000/docs có Buyer checkout; [checkout-api.md](checkout-api.md) ghi transaction và cookie/CSRF. HTTPS gateway/load testing không thuộc task này; chưa triển khai lịch sử đơn, Seller hoặc Admin Dashboard.

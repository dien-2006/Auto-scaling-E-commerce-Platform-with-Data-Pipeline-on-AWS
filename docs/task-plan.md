# ENV-DOCKER-RELEASE | DONE — local runtime (19/11/2026)

Theo yêu cầu gộp1env/đóng gói2images/hướng dẫnGit: `.env` root là private duy nhất; merge nguyên giá trị Auth/S3/commerce/Brevo, giữ byte prefix rootcũ, không đổi mật khẩu/secret. Bốn file private cũ đã backup ngoài repo rồi bỏ; public root `.env.example` thống nhất, templates cũ ghi legacy. Backend env_file root; frontend/PostgreSQL chỉ nhận env explicit. Image tags coco-backend/coco-frontend:2026.11.18, exporter scripts/package-images.ps1, docs/docker-release.md và Git ignore artifacts/tsbuildinfo.

PASS Compose before/after app env equality, Settings preflight, Docker build2, up--no-deps2apphealthy, homepage/readiness/OTPtrue, PG/Redis IDs/start/mount preserved. Export2tar (77.2/101.8MiB linux/amd64), SHA256/manifest/config, docker load roundtrip PASS; exact current secret scan434Gitcandidates và decompressed layers PASS. Một private env active, no stagedfiles/commit/push. Không DB DDL/writes/backupdata/AWSupload. Root `.env` thay đổi có chủ đích theo yêu cầu gộp nhưng giá trị cũ giữ nguyên. Bàn giao artifacts/docker/2026.11.18, docs/docker-release.md.

# RESET-REFERENCE | DONE — local runtime (18/11/2026)

Trang quên mật khẩu theo ảnh mới: form giữa/nền xanh/minh họa khôi phục và bảo mật hai bên, header tài khoản và footer gọn. Sao chép nguyên ảnh tham chiếu, SVG chỉ hiển thị hai phần trang trí; không render form từ ảnh. Form thật chỉ email/Brevo, OTP inline + Gửi mã; xác minh đúng server mới hiện mật khẩu mới và nút Đặt lại mật khẩu. Giữ backend/proof/TTL/returnTo. PASS lint/typecheck/97 frontend tests/production+Docker build; browser fixture reset320/390/768/1672 gồm mã sai/đúng/expiry/resend/proof expiry; đăng ký/login regression PASS. Chỉ frontend up --no-deps healthy; live GET4viewport/header/footer/returnTo/nooverflow PASS; backend/PostgreSQL/Redis ID/start/mount/root .env giữ nguyên. Không ghi DB/gửi email thật.

# SOCIAL-ICONS | DONE — local runtime (18/11/2026)

Chỉ sửa giao diện theo lựa chọn người dùng: thêm SVG Apple, Google đa màu, căn đều icon/chữ/khung; màn hình 320px xếp icon trên nhãn. Giữ disabled và ghi chú chưa hỗ trợ, không triển khai OAuth. PASS lint/typecheck/build/Docker frontend build; browser 1440/390/320 và kiểm lại live: đủ icon, khung đều, không tràn. Frontend healthy; backend/PostgreSQL/Redis ID/start/mount và root .env giữ nguyên.

# OTP-STEPS-REGISTER-LOGIN | DONE — local runtime (18/11/2026)

Quên mật khẩu 3 bước: email → OTP → sau khi server xác minh đúng mới hiện mật khẩu mới. Cấp proof 256 bit/300 giây/một lần/đúng mục đích; `/otp-verify` không nhận mật khẩu, `/password-reset` cần proof và kiểm lại ACTIVE/email/credential. Đăng ký giống mẫu hai cột, minh họa cũ bên trái, inline OTP/Gửi mã, họ tên/mật khẩu/xác nhận và success; gửi OTP chỉ cần email. Sửa icon đè chữ bằng SVG field riêng/CSS có scope. Căn giữa chữ Đăng nhập trong nút theo cả hai chiều.

PASS 544 backend full; 25 OTP targeted bản cuối; 97 frontend/lint/typecheck/Ruff/format/build/Docker hai image. Browser fixtures 390/1440: đăng ký/mã sai/đúng, password reset bị ẩn trước proof, bước hoàn tất riêng, expiry/resend/proof expiry/no-auto-send, nút login centered; đã xem ảnh. Triển khai hai app --no-deps healthy. Live GET 3 trang ở 2 viewport PASS, live OpenAPI proof-required và Origin/CSRF guard PASS. Cấu hình OTP đang bật/email configured, giữ secret của người dùng. PostgreSQL/Redis ID/start/mount/root .env giữ nguyên; READ ONLY 25 bảng/0 auth_security. Không gửi mail hay đổi mật khẩu user thật trong kiểm thử. Nội dung trạng thái chuẩn bị/chưa enable bên dưới là lịch sử trước lần cập nhật này.

# OTP-BREVO | IN_PROGRESS — code hoàn tất, chờ cấu hình gửi thật (18/11/2026)

Yêu cầu mới thay thế phương án OTP email/SMS bên dưới: chỉ đăng ký bằng email có xác nhận OTP và quên mật khẩu qua email; dùng thử Brevo; không thêm bảng/không đổi schema. Đã chuyển proof/rate/attempts sang Redis dùng chung, giữ mã 6 số/60 giây/5 lần thử; bỏ chọn SMS và đăng nhập bằng SĐT khỏi luồng. Đề xuất SQL OTP cũ đã rút lại, không còn DDL. Giữ nguyên 25 bảng, email NOT NULL. Đã chuẩn bị Brevo SMTP STARTTLS, `.env.otp` tắt OTP, template và overlay Redis local. Hướng dẫn: `docs/otp-setup.md`.

PASS 538 backend toàn bộ (2 cảnh báo Pydantic hiện hữu), 21 kiểm thử OTP trên bản cuối với PostgreSQL/Redis riêng (519 test khác deselected), 97 frontend, Ruff check/format, lint/typecheck, production build và Docker build hai ứng dụng, uv lock check, Compose overlay validation. Browser fixture 390/1440: đăng ký email/mã sai/60 giây/không lưu mật khẩu, hết hạn/gửi lại/đổi mật khẩu, link quên mật khẩu và email login. READ ONLY database thật: 25 bảng marketplace, 0 auth_security, email NOT NULL; container ID/start/mount/root .env không đổi, cả ba service healthy. Chưa gửi Brevo thật, chưa khởi chạy Redis runtime/chưa enable OTP/chưa cập nhật app đang chạy. Còn điền sender/SMTP login/SMTP key và kích hoạt theo hướng dẫn; không cần SQL.

# OTP-AUTH | IN_PROGRESS — code và hướng dẫn sẵn sàng (18/11/2026)

Theo yêu cầu mới: đăng ký email/SMS phải xác minh OTP; quên mật khẩu qua OTP; hạn mã60giây, resend60giây, tốiđa5lần thử. Đã chuẩn bị API/UI/SMTP+SES/SNS/privateconfigdisabled/SQLproposal. PASS534backendfull trước bổsungreadiness,16OTPtests kiểm lại bảncuối,97frontend/lint/typecheck/build/Docker2images/UVlockcheck; browserfixtureemail/SMS/reset/expiry/resend/phone-onlylogin. CHƯA cấu hình provider thật, CHƯA áp SQL auth_security2tables+users.emailnullable hoặc enableOTP/deployappruntime. Marketplace vẫn25bảng hiện tại; tổngDB sẽtăng2bảng nếuSQLđượcduyệt. Hướngdẫn docs/otp-setup.md. Không đánh dấuDONE cho chức năng gửi thật.

# CART-SELECTION-WALLET | DONE (17/11/2026)

BỏXemchitiếtthẻsp;checkboxgiỏ/checkoutselected/giữphầnchưamua;lưumãlocaltheoaccount+dropdowncheckout. PASS519backend+3legacy/96frontend/lint/typecheck/build/browser390+1440. Khôngschema/DBwrites.

# DIRECT-BUY | DONE (17/11/2026)

Mua ngay1sảnphẩm/qty,giữgiỏkhôngthayđổi,chungcheckoutvalidation/idempotency;legacycouponquoteđúngscope. PASS516backend+4legacy/95frontend/lint/typecheck/build/browserselection/addressback/noCartWrites. KhôngDDL. Xemdocs/direct-buy.md.

# BUY-NOW | DONE (17/11/2026)

Mua ngay cạnhThêmgiỏ→thêm sốlượngđangchọn→mởcheckoutgiỏhiệntại. PASSlint/typecheck/build/browser success/failure/self/Admin/responsive,frontendhealthy.

# CHECKOUT-ADDRESS-STOCK-FIX | DONE (17/11/2026)

Quaylạiđịachỉvềcheckout,UUIDan toàndùngđượcHTTPIP,legacymappingkhôngđổi25bảng. PASS512backend+3legacycheckout/cart/93frontend/lint/typecheck/build/Ruff/HTTPbrowserlink. Thêmgiỏkhôngtrừtồn;đặtthànhcôngmớitrừ/kiểmtrakhóa.

# SELLER-ORDER-DETAIL-FIX | DONE (17/11/2026)

SửaORMđọccộtchưaápởchi tiết đơnbán, hiệntênngườimua/ngườinhận/phone/address/items. PASS512backend(2warnings)/92frontend/lint/typecheck/build/5đơnthậtreadonly/browser390+1440. KhôngDDL/DBwrites.

# AUTH-NOTICES | DONE (17/11/2026)

Thêm thôngbáorõthànhcông/thấtbại/validation/pending/network/timeout;giữunknownresultkhimấtresponse,khôngautoretry. PASS91tests/lint/typecheck/build/8mobilefixtureoutcomes+empty. ĐồngbộoriginIPmới từ.env,2apphealthy,DBgiữnguyên.

# HOME-CARDS-OFFERS | DONE (17/11/2026)

Bỏ chú thích, tên2dòng/giácùnghàng;Ưuđãihiện6mãtừFlashSale thật. PASS lint/typecheck/build/browser390+1440,frontendhealthy,DBgiữnguyên.

# HOME-PRODUCTS | DONE (17/11/2026)

Hiển thị12sảnphẩm ởôbánchạy; ưu tiênxếphạngCOMPLETED, fallbacknewestghi rõkhi chưa códữliệu. PASS511backend/lint/typecheck/build/Ruff/browser390+1440. Khôngđổi25bảng.

# FLASH-CLEAN | DONE (17/11/2026)

Bỏ2dòng dưới thẻ Deal, giữđồnghồchung. PASS lint/typecheck/build/browser/Dockerfrontendhealthy.

# FLASH-30 | DONE (17/11/2026)

Đổi bộlọc/API/UI/view sangdưới30%, bỏnhãncạnhFLASHSALE;view180sảnphẩm/API100. PASSlint/typecheck/build/Ruff/browsermobile. Khôngsửacấu trúc25bảng.

# FLASH-STYLE | DONE (17/11/2026)

Giao diện theoảnh, lọcgiảm0–dưới20% server/UI, đồnghồ hạnthật. PASSlint/typecheck/build/Ruff/browserfixture390/1440;live0itemsđúngdo296viewrowsđều100%. KhôngđổiDB/coupon/view.

# DEAL-CARDS | DONE (17/11/2026)

Ảnh/rail/nút xem tiếp đã lên web, PASS390/1440; badge/clock fixture PASS. Đã được phép và áp view theo backend/migrations/proposals/20261117_deal_view.sql; API và browser xác nhận badge/clock dữ liệu thật. Không sửa25bảng.

# DEAL-VIEW | DONE (17/11/2026)

Đã triển khai API/UI:12 sản phẩm; lint/typecheck/build và browser mobile PASS. Backend phát hành riêng2file tương thích runtime, không áp checkout migration.

# Kế hoạch Marketplace

- [ ] **CHECKOUT-OPTIONS — Mã shop/COCO, vận chuyển và thanh toán** | IN_PROGRESS, code sẵn sàng (15/11/2026). Theo chốt mới:1mã/shop+COCOGOODS+COCOSHIPPING, cướcCOCO25k/40k/60k mỗi shop. Chuẩn bịAPI/UI/SQL2cột+constraints/index vàcommerceconfigdisabled; PASS510backend/87frontend/build/E2Eoptions+journey4widths. Chưa áp schema nghiệp vụ hoặc nạp app mới; cần phép chủ DB theo AGENT.md. Chuyển khoản chờ thông tin/đối soát; MoMo/VNPay disabled chưa tích hợp. Xem docs/checkout-options-proposal.md.

- [x] **SELLER-PURCHASES-ENTRY — Chủ shop xem đơn mua cá nhân** | DONE (15/11/2026). ThêmĐơnmua ởSellerHeader vàlối quayvềĐơnmuatrangĐơnbán. BackendgiữownershipUSERcóshop. PASS502backend (2warningPydantic)/E2Eownerpersonalorders4widths/lint/typecheck/build/frontendhealthy;PG/root.env/volume/networkgiữnguyên. Phânbiệtđơnmua củauser vàđơnbán kháchđặtởshop.

- [x] **CHECKOUT-AUTO-RESOLVE — Bỏ màn hình yêu cầu gửi lại đơn** | DONE (15/11/2026). GETbuyer/Idempotency-Key tựkiểmtraintentcũ; đãcóđơn xóaintent/mởgiỏmới, chưa có giữUUID/mởform. KhôngtựPOST; lỗimạnghiểnthịthửlạigọn. PASS499backend/86frontend/lint/typecheck/build/E2E4widths/screenshot390,2apphealthy,PG/root.env/volume/networkgiữnguyên.

- [x] **S3-PREFIX-02 — Đường dẫn ProductImages mới** | DONE (15/11/2026). Bổ sungdeliveryreadonly ProductImages/{3shop}/{product}/{product}_{index}.jpg, giữbốtụccũ/finalizevalidation. PASS498backend/Ruff/build/backendhealthy;2391/2391keysđượchỗtrợ,HEAD3shop200,catalog24/24URLs,GET3ảnh200,browser390ảnhload. Khôngkiểmtoànbộobjects; khôngsửaDB/S3/root.env,PG/volume/networkgiữnguyên.

- [x] **BUYER-MULTI-ORDER — Đặt đơn tiếp khi đơn trước chờ xác nhận** | DONE (15/11/2026). Xóa intent khi tạo đơn/replay thành công, giữ khi mất response; regression đặt sản phẩm khác khi đơn trướcPENDING và browser lượt mua mớiPASS.
- [x] **BUYER-COUPON — Áp mã giảm giá khi checkout** | DONE code/UI (15/11/2026). Quote/checkout1coupon, global/shopeligible/minimum/no shipping,1lượt mỗi khách, usedcount/usage atomic/idempotent, hoàn khi hủy toàn bộ/không hoàn2lần, Decimal/expecteddiscount. PASSconcurrency lượt cuối khácshop/hủy2shop/commitrollback/historyUI; live chưa có coupon còn hiệu lực, không seed mã thật. Chưa có UI phát hành/quản lý mã.
- [x] **BUYER-REVIEWS — Đánh giá sản phẩm đã mua** | DONE (15/11/2026). USER ACTIVE/owner/COMPLETED,1review/orderitem,1–5sao/comment≤2000; publiccount/avg/pagination/visibility/privacy, formđơn mua vàproductpage. PASS487backend/85frontend/lint/typecheck/build/E2E4widths,2apphealthy;PG/root.env/volume/network giữ nguyên. Chi tiết docs/buyer-coupons-reviews.md.

- [x] **S3-DISPLAY-01 — Ảnh đã upload chưa hiển thị** | DONE sửa delivery (15/11/2026). Hỗ trợ read-only ba prefix cũ từ DB, folder/filename cùng product ID/JPG, ký GET900s trực tiếp S3, không qua CDN chỉ phục vụ product-images/. Upload/finalize giữ nguyên kiểm tra. PASS473 backendtests/Ruff/format/build/backendhealthy;2391keys khớp,API24/24URLs,GETảnh200, browser390 cóảnhS3 tải được. Không kiểm toàn bộ2391objects hoặc upload/CORS/PUT; P6-03 chưa tự DONE. DB/PG/root.env/volume/network giữ nguyên.

- [x] **AUTH-ARGON2-KEEP — Giữ argon2-cffi** | DONE (15/11/2026). Theo yêu cầu người dùng, gỡ hỗ trợ bcrypt vừa thử, khôi phục verifier/rehash Argon2 và dependency lock. PASS 460 backend tests trên PostgreSQL test riêng (2 cảnh báo Pydantic), Ruff/format/uv lock; backend build/up --no-deps healthy. Không đổi mật khẩu/DB. Hash Admin hiện là bcrypt nên đăng nhập vẫn cần hash Argon2id hợp lệ do chủ tài khoản chuẩn bị.

- [x] **ADMIN-LOGIN-LAN-02** | DONE cấu hìnhLAN (15/11/2026). Admin hiệnADMIN/ACTIVE; LAN192.168.110.101 loginCSRF403 do runtimechỉlocalhost. ThêmexactLANalias,apphealthy; PASSlocalhost/LANvalidation422 vàhostile/token403, PG/env/volume/network giữ nguyên. Chưa kiểm password thật; hỏi URL/lỗi nếu user gặp trường hợp khác.

- [x] **PACKAGE-IMAGES-01 — Hai Docker image riêng** | DONE (14/11/2026). Build coco-backend/coco-frontend với tags2026-11-14 vàlatest; export2tar trongtmp/docker. PASSbackendimport/frontendstandalone/imageconfig/hash; không pushregistry hoặc đổi container/DB/env đang chạy.

- [x] **SCHEMA25-COMPAT — Mapping schema25** | DONE code/reference tests (14/11/2026). Metadata25tables/182columns/27explicitindexes,13extensionTables và Order discount/shipping/payment20; SQL nguồn copy vào fixture/testPG riêng, không DDL nghiệp vụ. PASS460backend trên sourceSQL25/80frontend/build/journey. LiveDB25tables nhưng identityBYDEFAULT khác sourceALWAYS vẫn ghi drift, không tự migration. Không tự bậtcoupon/review/payment/shipping/history API. Xem docs/schema25-crud-k6.md.
- [x] **SELLER-CRUD-25 — CRUD cả shop và sản phẩm** | DONE (14/11/2026). Tạo/xem/sửa có sẵn, bổ sung DELETE shop/{id} và products/{id}, confirmationUI/CSRF/ownership/busy/no replay. Shop/product cóFK liên quan409/rollback/giữ lịch sử; shopID chốngtabcũ xóa shop thay thế. PASS backend CRUD/reference + E2E shop/product320–1440, stock/history protection,80frontend tests/lint/typecheck/build/Docker. Không thay dữ liệu thật.
- [ ] **K6-AWS-ACCESS — k6 qua URL public web** | IN_PROGRESS. Thêm publicGETcatalog cùng origin + fixedproxy/queryvalidation/no privatecookie forwarding; script k6HTTP cóCSRF/cookie và workloadbounds. PASS k6v2.4container riêng25/25checks,0unexpectedHTTPerrors trên testDB25; chưa chạy từAWS/GrafanaCloud vì chưa cóURLpublic/domain/ALB. Sơ đồ cho thấy k6ngoàiAWS→Internet→publicLB; không deployAWS/mởDBInternet hoặc bỏauth. Cần URLstaging được chỉ định để xác minh đường thực tế.

- [x] **SCHEMA-REVIEW-02 — Đối chiếu file schema mới** | DONE review READ ONLY (12/11/2026), chưa đồng bộ code. File mới6bảng/chưaCOMMIT/identity BY DEFAULT; DB hiện12bảng/11identity BY DEFAULT/6triggers, model còn ALWAYS. Chờ xác nhận file đầy đủ hay phần đầu; không SQL execution/DDL/migration/data changes. Xem docs/schema-review-2026-11-12.md.

- [x] **FIX-MOBILE-AUTH-01 — Xác thực qua IP Wi-Fi hiện tại** | DONE cấu hình runtime (11/11/2026). Tái hiện LAN172.18.60.11 register403 CSRF_FAILED do hai app chỉ allowlocalhost. Giữ canonical localhost, additional_origins exact localhost+LAN đồng bộ, up riêng app --no-deps healthy; không sửa root.env/PG/Compose/source. PASS mobilebrowser390 LAN/localhost register+login empty422, hostile/token403/noJSerrors/overflow; không account/data writes, PostgreSQL/env/volume/network bảo toàn. Hướng dẫn hiện tại tại docs/mobile-local.md; chưa kiểm điện thoại vật lý và IP sẽ đổi theo Wi-Fi.

- [x] **ADMIN-GRANT-01 — Cấp quyền quản trị local** | DONE (11/11/2026). CLI preview READ ONLY/apply expected user ID, ACTIVE user hiện hữu/transaction/no-op/rollback. Người dùng đã chỉ định email; đã preview đúng user_id1 ACTIVE/USER, apply USER→ADMIN thành công và đọc lại xác nhận ACTIVE/ADMIN. Chỉ thay role/updated_at của target, không tạo account/đổi password/schema/public API. PASS383 backend full và11 CLI targeted tests từ lượt chuẩn bị; thao tác thật xác minh bằng read, không xin mật khẩu/đăng nhập thay user. Hướng dẫn [grant-admin.md](grant-admin.md). Không mở P7-02.

- [x] **FIX-AUTH-02 — Đăng nhập localhost khi dùng LAN** | DONE (10/11/2026). Tái hiện localhost403 CSRF_FAILED/LAN422; thêm additional_origins JSON exact allowlist cùng frontend/backend, Compose local alias localhost:3001 ngoài public origin LAN. Giữ token/cookie binding, CSRF/Origin/Referer và host-only cookies; production chỉ HTTPS. PASS323 backend full/PostgreSQL16 riêng+audit READ ONLY/Ruff/lock,53 frontend tests/lint/typecheck/build; browser login thật test DB cả canonical/localhost, live hai địa chỉ401 invalid credentials thay403, hostile/token403. Docker app healthy, PostgreSQL/env/volume/network bảo toàn. Không schema/data/secret/Terraform/AWS changes, không mở task khác.

- [x] **BRAND-02 — Logo trong suốt và lớn hơn** | DONE (10/11/2026). Tách nền bằng imagegen từ ảnh chủ dự án, giữ ảnh gốc; alpha thật/corners0, không bo khung trắng. BrandLogo/favicons dùng coco-logo-transparent.png, cao84px desktop/58px mobile (auth/Seller50px, shipping nhỏ40px), responsive320–1440. PASS lint/typecheck/production build/browser/visual QA; không đổi dữ liệu sản phẩm.

- [x] **BRAND-01 — Cập nhật logo ảnh COCO** | DONE (10/11/2026). Dùng nguyên loho.png người dùng gửi cho BrandLogo chung và favicon. PASS lint/typecheck/build/browser bảy route320–1440; không sửa ảnh nguồn hoặc gán vào sản phẩm. Xem docs/seller-products.md.

- [x] **UI-16 — Đồng bộ màu logo COCO** | DONE (10/11/2026). Dependencies: UI-15/P3-03/P4-03. File: frontend/src/app/globals.css, docs/progress.md/task-plan.md. Hoàn thành: token --color-coco-logo #0066FF chung cho header/footer/storefront/auth/seller, bỏ4 màu riêng; nét SVG dùng currentColor. PASS lint/typecheck/Docker production build,20 logo trên6 route ở390/1440 có cùng computed RGB(0,102,255), không overflow/JS errors; đã xem ảnh header homepage/Seller. Frontend healthy, giữ LAN origin; PostgreSQL/env/volume/network bảo toàn. Không API/DB/data/Compose/dependency changes, không triển khai vận chuyển từ ảnh; dừng sau UI-16.

- [x] **FIX-LAN-01 — Cho phép truy cập LAN trên mobile** | DONE phần cấu hình local (10/11/2026). Files: chỉ frontend binding trong docker-compose.yaml, docs/mobile-local.md/progress. Hoàn thành: frontend0.0.0.0:3001, runtime origin hai app dùngIP LAN qua biến phiên, không sửa .env/PG service. PASS compose config/app healthy/LAN browser200+responsive+CSRF+Origin/hostile403/guest401/PostgreSQL-env-volume-network giữ nguyên. Chưa kiểm chứng điện thoại thật sau khi nối cùng Wi-Fi/firewall-router từ thiết bị khác; không5G remote/HTTPS, không mở task tiếp theo.

- [x] **AUTH-POLICY-01 — Quy tắc mật khẩu theo yêu cầu mới** | DONE (10/11/2026). Đăng ký9–128 ký tự có chữ hoa A–Z, số0–9 và ký tự đặc biệt punctuation/symbol; không trim, không bắt buộc chữ thường. Backend validator + frontend helper/hint, login giữ tương thích hash cũ và mật khẩu9 ký tự mới. Files: schemas/auth.py, auth-contract/auth-form/CSS, tests, docs. PASS unit/API/browser: thiếu điều kiện bị từ chối, bypass client422, mật khẩu9 hợp lệ đăng ký/login, legacy hash login được; không đổi password user hiện hữu/schema.

- [x] **FIX-AUTH-01 — Bật xác thực local** | DONE (10/11/2026). Sửa lỗi đăng ký/đăng nhập503 do thiếu khóa. File: cấu hình riêng backend/.env.auth (ignored), backend section Compose, env mẫu và hướng dẫn auth. PASS: csrf200, guest401, đăng ký invalid422 không tạo user, login form gọi API và báo401 đúng cho email không tồn tại; E2E đăng ký/login/logout PostgreSQL16 test riêng. Secret chỉ vào backend, không frontend/PostgreSQL/image/Git. Backend healthy; PostgreSQL ID/start/mount/service config, volume/network và root .env hash giữ nguyên. Không tạo user test trong DB thật; không mở P5-01.

Ngày: 09/11/2026. Repository đích: `D:/Auto-scaling-E-commerce-Platform-with-Data-Pipeline-on-AWS`.

## Quy trình và giới hạn

Mỗi lần chỉ làm một TASK được người dùng yêu cầu. Trạng thái: TODO, IN_PROGRESS, DONE, BLOCKED; checklist chỉ đánh dấu khi DONE. Kết thúc task phải kiểm thử đúng phạm vi, cập nhật progress và dừng. Không tự thực hiện dependency hoặc task kế tiếp. Không sửa Terraform, commit/push, xóa dữ liệu hoặc triển khai AWS.

Giữ nguyên toàn bộ service postgres, cấu hình PostgreSQL, named volume `marketplace_postgres_data`, network `marketplace_network` và dữ liệu hiện có. Không tạo database/schema, không chạy SQL khởi tạo, không ORM create_all hoặc auto migration. Backend trong Docker kết nối hostname `postgres:5432`; browser không dùng hostname nội bộ này. Chỉ bổ sung frontend/backend ở task P2-04; không thay Compose ở phase phân tích. Database test phải tách khỏi volume/database hiện hữu.

## Các điểm cần giải quyết

- Q01 — RESOLVED (09/11/2026): Người dùng xác nhận `create_table (1) (1).sql` không phải schema cần dùng; loại file này khỏi nguồn yêu cầu Marketplace. Dùng `marketplace_schema.sql` để đối chiếu DOCX và database hiện hữu; không chạy SQL hoặc tạo lại schema.
- Q02 — RESOLVED: PostgreSQL đang chạy, truy vấn READ ONLY thành công. Kiểm tra lại xác nhận schema marketplace đầy đủ; xem docs/database-audit.md.
- Q03 — RESOLVED (P1-03): người dùng đồng ý Buyer hủy PENDING; Seller hủy PENDING/CONFIRMED; hoàn tồn một lần; shop khóa xử lý đơn cũ, user khóa không dùng protected API. Xem docs/business-rules.md.
- Q04 — RESOLVED (P1-03): người dùng đồng ý access JWT 15 phút, logout xóa cookie, chưa refresh token; giới hạn revocation được ghi rõ trong docs/architecture.md.
- Q05 — RESOLVED (P1-03): người dùng đồng ý giỏ cần login, chưa phí/giảm giá, chặn self-purchase, danh mục cha ẩn thì sản phẩm nhánh con ẩn. Checkout replay trả đơn cũ; chưa có API bật lại sản phẩm do schema không lưu chủ thể ẩn. Xem docs/business-rules.md và docs/api-contract.md.
- Q06 — RESOLVED về hướng thiết kế (P1-03): người dùng đồng ý dùng S3; local dùng endpoint S3-compatible được cung cấp hoặc task MinIO được duyệt riêng. Endpoint/bucket cụ thể vẫn là dependency P6-03, không tự thêm service/volume/network.
- Q07: AWS hai AZ, scaling EC2/pod, monitoring và ETL S3/Athena thuộc đề tài nhưng chưa được phép triển khai; cần scope/task riêng. Website sẵn sàng nhiều replica không đồng nghĩa đã hoàn thành auto scaling/ETL.
- Q08 — RESOLVED (P1-02 kiểm tra lại, 09/11/2026): marketplace hiện có đủ 12 bảng/86 cột, 55 constraints, 36 indexes, 6 triggers và 1 function phù hợp SQL gốc. Các chênh lệch D01–D10 không còn quan sát được. Xem kết quả mới nhất đầu docs/database-audit.md; không sửa DB trong lần kiểm tra.

## PHASE 1 Phân tích và thiết kế

- [x] **P1-01 — Phân tích và lập kế hoạch** | DONE. Mục tiêu: đọc repository, hai SQL, DOCX cả sơ đồ và Compose; đối chiếu hiện trạng. Dependencies: không. File: chỉ `docs/task-plan.md`, `docs/progress.md`. Hoàn thành: kế hoạch có task/dependency/file/acceptance/test; database chưa truy cập được phải ghi rõ. Test: kiểm kê file, review coverage FR, Compose config --quiet, inspect container/volume/network chỉ đọc. Không gộp task xác minh schema còn chờ vào DONE.
- [x] **P1-02 — Xác minh database hiện hữu** | DONE (kiểm tra lại metadata PASS; Q08 RESOLVED). Dependencies: P1-01 và DB truy cập được. File: `docs/progress.md`, `docs/database-audit.md`. Mục tiêu: trong transaction READ ONLY đối chiếu version/schema/tables/columns/identity/defaults/PK/FK/check/unique/indexes/triggers với SQL Marketplace. Hoàn thành: báo đủ 12 bảng hoặc mọi chênh lệch; không sửa DDL/data. Test: đọc pg_catalog/information_schema, ROLLBACK; không xuất dữ liệu cá nhân. Không tạo bảng kể cả thiếu.
- [x] **P1-03 — Chốt nghiệp vụ và API** | DONE (Q03–Q06 đã được người dùng duyệt, thiết kế và review tài liệu hoàn tất). Dependencies: P1-02; Q08 RESOLVED. File: `docs/business-rules.md`, `docs/api-contract.md`, `docs/architecture.md`. Mục tiêu: ma trận quyền, transition, HTTP errors, tiền/ID, pagination, auth và contract. Hoàn thành: mọi FR có endpoint/UI/test dự kiến; điểm chưa chốt không được ghi thành quyết định. Test: walkthrough Guest/Buyer/Seller/Admin và luồng concurrent checkout.

## PHASE 2 Nền tảng ứng dụng

- [x] **P2-01 — Frontend skeleton** | DONE (lint/typecheck/build và production HTTP smoke PASS). Dependencies: P1-03. File: `frontend/package.json`, lockfile, TS/Next/Tailwind config, `src/app/`. Mục tiêu: App Router, TypeScript strict, Tailwind và route shell. Hoàn thành: ứng dụng chạy được, chưa mock nghiệp vụ. Test: lint/typecheck/build theo scripts đã khai báo.
- [x] **P2-02 — Backend skeleton** | DONE (22 tests, Ruff và HTTP Uvicorn smoke PASS). Dependencies: P1-03. File: `backend/pyproject.toml`, lockfile, `app/main.py`, `app/core/`, `app/api/`, tests. Mục tiêu: FastAPI modular, env validation, error envelope, request ID/logging, liveness. Hoàn thành: không secrets trong code/logs, OpenAPI hoạt động. Test: config/error/health smoke tests.
- [x] **P2-03 — Mapping SQLAlchemy và pooling** | DONE (37 tests, metadata audit READ ONLY và readiness PASS). Dependencies: P2-02, P1-02. File: `backend/app/db/`, `models/`, integration tests. Mục tiêu: mapping chính xác schema marketplace, session lifecycle và readiness DB. Hoàn thành: dùng DB hiện hữu; DSN hostname postgres trong container; không create_all/migrations; pool có ngân sách theo replica. Test: introspection so với mapping, SELECT read-only; tests ghi dữ liệu chỉ trên DB test riêng.
- [x] **P2-04 — Bổ sung ứng dụng vào Compose** | DONE (Docker build, app health/network/non-root và bảo toàn PostgreSQL PASS). Dependencies: P2-01–03. File: Dockerfiles frontend/backend, `docker-compose.yaml`, `.env.example`, README. Mục tiêu: chỉ thêm hai service ứng dụng và biến ứng dụng, nối network đang có. Hoàn thành: postgres/volume/network giữ nguyên; không down -v, không recreate postgres, không chạy init; frontend server gọi backend qua network, browser qua URL cấu hình. Test: compose config, diff các cấu hình được bảo vệ, build riêng app, smoke endpoints; không start nếu chưa được yêu cầu trong task.

## PHASE 3 Catalog và trải nghiệm công khai

- [x] **P3-01 — API danh mục và shop** | DONE (47 tests, PostgreSQL test riêng, Docker/HTTP smoke PASS). Dependencies: P2-03, P1-03. File: backend routers/schemas/services/repositories catalog, tests. Hoàn thành: API public chỉ trả dữ liệu được phép; shop APPROVED; pagination khi cần. Test: dữ liệu active/inactive, shop khóa và 404 trên DB test.
- [x] **P3-02 — API sản phẩm và tìm kiếm** | DONE. Dependencies: P3-01. File: backend/app/{schemas,repositories,services}/products.py, api/v1/{router.py,routers/products.py}, tests/test_products.py, tests/integration/test_public_catalog.py, README/docs. Hoàn thành: tìm tên, lọc danh mục con/shop, thứ tự/phân trang ổn định, metadata ảnh/tồn, public visibility. URL ảnh null tới P6-03 vì delivery S3 chưa cấu hình, giống chính sách logo P3-01; không bịa URL hoặc trả storage key. Test: 68 passed đầy đủ integration, 56 passed/12 skipped khi không env; Ruff/lock PASS; Docker backend health và HTTP list200/validation422/detail404 PASS. Không thêm index/schema, không ghi DB hiện hữu. Frontend chưa nối API. Dừng sau P3-02.
- [x] **P3-03 — Giao diện chung và trang chủ** | DONE. Dependencies: P2-01, P3-01–02. File: page/globals.css, components/{layout,home}, lib/{catalog-api,categories}, nhãn preview layout cho routes UI-01, frontend tests/package script/docs. Hoàn thành: header/search/category/banner/footer và homepage API thật; 6 danh mục lấy ID qua API, loading/error/empty/retry, VND, responsive. Cart/account là thông tin chức năng chưa mở, không fake auth/cart; search/category chạy trên trang chủ, danh sách/chi tiết tích hợp đầy đủ ở P3-04/05. Test: 7 tests PASS, lint/typecheck/build PASS; Chrome fixtures success/error/timeout-contract/loading/empty/retry, 390/768/1440px và keyboard PASS; Docker frontend healthy, real API empty state PASS; PostgreSQL/env/volume/network giữ nguyên. Dừng sau P3-03.
- [x] **P3-04 — Trang danh sách và tìm kiếm** | DONE. Dependencies: P3-03. File: products route, CatalogBrowser, lib/catalog-query/catalog-api/categories, filter/pagination UI/styles/tests/docs, link header/campaign/footer/homepage. Hoàn thành: preview list thay bằng API thật, URL giữ q/danh-muc/sort/page/page_size, về trang đầu khi đổi lọc; GET form, retry/loading/empty; preview label chỉ còn detail UI-01. Test: 14 tests PASS; lint/typecheck/build PASS; Chrome fixture filter/sort/paging/back-forward/reload/error/retry/empty/loading và 390/768/1440px PASS; real Docker/API list200 total0 và search/mobile PASS; DB/config/env/volume/network giữ nguyên. Không sửa schema/seed/backend hoặc tự làm P3-05. Dừng sau P3-04.
- [x] **P3-05 — Chi tiết sản phẩm và gian hàng** | DONE. Dependencies: P3-03/04. File: app/san-pham/[slug]/page (ID thật), app/gian-hang/[shopSlug], gallery/shop avatar, resource API/query helpers, list card links, shared catalog/base path, docs/tests. Hoàn thành: bỏ detail mock, ảnh/tên/giá/tồn/mô tả/shop API thật, 404 phân biệt upstream failure, gallery keyboard/mobile và shop product list giữ filter/pagination. Giỏ/checkout chưa mở. Kiểm thử contract/boundaries/visibility/404/HTTP/loading/error/gallery/shop isolation/responsive. Không sửa backend/schema/seed/S3 hoặc tự làm P4.

## PHASE 4 Authentication và quyền

- [x] **P4-01 — Auth backend** | DONE. Dependencies: P2-03, P1-03. File: auth/users/core security, tests. Hoàn thành: email đăng ký/login, Argon2id, JWT algorithm allowlist/signature/exp/sub/issuer/audience, cookie HttpOnly và CSRF/origin theo contract, logout; không endpoint tự cấp Admin. Test: email trùng case-insensitive, mật khẩu sai, token giả/hết hạn, user khóa; không lộ hash.
- [x] **P4-02 — Policy và ownership** | DONE. Dependencies: P4-01. File: backend dependencies/policies, tests. Hoàn thành: USER mua; owner có quyền Seller, bán cần APPROVED; Admin từ DB; kiểm tra trạng thái mới nhất mỗi protected request. Test: ma trận 401/403, IDOR chéo user/shop, đổi trạng thái sau cấp JWT.
- [x] **P4-03 — Auth UI và tài khoản** | DONE. Dependencies: P4-01–02, P3-03. File: frontend auth/account routes/services. Hoàn thành: đăng ký/login/logout, validation, return URL nội bộ an toàn, không token localStorage. Test: luồng thành công/thất bại, session hết hạn, CSRF và protected API.
- [x] **P4-04 — Địa chỉ giao hàng** | DONE (10/11/2026). Dependencies: P4-02–03. File: addresses backend/UI/tests; Next private proxy; `/tai-khoan/dia-chi`; account link; docs/addresses.md. Hoàn thành: CRUD theo ownership, tối đa một mặc định, snapshot đơn cũ không đổi. Test: full131 backend PASS (PostgreSQL16 riêng + metadata audit READ ONLY), 26 frontend tests/lint/typecheck/build PASS; E2E thật thêm/sửa/đổi mặc định/xóa/reload/error/expiry/CSRF, responsive320/390/768/1440 PASS. Hai app Docker healthy, PostgreSQL/env/volume/network giữ nguyên. Auth local vẫn cần secret theo hướng dẫn, không tự ghi `.env`. Dừng; P5-01 chưa thực hiện.

## PHASE 5 Giỏ hàng và đơn hàng

- [x] **P5-01 — Giỏ nhiều shop** | DONE (10/11/2026). Dependencies: P4-02–03, P3-02/05. File: cart schemas/repository/service/router/tests; Next cart routes/proxy/client/contract; components/cart, giỏ/detail/header/account; docs/cart.md. Hoàn thành: thêm/xóa/sửa lượng, gom shop, unique dòng, giá/tồn mới từ API, không giữ hàng. PASS158 backend tests với PostgreSQL16 riêng + metadata audit READ ONLY, 30 frontend tests/lint/typecheck/build, Ruff/lock checks, E2E thật nhiều shop/default auth/stock-price updates/hidden/locked/CSRF/error/retry/expiry/mobile. Docker backend/frontend healthy; PostgreSQL/env/volume/network giữ nguyên; không data/SQL/schema/Compose/dependency changes. P5-02 chưa thực hiện.
- [x] **P5-02 — Checkout COD transaction** | DONE (10/11/2026). Dependencies: P5-01, P4-04. File: checkout schemas/repository/service/router, db/locks.py, tests, docs/checkout-api.md. Hoàn thành: Decimal + giới hạn NUMERIC, JWT/CSRF/ownership/status/full-cart/price/stock; khóa user→cart→category shared→shops→products→inventory; orders/shop_orders/items snapshots/composite FK, conditional stock decrement và clear cart nguyên tử; unique buyer/key,201 lần đầu/200 replay trước kiểm giỏ; bounded retry qua COMMIT. PASS205 backend full (PostgreSQL16 riêng + audit READ ONLY),31 frontend tests/lint/typecheck/build, browser9-character password + real HTTP COD hai shop/replay/trừ kho đúng một lần/giỏ rỗng. Docker hai app healthy; PostgreSQL/env/volume/network giữ nguyên. Không UI/proxy checkout trong task này; P5-03 chờ yêu cầu.
- [x] **P5-03 — Checkout UI** | DONE (10/11/2026). Dependencies: P5-02. File: checkout panel/contract/client/Next route/private proxy; cart link/layout/help copy; docs/checkout-ui.md. Hoàn thành: chọn địa chỉ, COD, review nhiều shop, response server xác nhận; intent tối thiểu theo user giữ key/payload qua retry/reload, sửa lỗi giá/tồn có xác nhận và giữ key; không tạo intent mới khi chưa rõ kết quả. PASS37 frontend tests/lint/typecheck/build, browser thật Next→FastAPI→PostgreSQL16 riêng: double submit, multi-shop/address, commit-response loss/reload/replay, price repair/stock failure/expiry login/storage failure/error retry/responsive320/390/768/1440. Docker frontend healthy; PostgreSQL/env/volume/network giữ nguyên. Không backend/schema/Compose/env/dependency changes; P5-04 chưa thực hiện.
- [x] **P5-04 — Theo dõi đơn Buyer** | DONE (10/11/2026). Dependencies: P5-02–03. File: orders schemas/repository/service/router/tests, Next proxy/client/pages/components, docs/buyer-orders.md. Hoàn thành: lịch sử phân trang ổn định, chi tiết snapshot, trạng thái từng shop, không trạng thái tổng giả, READ ONLY/ownership USER và ADMIN/no-store; liên kết tài khoản/checkout. PASS221 backend full/PostgreSQL16 riêng + metadata audit READ ONLY/Ruff,40 frontend tests/lint/typecheck/build, browser thật checkout→detail/mixed status/snapshots/14 đơn phân trang/IDOR/expiry/error-retry/responsive320/390/768/1440. Docker hai app healthy; PostgreSQL/env/volume/network giữ nguyên. Không schema/data/Compose/env/dependency changes. Hủy và hoàn tồn theo state machine ở P6-05; dừng sau P5-04.

## PHASE 6 Seller

- [x] **P6-01 — Gian hàng Seller** | DONE (10/11/2026). Dependencies: P4-02–03. File: seller_shop schemas/repository/service/router/tests; seller dashboard/client/proxy/route; header/account/login return; docs/seller-shop.md. Hoàn thành: tạo PENDING/một shop-owner/unique slug, đọc-sửa hồ sơ mọi shop_status theo ownership, không tự approve/đổi owner/slug/logo; dashboard `/kenh-nguoi-ban` có login/loading/error/retry/response-loss recovery. PASS250 backend full/PostgreSQL16 riêng+metadata audit READ ONLY/Ruff,44 frontend tests/lint/typecheck/build, browser thật register/edit/4 status/slug conflict/IDOR/commit response loss/error retry/expiry/locked/mobile. Docker hai app healthy; PostgreSQL/env/volume/network giữ nguyên. Không schema/data/Compose/env/dependency changes; dừng sau P6-01.
- [x] **P6-02 — Sản phẩm Seller** | DONE (10/11/2026). Dependencies: P6-01, P3-02. Files: seller_products schemas/repository/service/router/tests; SellerProducts/client/proxy/routes/dashboard; docs/seller-products.md. Hoàn thành: list/detail/thêm/sửa/ẩn theo ownership/shop APPROVED, SKU unique theo shop, category/tổ tiên active, Decimal, product+inventory transaction; không reactivation/sửa tồn qua PATCH. PASS287 backend/PostgreSQL16 riêng+audit READ ONLY/Ruff,48 frontend tests/lint/typecheck/build, browser thật CRUD/filter/pagination/SKU/response-loss/error retry/expiry/responsive. Docker app healthy, PostgreSQL/env/volume/network giữ nguyên; không schema/data/Compose/dependency changes. Dừng sau logo và P6-02; P6-03 chưa bắt đầu.
- [ ] **P6-03 — Ảnh S3** | IN_PROGRESS (10/11/2026), code và hướng dẫn đã chuẩn bị theo yêu cầu người dùng “chưa có bucket”. Dependencies: P6-02, Q06; cần storage thật để hoàn tất. Files: storage/image schemas/repository/service/router, public/Seller/cart delivery, Next proxy/client/image panel, backend-only optional env_file/template, tests/docs/s3-images.md. Có presigned POST MIME/size/grant, verify/decode và immutable final key, ownership/primary transaction/reference-only delete. PASS315 backend/PostgreSQL16 riêng+SDK double+audit READ ONLY,52 frontend tests/lint/typecheck/build; browser missing-storage disabled/503 và logo responsive. NOT RUN real bucket upload/CORS/IAM/delivery/conditional PUT; không đánh dấu DONE, không tạo bucket/upload AWS hoặc mở P6-04.
- [x] **P6-04 — Tồn kho Seller** | DONE (10/11/2026). Dependencies: P6-02, P5-02. GET inventory/POST adjustments, delta nguyên + X-Expected-Quantity dưới row lock/conditional update; bounds/ownership/approved shop/CSRF, rollback, không tự tạo tồn thiếu. UI nhập/xuất có xác nhận, stale/mất phản hồi yêu cầu đọc lại, không retry delta. PASS344 backend full PostgreSQL16 test riêng + audit READ ONLY,57 frontend tests/lint/typecheck/build, Ruff, Docker build/up app --no-deps. Browser thật PASS tồn tăng/giảm/stale/response-loss/expiry và bốn viewport; live localhost smoke PASS. Xem [seller-inventory.md](seller-inventory.md); ABA chưa có operation ID, P6-03 vẫn chờ bucket, chưa mở P6-05.
- [x] **P6-05 — Đơn hàng Seller** | DONE (11/11/2026). Dependencies: P6-01, P5-04, Q03. API/UI list/filter/pagination/detail/status riêng shop, Buyer cancel từng đơn shop, state machine/expected/no-op; hoàn tồn một lần cùng transaction, thiếu tồn/overflow/COMMIT rollback. APPROVED/LOCKED shop xử lý đơn cũ, user ACTIVE, cross-shop404 kể cả Admin. PASS358 backend full/PostgreSQL16 test riêng + audit READ ONLY/Ruff,61 frontend tests/lint/typecheck/build, Docker app --no-deps healthy; browser Seller/Buyer workflow, response loss/recovery/stale/25 đơn pagination/filter/locked/expiry/503/responsive và live localhost PASS. PostgreSQL/env/volume/network bảo toàn. Xem [seller-orders.md](seller-orders.md); S3 còn chờ bucket, chưa mở P7.

## PHASE 7 Admin

- [x] **ADMIN-COMMERCE-01 — Admin không mua hàng/tạo gian hàng** | DONE code/kiểm thử riêng (11/11/2026). buyer policy chỉ USER ACTIVE,403 COMMERCE_FORBIDDEN cho cart/checkout/replay/địa chỉ/đơn Buyer và seller/shop profile-registration kể cả token cũ/đã có shop. UI ẩn lối mua/tạo shop, chặn URL trực tiếp, giữ Admin/public catalog. PASS448backend trên PGtest riêng (exclude3audit vì DB nghiệp vụ dừng),77frontend/lint/typecheck/build/Docker/E2E. Không xóa/chuyển owner shop/đơn/giỏ cũ. Images đã build; chưa up app khi PostgreSQL nghiệp vụ đang dừng. Xem docs/authorization.md/progress.md.

- [x] **ADMIN-FR-VERIFY — Nghiệm thu FR-A01–04** | DONE phần chức năng theo bảng người dùng. Đối chiếu API/UI và thêm4 acceptance cases cho Guest/Buyer/owner bị chặn, Admin xem/tìm/khóa-mở USER, duyệt/từ chối/khóa shop, hide loại khỏi public search, create/edit/disable category và DELETE405 giữ FK/tồn. Không đổi chính sách ADMIN chỉ xem đã chốt. Evidence và giới hạn runtime tại docs/admin-acceptance.md/progress.md; không thay trạng thái shop/dữ liệu nghiệp vụ.

- [x] **P7-01 — Admin và người dùng** | DONE (11/11/2026), phạm vi đã điều chỉnh theo người dùng “bỏ qua phần đó”: tài khoản ADMIN chỉ xem, không khóa/mở khóa Admin. Dependencies: P4-02–03. GET list/search/status/page và PATCH trạng thái USER; role/status đọc DB, CSRF/Origin, khóa actor/target theo ID và recheck quyền, transaction/rollback/no hash/no-store. UI /admin/users có confirm/recovery/expiry; link account chỉ ADMIN. PASS374 backend full PostgreSQL16 test riêng + metadata audit READ ONLY/Ruff,65 frontend tests/lint/typecheck/build/Docker; browser27 users/search/filter/page/lock/unlock/lost-response/role-revocation/expiry/readonlyAdmin/returnTo/responsive và live localhost PASS. PostgreSQL/env/volume/network bảo toàn; xem [admin-users.md](admin-users.md). Chưa mở P7-02, S3 còn chờ bucket.
- [x] **P7-02 — Phê duyệt và khóa shop** | DONE (11/11/2026). Dependencies: P7-01, P6-01. API/UI search/filter/page, PENDING→APPROVED/REJECTED và APPROVED→LOCKED, expected/row lock/no-op/rollback; không unlock/resubmit. PASS401 backend full PostgreSQL16 test riêng+metadata audit READ ONLY,16 focused Admin shops/Ruff;69 frontend tests/lint/typecheck/build/Docker, browser approve→sell→checkout→lock/chặn đơn mới/giữ xử lý đơn cũ, stale/lost-response/recovery/27shop pagination/filter/expiry/responsive; live localhost PASS. PostgreSQL/env/volume/network bảo toàn; xem [admin-shops.md](admin-shops.md). Không thay shop nghiệp vụ trong triển khai; chưa mở P7-03, S3 vẫn chờ bucket.
- [x] **P7-03 — Kiểm duyệt sản phẩm** | DONE (11/11/2026). Dependencies: P7-01, P6-02. API/UI search tên/SKU/shop/is_active/page/hide; Admin mọi shop, không reactivation theo contract/schema hiện tại, không đổi tồn/đơn/snapshot. PASS417 backend full PostgreSQL16 test riêng+metadata audit READ ONLY/Ruff,73 frontend tests/lint/typecheck/build/Docker; browser hai shop/28products/filter/page/hide/lost-response/privacy/public404/cart hidden/checkout409/Seller không bật lại/old snapshot/responsive và live localhost PASS. PostgreSQL/env/volume/network bảo toàn. Xem [admin-products.md](admin-products.md); chưa mở P7-04, S3 còn chờ bucket.
- [x] **P7-04 — Cây danh mục** | DONE (11/11/2026). Dependencies: P7-01, P3-01. GET cây active/inactive, POST/PATCH name/slug/parent/active, exclusive PG advisory lock chung với checkout để chống concurrent cycle, unique slug/root/reparent/no delete; giới hạn kỹ thuật100 cấp khớp public client. UI tree/form/confirm/inherited visibility/no retry/privacy. PASS438 backend full PostgreSQL16 riêng+metadata audit READ ONLY/Ruff,77 frontend tests/lint/typecheck/build/Docker; browser parent-child/reparent/disable-enable/stale-cycle/lost-COMMIT recovery/public-cart-checkout/old snapshot/expiry/4widths và live localhost PASS. PostgreSQL/env/volume/network giữ nguyên, không tạo danh mục mẫu trên DB nghiệp vụ. Xem [admin-categories.md](admin-categories.md); chưa mở P8, S3 còn chờ bucket.

## PHASE 8 Kiểm thử và hoàn thiện

- [ ] **P8-01 — Regression tích hợp** | IN_PROGRESS (11/11/2026). Regression API hiện có PASS445 sau vá Pillow13/4 test decoder backend trên PostgreSQL16 tmpfs riêng + audit READ ONLY;77 frontend tests/lint/typecheck, Ruff/format/lock PASS. Thêm3 workflow kiểm duyệt sau checkout, replay/snapshot/ownership/hoàn tồn; ma trận FR và quyền tại docs/test-matrix.md. PostgreSQL/env/volume/network bảo toàn. Chưa DONE vì P6-03/S3 thật còn NOT RUN; P8-02–04 phần độc lập đã được người dùng yêu cầu tiếp, gate S3 vẫn mở. Dependencies: P3–P7 DONE. File: backend/tests/integration, docs/test-matrix.md. Hoàn thành: FR và permission matrix có evidence; DB test riêng, không dữ liệu thật. Test: API failures, rollback, ownership và concurrent checkout/inventory/idempotency.
- [ ] **P8-02 — E2E và responsive** | IN_PROGRESS (11/11/2026). Người dùng yêu cầu tiếp tục phần độc lập không bucket: PASS browser Next production/FastAPI/PostgreSQL16 riêng cho Guest tìm → Buyer keyboard/cart/address/checkout COD → Seller hoàn tất → Buyer theo dõi → Admin duyệt/ẩn/khóa, snapshot/ownership/stock/loading503/recovery/expiry;7 màn hình/4widths. Sửa fieldset/file input tràn320px. PASS77 frontend tests/lint/typecheck/build/Docker và live localhost; PG/env/volume/network giữ nguyên. Runner/hướng dẫn tại tests/e2e. Chưa DONE: S3 thật/ảnh storage lỗi tải NOT RUN; P8-01 dependency chưa hoàn tất S3. Dependencies: P8-01. File: tests/e2e, sửa lỗi được xác định trong task. Hoàn thành: Guest tìm → Buyer mua → Seller xử lý → Buyer theo dõi, Admin duyệt/ẩn/khóa; keyboard/mobile. Test: E2E với DB test, lỗi mạng/empty/loading, ảnh không tải.
- [x] **P8-03 — Hiệu năng và nhiều replica** | DONE phạm vi local độc lập S3 (11/11/2026). Hai Uvicorn process thật/cùng PostgreSQL16 tmpfs;2000products/120reads/8concurrent/0errors/p95~47ms, query plans trang1/80, pool budget10/process. Cùng key4HTTP→1order, tranh lastunit→1success/1conflict, stock exact. Graceful idle shutdown replica và testDB outage live200/ready503 PASS; không load DB thật/thêm index/extension/config tuning. Runner tests/e2e/run.py E2E_SUITE=performance, tests/performance; docs/performance.md và baseline JSON. P8-01 vẫn thiếu gate S3; user cho phép hoàn tất phần độc lập, không suy ra AWS/autoscaling hoặc capacity production.
- [ ] **P8-04 — Bảo mật và bàn giao** | IN_PROGRESS (11/11/2026), phần local hoàn tất. README/handoff/test-matrix/performance/runbooks; thêm header bảo mật Next và decoder allowlist, vá Pillow12.3→13.0 do JPEG advisories/cập nhật lock. PASS445 backend/77 frontend/lint/typecheck/build/E2E/header/two-process health+shutdown; OSV47packages0findings, npm production0, pattern scan Git-visible PASS. Còn7 moderate dev-only ESLint/minimatch chưa có thay thế tương thích, không force major. S3 ảnh thật, HTTPS/production edge và gate cuối P8-01/02 chưa xong nên chưa DONE. Xem docs/handoff.md; không AWS/ETL/data import/PG/env/Compose changes.

## Coverage yêu cầu DOCX

| Yêu cầu | TASK |
| --- | --- |
| Guest, FR-B02 xem sản phẩm/shop | P3-01–05 |
| FR-B03 tìm tên/lọc danh mục | P3-02/04 |
| FR-B01 đăng ký/login/logout | P4-01–03 |
| FR-B04 giỏ nhiều shop | P5-01 |
| FR-B05 địa chỉ và checkout COD | P4-04, P5-02–03 |
| FR-B06 lịch sử và trạng thái | P5-04 |
| FR-S01/02 đăng ký/quản lý shop | P6-01 |
| FR-S03 sản phẩm/ảnh | P6-02–03 |
| FR-S04 tồn kho | P6-04 |
| FR-S05 xử lý đơn shop | P6-05 |
| FR-A01 người dùng | P7-01 |
| FR-A02 shop | P7-02 |
| FR-A03 sản phẩm | P7-03 |
| FR-A04 danh mục | P7-04 |
| Stateless, pooling, health, env, logging | P2-02–04, P8-03–04 |

Không bổ sung chat, voucher, review, biến thể hoặc thanh toán thật vì chưa thuộc đặc tả. SQL gốc giữ nguyên, không đưa DDL vào startup/init của ứng dụng.

## Tài liệu bổ sung theo yêu cầu

- [x] **DOC-01 — Quy tắc code, README và chuẩn bị dữ liệu** | DONE. Mục tiêu: hướng dẫn cộng tác/khởi chạy và phân biệt dữ liệu tối thiểu với dữ liệu ứng dụng tự tạo. Dependencies: hiện trạng P3-01. File: AGENTS.md, AGENT.md, README.md, backend/README.md, docs/data-requirements.md, docs/task-plan.md, docs/progress.md. Hoàn thành: quy tắc bám các quyết định đã chốt, hướng dẫn Docker giữ DB hiện hữu, checklist dữ liệu không yêu cầu secrets/seed tự động. Test: kiểm tra Markdown/links/file tồn tại và đối chiếu commands/config hiện có; không chạy test ứng dụng cho thay đổi chỉ tài liệu. Không bắt đầu P3-02.

## Các task giao diện bổ sung

- [x] **UI-07 — Thay banner trang danh sách sản phẩm** | DONE. Theo làm rõ của người dùng: chỉ /san-pham, không đổi homepage. File: components/catalog-banner.tsx, app/san-pham/page.tsx, globals.css, public/images/coco-catalog-banner.png và docs. Banner ảnh mỹ phẩm kem/đào + tiêu đề coco, desktop ảnh phải/chữ trái, mobile ảnh dưới, không gán artwork vào catalog. Test: lint/typecheck/build PASS; Chrome390/768/1440 ảnh/H1/filter/sort/overflow/console và homepage giữ nguyên PASS; đã xem screenshots; Docker healthy/DB preservation PASS. Dừng sau UI-07.

- [x] **UI-06 — Bộ lọc dọc và thanh sắp xếp ngang** | DONE. Dependencies: P3-04. File: catalog-browser/sort-bar/extra-filters, globals.css, docs. Sidebar Bộ lọc tìm kiếm có nhóm đơn vị vận chuyển và dịch vụ/khuyến mãi; sort ngang Phổ biến/Mới nhất/Bán chạy và giá. Lựa chọn chưa có API disabled/ghi nhãn, không fake sorting hoặc nhà vận chuyển đã tích hợp. Mới nhất/giá hoạt động thật, giữ URL và reset trang; sort hidden trong form để không mất lựa chọn. Test: 14 tests/lint/typecheck/build PASS; Chrome regression fixture + real API/empty/sort reset/disabled groups/390–1440px PASS; đã xem screenshot; frontend Docker healthy, DB preservation PASS. Không thay schema/backend/auth. Dừng sau UI-06.

- [x] **UI-05 — Header gọn và banner theo ảnh tham khảo** | DONE. Dependencies: UI-04 phần đã xong. File: header/page/globals.css, campaign-banners, public/images/coco campaign art, docs/banner-assets và progress/README. Đăng nhập/Đăng ký trong utility header; bỏ account, guest bar và nav danh mục ngang; banner 2:1 với 2 ô phải xếp dọc, responsive. Ảnh banner editorial tạo bằng image_gen, không dùng làm ảnh sản phẩm thật/giá giảm. Test: lint/typecheck/build PASS; Chrome 320/390/768/1440 xác nhận header removals/auth placement, 1+2 layout, ảnh tải được, 6 popup bounds/search/keyboard, không JS errors/overflow PASS; đã xem screenshot desktop/mobile; Docker frontend healthy và DB preservation PASS. Không làm auth backend hoặc gán ảnh vào DB; UI-04 ảnh thật vẫn chờ nguồn. Dừng sau UI-05.

- [ ] **UI-04 — Header xanh biển nhạt, icon danh mục và thương hiệu/ảnh** | IN_PROGRESS. Dependencies: UI-03; cần tên website cụ thể và đường dẫn ảnh thật/mapping từ người dùng. File: frontend page/header/footer/layout, brand-logo/category-icon/site-brand, public/icon.svg, styles/card placeholder, docs. Đã bỏ dải 3 câu, chỉnh màu header và icon; chuẩn bị cấu hình thương hiệu dùng chung. Đã nhận tên coco và đổi đồng bộ qua site-brand.ts, lint/typecheck/build/browser PASS; còn chờ đường dẫn ảnh thật/mapping, chưa gán ảnh bất kỳ. Kiểm thử UI/build và bảo toàn DB trước bàn giao; chỉ đổi tên/gắn ảnh đúng khi có đầu vào. Không thực hiện task nghiệp vụ khác.

- [x] **UI-03 — Màu sắc trẻ trung, thanh tài khoản và khu mua sắm nổi bật** | DONE. Dependencies: UI-02/P3-03. File: frontend page/header/globals.css, components/home/shopping-highlights.tsx và docs. Tông xanh cobalt/cam san hô, thanh Đăng nhập/Đăng ký cho khách, khu Flash Sale và Sản phẩm bán chạy với empty state. Không giả auth/discount/countdown/sales ranking; các dữ liệu này chưa có API. Test: lint/typecheck/build PASS; Chrome 320/390/768/1440, 7 menu/search/font/2 sections/keyboard PASS, đã xem screenshot; Docker frontend healthy, DB/config/env/volume/network giữ nguyên. Không bắt đầu P3-04 hoặc auth backend.

- [x] **UI-02 — Header theo ảnh tham khảo và sửa font** | DONE. Dependencies: P3-03. File: frontend/src/components/layout/site-header.tsx, app/{layout,globals.css,fonts}, docs/task-plan/progress, frontend/README. Header 3 tầng, kênh người bán/thông báo/hỗ trợ, search/account/cart, tông tím mận/cam đất; font Noto Sans tự host kèm OFL, thống nhất chữ Việt. Các mục nghiệp vụ chưa mở chỉ có disclosure hướng dẫn; không fake backend. Test: lint/typecheck/build PASS; Chrome 320/390/768/1440, popup bounds của 5 menu/font load HTTP200/search/keyboard PASS; frontend Docker healthy, PostgreSQL/env/volume/network giữ nguyên. Không thực hiện P3-04.

- [x] **UI-01** | DONE. Theo yêu cầu mới: UI local trước API với đúng 6 danh mục. Dependencies: P2-01; chưa phụ thuộc P3-02. File: frontend/src/{app,components,lib}, frontend/README.md, README.md, docs/{task-plan,progress,data-requirements}. Hoàn thành: trang chủ, danh sách tìm/lọc/sắp xếp, chi tiết, responsive/keyboard, mẫu ghi nhãn rõ, không checkout giả, không gọi DB/API. Kiểm thử: lint/typecheck/build PASS; Docker frontend build/health PASS; Chrome kiểm tra tìm kiếm, giá, 6 routes danh mục, chi tiết/404, empty/reset, 390px không overflow, skip link và không JS errors/API requests PASS. PostgreSQL ID/start/mount/config/volume/network và .env giữ nguyên. Không hoàn thành thay các task API/auth/cart gốc. Dừng sau UI-01.


## UI-08 — Giao diện coco theo mẫu xanh và điều hướng liên kết

- [x] **UI-08** | DONE. Mục tiêu: chỉnh bố cục theo ảnh tham khảo mới nhất, đúng 6 danh mục sức khỏe/làm đẹp. Dependencies: P3-03/04/05. Files: app/page/globals.css; components/layout/{brand-logo,site-header,site-footer}; home/{campaign-banners,shopping-icon,shopping-highlights,home-catalog}; README/docs. Hoàn thành: header xanh, wordmark coco, menu dọc 6 nhóm, banner túi mua sắm SVG, hai CTA danh mục, 5 lối tắt, Deal sốc/bán chạy/ưu đãi có trạng thái thật, footer hỗ trợ; liên kết catalog/query/detail/shop hiện hữu. Không mở rộng auth/cart/khuyến mãi/backend/database. Test: 21 unit PASS, lint/typecheck/build PASS; Chrome320/390/768/1440 không overflow, 6 danh mục/search/anchor/panel/support PASS; fixture detail/shop/gallery/error/404/isolation PASS. Frontend Docker healthy, PostgreSQL ID/start/mount/config/env/volume/network trước-sau PASS. Dừng sau UI-08.


## UI-09 — Đồng bộ danh sách, chi tiết và bố cục giỏ/checkout theo ảnh

- [x] **UI-09** | DONE. Mục tiêu: tiếp tục bộ giao diện xanh theo bốn ảnh mới, chỉ6 danh mục đã chốt. Dependencies: UI-08, P3-04/05. Files: CategoryNavigation, ShoppingInformation, OrderLayoutPreview, routes san-pham/detail/gio-hang/thanh-toan, catalog-banner, header, globals.css, docs. Tiêu chí: list/detail giữ API và gallery/shop links; menu6 nhóm; giỏ→checkout→giỏ→catalog liên kết; preview nhãn rõ, không tạo dữ liệu/giá/giỏ/đơn giả. Không mở auth/cart API/transaction hoặc thanh toán ngoài COD. Test: 21 tests + lint/typecheck/build PASS; browser fixture detail/shop/gallery/error/404/isolation PASS; browser routes list/cart/checkout200,6 menu items,320/390/768/1440 no overflow/JS errors; không mutation/thu thập PII, nút đặt hàng disabled; Docker frontend healthy, DB/config/env/volume/network giữ nguyên. Dừng sau UI-09. P4/P5 vẫn TODO, không được xem preview là hoàn tất nghiệp vụ.


### P4-01 — Kết quả kiểm chứng

Files: core/security/config, schemas/auth, repositories/users, services/auth, routers/auth/router, tests/test_auth và test_auth_postgres, pyproject/uv.lock, backend env mẫu/root env mẫu, chỉ environment của service backend trong Compose, README/docs. PASS95 tests gồm audit READ ONLY schema hiện hữu và PostgreSQL16 tmpfs riêng: đăng ký/login/logout/me, unique LOWER(email) đồng thời, hash Argon2id, role/status hiện tại, rollback, JWT giả/exp/iat/sub/issuer/aud/alg, CSRF ký ràng buộc cookie session/Origin/Referer/rotation, HttpOnly/Secure/host cookie, hai app instance dùng chung khóa. Ruff check/format và uv lock --check PASS. Chưa làm UI auth/policy Buyer/Seller/Admin P4-02/03. Cần người dùng tự đặt MARKETPLACE_JWT_SECRET random trong env để bật auth local; thiếu khóa auth503 có chủ ý, catalog không bị chặn. Không tự tạo account/seed hoặc ghi DB thật. Dừng sau P4-01.


### P4-02 — Kết quả

Files: backend/app/api/dependencies.py, repositories/access.py, services/access.py, auth router/service dùng policy chung, tests/test_access.py và test_access_postgres.py, docs/README. Policy đọc role/status DB, ownership SQL scoped user/shop; Admin không bypass, shop APPROVED bán và LOCKED chỉ xử lý đơn cũ. ReadAccess/WriteAccess function-scope transaction, JWT/CSRF, write lock user→shop; commit trước response. PASS111 tests với PostgreSQL16 test riêng + READ ONLY audit DB hiện hữu, không skip; Ruff/format/lock check PASS. Tests bao gồm role/status đổi sau JWT, IDOR chéo owner, multi-shop order, rollback/commit failure503. Không mở dashboard/business CRUD, không sửa schema/data/env/Compose/dependencies, không tự làm P4-03. Xem docs/authorization.md.


### P4-03 — Kết quả

Files: frontend lib/auth-{contract,proxy,client}; components/auth; routes dang-ky/dang-nhap/tai-khoan/api/v1/auth/[endpoint]; root layout/header/footer/styles; tests/auth.test.mjs; frontend/.env.example; Compose chỉ thêm MARKETPLACE_PUBLIC_ORIGIN frontend; docs. Hoàn thành: đăng ký→login, login/me/header name/logout, loading/error/validation, returnTo allowlist, HttpOnly cookies/CSRF qua same-origin fixed-target proxy/no browser JWT storage. PASS24 tests + lint/typecheck/build; browser real Next/FastAPI/PostgreSQL16 riêng flow success/error/expired/cookie/reload/CSRF/return URL/mobile320/390/768/1440. Docker frontend healthy, live missing-secret error/3 routes200/proxy403 PASS; DB/schema/data/config/volume/network/root env giữ nguyên. Activation auth local còn cần người dùng tự cấu hình JWT secret theo P4-01. Dừng sau P4-03, không tự làm P4-04.


## UI-10 — Thiết kế lại đăng nhập/đăng ký theo hai ảnh tham khảo

- [x] **UI-10** | DONE. Mục tiêu: auth header gọn, nền xanh, form giữa, minh họa túi/quà/coupon hai bên, mobile gọn theo ảnh mới. Dependencies: P4-03. Files: components/auth/auth-form/auth-decoration, layout/site-frame, app/layout, globals.css, docs. Criteria: giữ API/validation/CSRF/JWT/returnTo, không thêm OTP/OAuth/reset-password không có backend. PASS24 tests + lint/typecheck/build; real-browser Next/FastAPI/PostgreSQL16 test riêng register/login/logout/duplicate/wrong password/cookie/reload/CSRF/expiry/return URL, responsive320/390/768/1440 và visual desktop/mobile. Chỉ frontend thay đổi, không backend/DB/schema/env/Compose/dependencies, không tự làm task tiếp theo.


- [x] **UI-11 — Thu gọn auth theo phản hồi** | DONE. Dependencies: UI-10. Files: auth-form.tsx, auth-decoration.tsx, globals.css, docs. Mục tiêu/criteria: bỏ slogan hai bên, title chỉ Đăng nhập/Đăng ký; khung desktop tối đa470px, input/padding gọn, không đổi API. PASS lint/typecheck/production build/browser390+1440 title/no slogan/compact/no overflow. Frontend healthy, DB/config giữ nguyên. Dừng sau task.


- [x] **UI-12 — Tỷ lệ minh họa trang đăng nhập** | DONE. Dependencies:UI-11. Files: auth-form/auth-decoration/site-frame/globals.css/docs. Criteria: header nhỏ, bỏ hint chỉ ở login, túi to nghiêng có chiều sâu và slogan theo yêu cầu, voucher to; register logic/design giữ nguyên. Test lint/typecheck/build/browser390/768/1440, register hint còn, DB/config bảo toàn PASS. Không đổi API/dependencies/schema/data.


- [x] **UI-13 — Login theo ảnh gốc** | DONE. Dependencies:UI-12/P4-03. Files: auth-form/login-reference-art/globals.css/public image/docs. Mục tiêu: giữ artwork từ ảnh người dùng bằng clip hai bên, form HTML thật căn theo mẫu, header/logo/help/account và social row. Không phone-login/forgot reset/OAuth backend: social disabled, help giải thích. PASS lint/typecheck/build/24 tests, browser390/768/1672 và screenshot, DB/config bảo toàn. Không thay registration hay tự làm task tiếp.


- [x] **UI-14 — Register theo ảnh mới** | DONE. Dependencies:UI-13/P4-03. Files: auth-form/register-reference-art/register-footer/site-frame/globals.css/public image/docs. Criteria: search header thật, artwork bên trái/form bên phải/footer gọn, giữ API/auth, họ tên bắt buộc/phone optional, không OTP/OAuth giả; social disabled. PASS24 tests/lint/typecheck/build, real backend+PostgreSQL16 isolated E2E, browser390/768/1672 layout/search/footer và no overflow. Chỉ cập nhật frontend, DB/config giữ nguyên, dừng sau task.


- [x] **UI-15 — Trang đăng ký Seller theo ảnh** | DONE (10/11/2026). Dependencies: P6-01. Mục tiêu: Kênh người bán mở thẳng form, header gọn/search/login/register; bố cục xanh nhạt/3D shop trái/form phải và benefits theo mẫu; API thật, giữ ownership/session/CSRF/recovery. Files: seller registration/header/icons, shop dashboard, site frame/header, CSS/illustration, slug helper/tests/docs/seller-registration-ui.md. PASS45 frontend tests/lint/typecheck/build; browser thật guest form/login return/PENDING submit/slug auto+custom409/owner dashboard/patch/response loss recovery/503-retry/expiry; visual/responsive320/390/768/1100/1440/1672. Frontend Docker healthy, live direct link/form/asset/login return không shop POST cho guest PASS; PostgreSQL/env/volume/network giữ nguyên. Không backend/schema/Compose/env/dependency changes hoặc shipping/phone storage giả; dừng sau UI-15.

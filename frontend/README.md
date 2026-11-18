# coco frontend

UI-15 mới nhất: **Kênh người bán** mở thẳng form `/kenh-nguoi-ban`, không dropdown/trang giới thiệu trung gian. Header gọn/search/auth, artwork shop3D trái/form phải và benefits xanh nhạt theo ảnh. Guest Continue dẫn login returnTo; người dùng có shop tiếp tục dashboard. Form dùng API P6-01, tự gợi ý slug/có sửa, SĐT account chỉ đọc. [Hướng dẫn đăng ký Seller theo ảnh](../docs/seller-registration-ui.md).

P6-01 mới nhất: `/kenh-nguoi-ban` có đăng ký shop PENDING, xem/sửa hồ sơ và bốn trạng thái. Link từ header/tài khoản, login returnTo, API thật/no-store/CSRF/projection theo owner, loading/empty/error/retry và phục hồi mất response bằng đọc lại hồ sơ. [Hướng dẫn gian hàng](../docs/seller-shop.md). Sản phẩm/tồn/đơn Seller và duyệt Admin thuộc các task sau.

P5-04 mới nhất: `/tai-khoan/don-hang` có lịch sử phân trang và chi tiết `/tai-khoan/don-hang/{id}`, snapshot và trạng thái riêng mỗi shop, chỉ đơn của tài khoản đang đăng nhập. API thật, loading/empty/error/retry và responsive. Liên kết từ tài khoản/checkout. [Hướng dẫn đơn Buyer](../docs/buyer-orders.md). Hủy đơn/state machine ở P6-05; các ghi chú chưa triển khai phía dưới là lịch sử.

P5-03: `/gio-hang` → `/thanh-toan` có chọn địa chỉ/review nhiều shop/COD/đặt hàng qua API thật. Intent tối thiểu giữ sessionStorage theo user, cùng key qua lỗi/reload, chỉ xác nhận theo response server. [Hướng dẫn checkout UI](../docs/checkout-ui.md).

10/11/2026: đăng ký kiểm mật khẩu9–128 ký tự, có A–Z/0–9/ký tự đặc biệt và hiện gợi ý ngay dưới ô nhập. Login không buộc complexity mới cho tài khoản cũ. Backend checkout P5-02 đã có; trang/nút checkout vẫn chờ P5-03, không giả thành công.

P5-01: `/gio-hang` dùng API thật, nhóm theo shop, cập nhật số lượng/xóa; trang chi tiết có Thêm vào giỏ, header đọc số dòng sản phẩm. Không localStorage/cart mock; guest cần login. [Hướng dẫn giỏ hàng](../docs/cart.md). Checkout vẫn chưa mở, nút disabled, `/thanh-toan` vẫn preview.

P4-04: `/tai-khoan/dia-chi` có danh sách, thêm/sửa/xóa và đặt mặc định qua API thật. Liên kết từ trang tài khoản; guest đăng nhập rồi quay lại, loading/error/empty/retry, không lưu địa chỉ vào browser storage. Xem [hướng dẫn địa chỉ](../docs/addresses.md) và [hướng dẫn auth UI](../docs/auth-ui.md). Những mục UI/P3 bên dưới là lịch sử; đăng ký/đăng nhập/đăng xuất đã triển khai P4-03.

UI-07: thay banner riêng trang danh sách `/san-pham` bằng `components/catalog-banner.tsx` và ảnh `public/images/coco-catalog-banner.png` (artwork image_gen). Tông kem/đào với copy “Chăm chút hôm nay. Rạng rỡ mỗi ngày.”, desktop chữ trái/ảnh phải; mobile ảnh dưới chữ. Banner homepage không đổi. [Prompt và đường dẫn ảnh](../docs/banner-assets.md) được lưu; artwork không thay ảnh sản phẩm thật. Kiểm tra tại localhost:3001/san-pham, Ctrl+F5. Sidebar/sort/API và dữ liệu DB giữ nguyên.

UI-06: danh sách có sidebar “Bộ lọc tìm kiếm” với Đơn vị vận chuyển, Dịch vụ & khuyến mãi. Các tên nhà vận chuyển chỉ là lựa chọn UI dự kiến, có nhãn Chưa kết nối và fieldset disabled; chưa liên kết đối tác hoặc gửi filter vào API. Dịch vụ/khuyến mãi tương tự. Thanh ngang `CatalogSortBar` có Phổ biến, Mới nhất, Bán chạy, Giá: Phổ biến/Bán chạy disabled Sắp có vì chưa định nghĩa ranking/API; không dùng newest giả làm ranking. Mới nhất dùng catalogHref, giá dùng router.push trong useTransition → URL → Next server → API thật, giữ q/danh mục/page_size và reset page1. Form sidebar giữ sort bằng hidden field. Source: components/catalog-sort-bar.tsx, catalog-extra-filters.tsx và catalog-browser.tsx.

## P3-04 — Danh sách API thật

`/san-pham` đã thay preview bằng Server Component `CatalogBrowser`. Header tìm kiếm, banner, các ô danh mục, footer và CTA Flash Sale/bán chạy dẫn đến route này. Giao diện header/banner của UI-05 được giữ nguyên; không thêm tài khoản hoặc thanh ngang bị người dùng bỏ. Tìm tên theo API ILIKE (chưa tìm không dấu), chọn 6 nhóm danh mục, sort newest/price_asc/price_desc, page size 12/24/48 và phân trang theo total API thật. Không có filter khoảng giá hoặc sort tên giả vì API chưa hỗ trợ.

URL giữ `q`, `danh-muc`, `sort`, `page`, `page_size`. Form “Áp dụng bộ lọc” dùng GET, không mang page nên đổi tìm kiếm/sort/size về trang1; category links qua catalogHref cũng reset trang1. Pagination giữ tất cả bộ lọc. URL có thể bookmark/reload/Back/Forward mà không mất trạng thái. Các query trùng/lỗi kiểu/overflow/sort không hợp lệ hiển thị lỗi; danh mục không có mapping không được âm thầm gọi API không lọc. Mapping ưu tiên slug unique, sau đó tên unique; không đoán ID nếu có tên trùng.

Ví dụ kiểm tra trình duyệt:

```text
http://localhost:3001/san-pham
http://localhost:3001/san-pham?q=serum&sort=price_asc&page_size=12
http://localhost:3001/san-pham?danh-muc=nuoc-hoa&page=2
```

Luồng: Browser GET danh sách → Next server parseCatalogQuery → getCategories/matchBeautyCategories → getProductPage → FastAPI GET /api/v1/products → SQLAlchemy READ ONLY → PostgreSQL. q/slug được encode; category_id thật luôn là string; sort/page/size validate trước fetch. Không tạo category/product khi DB rỗng. Trang tất cả dùng catalog public API, sidebar chỉ hiển thị 6 nhóm đã yêu cầu; lọc nhóm bao gồm descendants do backend xử lý. Không paginate/filter mock trong browser. Giá/số hàng/tổng đều từ API, không cộng số giả; pagination render số nút hữu hạn ngay cả total lớn.

Code chính `lib/catalog-query.ts`:

```typescript
if (["q", "category", "sort", "pageSize"].some(key => key in changes)
    && !("page" in changes)) next.page = 1;
```

`lib/catalog-api.ts` thêm getProductPage cho pagination; getProducts cũ giữ wrapper homepage 12 items, không phá contract sử dụng trước. Kiểm tra response echo page/page_size khi có, total không nhỏ hơn items/offset, không fallback mẫu khi HTTP/JSON/timeout sai. Suspense và retry router.refresh tái dùng; past-end có link về trang đầu, empty đúng không dữ liệu. P3-05 đã nối card live tới detail và shop thật. Auth/checkout/detail/shop API integration không thuộc P3-04.

Đã kiểm thử 14 unit/contract tests, lint/typecheck/build; Chrome fixture riêng có 50 records kiểm tra phân trang/search/filter/sort/Back/Forward/reload/reset, error/retry/loading/past-end/invalid URL, responsive390/768/1440, entry points và không browser gọi hostname API. Fixture không seed DB hoặc thay cấu hình Docker production. Real Docker backend hiện trả total0: danh sách thật empty, không banner preview/card mẫu và không lỗi JS. Không chạy lại backend suite vì backend không đổi.

Từ root chạy `docker compose build frontend` rồi `docker compose up -d --no-deps --wait frontend`; các lệnh npm/test bên dưới vẫn áp dụng. API ảnh vẫn null tới khi có delivery thật, placeholder rõ ràng. UI-04 ảnh sản phẩm thật vẫn chờ nguồn. P3-05 đã bỏ preview và layout nhãn cũ; detail dùng API thật.

UI-05: header đã bỏ Tài khoản, guest bar/câu “Khám phá tự do…” và nav danh mục ngang. Đăng nhập/Đăng ký nằm trên utility header cùng Thông báo/Hỗ trợ; bên dưới chỉ logo, search và giỏ hàng. Các auth menus vẫn là thông tin chức năng chưa mở. Danh mục thật trong homepage không bị xóa. `components/home/campaign-banners.tsx` thay hero cũ bằng một banner lớn bên trái và hai banner nhỏ bên phải (2:1), mobile xếp banner lớn trên hai ô nhỏ. Chữ Việt bằng HTML, ảnh local qua Next Image, link lọc danh mục thật. [Ảnh banner và prompt](../docs/banner-assets.md) ghi nguồn built-in image_gen; không dùng artwork này làm ảnh catalog hoặc giả khuyến mãi. Ảnh sản phẩm thật của UI-04 vẫn chờ người dùng cung cấp.

UI-04 đang thực hiện: bỏ dải 3 câu dưới banner, header xanh biển nhạt `#dff1ff`, 6 icon danh mục SVG mới ở `components/category-icon.tsx`, biểu tượng hoa/giọt sáng dùng chung tại `public/icon.svg` và `components/layout/brand-logo.tsx`. Favicon có version query để nhận logo mới. `lib/site-brand.ts` tập trung tên/tagline cho header/footer/metadata/hero/menu; tên đã được đổi thành coco theo lựa chọn người dùng. Người dùng sẽ cung cấp ảnh thật, nên chưa gán ảnh minh họa hoặc đổi dữ liệu API. Card ảnh thiếu chỉ được làm lại placeholder rõ ràng. Không tự chọn tên thay sau khi người dùng trả lời “tên khác”.

UI-03 mới nhất: palette xanh cobalt `#244ec9`, cam san hô `#ef6b43`, nền xanh trắng; banner gradient đồng bộ. Thanh khách có Đăng nhập/Đăng ký mở hướng dẫn chức năng chưa mở (không phải auth form/API). `components/home/shopping-highlights.tsx` thêm Flash Sale và Sản phẩm bán chạy bên dưới catalog, có minh họa và liên kết khám phá thật. Hiện hai khu dùng empty state vì API chưa có promotions hoặc sales ranking; không dùng latest products giả làm best sellers, không tạo discount/countdown hoặc dữ liệu bán giả. Cần task nghiệp vụ/API riêng để có các dữ liệu này sau khi thống nhất quy tắc; không suy ra được từ price hoặc inventory hiện tại. Backend/database và luồng catalog P3-03 giữ nguyên.

P3-03: Next.js App Router, TypeScript strict và Tailwind. Trang chủ `/` đã gọi API thật; giao diện lấy cảm hứng mua sắm Marketplace, giữ tông xanh/kem HealthBeauty. Header có tìm kiếm, điều hướng 6 danh mục và disclosure tài khoản/giỏ hàng báo chức năng chưa mở. Không có bộ đếm, đơn hàng hoặc đăng nhập giả.

UI-02 cập nhật header theo ảnh tham khảo với tông tím mận/cam đất, thêm Kênh người bán/Thông báo/Hỗ trợ và logo túi lá tự vẽ bằng SVG. Các menu mở hướng dẫn/thông tin thật về trạng thái chức năng, không giả thông báo hoặc dashboard đã tồn tại. Tìm kiếm vẫn gửi về homepage API thật. Không thay backend/database.

Font toàn site dùng `next/font/local` với `src/app/fonts/NotoSans-Variable.ttf`, đầy đủ dấu tiếng Việt; biến `--font-noto-sans` được áp dụng qua CSS theme và thay font serif ở tiêu đề nội dung. Icon ký hiệu trang trí vẫn có fallback riêng. Font tự host cùng app nên browser không gọi Google Fonts. Nguồn font: [Google Fonts / Noto Sans](https://github.com/google/fonts/tree/main/ofl/notosans); giấy phép SIL Open Font License lưu tại `src/app/fonts/OFL.txt`. Nếu còn cache giao diện cũ, dùng Ctrl+F5 tại localhost:3001.

## Chạy bằng Docker

Từ root repository, PostgreSQL và backend hiện hữu cần đang chạy:

```powershell
docker compose build frontend
docker compose up -d --no-deps --wait frontend
```

Mở http://localhost:3001. Không cần cài Node trên Windows nếu dùng Docker. Nếu Docker chưa có trong PATH, thay `docker` bằng `& "$env:LOCALAPPDATA/Programs/DockerDesktop/resources/bin/docker.exe"`. Chỉ cập nhật frontend, không recreate PostgreSQL hoặc thay volume/network.

## Chạy trực tiếp từ VS Code Terminal

Cần Node 24 và npm, backend tại http://localhost:8000:

```powershell
cd frontend
npm ci
$env:INTERNAL_API_URL = 'http://127.0.0.1:8000'
$env:NEXT_TELEMETRY_DISABLED = '1'
npm run dev -- --port 3002
```

Mở http://localhost:3002. Dùng cổng riêng vì Docker frontend đang giữ 3001, ứng dụng khác có thể giữ 3000. Không đổi root `.env`. Không có env/API thì UI hiển thị lỗi và nút thử lại, không đổi thành catalog rỗng hoặc sản phẩm mẫu. Build không cần kết nối API vì homepage render theo request.

## Frontend → API → database

Next.js Server Component `HomeCatalog` đọc `INTERNAL_API_URL`; trong Docker là `http://backend:8000`. Backend dùng SQLAlchemy/psycopg kết nối `postgres:5432`, schema `marketplace`. Browser không biết hostname Docker, không kết nối PostgreSQL hoặc đọc secret. Đây là server-side fetch, chưa cần thêm API proxy/CORS.

`src/lib/catalog-api.ts` chỉ được import runtime trong Server Components, validate public response, ID BIGINT và Decimal string; fetch `no-store`, timeout 5 giây, không tự đi theo redirect. Thiếu cấu hình, HTTP lỗi, timeout hoặc payload sai trả trạng thái lỗi chung; không lộ upstream body/host vào UI. Biến này không dùng prefix NEXT_PUBLIC_. Client card chỉ nhận projection các trường public cần hiển thị.

```typescript
const response = await fetch(new URL(path, origin), {
  cache: "no-store",
  redirect: "error",
  signal: AbortSignal.timeout(5000),
  headers: { Accept: "application/json" },
});
```

`src/components/home/home-catalog.tsx` lấy cây danh mục active, đối chiếu tên/slug với 6 khóa ở `src/lib/categories.ts`, rồi truyền category_id thật vào API sản phẩm. Không mặc định ID 1–6, không tạo danh mục trong DB. Danh mục chưa đối chiếu được hiển thị “Sắp cập nhật”. Chỉ lấy sản phẩm trong 6 nhóm được yêu cầu (backend bao gồm con/cháu). Một request categories rồi tối đa 6 request products song song; interleave theo danh mục, loại product_id trùng, tối đa 12 thẻ. Không phải catalog đầy đủ hoặc phân trang P3-04.

Header search dùng `/san-pham?q=serum`; category entry points dùng `/san-pham?danh-muc=nuoc-hoa` từ P3-04. Homepage vẫn hiểu URL root cũ để không phá bookmark trước đó. Chỉ tìm tên không phân biệt hoa/thường theo contract API; chưa hỗ trợ không dấu. Category/filter ID lấy từ server, không nhận taxonomy key làm DB ID. Card dùng summary thật và liên kết chi tiết/shop P3-05; giỏ hàng thuộc task riêng.

Suspense hiển thị skeleton khi tải. API thành công nhưng không có hàng hiển thị empty state thật. API lỗi hiển thị “Chưa thể tải sản phẩm” và `router.refresh()` qua nút thử lại. Không hiển thị một phần grid khi một request danh mục lỗi. Ảnh null hoặc tải lỗi dùng placeholder; không dùng hình bao bì mẫu thay ảnh thật. Tiền format từ Decimal string bằng BigInt phần nguyên để tránh mất chính xác; không dùng phép tính giá float. Ảnh API hiện null đến task S3.

## P3-05 và UI-08 — Trạng thái hiện tại

Không còn detail preview hoặc module preview-catalog/ProductArt/ProductCard. Thẻ public dẫn tới `/san-pham/{product_id}` và `/gian-hang/{shop_slug}`. Chi tiết có gallery keyboard/ảnh null/lỗi, giá/tồn/SKU/mô tả thật; shop có tìm kiếm/lọc/sort/phân trang trong shop. Server helper validate và chỉ project public fields. 404 tài nguyên giữ HTTP404; lỗi API có retry. Root loading.tsx đã bỏ để tránh stream200 trước notFound; Suspense cục bộ và NavigationHint vẫn hiển thị loading.

UI-08: header xanh/logo coco, menu6 danh mục, banner túi mua sắm SVG và CTA về catalog, lối tắt về đúng section, footer FAQ native details. Homepage không lặp category tiles. Không tạo ưu đãi/countdown/giá/ảnh sản phẩm giả. Auth/cart/seller chưa mở nghiệp vụ; panel giải thích hiện trạng. Mã giảm giá/Flash Sale/bán chạy có empty state. API thực hiện tại không có public products nên không có thẻ sản phẩm thật hiển thị.

Luồng: Browser → Next server → FastAPI `/api/v1/categories`, `/products`, `/products/{id}`, `/shops/{slug}` → PostgreSQL qua backend. Không dùng hostname Docker ở browser, không kết nối DB từ frontend. Shop list gửi shop_id thật và giữ URL shop khi đổi filter/page. Không thay backend/schema ở UI-08.

Mở http://localhost:3001, Ctrl+F5; thử6 danh mục, search và lối tắt/footer; đối chiếu API http://localhost:8000/docs. Khi có dữ liệu thật, bấm tên sản phẩm rồi tên gian hàng để kiểm tra đường dẫn liên kết. Không seed DB để minh họa. Build/update từ root: `docker compose build frontend` rồi `docker compose up -d --no-deps --wait frontend`.

## Kiểm thử

Từ frontend:

```powershell
npm run test
npm run lint
npm run typecheck
npm run build
```

21 unit tests dùng node:test và TypeScript dev dependency hiện có, không thêm thư viện ứng dụng: cấu hình server, contract/HTTP/JSON/timeout, query encoding, BIGINT/Decimal, URL ảnh, mapping danh mục, URL state/reset/boundaries và pagination. Build và typecheck chạy độc lập với ESLint. Browser QA P3-03/04 chạy desktop/tablet/mobile, tìm kiếm/danh mục, loading/empty/error/retry, keyboard và preview isolation. Kịch bản có sản phẩm/lỗi dùng fixture HTTP server và Next process riêng ở cổng ngẫu nhiên, không thay API trong Docker hoặc ghi PostgreSQL. Browser thật tại :3001 kiểm tra empty state từ backend/DB hiện hữu.

Kiểm tra thủ công: mở `/`, tìm “serum”, chọn danh mục và xóa bộ lọc. Mở http://localhost:8000/docs để so dữ liệu API. Khi DB chưa có catalog public, homepage rỗng là đúng; không cần seed để tiếp tục phát triển. Account/cart có thể mở thông tin bằng chuột hoặc Enter, chưa hỗ trợ nghiệp vụ.

## Cấu trúc chính

- `src/app/page.tsx`: banner, nội dung tĩnh, Suspense và query trang chủ.
- `src/components/layout`: header/footer chung.
- `src/components/home`: catalog API, card public, retry và loading.
- `src/lib/catalog-api.ts`: fetch/validation server; `categories.ts`: taxonomy hiển thị và VND.
- `tests/catalog-api.test.mjs`: kiểm thử contract/failure.
- `src/app/san-pham/[slug]/page.tsx`: chi tiết ID thật; `src/app/gian-hang/[shopSlug]/page.tsx`: shop API thật.
- `src/components/product-gallery.tsx`, `shop-avatar.tsx`: ảnh thật/fallback; `home/campaign-banners.tsx`: menu6 nhóm/banner SVG/lối tắt.

Dockerfile standalone, runtime USER node, không đổi ở P3-03. Dependencies/lock giữ nguyên; package.json chỉ thêm script test. Công cụ portable/screenshot ở D:/HealthBeauty chỉ phục vụ phiên làm việc, không được hardcode vào source app. Cảnh báo ESLint 9 hết hỗ trợ và các moderate dev-toolchain đã ghi ở progress từ trước; chưa nâng dependency trong task UI này.


## UI-09 — Trang danh sách/chi tiết và bố cục giỏ/checkout

Danh sách `/san-pham` và chi tiết `/san-pham/{product_id}` có menu6 danh mục và giao diện xanh đồng bộ, vẫn dùng API thật. `/gio-hang` và `/thanh-toan` là **bản xem trước bố cục**, chưa kết nối giỏ, tài khoản, địa chỉ hay checkout transaction. Không nhập PII/đặt hàng/tổng tiền mẫu. Chỉ COD mô phỏng sẽ được tích hợp theo P5; không hỗ trợ thẻ/ví/QR. Header giỏ có link đến preview, có thể đi tới checkout và quay lại catalog.

Kiểm tra http://localhost:3001/gio-hang và http://localhost:3001/thanh-toan, responsive và liên kết quay lại. Chạy root: `docker compose build frontend`, `docker compose up -d --no-deps --wait frontend`. Frontend: `npm run test`, `npm run lint`, `npm run typecheck`, `npm run build` đều PASS (21 tests); browser fixture và real UI PASS. DB/config giữ nguyên. P4/P5 vẫn chưa thực hiện.


## P4-03 — Giao diện tài khoản

Đã có /dang-ky, /dang-nhap, /tai-khoan và đăng xuất trên header; API thật qua proxy same-origin, JWT HttpOnly cookie, CSRF, safe return URL. Xem [hướng dẫn](../docs/auth-ui.md). Cần JWT secret của backend để bật auth local; thiếu khóa UI báo chưa sẵn sàng, không fake login. Root .env và DB giữ nguyên;24 tests/lint/typecheck/build và browser E2E với PostgreSQL16 riêng PASS. Chưa làm địa chỉ, giỏ thật hoặc dashboard.


## UI-10 — Cập nhật thiết kế

Auth pages dùng SiteFrame với header riêng, không storefront header/footer; form giữa nền xanh và SVG túi/quà/coupon hai bên. Mobile bỏ artwork hai bên, giữ input/label/focus/loading/error đầy đủ. /tai-khoan và các trang mua sắm giữ chrome cũ. API/CSRF/JWT/validation/returnTo P4-03 không đổi. Giữ đăng nhập email; chưa OTP/phone-login/OAuth/reset-password. Lint/typecheck/build,24 tests và E2E PostgreSQL16 riêng PASS. Ctrl+F5 ở /dang-nhap hoặc /dang-ky để xem.

## BRAND-01 / P6-02 (10/11/2026)

BrandLogo dùng `/images/coco-logo.png` nguyên ảnh người dùng cung cấp. `/kenh-nguoi-ban/san-pham` có list/create/edit/hide/search/filter/pagination qua proxy API thật, ownership và shop APPROVED kiểm ở server; form không chỉnh tồn sau tạo hoặc bật lại sản phẩm ẩn. Có response-loss read recovery, session expiry và loading/error/empty. Xem [seller-products.md](../docs/seller-products.md). PASS48 tests/lint/typecheck/production build và E2E PostgreSQL riêng. S3 ảnh/chỉnh tồn/đơn Seller chưa thuộc task này.

## BRAND-02 / P6-03 — Chuẩn bị ảnh

BrandLogo dùng PNG trong suốt/cao hơn. Seller có ProductImages panel, upload presigned POST không credential, primary/sort/reference-only delete; Next proxy allowlist ID/resource/method/CSRF. Chưa bucket nên upload disabled đúng flag API, không mock thành công. Xem [s3-images.md](../docs/s3-images.md);52 tests/lint/typecheck/build PASS, S3 thật chờ cấu hình.

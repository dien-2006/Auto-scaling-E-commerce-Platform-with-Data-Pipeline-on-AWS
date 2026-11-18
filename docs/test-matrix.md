# Ma trận regression tích hợp — P8-01

Ngày 11/11/2026. Phạm vi API và quyền trên PostgreSQL16 test riêng; không thay thế E2E trình duyệt P8-02 hoặc đo tải P8-03. P8-01 còn IN_PROGRESS vì P6-03 chưa có bucket thật.

## Yêu cầu và evidence

Các đường dẫn dưới đây tính từ `backend/tests/`. PASS chỉ áp dụng lượt full suite được ghi trong progress, không suy ra tích hợp với dịch vụ bên ngoài.

| Yêu cầu | Evidence kiểm thử | Giới hạn |
| --- | --- | --- |
| FR-B01 đăng ký/login/logout | test_auth.py, test_auth_postgres.py, test_checkout_postgres.py::test_new_nine_character_password_and_legacy_login | Không đổi mật khẩu thật |
| FR-B02 catalog/shop/detail | integration/test_public_catalog.py, test_products.py | Ảnh thật còn chờ S3 |
| FR-B03 tìm kiếm/lọc/phân trang | integration/test_public_catalog.py::test_search_literals_sorting_pagination_and_shop_filter | Không đo tải |
| FR-B04 giỏ nhiều shop | test_cart_postgres.py | Giỏ không giữ tồn |
| FR-B05 địa chỉ/checkout COD | test_addresses_postgres.py, test_checkout_postgres.py | COD mô phỏng |
| FR-B06 lịch sử/snapshot/hủy | test_orders_postgres.py, test_seller_orders_postgres.py | Vận chuyển mô phỏng |
| FR-S01/02 shop | test_seller_shop_postgres.py | Duyệt qua Admin |
| FR-S03 sản phẩm/ảnh | test_seller_products_postgres.py, test_product_images_postgres.py, test_storage_images.py | SDK double; NOT RUN S3 thật |
| FR-S04 tồn | test_inventory_postgres.py | Kiểm tra delta/precondition và đua checkout |
| FR-S05 đơn shop | test_seller_orders_postgres.py | Transition/hoàn tồn đúng một lần |
| FR-A01 users | test_admin_users_postgres.py | ADMIN chỉ xem, theo quyết định bỏ qua khóa Admin |
| FR-A02 shop | test_admin_shops_postgres.py | Không mở lại shop khóa |
| FR-A03 sản phẩm | test_admin_products_postgres.py | Không bật lại sản phẩm ẩn |
| FR-A04 danh mục | test_admin_categories_postgres.py | Cycle/slug race, ancestor visibility |
| Liên thông kiểm duyệt → đơn cũ | integration/test_workflow_regression.py | Ba trường hợp product/shop/category |
| Nghiệm thu FR-A01–04 theo bảng người dùng | integration/test_z_admin_requirements.py | Admin-only; USER lock/unlock; shop approve/reject/lock; hidden search; category link/delete405. Tài khoản ADMIN chỉ xem theo quyết định trước |

## Ma trận quyền

| Resource | Guest | USER/Buyer | Owner Seller | ADMIN ACTIVE |
| --- | --- | --- | --- | --- |
| Catalog công khai hợp lệ | Được đọc | Được đọc | Được đọc | Được đọc |
| Giỏ/địa chỉ/đơn Buyer | 401 | Chỉ của mình | Chỉ dữ liệu Buyer của mình | 403 COMMERCE_FORBIDDEN, kể cả tài nguyên cũ |
| Tạo/hồ sơ đăng ký shop | 401 | Shop của mình | Shop của mình | 403 COMMERCE_FORBIDDEN |
| Sản phẩm/tồn của Seller | 401 | Không phải owner bị từ chối | Shop APPROVED của mình | Không bypass ownership |
| Xử lý đơn shop cũ | 401 | Không phải owner bị từ chối | APPROVED/LOCKED, user ACTIVE | Không bypass ownership |
| Admin users/shops/products/categories | 401 | 403 | 403 | Được theo contract |
| Protected API khi user LOCKED | 401 nếu không phiên | Bị từ chối | Bị từ chối | Không thay chính sách khóa ADMIN |

Evidence: test_access_postgres.py và các bộ `test_*_postgres.py` tương ứng kiểm tra role/status hiện tại trong DB, ownership, CSRF, lỗi commit và rollback. Không dùng giao diện làm ranh giới quyền.

## Transaction và cạnh tranh

- test_checkout_postgres.py: hai Buyer tranh đơn vị cuối; cùng key đồng thời chỉ một order; key tách theo Buyer; lỗi giữa transaction/COMMIT rollback; kiểm lại trạng thái dưới khóa.
- test_inventory_postgres.py: hai adjustments và adjustment đua checkout, stale quantity không ghi đè.
- test_seller_orders_postgres.py: Buyer/Seller hủy đồng thời, confirm đua cancel, không hoàn tồn hai lần.
- test_admin_categories_postgres.py: reparent đồng thời không tạo cycle; tắt cha đua checkout; cây mới được kiểm sau exclusive lock.
- integration/test_workflow_regression.py: đặt hai shop → Admin ẩn sản phẩm/khóa shop/tắt cha → public404 nhưng replay cùng key và đơn cũ giữ nguyên → Admin khác không đọc đơn → owner hủy hai lần chỉ hoàn tồn shop mình một lần.

## Chạy lại an toàn

Tạo PostgreSQL16 dùng tmpfs, database đúng `marketplace_test`, port loopback riêng; không mount volume nghiệp vụ. Cấp `MARKETPLACE_TEST_DB_HOST/PORT/NAME/USER/PASSWORD` bằng môi trường tiến trình, không ghi secret vào tài liệu. Từ backend chạy `uv run --locked pytest -q`; pytest thêm `tests` vào pythonpath để dùng các fixture chung. Bộ catalog pristine chạy trước workflow theo thứ tự collection mặc định; chạy chọn riêng workflow cũng hợp lệ trên DB test mới. Không chạy đảo thứ tự hai bộ trên cùng schema đã có fixtures.

Metadata audit chỉ chạy khi cấu hình `MARKETPLACE_AUDIT_DB_*`, dùng transaction READ ONLY; thiếu cấu hình sẽ SKIPPED, không được báo PASS toàn bộ. Sau chạy, dọn đúng container test mình tạo và đối chiếu PostgreSQL ID/start/mount/config, root .env hash, volume/network trước/sau. Không chạy create_all/seed/migration trên DB nghiệp vụ.

NOT RUN ở P8-01: S3 upload/HEAD/conditional PUT/CORS/IAM/delivery thật; load/nhiều tiến trình thật P8-03; HTTPS và điện thoại vật lý. Không đánh dấu P8-01 DONE trước khi dependency S3 và evidence tương ứng hoàn tất.

Cập nhật P8-02 (11/11/2026): hành trình browser không bucket đã PASS qua tests/e2e/journey.cjs, Next production → FastAPI → PostgreSQL16 test riêng. Guest tìm/detail placeholder → Buyer keyboard add/địa chỉ/checkout → Seller hoàn tất → Buyer theo dõi → Admin duyệt/ẩn/khóa; empty/loading/503/recovery/expiry và bảy màn hình/bốn viewport. Chi tiết và giới hạn tại [E2E README](../tests/e2e/README.md); không thay thế S3 thật hoặc load test.

Cập nhật P8-03/04: PASS445 backend full sau Pillow13 và4 test decoder JPEG/PNG/WebP/TIFF;1 Pydantic alias warning trong concurrency test, không fail/skip. PASS77 frontend, E2E/header, hai Uvicorn process/2.000products/120reads/8concurrent, cùng key chỉ1order và lastunit không oversell. Graceful idle shutdown một process còn process khác ready; DB test outage live200/ready503. [Performance](performance.md), [security/handoff](handoff.md) ghi chính xác audit và phần còn thiếu; S3/production gates vẫn NOT RUN.

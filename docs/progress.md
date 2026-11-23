# ENV-DOCKER-RELEASE — DONE local runtime (19/11/2026)

Người dùng yêu cầu một file env, Docker image riêng frontend/backend và hướng dẫn đưa gì lênGit. Đã kiểm envnames/conflicts không invalues; merge4private files vào root.env bằng append giữ nguyên prefix/keyvalues, thêm COCO_IMAGE_TAG. Backup bản gốc ngoài repo D:/HealthBeauty/private-config-backups/unified-env-20261118, sau kiểm hash/equality và apphealthy mới bỏ4filebackendprivate; projectchỉcòn1private.env. Khôngrotatekeys hoặc đổiDBpassword. Root.env.example chỉplaceholder/các optionalcomment; service templates giữ làmlegacyreference. README/backendREADME vàdocsAuth/S3/OTP/commerce/handoff trỏrootenv/guide mới.

Compose bỏpostgresenv_file (không cấpappsecrets vàoDB khi recreate sau này), backendđọcroot.env, frontendgiữpublicenvexplicit. So sánhresolvedconfigtrước/sau: mọienvbackend/frontendcũ đúngynguyên, PG/Rediscommand/mount/network/ports khôngđổi. Settings từnewimagehợplệ OTPtrue/emailconfiguredtrue. Build coco-backend:2026.11.18/coco-frontend:2026.11.18 và chỉupbackend/frontend--no-depshealthy; PG/RedisID/start/mount giữnguyên. Homepage200/readiness200/OTPoptionsenabled+emailtrue; JWT/OTP/S3/SMTPvalues giữnguyên.

scripts/package-images.ps1 build/export2tar riêng/version/pathvalidated/refuseoverwrite/checklastExitCode/manifest/SHA256/copypublicconfigguide, khôngcopyprivateenv. Đã chạy thậtSkipBuild: backend77.2MiB frontend101.8MiB, linux/amd64. Exportdir artifacts/docker/2026.11.18 có2tar,manifest,SHA256SUMS,Compose,rootexample,README. SHA256/filebytes/imageIds/configcopy đốichiếuPASS; dockerload2archivesPASS. Scan exact6+secretvalues hiện tại trong434Gitcandidates và toàn decompressedOCIarchive layersPASS (không insecret); gitignore.env/tarsPASS. Gitindextrống, khôngstage/commit/push. Khôngbackupdatabasevàobundle, noDBDDL/writes/providerwrites/AWSregistryupload. Database/S3data phải chuyển riêng khi đổi máy; hướngdẫn ghi rõ khôngtựkhởitạoschema/seed, giữ25bảng.

Khôngchạy lại backend/frontendunit vì khôngđổiappcode; kiểmconfig thực, Dockerbuild và runtimesmoke làvalidationchính. Root.envhash thayđổitheoyêucầumerge, chỉcácgiátrịvàprefixcũđượcbảotoàn (không tuyênbốhashgiữnguyên). Docs/docker-release.md cólệnhpackage/load/up/Gitaddreview và phânbiệt source với image/data; artifactsbịignorekhôngđưaGit.

# RESET-REFERENCE — DONE local runtime (18/11/2026)

Theo ảnh Khôi phục mật khẩu COCO an toàn: thêm ResetReferenceArt dùng SVG clipping hai bên của ảnh được sao chép nguyên vào public/images/coco-reset-reference.png, loại hoàn toàn phần form/header/footer trong ảnh. Form trung tâm vẫn HTML thật. SiteFrame nhận quen-mat-khau là auth page, dùng header gọn có logo/help/account và ResetFooter với link giới thiệu/hỗ trợ/sản phẩm có thật; không tạo trang chính sách giả. Nền xanh/card bo góc/rays bên tiêu đề, inline OTP + Gửi mã, responsive bỏ minh họa ở mobile. Chỉ nhận email theo yêu cầu Brevo đã chốt. Giữ xác minh server rồi mới hiện PasswordFields; nút bước cuối Đặt lại mật khẩu. Giữ proof/CSRF/API/60s/returnTo, không sửa backend/schema/config.

PASS 97 frontend tests, ESLint/typecheck/production build/Docker frontend build. Browser fixtures reset320/390/768/1672: email-onlysend, mã sai không hiện password, mã đúng mới hiện, complete qua proof, expiry/resend/no auto send/proof expiry; registration1440/390 và login centered regression PASS. Đã xem ảnh desktop/mobile, chỉnh decoration sát tiêu đề và vị trí card mobile. QA helper/ảnh ngoài repo D:/HealthBeauty/reset-reference-ui* và reset-reference-live.cjs. Chỉ frontend Compose --no-deps --wait healthy; live GET4viewport kiểm compactheader/footer/inlineOTP/noPasswordBeforeProof/returnTo/nooverflow PASS. Backend/PostgreSQL/Redis ID/start/mount giữ nguyên, root .envhash giữ nguyên; không gửi OTP hoặc đổi mật khẩu tài khoản thật. Backend test NOT RUN vì chỉ thay giao diện. Không thêm schema/bảng hoặc OAuth/SMS.

# SOCIAL-ICONS — DONE local runtime (18/11/2026)

Người dùng chọn chỉ sửa giao diện/icon. Thêm Apple SVG còn thiếu bằng path đang dùng ở login, Google SVG đa màu thay chữ G, giữ Facebook; CSS scope chuẩn hóa nút cao 48px/icon 22px/căn giữa. Màn hình 320px xếp icon trên nhãn để không tràn. Giữ disabled/title/note chưa hỗ trợ, không bật OAuth hay thay API/OTP/config/schema.

PASS ESLint/typecheck/production build/Docker frontend build. Browser 1440/390/320 kiểm đủ ba icon, disabled, khung đều và không tràn; đã xem ảnh 390. Chỉ frontend up --no-deps --wait healthy; QA live ba viewport PASS. Backend/PostgreSQL/Redis ID/start/mount và root .env hash giữ nguyên; không ghi DB/gửi mail. Không viết test mới cho icon/styling; helper/ảnh ngoài repo tại D:/HealthBeauty/social-ui*.

# OTP-STEPS-REGISTER-LOGIN — DONE local runtime (18/11/2026)

Theo ảnh/yêu cầu mới, sửa chồng text/icon; reset phải xác minh đúng mã rồi mới đến mật khẩu mới; khôi phục đăng ký theo mẫu hai cột. Bổ sung sau đó: căn chữ Đăng nhập trong nút. Tái dùng RegisterReferenceArt/ảnh đã có, giữ logo hiện tại; không thêm schema/bảng/cột.

API cấp mã REGISTER/RESET chỉ nhận email (không cần/không lưu password pending), OTP vẫn60s/5attempts/rate/cooldown cũ. `/otp-verify` chỉ nhận UUID/code, consume code nguyên tử rồi kiểm email/user/credential, trả proof256bit/300s. Redis chỉ lưu proof bằng HMAC key; token private/no-store và client giữ memory. `/otp-register` cần proofREGISTER/full_name/password, cố địnhUSER/email lấy từproof; `/password-reset` cần proofRESET/new_password, kiểm lạiACTIVE/email/credentialstamp rồi Argon2id update, vô hiệu JWTstampcũ và clearcookie. Proof action-bound/one-use, consume trướcSQL; DBfail burnsproof; không claim distributed transaction. Grant không được dùng chéo endpoint hoặc replay; proof cũ/malformed bị chặn. Chặn schemaextra new_password trên verify, nên không thể bỏ bước chỉ bằng client.

UI resetemail→OTP→serverproof→newpassword/confirm (5min đặt mới sauverify, OTPgiữ1min); password không có trongDOM trướcproof, mã sai giữbước2, gửi lại thủcông khi60s, expiredproof không cho submit. Register email+inline OTP/send, name, password/confirm/showtoggle, submit; wrongOTP khôngtạouser. Socialproviderchưahỗtrợ vẫndisabled/có note, không giảOAuth. Xóa CSSbackgroundicons inherited ởscope mạnh hơn và thêminlineSVG/padding49px để không đèchữ. Signupdesktop hai cột/ảnh gốc masked, mobile card; loginbuttonflexcenter/padding0/lineheight1.2, đo Range offsets đạt trên2viewport.

PASS 544 full backend PostgreSQL riêng trước minorfailclosedget; 25 OTP targeted bản cuối (519 deselected) gồm schema25, one-use/concurrentproof, OTP/TTL/grant expiry, wrongpurpose, verify chưađổiPW, API khôngproof422/randomproof400, resetlocked, SQLfail/Redisfail/ses/smtpdoubles. PASS 97frontend/lint/typecheck/build, Ruffcheck/format. Browserfixture390/1440 đủ signupinline/emailonlysend/wrongcode/success/nostorage, resetpasswordhidden/wrongcode/verifythencomplete, expiry/resend/noauto/proofexpiry, showpassword, loginlabelcenter. Xem screenshotregisterdesktop/mobile/resetcode và livelogin, chỉnh socialnote vào trongcard. QA helper/artifact ngoài repo D:/HealthBeauty/otp-staged-ui* và otp-live-readonly.cjs.

Build hai images và cập nhật backend/frontend bằng Compose --no-deps --wait healthy. Preflight Settings từimage mới hợp lệ, OTPenabled/emailconfigured true; không in/đổi SMTPkey/envOTP. Live GET dang-ky/quen-mat-khau/dang-nhap 1440+390 PASS/nooverflow; OpenAPI verifykhôngpassword/resetproofrequired, POSTnewendpoints thiếuOrigin/CSRF403. Không gửi OTP/email thật, tạo tài khoản thật hoặc reset password thật để test. PostgreSQL và Redis ID/start/mount giữ nguyên, root .envhash giữ nguyên, READONLY25marketplace/0auth_security. Cấu hình Brevo hiện đã có; không còn trạng thái chưa cấu hình của lịch sử trước đây. Cần tải lại trang khi đang giữ tab JSphiênbảncũ, mã cũ đang chờ có thể yêu cầu lại. Docssetup/APIcontract cập nhật luồng mới.

# OTP-BREVO — chỉ email, giữ nguyên 25 bảng (18/11/2026)

Người dùng thay yêu cầu: không thêm bảng; đăng ký email phải xác nhận, có quên mật khẩu OTP email, dùng thử Brevo. Phương án 2 bảng auth_security và email nullable trước đây bị hủy. File SQL proposal cũ chỉ còn chú thích rút lại; không có migration mới. User ORM email trở lại NOT NULL, bỏ OTP_SCHEMA. Không sửa database/schema/credentials người dùng thật.

OTPStore dùng redis6.4 (uv.lock đã cập nhật), Lua atomic để cấp mã/rate limit/đếm sai/consume; TTL Redis server 60 giây, 5 lần sai, 5 yêu cầu/email/mục đích/giờ và 100/peerIP/giờ; cooldown 60 giây. HMAC code riêng, pending chỉ Argon2 hash, không trả/log OTP. Consume xóa proof trước SQL transaction, lỗi DB làm mất proof để tránh replay; không khẳng định hai hệ thống commit nguyên tử. Advisory contact lock và unique email giữ chống tạo trùng; reset credential stamp/LOCKED policy giữ nguyên. Delivery muộn không hồi sinh proof. Redis thiếu/lỗi fail closed, readiness kiểm Redis khi OTP enabled. Client Redis không tự retry mutation.

OTPRequest chỉ EMAIL/default EMAIL, SMS 422; delivery SMS không hoạt động dù còn cấu hình cũ, options sms=false. UI chỉ email, không có selector SĐT; AuthGate dùng login email thông thường có credential stamp. Đăng ký USER chỉ sau OTP; quên mật khẩu email mới/cũ cần mã trước đổi mật khẩu. Alias otp-login chỉ nhận email. Giữ CSRF/Origin/Argon2/role/ownership.

Brevo qua SMTP relay smtp-relay.brevo.com:587 STARTTLS, SMTP login/key riêng với verified sender. `.env.otp` giữ secret/giá trị người dùng đã điền, chỉ bổ sung mặc định Brevo và Redis; flag false đã kiểm tra, không in bí mật. `otp.env.example`, `docker-compose.otp.yaml` Redis dedicated/no host port/no volume/no persistence/maxmemory noeviction, hướng dẫn tài khoản/giới hạn free300email/ngày/config/activate/errors trong `docs/otp-setup.md`, contract/README đồng bộ. Chỉ build, không up app/cache thật và không gọi gửi Brevo thật.

PASS: 538 full backend trước bổ sung config/rate test (2 cảnh báo Pydantic có sẵn); 21 OTP targeted trên bản cuối với Redis thật và PostgreSQL marketplace_test riêng, 519 deselected; tổng collection540. Test kiểm đúng25bảng/emailNOTNULL/khôngauth_security, mã60s/hết hạn/5sai/one-use/concurrentverify/senderfailure/oldsessionrevoked/locked/reset/cooldown/resend/rate5+100/Redisdown/DBfailureburnsproof/lateSMTP không hồi sinh mã. SMTP/SES dùng doubles; Brevo SMTP host/587/TLS và khôngSMS được kiểm tra. Dọn chỉ test DB/Redis đã tạo.

PASS 97 frontend tests/lint/typecheck/build, Ruff check/format, uv lock check49packages, Docker backend/frontend builds, compose config --quiet overlay. Browser process riêng + mock API: 390px đăng ký email khôngSMSselector, mã sai/60s/success/no password storage; desktop1440 reset/expiry/resend không tự gửi; login email/link Quên mật khẩu. Đã xem ảnh thành công mobile. QA helper/screenshot nằm ngoài repository tại D:/HealthBeauty/otp-brevo-ui*.

READ ONLY live: 25 bảng marketplace / 0 auth_security / users.email nullable=NO. PostgreSQL và 2 app giữ ID/start/mount, root .env hash giữ nguyên; cả ba healthy. Chưa kích hoạt OTP/chưa gửi mail thật/chưa tạo user hoặc reset password thật. Cần cấu hình Brevo và khởi chạy Redis rồi bật/deploy theo hướng dẫn. Không cần duyệt hay chạy SQL cho yêu cầu mới. IN_PROGRESS chỉ vì gửi thật/kích hoạt còn chờ cấu hình.

# OTP-AUTH — chuẩn bị code, chưa kích hoạt (18/11/2026)

Người dùng yêu cầu quên mật khẩu OTPemail và đăng kýemail/phoneOTP; xác nhận chưa códịchvụ, yêu cầu chuẩnbịcode+hướngdẫncấu hình, sau đó chốt hạn1phút. Đã chuẩn bị GETauth/otp-options,POSTotp-request/verify/login, gatelegacyregister khi bậtOTP. 6số/TTLserver60giây/cooldown60/5attempts/HMACsecretriêng/hashArgon2pending/one-use txFORUPDATE/rateDB. KhôngcodeAPI/log/localstorage, pendinghash xóakhiconsume/invalidate/faildelivery. Genericrequestresponseunknownaccount, phoneidentityproofkhôngdùngphonecũchưaverify; nullableemailDTO/Adminclient hỗtrợphone-only, fixedUSER. ResetgiữLOCKED vàđổi credentialstampđểrevokemọisession, stampchụptrongtxloginđểtránhrace. CSRF/Origin khôngbỏ; authreadykhibậtkiểm2private tables/emailnullable.

DeliverySMTP TLS/SES/SNS transactional, khôngproviderfallback/mockproduction. Backgroundsendbest-effort, mấtprocess/phản hồimơhồfailclosed, córesendmanual; giới hạnIPthô sauproxyđượcghirõtrongdocs. Filebackend/.env.otpđãtạokhichưatồn tại,secretngẫunhiênkhôngin,flagfalse;backend-onlyoptionalenvfileCompose/templateotp.env.example. ChưaSMTP/SMScredentials, khônggửithư/SMSthật/AWSwrites. QuênmậtkhẩuUI/gateemail-SMS/countdown60/disableexpired/resend/canonicalerrors/giữreturnTo,success+nologinOTPautobypass.

SQLproposal20261118_auth_otp.sql chỉáp ởDBmarketplace_test test riêng: auth_security.challenges+identities (tổngDB+2,Marketplacevẫn25), users.emailNULLable+contactCHECK (thayđổicấutrúccầnphép). KHÔNG chạySQLDBnghiệpvụ, khôngseed/migrate/resetpassword thật. ORMnullabletheoflagOTPđểgiữauditschemahiện tại; lượtauditđầulệchnullableđãsửa, testtargetschema+OTPđãPASS. Modelmetadata/DDLkhôngstartup.

PASS534fullbackend trước bổsungreadiness,16OTP/schema-readiness/provider tests bảncuốiPASS (tổngcollection535);97frontendtests/lint/typecheck/productionbuild/Docker2imagebuild/uvlockcheck. BrowserQAprocesscổngriêng+mockAPI: emailregister/wrongcode/60s+noPWstorage,SMSregister,reset/expiry/resendnoautopost,phone-onlyloginPASS;đãxemscreenshotcode390/success390. DọnđúngtestDB/processđãtạo. Live backend/frontend/Postgres IDs/start/mount/root.envhashgiữnguyên;READONLYlive25marketplace/0auth_security/users.emailNOTNULL. Khôngupimagesmới/khôngbậtOTP. Cần provider vàchủDBduyệtSQLđểhoànthànhactivation;xemdocs/otp-setup.md.

# CART-SELECTION-WALLET — DONE (17/11/2026)

BỏlinktextXemchitiếttrênLiveProductCard,ảnh/tênvẫnclickdetail. Giỏcheckboxdòng/chọntấtcả/mặcđịnhavailable/tổngchọn/disablekhirỗng,checkoutselectedquerygiữaddress/loginback. BackendmodeSELECTED_CARTkhóacart/đốichiếuchỉselectedqty/khóastock/clearselectedonly,legacymãquoteđúngscope. LưumãtheotàikhoảnlocalStorage,6offerbutton/Đãlưu/reloadpersist/checkoutdropdown/expiry+dedup/storageerror,khôngđồngbộthiếtbị. PASS519backendfull+3legacyselected/cart/coupon trên25bảngkhôngproposal,96frontend/lint/typecheck/Ruff/build. Testquoteinitialfailed vìquerycartthiếuproduct_id;đãbổsungvàkiểmlạiPASS. Browserfixturemobile:save/reload/dropdown,uncheck1of2→selectedreview/orderonlyselected/noCartWritesselection/noXemchitietPASS;390/1440nooverflow,đãxemmobile. 2app--no-depshealthy;khôngDBwrites/DDL,PGID/start/mount/root.envpreserved. Xemcart-selection-coupon-wallet.md;preparedstackquote chưaactivecầnmởrộngscope.

# DIRECT-BUY — DONE local runtime (17/11/2026)

SửaMua ngay theochốt chỉ1product/qty,khôngthêm/xóagiỏ. URLqueryvalidated→reviewđọcpublicproduct→payloadpurchase_modeBUY_NOW. Backendbỏcartbranch,chungstock/price/public/ownership/transaction/idempotency,singleitem422;cartcheckoutcũgiữnguyên. Legacycouponquote direct_item tínhriêngsảnphẩm. Login/addressbackgiữselection,unknownintentskhácscopebịchặnkhichưarõkếtquả. PASS516backendfull/4legacytrên25bảngkhôngproposal/95frontend/lint/typecheck/Ruff/build. Browserfixturechosenqty2→checkoutmodeBUY_NOWsingleline/successheading,giữaddressquery; testcounterlầnđầusai vìmethodchưagọihàm,kiểm lạinoCartMutationPASS. Khôngđặtđơnthật/khôngDBwrites/schema;2app--no-depshealthy/PGID/start/mount/root.envpreserved. PhạmviruntimeCOD+legacycoupon;quotechoiceschuẩnbịchưaactivecầnmởrộngdirectitemsnhưdocs/direct-buy.md trước enable.

# BUY-NOW — DONE (17/11/2026)

Thêm nútMua ngay cạnhThêmgiỏ, dùngsubmitterđểchọnhànhđộng/chungformnativevalidation/guard/CSRF/thêm sốlượngđangchọn. ChỉsauchangeCartthànhcôngmớipushthanh-toan; khôngtựđặtđơn, khôngclearcart, checkoutgiỏhiệntại. GiữAdmin/self/outofstock/guestpolicy, khôngautoretryPOSTlỗi. PASS lint/typecheck/build/frontendhealthy;browserfixtureadd2/singlePOST/successnavigation/failurestay/selfdisabled/Adminhidden;mobile390vàdesktop1440cùnghàng/nooverflow. Đãxemmobile rồichỉnhgridđểhai nútcạnhnhau. Chỉfrontend,khôngbackend/DBwrites;PG/root.envpreserved.

# CHECKOUT-ADDRESS-STOCK-FIX — DONE (17/11/2026)

SửaUUIDbrowserHTTPIP thiếucrypto.randomUUID→checkoutKey dùnggetRandomValues128bitv4/khôngMath.random/giữidempotency. Linkquảnlý/thêmđịachỉ từcheckout mangreturnTo=thanh-toan, nútbacktheongữcảnh. Thêmlegacy mappingoptin choorders.shipping_discount_amount/coupons.coupon_type, checkoutkhôngghi/đọc cộtchưaáp; kíchhoạtbackend/.env.commerce flagtrue,giữoptionsfalse,khôngDDL. RuntimeREADONLY5ordersreplay/detail+couponlookupPASS. 512backendfullPASS(2Pydanticwarnings),3legacyteststrên25bảngkhôngproposalPASS(checkout/replay,lastunit2buyers,cartnoreservation). Lượtlegacyđầufailedvìrunnerlọcenvflag;đãsửarunnerforwardflagvàkiểm lạiPASS,debugtestđãgỡ. 93frontendtests/lint/typecheck/build/RuffPASS,HTTP172.18.59.17browserxácnhậnrandomUUIDundefined/getRandomValuesfunction/vềcheckoutlinkPASS. Chưađặtđơnthật/khôngghiDBnghiệpvụ;2appup--no-depshealthy/PGID/start/mount/root.envpreserved. Xemcheckout-schema-compat.md.

# SELLER-ORDER-DETAIL-FIX — DONE (17/11/2026)

READONLY tái hiện đơn3:ProgrammingError42703 orders.shipping_discount_amount khôngtồn tại doORMgetOrder chọnmọicột dùsellercontractkhôngcần. SửaSellerOrderRepository.detail chọnexplicitrecipient/phone/address/payment+joinUserfullname buyer_name, payment_ready chỉmethod/total; khôngDDL. DTO/clientprojectbuyernameoptional+labelNgườimua/Ngườinhận. Giữbackendownershipvàẩnemail/accountID/siblingorders. PASS512backend/2Pydanticwarnings ởtestconcurrency, regressionnofuturecolumn/buyername/crossshop404;92frontendtests/lint/typecheck/Ruff/build. Saudeploy2app--no-depshealthy,READONLY5đơnthậtDTO+frontendparserđềuvalid/buyernamepresent,khônginPII. Browserfixture390/1440recipient/buyer/product/qty/price/nooverflowPASS,đãxemmobile. Khôngloginthayuser/ghiđơnthật/DDL;PGID/start/mount/root.envpreserved. Backendreleaseoverlay2files,khôngđưacheckoutpendingmigrationvàoruntime. Ngoàiphạmvi:buyercheckout/orderORMvẫn cần xử lý tương thíchschema hoặc migrationđượcduyệt.

# AUTH-NOTICES — DONE (17/11/2026)

Thông báo register/login cótiêu đề, fieldvalidationtiếngViệt (empty/email/password/mismatch), pendingstatus, successởlogin sauđăngký. Emailtrùng/locked/CSRF/validation/rate/server/network/timeout mapped;khôngecho backendmessage. Mấtresponse/server5xxđăngkýghi rõchưa xácnhận/tàikhoảncóthểđãtạo,khôngautoretryPOST. PASS91frontendtests (4newfailure/noautoretry/privacy),lint/typecheck/build;browsermobilefixtures8outcomes+emptyemailPASS,khôngDBwrites/tàikhoảnthật. Đồngbộ .envngườidùngđãđổiIP172.18.59.17 cho2app;backendimageunchanged/frontendnew/up--no-depshealthy. PGID/start/mount/root.envhashgiữnguyên. Khôngbackendcode/schema/DBmigration.

# HOME-CARDS-OFFERS — DONE (17/11/2026)

Bỏ chú thích xếp hạng, tên thẻ clamp2dòng/titlefull, khung tên42px và dònggiá26px giữ giá thẳnghàng. ÔƯuđãi thayplaceholderbằng6coupon distinct từactiveDeals thậtđãtải, hiệngiảm/code/HSD/linkproduct; khôngcá nhân hóa/khôngtựáp hoặc tạo mã, khôngkhẳngđịnhliệtkêtoànbộcoupon. PASS lint/typecheck/build/frontendDocker--no-depshealthy;Chrome390/1440 namesclamp2,prices6desktop/2mobilecùngy,oldnoteabsent/6offers/nooverflow. Đãxemscreenshotsmobileoffers/cards (ảnhlazy chưa tải trongcardshot khôngcoilàảnhhỏng). PGID/start/mount/root.envgiữnguyên;khôngbackend/DB/viewchanges.

# HOME-PRODUCTS — DONE (17/11/2026)

Người dùng muốn hiện sản phẩm tại ô bán chạy. GET/api/v1/products/bestsellers aggregate sumOrderItem.quantity chỉShopOrderCOMPLETED, sortqtydesc/IDdesc/top12/lọcpubliccatalog, chưa cósales thìfallback12newest vàrankedfalse. UI ảnh/tên/giá/link/12cards responsive2–6cột, loading/error/empty. Khi fallback đổiheadingKhámphásảnphẩm vàghichúrõchưacócompleted, khôngfakebestsellers. PASS511backendPostgreSQLtest riêng: regressioncompletedordering/PENDING+CANCELLEDexcluded/hidden/fallback; lint/typecheck/Ruff/buildPASS. LiveAPI200/12/rankedfalse;Chrome390+1440/12cards+12imgelements/nooverflow,đãxemmobile. Chỉfrontend/backendimageoverlay3files/up--no-deps, khôngDDL/seed/DBwrites;PGID/start/mount/root.envpreserved.

# FLASH-CLEAN — DONE (17/11/2026)

Bỏ dòng chú thích điều kiện và đồng hồ từng sản phẩm theo ảnh người dùng, giữ mã/giá/%giảm và đồng hồ header. PASS lint/typecheck/build; frontend cập nhật --no-deps healthy; Chrome100cards/0smallnotes/0cardclocks/1headerclock. PostgreSQLID/start/mount/root.envgiữnguyên. Khôngsửabackend/view/DB.

# FLASH-30 — DONE (17/11/2026)

Theo yêu cầu mới, bỏnhãnƯuđãidưới20 và đổi0<discount<30 ởAPI/UI. View chọnbestcoupontrongphạmvicùngđiềukiệncp.discount_percent<30 (sao lưu định nghĩa trước tại D:/HealthBeauty/backups/v_deal_today_before30_*.sql), đểcoupon100%khôngchecouponmới. Khôngsửabảng/dữliệucoupon. View180sảnphẩm với5/8/10/12/15/18/20/25%. PASSRuff/lint/typecheck/build/API200top100under30/Chromemobile100cards/nhãncũabsent/nooverflow. Build/upchỉapp--no-deps;PGID/start/mount/root.envgiữnguyên.

# FLASH-STYLE — DONE (17/11/2026)

Theo ảnh người dùng: FLASH SALE cam/đồng hồ đen, một hàng ảnh/nhãn góc/giá cam/mã coupon thanhđào/nút xemtiếp. Chỉ0<discount_percent<20, lọc backend trướcLIMIT và UI phòngvệ, không sửaview/25bảng/coupon. Đồng hồ hạnthật dạng ngày+HH:mm:ss, header thờiđiểm hết hạn gần nhất; khôngfake salesbar. PASSRuff/lint/typecheck/build, appbuild/up--no-deps healthy. Liveview296records đều100%, API200items0/emptyđúng; chưa có dealdưới20. Browserfixture10rates:0/20/25bịloại,7thẻ còn lại;390/1440nooverflow/nútcuộnPASS,đãxemdesktop screenshot. FixturechỉbrowserkhôngDBseed. PostgreSQLID/start/mount/root.envgiữnguyên. Backendrelease chỉoverlayrepository giữruntimekhôngcheckoutmigration.

# DEAL-CARDS — DONE, view đã áp dụng (17/11/2026)

Người dùng cho phép “thay view”. Đã sao lưu định nghĩa cũ tại D:/HealthBeauty/backups/v_deal_today_20261117_132312.sql và áp đúng20261117_deal_view.sql trong transaction. PASS so sánh cấu trúc cột toàn bộ base tables trước/sau không đổi;296 eligible rows/0invalid metadata. APIHTTP200/100items cócoupon_code/ends_at/giágiảm hợp lệ. Chrome390:100badges/100clocks/100img elements và nútxemtiếpcuộnPASS. Hạn coupon hiện xa nên đồng hồ sốgiờlớn (8719giờ ởmẫu); không tự rút hạn hay fake dealdeadline. Không thay dữ liệu/bảng hoặc restartPostgres/app; frontend/API đang chạy tựnhậnview. Giáhiểnthị làgiásaucoupon kháchcầnáp ởcheckout, còn phụ thuộc lượt từngkhách.

# DEAL-CARDS — 17/11/2026

Đã triển khai API/view metadata tùy chọn, ảnh S3, một hàng ngang top100/nút trước-tiếp. PASS Ruff/lint/typecheck/build, HTTP200/100, Chrome390/1440 railcuộn/no pageoverflow; fixture riêng2coupon badges/countdowns PASS. Đã sửa lỗi RowMapping text không nhãn và grid minwidth qua runtime/browser kiểm lại. Giá theo mã chỉ hiện khi view có coupon_code; ends_at clock từngdeal, hết hạnẩn. SQL đề xuất20261117_deal_view.sql chỉ thayview, chưa thực thi; EXPLAIN SELECT readonly PASS. Không thêm/sửa25bảng. PostgreSQL ID/start/mount/root.env giữ nguyên (so sánh lần đầu mount ordering false, kiểm lại từngfield true). Task IN_PROGRESS chờ phép thayview để bật mã/clock thật; không xác nhận giá coupon được tựáp tại checkout.

# DEAL-VIEW — Đã triển khai (17/11/2026)

PASS lint/typecheck/production build; API backend và Next proxy HTTP200/12 sản phẩm; Chrome mobile390 xác nhận12 thẻ và link chi tiết. Backend image phát hành ghép đúng2file products từ code mới trên image đang chạy, tránh đưa checkout migration pending vào runtime. Frontend build/up --no-deps healthy. PostgreSQL ID/start/mount và root.env hash giữ nguyên, không DDL/seed. View hiện giá thường, không hiển thị %giảm giả. Chưa có ảnh trong thẻ Deal.

# DEAL-VIEW — 17/11/2026

Đã nối GET /api/v1/deals/today đọc membership v_deal_today, lọc catalog công khai/tồn kho, tối đa12 sản phẩm mới nhất; Next proxy không chuyển cookie, UI đọc items/IDchuỗi/giáthật/loading/error/empty. View có296 sản phẩm nhưng sale_price=original_price và discount0 nên không gắn giảm giả. Ruff PASS. Chưa triển khai app: image backend hiện có kèm thay đổi checkout chưa áp migration; cần tách bản phát hành tương thích schema trước khi bật runtime.

# Trạng thái mới nhất — CHECKOUT-OPTIONS code sẵn sàng, chưa áp DB thật (15/11/2026)

Người dùng chốt dùng đồng thời mã shop,1mãCOCOtiềnhàng và1mãCOCOvậnchuyển; cho phép COCO tự đặt cước. Đã chọn cố định mỗi shop:Tiêu chuẩn25000/Nhanh40000/COCOExpress60000, cấu hình được; không coi là API/bookinghãng vậnchuyển. Shop giảm trước,COCOgoods trên hàngcònlại,COCOshipping giảmriêngcước. Thêmcoupon_typeGOODS/SHIPPING vàOrder.shipping_discount_amount để không lẫn tiền hàng/cước; featureflagmặcđịnhfalse.

Code chuẩn bị: GETcheckout/options vàPOSTcheckout/quote buyer/CSRF/no-store, ômãriêng/3ship/4payment, invalidationquote khiđổi lựa chọn; serverexpecteddiscount/freight bắtbuộc để khôngnéphí. Couponlocks tăngtheoID saustock, mọiusage/stock/order/shipment/payment cùngtransaction. Cướcnetphânbổcent đến từngshop, khôngâm/saitổng. Giữ hủytoànbộhoànmọimã/partialgiữlượt theo chốttrước; usagehistorykhôngxóa. Lookupđơn/idempotencyvẫn hoạtđộng. CODready; BANK_TRANSFER chỉreadykhiđủrecipientconfig, tạoPENDING, khôngtựmarkpaid; Sellerbịchặnfulfillunpaid. Hủyall dừngpendingpayment. Chưa cóđốisoát/refundAdminUI hoặc tíchhợpMoMo/VNPay; hai cổngdisabled/rõlýdo/server503. Khônggiaonútgiảthànhcông.

SchemaSQL cụthể tại backend/migrations/proposals/20261115_checkout_options.sql:2cộtdefaultbảotoàndữliệu, thayuniqueorderidbằngcouponid+orderid, giữindexorderidvà mởCHECKbanktransfer. Modeltarget25tables/184columns/28explicitindexes. Test runners chỉ ápSQLnày saufixtureSQL25 trongDBtestmớiriêng; khôngstartupDDL/khôngsửaSQLDownloads. Live READ ONLY vẫn182columns/chưacoupon_type; khôngáp schema vàoDBnghiệpvụ. File backend/.env.commerce chuẩn bị từtemplate khi chưa tồn tại, flagfalse, giáđãchốt,bankcommented; Compose backend-only optionalenvfile. Privateconfigkhôngđượcbuild/Git/client.

PASS510backend trên PostgreSQL16test riêng (cóteststack4mã/order2shop/quote/replay/cancel/stock/counterrollback, lastCOCOuse2buyerskhácshop,typescope,tamper,bankPENDING/unpaidblock,roundshipdiscountcents). PASS87frontendtests,lệnhlint/typecheck/build; sửarefsrenderkeytheolint rồi kiểm lại. PASS E2Eoptions:300000hàng-75000goods,COCOExpress120000cước-60000shipcoupon→285000,4mã/3phươngthức,quoteinvalidation,MoMoVnPaydisabled,bankpending/create/history;320/390/768/1440/noJSerrors. Đãxemoptions390tạiD:/HealthBeauty/checkout-options-artifacts. PASSjourneycũ trênSQL25+proposal. Testprocess/containerđược dọn.

Dockerbackend/frontendbuildthànhcông, CHƯAupimage mới vàoappruntime vì chưađượcphépđổi schema. PostgreSQL/root.env/volume/network snapshotkhớpbaseline trước; khôngDBwrites/AWSwrites/DDL thật/secretchanges/commit/push. Quytrình và giới hạn tại [checkout-options-proposal.md](checkout-options-proposal.md). TaskchưaDONE: cần xác nhận phép áp schema, kích hoạtfeature và kiểm runtime; bankthật/gatewayintegrationvẫnphụthuộcthôngtinchủdựán.

# Trạng thái trước — CHECKOUT-OPTIONS khảo sát (15/11/2026)

Người dùng muốn tách mãshop/COCO và thêm lựa chọn vận chuyển/thanh toán. Đã hỏi dùng đồng thời hay chọn1mã, và danh sách phương thức mong muốn. READ ONLY xác nhận coupon_usages_order_id_key UNIQUE(order_id),0shipperactive/0shipments; schema payments chỉCOD/VNPAY/MOMO, checkoutCOD, chưarate/providerintegration. Chuẩn bị [đề xuất](checkout-options-proposal.md) có SQL thay constraint cụ thể để review (chưa thực thi), phạm vi code/test/điều kiện cấu hình. Không sửa schema/code runtime/DB/privateenv/AWS. Tests NOT RUN vì chỉ khảo sát/viết tài liệu; tính năng chưa hoàn thành, đang chờ quy tắc/phương thức/phí và quyền đổi constraint nếu cần.

# Trạng thái trước — SELLER-PURCHASES-ENTRY DONE (15/11/2026)

Người dùng nói tài khoản người bán không xem được Đơn mua. READ ONLY kiểm tra4đơn hiện hữu đềuCOD/PENDING,buyerUSERACTIVE,cóshoporders vàtổngtiềnkhớp; service list/detail của buyer đềuvalidateđược, chưa tái hiện lỗiAPI. Backend vốn không cấm chủshop mua/xemđơn từshopkhác. TrongKênhngườibán cósidebarĐơnmuacánhân nhưngHeaderthiếulốivào; đãthêmĐơnmua ởSellerHeader(USERonly) vàĐơnmuacủatôi trongbreadcrumbĐơnbán, giữsidebar1link. Khôngnớiquyềnxemđơncủakhách hoặcđổiAdminpolicy. Đơnmua làđơncùngbuyeraccountđãđặt;Đơnbán làkháchđặtởshop.

PASS502backendfull trênPostgreSQL16test riêng (2Pydanticwarnings ởconcurrencytests):3regressionPENDING/APPROVED/LOCKEDowner vẫncheckout/list/detailownorders,ngườikhácempty/404. PASS E2Ejourney tạoownshopchoBuyerđãmua→Kênhngườibán→clickHeaderĐơnmua→historycá nhân;responsive320/390/768/1440/nooverflow/noJSerrors. Đãxemscreenshot entry/history390 trongD:/HealthBeauty/seller-purchases-artifacts, dọn1sidebarlinktrùngtronglúcQA. PASSfrontend lint/typecheck/localbuild/Dockerbuild vàupchỉfrontend --no-deps healthy; không chạy lại86unitfrontend vìthayđổilinkUI đãđượcE2Ekiểm. Khôngsửabackendlogic/schema/datathật, testresourcesđãdọn. SnapshotPG/root.env/volume/networkgiữnguyên. Khôngđăngnhậpthayuser hoặcđọcpassword/token.

# Trạng thái trước — CHECKOUT-AUTO-RESOLVE DONE (15/11/2026)

Người dùng không muốn màn hình “Cần xác minh yêu cầu đặt hàng / Gửi lại yêu cầu đặt hàng”. Đã thay luồng mở checkout: intent cũ được tự tra cứu bằng GET /api/v1/orders/checkout-status, header Idempotency-Key, USER ACTIVE/buyer ownership/READ ONLY/no-store. Đã có đơn thì xóa intent cũ, mở form giỏ hiện tại và link đơn trước; chưa có thì giữ UUID cũ và mở form kiểm tra bình thường. Không tự replay POST hoặc tự tạo UUID mới khi chưa biết kết quả. Khi lỗi mạng còn thông báo/thử lại ngắn gọn; lỗi nghiệp vụ cho sửa form. Không gỡ idempotency/CSRF hoặc tự đặt hàng khi chỉ mở trang.

PASS499backend trên PostgreSQL16test riêng, test lookupnull không tạo đơn/không trừ tồn, lookup đơn cũ lặp lại/không lộ buyer khác/Admin403/header422. PASS86frontendtests/lint/typecheck/build, test client chỉGET/khôngbody/phân biệt null và response lỗi. PASS E2Ejourney mở rộng tái tạo sessionintent của đơn đã ghi nhận→form/intentcleared; intent chưa tạo đơn→form/giữUUID/0POST tự động; bấm đặt vẫn tạo lượt mua tiếp. Responsive320/390/768/1440/nooverflow/noJSerrors, đã xem checkout-auto-resolved-390 tại D:/HealthBeauty/checkout-auto-artifacts. Các testresource được dọn.

Build/up riêngbackend/frontend --no-deps healthy, giữoriginlocalhost/LAN/S3credentials. Livecheckoutpage200/statusguest401; snapshotPGID/start/mount/config/root.env/volume/network giữ nguyên. Không ghiDBnghiệp vụ, không tự đặt hoặc hủy đơn thật để xử lý screenshot, không migrations/AWSwrites/commit/push. Chi tiết tại docs/buyer-coupons-reviews.md; đây là lookup tự động, không khẳng định request POST đang trên mạng đã dừng khi GET trảnull.

# Trạng thái trước — S3-PREFIX-02 DONE (15/11/2026)

Người dùng sửa lại S3 rồi ảnh không hiện. READ ONLY xác nhận file storage/runtime vẫnkhớpbucket/region/credentials;2391DBreferences chuyển sang ProductImages/{shop}/{product}/{product}_{index}.jpg,0khớpallowlistcũ,catalog24URLsnull,ảnhmẫuHEAD200. Bổ sung đúngbốtụcmới trongLEGACY_KEY với3shophiệnhữu,folder/filename cùngID/JPG; giữlayoutcũ,privatepresignedGET vàuploadfinalizevalidation. Không đổiDB/objectkeys/bucketpolicy hoặccredentials.

PASS498backendfull trênPostgreSQL16test riêng,11cases thêm (3shop/newlayoutvà8rejectcases),Ruffcheck/format138files/build/upchỉbackend --no-deps healthy,originlogin/S3envgiữnguyên. Sauupdate2391/2391keysđượchỗtrợ;HEADảnhmẫumỗishop200,publiccatalog200/24of24imageURLs,GET3ảnhcatalog200JPEG. PlaywrightChrome390home có12imgProductImages/1ảnhnaturalWidth>0tạithờiđiểmchecklazyload. Khôngtuyênbốđãkiểm2391objects hoặcvisualQA. SnapshotPGID/start/mount/config/root.env/volume/networkgiữnguyên; khôngDBwrites/AWSwrites/DDL. Frontendtests NOT RUN vìkhôngsửafrontend.

# Trạng thái trước — BUYER-MULTI-ORDER / BUYER-COUPON / BUYER-REVIEWS DONE local (15/11/2026)

Người dùng yêu cầu áp mã checkout, review sản phẩm và mua tiếp khi đơn trước chưa xác nhận. Đã chốt: mỗi đơn1coupon; global/shopeligible,minimum trêneligible khôngshipping; kiểm tổng lượt+1lượt/khách/mã; ghi khi tạo đơn thành công; hoàn lượt khi toàn bộđơn hủy, hủy một phần giữ lượt. Dùng coupons/coupon_usages/product_reviews schema25 sẵn có, khôngDDL/seed dữ liệu thật. Chi tiết contract/locking ở [buyer-coupons-reviews.md](buyer-coupons-reviews.md).

Checkout xóa sessionintent chỉ sau response tạo đơn/replay được xác minh, không chờ Seller xác nhận; vẫn giữkey khi mấtresponse. Couponquote lấy giỏ server, không reserve; checkout khóa coupon sau stock, Decimal HALF_UP/expecteddiscount, totalnet/discount/shipping snapshot vàhistoryparser mới. Usage/counter cùngtransaction đặt đơn, replay khôngtănglượt. Hủytoànbộ khóa coupon sau shoporder/stock, đọcchildstatuses rồi decrement1lần, giữusagehistory vàkhôi phục customereligibility; partial/no-op khônghoànthêm. KhôngcouponadminUI hoặc tự tạo mã.

Review GET/POST theo orderitem chỉUSER ACTIVE/owner/COMPLETED, mỗi dòng1review, ratingint1–5/comment≤2000; khôngnhậnuser/producttừclient. Public chỉreview buyer/productkhớp đơncompleted vàproductpublic, trả4field antoàn/avg/count/page; khôngemail/name/order/userID. Buyer detailform đọc lại sau mấtresponse, productpage empty/loading/error/pagination, Reacttextescaped. Admin403 vớiquote/private review. Proxy fixedpaths/ID/query/method/bodylimits/CSRF; publicreviewGET khôngforwardcookie/Auth.

PASS487backend full trên PostgreSQL16tmpfs/schema25reference lượt cuối khôngwarning (lượttrước2warningPydantic runtime đồngthời),14cases mới gồm coupon scope/minimum/date/limit, global lastuse khácshop, rollbackcommit/replay, partial/full/no-opcancel,2sellerconcurrentcancel, khácproductkhiPENDING, reviewownership/status/CSRF/privacy/duplicateconcurrency. PASS85frontendtests/lint/typecheck/localbuild vàDocker2appbuild. Schema25testrunner đổi pg_isready sangTCP127.0.0.1 để tránh nhận bootstrapUnixserver làready; lầnđầuSQLfixturefailedtrướcpytest, chỉDBtestđãdọn; khôngsửa SQLfixture hoặcDBthật.

PASS E2Ejourney mởrộng: UIcoupon10%→240000 giảm24000 còn216000, orderhistorynet, sessionintentcleared, secondcheckoutkhi firstPENDING, cancel2ndgiữstock; Sellercomplete→review4sao/comment→reload→guestproductreviewvisible. Responsive320/390/768/1440/nooverflow/noJSerrors, đãxem screenshots checkout-coupon/buyer-review/product-reviews390 tại D:/HealthBeauty/shopping-artifacts. E2Etestresourcesđãdọn. Không dùngaccount/datathật cho checkout/reviewwrite.

Build/up riêngbackend/frontend --no-deps healthy, giữoriginlocalhost/LAN vàprivateS3env. Livepubliccatalog200/reviews200, guestprivateAPI401/403. READ ONLY live hiện0couponcònhiệulực; cầnchủdựáncấu hìnhmãthật đểdùng, khôngbịa mãhoặcseedproduction. PGid/start/mount/config/root.env/volume/network trước-sau giữnguyên. Khôngmigrations/AWSdeploy/bucketwrites/commit/push, khôngresetpassword hoặcđổiArgon2.

# Trạng thái trước — S3-DISPLAY-01 DONE delivery (15/11/2026)

Theo yêu cầu hỗ trợ ảnh cũ, ObjectStorage.url chấp nhận thêm đúng ba prefix hiện hữu (1-Lumi Beauty/2-Miora Lifestyle/3-Nuvia Care Store), product_image/{id}/{id}_{index}.jpg, fullmatch ASCII ID, folder/filename cùng ID. Không nhận URL tùy ý/traversal/query/newline/staging hoặc prefix lạ. Chỉ dùng cho delivery từ reference DB, không cho API finalize nhận key cũ; upload grant/verify/immutable final giữ nguyên. Legacy luôn ký GET900s theo key nguyên bản, không chuyển dấu cách thành dấu+ hoặc dùng CDN vốn chỉ phục vụ product-images/. Không HEAD từng ảnh trong request danh sách.

PASS473backend tests trên PostgreSQL test riêng,13cases mới cho3prefix vàreject10paths;Ruff check/format133files/build backend/up --no-deps healthy. Runtime2391/2391DBkeys khớp legacy; sample signedGET200/JPEG,publicAPI200 với24/24primaryURLs,firstcatalogimageGET200. PlaywrightChrome390 homepage có12S3img và2ảnh đã load naturalWidth>0 tại thời điểm kiểm (lazyload); không gọi là kiểm toàn bộảnh hoặc visualreview. PostgreSQL/root.env/volume/network snapshot giữ nguyên, không ghiDB/đổibucketpolicy/uploadobjects. Chưa kiểm2391objects tồn tại/quyền đọc hết hoặc CORS/upload/PUT; P6-03 integration vẫn chưa DONE.

## Các bước chẩn đoán trước khi sửa

Credentials đã được người dùng điền local. Nạp backend bằng up --no-deps --wait, giữ origin hiện tại, healthy. PASS authenticated HEAD200 và signed GET200/JPEG signature cho key thực `1-Lumi Beauty/product_image/1/1_1.jpg`; key chứa dấu+ literal trả403. DB READ ONLY xác nhận key có khoảng trắng đã liên kết đúng1reference, sample3keys cùng prefix cũ. Kết nối/đọc ảnh S3 thành công nhưng ObjectStorage.url vẫn từ chối định dạng cũ vì FINAL_KEY; cần compatibility có kiểm chứng trước khi ảnh hiện. Không in credentials/presignedURL, không upload/đổi quyền bucket hoặc ghi DB. Snapshot PostgreSQL/root.env/volume/network giữ nguyên. Chưa kiểm upload/CORS/PUT hoặc toàn bộ2391objects; không đánh dấu P6-03 hoặc S3-DISPLAY DONE.

Sau khi người dùng báo đã cấu hình: backend/.env.storage tồn tại nhưng bucket và AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY/AWS_SESSION_TOKEN đều trống; region mẫu khi đó chưa khớp region bucket. Up riêng backend --no-deps healthy, giữ origin hiện tại; runtime vẫn bucket=False. READ ONLY DB có2391 image references,0 key khớp FINAL_KEY. Đã điền riêng bucket=coco-marketplace và region=us-east-1 trong file private, không thay credential. Chưa nạp lại hai giá trị này vào runtime vì credential chưa có; chưa gọi S3 có xác thực hoặc sửa DB/code. PostgreSQL/env root/volume/network snapshot giữ nguyên. Cần người dùng điền credentials local để kiểm tiếp; ảnh cũ còn cần compatibility/import có kiểm chứng, không tự đánh dấu DONE.

Người dùng cung cấp URL bucket coco-marketplace, region us-east-1, key hiển thị 1-Lumi+Beauty/product_image/1/1_1.jpg. HEAD ẩn danh trả403 cho cả URL gốc và biến thể khoảng trắng/%2B; chưa kết luận object tồn tại hay bucket policy cụ thể từ403. Key này không khớp FINAL_KEY của app. Chưa có quyền AWS để kiểm HEAD có xác thực hoặc xác minh bytes; đã hỏi cách cấu hình credential local, không yêu cầu gửi secret. Chưa tự sửa quyền public bucket, liên kết DB hay nới validation key.

Người dùng báo đã upload S3 nhưng web chưa hiện ảnh. Kiểm tra READ ONLY runtime backend: bucket_configured=False, public_base_configured=False, endpoint_configured=False; backend/.env.storage chưa tồn tại. ObjectStorage.url trả null khi chưa có bucket hoặc key không đúng mẫu product-images/{shop}/{product}/{uuid32}.{jpg|png|webp}. Ảnh cần liên kết ProductImage; upload qua S3 Console không tự liên kết sản phẩm. Đã hỏi cách upload, bucket/region/object key mẫu, không hỏi credential. Chưa kiểm AWS/object/DB references, không sửa code/config/DB hoặc gọi AWS. Tests NOT RUN vì chỉ chẩn đoán cấu hình và ghi tài liệu; chưa xác nhận khắc phục.

# Trạng thái trước — AUTH-ARGON2-KEEP (15/11/2026)

Người dùng yêu cầu giữ argon2-cffi. Đã gỡ nhánh xác minh bcrypt, điều kiện chuyển bcrypt sang Argon2, dependency bcrypt và test tạm vừa thêm. Giữ nguyên xác minh/rehash Argon2 hiện có; không sửa script tạo hash của người dùng hoặc ghi dữ liệu tài khoản. Hash tài khoản Admin được kiểm tra trước đó là bcrypt, vì vậy lỗi đăng nhập chưa được giải quyết bằng thay đổi này; cần hash Argon2id của mật khẩu do chủ tài khoản chọn, không gửi mật khẩu qua chat.

PASS uv lock --check, Ruff check/format toàn backend, 460 tests trên PostgreSQL test riêng; có 2 cảnh báo Pydantic UnsupportedFieldAttributeWarning. Build/up riêng backend --no-deps healthy, runtime có Argon2id và không có bcrypt. PostgreSQL ID/start/mount/config, root.env, volume và network giữ nguyên theo snapshot trước/sau. Không đổi schema, mật khẩu hoặc triển khai AWS.

# Trạng thái trước — ADMIN-LOGIN-LAN-02 (15/11/2026)

User báo không login Admin. READ ONLY xác nhận email Admin đã chỉ định vẫn ADMIN/ACTIVE, auth key có cấu hình; không đọc hash/password hoặc đổi role/status. Runtime chỉ allowlocalhost, Wi-Fi192.168.110.101. Tái hiện localhost login{}422 nhưngLAN403CSRF_FAILED. Thêm exactLANalias đồng bộ2app, giữ canonical localhost, upapp --no-deps healthy. PASS2origin login{}422/hostile403/forgedtoken403, PostgreSQL ID/start/mount/config/root.envhash/volume/network giữ nguyên. Không thử login bằng password thật hoặc xác nhận credential; đã hỏi URL/thông báo lỗi của user để phân biệt trường hợp localhost. Không DBmutation/DDL/secret change/PGrestart/build/source change.

# Trạng thái trước — PACKAGE-IMAGES-01 DONE (14/11/2026)

Theo yêu cầu đóng riêng2image, build coco-backend:2026-11-14/latest từbackendDockerfile và coco-frontend:2026-11-14/latest từfrontendDockerfile hiện có. Export2filetar độc lập tmp/docker/coco-backend-2026-11-14.tar và coco-frontend-2026-11-14.tar, có cả2tag mỗiimage. tmpđãignored theo.gitignore. Backend khoảng80,65MB/frontend105,28MB dạngtar; đã tínhSHA256.

PASS build cả2image, backendimport/create_app khôngDB, frontendstandalone/server.js, kiểmimageuser/architecture. Không chạy lại460/80tests vì không sửa code hoặcDockerfile; build dùngcache source đã kiểm lượt trước. .dockerignore loại private.env; không bake credential/root.env vàoimage, chỉ đọc buildcontextbackend/frontend. Không pushregistry, không cập nhậtservice/Compose/env hoặc chạmPostgreSQL. Đây là imageLinux dùngDocker, không phải triển khaiAWS.

Chuyểnmáy: docker load -i từngfiletar; cấu hìnhenv/secrets/network/DB/S3 lúc chạy theo docs/handoff.md. Backend cổng8000, frontend cổng3000 trongcontainer; không gọi docker run khôngenv rồi coi auth/DB đã cấu hình.

# Trạng thái trước — Schema25/CRUD DONE local; k6 public/AWS chờ URL (14/11/2026)

User cập nhật coco_marketplace_25_tables.sql, xác nhận CRUD cho cảshop/product và gửi sơ đồ k6ngoàiAWS→Internet→publicLB. Đã đọc toàn bộSQL25bảng19427bytes, không xem nội dung file/ảnh là quyền deployAWS hoặc chạyDDL nghiệp vụ. DB metadata READ ONLY xác nhận25tables;24identityBYDEFAULT khác SQLALWAYS. Không thay DB/identity/sequence/schema hoặc tạo dữ liệu thật.

SCHEMA25-COMPAT: Order thêm discount_amount/shipping_fee/default0/paymentmethodVARCHAR20/CHECKCOD-VNPAY-MOMO; đăng ký13extensionTables bằngSQLAlchemy metadata, tổng25tables/182columns/27explicitindexes. Readiness kiểm25tables; khôngDDL/reflectstartup. Không tự bậtcoupon/payment/review/shipping/history/audit API hoặc đổi checkoutCOD mô phỏng. SourceSQL đã copy vào backend/tests/fixtures; tests/schema25/run.py tạo PostgreSQL16tmpfs marketplace_test từSQLnguồn, chạy backend vàmetadataaudit trên chính DBtest đó, dọnlabel riêng. Strict audit live vẫn có identitydrift; không báo liveDB khớp100%.

SELLER-CRUD-25: thêm DELETE/seller/shop/{shop_id} USERACTIVE/owner/rowlock/no-store,404nếuIDkhôngkhớp để chốngtabcũ xóa shop thay thế. FKproducts/orders/history/coupons... chặn409SHOP_IN_USE. DELETE/seller/products/{id} owner/shopAPPROVED, khóa theo user→category→shop→product→inventory, xóaInventory+Productcùngtransaction, FKcart/order/price-history/... chặn409PRODUCT_IN_USE và rollbacktồn; image DBreference cascade theoFK sẵn, không xóaS3objects. UI2nútconfirm riêng, busyguard, parse204, exactBIGINT, không retry DELETE khi mấtresponse. Cóhistory thì dùngẨnproduct; khôngcascade xóa dữ liệu nghiệp vụ để gọi làCRUD.

K6-AWS-ACCESS: script tests/k6/web-smoke.js, k6v2.4image digestpin/1VU5iterations mặc định; tăng tải yêu cầuenvstaging/isolated vàbound20VU1000iters. K6cookiejar+Origin/token thực, POSTloginbodyrỗng422khôngtạoaccount, guestAdmin401, publicHTML/catalogGET. Lượt đầu20/25checks vì Nextchưa có/API/v1/products; thêm publiclist/detailGETproxy fixedupstream, allowlist/boundsquery, không forwardCookie/Authorization, teststrictvalidation/privacy. Lượt cuối25/25checks/0unexpectedHTTPerrors. Chưa cóURLpublic/domainALB nên chưa chạy từAWS/GrafanaCloud, không tự deploy/kết nốiAWS/Terraform/EKS/ALB/HPA/ETL hoặc nớiCSRF.

- PASS460backend full trên **referenceSQL25 trong PostgreSQL16test riêng**, không fail/skip/warning lượt cuối, gồm9CRUDcases mới và3metadataaudit. Lượt đầu456passed/4failure do liveidentitydrift, unitcounts12/readinessmock12 và oldwrong-methodexpect404; cập nhậtunit25/182/27/REST405, giữstrictauditALWAYS và chuyển auditfullsuite sangSQLreference, không che driftlive. Các tests publiccatalog dùng CREATE SCHEMA IF NOT EXISTS chỉ trong guardtestDB để auditSQLkhởi tạo trước; không thay startupDDL.
- PASS80frontendtests (3nhóm publicproxyprivacy/query, DELETE204/BIGINT/no retry, privateproxysecurity/path),lint/typecheck/localproductionbuild vàDockerbackend/frontendbuild. Nextshop collectionhandlers đã bọc1arg để không nhầm context thànhshopId. Ruff check/format142files/uvlockcheck/diff PASS. Không thêmdependencyproduction.
- PASS browserjourneyBuyer/Seller/Admin cũ trên SQL25; PASS browserCRUDmới shopUIcreate/read/edit/delete/recreate/staleID, productUIcreate/read/edit/delete, cart-linkedproduct409/stockpreserved, shop-withproduct409;320/390/768/1440/noJSerrors. Đã xemshop-delete-390/product-delete-390; sửaspacing/nútconfirmshop rồibuild/browserCRUDlạiPASS. D:/HealthBeauty/schema25-artifacts. Testresources được dọn, khôngloginaccountthật.
- PASS build/upchỉbackend/frontend --no-deps healthy, giữruntimeoriginlocalhost/aliaslocalhost như đầu lượt. Live4guestpages/4widths/noJSerrors, catalogAPI200/badquery400, guestDELETEshop/product401, readiness200. Không tự đổiLAN/IP/firewall theo sơ đồ hoặc login bằngaccountthật. PASS .schema25-original.json trước/sau: PostgreSQL ID/start/mount/config/root.envhash/namedvolume/network giữ nguyên; tất cảtestcontainers labelschema25/schema25-reference/p802e2e đã dọn. Không load/stressDBnghiệp vụ bằngk6.

Hướng dẫn [schema25-crud-k6.md](schema25-crud-k6.md), cập nhậtdata-requirements/APIcontract/E2E. Còn identitymetadata source/live, URLpublic/AWSnetworkpath và các gateS3/production trước đây; không gộp vàoDONE. Không sửaSQLDownloads, root.env/Compose/PostgreSQL/Terraform/AWS/commit/push.

# Trạng thái trước — SCHEMA-REVIEW-02 đối chiếu READ ONLY (12/11/2026)

Người dùng thông báo cập nhật schema và chỉ định Downloads/marketplace_schema.sql. Đã đọc toàn bộ4435bytes:6bảng users/shops/categories/products/product_images/inventory,5identity BY DEFAULT,BEGIN nhưng chưaCOMMIT; chưa có6bảng giỏ/địa chỉ/đơn và phần trigger/function/index đầy đủ. Không chạy fileSQL. DB metadata READ ONLY xác nhận vẫn12bảng/11identity BY DEFAULT/6triggers, trong khi model còn Identity(always=True). Không suy ra cách hoặc thời điểm DB thay đổi; không đọc business rows hoặc chạy DDL/mutation.

Đã hỏi file là toàn bộ hay phần đầu; chưa nhận xác nhận trong lượt đối chiếu. Review hoàn tất trong phạm vi file hiện có, đồng bộ model/test/migration chưa thực hiện vì chưa có schema đầy đủ. Báo cáo [schema-review-2026-11-12.md](schema-review-2026-11-12.md). Chỉ sửa tài liệu, không chạy full tests/build/E2E hoặc restart/app/PG/env/Compose/AWS/Terraform/commit/push. Không đánh dấu schema/application đã đồng bộ.

# Trạng thái trước — FIX-MOBILE-AUTH-01 DONE runtime (11/11/2026)

Người dùng báo điện thoại đăng nhập nhưng ảnh là form đăng ký lỗi phiên xác thực. Kiểm tra hiện tại cả3container đã được mở lại/healthy, Wi-Fi172.18.60.11, runtime frontend/backend canonical localhost/additional chỉlocalhost. Tái hiện qua LAN GETcsrf200/POSTregister{}403 CSRF_FAILED. Thêm đúng LAN hiện tại vào additional_origins của cả2app bằng biến phiên, giữ canonical localhost và root.env; up backend/frontend --no-deps, không build lại hay restart/recreate PostgreSQL.

PASS desktop Chrome mobile390 thực qua LAN vàlocalhost: register/login{}422VALIDATION_ERROR, đã quaCSRF; hostileOrigin/forgedtoken403, không overflow/JSerrors. Không dùng tài khoản/password từ ảnh hoặc tạo account để test. Hai app healthy; ảnh chụp không cho biết URL điện thoại nhưng URL LAN hiện tại đã được kiểm, chưa có xác nhận lại từ điện thoại vật lý. Các chính sách CSRF/session-cookie/Origin không thay đổi và không wildcard. Không chạy lại full unit/build vì chỉ thay runtime env và tài liệu, không source/dependency/schema.

PASS .mobile-auth-baseline.json trước/sau: PostgreSQL ID/start/mount/config/root.envhash/volume/network giữ nguyên, không fixtures/business writes/AWS/Terraform/commit/push. Cập nhật docs/mobile-local.md với lệnh recreate đủ2biến theo terminal; IP thay đổi theo mạng nên cần cập nhật explicit allowlist, không giả URL cố định. App hiện hoạt động trở lại, supersede ghi chú runtime dừng của lượt trước; không tuyên bố login thật đã kiểm bằng tài khoản chủ dự án.

# Trạng thái trước — ADMIN-COMMERCE-01 DONE code/kiểm thử; runtime đang dừng (11/11/2026)

Người dùng yêu cầu Admin không mua hàng/tạo gian hàng, thay thế quyền Admin-as-Buyer trước đây. AccessPolicy.buyer chỉ cho USER ACTIVE và trả403 COMMERCE_FORBIDDEN cho ADMIN; role lấy DB mỗi request. Áp dụng cart/addresses/Buyer orders/cancel/checkout (trước idempotency replay) và SellerShopService GET/POST/PATCH hồ sơ đăng ký shop. auth/me/Admin API/public catalog vẫn hoạt động. Không chuyển role/owner, khóa shop hoặc xóa dữ liệu cũ; không mở rộng thành chính sách xóa shop của Admin.

UI: Admin thấy link quản trị thay giỏ/kênh đăng ký bán, không nút thêm giỏ; account không link địa chỉ/giỏ/đơn/đăng ký shop. Direct URL giỏ/checkout/địa chỉ/đơn/đăng ký shop hiển thị CommerceRestriction và link quản trị, không mount flow ghi. Giữ class header để không đổi layout khách/USER. USER vẫn đăng ký shop/mua hàng như trước.

- PASS448 backend trên PostgreSQL16 tmpfs marketplace_test riêng, không fail/skip/warning lượt cuối; chủ động exclude3metadata-audit tests vì PostgreSQL nghiệp vụ đang dừng, không gọi full suite có audit. Thêm2case promotion/token cũ/đã có shop hoặc chưa/order cũ/replay/new key/cart/shop/address/cancel bị chặn, dữ liệu không thay đổi, Admin/public access còn dùng, demote USER dùng giỏ lại. Cập nhật test expectations cũ cho policy mới và tách Buyer USER trong category concurrency để không kiểm bằng Admin giả Buyer. Lượt đầu446passed/2failure vì test giữ CSRF token cũ sau helper checkout rotate; sửa harness lấy CSRF mới cho mutation, không nới CSRF production.
- PASS77frontend tests/lint/typecheck/local build; Docker backend/frontend build PASS. Ruff check/format139files,uv lock --check,git diff --check PASS; không dependency/schema/Compose/env change.
- PASS browser Nextproduction/FastAPI/PGtest: Admin login → mở trực tiếp5trang Buyer/shop đều thấy restriction, account không link giỏ/Seller; Admin duyệt/ẩn/khóa vẫn chạy. USER Guest tìm→keyboardadd/địa chỉ/checkout→Seller hoàn tất→Buyer theo dõi vẫn PASS,7màn hình/4widths/noJSerrors. Harness tests/e2e/journey.cjs, script fixture Admin trong DBtest; không đăng nhập tài khoản nghiệp vụ. Trả403 thay404 cho Admin gọi Buyer orders theo policy mới.
- Runtime PostgreSQL vẫn exited, không up/restart app hoặc PostgreSQL. Chỉ build image mới và chạy test processes/container riêng, đã dọn; cần áp dụng app bằng up --no-deps khi môi trường nghiệp vụ được mở lại. Baseline helper xác nhận PostgreSQL ID/start/mount/config/root.envhash/namedvolume/network giữ nguyên; không seed/DDL/mutation DB nghiệp vụ/AWS/Terraform/commit/push.

Cập nhật authorization/business-rules/API contract/seller-shop/buyer-orders/handoff/test-matrix. Dữ liệu đơn/gian hàng Admin đã có được giữ, không thể dùng API Buyer hoặc hồ sơ shop khi role hiện tại ADMIN. Thiếu bucket không ảnh hưởng chính sách này. Không đánh dấu đã cập nhật live trong lúc app/DB dừng.

# Trạng thái trước — ADMIN-FR-VERIFY DONE chức năng (11/11/2026)

Người dùng yêu cầu bảo đảm đúng FR-A01–04 và4quy tắc Admin. Đối chiếu API/UI hiện có không thấy thiếu chức năng trong bảng. Không bổ sung duyệt lại shop/mở khóa shop hoặc khóa ADMIN vì ngoài bảng/chính sách trước. Thêm integration/test_z_admin_requirements.py với4acceptance cases: Guest/Buyer/owner không truy cập4nhóm Admin và không approve/lock/hide/change category/user; Admin xem/tìm/khóa-mở USER (token cũ mất quyền khi khóa), xem/duyệt/từ chối/khóa shop, hide loại public search/detail, category create/edit/disable/DELETE405 giữ FK sản phẩm và tồn. Các tests chuyên biệt hiện hữu xác minh shopLOCKED chặn checkout/new product độc lập và category/order snapshot/concurrency/rollback.

- PASS446 backend trên PostgreSQL16 tmpfs marketplace_test riêng; gồm4case mới,1 Pydantic alias data warning trong image concurrency test, không fail/skip. Lượt cuối chủ động exclude test_existing_schema.py, không gọi đó là full suite có audit;3metadata checks hiện hữu NOT RUN thành công do PostgreSQL nghiệp vụ đang dừng. Lượt đầu446passed/3audit setup errors do loopback5432timeout; không báo lỗi hạ tầng này là lỗi chức năng Admin.
- PASS77frontend tests/lint/typecheck; Ruff check/format130backend files và git diff --check. Không đổi runtime/backend/frontend production code, không build/deploy hoặc chạy browser live khi app đang dừng. UI có4trang Admin như docs/admin-acceptance.md; evidence browser trước đã ghi riêng, không coi là browser mới.
- Kiểm tra Docker thấy không có container chạy, marketplace_postgres state exited; không có snapshot state đầu lượt nên không xác định thời điểm/nguyên nhân dừng. Không lệnh stop/restart/recreate PostgreSQL hoặc app nghiệp vụ trong lượt này. Giữ nguyên trạng thái hiện có, không ghi fixture trên DB thật.
- PASS baseline helper trước/sau: PostgreSQL ID/start/mount/config/root.env hash/volume/network giữ nguyên sau khi trạng thái Docker ổn định. Lượt đầu helper báo mismatch tạm thời khi cleanup, kiểm lại độc lập các section không khác; lượt cuối helper PASS. Chỉ container test thuộc runner được tạo/dọn.

Tài liệu nghiệm thu [admin-acceptance.md](admin-acceptance.md), cập nhật test-matrix/checklist. ADMIN vẫn chỉ xem theo yêu cầu bỏ qua khóa Admin trước đó; FR-A01 lock/unlock USER. Không cần S3 để kiểm chứng4FR; ảnh thật/bucket và các gate ngoài đã ghi trước không được đánh dấu DONE. Không sửa schema/DB/business status/env/Compose/AWS/Terraform/commit/push.

# Trạng thái trước — P8-03 DONE local; P8-04 phần local hoàn tất, còn gate ngoài (11/11/2026)

Người dùng yêu cầu làm nốt các nhiệm vụ, mở rộng rõ nhiều task. Đã tuần tự hoàn thành phần P8-03 và chuẩn bị/kiểm phần local P8-04, chạy lại P8-01/02 sau thay đổi. Không tự coi thiếu bucket/ảnh thật là đã hoàn tất; P6-03/P8-01/02/04 và UI-04 còn các đầu vào/gate ghi trong handoff. Không triển khai AWS hoặc nhập dữ liệu bán hàng.

P8-03: thêm tests/performance/probe.py/serve.py và mode E2E_SUITE=performance vào runner chung. Hai Uvicorn process thật/cùng PostgreSQL16 tmpfs,2000products/120catalog requests/8concurrent/0errors,266,28requests/s,p50=27,26ms,p95=47,19ms,max62,68ms. Cùng key4checkout HTTP chia2process→201/200/200/200,cùng1order; haiBuyer tranh tồn1→201/409,tồn0; stock/order exact. EXPLAIN repositorySQL trang1/80 execution3,722/7,348ms; full plan sanitized trong performance-baseline.json. Graceful idle shutdown Uvicorn replica exit0/backend khác ready200; dừng đúng testDB của runner thì live200/ready503. Không thêm index/extension/tune DB hoặc đo tải dữ liệu nghiệp vụ. Docs/performance.md ghi pool budget10/process, giới hạn máy/cache/workload ngắn, không suy ra AutoScaling/production capacity.

P8-04: thêm nosniff/frameDENY/referrer/permissions headers cho Next, E2E kiểm response thật. OSV47registry packages ban đầu báo Pillow12.3.0, gồm critical JPEG decoder dùng trong upload. Đọc release notes chính thức, nâng Pillow13.0.0/cập nhật uv.lock và sync; thêm decoder allowlist trước verify/load,4tests cho JPEG/PNG/WebP publish và TIFF giảPNG bị chặn. Không override major chỉ để che audit; đây là vá decoder input không tin cậy có test tương thích. OSV sau cập nhật0finding. Full npm audit7moderate dev-only ESLint/minimatch10.2.6; production-only0. npm audit fix --dry-run cho biết patch11dev packages vẫn còn7moderate, không apply/force/override major. Thêm bounded Git-visible pattern scanner và OSV runner, không in secrets, có giới hạn rõ.

- PASS445 backend full/PostgreSQL16 test riêng + metadata audit READ ONLY sau vá, không fail/skip;1 Pydantic UnsupportedFieldAttributeWarning alias order_id trong concurrent test. Ruff check/format cuối137files và uv lock --check PASS. Kiểm từ root ban đầu phân loại import app khác cwd backend; đã khai báo known-first-party=app trong Ruff config và format3 import runner để hai cách chạy nhất quán, không đổi logic runtime.
- PASS77frontend tests/lint/typecheck/local build/Docker backend+frontend build. E2E journey lượt cuối Chrome/Nextproduction/FastAPI/Pillow13/PGtest PASS, gồm7màn hình/4widths,keyboard/checkout/orders/Admin/noimage/storage-disabled/loading503/expiry/ownership/snapshots và securityheaders; không JS errors. Chỉ format config/JS sau đó, không đổi logic đã kiểm. Performance/health/shutdown suite PASS riêng trước đổi Pillow; không nói nó đo S3.
- PASS build/up backend/frontend --no-deps healthy, runtimePillow13.0.0; live4guest routes/4widths/noJSerrors/readiness200 và header thật. Không đăng nhập thay tài khoản thật hoặc ghi fixture/user/shop/category/product/order vào DB nghiệp vụ. Giữ canonicalLAN cũ/localhostalias, không đổi root.env/Compose/PostgreSQL/Terraform.
- PASS baseline .p8final-original.json trước/sau toàn lượt: PostgreSQL ID/start/mount/config/root.envhash/namedvolume/network giữ nguyên; tất cả test containers label p802e2e được dọn, chỉ test process của mình bị dừng. Không restart/recreate PostgreSQL nghiệp vụ/DDL/seed/AWS/commit/push.

README đã cập nhật trạng thái hiện tại, giữ mục cũ là lịch sử; bàn giao local/config/test/FR/health/risks tại [handoff.md](handoff.md), [performance.md](performance.md), tests/security/README.md. NOT RUN S3 thật/CORS/IAM/upload/delivery/expiry/ảnh storage lỗi tải, ảnh/mapping nghiệp vụ, HTTPS/device thật/soak/rolling transaction drain. Production edge rate-limit/CSP/TLS và7dev findings vẫn cần xử lý trước phát hành thật. AWS/ETL ngoài scope được triển khai và chưa có hạ tầng. Đã làm hết phần local khả dụng; không đánh dấu các gate này DONE hoặc yêu cầu secret qua chat.

# Trạng thái trước — P8-02 IN_PROGRESS, E2E không bucket PASS (11/11/2026)

Người dùng xác nhận tiếp tục phần không cần bucket sau giải thích các bước độc lập. Triển khai phạm vi E2E/responsive P8-02 dù P8-01/P6-03 còn phần S3 chưa kiểm chứng; không đánh dấu các dependency DONE và không mở P8-03/04.

Thêm tests/e2e/run.py, journey.cjs, promote_test_admin.py và README hướng dẫn chạy lại. Runner tạo PostgreSQL16 marketplace_test tmpfs/loopback/name UUID/label riêng, backend/Next production process riêng, secret ngẫu nhiên; bỏ biến MARKETPLACE_/AWS_ kế thừa, không bucket/root.env/production volume. Chỉ fixture nâng Admin ghi testDB, có guard môi trường/tên DB/host/email. Shop/category/product chuẩn bị qua API thật, Admin duyệt shop bằng UI; Guest tìm bằng form → Buyer login/UI thêm giỏ bằng keyboard/địa chỉ/checkout COD → Seller xác nhận/giao/hoàn tất → Buyer theo dõi → Admin ẩn sản phẩm/khóa shop. Xác minh ownership, snapshot và tồn, empty/missing-address/loading/503/recovery/expiry privacy.

E2E phát hiện fieldset chọn file trong Seller quản lý ảnh có min-content width làm tràn320px dù thiếu storage. Sửa đúng2 rule globals.css: min-inline-size:0/grid minmax(0,1fr), input file width100%/min-width0. Không đổi quy tắc upload/CSRF/API hoặc dữ liệu.

- PASS E2E lượt cuối trên Chrome headless: bảy màn hình ở320/390/768/1440 không overflow; page JS errors rỗng; upload disabled và placeholder không ảnh đúng. Đã xem ảnh seller-no-storage-390.png/checkout-390.png tại D:/HealthBeauty/p802-artifacts. Các lượt đầu sai selector nút + Thêm địa chỉ, kỳ vọng403/404 Admin không shop và selector text trùng option; đã sửa harness theo contract. Lỗi overflow là lỗi ứng dụng thật, đã sửa và chạy lại PASS.
- PASS77 frontend tests/lint/typecheck/local production build/Docker frontend build. Ruff check/format với backend/pyproject.toml cho runner/fixture và node --check PASS. Không thay backend production nên không chạy lại441 backend tests đã đạt P8-01; không báo số đó là lượt chạy mới.
- PASS frontend build/up --no-deps healthy, live localhost4 guest routes/4widths/no JS errors, CSS mới được serve, readiness200. Không đăng nhập account thật hoặc tạo fixture/danh mục/sản phẩm trên DB nghiệp vụ. Giữ canonical LAN cũ và alias localhost; không kiểm chứng LAN cũ.
- PASS baseline .p802-original.json trước/sau: PostgreSQL ID/start/mount/config/root.env hash/volume/network giữ nguyên. Tất cả container test label p802e2e được dọn; không restart/recreate PostgreSQL/DDL/seed/env/Compose/dependency/AWS/Terraform/commit/push.

NOT RUN S3 thật/ảnh sản phẩm lỗi tải từ storage, HTTPS/thiết bị vật lý/browser khác/load. P8-02 giữ IN_PROGRESS vì phần ảnh thật chưa có dependency; phạm vi không bucket đã PASS. Hướng dẫn [../tests/e2e/README.md](../tests/e2e/README.md). Dừng sau phạm vi P8-02.

# Trạng thái trước — P8-01 IN_PROGRESS (11/11/2026)

Theo yêu cầu làm tiếp, thực hiện phần regression API độc lập của P8-01; dependency P6-03 vẫn thiếu bucket nên không đánh dấu DONE. Bổ sung docs/test-matrix.md ánh xạ FR, quyền, rollback/concurrency và giới hạn. Thêm integration/test_workflow_regression.py với3 trường hợp Admin ẩn sản phẩm/khóa shop/tắt danh mục sau checkout hai shop: public404, replay cùng key giữ nguyên order/snapshot, Admin khác không đọc đơn Buyer, Seller vẫn hủy đơn cũ và replay hủy không hoàn tồn lần hai hoặc tác động shop khác.

- PASS441 backend full trên PostgreSQL16 marketplace_test tmpfs riêng + metadata audit READ ONLY; không fail/skip/warning trong lượt cuối. Ruff check/format PASS129 files, uv lock --check PASS. Thêm tests vào pytest pythonpath để dùng fixture chung từ integration. Lượt đầu lỗi import; lượt kế tiếp432 passed/9 setup errors do workflow tạo schema trước bộ catalog pristine. Đã đặt workflow sau public_catalog theo collection mặc định và ghi giới hạn chạy lại; không thay fixture/schema production, không sửa production code. Đây không phải hỗ trợ chạy suite đảo thứ tự tùy ý.
- PASS77 frontend tests, lint và typecheck. NOT RUN build/browser trong lượt này vì chỉ thêm tests/tài liệu và cấu hình pytest; không thay frontend/runtime.
- PASS harness D:/HealthBeauty/.p801-check.py: container test có label riêng đã dọn; PostgreSQL ID/start/mount/config, root.env hash, named volume/network giữ nguyên. Không seed/DDL hoặc mutation trên DB nghiệp vụ; metadata audit chỉ READ ONLY. Không build/up/restart app hoặc PostgreSQL, không AWS/Terraform/commit/push.

NOT RUN S3 thật upload/HEAD/conditional PUT/CORS/IAM/delivery do chưa có bucket; P8-01 và P6-03 giữ IN_PROGRESS. Browser hành trình tổng thể, load/nhiều tiến trình, HTTPS/điện thoại vật lý thuộc các bước sau, không tuyên bố đã hoàn tất. Dừng sau phạm vi P8-01 hiện có; xem [test-matrix.md](test-matrix.md).

# Trạng thái trước — P7-04 DONE (11/11/2026)

Theo yêu cầu làm tiếp sau danh sách việc còn thiếu, triển khai đúng P7-04 cây danh mục. Có GET /api/v1/admin/categories gồm inactive, POST create/PATCH name/slug/parent/is_active; ADMIN ACTIVE theo DB, USER/Seller403/guest401, CSRF/Origin/no-store. Name trim1..120, slug lowercase/hyphen1..140 unique, parent BIGINT/null, bool strict; PATCH nonempty/no extra/null chỉ parent. Không delete/schema/FK changes. Mutation response node children=[], GET đọc cây đầy đủ.

Thêm exclusive PostgreSQL advisory lock cùng key(731921,1) với shared lock checkout/catalog writes, sau user và giữ đến COMMIT. Đọc lại mapping sau khóa, validate toàn bộ cây đề xuất để chặn self/multinode/concurrent cycle, parent thiếu, slug trùng và depth kỹ thuật100 cấp khớp public client. Read cây không âm thầm bỏ malformed nodes. Slug409/parent422/cycle409/missing404, DB/COMMIT503 sanitized/rollback. Tắt cha không cascade sửa con hoặc product/order/stock; public/cart/checkout dựa ancestors. Không expected_version; serialize bảo toàn cây, không hứa phát hiện mọi stale field edit.

UI /admin/categories/nav Danh mục/returnTo exact, cây phẳng có cấp/path, trạng thái node và ẩn do cha. Form name/slug gợi ý từ tiếng Việt/parent/active, loại self+descendants khỏi parent select, review/confirm trước lưu, loading/empty/error/retry, abort/account/expiry privacy. Lost response bỏ form/kết quả, GET xác minh không auto replay/create duplicate. Không tự tạo danh mục nghiệp vụ khi triển khai.

- PASS438 backend full PostgreSQL16 tmpfs marketplace_test riêng + metadata audit hiện hữu READ ONLY;21 cases mới: create/edit/root/parent inactive/read-only/no N+1, self/multinode cycle, cross-Admin reparent race/slug race, tắt cha giữ children/product/stock/order và race checkout atomic, permissions/CSRF/validation/no delete/COMMIT rollback/100-level boundary. Có3 Pydantic alias warnings payload/item_id trong concurrent tests, không fail/skip; Ruff check/format PASS127 files.
- PASS77 frontend tests, thêm4 nhóm tree identity/parent/duplicate/depth/effective visibility, descendant exclusion, client allowlist/CSRF/no retry và proxy/returnTo/security; lint/typecheck/local production build và Docker backend/frontend build PASS.
- PASS browser thật Next→FastAPI→PostgreSQL test: empty→parent/child/slug auto, edit/reparent/root, disable-enable inherited public visibility/product404/cart CATEGORY_UNAVAILABLE/checkout409 nhưng order snapshot nguyên, Seller403, stale form cycle409, create COMMIT response mất→GET đúng1 node không replay, slug duplicate409,503 retry/expiry/privacy/login returnTo và320/390/768/1440 không overflow/JS errors. Đã xem p704-categories-390.png/p704-categories-1440.png. D:/HealthBeauty/.p704-* resources test riêng đã dọn, không dùng fixtures DB thật.
- PASS live localhost guest Admin categories UI/login returnTo/navigation/4widths, không data/overflow/JS errors; API guest401/query400/hostile403/readiness200. Không đăng nhập thay Admin thật hoặc tạo/sửa danh mục nghiệp vụ. Chỉ app build/up --no-deps healthy, giữ canonical LAN cũ/alias localhost.
- PASS .p704-original.json trước/sau: PostgreSQL ID/StartedAt/mount/config/root.env hash/named volume/network giữ nguyên (normalize mount order). Không restart/recreate postgres/DDL/seed/data/env/Compose/dependency/AWS/Terraform/commit/push.

Hướng dẫn [admin-categories.md](admin-categories.md). NOT RUN tải cao/HTTPS/điện thoại vật lý; S3 P6-03 còn chờ bucket. Dừng sau P7-04, chưa mở P8 regression tổng thể.

# Trạng thái trước — P7-03 DONE (11/11/2026)

Người dùng ngắt lượt chuẩn bị data và yêu cầu “hãy tạo web tiếp”; chuyển sang một task P7-03 kế tiếp. Chưa tạo workbook/builder/data hoặc nhập sản phẩm từ lượt spreadsheet, chỉ đã đọc skill. Không triển khai P7-04 trong lượt này.

Có GET /api/v1/admin/products search tên/SKU/shop_id/is_active/page, POST /{id}/hide; chỉ ADMIN ACTIVE theo DB, Seller403. Admin xem/ẩn mọi shop_status, response AdminProduct private không raw image_key/owner PII, ID/Decimal string/UTC. Batch images, không N+1. Tách projection sản phẩm quản lý dùng chung Seller/Admin, giữ Seller ownership. Read READ ONLY/no-store; write user→shared category→shop→product locks/conditional active=false đến COMMIT, lỗi503 sanitized/rollback/no-op đã ẩn.

UI /admin/products, nav quản trị thêm Sản phẩm, login returnTo đúng path; filter shopID/active/search, thông tin/SKU/giá/tồn/mô tả/link ảnh HTTPS, xác nhận ẩn, loading/empty/error/retry/page. Không fake ảnh; is_active chỉ là bật/ẩn, public vẫn cần shop/category hợp lệ. Không auto retry mutation; lost response xóa xác nhận/kết quả và yêu cầu GET, role/expiry clear private data. Schema không phân biệt ai ẩn nên giữ không reactivation cho cả Admin/Seller như contract; Seller PATCH is_active bị từ chối, sửa giá/mô tả không bật lại. Không xóa sản phẩm/ảnh/đơn hoặc giảm/hoàn tồn; order snapshot bất biến.

- PASS417 backend full PostgreSQL16 tmpfs marketplace_test riêng + metadata audit DB hiện hữu READ ONLY. Thêm16 integration cases cho search/filter/page/read-only/projection/no N+1, public/detail/cart/checkout, no Seller reactivation, snapshot bốn shop_status, hide vs checkout/Seller edit, permissions/validation/COMMIT rollback. Full có1 Pydantic alias warning query ở inventory concurrency, không fail/skip. Shared Seller projection regression PASS; Ruff check/format PASS.
- PASS73 frontend tests, thêm4 nhóm projection/stock/Decimal/unsafe image/returnTo, page/shop/active/duplicates/search encoding, hide no retry/CSRF, proxy/path/query/Origin/cookie. Lint/typecheck/local production build/Docker backend/frontend build PASS.
- PASS browser thật Next→FastAPI→PostgreSQL test: USER403, hai shops, filter/SKU/shop/active, hide thường và mất phản hồi sau COMMIT→GET xác minh không replay, public detail404/search không còn/cart HIDDEN_PRODUCT/checkout409; Seller is_active422/sửa giá không bật lại, order snapshot giữ nguyên;28products phân trang/empty/503 retry/expiry/privacy/login returnTo và320/390/768/1440 không overflow/JS errors. Harness đầu gọi nhầm public catalog qua Next private proxy không có route nên JSON parse fail; sửa harness gọi đúng API public test, lượt cuối PASS. Đã xem p703-products-390.png/p703-products-1440.png. D:/HealthBeauty/.p703-* fixtures có guard DB test riêng, processes/containers đã dọn.
- PASS live localhost:3001 guest Admin products UI/returnTo/navigation/4widths, không PII/overflow/JS errors; API401/query400/hostile403/readiness200. Không đăng nhập thay user Admin hoặc ẩn/tạo sản phẩm nghiệp vụ. Chỉ app build/up --no-deps healthy, giữ origin LAN cũ/alias localhost.
- PASS .p703-original.json đầu/cuối: PostgreSQL ID/start/mount/config/root.env hash/volume/network giữ nguyên (chuẩn hóa mount order); không restart/recreate postgres/schema/data/seed/env/Compose/dependency/AWS/Terraform/commit/push.

Hướng dẫn [admin-products.md](admin-products.md). NOT RUN load/HTTPS/điện thoại vật lý/real S3; P6-03 chờ bucket. Dừng sau P7-03, chưa mở P7-04.

# Trạng thái trước — P7-02 DONE (11/11/2026)

Theo yêu cầu làm tiếp sau cấp Admin, triển khai P7-02 phê duyệt/khóa shop. GET /api/v1/admin/shops search tên/slug/contact_email, status/page; PATCH /{id}/status expected_status/shop_status. Chỉ ADMIN ACTIVE theo DB, Seller không tự approve. PENDING→APPROVED/REJECTED, APPROVED→LOCKED; không unlock/resubmit. Same-target no-op, stale409 INVALID_TRANSITION, missing404, input extra422. Shape ShopPrivate/ID string/UTC/logo_url null, không raw key/PII tài khoản owner. Count+page ổn định không N+1, read READ ONLY/no-store.

Mutation khóa user Admin→shop, conditional transition đến COMMIT; cùng shop lock với checkout. Khóa commit trước chặn đơn mới, đơn commit trước giữ nguyên; không chỉnh product/stock/order hay tự hủy/hoàn tồn. Owner ACTIVE xử lý đơn cũ ở LOCKED; catalog/inventory bị chặn như policy có sẵn. DB/COMMIT lỗi503 sanitized/rollback. Next proxy exact allowlist/CSRF/Origin/cookie; client projection/identity/page, không retry mutation, stale/lost response xóa kết quả/xác nhận và GET xác minh; account/expiry clear privacy.

UI /admin/shops có confirm approve/reject/lock, search/filter/page/empty/error/loading/retry, điều hướng Người dùng/Gian hàng dùng chung; returnTo chỉ mở thêm đúng /admin/shops. Không link giả hoặc thao tác mở khóa chưa có.

- PASS401 backend full với PostgreSQL16 tmpfs marketplace_test riêng và metadata audit DB hiện hữu READ ONLY. Thêm16 cases Admin shops (ma trận16 transition trong1case, readonly/search/page/no N+1, validation/permissions/self-approve, rollback, approve-vs-reject, lock vs checkout, giữ đơn cũ). Full có3 Pydantic alias warnings payload/item_id trong concurrent tests hiện hữu, không fail/skip. Sau full cải thiện test lấy timestamp fixture sau COMMIT, chạy focused16cases PASS; source nghiệp vụ không đổi. Ruff check/format PASS116 files.
- PASS69 frontend tests gồm4 nhóm mới projection/private fields, search/page/duplicate/filter validation, transition/client/no retry, proxy/returnTo/security. Lint/typecheck/local production build/Docker backend/frontend build PASS.
- PASS browser thật Next→FastAPI→PostgreSQL test: Admin phê duyệt→Seller tạo sản phẩm→Buyer checkout, khóa→checkout mới409/catalog404/Seller catalog403 nhưng Seller CONFIRMED đơn cũ được; reject/không unlock, mất phản hồi sau COMMIT đọc lại không replay, stale409,27shops page/filter/empty,503 retry/expiry/login returnTo,320/390/768/1440 không overflow/JS errors. Đã xem screenshot desktop/mobile p702-shops-390.png/p702-shops-1440.png; harness D:/HealthBeauty/.p702-*, fixtures test DB có guard; processes/containers riêng đã dọn.
- PASS live localhost:3001 guest /admin/shops/returnTo/navigation tới users ở bốn viewport, không PII/overflow/JS errors; API guest401/query400/hostile403/readiness200. Không đăng nhập thay Admin người dùng hoặc approve/reject/lock shop nghiệp vụ. Chỉ build/up app --no-deps healthy, giữ origin LAN cũ + alias localhost.
- PASS baseline .p702-original.json đầu/cuối: PostgreSQL ID/StartedAt/mount/config/root.env hash/named volume/network giữ nguyên (chuẩn hóa thứ tự mounts). Không restart/recreate postgres/schema/seed/data/env/Compose/dependency/AWS/Terraform/commit/push.

Hướng dẫn [admin-shops.md](admin-shops.md). NOT RUN tải cao/HTTPS/điện thoại vật lý; S3 P6-03 vẫn chờ bucket. Dừng sau P7-02, chưa mở P7-03/P7-04.

# Trạng thái trước — ADMIN-GRANT-01 DONE (11/11/2026)

Người dùng đã gửi email tài khoản cần cấp quyền sau yêu cầu cấp ADMIN. CLI preview READ ONLY tìm đúng user_id1, ACTIVE/USER; apply với expected-user-id1 thành công changed=true, role ADMIN. Chạy preview lần nữa từ transaction riêng xác nhận cùng ID ACTIVE/ADMIN, dry_run=true/changed=false. Không đưa email/PII vào tài liệu repository; định danh target đã có trong hội thoại.

Chỉ thực thi CLI đã kiểm thử ở backend container đang chạy, không rebuild/restart container/PostgreSQL, không schema/sequence/seed/create account/password/status/shop changes. Thay user_role và updated_at của đúng target theo ủy quyền trực tiếp. Không yêu cầu password hoặc đăng nhập thay người dùng. PASS383 backend full +11 targeted CLI tests ở lượt chuẩn bị; lượt này không đổi code nên không chạy lại full tests/build. Xác minh thật bằng đọc DB thông qua CLI, chưa kiểm tra phiên trình duyệt của người dùng. Có thể tải lại hoặc đăng nhập rồi mở /admin/users. Dừng sau ADMIN-GRANT-01, không mở P7-02.

# Trạng thái trước — ADMIN-GRANT-01 chuẩn bị CLI xong, chờ tài khoản đích (11/11/2026)

Người dùng hỏi cách cấp quyền quản trị và yêu cầu làm tiếp. Đã hỏi email tài khoản đã đăng ký, không hỏi mật khẩu; chưa có email đích nên chưa cấp quyền trên DB nghiệp vụ, không đoán tài khoản đầu tiên. Scope lần này là công cụ và thao tác cấp Admin được chỉ định; chưa mở P7-02.

Thêm CLI operator-only python -m app.grant_admin, repository/service riêng, không HTTP route tự nâng quyền. Mặc định preview READ ONLY đúng email chuẩn hóa giống login; apply bắt buộc expected user ID khớp preview, target ACTIVE hiện hữu, row lock/conditional USER→ADMIN + updated_at cùng COMMIT. Already ADMIN no-op, không đổi hash/email/status/shop/schema/sequence. Missing/locked/mismatched/invalid target fail closed; CLI environment local/test, lỗi sạch không DSN/secret. Kết quả thành công chỉ in sau COMMIT. Hướng dẫn [grant-admin.md](grant-admin.md); Admin trong UI P7-01 vẫn chỉ xem theo phạm vi đã thống nhất.

- PASS383 backend full PostgreSQL16 tmpfs marketplace_test riêng + metadata audit hiện hữu READ ONLY; preview/no-password-query, grant đúng user và JWT cũ có quyền ở request tiếp theo, preserve hash/status/user khác, missing/locked/mismatch/no expected ID, no-op/concurrent/COMMIT rollback. Sau lượt full thêm test che DSN và subprocess CLI thật; PASS11 targeted tests trên DB test riêng, gồm2 test mới, không gọi chúng là đã nằm trong lượt383. Ruff check/format PASS111 files.
- PASS Docker backend build/up --no-deps healthy, python -m app.grant_admin --help chạy trong container, readiness200. Chỉ backend thay đổi; frontend/tests/build không chạy lại vì không có thay đổi frontend, kết quả P7-01 giữ nguyên làm baseline.
- PASS baseline .admin-grant-original.json trước/sau: PostgreSQL ID/start/mount/config/root.env hash/named volume/network giữ nguyên, chuẩn hóa thứ tự mounts. Hai DB test riêng được dọn, không restart/recreate postgres/DDL/seed/test account trên DB nghiệp vụ, không env/Compose/dependency/AWS/Terraform/commit/push.

ADMIN-GRANT-01 vẫn IN_PROGRESS vì thiếu email đích. CLI đã sẵn sàng; chưa có preview/apply cho bất kỳ tài khoản nghiệp vụ nào. Khi người dùng gửi email được chỉ định, tiếp tục preview→kiểm ID/status→apply và xác minh role bằng read, không yêu cầu gửi mật khẩu hay xin lại quyền cấp ADMIN đã được yêu cầu.

# Trạng thái trước — P7-01 DONE trong phạm vi đã điều chỉnh (11/11/2026)

Theo yêu cầu “tiếp”, thực hiện P7-01 quản trị người dùng. Người dùng yêu cầu giải thích chính sách khóa Admin rồi trả lời “bỏ qua phần đó”; đã thông báo bỏ thao tác khóa/mở khóa ADMIN, chỉ xem Admin, tiếp tục USER. Không coi đây là đồng ý chọn chính sách khóa Admin trong tương lai. PATCH mọi target ADMIN403 ADMIN_PROTECTED kể cả self/ACTIVE no-op/locked Admin; UI Admin chỉ xem disabled. Không nâng quyền/cấp tài khoản Admin trên DB nghiệp vụ.

GET /api/v1/admin/users tìm tên/email/phone (q≤200, escape literal %/_/backslash), lọc ACTIVE/LOCKED, phân trang24/max100 ổn định created_at DESC,user_id DESC, count+page không N+1. Chỉ chọn response columns, không password_hash. PATCH /admin/users/{id}/status chỉ user_status ACTIVE/LOCKED của USER, extra fields422/missing404; cùng trạng thái no-op không đổi updated_at. ADMIN ACTIVE theo DB mới được dùng; USER/locked/demoted từ chối, không tin role JWT/client. Read READ ONLY; write CSRF/Origin, kiểm quyền ban đầu, khóa actor+target user theo ID rồi recheck role/status, giữ đến COMMIT; lỗi503 sanitized/rollback. Khóa USER ảnh hưởng protected request tiếp theo, mở khóa không đổi role/shop hoặc hủy đơn. Token chưa hết hạn dùng tiếp sau mở khóa, không tuyên bố revoke copied JWT.

UI /admin/users, /admin redirect, link từ tài khoản ADMIN, login returnTo allowlist đúng /admin/users; USER thấy không có quyền. Search/filter/page/loading/empty/error/retry/confirm/submit guard; lost response bỏ kết quả/xác nhận cũ và GET xác minh, không retry mutation. Client validate/projection/no browser PII storage; role thay đổi/expiry xóa dữ liệu riêng.

- PASS374 backend full với PostgreSQL16 tmpfs marketplace_test riêng và metadata audit DB hiện hữu READ ONLY;16 test cases mới cho permissions/search/escape/page/projection/no password SQL/READ ONLY/lock-unlock token cũ/readonly Admin/CSRF/mass assignment/rollback/concurrent Admin. Lượt cuối không fail/skip/warning; Ruff check/format PASS. Lượt đầu test SQL observer gắn engine fixture trong khi TestClient dùng engine riêng nên kiểm READ ONLY fail; sửa test override cùng session, kiểm chứng cuối PASS.
- PASS65 frontend tests, thêm4 nhóm projection/validation/search/page/no retry/proxy/returnTo; lint/typecheck/local production build và Docker backend/frontend build PASS. Browser phát hiện select label chứa text options; thêm aria-label rõ ràng, build/checks cuối trên source đã sửa.
- PASS browser thật Next→FastAPI→PostgreSQL test: USER403, account link,27 users phân trang/search/status/empty, lock/unlock với JWT đã có, mất phản hồi sau COMMIT rồi read recovery không lặp ghi, Admin chỉ xem/API403,503 retry, thu hồi role/expiry xóa list và login về /admin/users,320/390/768/1440 không overflow/JS errors. Đã xem screenshot desktop/mobile p701-users-390.png/p701-users-1440.png. Harness đầu trùng nút search với header và chưa chờ navigation; sửa scope/wait, lượt cuối PASS. Harness/fixtures D:/HealthBeauty/.p701-* chỉ test DB được guard; containers/processes riêng đã dọn.
- PASS live localhost:3001 /admin/users và /admin redirect, login returnTo, guest401/query400/hostile403/readiness200 và bốn viewport. Không truy cập PII bằng account thật, không tạo/nâng quyền/khóa user test trên DB nghiệp vụ. Chỉ build/up app --no-deps healthy, giữ LAN canonical cũ/alias localhost; không đổi cấu hình mạng.
- PASS .p701-original.json đầu/cuối: PostgreSQL ID/StartedAt/mount/config, root.env hash, named volume/network giữ nguyên (chuẩn hóa thứ tự Mounts). Không restart/recreate postgres/schema/data/SQL/env/Compose/dependency changes, không AWS/Terraform/commit/push.

Hướng dẫn [admin-users.md](admin-users.md). NOT RUN tải cao/HTTPS/điện thoại vật lý; trạng thái ADMIN nằm ngoài phạm vi hiện tại. S3 P6-03 còn IN_PROGRESS chờ bucket. Dừng sau P7-01, chưa mở phê duyệt shop P7-02.

# Trạng thái trước — P6-05 DONE (11/11/2026)

Theo yêu cầu “làm tiếp”, triển khai đúng một task kế tiếp P6-05. Seller có GET list/filter/status/page/detail và PATCH status tại /api/v1/seller/orders; giao diện /kenh-nguoi-ban/don-hang và /{shop_order_id}, link từ gian hàng/sản phẩm. Danh sách không PII, detail chỉ shipping/items snapshot shop mình, không tổng/dòng shop khác. User ACTIVE/shop APPROVED hoặc LOCKED xử lý đơn cũ; foreign404 kể cả Admin, không impersonation. Read READ ONLY, private no-store.

Buyer có POST /orders/{id}/shop-orders/{sid}/cancel và nút hủy ở chi tiết đơn mua. Buyer PENDING→CANCELLED; Seller PENDING→CONFIRMED→SHIPPING→COMPLETED hoặc hủy PENDING/CONFIRMED. Expected status kiểm dưới khóa, đúng target hiện tại no-op không đổi updated_at; terminal không sửa. Khóa user→shop→product→inventory→shop_order theo thứ tự chung, conditional transition và hoàn tồn snapshot cùng COMMIT; CANCELLED guard không cộng lần hai. Thiếu inventory/overflow409 rollback, lỗi COMMIT503 đã làm sạch. UI xác nhận, submit guard, lỗi/stale/mất phản hồi yêu cầu GET xác minh, không tự retry mutation; expiry xóa dữ liệu riêng, không PII browser storage. COD/vận chuyển vẫn mô phỏng.

- PASS358 backend full PostgreSQL16 tmpfs marketplace_test riêng + metadata audit DB hiện hữu READ ONLY. Thêm14 integration test cases, trong đó ma trận25 transitions, Buyer terminal, snapshots/ownership/Admin/locked shop/user, Buyer–Seller cancel đồng thời, confirm đua cancel, cancel đua checkout/chỉnh tồn, missing/overflow/COMMIT rollback. Lượt cuối có3 Pydantic UnsupportedFieldAttributeWarning alias image_id/product_id, không fail/skip. Ruff check/format PASS,101 files formatted; không dependency/schema changes.
- PASS61 frontend tests, thêm4 nhóm projection/identity/exact-money/privacy/client/no retry/proxy/security; lint/typecheck/local production build và Docker backend/frontend build PASS. Đã chỉnh style nút và tách tên/giá sau khi xem ảnh panel, build/browser lượt cuối dùng CSS mới.
- PASS browser thật Next→FastAPI→PostgreSQL test: hai Seller/một Buyer, checkout→xác nhận→giao→hoàn tất, Buyer hủy đúng shop, Seller hủy CONFIRMED, stale expected, mất phản hồi sau COMMIT của cả hai luồng hủy rồi GET xác minh không replay, cross-shop404/snapshot privacy, filter/phân trang25 đơn, LOCKED xử lý đơn cũ,503 retry/expiry và320/390/768/1440 không overflow/JS errors. Đã xem ảnh desktop/mobile p605-detail-390.png/p605-detail-1440.png. Các lượt harness đầu sai slug/email casing, chờ UI đang lưu chưa xong, hiểu nhầm same-target no-op và selector trùng Next announcer; đã sửa harness theo contract, lượt cuối PASS. Harness D:/HealthBeauty/.p605-*; test containers/processes đã dọn.
- PASS runtime localhost:3001 list/detail Seller/detail Buyer ở bốn viewport, login returnTo, guest401/query400/hostile403/readiness200, không JS errors/overflow. Không login account thật hoặc tạo fixture/account/shop/order trên DB nghiệp vụ. Chỉ build/up app --no-deps, giữ canonical LAN cũ và alias localhost; không đổi network/firewall/IP origin.
- PASS baseline .p605-original.json trước/sau: PostgreSQL ID/StartedAt/mount/config, root.env hash, volume/network giữ nguyên; chuẩn hóa thứ tự Mounts khi đối chiếu. Không restart/recreate PostgreSQL, schema/data/SQL/env/Compose/dependency/Terraform changes, không AWS/commit/push.

Hướng dẫn [seller-orders.md](seller-orders.md). Chưa kiểm tra tải cao/HTTPS/điện thoại vật lý/thanh toán hoặc hãng vận chuyển thật; S3 P6-03 còn IN_PROGRESS chờ bucket. Dừng sau P6-05, không mở P7.

# Trạng thái trước — FIX-AUTH-03 và P6-04 DONE (10/11/2026)

Theo yêu cầu đăng nhập về trang chủ và làm tiếp, đổi fallback safeReturnPath từ /tai-khoan thành /. Trước đây login thường không có returnTo nên vào trang tài khoản COCO; đây là đích đến mặc định, không phải đăng nhập sang tài khoản khác. Các returnTo hợp lệ vẫn giữ, gồm trang tài khoản được bảo vệ, giỏ hàng và Seller; đường dẫn không an toàn quay về /. Không sửa phiên/quyền/account hay nới CSRF.

P6-04: GET Seller inventory và POST adjustments với delta/X-Expected-Quantity, lock user→shared category→shop→product→inventory và conditional UPDATE, giữ transaction đến COMMIT. Kiểm tra quyền ACTIVE owner/shop APPROVED, stale, bounds trước SQL arithmetic; thiếu tồn không tạo giả0, foreign404 cả Admin, sản phẩm ẩn không tự public lại. UI nhập/xuất có bước xác nhận, cập nhật danh sách theo server, tải lại sau stale/lỗi/mất phản hồi, không replay delta; expiry xóa dữ liệu riêng. Xem [seller-inventory.md](seller-inventory.md).

- PASS344 backend full trên PostgreSQL16 tmpfs marketplace_test riêng + metadata audit hiện hữu READ ONLY, thêm21 integration cases cho validation/permissions/bounds/stale/rollback/concurrency với checkout. Ruff check/format PASS; không đổi dependency/schema.
- PASS57 frontend tests (thêm4 cho redirect/projection/client/proxy), lint/typecheck/local production build/Docker backend/frontend build.
- PASS browser thật Next→FastAPI→PostgreSQL test: đăng nhập form canonical/localhost alias về trang chủ; explicit returnTo giỏ hàng được giữ; nhập/xuất, underflow, stale, phản hồi mất sau COMMIT rồi GET thấy đúng tồn không lặp ghi, cập nhật row, hết phiên xóa panel,320/390/768/1440 không overflow/JS errors. Đã xem ảnh panel390. Harness D:/HealthBeauty/.inventory-*; test processes/container đã dọn. Lượt đầu harness lỗi encoding label tiếng Việt; sửa harness, lượt cuối PASS.
- PASS up riêng app --no-deps healthy và live localhost:3001: login tới401 INVALID_CREDENTIALS thay vì CSRF403 với email probe không tồn tại, request hợp lệ422/hostile-token403/guest401;7 route/bốn viewport/logo/readiness PASS. Không tạo fixture/account/shop/product trên DB nghiệp vụ.
- Đối chiếu baseline đầu lượt tiếp tục .inventory-baseline.json: PostgreSQL ID/StartedAt/mount/config/root.env hash/named volume/network giữ nguyên (chuẩn hóa thứ tự Mounts khi so sánh). Baseline cũ .p604-baseline.json có StartedAt07:06:45Z, trong khi trước kiểm thử lượt tiếp tục đã là16:28:39Z cùng ID; không khẳng định bảo toàn thời điểm khởi động giữa hai lượt. Không lệnh restart/recreate postgres trong lượt này.

LAN cũ192.168.110.101 hiện không kết nối; Wi-Fi máy hiện192.168.0.109. Giữ cấu hình canonical LAN cũ và alias localhost theo phạm vi đã thống nhất; chưa đổi origin/router/firewall. Live kiểm chứng qua localhost, không báo LAN cũ PASS. Chưa kiểm tra điện thoại vật lý/HTTPS/load/S3 thật. P6-03 còn IN_PROGRESS chờ bucket; dừng sau P6-04, chưa mở P6-05. Không AWS/Terraform/commit/push, không đổi root.env hay dữ liệu nghiệp vụ.

# Trạng thái trước — FIX-AUTH-02 DONE (10/11/2026)

Người dùng báo đăng nhập “Phiên xác thực đã thay đổi” và xác nhận dùng localhost:3001. Tái hiện trên runtime: cả hai app chỉ chấp nhận MARKETPLACE_PUBLIC_ORIGIN=http://192.168.110.101:3001; GET csrf200 nhưng POST login từ localhost403 CSRF_FAILED, cùng body rỗng từ LAN422 VALIDATION_ERROR. Đây là lệch origin sau cấu hình LAN, chưa tới kiểm mật khẩu; không phải bằng chứng tài khoản sai.

Sửa bằng additional_origins JSON allowlist rõ ràng trong backend Settings/Security và frontend proxy. Compose hai app mặc định thêm đúng http://localhost:3001 ngoài canonical LAN; .env.example ghi cách cấu hình. Không rewrite Origin, không trust Host/Forwarded, không wildcard và không bỏ kiểm token/cookie/session binding. Origin/Referer lạ, sai port, giả token vẫn403. Config từ chối path/query/fragment/credentials và HTTP alias trong production. Cookie vẫn host-only, hai địa chỉ có phiên riêng. Root .env và JWT secret không đổi.

- PASS323 backend full với PostgreSQL16 tmpfs marketplace_test riêng+audit metadata DB hiện hữu READ ONLY;8 tests origin/validation/production mới. Ruff check/format/lock PASS.
- PASS53 frontend tests gồm proxy localhost/LAN/Referer, giữ header/cookie projection và fail closed khi alias config sai; lint/typecheck/local production build/Docker build PASS.
- PASS browser E2E thật Next→FastAPI→PostgreSQL test: register fixture riêng, login form qua canonical và localhost alias, auth/me200, cookie tách host, hostile/token403, Referer hợp lệ422, không JS errors. Test resources đã dọn.
- PASS live localhost:3001 và192.168.110.101:3001: login form với email probe không tồn tại tới401 INVALID_CREDENTIALS thay vì CSRF403; body rỗng422, hostile Origin/token giả403, guest shop401. Không đăng nhập bằng account người dùng hoặc tạo account/shop/order test trên DB thật.
- Build/up riêng backend/frontend --no-deps healthy, giữ origin LAN và alias localhost. Đối chiếu PostgreSQL ID/start/mount/config, root .env hash, volume/network trước-sau. Không schema/data/secret/dependency/Terraform changes, không AWS/commit/push. P6-03 còn chờ bucket thật, không mở task mới.

Hướng dẫn: [mobile-local.md](mobile-local.md). Harness D:/HealthBeauty/.auth02-*. Mở http://localhost:3001/dang-nhap rồi tải lại trang và thử tài khoản của mình; không cần gửi mật khẩu qua chat. Điện thoại vật lý/HTTPS vẫn ngoài kiểm chứng lượt này.

# Trạng thái trước — BRAND-02 DONE; P6-03 code đã chuẩn bị, IN_PROGRESS (10/11/2026)

Theo yêu cầu logo bỏ khung trắng/cao to hơn và làm tiếp, đã dùng skill imagegen/background-extraction trên loho.png, giữ ảnh nguồn và asset cũ. Asset mới frontend/public/images/coco-logo-transparent.png2193×717 có alpha0..255/cả4 góc0; giữ túi/chữ/tia/sao và chi tiết trắng trong túi. BrandLogo chung/favicons dùng ảnh mới, bỏ border-radius/nền trắng, cao84px desktop và58px mobile (auth/Seller50px, shipping nhỏ40px). Đã xem screenshot header mới: logo hòa vào nền, lớn hơn rõ so với BRAND-01; không crop mất chữ hoặc kéo giãn.

Người dùng xác nhận chưa có bucket và yêu cầu chuẩn bị code/hướng dẫn, không triển khai storage. P6-03 đã bổ sung presigned POST5 phút chính xác MIME/size/key, grant ký riêng, upload staging theo shop/product, HEAD/ETag/bounded GET/Pillow verify-decode để kiểm ảnh thật≤5MiB/4096px/16MP, rồi conditional PUT vào key immutable khác staging. DB chỉ giữ key; primary unset/flush/set cùng transaction và khóa user→category→shop→product; DELETE chỉ bỏ reference, không xóa object. Public catalog/detail, Seller và cart sinh URL từ key đã xác minh; presigned GET15 phút hoặc HTTPS CDN base. Không cấu hình bucket giữ URL null và không khởi tạo SDK/credential discovery.

Seller có Quản lý ảnh: file/type/size/primary/sort/delete-confirm, same-origin CSRF proxy, S3 POST không cookie/app credentials, projection/ownership/expiry/error/retry/response-loss recovery. API trả image_upload_enabled=false và UI upload disabled khi bucket chưa có; API503 STORAGE_NOT_CONFIGURED thật. Chuẩn bị backend/storage.env.example và chỉ thêm backend/.env.storage optional env_file trong Compose, không tạo file private/đưa secret vào root.env/PostgreSQL/frontend. Thêm boto3/Pillow và cập nhật uv.lock; không schema/SQL/data changes.

- PASS315 backend full với PostgreSQL16 tmpfs marketplace_test riêng và audit metadata hiện hữu READ ONLY, thêm21 SDK/validation+7 integration tests cho key/metadata/expiry/MIME/SDK errors/ownership/status/CSRF/primary race/rollback/reference-only delete. Có1 Pydantic warning alias payload trong concurrent cart test hiện có; không test fail/skip ở lượt full. Ruff check/format/lock PASS. SDK double không phải S3 integration thật.
- PASS52 frontend tests, lint/typecheck/production build và Docker backend/frontend build. Browser thật Next→FastAPI→PostgreSQL test riêng PASS regression P6-02, image panel empty/missing-storage disabled/upload503, expiry/privacy; logo6 route và live7 route ở320/390/768/1440 không overflow/JS errors. Đã xem ảnh header/logo và panel desktop/mobile. Harness/screenshots D:/HealthBeauty/.p603-*, p603-logo.png, p603-storage-390.png, p603-storage-1440.png; test resources đã dọn.
- Chỉ build/up app --no-deps, giữ LAN origin http://192.168.110.101:3001; PostgreSQL ID/start/mount/config/root.env hash/volume/network được đối chiếu baseline. Không account/shop/product fixtures trên DB thật, không AWS bucket/upload/MinIO/Terraform/commit/push.

Hướng dẫn cấu hình IAM/CORS/endpoint/backend-only credential và checklist kiểm bucket thật: [s3-images.md](s3-images.md). NOT RUN: S3 thật upload/HEAD/conditional PUT/delivery/CORS/IAM/CDN/expiry/load/điện thoại vật lý. P6-03 vẫn IN_PROGRESS; scope chuẩn bị code đã xử lý, dừng không mở P6-04.

# Trạng thái trước — BRAND-01 và P6-02 DONE (10/11/2026)

Theo yêu cầu “cập nhật logo và làm tiếp”, dùng nguyên loho.png cho BrandLogo chung header/footer/auth/Seller và favicon; asset frontend/public/images/coco-logo.png giống byte ảnh nguồn. Không vẽ lại hoặc gán vào sản phẩm. Đã xem header desktop và trang Seller desktop/mobile; logo bảy route320/390/768/1440 không overflow/JS errors.

P6-02 có GET list/detail, POST create, PATCH và POST hide /api/v1/seller/products; UI /kenh-nguoi-ban/san-pham gọi proxy/API thật, link từ dashboard. ACTIVE owner/shop APPROVED mới quản lý; Admin không truy cập sản phẩm shop khác. SKU unique theo shop; input validate, chống mass assignment; category mới/đổi có toàn bộ tổ tiên active. ID/Decimal string, UTC; không PII/raw storage keys. Product+inventory transaction, inventory/COMMIT lỗi rollback toàn bộ. Khóa user→shared category→shop→product tương thích checkout; PATCH không overwrite tồn. Read APIs READ ONLY, list/search/filter/pagination ổn định, batch metadata ảnh không N+1.

Frontend có loading/empty/error/retry/confirm ẩn/submit guard, account isolation/expiry và response-loss recovery bằng đọc lại, không tự retry mutation hoặc lưu token/PII browser storage. Không bật lại/xóa sản phẩm, ảnh URL null tới P6-03.

- PASS287 backend full/PostgreSQL16 tmpfs marketplace_test riêng+metadata audit hiện hữu READ ONLY; thêm28 unit và9 integration tests cho quyền/visibility/SKU race/rollback/no N+1. Ruff check/format/lock PASS. Lỗi annotation list che type ở lượt đầu đã sửa trước checks cuối. So sánh bảo toàn ngay sau dọn container có khác biệt tạm thời; kiểm lại độc lập sau cleanup/update app xác nhận baseline giữ nguyên.
- PASS48 frontend tests/lint/typecheck/production build;3 nhóm projection/proxy/client/no retry mới. Browser thật Next→FastAPI→PostgreSQL16 riêng PASS: shop gate/create/edit/tồn/SKU conflict/hide/filter/pagination/response mất sau COMMIT→read recovery/503 retry/expiry privacy. E2E giúp sửa label danh mục bằng htmlFor/id và scope selector search riêng form; checks cuối dùng source đã sửa.
- PASS Docker build/up backend/frontend --no-deps healthy, giữ origin LAN http://192.168.110.101:3001. Live bảy route/bốn viewport, guest401/query400/ID404/hostile403/CSRF200/readiness200, không browser mutations. Không fixtures/account/shop/product test trên DB thật. PostgreSQL ID/StartedAt/mount/config/root.env hash/volume/network trước-sau giữ nguyên; test processes/container đã dọn.

Hướng dẫn/giới hạn: [seller-products.md](seller-products.md). Harness/screenshots D:/HealthBeauty/.p602-*, p602-products-390.png, p602-products-1440.png, p602-logo.png. Không schema/SQL/data/Compose/env/dependency/Terraform changes, không AWS/commit/push. S3 ảnh/chỉnh tồn/đơn Seller/HTTPS/load/điện thoại vật lý chưa làm; dừng sau BRAND-01/P6-02, không tự mở P6-03.

# Trạng thái trước — UI-16 DONE (10/11/2026)

Theo yêu cầu màu logo COCO phải giống nhau, đã bỏ các màu riêng ở header Seller/auth/footer đăng ký và thay màu base wordmark bằng CSS token `--color-coco-logo: #0066ff`. BrandLogo dùng chung áp dụng cho trang chủ/danh sách/auth/Seller/footer; SVG nét trang trí có stroke=currentColor nên khớp chữ. Chỉ sửa màu, không mở task vận chuyển từ ảnh tham chiếu hoặc sửa artwork/typography/flow.

PASS lint/typecheck/Docker production build. Browser qua URL LAN kiểm20 logo header/footer trên6 route /,/san-pham,/dang-nhap,/dang-ky,/kenh-nguoi-ban,/tai-khoan/don-hang ở390/1440: chữ và SVG đều rgb(0,102,255), HTTP200, không overflow/JS errors. Đã xem screenshots header homepage/Seller. Không thêm tests lặp CSS hoặc chạy lại full250 backend/45 frontend vì không đổi logic/API; kiểm computed style và build phù hợp thay đổi.

PASS up riêng frontend --no-deps healthy, giữ MARKETPLACE_PUBLIC_ORIGIN=http://192.168.110.101:3001 theo cấu hình LAN hiện dùng. PostgreSQL ID/start/mount/config/volume/network/root .env hash giữ nguyên. Không backend/API/schema/data/Compose/env/dependency/Terraform changes, không commit/push/AWS. Điện thoại thật qua Wi-Fi và HTTPS chưa kiểm chứng; LAN browser PASS. Dừng sau UI-16.

Code tại frontend/src/app/globals.css: `:root { --color-coco-logo: #0066ff; }` và `.coco-wordmark { color: var(--color-coco-logo); }`. Xem trên http://192.168.110.101:3001, tải lại trang hoặc Ctrl+F5 trên máy tính. Khi chạy lại: `$env:MARKETPLACE_PUBLIC_ORIGIN='http://192.168.110.101:3001'`, `docker compose build frontend`, `docker compose up -d --no-deps --wait frontend`. Kết nối vẫn browser→Next proxy→FastAPI→PostgreSQL, không đổi API.

# Trạng thái trước — FIX-LAN-01 cấu hình local DONE (10/11/2026)

Sau ảnh điện thoại tải trắng/hiển thị5G, kiểm tra thấy localhost:3001 trả200 nhưng192.168.110.101:3001 không kết nối được; frontend vẫn bind127.0.0.1 và hai app origin localhost. Đã đổi chỉ binding frontend trong Compose thành0.0.0.0:3001→3000 và up --no-deps backend/frontend với MARKETPLACE_PUBLIC_ORIGIN=http://192.168.110.101:3001 trong PowerShell session. Không sửa root .env hoặc service PostgreSQL. Tài liệu [mobile-local.md](mobile-local.md) ghi cách giữ origin khi chạy lại; các task sau recreate app cần đặt biến origin LAN này nếu vẫn kiểm bằng điện thoại.

PASS compose config, hai app healthy, browser qua IP LAN HTTP200/form/artwork/390px/no JS errors, CSRF+Origin LAN hợp lệ đi tới validation422 với login body rỗng, hostile Origin403 và guest shop401. Không tạo account/shop/đơn test hoặc ghi DB thật. PASS PostgreSQL ID/start/mount/service config, named volume/network và root .env hash trước-sau giữ nguyên, git diff --check. Không source/dependency/schema/Terraform/AWS/commit/push; không lặp full tests vì không đổi code, đã smoke runtime cấu hình thực.

Điện thoại cần chuyển sang cùng Wi-Fi máy tính (Phuc An T2 2), mở http://192.168.110.101:3001; địa chỉ private LAN không dùng từ5G/Internet. Chưa kiểm chứng điện thoại thật/firewall/router từ thiết bị khác; không sửa firewall/router hoặc hứa truy cập từ xa. HTTPS/toàn bộ checkout mobile HTTP chưa kiểm chứng. Dừng sau sửa cấu hình LAN.

# Trạng thái trước — UI-15 DONE (10/11/2026)

Theo ảnh đăng ký bán hàng mới, header Kênh người bán đổi từ dropdown giới thiệu thành link trực tiếp /kenh-nguoi-ban. Guest thấy form ngay, bỏ màn hình Bán hàng cùng coco/Gian hàng của bạn bắt đầu từ đây; Continue guest dẫn login returnTo, không shop POST trái phép. User chưa có shop thấy cùng form sau GET404; đã có shop tiếp tục dashboard P6-01. Không mở P6-02.

Header riêng gọn có logo/search/auth và hướng dẫn trạng thái, nền xanh nhạt, headline/shop3D bên trái/form trắng phải, icons và benefits dưới theo mẫu. Minh họa tạo bằng skill imagegen, copy vào frontend/public/images/coco-seller-store.png; đây là artwork UI, không ảnh sản phẩm/shop thật hoặc S3 upload. Đã xem screenshot1672×941/mobile390 và chỉnh lại tỷ lệ card/nền. Responsive320/390/768/1100/1440/1672 không tràn hoặc JS errors.

Form dùng API hiện có: tên/mô tả/email, gợi ý slug từ tiếng Việt bỏ dấu/Đ/đ, có Tùy chỉnh đường dẫn shop cho trường hợp trùng. SĐT readonly từ auth/me, guest trống và không gửi phone trong payload shop; không thêm cột hoặc giả lưu SĐT riêng. Bước2 Gửi hồ sơ thay cài đặt vận chuyển vì hiện chưa có feature/schema vận chuyển. Không fake triệu khách/analytics/giao vận/payment. Submit thật tạo PENDING; còn JWT/CSRF/one-shop/unique slug/response-loss GET recovery. Không persist bản nháp/PII/JWT vào browser storage. Expiry/account change không hiển thị hồ sơ người trước.

- PASS45 frontend tests, lint/typecheck/production build, gồm test mới slug tiếng Việt/emoji/độ dài; proxy/client/ownership/CSRF regression giữ PASS. Có lỗi UTF-8 trong dữ liệu test tạo qua shell và một import lúc refactor đã được sửa; checks cuối PASS, không để font lỗi ở UI/breadcrumbs. Source cuối sửa hint hỗ trợ screen reader, lint/typecheck/Docker build PASS.
- PASS browser E2E thật Next production→FastAPI→PostgreSQL16 test riêng: direct link/form/search/auth return, guest không shop POST, phone account chỉ đọc/không payload, double submit1POST/create PENDING/slug auto, trùng slug409→custom→success, dashboard/patch shop cũ, drop response sau real COMMIT→đọc lại,503/error/retry, expiry bỏ dữ liệu riêng. Không tạo fixtures trên DB thật, test processes/container đã dọn.
- Backend không đổi nên không lặp full250 tests P6-01; E2E mới xác minh API thật. HTTPS/gateway/load chưa kiểm chứng. Không API/schema/SQL/data/Compose/env/secret/dependency/Terraform changes, không commit/push/AWS.
- PASS build/up riêng frontend --no-deps healthy; live header→form/asset/header gọn/responsive/Continue→login return, API401/readiness200 và0 shop POST guest. PostgreSQL ID/start/mount/service config, named volume/network và root .env hash trước-sau giữ nguyên. Git diff --check PASS với cảnh báo line ending .env.example đã có.

Code/giới hạn/manual QA: [seller-registration-ui.md](seller-registration-ui.md). Mở http://localhost:3001/kenh-nguoi-ban hoặc trang chủ → Kênh người bán, Ctrl+F5. Root lệnh `docker compose build frontend`, `docker compose up -d --no-deps --wait frontend`. Dừng sau UI-15; P6-02 vẫn chờ yêu cầu riêng.

# Trạng thái trước — P6-01 DONE (10/11/2026)

Theo yêu cầu làm gian hàng Seller, đã hoàn thành một task P6-01: đăng ký, xem/sửa hồ sơ shop và dashboard /kenh-nguoi-ban. Không mở P6-02 hoặc Admin. POST/GET/PATCH /api/v1/seller/shop thật; Seller là chủ shop, không role SELLER mới. USER/ADMIN ACTIVE đều thao tác shop mình; không impersonation/owner ID từ client. POST luôn PENDING, mỗi owner một shop và slug unique theo ràng buộc sẵn có. ReadAccess GET READ ONLY; WriteAccess khóa user→owned shop xuyên COMMIT. Race đăng ký cùng owner chỉ1x201/1x409 SHOP_EXISTS; khác owner trùng slug409 SLUG_EXISTS, không in-memory lock. Commit lỗi rollback và503 sanitized.

Hồ sơ gồm tên, slug cố định, mô tả và email liên hệ tùy chọn, status và timestamps/ID string/UTC; logo_url null, không raw storage key. PATCH chỉ tên/mô tả/email, nullable clear; cập nhật updated_at bằng giờ DB, không đổi status/owner/slug. Chủ shop ACTIVE xem/sửa hồ sơ mọi shop_status, thao tác không approve/resubmit/unlock. APPROVED mới link shop public; status khác public404. Body có field không cho phép hoặc validation sai422. Không thay schema/index/default hoặc tạo role/bảng mới.

Frontend cùng tone coco xanh nhạt, sidebar các link thật, form/bốn status, guest login returnTo đã allowlist, label/validation/loading/empty/error/retry/disabled/responsive. Header Kênh người bán và tài khoản dẫn tới dashboard. Next proxy fixed GET/POST/PATCH, cookie filtering/Origin/CSRF/no-store/query reject; body seller32KiB cho5.000 ký tự UTF-8, auth/cart/address vẫn8KiB. Projection kiểm đúng owner/BIGINT/status/timestamps, không browser token/storage PII. Submit ref guard; sau server201/200 mới success/session refresh. Mất response hoặc503/SHOP_EXISTS yêu cầu GET đọc lại hồ sơ trước ghi tiếp, không tự retry hoặc giả thành công. Không có button sản phẩm/tồn/đơn/Admin giả; chức năng đó vẫn chờ task riêng.

- PASS250 backend full tests với PostgreSQL16 tmpfs marketplace_test riêng và audit metadata hiện hữu READ ONLY.29 trường hợp mới: tạo PENDING/private projection/GET READ ONLY, patch4 status/nullable, foreign owner+ADMIN isolation, guest/CSRF/locked, mutation mass assignment và validation, race cùng owner/trùng slug qua hai app, rollback create/patch trước commit. Public không lộ owner/contact/raw key. Ruff check/format PASS; dependencies/lock không đổi.
- PASS44 frontend tests, lint/typecheck/production build, thêm4 nhóm test projection/input/return URL/proxy/client404 khác503/allowlisted write/no auto retry. Lint/typecheck sau sửa copy guidance PASS; Docker production build dùng source cuối PASS.
- PASS Chrome E2E Next production→FastAPI→PostgreSQL16 riêng: guest→login UI→return seller, register submit đôi chỉ1POST, edit/clear/reload,4 status/public APPROVED, slug conflict/retry và shop độc lập, owner/status injection422, response bị drop sau real commit→đọc lại shop,503/error/retry, locked user/expiry không lộ hồ sơ. Responsive320/390/768/1440 không overflow/JS errors; xem ảnh desktop/mobile. Đổi trạng thái chỉ fixture test, không Admin API hoặc DB thật. Test container/process riêng đã dọn.
- PASS Docker build/up backend+frontend --no-deps, healthy. Live header→seller guest→login return, API401/no-store, query400/method405, readiness/OpenAPI GET/POST/PATCH, responsive không JS errors. Không đăng ký shop/tài khoản test hoặc ghi dữ liệu trên DB hiện hữu.
- PASS PostgreSQL ID/start/mount/config, volume/network và root .env hash giữ nguyên trước-sau. Không SQL/schema/data/Compose/env/secret/dependency/lock/Terraform changes, không commit/push/AWS. Chưa kiểm HTTPS/gateway/load. Admin duyệt P7-02, quản lý sản phẩm P6-02, ảnh/tồn/đơn Seller vẫn chưa làm. PATCH serialize theo khóa nhưng chưa có version/ETag để phát hiện mọi stale edit; ghi rõ giới hạn, không hứa chống ghi đè nhiều tab.

Code/API/manual QA: [seller-shop.md](seller-shop.md). Mở http://localhost:3001/kenh-nguoi-ban; đăng nhập, đăng ký shop thật nếu muốn bắt đầu bán, chờ phê duyệt; không tự sửa SQL để duyệt. Lệnh root: `docker compose build backend frontend`, `docker compose up -d --no-deps --wait backend frontend`. Dừng sau P6-01; task kế tiếp P6-02 — Sản phẩm Seller, chờ người dùng yêu cầu.

# Trạng thái trước — P5-04 DONE (10/11/2026)

Đã hoàn thành một task tiếp theo: lịch sử và chi tiết đơn Buyer, không tự mở Seller/Admin. GET /api/v1/orders phân trang và GET /api/v1/orders/{id} qua ReadAccess/transaction READ ONLY; kiểm user ACTIVE/role hiện tại, SQL predicate buyer_user_id cho cả USER/ADMIN. Đơn người khác/missing cùng404, không bypass Admin, không query owner do client cung cấp. Tiền Decimal string/ID BIGINT string/UTC, no-store. List count/page/all shop summaries và detail owned order/all shops/all items, cố định3 SELECT sau principal, không N+1. Chi tiết checkout chuyển sang dùng chung OrderRepository; full checkout regression đã chạy lại.

Frontend /tai-khoan/don-hang và /tai-khoan/don-hang/{id} gọi Next same-origin proxy cố định GET, query/ID allowlist/cookie filtering/no-store, không secrets/browser JWT. History12 đơn/trang, snapshot người nhận/địa chỉ/tên-giá sản phẩm, trạng thái riêng từng shop; không tạo trạng thái đơn tổng/paid giả. Snapshot không phụ thuộc Product/Address hiện tại, shop name vẫn là tên hiện tại theo giới hạn schema. Tổng/subtotal giữ giá trị đặt hàng kể cả đơn shop CANCELLED. Có loading/empty/error/retry, login returnTo, cập nhật trạng thái bằng refetch, abort/kết quả cũ không hiển thị sau account/page change. Liên kết thật từ tài khoản và xác nhận checkout; không lưu dữ liệu lịch sử/địa chỉ vào browser storage. Hủy Buyer và hoàn tồn/state machine chưa triển khai trong task đọc này, được ghi rõ vào P6-05 theo API contract; không nút hủy giả.

- PASS221 backend full tests với PostgreSQL16 tmpfs marketplace_test riêng và audit metadata DB hiện hữu READ ONLY:16 trường hợp mới gồm guest/locked/own Admin/foreign USER+ADMIN404, snapshots khi đổi tên/giá/ẩn sản phẩm/xóa address/khóa shop, mixed status, pagination cùng timestamp/tie-break/trang quá cuối, validation/response projection/no-store/READ ONLY/constant query count. Full suite kiểm lại checkout rollback/concurrency/replay sau refactor detail. Ruff check/format PASS; dependency/lock không thay đổi.
- PASS40 frontend tests, lint/typecheck/production build: projection/money/BIGINT/enum/private extras, proxy method/path/query/cookie/no-store, client failure/invalid response không giả empty. Có lỗi lint ban đầu do dùng anchor nội bộ, đã sửa Link và chạy lại PASS.
- PASS browser thật Chrome Next production→FastAPI→PostgreSQL16 test: guest/empty, checkout2 shop→detail, refetch SHIPPING/CANCELLED, snapshots tên/giá/địa chỉ sau đổi catalog/xóa address,14 đơn/2 trang không trùng, API503/error/retry, foreign IDOR404 không lộ snapshot, expiry bỏ dữ liệu riêng. Responsive320/390/768/1440 không overflow/JS errors; đã xem ảnh desktop/mobile. Fixtures pagination/status chỉ DB test, processes/container đã dọn.
- PASS Docker build/up backend frontend --no-deps, hai app healthy. Live guest history/detail/render200/login return, API401/no-store, query không cho phép hoặc trùng400, OpenAPI hai GET mới và readiness200, responsive/no JS errors. Không tạo tài khoản/đơn hoặc mutation test trong DB thật.
- PASS PostgreSQL ID/start/mount/service config, named volume/network và root .env hash trước-sau không đổi. Không SQL/schema/data/Compose/env/secret/dependency/lock/Terraform thay đổi, không commit/push/AWS. HTTPS/gateway/load và Seller thay trạng thái qua API chưa kiểm chứng (P6-05 chưa làm).

Hướng dẫn/code/API/kiểm tra: [buyer-orders.md](buyer-orders.md). Mở http://localhost:3001/tai-khoan/don-hang sau đăng nhập; chưa có đơn sẽ rỗng thật. Từ root chạy `docker compose build backend frontend` và `docker compose up -d --no-deps --wait backend frontend`. Dừng sau P5-04. Task kế tiếp trong kế hoạch là P6-01 — Gian hàng Seller, chờ người dùng yêu cầu.

# Trạng thái trước — P5-03 DONE (10/11/2026)

Đã thay `/thanh-toan` preview bằng checkout thật: từ giỏ bấm Tiến hành thanh toán, chọn địa chỉ của tài khoản, kiểm tra dòng/tạm tính từng shop và tổng, COD mô phỏng, đặt hàng → xác nhận từ OrderDetail của backend. Guest login rồi quay lại; có loading/empty/no-address/error/retry. Nút đặt khóa khi giỏ thiếu điều kiện, không địa chỉ, >1000 dòng hoặc tổng vượt NUMERIC. Không phí/discount/voucher/payment gateway giả. Lịch sử đơn vẫn chờ P5-04; dừng sau P5-03.

- Source: `components/checkout/checkout-panel.tsx`; `lib/checkout-contract.ts`, `checkout-client.ts`; Next POST `/api/v1/orders/checkout`; private proxy giữ target cố định/cookies/CSRF/Origin/no-store/timeouts, chuyển Idempotency-Key UUID. Body limit checkout128KiB; các route auth/cart/address vẫn8KiB. Không proxy tùy ý hoặc đưa secrets vào frontend. Cart button/link thật, account/header/footer bỏ thông tin checkout chưa mở; xóa component preview không còn được import.
- Intent lưu trước POST bằng crypto.randomUUID, theo user trong sessionStorage: version/user_id/key và payload chỉ address_id tham chiếu/COD/product IDs/quantity/expected prices. Không localStorage, JWT, recipient name/phone/địa chỉ nguyên văn/tên sản phẩm/OrderDetail trong storage. Lưu/đọc lại thất bại thì không POST. Ref guard/disabled chặn gửi đôi; unique backend vẫn bảo vệ nghiệp vụ. Dữ liệu riêng chỉ tải client/no-store, không SSR cache; unmount/account change không hiển thị response riêng cho user khác.
- Reload có intent vào recovery, không tự coi browser record là thành công. Gửi lại đúng key/payload, không phụ thuộc cart/address hiện tại còn tồn tại hoặc API đọc đang hoạt động. Mạng/503/response không hợp lệ/expiry giữ recovery, không cho tạo yêu cầu mới. Business errors cho tải lại giá/giỏ/địa chỉ và xác nhận rõ ràng, giữ cùng key khi sửa request. Chỉ sau200/201 với response đúng ID/enum/Decimal/arithmetic mới hiển thị success; order dùng dữ liệu server, không ghép giá/tên/địa chỉ giả từ UI. Intent giữ qua success/reload để replay; chỉ nút Bắt đầu lượt thanh toán mới sau server confirmation mới clear intent. Mã scope theo user, login lại cùng user khôi phục; storage hỏng chặn checkout, không âm thầm rotate key.
- Xác nhận hiển thị order ID/ngày/COD/snapshots người nhận/phone/address/products, trạng thái từng đơn shop và tổng. Header giỏ refetch sau success. Tiền hiển thị VND qua BigInt, JSON không arbitrary HTML. Chọn default address trước hoặc địa chỉ đầu, có thể đổi; thiếu địa chỉ dẫn sang P4-04. Đóng tab/xóa sessionStorage có thể mất key; không hứa khôi phục intent đã bị xóa (P5-04 sẽ bổ sung lịch sử đối chiếu).
- PASS37 frontend unit/contract tests, lint/typecheck/production build. Unit kiểm payload giới hạn/duplicate/IDs/giá/COD, OrderDetail projection/totals/enum/unsafe extras, persistence/account isolation/storage failure, proxy method/key/Origin/cookie/body limit và client uncertainty/repairability/no auto retry. Source cuối chỉ sửa copy hỗ trợ và xóa preview dead code, lint/typecheck/Docker production build sau đó cũng PASS.
- PASS Chrome E2E Next production→proxy→FastAPI→PostgreSQL16 tmpfs riêng: guest/login/no-address/empty, chọn địa chỉ khác default, hai shop/tiền đúng/COD, submit hai lần chỉ một POST/order, success/reload/replay200/order không trùng, explicit new purchase mới key. Đã cho real backend commit rồi cố tình drop response: recovery/reload gửi lại cùng key/payload, đúng order cũ dù địa chỉ bị xóa và GET cart/addresses503. Có price409→review mới→resubmit cùng key đúng giá mới, stock409→blocked review, precommit503→JWT expiry→login lại→same-key201, storage write failure không POST, fetch lỗi không giả empty/reload phục hồi. Responsive320/390/768/1440 không overflow/JS errors; đã xem screenshots desktop/mobile. Các lỗi mạng giả lập chỉ trong harness test, không app/production fallback.
- Test fixtures/accounts/cart/address/order chỉ DB test marketplace_test, processes/container riêng đã dọn; không đặt đơn thử/seed hoặc ghi DB hiện hữu. Backend không đổi nên không lặp lại full205 tests của P5-02; browser test dùng backend thật để kiểm transaction/replay end-to-end. HTTPS/gateway/load chưa kiểm chứng.
- PASS Docker build/up riêng frontend --no-deps, healthy. Live guest checkout200/login link, thiếu key400/hostile Origin403 bị chặn trước backend, csrf/readiness200; không valid checkout mutation trên DB thật. PostgreSQL ID/start/mount/config, root .env hash, named volume/network trước-sau giữ nguyên. Không backend/SQL/schema/Compose/env/secret/dependency/lock/Terraform changes, không commit/push/AWS. Git diff --check PASS, cảnh báo line ending .env.example có sẵn.

Code/chạy/manual QA: [checkout-ui.md](checkout-ui.md). Root `docker compose build frontend`, `docker compose up -d --no-deps --wait frontend`. Mở http://localhost:3001/gio-hang → thanh toán hoặc http://localhost:3001/thanh-toan, Ctrl+F5. Frontend → Next same-origin → FastAPI → PostgreSQL, chỉ COD mô phỏng. Chờ yêu cầu P5-04 — Theo dõi đơn Buyer.

# Trạng thái trước — P5-02 và AUTH-POLICY-01 DONE (10/11/2026)

Theo yêu cầu “làm tiếp và mật khẩu trên8 ký tự có chữ hoa/số/ký tự đặc biệt”, đã hoàn thành backend checkout COD transaction P5-02 và cập nhật policy đăng ký. Dừng sau hai phần được yêu cầu; chưa làm UI checkout P5-03.

## Quy tắc mật khẩu mới

- `backend/app/schemas/auth.py`: RegisterRequest9–128 ký tự, có A–Z/0–9/punctuation-symbol Unicode, whitespace không được tính là ký tự đặc biệt, không trim/normalize, không buộc chữ thường. LoginRequest1–128 ký tự để kiểm hash cũ và mật khẩu9 mới, không áp lại complexity đăng ký lên tài khoản có sẵn. Không sửa password/hash dữ liệu hiện hữu, không schema changes. Quyết định trực tiếp mới được ghi business-rules/architecture/API/auth docs, thay min12 kỹ thuật trước đây.
- Frontend `auth-contract.ts` có helper đồng bộ policy (đếm code points, regex uppercase/digit/P+S); AuthForm chặn submit yếu/focus error, gợi ý9–128 hiện rõ dưới password. Login không dùng min12 gây chặn mật khẩu9. Giữ confirm/show-hide/password whitespace/CSRF/session/return URL flow; không OTP/OAuth giả. Native minLength kết hợp helper; không dùng maxLength UTF16 để cắt sai mật khẩu Unicode, backend giới hạn128 code points.

## Checkout backend

- Thêm schemas/repositories/services/routers checkout, `db/locks.py`; POST `/api/v1/orders/checkout` nhận UUID Idempotency-Key/address_id/COD/items product+strict quantity+decimal expected price. Items1..1000, unique products, forbid extra, không nhận buyer/shop/tổng tiền giả. Response201 lần đầu/200 replay, OrderDetail BIGINT strings/Decimal/UTC/no-store, snapshot recipient/phone/shipping/product name/unit price/quantity.
- Router tái dùng current_subject/csrf_guard/session; CheckoutService sở hữu transaction qua COMMIT, tạo AccessPolicy với repository write mỗi attempt để khóa user/kiểm trạng thái DB, không begin/commit lồng WriteAccess. Order theo buyer/key được tìm trước cart/address/catalog; replay không áp payload mới/giảm tồn/xóa giỏ mới. Missing/foreign address404, self-purchase403, price409 PRICE_CHANGED, stock409 OUT_OF_STOCK, cart/visibility/overflow409 CART_CHANGED. Lỗi validate422, không leak payload/DB exception.
- Lock order: user→cart→shared PostgreSQL advisory category `(731921,1)`→shop ID tăng→product ID tăng→inventory ID tăng. Sau khóa đọc lại dữ liệu/visibility; category mutations phase7 phải dùng exclusive cùng key, shop/product/inventory mutations tương lai phải phối hợp thứ tự. Shared tree lock không serialize checkout toàn cục. Không mutex/idempotency trong memory; unique buyer/key schema có sẵn là hàng rào cuối. Tối đa3 attempts cùng key cho40001/40P01 hoặc đúng unique constraint idempotency; lỗi DB khác trả503 đã làm sạch, caller retry cùng key để xử lý kết quả commit chưa rõ.
- Validate toàn bộ giỏ/giá/tồn/active product/category+ancestors/shop APPROVED/address ownership trước ghi. Tính Decimal, guard tổng<=999999999999.99; tạo orders/mỗi shop một shop_orders/order_items đúng composite FK; giảm inventory có điều kiện quantity>=requested dưới row lock, clear cart cùng transaction. Bất kỳ lỗi giữa chừng/commit rollback tất cả. Shop name trong response hiện tại lấy bảng shops vì schema không có snapshot shop name; snapshots product/address vẫn lấy order tables. Không sửa SQL/schema hoặc giả thêm cột.

## Kiểm chứng và local

- PASS205 backend full không skip: PostgreSQL16 tmpfs riêng + metadata audit DB thật READ ONLY. Tranh tồn cuối hai buyer chỉ một201; cùng buyer/key4 app instances tạo1 order (201/200), không trừ kho lại; key scope theo buyer, replay sau xóa address/đổi price/name/ẩn product, cart rỗng, totals/numeric overflow, quantity/schema/auth/CSRF/foreign address/self-purchase/hidden/category/locked shop, stock missing/zero. Có rollback sau giảm tồn và khi COMMIT lỗi, serialization retry; concurrent user/cart/category/shop/price/inventory changes đang giữ khóa được kiểm lại đúng sau release. Test legacy login và đăng ký/login đúng9 ký tự PASS. Lần đầu suite có1 test auth cũ dùng fixture không chữ hoa nên422 đúng policy; cập nhật fixture hợp lệ, chạy lại full205 PASS, không nới validator để vượt test.
- PASS31 frontend tests + lint/typecheck/build; Ruff check/format + uv lock --check PASS. Browser E2E Next production/proxy/FastAPI/PostgreSQL16 test: weak password thiếu từng điều kiện bị chặn không POST, direct bypass422, đúng9 đăng ký/login; cart hai shop + địa chỉ thật qua API test → backend HTTP checkout201/replay200 cùng order, stock mỗi sản phẩm giảm một lần, cart rỗng sau reload. Không có UI submit checkout/proxy mới; test dùng HTTP client giữ auth cookies để gọi backend theo scope P5-02. Responsive390/768/1672 gợi ý hiện/no overflow/no JS errors; screenshot desktop đã xem. Test fixtures/process/container riêng đã dọn, không tạo account/order/seed trên DB hiện hữu.
- PASS Docker build/up --no-deps backend/frontend, healthy. Live policy hint/weak client error/server422 không tạo user, OpenAPI checkout/register min9/login min1, readiness200/no JS errors. PostgreSQL ID/start/mount/config, root .env hash, named volume/network trước-sau không đổi; backend auth key riêng giữ nguyên. Không Compose/env/secret/dependency/lock/Terraform/SQL/data changes, không commit/push/AWS. Git diff --check PASS (cảnh báo LF/CRLF env mẫu có sẵn).

Hướng dẫn code/API/transaction/checks: [checkout-api.md](checkout-api.md), [auth-development.md](auth-development.md). Root: `docker compose build backend frontend`, `docker compose up -d --no-deps --wait backend frontend`. Kiểm tra http://localhost:3001/dang-ky Ctrl+F5; Swagger http://localhost:8000/docs Buyer checkout. Frontend→Next proxy→FastAPI→PostgreSQL cho auth/cart/address; checkout API hiện chỉ backend, UI/proxy là P5-03. HTTPS/public gateway/load/performance chưa kiểm chứng; chưa tuyên bố website đặt hàng UI hoàn chỉnh. Chờ yêu cầu P5-03.

# Trạng thái trước — P5-01 DONE (10/11/2026)

Giỏ hàng nhiều shop đã dùng API thật: `/gio-hang` thay preview bằng danh sách riêng tư, nhóm shop, đơn giá/tồn hiện tại, sửa lượng, xóa có xác nhận, subtotal/tạm tính. Chi tiết có AddToCart, guest login rồi quay lại, UI chặn own-shop; backend vẫn kiểm tra thật. Header chuyển thành link giỏ và đọc số dòng sản phẩm từ API, cập nhật sau mutation cùng tab. Account có link giỏ/địa chỉ. Checkout còn disabled; không làm task tiếp theo.

- Backend: `schemas/cart.py`, `repositories/cart.py`, `services/cart.py`, `api/v1/routers/cart.py`, đăng ký v1 router. GET cart chỉ đọc, không tạo cart khi rỗng. POST cộng thêm, PATCH đặt lượng mục tiêu, DELETE204. Owner lấy từ JWT/current DB principal; USER/ADMIN đều chỉ giỏ mình, resource foreign/missing404; user LOCKED403, guest401. Mutations có CSRF/Origin, extra forbid, quantity strict int1..2147483647, ID không float/bool. Body giá/user/cart/shop không được nhận.
- Tính duy nhất/nguyên tử: WriteAccess khóa user rồi cart/dòng giỏ trong một transaction; same buyer ở nhiều app instance serialize trên PostgreSQL, không lost increment hoặc cart/item trùng. Giữ unique cart/user và item/cart/product có sẵn, không thêm schema/index. Lượng cộng thêm kiểm cả lượng cũ + mới, chặn integer overflow. Cart không giảm inventory/giữ giá, không thay cơ chế checkout chống overselling của P5-02. Product/catalog có thể đổi sau thời điểm kiểm tra giỏ, GET sau đó đánh dấu unavailable đúng trạng thái mới.
- GET join một query, tái dùng public category CTE để ẩn cả ancestor inactive; vẫn giữ dòng giỏ unavailable cho buyer xóa. Kiểm shop APPROVED/product active/category visible/inventory/stock/self-purchase khi thêm/sửa. Reasons rõ HIDDEN_PRODUCT/SHOP_UNAVAILABLE/CATEGORY_UNAVAILABLE/SELF_PURCHASE/MISSING_INVENTORY/OUT_OF_STOCK/INSUFFICIENT_STOCK. Không storage keys/password/owner email trong response, ảnh null theo delivery chưa cấu hình; UI dùng placeholder trung thực.
- Decimal/BigInt: unit_price từ NUMERIC14,2; line/subtotal/total giỏ tính chính xác và không lưu DB. Làm rõ docs/api-contract.md: tạm tính dẫn xuất có thể vượt giới hạn NUMERIC với lượng rất lớn; không cắt/giả giá, frontend kiểm arithmetic bằng BigInt cents. Tổng đơn lưu DB phải được guard tại P5-02. Tạm tính bao gồm mọi dòng, kể cả unavailable, đã ghi rõ ở UI/docs; không thu phí/voucher/shipping hoặc tạo order giả.
- Frontend: `components/cart` add/cart/header/use-cart; `lib/cart-{contract,client}`; private proxy allowlist đúng4 method/route, giữ cookie filter/CSRF/Origin/body8KiB/no-store/timeout/redirect:error. Client không token/cart browser storage; event chỉ yêu cầu refetch, DB là nguồn dữ liệu. Parse response projection/ID/money/totals/unique rows/stock/image schemes; error không giả empty. Duplicate submit guard, loading/disabled, error focus, login returnTo, delete confirm/cancel, GET retry; POST không idempotency nên timeout chưa rõ phải xem giỏ trước khi thêm lại, không auto retry mutation.
- PASS158 backend tests đầy đủ, không skip, PostgreSQL16 tmpfs riêng; audit DB hiện hữu READ ONLY. Bao gồm concurrent create/upsert nhiều app instances, accumulated quantity/stock rejection, inventory không đổi, role/ownership/Admin không bypass, CSRF, parent inactive/hidden/locked/zero/missing stock, cập nhật giá/tồn, quantity overflow/validation, rollback cart+item khi commit lỗi. Ruff check/format và uv lock --check PASS.
- PASS30 frontend tests, lint/typecheck/build. Browser E2E Next production→proxy→FastAPI→PostgreSQL16 riêng: guest/login returnTo, double-submit chỉ một POST, thêm2 shops/gom dòng/tổng, update/stock409, refresh giá/tồn, hidden/locked retained/removable, xác nhận/giữ lại/xóa, header count/reload, CSRF403/error retry/expiry, no browser cart/JWT storage. Responsive320/390/768/1440 không overflow/JS errors, screenshot desktop/mobile đã xem. Fixtures chỉ DB test riêng; test processes/container dọn đúng tài nguyên sở hữu.
- PASS Docker build/up --no-deps backend/frontend, cả hai healthy. Live guest cart200/headerlink/401 private API, csrf200 (khóa local vẫn hoạt động), readiness200, đủ4 methods trong OpenAPI, mobile không tràn/JS errors; không gửi cart mutation lên DB thật. PostgreSQL ID/start/mount/service config, root .env hash, volume/network trước-sau không đổi. Không SQL/schema/data/Compose/env/secret/dependency/lock/Terraform changes trong task; không commit/push/AWS. Git diff --check PASS, cảnh báo line ending .env.example có sẵn.

Hướng dẫn code/chạy/test: [cart.md](cart.md). Root: `docker compose build backend frontend`, `docker compose up -d --no-deps --wait backend frontend`; mở http://localhost:3001/gio-hang. Nếu chưa có catalog thật thì chưa có hàng để thêm trên DB hiện hữu; không tự seed. Giỏ thật đã kiểm chứng bằng fixture ở DB test riêng. HTTPS/gateway production, checkout chống overselling/idempotency/order vẫn chưa triển khai/kiểm chứng. Dừng sau P5-01; chờ yêu cầu P5-02.

# Trạng thái trước — FIX-AUTH-01 DONE (10/11/2026)

Người dùng báo không đăng ký/đăng nhập được. Xác minh live Next `/api/v1/auth/csrf` trả503 AUTH_NOT_CONFIGURED trong khi readiness200: thiếu MARKETPLACE_JWT_SECRET, không phải lỗi database hoặc form. Đã tạo khóa random64 ký tự bằng secrets.token_urlsafe(48), lưu riêng `backend/.env.auth`; Compose chỉ backend nạp file này, required:false để môi trường thiếu khóa vẫn fail closed. Không in khóa vào log/chat, không JWT trong frontend.

Root `.env` cũng được service PostgreSQL nạp qua env_file. Thử bổ sung khóa vào root khiến kiểm tra cấu hình PostgreSQL phát hiện biến môi trường thừa, nên dừng trước recreate ứng dụng; đã chuyển khóa sang file backend riêng và khôi phục root .env khớp hash byte-for-byte ban đầu. Không restart/recreate postgres trong quá trình này. Chỉ thay Compose backend env_file và bỏ JWT interpolation từ root; cập nhật .env.example bỏ dòng secret root, hướng dẫn auth-development/auth-ui dùng backend file. Git ignore và backend Docker ignore đã có `.env.*`, không cần sửa để bảo vệ file mới. Mọi replica ngoài local vẫn nhận JWT qua environment theo deployment; không đổi Python settings/auth logic.

PASS: Compose config --quiet; backend up --no-deps healthy; khóa có trên backend nhưng không có trong environment frontend/PostgreSQL; PostgreSQL container ID/start/mount/service config, volume/network và root .env hash giữ nguyên. Live browser csrf200, guest me401, register body rỗng422, login form email không tồn tại401 với thông báo tiếng Việt đúng; trang đăng ký sẵn sàng, không JS errors. Không tạo tài khoản test trong DB thật.

PASS browser E2E Next production→proxy→FastAPI→PostgreSQL16 tmpfs riêng: đăng ký thật, login/logout/me/reload, trùng email/sai mật khẩu/confirm, HttpOnly cookie/no browser token storage, hostile CSRF403, expired session, safe returnTo, responsive320/390/768/1440. Test container/process riêng đã dọn. Không đổi code ứng dụng/dependencies nên không chạy lại full131 backend hoặc26 frontend tests; kiểm chứng lại full auth flow và cấu hình thực tế phù hợp thay đổi. Git diff --check PASS, chỉ cảnh báo line ending .env.example có sẵn.

Đăng ký http://localhost:3001/dang-ky, đăng nhập http://localhost:3001/dang-nhap; dùng email/password12–128 ký tự. Chưa có OTP/social login. Khóa local đã có, không cần tạo lại; tái áp dụng bằng `docker compose up -d --no-deps --wait backend`. HTTPS/gateway production chưa kiểm chứng. Không schema/data/SQL/Terraform changes, không commit/push; dừng sau sửa lỗi xác thực.

# Trạng thái trước — P4-04 DONE (10/11/2026)

Đã hoàn thành quản lý địa chỉ giao hàng: `/tai-khoan` có liên kết `/tai-khoan/dia-chi`; danh sách, thêm/sửa/xóa có xác nhận, đặt mặc định, loading/empty/error/retry, guest đăng nhập rồi quay lại. Browser gọi Next private proxy → FastAPI → SQLAlchemy → PostgreSQL marketplace.addresses thật. Không localStorage/sessionStorage PII, không SSR cache địa chỉ, không mock dữ liệu production. Giỏ/checkout/dashboard chưa mở rộng; dừng sau một TASK.

- Backend: schemas/repositories/services/routers `addresses.py`, đăng ký v1 router. Input trim/length/phone/strict boolean, extra forbid; PATCH không rỗng, required fields không null, ward/district có thể null. ID BIGINT trả chuỗi, created_at UTC theo mapping. Mọi query theo principal.user_id; Admin không bypass; missing/foreign cùng404; tài khoản LOCKED403, guest401 khi auth có cấu hình. Response chỉ fields contract, không owner ID.
- Ghi dùng WriteAccess hiện hữu: JWT/CSRF/Origin, khóa user trước địa chỉ, một transaction qua commit trước response. Clear default cũ bằng UPDATE trước flush mới để giữ partial unique index; không mutex trong process/schema mới. Cùng user được serialize giữa replica. Không tự chọn mặc định đầu tiên/thay thế sau xóa; cho phép zero default. Không cập nhật order snapshots.
- Frontend: `address-panel.tsx`, `address-client.ts`, `address-contract.ts`, route `tai-khoan/dia-chi`, Next address routes, account link. Proxy private dùng chung auth transport nhưng allowlist từng nhóm riêng; thêm kiểm tra PATCH/DELETE, không mở generic proxy. Cookie allowlist/CSRF/source checks/body8KiB/no-store/redirect:error/timeout giữ nguyên. Không retry mutation mù; khi kết quả chưa rõ hướng dẫn reload. Form focus/labels/native validation, duplicate-submit ref guard; response projection bỏ owner/extras.
- PASS131 backend tests đầy đủ, không skip: PostgreSQL16 tmpfs riêng, audit metadata DB hiện hữu READ ONLY. Có validation, ownership USER/ADMIN, guest/LOCKED/CSRF, concurrent create/default switch qua app instances, rollback khi before_commit lỗi, xóa/sửa không đổi order snapshots. Ruff check/format, uv lock --check PASS. Không DDL/fixture/sequence writes trong DB thật.
- PASS26 frontend tests, lint/typecheck/build. Browser E2E Next production → proxy → FastAPI thật → PostgreSQL16 test: guest→register/login→địa chỉ, thêm2/sửa/chuyển mặc định/reload/xóa-cancel/xóa thật, CSRF hostile403, expired session, lỗi fetch không giả empty và retry; không PII browser storage. Responsive320/390/768/1440 không overflow/JS errors; screenshot desktop đã xem. Lần đầu lint effect bị lỗi setState đồng bộ, đã tách tải ban đầu async; lần đầu E2E phát hiện tên user dài gây tràn header320px, đã thêm min-width:0 cho auth links và chạy lại PASS, không tắt rule/che overflow.
- PASS Docker build/up riêng backend/frontend --no-deps, cả hai healthy. Live trang địa chỉ200, OpenAPI đủ4 methods, readiness200, guest/private API bị từ chối; không gửi mutation lên DB thật. PostgreSQL ID/start/mount/service config, root .env hash, named volume/network trước-sau không đổi. Test container/process đã dọn đúng tài nguyên sở hữu. Git diff --check PASS (cảnh báo LF/CRLF .env.example có sẵn).
- Giới hạn: auth trên Docker local vẫn thiếu JWT secret nên có thể503 AUTH_NOT_CONFIGURED; không tự tạo/ghi secret. Luồng thành công đã test bằng secret tạm trên DB test riêng, không báo đăng nhập DB thật PASS. HTTPS/gateway production chưa kiểm chứng. Không SQL/schema/Compose/env/dependencies/lock/Terraform changes trong task, không commit/push/AWS.

Hướng dẫn code/chạy/manual QA: [addresses.md](addresses.md). Root: `docker compose build backend frontend`, `docker compose up -d --no-deps --wait backend frontend`; mở http://localhost:3001/tai-khoan/dia-chi và http://localhost:8000/docs. Task kế tiếp P5-01 — Giỏ nhiều shop, chờ người dùng yêu cầu.

# Trạng thái trước — UI-14 DONE

Thiết kế lại /dang-ky theo ảnh mới: header có search thật, minh họa/túi/quà bên trái dùng ảnh người dùng, form HTML bên phải, service strip và footer gọn. Nền ảnh dùng SVG mask bỏ form raster; card thật nền opaque để không lộ chữ/nút ảnh phía dưới. Email trước họ tên, password/confirm; phone optional trong details. Họ tên vẫn bắt buộc theo API, không thay bằng OTP giả. Social disabled và ghi rõ chưa hỗ trợ. API/auth logic không đổi, login không đổi bố cục.

Files: auth-form, register-reference-art, register-footer, site-frame, globals.css, public/images/coco-register-reference.png và docs. PASS24 unit tests/lint/typecheck/build; E2E Next→FastAPI→PostgreSQL16 riêng đăng ký/login/logout/cookie/CSRF/expiry/return URL; browser390/768/1672 search→catalog/footer/social/no overflow/JS errors, screenshot desktop đã xem. Test process/container dọn xong; Docker frontend healthy; PostgreSQL/env/config/volume/network không đổi. Không schema/backend/dependency/Compose/secret/real-data changes, không commit/push. Dừng sau UI-14.

# Trạng thái trước — UI-13 DONE

Thiết kế trang login sát ảnh mới: copy nguyên ảnh người dùng vào public/images/coco-login-reference.png, chỉ hiển thị hai vùng minh họa và đáy bằng SVG clip, không hiển thị form raster của ảnh. Form live ở giữa, header trắng/logo/help/account, title/offset/input/eye icon/submit/social row/switch theo mẫu. Form vẫn email/password với API/CSRF/JWT cũ. Social buttons disabled và ghi chưa hỗ trợ; Quên mật khẩu mở disclosure giải thích chưa có reset backend, không fake gửi email. Registration không đổi.

Files: login-reference-art.tsx, auth-form.tsx, globals.css, ảnh reference, docs. PASS lint/typecheck/production build và24 tests; Chrome390/768/1672 không overflow/JS errors, social disabled/help disclosure, screenshot desktop đã xem và căn lại card. Docker frontend healthy; PostgreSQL/env/config/volume/network giữ nguyên. Không backend/schema/dependency/Compose change, không commit/push. Dừng sau UI-13.

# Trạng thái trước — UI-12 DONE

Chỉnh riêng trang đăng nhập theo phản hồi: header60px (mobile55px), bỏ password hint và aria-describedby tương ứng; túi SVG lớn/nghiêng12 độ, gradient và đổ bóng tạo chiều sâu; slogan “Siêu nhanh – Siêu rẻ” trên túi, voucher bên phải lớn hơn. Giữ đăng ký và logic auth/backend nguyên trạng. Files: auth-form.tsx, auth-decoration.tsx, site-frame.tsx, globals.css. PASS lint/typecheck/production Docker build và browser390/768/1440 header/hint/responsive; đã xem screenshot. Frontend healthy; PostgreSQL/config/env/volume/network giữ nguyên. Dừng sau UI-12.

# Trạng thái trước — UI-11 DONE

Theo phản hồi người dùng: bỏ slogan hai bên, tiêu đề chỉ “Đăng nhập” / “Đăng ký”; thu khung desktop từ600 xuống470px, giảm padding/input/button/khoảng cách; mobile vẫn responsive. Sửa auth-form/auth-decoration/globals.css, không đổi logic API/xác thực. PASS lint/typecheck/Docker production build; browser title chính xác, không slogan, card≤470px desktop/mobile không overflow. Frontend healthy; PostgreSQL/config/env/volume/network giữ nguyên. Dừng sau UI-11.

# Trạng thái trước — UI-10 DONE

Docker build/up riêng frontend healthy PASS; PostgreSQL ID/start/mount/config, .env hash, volume/network trước-sau không đổi. Giao diện mới đã chạy trên :3001.

Đã thiết kế lại /dang-nhap và /dang-ky theo ảnh mới: header COCO tối giản, nền xanh có mảng cong, form trắng giữa bo tròn lớn, minh họa túi mua sắm/quà/coupon SVG riêng ở hai bên. Mobile chỉ hiện form/header để tránh chật. API và luồng xác thực P4-03 giữ nguyên; không thêm OTP/OAuth/reset password chưa có backend. Dừng sau UI-10.

## UI-10 — Thay đổi và kiểm thử

- components/layout/site-frame.tsx chọn chrome theo đúng pathname auth: header riêng/trợ giúp/tài khoản/login/register; các trang còn lại giữ SiteHeader/SiteFooter chung. SessionProvider không đổi. Không di chuyển route hoặc đổi URL. Auth pages không còn storefront search/header/footer dài.
- components/auth/auth-decoration.tsx SVG code-native trang trí (gradient bag/gift/ticket/stars), không ảnh sản phẩm hay ưu đãi thật. AuthForm giữ submit/validation/loading/error/ref-guard/password-preservation/show-hide/returnTo logic; chỉ đổi JSX hiển thị, title, placeholders và vị trí. Label visually-hidden vẫn gắn htmlFor cho screen reader. CSS auth-scene scoped, không áp theme này lên account/catalog.
- Giữ email login và full_name/phone/password/confirm đăng ký theo contract. Mẫu ảnh có phone-or-email/OTP/forgot password/social sign-in, nhưng các chức năng đó chưa có backend hoặc chưa được yêu cầu trong auth task, nên không tạo nút giả/gửi mã giả. Không hứa ưu đãi live; dùng slogan chăm sóc/làm đẹp.
- PASS24 tests, lint/typecheck/build. Chrome E2E Next production→FastAPI thật→PostgreSQL16 tmpfs riêng: register→login→me/reload→logout, mismatch/duplicate/wrong password, HttpOnly/no browser token storage, CSRF403, expired session và safe return URL. Responsive320/390/768/1440 không overflow/JS errors. Đã xem screenshot desktop login/mobile register. Harness chỉ cập nhật heading theo title mới; không sửa app logic để vượt test.
- Không chạy lại backend suite vì backend không đổi; positive-flow dùng backend thật với DB test riêng, dọn container/process xong, không ghi DB hiện hữu. Root .env/JWT config không đổi; local vẫn có thể báo auth chưa sẵn sàng nếu chưa đặt JWT secret theo P4-01. Không sửa SQL/schema/Compose/dependency/lock/Terraform, không commit/push/AWS.

Chạy root: docker compose build frontend; docker compose up -d --no-deps --wait frontend. Xem http://localhost:3001/dang-nhap và http://localhost:3001/dang-ky, Ctrl+F5. Hướng dẫn xác thực vẫn docs/auth-ui.md. Chờ yêu cầu tiếp theo.

# Trạng thái trước — P4-03 DONE

Đã có giao diện /dang-ky, /dang-nhap, /tai-khoan và header guest/authenticated/logout. Next same-origin proxy nối API thật, JWT giữ HttpOnly cookie, CSRF mới trước POST, không localStorage/sessionStorage token. Frontend http://localhost:3001 healthy. Local backend hiện thiếu khóa nên UI báo đăng nhập chưa sẵn sàng; full success flow đã kiểm bằng khóa tạm + PostgreSQL16 test riêng, không account/dữ liệu giả trong DB thật. Dừng sau P4-03.

## P4-03 — Thay đổi và kiểm chứng

- Source frontend: lib/auth-contract/auth-client/auth-proxy; components/auth (form,session-provider,header-auth,account-panel); app/api/v1/auth/[endpoint], dang-ky/dang-nhap/tai-khoan; root layout/HeaderAuth và CSS đồng bộ coco xanh. Footer cập nhật trạng thái auth. Chỉ thêm public-origin env frontend trong Compose và frontend/.env.example, không đổi backend/SQL/deps/lock/Terraform/root .env.
- Proxy fixed INTERNAL_API_URL, allowlist5 endpoints/method, chỉ auth cookies/CSRF/Origin/Referer/requestID, no-store/redirect:error/timeout15s/body8KiB; client same-origin credentials, request csrf mới rồi mutation, không retry mù. Mọi backend guards vẫn ở FastAPI. Safe return path allowlist chống external redirects/auth loops; Account projection loại extra private fields và giữ BIGINT string.
- Form validation native/backend, confirm password, loading/disable/ref guard duplicate submit, show/hide password, focus error. Registration không auto-login; login kiểm me rồi redirect; logout clear backend cookie rồi session state. Session refresh khi visible/mỗi60s; UI state không cấp quyền, backend source role/status. /tai-khoan không SSR PII/static private cache, guest/error/retry rõ.
- PASS24 frontend unit/contract tests (21 cũ+3 auth), npm lint/typecheck/build. Lỗi đầu lint synchronous state trong effect và TS target BigInt literal đã sửa trước final check, không tắt rule/đổi tsconfig. Formatter chạy qua npm exec tạm, không thêm dependency/lock.
- PASS browser E2E real Next production→proxy→FastAPI→PostgreSQL16 tmpfs riêng: register/login/logout/me; mismatch/duplicate email/wrong password; reload cookie; HttpOnly không đọc bằng JS; no JWT localStorage/sessionStorage; hostile CSRF403; expired cookie quay về guest; returnTo ngoài bị chặn; responsive320/390/768/1440 no overflow/JS errors. Đã xem screenshot desktop login/mobile register. Harness ngoài repo từng gặp pg_isready trước TCP server ready; thêm retry SELECT kiểm readiness DB test, chạy lại full browser PASS. Không đổi logic DB/app vì lỗi harness.
- PASS Docker build/up frontend --no-deps healthy; live3 pages200, missing-secret error hiển thị đúng, không mutation tới backend do CSRF endpoint503, proxy chặn origin giả403. PostgreSQL ID/start/mount/config/root env hash/named volume/network trước-sau giữ nguyên. Không tự tạo khóa/account hoặc dữ liệu thật. Test processes và container riêng có nhãn đã được dọn, không dùng production volume.
- NOT VERIFIED: HTTPS production cookie flow/public gateway/rate limiter; backend không đổi nên không lặp full backend111 tests đã PASS P4-02, nhưng E2E thực dùng backend cùng PostgreSQL riêng. Auth thật trên DB hiện hữu chưa activate do MARKETPLACE_JWT_SECRET thiếu, không báo login production PASS.

Hướng dẫn chạy/code/manual test: docs/auth-ui.md. Root: docker compose build frontend; docker compose up -d --no-deps --wait frontend. Người dùng tự đặt JWT secret theo docs/auth-development.md và recreate riêng backend để bật auth. Giao diện giỏ/checkout và dashboard không được mở rộng. Chờ yêu cầu P4-04.

# Trạng thái trước — P4-02 DONE

Docker backend build/up --no-deps và healthy PASS. Smoke live: readiness/catalog/frontend200, các probe test không có trong production OpenAPI; auth vẫn503 AUTH_NOT_CONFIGURED do chưa có khóa. PostgreSQL ID/start/mount/config, volume/network và root .env hash trước-sau giống nhau. ReadAccess đã bật PostgreSQL READ ONLY; full111 tests chạy lại sau thay đổi PASS.

Đã tạo policy/dependencies quyền và ownership dùng chung; /auth/me dùng policy này. USER/ADMIN ACTIVE có quyền Buyer cho dữ liệu mình, Admin không bypass, Seller là owner shop. Bán/sửa catalog/tồn cần APPROVED; shop LOCKED chỉ xử lý đơn cũ khi user ACTIVE. Chưa xây dashboard hoặc API CRUD của các phase sau. Frontend giữ nguyên, task tiếp theo P4-03 chờ yêu cầu.

## P4-02 — Phạm vi và quyết định

- Code: api/dependencies.py, repositories/access.py, services/access.py; auth service/me và router tái sử dụng current_subject/csrf_guard chung. Repositories project principal không hash, owner predicates trong SQL, shop ID từ DB user hiện tại. Principal frozen/request-scoped, không role cache/JWT role.
- Policy admin/buyer/shop/selling_shop/seller_product/address/cart/order/buyer_shop_order/seller_shop_order; thiếu user401, user LOCKED403, role sai403, resource sai owner/missing404. Admin chỉ quản trị qua API riêng trong phase7, không impersonate Buyer/Seller. APPROVED/LOCKED xử lý đơn cũ; PENDING/REJECTED không có quyền xử lý đơn. Policy không thay state machine/inventory/checkout guards của task sau.
- WriteAccess dùng JWT và CSRF, explicit transaction, row lock user→shop, function scope để commit/rollback trước response; ReadAccess phục vụ read policies. Dịch vụ tương lai phải cùng session, không begin/commit lồng và giữ thứ tự user→category→shop→product→inventory. Child resources phải query theo parent đã được kiểm quyền. Không tuyên bố đã có transaction checkout hoặc CRUD dashboard.
- PASS111 tests full không skip: PostgreSQL16 tmpfs riêng, SQL schema audit hiện hữu READ ONLY; role401/403, ownership crossuser/shop404, multi-shop chung order, ADMIN không bypass, owner ACTIVE/LOCKED, shop mọi trạng thái, role/status đổi không cấp JWT lại, missing user401, write CSRF và rollback/error commit503 trước response. Fixture đầu dùng dict cho shipping_address TEXT và thiếu recipient/phone; đã sửa fixture theo mapping hiện hữu, giữ schema và chạy lại full PASS. Ruff check/format và uv lock --check PASS; git diff --check PASS (chỉ cảnh báo line ending env mẫu có sẵn).
- Không sửa schema/data/SQL/Compose/.env/dependency/Frontend/Terraform; không commit/push/AWS. Container test riêng có nhãn/tmpfs/random port, dọn đúng container sau test, không mount volume production. Policy probe routes chỉ có trong test, không xuất hiện OpenAPI production. Đăng nhập thật vẫn phụ thuộc cấu hình khóa JWT của P4-01, không tự tạo secrets/account/role trên DB thật.

Hướng dẫn code, chạy và kiểm tra: docs/authorization.md. Chạy root `docker compose build backend` rồi `docker compose up -d --no-deps --wait backend`; xem http://localhost:8000/docs và http://localhost:3001. Dừng sau P4-02.

# Trạng thái trước — P4-01 DONE

Docker backend build/up --no-deps PASS, healthy; PostgreSQL ID/start/mount/config/env/volume/network trước-sau không đổi. Smoke live: OpenAPI đủ5 endpoint auth, readiness/catalog/frontend200; auth/csrf503 AUTH_NOT_CONFIGURED đúng do chưa có khóa; chỉ gửi GET, không ghi dữ liệu thật. Ruff check/format và uv lock --check cuối PASS.

Backend có GET `/api/v1/auth/csrf`, POST register/login/logout và GET me. Schema/data PostgreSQL giữ nguyên; không tạo account hoặc test fixtures trong DB thật. Thiếu MARKETPLACE_JWT_SECRET thì auth503 AUTH_NOT_CONFIGURED; người dùng tự tạo khóa local, không có default secret và không sửa root .env. Giao diện auth và phân quyền nghiệp vụ là P4-02/03, chưa tự triển khai.

## P4-01 — Thiết kế và kiểm thử

- Password Argon2id qua argon2-cffi; email trim/lower/validation, password12–128 Unicode không trim; full_name/phone validate/trim, extra fields role/status/owner bị cấm. Registration USER/ACTIVE, không tự login. Unique index uq_users_email_lower xử lý đăng ký đồng thời. Không DDL/migration trong app.
- JWT HS256 allowlist, exp/iat/sub/iss/aud bắt buộc, exact positive BIGINT subject, max TTL900s; secret từ env. Cookie HttpOnly/SameSite=Lax/Path=/; production Secure/__Host prefix/no Domain. Role/status/shop đọc DB từ /me, không lấy role từ JWT; password sai/missing cùng401. Login dùng row lock và rehash nếu cần. Repository không commit, service explicit transaction/rollback, DB error sanitized503.
- CSRF HMAC double submit ràng buộc access-cookie hash + random nonce + timestamp, TTL1h; cookie readable và X-CSRF-Token, Origin exact hoặc Referer origin, không tin forwarded headers. Login rotate access+CSRF; logout clear hai cookies, không đòi access JWT còn hạn. Logout không revoke JWT đã bị sao chép. Không session store trong process; hai app instances kiểm chứng cùng JWT. Rate limit cần shared gateway/store khi triển khai public, chưa có limiter trong task này.
- Config/env mẫu/Compose chỉ bổ sung env backend, không sửa postgres/network/volume hoặc root .env. Empty secret vô hiệu auth503; catalog/liveness giữ hoạt động. Không tạo proxy frontend trước P4-03; Swagger khác origin cần gửi Origin/CSRF đúng bằng client có cookie, không bỏ guard để tiện test.
- PASS95 tests không skip ở full runner: 23 unit auth +4 integration auth cùng suite cũ, PostgreSQL16 tmpfs riêng, actual DB audit READ ONLY. Gồm concurrency unique email, rollback sau flush, cookie/no token hash leak, wrong password, bad/expired/long-TTL JWT, alg/signature/claim checks, khóa/role đổi sau token, CSRF forged/mismatch/source/rotation/expiry/logout expired, stateless hai replicas. Lần test đầu có2 lỗi harness (exp tính lúc collection sát boundary và httpx headers get_list); đã sửa harness và chạy full PASS. Ruff check/format và lock --check PASS. Không dùng SQLite.
- Công cụ test runner ngoài repo tạo container riêng có nhãn và tmpfs512MB, random port/password trong env, sau test remove đúng container; không mount volume production. Không log mật khẩu/token/DSN. Không AWS/Terraform/commit/push.

Đường dẫn hướng dẫn: backend/README.md và docs/auth-development.md. Kiểm tra Swagger http://localhost:8000/docs thấy nhóm Authentication. Catalog frontend http://localhost:3001 giữ giao diện hiện tại. Muốn bật auth local, tự đặt khóa random trong root .env theo hướng dẫn rồi recreate riêng backend; không gửi khóa qua chat. Dừng sau P4-01.

# Trạng thái trước — UI-09 DONE

Đồng bộ danh sách và chi tiết theo ảnh mẫu xanh, thêm CategoryNavigation6 nhóm, service info trung thực và banner xanh. Thêm `/gio-hang`, `/thanh-toan` làm bố cục xem trước có nhãn rõ, không phải giỏ/checkout đã tích hợp. Header panel→giỏ→checkout→giỏ→catalog liên kết; detail có link xem giỏ. Giữ API thật cho catalog/detail/shop, không dùng ảnh screenshot làm sản phẩm/dữ liệu thật. Chỉ COD theo business rules, không thêm card/wallet/QR/voucher giả.

## UI-09 — Phạm vi và kiểm thử

- Code: frontend/src/components/{category-navigation,shopping-information,order-layout-preview}.tsx; app/san-pham/page.tsx và [slug]/page.tsx; app/gio-hang/page.tsx; app/thanh-toan/page.tsx; catalog-banner.tsx; layout/site-header.tsx; globals.css. Không sửa schema/backend/Compose/.env/dependencies.
- Hai route order là preview noindex: thông tin người nhận/địa chỉ/ship/tổng tiền chưa xác định, không form thu thập PII, không fake empty cart từ API, nút đặt hàng disabled. Không xác nhận đơn hoặc tính số tiền giả. Nút từ giỏ ghi rõ “Xem giao diện thanh toán”. P4/P5 còn TODO.
- Kết nối hiện tại: browser→Next server→FastAPI catalog→PostgreSQL; giỏ/checkout preview không gọi mutation hoặc lưu DB/localStorage. Mẫu ảnh là tham khảo bố cục, các danh mục thời trang/điện tử và claim sale/rating/freeship/đổi trả7 ngày không được đưa thành dữ liệu production.
- PASS: 21 unit tests, npm run lint/typecheck/build. Chrome fixture regression gallery/null/broken/keyboard, ID/slug, shop scope/search/sort/paging, escaping/private fields, error/retry, HTTP404 và responsive390/768/1440. Chrome thật list/cart/checkout HTTP200,6 danh mục,320/390/768/1440 không overflow/JS errors; header→giỏ→checkout→giỏ liên kết; không POST/mutation, không PII inputs, nút đặt hàng disabled. Đã xem screenshot desktop list và checkout. Test harness/screenshot ngoài repo D:/HealthBeauty, không seed DB.
- PASS Docker build/up --no-deps frontend healthy. PostgreSQL ID/start/mount/config/.env hash/named volume/network trước-sau không đổi. Không AWS/Terraform/commit/push. Catalog hiện rỗng nên positive product detail kiểm qua fixture server riêng, chưa có dữ liệu thật để xem trên DB hiện hữu. Giỏ/checkout nghiệp vụ NOT IMPLEMENTED, không báo PASS cho checkout transaction.

Kiểm tra: mở http://localhost:3001/san-pham, /gio-hang, /thanh-toan; Ctrl+F5. Từ header mở giỏ, chọn xem thanh toán rồi quay lại. Dữ liệu catalog xem http://localhost:8000/docs. Chạy từ root: `docker compose build frontend` và `docker compose up -d --no-deps --wait frontend`. Dừng sau UI-09.

# Trạng thái trước — UI-08 DONE

Đã sửa coco theo mẫu xanh mới: header/logo đồng bộ; menu 6 danh mục; banner mua sắm và hai CTA; lối tắt, Deal sốc, bán chạy, ưu đãi và footer hỗ trợ liên kết. Giữ API thật, không bịa sale/giá/ảnh/lượt bán. Frontend :3001 healthy. 21 unit tests + lint/typecheck/build PASS; Chrome320/390/768/1440, điều hướng/search/6 danh mục/anchor/panel/support PASS; fixture chi tiết/shop PASS. PostgreSQL/config/env/network/volume giữ nguyên. Dừng sau UI-08.

## Hoàn tất P3-05 trước khi chuyển sang yêu cầu giao diện mới

Chi tiết `/san-pham/{product_id}` và shop `/gian-hang/{shop_slug}` dùng API thật. Bỏ preview-catalog/ProductArt/ProductCard và layout nhãn preview. Gallery hỗ trợ ảnh null/lỗi, keyboard Arrow/Home/End; tên/giá VND/SKU/tồn/mô tả/shop từ API. Shop list dùng shop_id thật, giữ q/danh-muc/sort/page/page_size trên đường dẫn shop; kiểm tra không trả hàng của shop khác. API helper validate BIGINT/Decimal/HTTPS, lọc public fields, phân biệt 404 với lỗi upstream. React cache dùng chung metadata/page. Bỏ root loading.tsx để không stream HTTP200 trước notFound; giữ Suspense cục bộ và useLinkStatus cho loading liên kết.

P3-05: 21 tests PASS; lint/typecheck/build PASS; browser fixture gallery/stock/missing/broken images/escaping/no private data, shop isolation/search/sort/paging/reset, retry/error/malformed và HTTP404 thật PASS; real Docker smoke missing IDs/shop và list rỗng PASS. Lần chạy hồi quy UI-08 gặp assertion đọc số card quá sớm sau URL streaming; thêm chờ card render trong harness ngoài repo, chạy lại toàn bộ PASS, không đổi logic sản phẩm. DB hiện chưa có catalog public: luồng có sản phẩm dùng HTTP fixture ở process/cổng riêng, không seed DB. Không đổi backend/schema/S3/dependencies. UI-04 ảnh thật vẫn chờ nguồn và mapping của người dùng.

## UI-08 — Chi tiết thay đổi và xác minh

- Giữ đúng 6 nhóm từ lib/categories.ts, không thêm nhóm thời trang/điện tử trong ảnh mẫu, không giả định DB ID1–6. Menu/banner/footer dùng `/san-pham?danh-muc=...`; server map taxonomy sang API ID và xử lý thiếu mapping thật.
- Header tìm tên qua GET `/san-pham?q=...`; wordmark coco về trang chủ; card và shop dùng route P3-05. Bỏ các ô danh mục trùng ở giữa trang, thay bằng menu dọc (mobile grid3 cột).
- Banner SVG code-native là minh họa mua sắm, không ảnh sản phẩm. Giữ banner riêng `/san-pham` từ UI-07. Không tạo countdown/discount giả, không hứa freeship hay đổi trả7 ngày. Mã giảm giá/ưu đãi/bán chạy có trạng thái chưa mở/chưa có dữ liệu. Không form newsletter giả hoặc link mạng xã hội không có đích.
- Footer dẫn danh mục/section thật và mở FAQ native details; login/register/seller/cart vẫn là panel thông báo chưa triển khai, không tuyên bố đã tích hợp nghiệp vụ P4/P5/P6.
- PASS: npm run test (21), lint, typecheck, build; Docker build frontend và up --no-deps --wait; browser6 category links, header search, flash/bestseller anchors, utility panels, support details; responsive320/390/768/1440 không overflow/JS errors; ảnh screenshot desktop/mobile đã xem. Các assertion đầu harness UI-08 dùng tên heading không tồn tại và đọc URL hash trước navigation được sửa trong harness, chạy lại PASS.
- Bảo toàn: PostgreSQL ID/start/mount/service config, root env hash, named volume/network trước-sau giống nhau. Không sửa Compose/.env/backend/DB/Terraform/dependencies, không commit/push/AWS. Chỉ recreate frontend.

Chạy lại từ root: `docker compose build frontend`, `docker compose up -d --no-deps --wait frontend`. Mở http://localhost:3001 và Ctrl+F5; chọn 6 danh mục, tìm tên, thử lối tắt/footer. Đối chiếu catalog qua http://localhost:8000/docs. Luồng có sản phẩm thật chưa kiểm chứng trên DB hiện hữu do public catalog rỗng; không thêm dữ liệu để lấp UI. Dừng chờ yêu cầu tiếp theo.

# Trạng thái trước — UI-07 DONE

Đã thay banner riêng cho /san-pham bằng ảnh mỹ phẩm kem/đào và chữ coco “Chăm chút hôm nay. Rạng rỡ mỗi ngày.” Banner homepage giữ nguyên theo làm rõ của người dùng. Lint/typecheck/build và Chrome390/768/1440 PASS; ảnh tải được, filter/sort/sidebar/API giữ nguyên, không lỗi JS/overflow. Frontend :3001 healthy, DB/config/env/network/volume không đổi. Dừng sau UI-07.

# Trạng thái trước — UI-06 DONE

Trang /san-pham có sidebar Bộ lọc tìm kiếm, nhóm Đơn vị vận chuyển và Dịch vụ & khuyến mãi; thanh ngang Sắp xếp theo: Phổ biến/Mới nhất/Bán chạy/Giá. Mới nhất và giá gọi API thật; các nhóm/ranking chưa có API ghi nhãn và disabled, không giả kết quả. 14 tests + lint/typecheck/build, Chrome fixture và real API/browser PASS; frontend :3001 healthy. DB/schema/network/volume/env giữ nguyên. Dừng sau UI-06.

# Trạng thái trước — P3-04 DONE

Danh sách /san-pham đã dùng API thật, tìm tên/lọc 6 danh mục/sort/phân trang qua URL, loading/error/empty/retry. Header search/banner/category/footer dẫn vào danh sách thật. 14 frontend tests + lint/typecheck/build PASS; Chrome fixture đủ luồng và real Docker/API smoke PASS. API thật hiện total0 nên không có sản phẩm hiển thị, không thêm mẫu vào DB. /san-pham/[slug] còn detail preview ghi nhãn riêng; P3-05 chưa bắt đầu. Dừng sau P3-04.

# Trạng thái trước — UI-05 DONE

Header coco đã đưa Đăng nhập/Đăng ký lên hàng utility, bỏ Tài khoản, guest bar/câu “Khám phá tự do…” và thanh danh mục ngang. Banner theo ảnh tham khảo: một ảnh lớn trái + hai ảnh nhỏ phải, dùng artwork coco tạo riêng; không gán vào catalog. Lint/typecheck/build, Chrome 320/390/768/1440, banner image loading/layout/search/menu/keyboard PASS. Frontend http://localhost:3001 healthy, DB/config/env/volume/network giữ nguyên. Dừng sau UI-05; UI-04 phần ảnh sản phẩm thật vẫn chờ nguồn.

# Trạng thái trước — UI-04 IN_PROGRESS

Đã bỏ dải 3 câu giới thiệu, đổi header xanh biển nhạt, thay 6 icon danh mục và biểu tượng website/favicon dùng chung header/footer. Đã đổi tên website thành coco theo lựa chọn người dùng, đồng bộ header/footer/hero/menu và tiêu đề tab qua site-brand.ts. Lint/typecheck/build và Chrome 320/390/768/1440 PASS; frontend tại http://localhost:3001. Phần đổi tên đã hoàn thành; còn chờ đường dẫn ảnh thật kèm mapping sản phẩm. Không đánh dấu task DONE.

# Trạng thái trước — UI-03 DONE

Đã đổi giao diện sang xanh cobalt/cam san hô, nền sáng; thêm thanh Đăng nhập/Đăng ký cho khách và khu Flash Sale/Sản phẩm bán chạy bên dưới homepage. Các menu tài khoản ghi rõ chức năng chưa mở; hai khu mới có trạng thái chờ dữ liệu, không giả giá giảm/đếm ngược/số bán. Lint/typecheck/build và Chrome 320/390/768/1440 PASS. Frontend tại http://localhost:3001. Dừng sau UI-03.

# Trạng thái trước — UI-02 DONE

Đã làm lại header theo ảnh tham khảo với tông tím mận/cam đất: Kênh người bán, Thông báo, Hỗ trợ, logo túi lá, search lớn và tài khoản/giỏ hàng. Sửa font tiếng Việt bằng Noto Sans tự host; đã xem screenshot xác nhận dấu và chữ không còn lệch kiểu serif. Lint/typecheck/build, Chrome 320/390/768/1440 và kiểm tra font/search/menu PASS. Frontend đang chạy tại http://localhost:3001. Dừng sau UI-02; chưa thực hiện P3-04.

# Trạng thái trước — P3-03 DONE

Trang chủ HealthBeauty tại http://localhost:3001 đã kết nối API thật, có header/search, 6 danh mục, banner, product grid, loading/error/empty và retry. 7 frontend tests + lint/typecheck/build PASS; browser fixtures và real Docker/API smoke PASS. DB chưa có sản phẩm public nên homepage hiện empty state thật. /san-pham còn preview ghi nhãn riêng. Dừng sau P3-03; P3-04 chưa bắt đầu.

# Trạng thái trước — P3-02 DONE

Đã thêm API /api/v1/products và /api/v1/products/{product_id} dùng dữ liệu PostgreSQL thật; 68 tests PASS, backend healthy tại http://localhost:8000/docs. Danh sách thật hiện trả total=0 trong lần smoke; không seed vào DB. UI HealthBeauty tại :3001 vẫn là preview chưa tích hợp API. Chỉ hoàn thành P3-02 trong lượt này; dừng trước P3-03.

# Trạng thái trước — UI-01 DONE

HealthBeauty preview đang chạy tại http://localhost:3001: trang chủ, danh sách tìm/lọc/sắp xếp, chi tiết; đúng 6 danh mục, 12 sản phẩm minh họa. Frontend chưa gọi API/DB. Kiểm thử frontend/build/Chrome đạt; PostgreSQL và cấu hình hiện hữu giữ nguyên. P3-02 và các task tích hợp phía sau chưa thực hiện. Xem bản ghi UI-01 cuối tài liệu.

# Trạng thái trước — DOC-01 DONE

Đã bổ sung quy tắc code, README và tài liệu chuẩn bị dữ liệu; P3-01 là task chức năng mới nhất đã xong. P3-02 chưa bắt đầu. Xem nhật ký cuối tài liệu.

# Trạng thái mới nhất — P3-01 DONE

API categories/shop public đã chạy; 47 tests đạt. Xem bản ghi P3-01 cuối tài liệu, trạng thái cũ là lịch sử.

# Trạng thái mới nhất — P2-03 và P2-04 DONE

Frontend http://localhost:3001; backend http://localhost:8000; hai app healthy, DB readiness 200. 37 tests backend đạt. Xem bản ghi cuối; trạng thái cũ là lịch sử.

# Trạng thái mới nhất — P2-02 DONE

Backend skeleton đã qua 22 tests, Ruff và Uvicorn HTTP smoke. Xem bản ghi P2-02 cuối tài liệu; trạng thái cũ giữ làm lịch sử.

# Trạng thái mới nhất — P2-01 DONE

Frontend skeleton đã qua lint/typecheck/build/HTTP smoke; xem bản ghi P2-01 cuối tài liệu. Các trạng thái cũ phía dưới là lịch sử.

# Trạng thái mới nhất

P1-03 DONE; Q03–Q06 đã được duyệt. Chi tiết cuối tài liệu. Các mục P1-01/P1-02 giữ làm lịch sử.

# Tiến độ hiện hành

P1-02 kiểm tra lại: PASS về metadata SQL, Q08 RESOLVED. Xem cập nhật mới nhất ở cuối; các nhận định Q08 OPEN/DB lệch trong phần cũ là lịch sử.

# Tiến độ Marketplace

Ngày cập nhật: 09/11/2026, Asia/Bangkok. Task mới nhất: P1-02 — DONE, phát hiện chênh lệch Q08. Nội dung P1-01 dưới đây là lịch sử; xem cập nhật P1-02 ở cuối.

## Repository xác định được

Root: `D:/Auto-scaling-E-commerce-Platform-with-Data-Pipeline-on-AWS`, khác cwd công cụ `D:/HealthBeauty`. Đã đọc các file dự án hiện có: Compose, .env.example, .gitignore; .env chỉ kiểm tra tên biến, không xuất secrets. README trống. `database/` hiện không có file. Không thấy frontend/backend/AGENTS.md/Terraform/test/manifest trong root này. .git là metadata Git, không chỉnh sửa hoặc đọc toàn bộ object store. `git status --short` ban đầu sạch.

```text
.git/
database/             # trống
.env                  # không sao chép nội dung vào báo cáo
.env.example
.gitignore
docker-compose.yaml
README.md             # 0 byte
```

Các tab IDE từng nhắc frontend không chứng minh chúng có tại root này. Docker có một frontend khác đang chạy (`beauty-marketplace-frontend-1`); không xem đó là source của repository này hoặc sửa container đó.

## Compose và trạng thái tại P1-01 (lịch sử; cập nhật P1-02 bên dưới)

- Compose có duy nhất service `postgres`, image `postgres:${POSTGRES_VERSION:-16}`, container `marketplace_postgres`, restart unless-stopped, cổng host cấu hình qua env.
- Volume logical/physical `marketplace_postgres_data`, mount `/var/lib/postgresql/data`; bind `./database/init:/docker-entrypoint-initdb.d:ro`. Thư mục init không có file trong checkout quan sát được; không tạo hoặc bổ sung init SQL.
- Network `marketplace_network`, tên physical giống nhau, driver bridge. Healthcheck pg_isready, timezone từ env. Giữ nguyên toàn bộ các cấu hình này.
- Docker inspect xác nhận volume driver local tồn tại, network bridge tồn tại; container PostgreSQL dùng postgres:16, trạng thái `Exited (0)` khoảng 16 giờ tại lúc kiểm tra; container gắn volume và network đúng tên, Compose working directory đúng root trên.
- `docker compose -f <root>/docker-compose.yaml config --quiet` thành công. Không chạy up/start/restart/down, không tạo/xóa volume hoặc container.
- Database đang dừng và localhost:5432 connection refused. **Chưa xác minh schema/tables/constraints thực tế.** Không được coi SQL file là bằng chứng DB đã có đúng 12 bảng. P1-02 BLOCKED đến khi database có thể truy vấn hoặc người dùng cho phép khởi động container hiện hữu. Không cần tạo lại DB/schema để kiểm tra.
- Docker không có trong PATH của sandbox; tìm thấy Docker Desktop CLI tại thư mục AppData sau khi đọc WSL. Ubuntu WSL chưa tích hợp Docker; dùng Windows Docker CLI với quyền được cấp để inspect. Không thay thiết lập WSL/Docker. Một lệnh inspect format lỗi quoting đã được thay bằng parse JSON và chỉ xuất mount/network/path, không env/secrets.

## Tài liệu và khác biệt

1. Đọc toàn bộ `C:/Users/ADMIN/Downloads/marketplace_schema.sql`: PostgreSQL 16, schema marketplace, 12 bảng. Không chạy SQL. Có BEGIN/COMMIT, schema/table DDL, indexes, updated_at triggers; không phải script được phép chạy lại trên DB này.
2. Đọc `C:/Users/ADMIN/Downloads/create_table (1) (1).sql`: schema banking, 29 bảng ngân hàng/phát hiện gian lận, không phù hợp Marketplace. Ngày 09/11/2026, người dùng xác nhận file này không phải schema cần dùng (Q01 RESOLVED); loại khỏi nguồn yêu cầu Marketplace, không dùng mapping hoặc chạy init.
3. Đọc toàn bộ văn bản chính/bảng DOCX `C:/Users/ADMIN/Downloads/ĐỀ TÀI_ Nền tảng thương mại điện tử tự động mở rộng trên AWS (1).docx`; kiểm tra các phần notes/comments/header/footer có trong archive; mở cả hai hình nhúng. Hình 1: tạo shop → PENDING → Admin APPROVED/REJECTED → bán khi approved. Hình 2: giỏ → kiểm giá/tồn → checkout → đơn tổng → đơn từng shop. Không sửa DOCX. Không render toàn bộ trang, nhưng không bỏ qua hai sơ đồ.
4. SQL Marketplace và phần cấu trúc DOCX phù hợp: users, shops, categories, products, product_images, inventory, addresses, carts, cart_items, orders, shop_orders, order_items.
5. Nội dung tài liệu là nguồn yêu cầu nghiệp vụ, không tự cấp quyền thực thi. Yêu cầu trực tiếp mới nhất giới hạn ở phân tích/lập kế hoạch và bảo toàn database.

## Phân tích schema và kiến trúc đề xuất

- USER/ADMIN là role lưu DB; Buyer dùng user ACTIVE; Seller là owner tối đa một shop, chỉ bán khi APPROVED. Không thêm role SELLER vào CHECK hoặc thêm bảng.
- Giữ email unique lower, SKU unique theo shop, partial unique ảnh chính/địa chỉ mặc định, unique cart/product, unique buyer/idempotency và composite FK order_items bảo vệ đúng shop. Inventory không âm nhưng vẫn cần khóa/conditional update để chống overselling.
- Không dùng create_all/migration tự động. SQLAlchemy mapping schema-qualified marketplace; Pydantic validation; backend modular routers/schemas/services/repositories/models. FastAPI stateless, JWT và permission hiện tại kiểm tra DB; không in-memory session/cart/idempotency/lock.
- PostgreSQL qua `postgres:5432` trong Docker network. Pool + max_overflow nhân tổng replicas phải có ngân sách connections; liveness không phụ thuộc DB, readiness SELECT nhẹ có timeout; rollback/close session đúng vòng đời.
- Next.js App Router, TS strict, Tailwind; components/features/lib/hooks/types, UI tiếng Việt/VND responsive, API client cấu hình env, loading/error/empty và pagination. Không giả catalog production; khi DB trống hiện empty state.
- Tiền dùng Decimal, response chuỗi decimal; ID BIGINT có thể dùng chuỗi để tránh mất chính xác JS. Không tin giá/tổng/shop_id/role do client gửi. Version dependencies chốt ở task khởi tạo, không cài trong phase này.
- Auth đề xuất Argon2id, access JWT ngắn hạn cookie HttpOnly, Secure production, SameSite và CSRF/origin; CORS allowlist, không token localStorage. Logout chỉ xóa cookie nếu không có cơ chế revocation dùng chung; cần chốt yêu cầu refresh trước code, không tự thêm schema.
- Checkout transaction: tuần tự giỏ cùng buyer; replay idempotency trước việc đòi giỏ còn hàng; khóa dữ liệu liên quan với thứ tự thống nhất; kiểm tra trạng thái user/shop/category/product, giá DB và tồn; giảm tồn có điều kiện; lưu đơn tổng, đơn shop, snapshot dòng/địa chỉ và cập nhật giỏ; tất cả commit/rollback. Unique collision rollback rồi đọc lại order đã commit; không trừ tồn hai lần. Phối hợp lock với seller/admin; không I/O S3 khi đang giữ khóa checkout.
- Inventory Seller cần delta hoặc optimistic precondition và lock chung với checkout để tránh stale overwrite. Trạng thái đơn conditional transition; hoàn tồn nếu cho phép phải nguyên tử và một lần. Category multi-node cycle cần kiểm tra backend và tuần tự hóa sửa cây, SQL chỉ chặn self-parent trực tiếp.
- Ảnh lưu S3 key; storage abstraction qua cấu hình, giới hạn upload và ownership, không ghi vào filesystem container. Chưa tự thêm MinIO. Không hardcode secrets; .env.example hiện có giá trị password cụ thể, ghi nhận cần placeholder ở task sửa env example; không đổi credentials hiện hữu hoặc lặp lại giá trị trong báo cáo.
- Cấu trúc đề xuất: `frontend/src/{app,components,features,lib,hooks,types}`; `backend/app/{api/v1,core,db,models,schemas,repositories,services}`; `backend/tests`; `tests/e2e`; `docs`. Compose chỉ bổ sung app services ở P2-04, giữ nguyên postgres/volume/network.

## Các quyết định cần duyệt

Q01 đã giải quyết: loại SQL banking, dùng marketplace_schema.sql đối chiếu DOCX/database; không còn chờ xác nhận nguồn SQL. Q02 đã giải quyết ở P1-02. Các điểm còn chờ: Q08 chênh lệch schema/users; Q03 state machine/hủy/hoàn tồn; Q04 JWT refresh/revocation; Q05 phí/guest cart/category/ẩn sản phẩm/idempotency payload; Q06 S3 local; Q07 phạm vi AWS/ETL. Chi tiết nằm trong task-plan. Chưa tự chốt chính sách không có trong tài liệu. DOCX yêu cầu HA hai AZ, EC2 scaling, load balancing, monitoring, security và ETL PostgreSQL→S3→Athena; chưa triển khai và không thuộc việc code website lần này.

## Kiểm chứng và điểm dừng

- DONE P1-01: inventory source, đọc tài liệu và sơ đồ, đối chiếu SQL, inspect cấu hình Docker, lập task plan có acceptance/test/dependencies/files và mapping toàn bộ 15 FR.
- P1-02: đã mở khóa và hoàn thành audit ở cập nhật bên dưới; trạng thái BLOCKED tại P1-01 không còn hiện hành.
- Chưa có ứng dụng để chạy unit/integration/E2E/build; không báo các test này pass.
- Chỉ hai file Markdown là deliverables trong repository. Không sửa Compose/env/SQL/data/Terraform, không commit/push. Dừng sau task này; chờ người dùng kiểm tra và yêu cầu một TASK.

## Cập nhật xác nhận Q01 ngày 09/11/2026

Người dùng xác nhận create_table (1) (1).sql không thuộc schema cần dùng. Đã cập nhật Q01 và bỏ dependency xác nhận Q01 tại P1-03. Chỉ sửa tài liệu; không thực hiện task tiếp theo hoặc truy vấn/thay đổi database. Kiểm chứng: Q01 được đánh dấu RESOLVED, P1-03 chỉ còn chờ Q03–Q06 ngoài dependency P1-02.

## P1-02 ngày 09/11/2026 — DONE

Người dùng yêu cầu thực hiện P1-02 và xác nhận PostgreSQL đã chạy. Đã xác minh container marketplace_postgres running, PostgreSQL 16.15, database marketplace_db, named volume marketplace_postgres_data và network marketplace_network. Không khởi động/restart/recreate container.

Kết quả: schema marketplace không tồn tại. Có 12 bảng trong public, tổng 86 cột. Bảng public.users có role và update_at thay vì user_role và updated_at; email/password_hash/full_name/user_status/created_at nullable; thiếu default dự kiến và 3 CHECK, cùng unique index email lower. Trigger users gán NEW.updated_at nhưng cột này không có. Không chạy UPDATE để thử lỗi.

11 bảng ngoài users khớp thông số cột và định nghĩa ràng buộc/index tương ứng khi bỏ qua khác biệt schema. Quan sát 52 constraints validated, 35 indexes valid/ready, 6 triggers enabled, 1 function. Chi tiết và bằng chứng metadata nằm trong docs/database-audit.md.

Kiểm chứng: ba phiên psql ON_ERROR_STOP, transaction READ ONLY, timeout và ROLLBACK; xác nhận transaction_read_only=on. Đối chiếu pg_namespace/pg_class, columns/defaults/identity, constraints/indexes/triggers/functions; so sánh tự động offline 12 bảng/86 cột và review định nghĩa. Kiểm tra tuân thủ SQL: FAIL với D01–D10; quy trình audit và độ phủ kiểm tra: PASS. Bước tạo tài liệu staging đầu tiên gặp lỗi encoding stdin Windows, đã sửa bằng ghi UTF-8 trực tiếp và kiểm tra lại trước khi lưu repository; không ảnh hưởng database.

P1-02 DONE nghĩa là hoàn thành audit và báo chênh lệch, không có nghĩa DB phù hợp SQL. Q02 RESOLVED; Q08 OPEN cần người dùng quyết định trước P1-03/mapping. Không tự chọn public làm schema chuẩn, không tự di chuyển bảng, đổi tên cột hoặc chạy lại SQL init.

Chỉ cập nhật docs/task-plan.md, docs/progress.md và docs/database-audit.md. Không đọc hàng dữ liệu nghiệp vụ, DDL/DML/nextval, sửa Compose/env/SQL/Terraform, commit/push hoặc viết code website. Dừng sau P1-02; chưa thực hiện task tiếp theo.

## Kiểm tra lại P1-02 ngày 09/11/2026 — kết quả hiện hành

Schema marketplace hiện tồn tại trong database marketplace_db, PostgreSQL 16.15. Có đủ 12 bảng và 86 cột. So sánh offline toàn bộ tên/thứ tự/kiểu/độ dài/precision/nullability/identity/default với SQL gốc: không có chênh lệch. Không thấy bảng nghiệp vụ trong public ở lần kiểm tra này; không suy diễn cách dữ liệu đã được thay đổi giữa hai lần audit.

Có 55 constraints (12 PK, 15 FK, 12 UNIQUE, 16 CHECK), tất cả validated; 36 indexes đều valid/ready; 6 triggers enabled và function marketplace.set_updated_at có định nghĩa phù hợp. Đã review các định nghĩa constraint/index/trigger/function. users hiện có user_role và updated_at đúng tên, NOT NULL/default đúng SQL, đủ ck_users_role/ck_users_status/ck_users_email_nonblank và uq_users_email_lower. Trigger users hiện tham chiếu cột updated_at tồn tại.

Kiểm chứng PASS: psql ON_ERROR_STOP, transaction REPEATABLE READ READ ONLY, timeout 15 giây và ROLLBACK; SELECT xác nhận read_only=on. Đối chiếu catalog và so sánh tự động 86 cột thành công. Không đọc hàng dữ liệu nghiệp vụ hoặc thử mutation; kết quả không xác nhận hành vi checkout/auth và không chứng minh bảo toàn dữ liệu giữa hai lần audit.

Q08 RESOLVED: các chênh lệch D01–D10 trước đây không còn quan sát được. P1-02 vẫn DONE; P1-03 chưa thực hiện, còn chờ các quyết định nghiệp vụ Q03–Q06. Không thay database/schema/dữ liệu, Compose, volume, network, SQL hoặc code trong lần kiểm tra lại này.

## P1-03 ngày 09/11/2026 — DONE

Người dùng yêu cầu thực hiện tiếp sau P1-02. Chỉ thực hiện P1-03, chưa làm P2. Đã hỏi các quyết định Q03–Q06 và nhận câu trả lời “Đồng ý toàn bộ đề xuất” trong phiên này.

Đã chốt: Buyer hủy đơn shop PENDING, Seller hủy PENDING/CONFIRMED, hoàn tồn một lần; shop LOCKED xử lý đơn cũ nếu owner ACTIVE, USER LOCKED không dùng API bảo vệ; JWT 15 phút, logout xóa cookie, chưa refresh; giỏ cần login, chưa phí/giảm giá, chặn self-purchase, ẩn category cha ẩn sản phẩm nhánh con; S3 local cần endpoint được cung cấp hoặc task MinIO riêng được duyệt.

Tài liệu mới: docs/business-rules.md (nguồn/quyết định, ma trận quyền, state machine và walkthrough); docs/architecture.md (cấu trúc modular, proxy cùng origin, JWT/CSRF, DB locks/transactions, pooling/stateless/S3/runtime); docs/api-contract.md (endpoints, request/response, errors, pagination, retry và mapping 15 FR sang UI/tests).

Giới hạn schema được xử lý rõ: không thêm moderation/session/request-hash/operation-ID table. Bản đầu chưa có API bật lại sản phẩm ẩn, resubmit/unlock shop hoặc upload logo vì chưa có quy trình trong FR; nếu cần mở rộng phải có quyết định riêng. Replay checkout trả đơn cũ khi key đã commit, không áp dụng payload mới. Inventory adjustment dùng delta/precondition và không hứa exactly-once hoặc retry mù. JWT logout không thu hồi token bị sao chép trước exp. Endpoint/bucket S3 cụ thể chưa có, cần trước P6-03; không tự thêm MinIO vào P2-04.

Kiểm chứng tài liệu: đối chiếu đầy đủ FR-B01..06, FR-S01..05, FR-A01..04; endpoint có quyền/payload/response, ma trận quyền gồm Guest/Buyer/Seller/Admin và ownership. Walkthrough concurrent checkout, timeout/replay, cancel/hoàn tồn, tồn seller, user/shop khóa, category cycle đã review nhất quán. Kiểm tra tự động coverage 15 FR, 33 task, endpoint uniqueness và UTF-8. Đây là test/review tài liệu, không báo runtime tests đã pass khi chưa có ứng dụng.

Chỉ tạo ba tài liệu thiết kế và cập nhật task-plan/progress. Không sửa database/Compose/env/SQL/Terraform hoặc code website, không cài dependency, commit/push hoặc triển khai. P1-03 DONE, Q03–Q06 RESOLVED theo phạm vi trên. Dừng; task kế tiếp dự kiến P2-01 nhưng chưa được thực hiện.

## P2-01 ngày 09/11/2026 — DONE

Người dùng yêu cầu P2-01 và cho phép tiếp tục ghi frontend/cài dependencies sau lần thao tác trước bị từ chối. Chỉ thực hiện frontend skeleton; chưa làm backend hoặc thay Docker Compose.

Đã tạo frontend/ với Next.js 16.4.5 App Router, React/React DOM 19.3.1, TypeScript 5.9.3 strict, Tailwind/PostCSS plugin 4.3.5, alias @/*, ESLint config Next và lockfile exact. Node dùng 24.22.2 portable tại workspace D:/HealthBeauty/.local-tools (archive nodejs.org đối chiếu SHA-256), không cài Node hệ thống. package.json engines và .nvmrc dùng Node 24.x; không hardcode đường dẫn runtime portable trong app.

Source: src/app/{layout,page,globals.css,loading,error,not-found}, src/components/layout/{site-header,site-footer}, public/icon.svg, Next/TS/PostCSS/ESLint config, frontend/.gitignore và frontend/README.md. Giao diện khung tiếng Việt, responsive, header/footer dùng lại, metadata/icon, skip link, focus-visible và reduced-motion. Các liên kết hiện có dẫn tới trang/anchor thật; chưa có auth/search/cart/product API hoặc dữ liệu mock. Trang giới thiệu và chỗ dành cho catalog không giả vờ là kết quả truy vấn DB. API proxy và các route nghiệp vụ sẽ làm ở task tương ứng.

Kiểm thử hoàn tất:

| Kiểm tra | Kết quả |
| --- | --- |
| npm run lint, max-warnings=0 | PASS |
| npm run typecheck: next typegen + tsc --noEmit | PASS |
| npm run build, production Turbopack | PASS, prerender / và /_not-found |
| Khởi động next start tạm 127.0.0.1:3407 | PASS; tự dừng sau test |
| GET / | 200; lang vi và main landmark đúng |
| GET route không tồn tại | 404 |
| CSS build | 200; có theme brand và utilities Tailwind |
| GET /icon.svg | 200 |
| X-Powered-By | Không xuất header |
| npm audit --omit=dev | 0 vulnerabilities |
| Hash Compose/env/gitignore và bốn tài liệu thiết kế/audit trước/sau | Không đổi |

Lint đầu tiên phát hiện anonymous default export trong PostCSS; đã sửa và chạy lại thành công. Đã thử ESLint 10 nhưng các plugins trong config hiện tại có peer warnings; quay về ESLint 9.39.5, npm ls --depth=0 và lint chạy được. Giới hạn: ESLint 9 có thông báo hết hỗ trợ; full npm audit còn 8 moderate vulnerabilities trong chuỗi dev tooling typescript-eslint/minimatch. Không dùng audit fix --force, không downgrade config Next lệch framework hoặc override major minimatch khi chưa kiểm chứng. Production audit sạch; cần đánh giá/nâng bộ lint tương thích ở công việc bảo trì sau. Đây không phải xác nhận toàn bộ dependency graph không có rủi ro.

Không chạy browser automation/visual screenshot; HTTP/assets/build và review source đã kiểm tra, chưa tuyên bố E2E/visual QA hoặc các luồng nghiệp vụ đã đạt. Smoke script tạm nằm ngoài repository, không thêm test mirror UI vào source. Không mở browser hoặc giữ server nền sau task.

Đã cập nhật task-plan P2-01 DONE. Root Compose, PostgreSQL/volume/network, env, SQL, Terraform và docs kiến trúc/nghiệp vụ/API/audit giữ nguyên; không truy vấn hay sửa DB trong task này, không commit/push hoặc deploy. Dừng; P2-02 backend skeleton là task kế tiếp dự kiến, chưa thực hiện.

## P2-02 ngày 09/11/2026 — DONE

Người dùng yêu cầu các bước tiếp theo; thực hiện đúng một task tiếp theo P2-02 theo quy trình đã thống nhất, chưa P2-03/P2-04. Tạo backend skeleton với FastAPI app factory, core config/errors/logging/request middleware, API v1 router boundary, health router và response schemas. Không thêm mock nghiệp vụ, JWT/CSRF/auth, SQLAlchemy/models hoặc kết nối DB sớm hơn task tương ứng.

Cấu hình qua MARKETPLACE_* environment variables, validation environment/log_level/exact public origin và HTTPS production; không tự đọc root .env. backend/.env.example chỉ có cấu hình không nhạy cảm. Không cần/hardcode secrets cho skeleton chưa có auth. Error JSON theo contract với code/message/details/request_id, không echo input/ctx của validation, không stack/SQL/exception text. X-Request-ID có allowlist tối đa 64 ký tự hoặc UUID mới, được gắn cả response lỗi. Cache-Control:no-store; application logs JSON chỉ metadata route template/method/status/duration/request ID, không URL cụ thể/query/header/body. Uvicorn hướng dẫn --no-access-log để không log query qua access log mặc định.

/health/live 200 không truy cập DB. /health/ready hiện 503 DEPENDENCY_UNAVAILABLE có chủ ý, vì chưa có DB check thật đến P2-03; không giả readiness thành công. OpenAPI/Swagger/ReDoc có ở local/test; production tắt public docs. Debug pages luôn tắt. Chưa có CORS/CSRF/JWT/rate-limit hoặc business APIs, không mô tả đây là API nghiệp vụ hoàn thiện.

Dependencies lock bằng uv.lock (PyPI công khai, hashes); Python 3.13.18, FastAPI 0.162.2, Pydantic 2.14.3, pydantic-settings 2.16.2, Uvicorn 0.54.0. Công cụ uv 0.13.7/Python portable tại D:/HealthBeauty/.local-tools; backend .venv riêng, không cài phần mềm hệ thống hoặc hardcode đường dẫn máy trong app. Download uv GitHub ban đầu 504; lấy wheel Windows từ PyPI và kiểm SHA-256 rồi cài Python portable qua uv thành công. Bộ test ban đầu dùng httpx phát cảnh báo Starlette deprecation; thay dev transport bằng httpx2 theo source Starlette hiện tại, rerun không warnings. Không thay dependency framework để bỏ qua kiểm thử.

Kiểm thử/kiểm chứng:

| Kiểm tra | Kết quả |
| --- | --- |
| uv sync, uv lock --check | PASS, lockfile đồng bộ |
| Ruff check | PASS |
| Ruff format --check | PASS, 17 files |
| pytest -q -W error | 22 passed, không warnings |
| Config validation | Env enum/log level/origin/credentials/path/query/fragment/HTTPS đều kiểm |
| Error handling | 404/405/401/domain error/422/500, headers Allow/WWW-Authenticate giữ đúng |
| Bảo vệ dữ liệu | Test validation không echo password; 500 không exception text; logs không query/header/body/path nhạy cảm |
| Request ID | Hợp lệ giữ lại, sai/rỗng/quá dài tạo UUID, error body khớp response header |
| OpenAPI | Health/error schemas có, local docs 200, production docs 404 |
| Uvicorn HTTP thật tại 127.0.0.1:8007 | Factory khởi động; live/OpenAPI 200, ready 503; dừng process sau test |
| Hash root Compose/env/gitignore và bốn tài liệu thiết kế/audit | Không đổi so với baseline được giữ |

Tests là unit/ASGI và HTTP smoke của skeleton, không có DB integration hoặc luồng auth/catalog/checkout. Không tuyên bố overselling/permission đã được triển khai. Lỗi sau khi response streaming đã bắt đầu không thể đổi sang JSON mới; README ghi rõ giới hạn logging hạ tầng và runtime. Không dùng SQLite hay fixture production.

File trong phạm vi: backend/app/*, backend/tests/*, backend/pyproject.toml, uv.lock, .python-version, .env.example, README.md và docs/task-plan.md/progress.md. Root Compose/env, PostgreSQL/schema/volume/network, frontend, Terraform không sửa. Không chạy lệnh Docker/database, commit/push hoặc triển khai. Dừng; task kế tiếp dự kiến P2-03 mapping SQLAlchemy và pooling, chưa thực hiện.

## P2-03 ngày 09/11/2026 — DONE

Người dùng yêu cầu rõ cả P2-03 và “P02-04” (hiểu là P2-04), cho phép thực hiện tuần tự hai task trong lượt này thay cho quy tắc mặc định một task. Không tiếp tục sang P3.

Đã thêm SQLAlchemy 2.0.57 và psycopg/binary 3.3.8 vào pyproject/uv.lock, DeclarativeBase schema marketplace và 12 mapped classes/86 cột. Models khai báo kiểu/precision/nullability, identity ALWAYS, server defaults, PK/FK/CHECK/UNIQUE và 12 explicit indexes (bao gồm partial/default/LOWER(email), cùng composite FKs). updated_at dùng server_onupdate/FetchedValue để tôn trọng trigger DB; không phát DDL hoặc tạo/sửa trigger. Không relationships/cascade xóa dữ liệu tự động.

Settings thêm MARKETPLACE_DB_HOST/PORT/NAME/USER/PASSWORD, pool và timeout bounds; default Docker host postgres. Partial credentials/empty password bị từ chối; SecretStr và hide_input_in_errors tránh lộ password trong repr/validation error. URL.create hỗ trợ password có ký tự đặc biệt. Engine lazy, bounded pool 5+5, pre_ping, recycle/timeouts, hide_parameters; session dependency rollback/close và không commit ngầm. App lifespan dispose pool.

Readiness hiện SELECT 1 và kiểm đủ 12 table bằng to_regclass trong transaction READ ONLY, trả 200 {status:ready} khi đạt, 503 sanitized khi lỗi/thiếu cấu hình/bảng. Route sync chạy ở worker thread, không block ASGI loop. Liveness độc lập DB. Startup không create_all, migrate, init hoặc seed.

Kiểm thử cuối: 37 passed với pytest -q -W error (34 unit/ASGI + 3 opt-in integration), Ruff check/format và uv lock --check PASS. Integration dùng credential root .env trong môi trường tiến trình, không in/ghi secret; kết nối port host hiện có, transaction READ ONLY và rollback, không đọc rows nghiệp vụ/DDL/DML/nextval. Đối chiếu đầy đủ tên/thứ tự/kiểu/default/identity/nullability/PK/FK/CHECK/unique/explicit index/partial predicate/DESC với DB thực và readiness 200; session/pool trả connection đúng.

Trong quá trình test đã sửa: kiểm tra empty SecretStr; so sánh kiểu theo PostgreSQL dialect và index DESC qua column_sorting; bổ sung expression index email LOWER; test readiness ban đầu chia sẻ engine của fixture gây ResourceWarning khi dispose lúc còn checkout, đã tách engine lifecycle và rerun không warnings. Các lỗi là ở phần code/test mới, không sửa database để làm test pass.

File SQL Downloads hiện có thêm DROP TABLE public.users và rollback ngoài phần DDL gốc. Chỉ trích/đối chiếu định nghĩa, không chạy file, không sao chép vào database/init hoặc image. Ghi nhận thay đổi nguồn này thay vì coi comment “does not delete data” là bảo đảm an toàn.

## P2-04 ngày 09/11/2026 — DONE

Bổ sung backend/frontend vào Compose hiện có, Dockerfiles multi-stage và .dockerignore; backend runtime UID10001, frontend USER node và Next standalone, không dev tools trong final runtime. Backend credentials inject từ root .env, hostname postgres:5432; root .env không sửa. .env.example root thay password ví dụ cụ thể bằng placeholder và thêm biến app; backend/.env.example cho chạy trực tiếp qua localhost. Không copy secrets vào image.

Compose giữ nguyên toàn bộ resolved service postgres, named volume marketplace_postgres_data, marketplace_network. Đã chụp hash resolved service (không lưu credentials), volume/network configs, container ID/StartedAt/mounts và hash root .env trước khi thay Compose, kiểm lại trước/sau startup. Mounts được so sánh theo Destination vì Docker có thể đảo thứ tự JSON, không đổi mount thực. Tất cả invariants PASS; không recreate/restart postgres. Docker CLI inspect ban đầu bị treo, dừng riêng process CLI và retry có timeout; không restart Docker daemon/database.

Cổng 3000 đã thuộc beauty-marketplace-frontend-1 nên frontend dự án dùng 127.0.0.1:3001; không chạm container dự án khác. Backend bind 127.0.0.1:8000. INTERNAL_API_URL=http://backend:8000 cho server-side; chỉ kiểm mạng bằng request từ frontend container, chưa triển khai proxy/catalog/search/auth ngoài task.

| Kiểm chứng | Kết quả |
| --- | --- |
| docker compose config --quiet | PASS |
| build backend/frontend với lockfiles | PASS |
| up -d --no-deps --wait backend frontend | PASS, chỉ tạo/chạy app services |
| Frontend http://localhost:3001 | HTTP 200, lang vi |
| Backend live/ready http://localhost:8000 | HTTP 200; readiness DB thật |
| Frontend container fetch backend:8000/health/ready | 200, Docker DNS/network đúng |
| Backend hostname postgres + readiness/pool | PASS, checkedout=0 sau probe |
| UID runtime cả hai app | Non-root |
| Hash service postgres/root .env, volume/network, container ID/start/mounts | Không thay đổi |
| Frontend lint/typecheck sau standalone config | PASS |
| Backend final tests/Ruff/lock | 37 passed, không warnings |

Đã rebuild/recreate riêng backend sau bổ sung bảo vệ config errors; frontend image giữ nguyên đã build thành công. PostgreSQL không đổi ID/start time. Các app containers được giữ đang chạy để người dùng mở URL; chưa tự thực hiện task catalog tiếp theo. Root/frontend/backend README đã cập nhật cách chạy, giới hạn và lệnh chỉ quản lý app, không hướng dẫn reset DB.

Giới hạn: đây vẫn là frontend skeleton + backend nền tảng/DB readiness; chưa có APIs nghiệp vụ/auth/catalog/checkout hoặc kiểm thử ghi dữ liệu. Frontend còn giới hạn dev lint dependencies từ P2-01; không dùng audit fix --force. S3/MinIO, AWS/Kubernetes/ETL chưa triển khai. Chưa kiểm browser visual/E2E trong hai task này.

Dừng sau P2-04, không Terraform/commit/push/delete data hoặc chạy SQL init. Task tiếp theo dự kiến P3-01 API danh mục và shop, chờ người dùng yêu cầu.

## P3-01 ngày 09/11/2026 — DONE

Chỉ thực hiện P3-01: API danh mục và gian hàng công khai. Tạo schemas/catalog.py, repositories/catalog.py, services/catalog.py, api/v1/routers/catalog.py và include vào router /api/v1. Không viết frontend/API sản phẩm/search/auth hoặc làm P3-02.

GET /api/v1/categories trả {items:CategoryTree[]} theo contract không phân trang; query một lần chỉ active categories, sắp category_name ASC + ID ASC. Service nối cây từ root nên nhánh có cha/tổ tiên inactive hoặc thiếu sẽ không bị đưa lên root. Cycle/orphan không nối về root không xuất public, không sửa dữ liệu. IDs BIGINT trả chuỗi chính xác. Cây rỗng trả items=[].

GET /api/v1/shops/{shop_slug} chỉ query shop APPROVED và chiếu field công khai shop_id/name/slug/description, không đọc/trả contact_email/owner ID/logo_key/password. Shop hidden/PENDING/REJECTED/LOCKED và missing cùng 404; slug >160 là 422. logo_url null vì S3/logo delivery chưa cấu hình, được ghi rõ contract; không tạo URL giả hoặc mở rộng storage task.

GET dependency mở transaction READ ONLY; timeout/OperationalError trả 503 chung, không lộ SQL/DSN/driver message. Response schemas/OpenAPI, request IDs/no-store theo nền tảng hiện có. Không thêm pagination endpoint không có trong contract (categories là toàn cây, shop là detail).

Kiểm thử:

| Kiểm tra | Kết quả |
| --- | --- |
| pytest -q -W error, bật tất cả integration | 47 passed, không warnings |
| Chạy không env integration | 38 passed, 9 skipped theo guard |
| Ruff check/format | PASS, 32 files |
| uv lock --check | PASS; dependencies/lock không thay đổi |
| Catalog tree | Active/inactive ancestors, orphan/cycle, empty tree, deterministic children, 15-level tree một SELECT |
| Shop public | APPROVED 200; PENDING/REJECTED/LOCKED/missing 404; projection không lộ email/storage key; slug injection không bypass; dài >160 422 |
| ID/error | BIGINT > JS safe integer vẫn chính xác; thiếu/DB lỗi 503 không lộ private secret/query |
| Docker backend build/update | PASS, chỉ recreate app backend bằng --no-deps |
| HTTP thật | categories 200, missing shop 404, OpenAPI routes đúng, DB readiness 200 |
| Bảo toàn | PostgreSQL ID/StartedAt/mounts và service/root env/volume/network không đổi |

6 tests catalog integration ghi fixture chỉ vào PostgreSQL 16 tạm riêng tên database marketplace_test, storage tmpfs, port ngẫu nhiên và credential ngẫu nhiên không in log. Không mount marketplace_postgres_data hoặc thêm vào marketplace_network/Compose. Schema test được tạo từ SQLAlchemy metadata, KHÔNG chạy SQL Downloads. Mỗi test transaction rollback; cuối lượt xóa đúng container test có tên/label riêng đã kiểm. Container test đã dọn, không dữ liệu test tồn tại trong DB nghiệp vụ. Ba tests audit trên database hiện hữu vẫn chỉ đọc metadata và readiness, không rows mutation. Không dùng rollback như lý do để INSERT vào DB thật (sequence không rollback).

Đã rebuild/start riêng backend để API hiện có tại localhost:8000; frontend/Compose/root .env/.env.example/SQL/schema/volume/network giữ nguyên. Cập nhật api-contract, backend README, task-plan/progress; không thay requirements hoặc business policy. Không commit/push/Terraform/deploy AWS. Backend đang healthy; frontend vẫn là skeleton đến task UI.

Điểm dừng: P3-01 DONE; task kế tiếp P3-02 API sản phẩm/tìm kiếm chưa thực hiện.

## DOC-01 ngày 09/11/2026 — DONE

Người dùng yêu cầu file quy tắc code AGENT.md, README hướng dẫn dự án và giải thích còn thiếu dữ liệu gì. Đây là task tài liệu bổ sung; 33 task chức năng giữ nguyên, không tự làm P3-02.

Tạo AGENT.md làm bộ quy tắc thống nhất và AGENTS.md dẫn tới bộ quy tắc đó. Nội dung giữ quy trình một task mặc định/nhiều task khi người dùng yêu cầu rõ, nguồn SQL/DOCX, ranh giới backend/frontend, bảo toàn DB/Compose/volume/network, secrets, API/ownership/transactions/stateless và kiểm thử thật. Không thêm yêu cầu xin quyền lại cho thao tác đã được người dùng cho phép.

Viết lại README root: trạng thái P3-01, cấu trúc/stack, Docker build/up --no-deps không recreate PostgreSQL, URLs/cổng, cấu hình/root .env, trạng thái từng chức năng và commands test. Sửa dòng số integration skip cũ trong backend README cho khớp hiện trạng 9.

Tạo docs/data-requirements.md: có thể tiếp tục code khi DB trống; tối thiểu cần category, owner/shop, product SKU/shop/category/giá, inventory và ảnh khi có storage. Gợi ý 3–5 category/2 shop/10–20 sản phẩm phục vụ demo, không áp đặt đây là yêu cầu để phát triển. Không phải điền sẵn cả 12 bảng; cart/address/orders do các luồng ứng dụng tạo sau. Nêu rõ auth/bootstrap/import/storage chưa hoàn tất, không hướng dẫn gọi API chưa tồn tại. Không tự tạo giá/tồn/hash hoặc nhập review thành user/shop thật; không yêu cầu mật khẩu/keys qua chat.

Dữ liệu đầu vào có thể chuẩn bị dưới dạng bảng hoặc JSON với mã tham chiếu, không cần tự gán DB identity. Nếu cần demo/import phải yêu cầu task riêng, xác định local/test/nguồn/ownership và dry-run trước ghi. Không tự seed vào DB hiện hữu hoặc dùng SQL Downloads có DROP.

Kiểm chứng: review tài liệu so với README/config và task-plan hiện tại; kiểm các liên kết Markdown nội bộ tồn tại, fence đóng đủ, AGENTS.md dẫn đúng AGENT.md, P3-02 vẫn TODO. Không chạy unit/build/Docker cho thay đổi chỉ tài liệu; không truy vấn hoặc đếm dữ liệu thật trong lượt này, không khẳng định DB đang trống dựa trên kiểm tra chưa làm. Không sửa code, env, Compose, schema, data, Terraform, commit/push hoặc deploy.

Dừng sau DOC-01; chờ người dùng yêu cầu P3-02 hoặc task chuẩn bị dữ liệu cụ thể.


## UI-01 ngày 09/11/2026 — DONE

Yêu cầu mới ưu tiên code giao diện trước tích hợp database, chỉ gồm 6 danh mục: ChamSocDaMat, TrangDiem, DungCuPhuKienLamDep, VatTuYTe, DungCuMassageTriLieu, NuocHoa. Task bổ sung UI-01 độc lập; không tự thực hiện P3-02 hoặc đánh dấu hoàn thành API/auth/cart/dashboard.

Đã thay skeleton bằng HealthBeauty: header/tìm kiếm, hero vector tự thiết kế, 6 ô danh mục, sản phẩm gợi ý, bộ sưu tập và footer. Trang /san-pham có search không dấu, lọc danh mục qua URL, lọc khoảng giá, sắp xếp giá/tên, số kết quả và empty/reset. Trang /san-pham/[slug] có breadcrumb, thông tin, quy cách, giá VND, sản phẩm cùng danh mục và notFound cho slug sai. Tái sử dụng ProductArt/ProductCard/CatalogBrowser và nguồn preview-catalog.ts. Không thêm dependency vào frontend/package.json hoặc package-lock.json.

12 mẫu minh họa (2/danh mục) tồn tại chỉ trong source preview, không import/seed DB. Banner/footer và trang chi tiết ghi rõ chưa mở bán, giá/nhãn hiệu/bao bì mẫu; không tạo fake rating, số bán, tồn kho, login, giỏ hàng hoặc checkout. Dữ liệu này không được dùng như catalog production. Taxonomy key/slug không khẳng định ID 1–6 trong DB. Backend không thay đổi; không tạo endpoint mock hoặc frontend fallback khi API lỗi. Sau này chuyển nguồn API theo task tích hợp được yêu cầu.

Kiểm chứng cuối:

| Kiểm tra | Kết quả |
| --- | --- |
| npm run lint | PASS, không warnings |
| npm run typecheck | PASS |
| npm run build | PASS, homepage và 12 trang chi tiết prerender; catalog dynamic searchParams |
| Docker compose build frontend | PASS |
| Update frontend --no-deps/health | PASS, http://localhost:3001 |
| Chrome headless, desktop 1440px | PASS: 6 danh mục, 12 mẫu, search nuoc hoa trả 2, sort giá tăng, filter <=100.000 trả 3, đổi danh mục, empty/reset và chi tiết |
| Routes | PASS: 6 danh mục mỗi trang 2 mẫu; slug sản phẩm sai HTTP 404 |
| Responsive/keyboard | PASS: homepage/catalog/detail 390px không tràn ngang, skip link nhận Tab focus |
| Browser console/network | PASS: không pageerror, không request /api/ hoặc :8000 |
| Visual QA | Đã xem screenshot fullpage desktop/mobile của homepage; ảnh chụp chi tiết cũng được lưu |
| Bảo toàn | PASS: so baseline trước/sau, PostgreSQL ID/StartedAt/mounts/service config, named volume/network và hash .env không đổi |

Tool QA Playwright 1.56.1 và Prettier 3.6.2 chỉ cài/chạy ở cache hoặc scratch ngoài repository; không thay dependency ứng dụng. Script, baseline không chứa plaintext secrets và screenshots nằm tại D:/HealthBeauty/.ui-01-tools. Có lỗi encoding khi ghi source bằng PowerShell pipeline trong lượt đầu, đã sửa UTF-8 và chạy lại lint/typecheck/build thành công trước khi build image cuối. Không dùng kết quả typecheck lỗi ban đầu làm bằng chứng PASS.

Giới hạn: browser smoke không thay thế E2E nghiệp vụ; chưa thử giao dịch/auth/API vì ngoài phạm vi. Không truy vấn hoặc ghi DB, không sửa .env/Compose/SQL/schema/Terraform, không AWS/commit/push. README và data-requirements được cập nhật theo frontend-first. Dừng sau UI-01 để người dùng kiểm tra giao diện.


## P3-02 ngày 09/11/2026 — DONE

Người dùng yêu cầu tiếp tục website, mỗi lượt đúng một task, giải thích code/kết nối/lệnh/test/cách kiểm tra. Chọn task kế tiếp chưa xong trong kế hoạch là P3-02; không triển khai đồng thời auth/cart/seller/admin hoặc thay UI. Giao diện vẫn là preview với đúng 6 danh mục; việc đổi thiết kế theo trải nghiệm Shopee và tích hợp API nằm trong P3-03–05, chưa làm lượt này.

Tạo schemas/products.py (query validation và public response), repositories/products.py (SQLAlchemy queries), services/products.py (response mapping), api/v1/routers/products.py (2 public GET) và include router. GET /products hỗ trợ q literal ILIKE, category_id kèm nhánh con, shop_id, page/page_size và 3 sort theo contract. Recursive CTE bắt đầu từ root active, chỉ đi qua node active; loại danh mục có tổ tiên inactive và cycle không nối về root. SELECT chỉ trả sản phẩm active và shop APPROVED. Sort allowlist có ID DESC tie-breaker; giá Decimal và BIGINT không mất chính xác. Không nội suy chuỗi SQL hoặc tạo index/schema mới.

GET /products/{product_id} dùng cùng predicate visibility, 404 chung cho hidden/missing; inventory thiếu hoặc 0 là hết hàng, vẫn xem được. READ ONLY dependency dùng lại từ catalog; không commit/DDL/seed. List 2 SELECT (count/page); detail tối đa 2 (product/image metadata), không N+1. S3 chưa được cấu hình: primary_image_url/images[].url null, vẫn trả metadata ảnh theo primary/sort_order/ID. Không đọc hoặc trả storage key/owner/email/hash. Làm rõ nullable image URL trong API contract, không thay schema hoặc tự thêm storage task.

Kết nối: frontend hiện chưa gọi API; sau này Next server sẽ gọi backend qua INTERNAL_API_URL=http://backend:8000. Backend router → service → repository → request session → PostgreSQL hostname postgres:5432/schema marketplace. Browser chỉ dùng URL localhost public, không gọi hostname Docker. Dữ liệu mẫu UI không được fallback vào API production. API search hiện chưa tìm không dấu như local preview; giữ contract ILIKE, không tự thêm extension/unaccent.

Kiểm thử cuối:

| Kiểm tra | Kết quả |
| --- | --- |
| Ruff check/format | PASS, 36 files |
| uv lock --check | PASS, không thay dependencies/lock |
| pytest -q -W error, không integration env | 56 passed, 12 skipped theo guard |
| pytest đầy đủ integration | 68 passed, không warnings |
| Validation | Query bounds, sort allowlist, unknown field, BIGINT/path invalid; unit test isolate service để không bị missing DB dependency che validation |
| PostgreSQL riêng | Visibility product/shop/category ancestor/cycle, nhánh con, literal %/_/slash, injection-like search, shop filter, sort tie-break, pagination hết trang |
| Response/query count | Decimal string, BIGINT > JS safe, thiếu inventory, metadata ảnh không key/PII; list/detail 2 SELECT |
| Docker backend | Build/update --no-deps, health PASS; không rebuild frontend |
| HTTP thật | /products?page_size=2: 200 total=0/items=[]; page_size=101:422; missing max BIGINT product:404; OpenAPI có cả 2 endpoint |
| Bảo toàn | PostgreSQL ID/start/mount/service config, named volume/network, root .env hash không đổi trước/sau update |

Fixtures chỉ ghi trong postgres:16 tmpfs marketplace_test riêng với credential/port ngẫu nhiên; dùng lại helper test isolation ở D:/HealthBeauty/.p3-01/run-integration.py, xóa đúng container test sau chạy. 3 audit tests trên DB hiện hữu READ ONLY. Không seed/ghi DB nghiệp vụ; empty API là kết quả thật của lần kiểm tra, không suy ra toàn bộ 12 bảng đều trống. Lượt test đầu phát hiện các tests validation bị missing DB dependency trả 503 trước validation; đã sửa cách isolate service trong unit tests, chạy lại toàn bộ thành công. Ruff format sửa line length trước kết quả PASS cuối.

Kiểm tra thủ công: mở http://localhost:8000/docs → Public products → Try it out. /products với page_size=24/sort=price_asc; category_id lấy từ /categories thật; product_id lấy từ items khi có hàng. /products/{ID} không public trả 404; page_size=101 trả 422. Lệnh build/start và test đầy đủ trong backend/README.md. Không cần sửa/khởi tạo DB để thử API; thiếu dữ liệu thì list rỗng đúng thiết kế.

Đã cập nhật README root/backend, API contract, task-plan và progress. Không sửa frontend/.env/Compose/SQL/schema/Terraform, không AWS/commit/push. Chưa kiểm chứng API→frontend hoặc nghiệp vụ đăng nhập/checkout vì ngoài phạm vi task này. Dừng sau P3-02, không tự bắt đầu P3-03.


## P3-03 ngày 09/11/2026 — DONE

Chỉ thực hiện P3-03 được người dùng chỉ định: hoàn thiện giao diện chung và homepage lấy API thật. Giữ màu xanh/kem HealthBeauty riêng, tổ chức lại header với search/account/cart, thanh 6 danh mục, hero + hai banner cảm hứng, dải thông tin, danh mục và product grid; footer thống nhất. Account/cart là native disclosure có nội dung giải thích chức năng chưa mở, không fake số lượng/auth hoặc link đến route chưa có. Banner dùng vector trang trí không phụ thuộc catalog mẫu/S3 và không bịa khuyến mãi.

Tạo src/lib/catalog-api.ts: fetch chỉ ở Server Component, origin từ INTERNAL_API_URL có validation http/https không credentials/path/query, no-store, redirect:error và AbortSignal timeout 5s; validate categories/product public schema và chiếu field cần thiết trước khi gửi Client Component. Decimal price và BIGINT giữ chuỗi. Lỗi HTTP/JSON/timeout/schema không được đổi thành catalog rỗng hoặc fallback mock, cũng không hiển thị upstream exception/body. Không thêm dependency hoặc đổi package-lock; package.json thêm npm run test.

src/lib/categories.ts chứa đúng 6 taxonomy key, label tiếng Việt, slug/icon/color. HomeCatalog đọc active tree từ API để tìm tên/slug tương ứng sau normalize; category_id luôn từ DB, không giả định 1–6 hoặc seed. Danh mục chưa match hiển thị “Sắp cập nhật”. Homepage chỉ chọn sản phẩm từ các nhóm được yêu cầu; 1 categories request rồi tối đa 6 products requests song song. Interleave/deduplicate, tối đa 12 thẻ. Đây là preview section homepage, chưa catalog phân trang. Search /?q=... và /?danh-muc=... dùng API tìm tên ILIKE theo contract (chưa tìm không dấu). Không tự sửa API/schema hoặc thêm price filter ngoài contract.

HomeCatalog async trong Suspense có skeleton; failure component có retry router.refresh dùng useTransition; success rỗng có empty state thật. LiveProductCard dùng summary thật (shop/name/price/in_stock), thông tin nhanh có thể mở bằng bàn phím. URL ảnh null hoặc tải lỗi dùng placeholder; không lấy mock bao bì. Giá VND dùng BigInt phần nguyên/Decimal string. S3 URL hiện null theo backend P3-02, nên chưa có ảnh thật; không tích hợp S3 task này.

Ranh giới: homepage và header/footer không import preview-catalog và không dẫn product thật sang detail mẫu. /san-pham routes giữ UI-01, bổ sung layout banner “Bản xem trước UI-01” và link về homepage API thật để không đánh tráo mẫu thành dữ liệu production. Không triển khai list/detail/shop API integration P3-04/05 hoặc auth/cart/seller/admin. Chưa có link detail thật; thẻ mở thông tin nhanh từ summary đã nhận.

Luồng kết nối: Browser yêu cầu /?q=... → Next server HomeCatalog → INTERNAL_API_URL=http://backend:8000/api/v1/categories và /products → FastAPI service/repository → SQLAlchemy READ ONLY → postgres:5432, schema marketplace. Không browser fetch hostname Docker, không credentials ở NEXT_PUBLIC hoặc client props, chưa cần proxy/CORS. Trên Windows dev trực tiếp đặt INTERNAL_API_URL=http://127.0.0.1:8000 qua terminal, chạy cổng 3002 để không trùng Docker 3001.

Kết quả cuối:

| Kiểm tra | Kết quả |
| --- | --- |
| npm run test | 7 passed: taxonomy/VND, env validation, empty-vs-error, HTTP/JSON/timeout, actual ID/query encoding/no-store, unsafe image URLs, product schema |
| npm run lint | PASS, không warnings |
| npm run typecheck | PASS |
| npm run build | PASS; homepage dynamic, build không cần env/API; preview routes giữ nguyên |
| Browser với fixture HTTP API riêng | PASS: 6 nhóm ID 101–106 (không phải giả định 1–6), 6 products, giá/stock, search/filter, không mock leakage hoặc private extra field |
| Failure/UX browser | PASS: categories503, products503, payload sai, empty, retry refresh, suspense loading khi delay, broken image placeholder |
| Responsive/keyboard | PASS: 390/768/1440px không document overflow; disclosure mobile không tràn; Tab/Enter skip link tới main |
| Network/JS | PASS: không pageerror, không request /api/v1 từ browser, server gọi API thay browser |
| Visual | Đã xem screenshots desktop/mobile và empty state fixture; ảnh real homepage cũng được lưu |
| Docker frontend | Build + up --no-deps --wait PASS, :3001 healthy |
| API thật → DB | Browser :3001 HTTP200, 6 taxonomy tiles, 0 product cards, empty state thật, không alert hoặc mẫu BOTANIC, không JS errors/mobile overflow |
| Bảo toàn | PostgreSQL ID/StartedAt/mounts/config/volumes/networks và hash .env không đổi, so baseline trước/sau |

Fixture success/error browser chạy HTTP server và Next production process trên cổng ngẫu nhiên ngoài Compose, dùng Playwright/Chrome trong scratch D:/HealthBeauty/.p3-03-tools. Mọi process fixture đã dừng. Không trỏ app Docker vào fixture, không tạo schema hoặc ghi DB. Script và screenshots nằm trong scratch; 7 contract tests nằm trong frontend/tests/catalog-api.test.mjs và chạy bằng npm run test. Không chạy lại backend tests vì không sửa backend. Đây chưa phải E2E nghiệp vụ mua hàng.

Lượt typecheck đầu bắt lỗi BigInt literal không tương thích target hiện có, đã chuyển sang BigInt constructor và chạy lại toàn bộ test/lint/typecheck/build PASS. Browser test đầu vướng locator alert của Next route announcer, đã thu hẹp selector vào catalog alert rồi chạy lại PASS. Verifier raw mounts ban đầu báo khác biệt; đối chiếu lại baseline theo Destination và các field khác không thay đổi, đã chuẩn hóa so sánh thứ tự mounts trước khi xác nhận PASS. Không thay baseline để bỏ qua khác biệt cấu hình.

Đã cập nhật frontend README với lệnh VS Code/Docker/test, code fetch quan trọng, đường dẫn và hướng dẫn kiểm tra; README root, data-requirements, task-plan/progress đồng bộ. Không sửa backend/Compose/root .env/SQL/schema/Terraform, không deploy AWS/commit/push. Chỉ recreate app frontend. Hạn chế hiện tại: dữ liệu public chưa có nên người dùng thấy empty state; ảnh thật, list/detail integration và auth/cart còn các task sau. Dừng sau P3-03, chưa bắt đầu P3-04.


## UI-02 ngày 09/11/2026 — DONE

Theo yêu cầu trực tiếp: tạo lại header như bố cục ảnh, có Kênh người bán/Thông báo/Hỗ trợ, màu khác và sửa font. Chỉ sửa header + typography dùng chung; không thực hiện task P3-04 hoặc nghiệp vụ Seller/auth/notification/cart.

Header mới 3 tầng: utility bar tím mận (#503b63) với seller/bell/support; main row logo túi lá tự vẽ + HealthBeauty hai màu tím/cam đất, search rộng, account/cart; thanh danh mục nền tím nhạt với đúng 6 nhóm. Dùng SVG icon nhất quán và HeaderMenu tái sử dụng native details/summary, hoạt động chuột/bàn phím. Seller/notification/account/cart mở thông tin chức năng chưa triển khai; Hỗ trợ có hướng dẫn tìm sản phẩm và link danh mục/giới thiệu thật, không thêm email/hotline giả hoặc counter giả. Search vẫn GET /?q=... và backend API như P3-03, không đổi luồng dữ liệu.

Sửa font: nội dung trước trộn system sans với serif và tiêu đề có dấu trông lệch trên Windows. Thêm NotoSans variable từ Google Fonts repository, kèm OFL.txt; next/font/local khai báo weight 100..900, display swap và biến --font-noto-sans trên html. CSS theme sans/serif và section heading dùng cùng font Việt; ký hiệu trang trí không chứa chữ Việt vẫn có serif fallback. Không sửa text bằng cách bỏ dấu. Font được đóng gói trong static media của app, không phụ thuộc tải Google Fonts ở runtime hoặc build. Không đổi dependencies/lock.

Kiểm chứng:

| Kiểm tra | Kết quả |
| --- | --- |
| npm run lint | PASS |
| npm run typecheck | PASS |
| npm run build | PASS; Docker build cuối cũng PASS sau chỉnh CSS popup |
| Chrome 320/390/768/1440 | PASS, không overflow document |
| 5 disclosure menus | PASS: mở/đóng và bounding box nằm trong viewport cả 4 kích thước |
| Noto font | PASS: document.fonts báo loaded, computed h1 dùng Noto, font response HTTP200 |
| Search/keyboard | PASS: submit serum → /?q=serum → empty response thật; Tab skip link, Enter mở seller menu |
| JS errors | Không pageerror |
| Visual QA | Đã xem screenshot desktop1440/mobile390: header/typography có dấu rõ, không lỗi dấu serif trước đó |
| Docker/preservation | Frontend :3001 healthy; PostgreSQL ID/start/mounts/config, volumes/network và root .env hash không đổi |

Browser test đầu phát hiện popup Thông báo tràn 0.55px ở viewport320; đã chỉnh offset riêng mobile từ -90px thành -65px, rebuild image rồi chạy lại toàn bộ browser checks PASS. Script/screenshots tại D:/HealthBeauty/.ui-02-tools, không dependency hardcode trong source app. Không viết unit tests mirror markup/CSS; dùng browser QA thực tế cho thay đổi UI. Không chạy lại backend suite vì không sửa backend.

Code quan trọng ở frontend/src/components/layout/site-header.tsx (HeaderIcon/HeaderMenu/SiteHeader); frontend/src/app/layout.tsx (next/font/local); frontend/src/app/globals.css (typography/header/mobile). Hướng dẫn chạy vẫn docker compose build frontend rồi docker compose up -d --no-deps --wait frontend, hoặc npm dev theo frontend README. Mở localhost:3001 và Ctrl+F5 để xem font/header mới; bấm seller/bell/support để kiểm tra popup. Đây vẫn chưa phải hệ thống thông báo hoặc Seller Dashboard.

Đã cập nhật frontend README/task-plan/progress. Không sửa backend/API/database/schema/root .env/Compose/Terraform, không commit/push hoặc AWS. Chỉ cập nhật container frontend. Dừng sau UI-02.


## UI-03 ngày 09/11/2026 — DONE

Theo yêu cầu đổi màu trẻ trung/năng động/hiện đại, có thanh Đăng nhập/Đăng ký ở trang guest và thêm Flash Sale, Sản phẩm bán chạy. Đây là một task UI bổ sung, không tự làm task auth/P3-04 hoặc thay schema để đáp ứng promotion ngoài đặc tả ban đầu.

Thay palette toàn site sang xanh cobalt #244ec9, cam san hô #ef6b43, nền #f6f8ff; header/logo/search/navigation và text-brand đồng bộ. Hero nền gradient xanh sáng, banner phụ peach/sky, font Noto Sans tự host giữ nguyên. Thêm guest-account-bar dưới header main, có Đăng nhập/Đăng ký là native disclosure: thông báo xác thực chưa mở, không thu thập password hoặc báo thành công giả; links tiếp tục về homepage/danh mục thật. Public browsing/search không yêu cầu tài khoản.

Tạo ShoppingHighlights: section #flash-sale có icon tia chớp, gradient cam/kem, empty state và CTA #san-pham; #ban-chay có icon cúp/star, nhãn và empty state, CTA thật. Homepage render component này bên dưới Suspense HomeCatalog. Không lấy catalog newest làm best sellers, không thêm sample product/giảm giá/%/countdown/sales count. API/schema hiện chưa định nghĩa promotion hoặc thời điểm/chỉ số xếp hạng, do đó chỉ hoàn thành bố cục chờ dữ liệu; cần task nghiệp vụ/API riêng nếu người dùng yêu cầu hoạt động thật. Không đọc/ghi đơn hàng hoặc inventory để tự suy ra xếp hạng.

Kiểm thử cuối: npm run lint PASS; npm run typecheck PASS; npm run build PASS; Docker frontend build/up --no-deps --wait healthy. Chrome thực tế trên localhost:3001 kiểm tra 320/390/768/1440px không document overflow, 7 menu có bounding box trong viewport (seller/bell/support/account/cart/login/register), font Noto loaded/HTTP200, 2 section headings hiện, search serum → API empty state, Tab skip và Enter seller menu, không JS pageerror. Script D:/HealthBeauty/.ui-03-tools/browser-check.cjs kế thừa script UI-02 nên log cũ ghi “five” nhưng vòng lặp thực tế đã mở/đóng 7 labels. Đã xem screenshots fullpage desktop1440/mobile390 để xác nhận palette/guest bar/Flash Sale/best sellers responsive.

Bảo toàn PASS: baseline PostgreSQL ID/StartedAt/mounts/config/volume/network và root .env hash không đổi trước/sau update. Không sửa Compose/backend/schema/data/secrets/Terraform, không AWS hoặc commit/push. API connection Next server → backend → postgres không đổi. Không chạy lại backend/unit contract suite vì thay đổi UI không đổi logic data, không tạo test mirror CSS; browser QA kiểm tra hành vi thật.

Code chính: frontend/src/components/layout/site-header.tsx (guest-account-bar); frontend/src/app/globals.css (palette/highlights/mobile); frontend/src/components/home/shopping-highlights.tsx (2 sections); frontend/src/app/page.tsx (composition). Cập nhật frontend README/task-plan/progress. Kiểm tra bằng http://localhost:3001, Ctrl+F5, mở Đăng nhập/Đăng ký và cuộn xuống Flash Sale/bán chạy. Lệnh từ root: docker compose build frontend; docker compose up -d --no-deps --wait frontend. Những section này chưa phải engine giảm giá hoặc xếp hạng production; auth vẫn task P4. Dừng sau UI-03.


## UI-04 ngày 09/11/2026 — IN_PROGRESS, chờ thông tin thương hiệu/ảnh

Yêu cầu: bỏ “6 danh mục chăm sóc & làm đẹp / Khám phá sản phẩm không cần đăng nhập / Một khoảng riêng dành cho bạn”, header xanh biển nhạt, cập nhật icon danh mục, ảnh sản phẩm, logo và tên web. Đã hỏi tên cụ thể + nguồn ảnh. Người dùng trả lời tên khác (không chọn Lumi Beauty/BloomCare/Mira Beauty), sẽ cung cấp đường dẫn ảnh thật. Đã hỏi tiếp tên chính xác và đường dẫn ảnh kèm tên/mã sản phẩm; chưa có đầu vào nên không tự suy diễn thương hiệu hoặc gán ảnh sai. Các câu hỏi vẫn pending, không phải yêu cầu quyền thay đổi lại.

Phần đã làm và review được tại localhost:3001: xóa hẳn 3 câu + container; header utility #dff1ff, text #245b88, search #4e9dd8 và category bar #f0f8ff. Thay ký tự category bằng 6 SVG đồng nhất (skincare/makeup/brush/medical/massage/perfume), taxonomy và ID API giữ nguyên. Đổi biểu tượng website thành hoa/giọt sáng xanh trời, dùng public/icon.svg cho BrandLogo ở header/footer và favicon version2. Không xóa 6 danh mục thật: chỉ bỏ dải giới thiệu 3 câu theo yêu cầu.

Tạo lib/site-brand.ts để đồng bộ name/tagline trong BrandLogo, header menus, footer, metadata/title và hero. Hiện vẫn tên HealthBeauty vì chưa có tên thay được người dùng chỉ định; sẵn sàng đổi một chỗ khi nhận tên. AWS project/repository name không thay đổi. Card thiếu ảnh có placeholder khung ảnh SVG rõ nhãn “Chưa có hình ảnh”, không thay ảnh thật bằng bao bì mẫu. Không tạo bitmap bằng imagegen hoặc tự tải ảnh stock vì người dùng đã chọn cung cấp ảnh thật. Chưa copy/upload ảnh, chưa sửa DB/image_key/API/S3.

Kiểm chứng phần đã sửa: lint PASS, typecheck PASS, build PASS, Docker frontend build/up --no-deps healthy. Chrome 320/390/768/1440 PASS: không overflow; 7 menu bounds trong viewport; 3 phrase exact không còn; 6 category-art SVG; 2 brand-logo-image; computed utility background rgb(223,241,255); font Noto loaded và HTTP200; search/API/keyboard không lỗi JS. Đã xem screenshot desktop mới, lưu desktop/mobile và script ở D:/HealthBeauty/.ui-04-tools. Không chạy backend tests vì không sửa backend.

Bảo toàn baseline trước/sau PASS: PostgreSQL ID/start/mounts/config, root .env hash, named volume/network giữ nguyên. Không sửa Compose/backend/schema/Terraform, không commit/push/AWS; chỉ recreate frontend. README/task-plan/progress đã cập nhật trạng thái trung thực. Task chưa DONE: cần tên web cụ thể và ảnh thật/mapping sản phẩm để tiếp tục đúng phạm vi.

## UI-04 — Cập nhật tên coco, 09/11/2026

Người dùng chọn tên website “coco”. Đổi siteBrand.name thành coco; BrandLogo, header/footer, các menu seller/auth/support, hero và metadata tự đồng bộ từ cấu hình dùng chung. Giữ đúng cách viết thường theo lựa chọn, không đổi tên dự án AWS/repository hoặc dữ liệu DB. Không còn HealthBeauty trong source UI runtime ngoài tên lịch sử ở tài liệu/dataset.

Kiểm thử: lint/typecheck/build PASS; Docker frontend build/up --no-deps healthy; Chrome xác nhận 2 wordmark coco, title homepage “coco | Chăm chút từng ngày”, title preview “Bộ sưu tập | coco”, menu “Đăng nhập coco”, favicon version2, không text HealthBeauty trong body, không JS errors hoặc overflow320. PostgreSQL ID/start/mounts/config/root env/volume/network vẫn giống baseline. Script: D:/HealthBeauty/.ui-04-tools/brand-check.cjs.

Chỉ cập nhật tên trong UI-04 hiện tại; vẫn IN_PROGRESS do ảnh thật/mapping chưa được cung cấp. Chưa thay ảnh mẫu/ảnh stock vào catalog. Mở http://localhost:3001 và Ctrl+F5 để xem coco. Không commit/push/Terraform/AWS/backend/schema/data.


## UI-05 ngày 09/11/2026 — DONE

Yêu cầu trực tiếp mới: bỏ câu “Khám phá tự do, làm đẹp theo cách bạn”, đưa Đăng nhập/Đăng ký lên header, bỏ thanh danh mục ngang dưới auth và mục Tài khoản, làm banner theo ảnh đính kèm. Triển khai riêng UI-05, không tự thực hiện P3-04/auth hoặc task ảnh sản phẩm còn thiếu đầu vào.

Header hiện hai hàng: utility với Kênh người bán, Thông báo, Hỗ trợ, Đăng nhập, Đăng ký; main với logo coco/search/giỏ hàng. Bỏ toàn bộ guest-account-bar và header-category-bar trong markup, không chỉ ẩn CSS; không render summary Tài khoản. Tái sử dụng HeaderMenu với icon optional, details name group để một menu mở mỗi lần. Popup mobile fixed trong viewport, desktop vẫn neo đúng menu. Đăng nhập/đăng ký vẫn thông tin chức năng chưa mở, không giả auth. Category tiles và lọc thật trên homepage giữ nguyên.

Thay hero cũ bằng components/home/campaign-banners.tsx: grid 2fr/1fr, banner chính trái và stack hai ô phải, gap8px, chiều cao desktop cân nhau; mobile banner chính ở trên, hai ô nhỏ bên dưới. Hai ảnh gốc photorealistic editorial tạo bằng built-in image_gen theo skill imagegen, copy vào public/images/coco-skincare-campaign.png và coco-fragrance-campaign.png. Đã xem cả hai ảnh để kiểm tra unbranded/no text/no prices, chỉ dùng cho artwork banner, không coi là ảnh sản phẩm thật. Chữ coco/campaign title/CTA render bằng HTML, không text raster dễ lỗi font. Ảnh do Next Image phục vụ local, ảnh chính priority. Nhãn hình minh họa bộ sưu tập; không bịa Shopee Mall, freeship, voucher, % giảm hoặc countdown của ảnh tham khảo. Các CTA link category-filter API thật.

Prompt đầy đủ và đường dẫn asset được ghi trong docs/banner-assets.md. Original files còn giữ tại C:/Users/ADMIN/.codex/generated_images/01a1be6a-3827-7e42-aadd-933c728c1b10. Không upload AWS/S3, không gán image_key/DB hoặc thay ảnh catalog bằng AI. UI-04 phần ảnh thật vẫn pending nguồn người dùng.

Kiểm chứng cuối: npm run lint PASS; npm run typecheck PASS; npm run build PASS. Docker frontend build cuối cũng PASS sau chỉnh crop mobile. Browser Chrome localhost:3001 ở 320/390/768/1440 xác nhận không document overflow; không guest/category header bar, không summary Tài khoản hoặc câu bị bỏ; login/register đều thuộc utility header; 1 main/2 side banner, ảnh complete và naturalWidth>0; desktop ratio2:1, stack dọc và chiều cao main/side bằng nhau; 6 popup menu bounds trong viewport; banner nước hoa lọc đúng URL/category, search serum đúng URL/API; Tab skip link/Enter login; không pageerror. Đã xem screenshot fullpage desktop/mobile. Visual QA ban đầu thấy ảnh ô nhỏ bị crop khuất, đã đổi object-position78% mobile, rebuild và chạy lại browser checks PASS; screenshot mobile cuối đã xem lại. Copy fragrance lần đầu sai relative path, đã copy đúng vào public/images trước build/runtime QA; không asset thiếu trong bản cuối.

Docker chỉ recreate frontend bằng --no-deps; health PASS. Baseline PostgreSQL ID/StartedAt/mount/config, named volume/network, hash .env không đổi. Không sửa backend/Compose/schema/data/Terraform hoặc commit/push/AWS. Tests API/backend không chạy lại vì không đổi logic dữ liệu. Script/screenshots tại D:/HealthBeauty/.ui-05-tools. Cập nhật frontend README/task-plan/progress và docs/banner-assets. Mở localhost:3001, Ctrl+F5; lệnh build/update frontend giữ nguyên. Dừng sau UI-05.


## P3-04 ngày 09/11/2026 — DONE

Người dùng yêu cầu “LÀM TIẾP”; tiếp tục đúng task kế tiếp P3-04, không triển khai nhiều task. Chuyển /san-pham từ mock UI-01 sang catalog server dùng API thật. Giữ header/logo/banner theo các điều chỉnh UI-05, không phục hồi nav ngang/account hoặc câu giới thiệu đã bỏ.

Tạo lib/catalog-query.ts: parse q(max200), danh-muc slug, sort allowlist, page 1..2147483647 và page_size UI12/24/48; lặp query/kiểu sai/sort sai/overflow hiển thị lỗi thay vì âm thầm bỏ filter. catalogHref encode query, reset page1 khi đổi q/category/sort/size, giữ bộ lọc khi pagination. paginationPages chỉ tạo tối đa5 số trang, không tạo array theo total lớn. Unit tests round-trip/boundaries/URL injection-like text và past-end. Các tham số không thuộc nhóm UI hiện tại không được gửi thành SQL/filter tùy ý.

catalog-api.ts thêm getProductPage({categoryId?,query,page,pageSize,sort}); wrapper getProducts cũ giữ 12 items cho homepage. Fetch no-store, timeout5s, JSON/HTTP/schema validation, response projection không thay. Validate input trước network và echo page/page_size khi có, total/offset hợp lý. Decimal/ID vẫn chuỗi. Không thêm dependency/lock hoặc backend query/schema/index. matchBeautyCategories dùng chung homepage/list: flatten active tree, ưu tiên slug unique sau đó tên unique; ambiguity không tự chọn ID. Sidebar đúng 6 nhóm hiển thị. Trang tất cả dùng catalog public API, khi lọc nhóm thì backend bao gồm descendants; không có dữ liệu mock trong client.

CatalogBrowser chuyển từ Client Component lọc mẫu sang async Server Component: sidebar danh mục, GET form tìm tên/sort/page-size có nút Áp dụng và reset, total/counter từ API, grid LiveProductCard, pagination links giữ URL, unavailable category state, invalid URL state, empty/past-end/first-page action và sanitized failure/retry. form không có page nên submit về trang1; Back/Forward/reload phục hồi từ URL, không state local sai lệch. Chưa có price-range filter/sort tên vì backend contract không hỗ trợ, đã bỏ filter giá mẫu. Chưa nối product-detail/shop links vào preview giả: card live chỉ có thông tin nhanh, detail API integration thuộc P3-05.

Root layout preview /san-pham/layout.tsx được bỏ; chuyển nhãn riêng sang /san-pham/[slug]/layout.tsx. List không còn nhãn/mẫu; detail cũ vẫn có banner “Bản xem trước chi tiết UI-01” và link quay list thật. Header search action=/san-pham; banner/category/footer/Flash Sale/bestseller CTA chuyển vào list thật. Legacy root q/danh-muc vẫn hoạt động trên homepage, không phá bookmark. HomeCatalog chia sẻ mapping mới, giữ dữ liệu API/skeleton hiện có.

Kiểm chứng cuối:

| Kiểm tra | Kết quả |
| --- | --- |
| npm run test | 14 passed, không skip |
| npm run lint | PASS |
| npm run typecheck | PASS |
| npm run build | PASS; /san-pham dynamic, homepage dynamic; preview detail static như cũ |
| Browser fixture API | PASS với 50 public records, ID danh mục > JS safe; 24/12 items/page, price sort, pagination/reload/back-forward, category/search reset page và giữ URL |
| Failure/empty | PASS unknown category, empty query result, past-end/first page, invalid/duplicate URL, categories503/products503/malformed payload, retry refresh, delayed suspense loading |
| Entry points/preview | PASS header search/banner nước hoa → /san-pham thật, list không BOTANIC/preview; detail preview vẫn có nhãn riêng |
| Responsive/console | PASS 390/768/1440 không document overflow, không pageerror hoặc browser request /api/v1; đã xem fullpage desktop/mobile screenshots |
| Docker frontend | Build/update --no-deps healthy PASS |
| Real API/DB | Browser /san-pham HTTP200 total0/items0, empty thật, search serum tới URL danh sách và không alert/preview/mock; mobile390 không overflow |
| Preservation | PostgreSQL ID/start/mounts/config/root .env hash/volume/network giữ nguyên |

Fixture HTTP API + Next production process trên cổng ngẫu nhiên chỉ phục vụ QA, đã dừng trong finally. Không seed hoặc tạo schema/fixtures vào DB thật; không đổi INTERNAL_API_URL của Docker để test với mẫu. Scripts/screenshots tại D:/HealthBeauty/.p3-04-tools. 14 tests tracked trong frontend/tests, chạy bằng Node24/test và TypeScript dev dependency sẵn có. Không chạy lại backend suite vì không sửa backend. UI-04 ảnh thật vẫn chờ nguồn, không lấy ảnh AI banner thay ảnh catalog.

Code quan trọng: frontend/src/lib/catalog-query.ts (URL state/reset), catalog-api.ts (getProductPage), categories.ts (identity mapping), components/catalog-browser.tsx (server list/filter/pagination), app/san-pham/page.tsx (Suspense route). Frontend/API/database: Browser GET → Next parse/filter/mapping → FastAPI GET /api/v1/products → SQLAlchemy READ ONLY → postgres:5432 marketplace. Không browser gọi hostname nội bộ hoặc đọc secrets.

Đã cập nhật README root/frontend, api-contract, data-requirements, task-plan/progress. Lệnh từ root: docker compose build frontend; docker compose up -d --no-deps --wait frontend. Kiểm tra /san-pham?q=serum&sort=price_asc&page_size=12, hoặc form/sidebar; Swagger http://localhost:8000/docs để so API thật. Khi catalog public rỗng thì không thấy pagination/ảnh là đúng, không tạo giả. Không sửa backend/Compose/root env/schema/data/Terraform, không AWS/commit/push. Dừng sau P3-04; P3-05 chưa bắt đầu.


## UI-06 ngày 09/11/2026 — DONE

Người dùng yêu cầu thanh dọc bộ lọc tìm kiếm có đơn vị vận chuyển/dịch vụ/khuyến mãi, thanh ngang sort Phổ biến/Mới nhất/Bán chạy. Phạm vi UI bổ sung, không thay schema hoặc tự định nghĩa metrics xếp hạng/promotions/carrier contract.

Sidebar có h2 Bộ lọc tìm kiếm với icon funnel, nhóm danh mục, search tên, page-size và form/reset cũ; thêm CatalogExtraFilters với 2 fieldsets Đơn vị vận chuyển và Dịch vụ & khuyến mãi. Tên carrier GHN/GHTK/Viettel Post chỉ dự kiến giao diện, disabled + nhãn Chưa kết nối + mô tả rõ chưa có đơn vị được kết nối; không khẳng định hợp tác/tích hợp. Services/khuyến mãi cũng disabled Sắp có, không fake vouchers/giảm giá hoặc gửi tham số API không hỗ trợ. 6 checkbox không có name và nằm ngoài GET form, không tác động kết quả giả.

CatalogSortBar client phía trên product grid có label Sắp xếp theo, Phổ biến/Mới nhất/Bán chạy và price dropdown. Phổ biến/Bán chạy disabled aria-describedby về dữ liệu chưa có, không âm thầm ánh xạ newest. Mới nhất là Next Link/catalogHref(... sort:newest); Giá router.push trong useTransition, disable dropdown khi pending. URL helper có sẵn reset trang1/giữ q/category/page_size. Sidebar bỏ dropdown sort cũ, thay hidden sort để submit search/page-size giữ lựa chọn trên thanh ngang. Backend GET /products chỉ nhận sort allowlist thật newest/price_asc/price_desc như cũ, không sửa API hoặc DB.

Kết quả: 14 frontend unit/contract tests PASS; lint PASS; typecheck PASS; build PASS, Docker frontend build/up --no-deps healthy. Browser fixture regression từ P3-04 đã chỉnh theo dropdown ngang: API pagination/sort/category/search/empty/error/retry/loading/Back/Forward/reload và 390/768/1440 PASS; kiểm tra h2 filter, cả 6 checkbox disabled, 2 ranking buttons disabled, newest active. Fixture HTTP/Next process riêng đã dừng, không ghi DB.

Real Docker browser PASS: sidebar 2 groups và sortbar xuất hiện, API hiện empty thật, price_asc từ q=serum&page2 reset về page1 vẫn q=serum, chọn newest xóa sort giữ q, disabled controls, mobile no overflow, không pageerror. Đã chờ final empty render sau transition rồi chụp và xem screenshot desktop/mobile; ảnh chụp sớm đầu tiên bắt skeleton đã được thay bằng screenshot final để không nhầm loading là kết quả. Script/screenshot D:/HealthBeauty/.ui-06-tools. Không tạo unit test chỉ mirror CSS; regression browser kiểm hành vi thật.

Bảo toàn: PostgreSQL ID/start/mount/config, root .env hash, network/volume không đổi. Không sửa backend/Compose/schema/data/Terraform hoặc commit/push/AWS. Cập nhật frontend README/task-plan/progress. Mở http://localhost:3001/san-pham, Ctrl+F5, thử giá hoặc newest; lựa chọn vận chuyển/dịch vụ/khuyến mãi/ranking cần task nghiệp vụ/API riêng trước khi bật. Lệnh build/update frontend giữ nguyên. Dừng sau UI-06, không tự làm P3-05.


## UI-07 ngày 09/11/2026 — DONE

Người dùng yêu cầu “đổi banner”, sau đó làm rõ “banner của trang sản phẩm”. Phạm vi chỉ trang danh sách /san-pham; không đổi homepage/campaign-banners.tsx. Lượt đầu khởi chạy tạo ảnh khi chưa rõ vị trí đã bị ngắt; một ảnh skincare hoàn tất và được kiểm tra phù hợp để dùng cho banner danh sách. Không tích hợp các banner phụ từ ý tưởng trước khi làm rõ.

Tạo CatalogBanner dùng siteBrand coco + HTML headline “Chăm chút hôm nay. Rạng rỡ mỗi ngày.”, caption ngắn và nhãn artwork minh họa. Ảnh gốc built-in image_gen có ba bao bì mỹ phẩm unbranded, nền kem/đào, dùng public/images/coco-catalog-banner.png; gốc còn ở generated_images/01a1be6a-3827-7e42-aadd-933c728c1b10/exec-a8ebd8de-f795-47a7-836c-f19a71b7dfd7.png. Prompt exact được lưu trong docs/banner-assets.md. Không dùng ảnh AI cho catalog/DB, không thêm fake promo hoặc giá. Next Image local priority, background gradient làm rõ chữ; desktop art70% bên phải, mobile art dưới chữ để không đè tiêu đề.

Thay phần catalog-page-intro trên app/san-pham/page.tsx bằng <CatalogBanner />; không sửa parse query/Suspense/CatalogBrowser. Header/search/sidebar/sort/pagination/API giữ nguyên. Homepage vẫn có ảnh UI-05 và đã kiểm tra src cũ, không có CatalogBanner ở route /.

Kiểm thử: lint PASS; typecheck PASS; build PASS; Docker frontend build/up --no-deps healthy. Chrome tại390/768/1440 PASS: img.complete và naturalWidth>0, chỉ một h1 chứa headline mới, không document overflow, sidebar/sort vẫn hiện, đổi price_asc vẫn điều hướng API đúng, homepage campaign cũ giữ nguyên, không JS errors. Đã xem screenshot desktop và mobile. Scripts/screenshots D:/HealthBeauty/.ui-07-tools. Không chạy lại unit/backend suite vì chỉ đổi banner không đổi logic dữ liệu; không thêm test mirror CSS.

Preservation trước/sau PASS: PostgreSQL ID/StartedAt/mount/config/env hash/network/volume giữ nguyên. Chỉ cập nhật container frontend; không thay backend/Compose/schema/data/Terraform, không AWS/commit/push. Cập nhật README frontend/task-plan/progress/banner-assets. Mở localhost:3001/san-pham và Ctrl+F5 để xem. Lệnh docker compose build frontend; docker compose up -d --no-deps --wait frontend. Dừng sau UI-07; UI-04 ảnh sản phẩm thật vẫn chờ nguồn.

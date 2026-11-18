const assert = require("node:assert/strict");
const { execFileSync } = require("node:child_process");
const { randomUUID } = require("node:crypto");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");

(async () => {
  const base = process.env.AUTH_E2E_URL;
  assert.match(base || "", /^http:\/\/127\.0\.0\.1:\d+$/);
  assert.equal(process.env.MARKETPLACE_ENVIRONMENT, "test");
  assert.equal(process.env.MARKETPLACE_DB_NAME, "marketplace_test");
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.E2E_CHROME
      ? { executablePath: process.env.E2E_CHROME }
      : {}),
  });
  const contexts = [],
    errors = [];
  async function actor(label) {
    const context = await browser.newContext();
    contexts.push(context);
    const page = await context.newPage();
    page.setDefaultTimeout(15000);
    page.on("pageerror", (error) => errors.push(error.message));
    const email = `e2e-${label}-${randomUUID()}@example.com`,
      password = "Checkout1!";
    async function write(resource, data, method = "POST") {
      const csrf = (
        await (await context.request.get(base + "/api/v1/auth/csrf")).json()
      ).data.csrf_token;
      return context.request.fetch(base + "/api/v1/" + resource, {
        method,
        headers: { Origin: base, "X-CSRF-Token": csrf },
        data,
      });
    }
    assert.equal(
      (
        await write("auth/register", { email, password, full_name: label })
      ).status(),
      201,
    );
    return { context, page, email, password, write };
  }
  async function login(a, destination = "/") {
    await a.page.goto(
      base +
        "/dang-nhap" +
        (destination === "/"
          ? ""
          : "?returnTo=" + encodeURIComponent(destination)),
    );
    await a.page.getByLabel("Email", { exact: true }).fill(a.email);
    await a.page.getByLabel("Mật khẩu", { exact: true }).fill(a.password);
    await a.page
      .getByRole("button", { name: "Đăng nhập", exact: true })
      .click();
    await a.page.waitForURL(base + destination);
  }
  async function responsive(page, label) {
    for (const width of [320, 390, 768, 1440]) {
      await page.setViewportSize({ width, height: 1000 });
      if (process.env.E2E_ARTIFACTS && [390, 1440].includes(width)) {
        await page.screenshot({
          path: path.join(process.env.E2E_ARTIFACTS, `${label}-${width}.png`),
          fullPage: true,
        });
      }
      assert.deepEqual(
        await page.evaluate(() =>
          [...document.querySelectorAll("main *")]
            .filter((el) => {
              const rect = el.getBoundingClientRect();
              return (
                rect.width && (rect.right > innerWidth + 1 || rect.left < -1)
              );
            })
            .slice(0, 8)
            .map((el) => ({
              tag: el.tagName,
              class: el.className,
              width: el.getBoundingClientRect().width,
            })),
        ),
        [],
        `${label} overflow ${width}`,
      );
      assert.equal(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
        true,
        `${label} page overflow ${width}`,
      );
    }
  }
  async function orderAction(page, name) {
    await page.getByRole("button", { name, exact: true }).click();
    await page
      .getByRole("button", { name: "Xác nhận thay đổi", exact: true })
      .click();
  }
  try {
    const admin = await actor("admin");
    execFileSync(
      process.env.CART_TEST_PYTHON,
      [path.join(__dirname, "promote_test_admin.py"), admin.email],
      { env: process.env },
    );
    await login(admin, "/admin/shops");
    for (const route of [
      "/gio-hang",
      "/thanh-toan",
      "/kenh-nguoi-ban",
      "/tai-khoan/dia-chi",
      "/tai-khoan/don-hang",
    ]) {
      await admin.page.goto(base + route);
      await admin.page
        .getByRole("heading", {
          name: "Tài khoản dành cho quản trị",
          exact: true,
        })
        .waitFor();
      assert.equal(
        await admin.page
          .getByRole("button", { name: "Đặt hàng COD", exact: true })
          .count(),
        0,
      );
    }
    await admin.page.goto(base + "/tai-khoan");
    await admin.page
      .getByRole("link", { name: "Quản lý người dùng →", exact: true })
      .waitFor();
    assert.equal(
      await admin.page
        .locator('a[href="/gio-hang"], a[href="/kenh-nguoi-ban"]')
        .count(),
      0,
    );
    await admin.page.goto(base + "/admin/shops");
    const categoryResponse = await admin.write("admin/categories", {
      category_name: "E2E chăm sóc da",
      category_slug: "e2e-care",
      is_active: true,
    });
    assert.equal(categoryResponse.status(), 201);
    const category = (await categoryResponse.json()).data;
    const seller = await actor("seller");
    await login(seller);
    const shopResponse = await seller.write("seller/shop", {
      shop_name: "E2E Shop",
      shop_slug: "e2e-shop",
    });
    assert.equal(shopResponse.status(), 201);
    const shop = (await shopResponse.json()).data;
    await admin.page.reload();
    await admin.page
      .getByRole("button", { name: "Phê duyệt", exact: true })
      .click();
    await admin.page
      .getByRole("button", { name: "Xác nhận thay đổi", exact: true })
      .click();
    await admin.page
      .getByRole("button", { name: "Khóa gian hàng", exact: true })
      .waitFor();
    const productResponse = await seller.write("seller/products", {
      category_id: category.category_id,
      sku: "E2E-SERUM",
      product_name: "E2E Serum dịu nhẹ",
      price: "120000",
      initial_quantity: 10,
    });
    assert.equal(productResponse.status(), 201);
    const product = (await productResponse.json()).data;
    await seller.page.goto(base + "/kenh-nguoi-ban/san-pham");
    await seller.page
      .getByRole("button", { name: "Quản lý ảnh", exact: true })
      .click();
    await seller.page.getByText(/Kho ảnh chưa được cấu hình/).waitFor();
    assert.equal(
      await seller.page
        .getByRole("button", { name: "Tải ảnh lên", exact: true })
        .isDisabled(),
      true,
    );
    await responsive(seller.page, "seller-no-storage");

    const guest = await browser.newContext();
    contexts.push(guest);
    const gp = await guest.newPage();
    gp.on("pageerror", (e) => errors.push(e.message));
    const catalogResponse = await gp.goto(base + "/san-pham");
    assert.equal(
      catalogResponse.headers()["x-content-type-options"],
      "nosniff",
    );
    assert.equal(catalogResponse.headers()["x-frame-options"], "DENY");
    assert.equal(
      catalogResponse.headers()["referrer-policy"],
      "strict-origin-when-cross-origin",
    );
    assert.equal(
      catalogResponse.headers()["permissions-policy"],
      "camera=(), microphone=(), geolocation=()",
    );
    await gp
      .getByLabel("Tìm theo tên sản phẩm", { exact: true })
      .fill("E2E Serum");
    await gp
      .getByRole("button", { name: "Áp dụng bộ lọc ↗", exact: true })
      .click();
    await gp
      .getByRole("link", { name: /E2E Serum dịu nhẹ/ })
      .first()
      .click();
    await gp
      .getByRole("heading", { name: product.product_name, exact: true })
      .waitFor();
    await gp
      .getByRole("link", { name: "Đăng nhập để thêm vào giỏ", exact: true })
      .waitFor();
    assert.equal(await gp.locator(".gallery-main img").count(), 0);
    await responsive(gp, "product-no-image");

    const buyer = await actor("buyer");
    await login(buyer);
    const bp = buyer.page;
    await bp.goto(base + "/thanh-toan");
    await bp
      .getByRole("heading", { name: "Giỏ hàng đang trống", exact: true })
      .waitFor();
    await bp.goto(base + "/san-pham/" + product.product_id);
    await bp
      .getByRole("button", { name: "Thêm vào giỏ", exact: true })
      .waitFor();
    const qty = bp.getByLabel("Số lượng", { exact: true });
    await qty.focus();
    await bp.keyboard.press("ControlOrMeta+A");
    await bp.keyboard.type("2");
    await bp.keyboard.press("Tab");
    assert.equal(
      await bp
        .getByRole("button", { name: "Thêm vào giỏ", exact: true })
        .evaluate((el) => el === document.activeElement),
      true,
    );
    await bp.keyboard.press("Enter");
    await bp.getByRole("link", { name: "Xem giỏ hàng →", exact: true }).click();
    await bp
      .getByRole("link", { name: "Tiến hành thanh toán →", exact: true })
      .click();
    await bp
      .getByText("Bạn chưa có địa chỉ giao hàng.", { exact: true })
      .waitFor();
    assert.equal(
      await bp
        .getByRole("button", { name: "Đặt hàng COD", exact: true })
        .isDisabled(),
      true,
    );
    await bp
      .getByRole("link", { name: "Thêm địa chỉ giao hàng →", exact: true })
      .click();
    await bp
      .getByRole("button", { name: "+ Thêm địa chỉ", exact: true })
      .click();
    await bp
      .getByLabel("Họ tên người nhận *", { exact: true })
      .fill("E2E Buyer");
    await bp.getByLabel("Số điện thoại *", { exact: true }).fill("0901234567");
    await bp
      .getByLabel("Số nhà, tên đường *", { exact: true })
      .fill("12 E2E Test");
    await bp.getByLabel("Tỉnh / thành phố *", { exact: true }).fill("Hà Nội");
    await bp.getByRole("button", { name: "Lưu địa chỉ", exact: true }).click();
    await bp.getByRole("heading", { name: "E2E Buyer", exact: true }).waitFor();
    await bp.goto(base + "/thanh-toan");
    await bp
      .getByRole("button", { name: "Đặt hàng COD", exact: true })
      .waitFor();
    await responsive(bp, "checkout");
    execFileSync(
      process.env.CART_TEST_PYTHON,
      [path.join(__dirname, "create_test_coupon.py")],
      { env: process.env },
    );
    await bp.getByLabel("Mã giảm giá (tối đa 1 mã)").fill("E2E10");
    await bp.getByRole("button", { name: "Áp dụng", exact: true }).click();
    await bp.getByText(/Mã E2E10: giảm/).waitFor();
    await responsive(bp, "checkout-coupon");
    const pending = bp.waitForResponse(
      (r) =>
        r.url().endsWith("/api/v1/orders/checkout") &&
        r.request().method() === "POST",
    );
    await bp.getByRole("button", { name: "Đặt hàng COD", exact: true }).click();
    const response = await pending;
    assert.equal(response.status(), 201);
    const order = (await response.json()).data;
    await bp
      .getByRole("heading", { name: "Đơn hàng đã được ghi nhận", exact: true })
      .waitFor();
    assert.equal(order.total_amount, "216000.00");
    assert.equal(order.discount_amount, "24000.00");
    await responsive(bp, "order-success");
    assert.equal(
      await bp.evaluate(
        () =>
          Object.keys(sessionStorage).filter((k) =>
            k.startsWith("coco.checkout.intent.v1:"),
          ).length,
      ),
      0,
    );
    // Another order can be placed while the first still has PENDING shop orders.
    assert.equal(
      (
        await buyer.write("cart/items", {
          product_id: product.product_id,
          quantity: 1,
        })
      ).status(),
      200,
    );
    const me = (
      await (await buyer.context.request.get(base + "/api/v1/auth/me")).json()
    ).data;
    const oldIntent = {
      version: 1,
      user_id: me.user_id,
      key: response.request().headers()["idempotency-key"],
      payload: response.request().postDataJSON(),
    };
    await bp.evaluate(
      (value) =>
        sessionStorage.setItem(
          `coco.checkout.intent.v1:${value.user_id}`,
          JSON.stringify(value),
        ),
      oldIntent,
    );
    await bp.goto(base + "/thanh-toan");
    await bp
      .getByRole("button", { name: "Đặt hàng COD", exact: true })
      .waitFor();
    assert.equal(
      await bp
        .getByText("Cần xác minh yêu cầu đặt hàng", { exact: true })
        .count(),
      0,
    );
    assert.equal(
      await bp.evaluate(
        (uid) => sessionStorage.getItem(`coco.checkout.intent.v1:${uid}`),
        me.user_id,
      ),
      null,
    );
    const notCreated = { ...oldIntent, key: randomUUID() };
    await bp.evaluate(
      (value) =>
        sessionStorage.setItem(
          `coco.checkout.intent.v1:${value.user_id}`,
          JSON.stringify(value),
        ),
      notCreated,
    );
    let unexpectedPosts = 0;
    const watch = (request) => {
      if (
        request.url().endsWith("/api/v1/orders/checkout") &&
        request.method() === "POST"
      )
        unexpectedPosts++;
    };
    bp.on("request", watch);
    await bp.reload();
    await bp
      .getByRole("button", { name: "Đặt hàng COD", exact: true })
      .waitFor();
    assert.equal(unexpectedPosts, 0);
    bp.off("request", watch);
    assert.equal(
      await bp.evaluate(
        (uid) =>
          JSON.parse(sessionStorage.getItem(`coco.checkout.intent.v1:${uid}`))
            .key,
        me.user_id,
      ),
      notCreated.key,
    );
    await responsive(bp, "checkout-auto-resolved");
    const secondPending = bp.waitForResponse(
      (r) =>
        r.url().endsWith("/api/v1/orders/checkout") &&
        r.request().method() === "POST",
    );
    await bp.getByRole("button", { name: "Đặt hàng COD", exact: true }).click();
    const secondResponse = await secondPending;
    assert.equal(secondResponse.status(), 201);
    const second = (await secondResponse.json()).data;
    assert.notEqual(second.order_id, order.order_id);
    assert.equal(
      (
        await buyer.write(
          `orders/${second.order_id}/shop-orders/${second.shop_orders[0].shop_order_id}/cancel`,
        )
      ).status(),
      200,
    );
    await bp.goto(base + "/tai-khoan/don-hang");
    await bp
      .getByRole("heading", { name: `Đơn #${order.order_id}`, exact: true })
      .waitFor();
    // Owning a shop does not hide purchases made from another shop.
    assert.equal((await buyer.write("seller/shop",{shop_name:"Buyer personal shop",shop_slug:"e2e-buyer-personal-shop"})).status(),201);
    await bp.goto(base+"/kenh-nguoi-ban");
    await bp.getByRole("heading",{name:"Gian hàng của tôi",exact:true}).waitFor();
    await responsive(bp,"seller-personal-purchase-entry");
    await bp.getByRole("link",{name:"Đơn mua",exact:true}).click();
    await bp.getByRole("heading",{name:`Đơn #${order.order_id}`,exact:true}).waitFor();
    await responsive(bp,"seller-personal-purchases");

    const sp = seller.page;
    const sid = order.shop_orders[0].shop_order_id;
    await sp.goto(base + "/kenh-nguoi-ban/don-hang/" + sid);
    await orderAction(sp, "Xác nhận đơn");
    await sp
      .getByRole("button", { name: "Bắt đầu giao hàng", exact: true })
      .waitFor();
    await orderAction(sp, "Bắt đầu giao hàng");
    await sp
      .getByRole("button", { name: "Hoàn tất đơn", exact: true })
      .waitFor();
    await orderAction(sp, "Hoàn tất đơn");
    await sp.getByText("Hoàn thành", { exact: true }).waitFor();
    await responsive(sp, "seller-order");
    await bp.goto(base + "/tai-khoan/don-hang/" + order.order_id);
    await bp.getByText("Hoàn thành", { exact: true }).waitFor();
    await responsive(bp, "buyer-order");
    await bp.getByLabel("Số sao", { exact: true }).selectOption("4");
    await bp
      .getByLabel("Nhận xét (không bắt buộc)")
      .fill("Sản phẩm tốt, giao hàng cẩn thận.");
    await bp.getByRole("button", { name: "Gửi đánh giá", exact: true }).click();
    await bp.getByText("Đánh giá của bạn: 4/5 sao", { exact: true }).waitFor();
    await bp.reload();
    await bp.getByText("Đánh giá của bạn: 4/5 sao", { exact: true }).waitFor();
    await responsive(bp, "buyer-review");
    await gp.goto(base + "/san-pham/" + product.product_id);
    await gp
      .getByText("Sản phẩm tốt, giao hàng cẩn thận.", { exact: true })
      .waitFor();
    await responsive(gp, "product-reviews");
    const stock = await seller.context.request.get(
      base + `/api/v1/seller/products/${product.product_id}/inventory`,
    );
    assert.equal((await stock.json()).data.quantity, 8);
    assert.equal(
      (
        await admin.context.request.get(base + "/api/v1/seller/orders/" + sid)
      ).status(),
      403,
    );
    assert.equal(
      (
        await admin.context.request.get(
          base + "/api/v1/orders/" + order.order_id,
        )
      ).status(),
      403,
    );

    await admin.page.goto(base + "/admin/products");
    await admin.page
      .getByRole("button", { name: "Ẩn sản phẩm", exact: true })
      .click();
    await admin.page
      .getByRole("button", { name: "Xác nhận ẩn", exact: true })
      .click();
    await admin.page
      .locator(".admin-shop-status")
      .filter({ hasText: /^Đã ẩn$/ })
      .waitFor();
    await admin.page.goto(base + "/admin/shops");
    await admin.page
      .getByRole("button", { name: "Khóa gian hàng", exact: true })
      .click();
    await admin.page
      .getByRole("button", { name: "Xác nhận thay đổi", exact: true })
      .click();
    await admin.page
      .locator(".admin-shop-status")
      .filter({ hasText: /^Đã khóa$/ })
      .waitFor();
    assert.equal(
      (
        await guest.request.get(base + "/san-pham/" + product.product_id)
      ).status(),
      404,
    );
    await bp.reload();
    await bp.getByText("Hoàn thành", { exact: true }).waitFor();
    const unchanged = (
      await (
        await buyer.context.request.get(
          base + "/api/v1/orders/" + order.order_id,
        )
      ).json()
    ).data;
    assert.equal(unchanged.total_amount, order.total_amount);
    assert.deepEqual(
      unchanged.shop_orders[0].items,
      order.shop_orders[0].items,
    );

    const route = "**/api/v1/cart";
    let release;
    const held = new Promise((resolve) => {
      release = resolve;
    });
    await bp.route(route, async (r) => {
      await held;
      await r.fulfill({
        status: 503,
        contentType: "application/json",
        body: '{"error":{"code":"DEPENDENCY_UNAVAILABLE"}}',
      });
    });
    await bp.goto(base + "/gio-hang");
    await bp
      .getByText("Đang tải giá, tồn kho và giỏ hàng…", { exact: true })
      .waitFor();
    release();
    await bp.locator("main [role=alert]").waitFor();
    await responsive(bp, "cart-error");
    await bp.unroute(route);
    await bp.reload();
    await bp
      .getByRole("heading", {
        name: "Giỏ hàng của bạn đang trống",
        exact: true,
      })
      .waitFor();
    await buyer.context.addCookies([
      {
        name: "marketplace_access",
        value: process.env.EXPIRED_TOKEN,
        url: base,
        httpOnly: true,
        sameSite: "Lax",
      },
    ]);
    await bp.goto(base + "/tai-khoan/don-hang/" + order.order_id);
    await bp
      .getByRole("heading", { name: "Đăng nhập để xem đơn mua", exact: true })
      .waitFor();
    assert.equal(
      await bp
        .getByRole("heading", { name: "Thông tin nhận hàng", exact: true })
        .count(),
      0,
    );
    assert.deepEqual(errors, []);
    console.log(
      "PASS Guest search/no-image; keyboard add; UI coupon/checkout/discounted history; second purchase while first PENDING; verified review create/reload/public display; Seller lifecycle; Admin approve/hide/lock; snapshot/ownership; loading/503/recovery; 4 widths.",
    );
  } finally {
    for (const context of contexts) await context.close();
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

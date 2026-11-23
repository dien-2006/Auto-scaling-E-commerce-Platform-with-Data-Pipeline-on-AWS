const assert = require("node:assert/strict");
const { execFileSync } = require("node:child_process");
const path = require("node:path");
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
(async () => {
  assert.equal(process.env.MARKETPLACE_DB_NAME, "marketplace_test");
  assert.equal(process.env.MARKETPLACE_CHECKOUT_OPTIONS_ENABLED, "true");
  const seed = JSON.parse(
    execFileSync(
      process.env.CART_TEST_PYTHON,
      [path.join(__dirname, "options_seed.py")],
      { env: process.env, encoding: "utf8" },
    ),
  );
  const browser = await chromium.launch({
    headless: true,
    executablePath: process.env.E2E_CHROME,
  });
  const page = await browser.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const base = process.env.AUTH_E2E_URL;
  assert.match(base, /^http:\/\/127\.0\.0\.1:\d+$/);
  try {
    await page.goto(base + "/dang-nhap?returnTo=%2Fthanh-toan");
    await page.getByLabel("Email", { exact: true }).fill(seed.email);
    await page.getByLabel("Mật khẩu", { exact: true }).fill("Options1!");
    await page.getByRole("button", { name: "Đăng nhập", exact: true }).click();
    await page.waitForURL(base + "/thanh-toan");
    await page
      .getByLabel("Mã shop Options shop 0", { exact: true })
      .fill("SHOP10");
    await page
      .getByLabel("Mã shop Options shop 1", { exact: true })
      .fill("SHOP20");
    await page
      .getByLabel("Mã COCO giảm tiền hàng", { exact: true })
      .fill("COCO10");
    await page
      .getByLabel("Mã COCO giảm phí vận chuyển", { exact: true })
      .fill("SHIP50");
    async function quote(expected) {
      const pending = page.waitForResponse(
        (r) =>
          r.url().endsWith("/api/v1/checkout/quote") &&
          r.request().method() === "POST",
      );
      await page
        .getByRole("button", { name: "Áp dụng và tính tổng tiền", exact: true })
        .click();
      const response = await pending;
      assert.equal(response.status(), 200);
      const result = await response.json();
      assert.equal(result.total_amount, expected);
      await page.locator(".checkout-quote").waitFor();
    }
    await quote("250000.00");
    await page.getByRole("radio", { name: /Nhanh/ }).check();
    assert.equal(
      await page
        .getByRole("button", { name: "Đặt hàng COD", exact: true })
        .isDisabled(),
      true,
    );
    await quote("265000.00");
    await page.getByRole("radio", { name: /COCO Express/ }).check();
    await quote("285000.00");
    assert.equal(
      await page.getByRole("radio", { name: /Ví MoMo/ }).isDisabled(),
      true,
    );
    assert.equal(
      await page.getByRole("radio", { name: /VNPay/ }).isDisabled(),
      true,
    );
    await page.getByRole("radio", { name: /Chuyển khoản ngân hàng/ }).check();
    await quote("285000.00");
    for (const width of [320, 390, 768, 1440]) {
      await page.setViewportSize({ width, height: 1000 });
      assert.equal(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
        true,
      );
      if (process.env.E2E_ARTIFACTS && [390, 1440].includes(width))
        await page.screenshot({
          path: path.join(process.env.E2E_ARTIFACTS, `options-${width}.png`),
          fullPage: true,
        });
    }
    const placed = page.waitForResponse(
      (r) =>
        r.url().endsWith("/api/v1/orders/checkout") &&
        r.request().method() === "POST",
    );
    await page
      .getByRole("button", { name: "Đặt hàng và chuyển khoản", exact: true })
      .click();
    const response = await placed;
    assert.equal(response.status(), 201);
    const order = (await response.json()).data;
    assert.equal(order.total_amount, "285000.00");
    assert.equal(order.payment_status, "PENDING");
    assert.equal(order.applied_coupons.length, 4);
    await page.getByText("Chờ xác nhận thanh toán", { exact: true }).waitFor();
    await page
      .getByText("Số tài khoản: TEST-ONLY-123", { exact: true })
      .waitFor();
    await page.goto(base + "/tai-khoan/don-hang/" + order.order_id);
    await page.getByText("Chờ xác nhận thanh toán", { exact: true }).waitFor();
    await page
      .getByText("Số tài khoản: TEST-ONLY-123", { exact: true })
      .waitFor();
    assert.deepEqual(errors, []);
    console.log(
      "PASS scoped shop + COCO goods + COCO freight coupons; three shipping rates; quote invalidation; disabled gateways; bank PENDING/create/history; 4 widths",
    );
  } finally {
    await browser.close();
  }
})().catch((e) => {
  console.error(e);
  process.exitCode = 1;
});

const { chromium } = require(process.env.PLAYWRIGHT_MODULE || "playwright");
const assert = require("node:assert/strict"),
  { execFileSync } = require("node:child_process"),
  { randomUUID } = require("node:crypto"),
  path = require("node:path");
(async () => {
  const base = process.env.AUTH_E2E_URL;
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
    page.on("pageerror", (e) => errors.push(e.message));
    const email = `e2e-${label}-${randomUUID()}@example.com`;
    async function write(resource, data, method = "POST") {
      const csrf = (
        await (await context.request.get(base + "/api/v1/auth/csrf")).json()
      ).data.csrf_token;
      return context.request.fetch(base + "/api/v1/" + resource, {
        method,
        headers: { Origin: base, "X-CSRF-Token": csrf },
        ...(data === undefined ? {} : { data }),
      });
    }
    assert.equal(
      (
        await write("auth/register", {
          email,
          password: "Checkout1!",
          full_name: label,
        })
      ).status(),
      201,
    );
    assert.equal(
      (await write("auth/login", { email, password: "Checkout1!" })).status(),
      200,
    );
    return { context, page, email, write };
  }
  async function widths(page, label) {
    for (const width of [320, 390, 768, 1440]) {
      await page.setViewportSize({ width, height: 1000 });
      assert.equal(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
        true,
        label + width,
      );
      if (process.env.E2E_ARTIFACTS && [390, 1440].includes(width))
        await page.screenshot({
          path: path.join(process.env.E2E_ARTIFACTS, `${label}-${width}.png`),
          fullPage: true,
        });
    }
  }
  try {
    const admin = await actor("admin"),
      owner = await actor("crud"),
      buyer = await actor("buyer");
    execFileSync(
      process.env.CART_TEST_PYTHON,
      [path.join(__dirname, "promote_test_admin.py"), admin.email],
      { env: process.env },
    );
    const category = (
      await (
        await admin.write("admin/categories", {
          category_name: "CRUD Category",
          category_slug: "crud-category",
        })
      ).json()
    ).data;
    const page = owner.page;
    async function createShop() {
      await page.goto(base + "/kenh-nguoi-ban");
      await page
        .getByPlaceholder("Tên shop", { exact: true })
        .fill("CRUD Shop");
      await page.getByRole("button", { name: "Tiếp tục", exact: true }).click();
      await page
        .getByRole("heading", { name: "CRUD Shop", exact: true })
        .waitFor();
      return (
        await (
          await owner.context.request.get(base + "/api/v1/seller/shop")
        ).json()
      ).data;
    }
    let shop = await createShop();
    const old = shop.shop_id;
    await page.locator("#seller-shop-name").fill("CRUD Shop Edited");
    await page
      .getByRole("button", { name: "Lưu thay đổi", exact: true })
      .click();
    await page
      .getByRole("heading", { name: "CRUD Shop Edited", exact: true })
      .waitFor();
    await page
      .getByRole("button", { name: "Xóa gian hàng", exact: true })
      .click();
    await widths(page, "shop-delete");
    await page
      .getByRole("button", { name: "Xác nhận xóa gian hàng", exact: true })
      .click();
    await page.getByPlaceholder("Tên shop", { exact: true }).waitFor();
    assert.equal(
      (await owner.context.request.get(base + "/api/v1/seller/shop")).status(),
      404,
    );
    shop = await createShop();
    assert.equal(
      (await owner.write("seller/shop/" + old, undefined, "DELETE")).status(),
      404,
    );
    assert.equal(
      (
        await admin.write(
          "admin/shops/" + shop.shop_id + "/status",
          { expected_status: "PENDING", shop_status: "APPROVED" },
          "PATCH",
        )
      ).status(),
      200,
    );
    await page.goto(base + "/kenh-nguoi-ban/san-pham");
    await page
      .getByRole("button", { name: "Thêm sản phẩm", exact: true })
      .click();
    const form = page
      .locator("form")
      .filter({
        has: page.getByRole("button", { name: "Lưu sản phẩm", exact: true }),
      });
    await form.getByLabel("Tên sản phẩm", { exact: true }).fill("CRUD Product");
    await form.getByLabel("SKU", { exact: true }).fill("CRUD-ONE");
    await form
      .getByLabel("Danh mục", { exact: true })
      .selectOption(category.category_id);
    await form.locator('input[name="price"]').fill("100");
    await form.locator('input[name="initial_quantity"]').fill("3");
    await form
      .getByRole("button", { name: "Lưu sản phẩm", exact: true })
      .click();
    await page
      .getByText("Đã tạo sản phẩm và tồn kho ban đầu.", { exact: true })
      .waitFor();
    await page.getByRole("button", { name: "Chỉnh sửa", exact: true }).click();
    await form
      .getByLabel("Tên sản phẩm", { exact: true })
      .fill("CRUD Product Edited");
    await form
      .getByRole("button", { name: "Lưu sản phẩm", exact: true })
      .click();
    await page.getByText("Đã lưu sản phẩm.", { exact: true }).waitFor();
    await page
      .getByRole("button", { name: "Xóa sản phẩm", exact: true })
      .click();
    await widths(page, "product-delete");
    await page
      .getByRole("button", { name: "Xác nhận xóa sản phẩm", exact: true })
      .click();
    await page.getByText("Đã xóa sản phẩm.", { exact: true }).waitFor();
    assert.equal(await page.locator(".seller-product-list li").count(), 0);
    const used = (
      await (
        await owner.write("seller/products", {
          category_id: category.category_id,
          sku: "USED",
          product_name: "Used Product",
          price: "100",
          initial_quantity: 3,
        })
      ).json()
    ).data;
    assert.equal(
      (
        await buyer.write("cart/items", {
          product_id: used.product_id,
          quantity: 1,
        })
      ).status(),
      200,
    );
    await page.reload();
    await page
      .getByRole("button", { name: "Xóa sản phẩm", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Xác nhận xóa sản phẩm", exact: true })
      .click();
    await page
      .getByRole("alert")
      .filter({ hasText: "Sản phẩm có giỏ hàng" })
      .waitFor();
    assert.equal(
      (
        await (
          await owner.context.request.get(
            base + `/api/v1/seller/products/${used.product_id}/inventory`,
          )
        ).json()
      ).data.quantity,
      3,
    );
    await page.goto(base + "/kenh-nguoi-ban");
    await page
      .getByRole("button", { name: "Xóa gian hàng", exact: true })
      .click();
    await page
      .getByRole("button", { name: "Xác nhận xóa gian hàng", exact: true })
      .click();
    await page
      .getByRole("alert")
      .filter({ hasText: "Gian hàng có sản phẩm" })
      .waitFor();
    assert.deepEqual(errors, []);
    console.log(
      "PASS 25-table browser CRUD shop/product; stale shop ID; used product/shop409; stock preserved; 4 widths/no JS errors",
    );
  } finally {
    for (const c of contexts) await c.close();
    await browser.close();
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});

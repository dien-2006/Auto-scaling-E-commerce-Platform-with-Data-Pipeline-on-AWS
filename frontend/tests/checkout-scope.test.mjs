import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import ts from "typescript";

const source = await readFile(
  new URL("../src/lib/checkout-options-client.ts", import.meta.url),
  "utf8",
);
const { outputText } = ts.transpileModule(source, {
  compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 },
});
const { quoteChoices } = await import(
  `data:text/javascript;base64,${Buffer.from(outputText).toString("base64")}`
);

for (const scope of [
  { selected_product_ids: ["1"] },
  { direct_item: { product_id: "1", quantity: 1, expected_unit_price: "100.00" } },
]) {
  test(`checkout quote forwards ${Object.keys(scope)[0]} to the backend`, async () => {
    const previousFetch = globalThis.fetch;
    let sent;
    globalThis.fetch = async (path, init) => {
      if (path === "/api/v1/auth/csrf")
        return Response.json({ data: { csrf_token: "test-csrf" } });
      assert.equal(path, "/api/v1/checkout/quote");
      assert.equal(init.method, "POST");
      sent = JSON.parse(init.body);
      return Response.json({
        subtotal: "100.00",
        discount_amount: "0.00",
        shipping_fee: "10.00",
        shipping_discount_amount: "0.00",
        total_amount: "110.00",
        applied_coupons: [],
        shipping: [{ shop_id: "10", method: "STANDARD", fee: "10.00" }],
      });
    };
    try {
      const selection = {
        shipping_method: "STANDARD",
        payment_method: "COD",
        shop_coupons: [],
        ...scope,
      };
      const result = await quoteChoices(selection);
      assert.deepEqual(sent, selection);
      assert.equal(result.total_amount, "110.00");
    } finally {
      globalThis.fetch = previousFetch;
    }
  });
}

import http from "k6/http";
import { check, fail, sleep } from "k6";

const base = (__ENV.BASE_URL || "").replace(/\/$/, "");
const origin = __ENV.PUBLIC_ORIGIN || base;
if (
  !/^https?:\/\/[^/?#@]+$/.test(base) ||
  !/^https?:\/\/[^/?#@]+$/.test(origin)
)
  throw new Error(
    "Set BASE_URL and optional PUBLIC_ORIGIN to explicit origins without credentials or paths",
  );
const vus = Number(__ENV.VUS || 1),
  iterations = Number(__ENV.ITERATIONS || 5);
if (
  !Number.isInteger(vus) ||
  !Number.isInteger(iterations) ||
  vus < 1 ||
  vus > 20 ||
  iterations < 1 ||
  iterations > 1000
)
  throw new Error("Bounded run requires VUS1..20 and ITERATIONS1..1000");
if (
  (vus > 1 || iterations > 5) &&
  !["isolated", "staging"].includes(__ENV.TEST_ENV)
)
  throw new Error(
    "Load runs require TEST_ENV=isolated or staging; default is a small read-only smoke",
  );
export const options = {
  scenarios: {
    web: { executor: "shared-iterations", vus, iterations, maxDuration: "60s" },
  },
  thresholds: { checks: ["rate==1"], http_req_failed: ["rate<0.01"] },
};
const params = { timeout: "10s", redirects: 0 };
export default function () {
  const page = http.get(base + "/", { ...params, tags: { name: "homepage" } });
  check(page, { "web reachable": (r) => r.status === 200 });
  const products = http.get(base + "/api/v1/products?page_size=12", {
    ...params,
    tags: { name: "catalog" },
  });
  check(products, {
    "catalog public": (r) => r.status === 200 && Array.isArray(r.json("items")),
  });
  const csrf = http.get(base + "/api/v1/auth/csrf", params);
  if (
    !check(csrf, {
      "csrf cookie/token issued": (r) =>
        r.status === 200 && typeof r.json("data.csrf_token") === "string",
    })
  )
    fail("CSRF unavailable");
  // Deliberately invalid body: validates CSRF integration without creating users or login attempts.
  const validation = http.post(base + "/api/v1/auth/login", "{}", {
    ...params,
    headers: {
      Origin: origin,
      "Content-Type": "application/json",
      "X-CSRF-Token": csrf.json("data.csrf_token"),
    },
    responseCallback: http.expectedStatuses(422),
    tags: { name: "csrf_validation" },
  });
  check(validation, {
    "k6 respects Origin and cookie-bound CSRF": (r) =>
      r.status === 422 && r.json("error.code") === "VALIDATION_ERROR",
  });
  const denied = http.get(base + "/api/v1/admin/shops", {
    ...params,
    responseCallback: http.expectedStatuses(401),
    tags: { name: "guest_denied" },
  });
  check(denied, {
    "k6 does not bypass Admin authentication": (r) => r.status === 401,
  });
  sleep(0.1);
}

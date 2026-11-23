import http from "k6/http";
import { check, fail, sleep } from "k6";

// Public HTTP only. No login, checkout, cookies/CSRF setup, inventory or SQL.
const base = (__ENV.BASE_URL || "").replace(/\/$/, "");
if (!/^https?:\/\/[^/?#@\s]+$/.test(base)) {
  throw new Error("BASE_URL must be an explicit HTTP(S) origin without credentials/path/query");
}
const profile = __ENV.PROFILE || "smoke";
const peak = Number(__ENV.PEAK_VUS || 50);
const hold = Number(__ENV.HOLD_SECONDS || 600);
if (!["smoke", "scale"].includes(profile) ||
    !Number.isInteger(peak) || peak < 1 || peak > 200 ||
    !Number.isInteger(hold) || hold < 60 || hold > 1200) {
  throw new Error("Use PROFILE=smoke|scale, PEAK_VUS=1..200, HOLD_SECONDS=60..1200");
}

export const options = {
  discardResponseBodies: true,
  scenarios: profile === "smoke" ? {
    browsing: { executor: "shared-iterations", vus: 1, iterations: 5, maxDuration: "60s" },
  } : {
    browsing: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "30s", target: Math.min(5, peak) },
        { duration: "1m", target: Math.min(20, peak) },
        { duration: "2m", target: peak },
        { duration: `${hold}s`, target: peak },
        { duration: "1m", target: 0 },
      ],
      gracefulRampDown: "30s",
      gracefulStop: "30s",
    },
  },
  thresholds: {
    checks: ["rate>0.99"],
    http_req_failed: ["rate<0.05"],
    http_req_duration: ["p(95)<5000"],
  },
};

const params = { timeout: "15s", redirects: 0 };

function validCatalog(response) {
  if (response.status !== 200) return false;
  try {
    return Array.isArray(response.json("items"));
  } catch (_) {
    return false;
  }
}

export function setup() {
  const live = http.get(`${base}/health/live`, {
    ...params, tags: { name: "frontend_liveness", phase: "preflight" },
  });
  if (live.status !== 200) fail(`Frontend preflight failed: HTTP ${live.status}`);
  const catalog = http.get(`${base}/api/v1/products?page_size=12`, {
    ...params, responseType: "text", tags: { name: "catalog", phase: "preflight" },
  });
  if (!validCatalog(catalog)) fail(`Catalog preflight failed: HTTP ${catalog.status}; no load started`);
  console.log(`Profile=${profile}; peak=${profile === "smoke" ? 1 : peak} VUs; target=${base}`);
}

export default function () {
  const page = http.get(`${base}/`, { ...params, tags: { name: "homepage" } });
  check(page, { "homepage HTTP 200": (response) => response.status === 200 });
  const number = (__ITER % 4) + 1;
  const catalog = http.get(`${base}/api/v1/products?page=${number}&page_size=12`, {
    ...params, responseType: "text", tags: { name: "catalog" },
  });
  check(catalog, { "public catalog HTTP 200 with items": validCatalog });
  sleep(0.5);
}

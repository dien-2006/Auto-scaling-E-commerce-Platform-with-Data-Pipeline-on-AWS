import test from "node:test";
import assert from "node:assert/strict";
import http from "node:http";
import metricsModule from "../observability/http-metrics.cjs";

const { createRegistry, createMetricsServer, installObserver } = metricsModule;

test("frontend histogram keeps cumulative buckets, final status and bounded labels", () => {
  const registry = createRegistry();
  registry.observe("GET", 200, 0.025);
  registry.observe("GET", 200, 2);
  registry.observe("custom\nprivate-data", 500, 0.1);
  const metrics = registry.render();
  assert.match(metrics, /marketplace_frontend_http_requests_total\{method="GET",status_code="200"\} 2/);
  assert.match(metrics, /_bucket\{method="GET",status_code="200",le="0.01"\} 0/);
  assert.match(metrics, /_bucket\{method="GET",status_code="200",le="0.025"\} 1/);
  assert.match(metrics, /_bucket\{method="GET",status_code="200",le="2.5"\} 2/);
  assert.match(metrics, /_bucket\{method="GET",status_code="200",le="\+Inf"\} 2/);
  assert.match(metrics, /_count\{method="GET",status_code="200"\} 2/);
  assert.match(metrics, /method="OTHER",status_code="500"/);
  assert.doesNotMatch(metrics, /private-data/);
});

test("HTTP observer preserves streaming/body/cookies and ignores health and its own scrape", async (t) => {
  const registry = createRegistry();
  const metricsServer = createMetricsServer(registry);
  let resolveAborted;
  const aborted = new Promise((resolve) => { resolveAborted = resolve; });
  const app = http.createServer((request, response) => {
    if (request.url === "/abort") {
      response.once("close", resolveAborted);
      response.destroy();
      return;
    }
    if (request.url.startsWith("/stream")) {
      response.writeHead(201, { "Content-Type": "text/plain", "Set-Cookie": "test-cookie=unchanged; HttpOnly" });
      response.write("first-");
      setTimeout(() => response.end("last"), 10);
      return;
    }
    response.statusCode = request.url === "/failure" ? 503 : 200;
    response.end("ok");
  });
  const undo = installObserver(registry, metricsServer);
  t.after(async () => {
    undo();
    await Promise.all([app, metricsServer].map((server) => new Promise((resolve) => {
      server.closeAllConnections();
      server.close(resolve);
    })));
  });
  await Promise.all([app, metricsServer].map((server) => new Promise((resolve) => server.listen(0, "127.0.0.1", resolve))));
  const base = `http://127.0.0.1:${app.address().port}`;
  const response = await fetch(`${base}/stream?private-search=do-not-export`);
  assert.equal(response.status, 201);
  assert.equal(response.headers.get("set-cookie"), "test-cookie=unchanged; HttpOnly");
  assert.equal(await response.text(), "first-last");
  await (await fetch(`${base}/health/live?probe=true`)).text();
  await (await fetch(`${base}/failure`)).text();
  await new Promise((resolve, reject) => {
    const request = http.get(`${base}/abort`, (res) => { res.resume(); res.on("end", () => reject(new Error("Abort unexpectedly completed"))); });
    request.once("error", resolve);
  });
  await aborted;
  const scraped = await fetch(`http://127.0.0.1:${metricsServer.address().port}/metrics`);
  assert.match(scraped.headers.get("content-type"), /text\/plain; version=0\.0\.4/);
  const metrics = await scraped.text();
  assert.match(metrics, /requests_total\{method="GET",status_code="201"\} 1/);
  assert.match(metrics, /requests_total\{method="GET",status_code="503"\} 1/);
  assert.match(metrics, /requests_aborted_total\{method="GET"\} 1/);
  assert.doesNotMatch(metrics, /status_code="200"/);
  assert.doesNotMatch(metrics, /private-search|do-not-export|test-cookie|route=|url=/);
});

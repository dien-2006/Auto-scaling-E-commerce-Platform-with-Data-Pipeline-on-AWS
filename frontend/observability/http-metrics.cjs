"use strict";

const http = require("node:http");

const BUCKETS = Object.freeze([0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 15, 30, 60]);
const METHODS = new Set(["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]);
const CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8";

function methodLabel(method) {
  return METHODS.has(method) ? method : "OTHER";
}

function createRegistry() {
  const responses = new Map();
  const aborted = new Map();
  return {
    observe(method, status, seconds) {
      if (!Number.isFinite(seconds) || seconds < 0) return;
      const verb = methodLabel(method);
      const code = Number.isInteger(status) && status >= 100 && status <= 599 ? String(status) : "other";
      const key = `${verb}:${code}`;
      let row = responses.get(key);
      if (!row) {
        row = { method: verb, status: code, count: 0, sum: 0, buckets: BUCKETS.map(() => 0) };
        responses.set(key, row);
      }
      row.count += 1;
      row.sum += seconds;
      BUCKETS.forEach((limit, index) => { if (seconds <= limit) row.buckets[index] += 1; });
    },
    abort(method) {
      const label = methodLabel(method);
      aborted.set(label, (aborted.get(label) || 0) + 1);
    },
    render() {
      const lines = [
        "# HELP marketplace_frontend_http_requests_total Completed frontend HTTP responses, excluding health and metrics.",
        "# TYPE marketplace_frontend_http_requests_total counter",
      ];
      for (const row of responses.values()) {
        lines.push(`marketplace_frontend_http_requests_total{method="${row.method}",status_code="${row.status}"} ${row.count}`);
      }
      lines.push(
        "# HELP marketplace_frontend_http_request_duration_seconds Frontend response duration until HTTP finish, excluding aborted responses.",
        "# TYPE marketplace_frontend_http_request_duration_seconds histogram",
      );
      for (const row of responses.values()) {
        const labels = `method="${row.method}",status_code="${row.status}"`;
        BUCKETS.forEach((limit, index) => {
          lines.push(`marketplace_frontend_http_request_duration_seconds_bucket{${labels},le="${limit}"} ${row.buckets[index]}`);
        });
        lines.push(
          `marketplace_frontend_http_request_duration_seconds_bucket{${labels},le="+Inf"} ${row.count}`,
          `marketplace_frontend_http_request_duration_seconds_count{${labels}} ${row.count}`,
          `marketplace_frontend_http_request_duration_seconds_sum{${labels}} ${row.sum}`,
        );
      }
      lines.push(
        "# HELP marketplace_frontend_http_requests_aborted_total Responses closed before the finish event.",
        "# TYPE marketplace_frontend_http_requests_aborted_total counter",
      );
      for (const [method, count] of aborted) {
        lines.push(`marketplace_frontend_http_requests_aborted_total{method="${method}"} ${count}`);
      }
      return lines.join("\n") + "\n";
    },
  };
}

function createMetricsServer(registry) {
  return http.createServer((request, response) => {
    const path = (request.url || "").split("?", 1)[0];
    if (path !== "/metrics" || !["GET", "HEAD"].includes(request.method)) {
      response.writeHead(404);
      response.end();
      return;
    }
    response.writeHead(200, { "Content-Type": CONTENT_TYPE, "Cache-Control": "no-store" });
    response.end(request.method === "HEAD" ? undefined : registry.render());
  });
}

function installObserver(registry, ignoredServer) {
  const original = http.Server.prototype.emit;
  function instrumented(event, ...args) {
    if (event === "request" && this !== ignoredServer) {
      const [request, response] = args;
      const path = (request.url || "").split("?", 1)[0];
      if (!["/metrics", "/health/live", "/health/ready"].includes(path)) {
        const started = process.hrtime.bigint();
        let settled = false;
        const onClose = () => {
          if (settled) return;
          settled = true;
          response.removeListener("finish", onFinish);
          registry.abort(request.method);
        };
        const onFinish = () => {
          if (settled) return;
          settled = true;
          response.removeListener("close", onClose);
          registry.observe(request.method, response.statusCode,
            Number(process.hrtime.bigint() - started) / 1e9);
        };
        response.once("finish", onFinish);
        response.once("close", onClose);
      }
    }
    // Preserve Node's dispatch, request/body, streaming, cookies, status and errors.
    return Reflect.apply(original, this, [event, ...args]);
  }
  http.Server.prototype.emit = instrumented;
  return () => {
    if (http.Server.prototype.emit === instrumented) http.Server.prototype.emit = original;
  };
}

module.exports = { BUCKETS, CONTENT_TYPE, createRegistry, createMetricsServer, installObserver };

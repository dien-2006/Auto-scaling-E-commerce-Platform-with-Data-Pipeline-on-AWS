import { test } from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import ts from "typescript";
const url = source => `data:text/javascript;base64,${Buffer.from(ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } }).outputText).toString("base64")}`;
const contract = url(await readFile(new URL("../src/lib/auth-contract.ts", import.meta.url), "utf8"));
const source = (await readFile(new URL("../src/lib/auth-client.ts", import.meta.url), "utf8")).replace("@/lib/auth-contract", contract);
const { mutateAuth, AuthFailure } = await import(url(source));
for (const [name, failure, expected] of [
  ["lost registration response", new TypeError("network private details"), "NETWORK_ERROR"],
  ["registration timeout", new DOMException("private timeout details", "TimeoutError"), "REQUEST_TIMEOUT"],
  ["non-JSON rate limit", new Response("private html", {status:429}), "RATE_LIMITED"],
  ["non-JSON server failure", new Response("private html", {status:503}), "SERVER_ERROR"],
]) {
  test(name + " is sanitized and never automatically retries registration", async () => {
    const original = globalThis.fetch;
    let posts = 0;
    globalThis.fetch = async (path, init) => {
      if (path.endsWith("/csrf")) return Response.json({data:{csrf_token:"test-only"}});
      assert.equal(init.method, "POST");
      posts++;
      if (failure instanceof Error) throw failure;
      return failure;
    };
    try {
      await assert.rejects(mutateAuth("register", {email:"fixture@example.test", password:"test-only"}), e => e instanceof AuthFailure && e.code === expected && !e.message.includes("private"));
      assert.equal(posts, 1);
    } finally { globalThis.fetch = original; }
  });
}


const otpSource=(await readFile(new URL("../src/lib/otp-client.ts",import.meta.url),"utf8")).replace("@/lib/auth-client",url(source));
const {requestOTP}=await import(url(otpSource));
test("OTP requests preserve 60-second contract and never retry after response loss",async()=>{
  const old=globalThis.fetch;let requests=0;
  globalThis.fetch=async path=>{
    if(path.endsWith("/csrf"))return Response.json({data:{csrf_token:"test"}});
    requests++;throw new TypeError("private transport error");
  };
  try {await assert.rejects(requestOTP({purpose:"RESET_PASSWORD",channel:"EMAIL",target:"fixture@example.test"}),e=>e.code==="NETWORK_ERROR"&&!e.message.includes("private"));assert.equal(requests,1);}
  finally {globalThis.fetch=old;}
});

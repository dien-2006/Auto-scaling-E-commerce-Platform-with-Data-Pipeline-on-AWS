"""Shared Redis proofs: atomic rates, five attempts, 60-second TTL and consume-once.

Proof is deleted BEFORE the SQL mutation. A SQL failure burns the proof instead of
allowing replay; Redis and PostgreSQL are deliberately not claimed to be one tx.
"""

import json

from redis import Redis
from redis.backoff import NoBackoff
from redis.exceptions import RedisError
from redis.retry import Retry

from app.core.errors import APIError

PREFIX = "coco:{otp}:"

ISSUE = """
local t=redis.call('TIME')
local now=tonumber(t[1])*1000+math.floor(tonumber(t[2])/1000)
for i=3,4 do redis.call('ZREMRANGEBYSCORE',KEYS[i],'-inf',now-3600000) end
if redis.call('EXISTS',KEYS[5])==1 or redis.call('ZCARD',KEYS[3])>=5
or redis.call('ZCARD',KEYS[4])>=100 then return 0 end
local old=redis.call('GET',KEYS[2])
if old then redis.call('DEL',old) end
local row=cjson.decode(ARGV[1])
row.created_at=now
row.expires_at=now+60000
redis.call('SET',KEYS[1],cjson.encode(row),'PX',60000)
redis.call('SET',KEYS[2],KEYS[1],'PX',60000)
redis.call('SET',KEYS[5],'1','PX',60000)
for i=3,4 do
 redis.call('ZADD',KEYS[i],now,KEYS[1])
 redis.call('PEXPIRE',KEYS[i],3600000)
end
return 1
"""

DELIVERED = """
local raw=redis.call('GET',KEYS[1])
if not raw then return 0 end
if ARGV[1]=='0' then return redis.call('DEL',KEYS[1]) end
local row=cjson.decode(raw)
row.delivered=true
redis.call('SET',KEYS[1],cjson.encode(row),'KEEPTTL')
return 1
"""

CONSUME = """
local raw=redis.call('GET',KEYS[1])
if not raw then return '' end
local row=cjson.decode(raw)
if not row.delivered then return '' end
local diff=0
for i=1,64 do
 diff=bit.bor(diff,bit.bxor(string.byte(row.code_hash,i),string.byte(ARGV[1],i)))
end
if diff~=0 then
 row.attempts=row.attempts+1
 if row.attempts>=5 then redis.call('DEL',KEYS[1])
 else redis.call('SET',KEYS[1],cjson.encode(row),'KEEPTTL') end
 return ''
end
redis.call('DEL',KEYS[1])
return raw
"""


CONSUME_GRANT = """
local raw=redis.call('GET',KEYS[1])
if not raw then return '' end
local row=cjson.decode(raw)
if row.purpose~=ARGV[1] then return '' end
redis.call('DEL',KEYS[1])
return raw
"""


class OTPStore:
    def __init__(self, settings):
        self.client = None
        if settings.otp_redis_url:
            try:
                self.client = Redis.from_url(
                    settings.otp_redis_url.get_secret_value(),
                    decode_responses=True,
                    socket_connect_timeout=3,
                    socket_timeout=3,
                    retry=Retry(NoBackoff(), 0),
                    max_connections=20,
                )
            except (ValueError, RedisError):
                pass  # Never expose a credential-bearing URL.

    def run(self, script, keys, args):
        if self.client is None:
            raise APIError(503, "OTP_NOT_CONFIGURED", "Chưa cấu hình Redis cho OTP")
        try:
            return self.client.eval(script, len(keys), *keys, *args)
        except RedisError as exc:
            raise APIError(503, "OTP_UNAVAILABLE", "Chức năng OTP chưa sẵn sàng") from exc

    @staticmethod
    def key(challenge_id):
        return PREFIX + "challenge:" + str(challenge_id)

    def issue(self, challenge_id, row, target_key, ip_key):
        keys = [
            self.key(challenge_id),
            PREFIX + "active:" + target_key,
            PREFIX + "target:" + target_key,
            PREFIX + "ip:" + ip_key,
            PREFIX + "cooldown:" + target_key,
        ]
        if not self.run(ISSUE, keys, [json.dumps(row)]):
            raise APIError(429, "RATE_LIMITED", "Vui lòng đợi trước khi yêu cầu mã mới")

    def delivered(self, challenge_id, success):
        self.run(DELIVERED, [self.key(challenge_id)], ["1" if success else "0"])

    def consume(self, challenge_id, digest):
        raw = self.run(CONSUME, [self.key(challenge_id)], [digest])
        if not raw:
            raise APIError(400, "OTP_INVALID", "Mã không đúng, đã hết hạn hoặc đã được sử dụng")
        return json.loads(raw)

    def grant(self, digest, row):
        # Server-generated 256-bit bearer token is never stored verbatim.
        self.run(
            "return redis.call('SET',KEYS[1],ARGV[1],'EX',300,'NX')",
            [PREFIX + "grant:" + digest],
            [json.dumps(row)],
        )

    def consume_grant(self, digest, purpose):
        raw = self.run(CONSUME_GRANT, [PREFIX + "grant:" + digest], [purpose])
        if not raw:
            raise APIError(
                400, "OTP_INVALID", "Xác minh đã hết hạn hoặc đã dùng. Vui lòng lấy mã mới"
            )
        return json.loads(raw)

    def ready(self):
        if self.client is None:
            return False
        try:
            return bool(self.client.ping())
        except RedisError:
            return False

    def close(self):
        if self.client:
            self.client.close()

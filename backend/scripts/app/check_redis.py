# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

import asyncio
import os

from dotenv import load_dotenv

load_dotenv()

async def check_redis():
    redis_url = os.environ.get('REDIS_URL', '')
    print(f"Redis URL configured: {'YES' if redis_url else 'NO'}")

    try:
        import redis.asyncio as aioredis
        # Upstash requires TLS - ensure rediss:// not redis://
        tls_url = redis_url.replace('redis://', 'rediss://', 1) if redis_url.startswith('redis://') else redis_url
        print(f'Using TLS URL: {tls_url[:40]}...')
        client = aioredis.from_url(tls_url, decode_responses=True, ssl_cert_reqs=None)

        # Test ping
        pong = await client.ping()
        print(f"Ping: {pong}")

        # Test set/get
        await client.set("test_key", "SafeVixAI_alive", ex=60)
        val = await client.get("test_key")
        print(f"Set/Get test: {val}")

        # Check memory info
        info = await client.info("memory")
        print(f"Used memory: {info.get('used_memory_human', 'N/A')}")

        await client.aclose()
        print("\nREDIS STATUS: FULLY OPERATIONAL")

    except Exception as e:
        print(f"\nREDIS ERROR: {type(e).__name__}: {e}")

asyncio.run(check_redis())

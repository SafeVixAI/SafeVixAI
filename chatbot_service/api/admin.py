# SPDX-License-Identifier: MIT
# Copyright (c) 2026 SafeVixAI Team

from __future__ import annotations

import html as _html

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from fastapi.responses import HTMLResponse

from agent.graph import ChatEngine
from config import get_settings
from core.queue import TaskQueue, task

# S18: Import limiter for per-IP rate limiting on admin endpoints (5/min)
from limiter import limiter
from memory.redis_memory import ConversationMemoryStore

router = APIRouter(tags=['Admin'])


def get_engine(request: Request) -> ChatEngine:
    return request.app.state.chat_engine


def get_memory(request: Request) -> ConversationMemoryStore:
    return request.app.state.memory_store


def _require_admin(x_admin_key: str = Header(default='')) -> None:
    """Validate admin API key from X-Admin-Key header (constant-time compare)."""
    import hmac
    secret = get_settings().admin_secret
    if not secret:
        raise HTTPException(status_code=503, detail='Admin endpoint is disabled (ADMIN_SECRET not configured).')
    # P0-06: Use hmac.compare_digest to prevent timing side-channel attacks (audit H7)
    if not hmac.compare_digest(x_admin_key, secret):
        raise HTTPException(status_code=403, detail='Invalid admin key.')


@router.get('/admin/health')
@limiter.limit('5/minute')
async def health(
    request: Request,  # noqa
    _: None = Depends(_require_admin),
    engine: ChatEngine = Depends(get_engine),
    memory_store: ConversationMemoryStore = Depends(get_memory),
) -> dict:
    index = await engine.stats()
    return {
        'status': 'ok',
        'chunks': index.get('chunks', 0),
        'categories': index.get('categories', 0),
        'chroma_chunks': index.get('chroma_chunks', 0),
        'embedding_model': index.get('embedding_model'),
        'memory_backend': memory_store.backend_name,
        'memory_available': await memory_store.ping(),
    }


@router.post('/admin/rebuild-index')
@limiter.limit('5/minute')
async def rebuild_index(
    request: Request,
    _: None = Depends(_require_admin),
    engine: ChatEngine = Depends(get_engine),
) -> dict:
    queue = getattr(request.app.state, "queue", None)
    if queue is not None:
        job_id = await queue.enqueue("rebuild_rag_index")
        return {
            'status': 'queued',
            'job_id': job_id,
            'message': 'RAG index rebuild triggered in background. Poll /admin/jobs/{job_id} for progress.'
        }
    stats = await engine.rebuild_index()
    return {'status': 'rebuilt', 'index': stats}


@router.get('/admin/jobs/{job_id}')
@limiter.limit('10/minute')
async def get_job_status(
    job_id: str,
    request: Request,
    _: None = Depends(_require_admin),
) -> dict:
    queue = getattr(request.app.state, "queue", None)
    if queue is None:
        raise HTTPException(status_code=503, detail="Task queue not active.")
    job = await queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return job.to_dict()


@router.get('/admin/providers/health')
@limiter.limit('5/minute')
async def provider_health(
    request: Request,  # noqa
    _: None = Depends(_require_admin),
    engine: ChatEngine = Depends(get_engine),
) -> dict:
    import asyncio
    import time

    from providers.base import ProviderRequest

    provider_router = engine.provider_router
    matrix = {}

    async def ping_provider(name: str, provider) -> tuple[str, dict]:
        if provider_router._provider_unavailable(name):
            return name, {'status': 'disabled', 'latency_ms': None, 'error': 'Circuit breaker open'}

        if name == 'template':
            return name, {'status': 'healthy', 'latency_ms': 0, 'error': None}

        start = time.time()
        try:
            req = ProviderRequest(message="Health check ping", history=[], intent="general")
            # Ping with a short timeout
            await asyncio.wait_for(provider.generate(req), timeout=5.0)
            latency = int((time.time() - start) * 1000)
            return name, {'status': 'healthy', 'latency_ms': latency, 'error': None}
        except Exception as e:
            return name, {'status': 'error', 'latency_ms': None, 'error': str(e)}

    # Deduplicate actual provider instances so we don't ping 'sarvam' and 'sarvam_30b' twice if they share the same backend,
    # but the simplest is just to ping all configured keys.
    tasks = [ping_provider(name, provider) for name, provider in provider_router.providers.items()]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for res in results:
        if isinstance(res, tuple):  # pragma: no branch
            matrix[res[0]] = res[1]

    return {'status': 'completed', 'providers': matrix}


@router.get('/admin/providers/dashboard')
@limiter.limit('5/minute')
async def provider_health_dashboard(
    request: Request,  # noqa
    _: None = Depends(_require_admin),
    engine: ChatEngine = Depends(get_engine),
    memory_store: ConversationMemoryStore = Depends(get_memory),
) -> HTMLResponse:
    """C11: Provider health dashboard UI — renders provider status as HTML."""
    import asyncio
    import time

    from providers.base import ProviderRequest

    provider_router = engine.provider_router
    matrix = {}

    async def ping_provider(name: str, provider) -> tuple[str, dict]:
        if provider_router._provider_unavailable(name):
            return name, {'status': 'disabled', 'latency_ms': None, 'error': 'Circuit breaker open'}
        if name == 'template':
            return name, {'status': 'healthy', 'latency_ms': 0, 'error': None}
        start = time.time()
        try:
            req = ProviderRequest(message="Health check", history=[], intent="general")
            await asyncio.wait_for(provider.generate(req), timeout=5.0)
            latency = int((time.time() - start) * 1000)
            return name, {'status': 'healthy', 'latency_ms': latency, 'error': None}
        except Exception as e:
            return name, {'status': 'error', 'latency_ms': None, 'error': str(e)[:100]}

    tasks = [ping_provider(name, provider) for name, provider in provider_router.providers.items()]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    for res in results:
        if isinstance(res, tuple):  # pragma: no branch
            matrix[res[0]] = res[1]

    memory_ok = await memory_store.ping()
    cache = getattr(engine.provider_router, 'cache', None)
    cache_ok = await cache.ping() if cache else False

    healthy_count = sum(1 for v in matrix.values() if v['status'] == 'healthy')
    error_count = sum(1 for v in matrix.values() if v['status'] == 'error')
    disabled_count = sum(1 for v in matrix.values() if v['status'] == 'disabled')

    rows = []
    for name, info in matrix.items():
        status = info['status']
        color = '#22c55e' if status == 'healthy' else ('#ef4444' if status == 'error' else '#f59e0b')
        latency = f"{info['latency_ms']}ms" if info['latency_ms'] is not None else '—'
        error = info['error'] or '—'
        rows.append(
            f'<tr>'
            f'<td class="name">{_html.escape(name)}</td>'
            f'<td class="status" style="color:{color}">{status.upper()}</td>'
            f'<td class="latency">{latency}</td>'
            f'<td class="error" title="{_html.escape(error)}">{_html.escape(error[:60])}</td>'
            f'</tr>'
        )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SafeVixAI — Provider Health Dashboard</title>
<style>
  body {{ font-family: system-ui, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; background: #0f172a; color: #e2e8f0; }}
  h1 {{ color: #38bdf8; }}
  .summary {{ display: flex; gap: 1rem; margin: 1rem 0; }}
  .card {{ flex: 1; padding: 1rem; border-radius: 8px; text-align: center; }}
  .card.healthy {{ background: #166534; }}
  .card.error {{ background: #991b1b; }}
  .card.disabled {{ background: #78350f; }}
  .card .num {{ font-size: 2rem; font-weight: bold; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; }}
  th, td {{ padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid #334155; }}
  th {{ color: #94a3b8; font-size: 0.85rem; text-transform: uppercase; }}
  .name {{ font-weight: 600; }}
  .status {{ font-weight: 700; }}
  .latency {{ font-family: monospace; }}
  .error {{ font-size: 0.85rem; color: #94a3b8; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
  .meta {{ margin-top: 1rem; font-size: 0.85rem; color: #94a3b8; }}
  .meta span {{ margin-right: 1.5rem; }}
  .dot {{ display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 4px; }}
</style>
</head>
<body>
<h1>🟢 SafeVixAI Provider Health Dashboard</h1>
<div class="summary">
  <div class="card healthy"><div class="num">{healthy_count}</div>Healthy</div>
  <div class="card error"><div class="num">{error_count}</div>Errors</div>
  <div class="card disabled"><div class="num">{disabled_count}</div>Disabled</div>
</div>
<div class="meta">
  <span><span class="dot" style="background:{'#22c55e' if memory_ok else '#ef4444'}"></span>Memory: {memory_store.backend_name}</span>
  <span><span class="dot" style="background:{'#22c55e' if cache_ok else '#ef4444'}"></span>LLM Cache: {'Redis' if cache_ok else 'Disabled'}</span>
</div>
<table>
<tr><th>Provider</th><th>Status</th><th>Latency</th><th>Error</th></tr>
{''.join(rows)}
</table>
<p class="meta">Auto-refreshes every 30s. Last check: {time.strftime('%H:%M:%S UTC', time.gmtime())}</p>
<script>setTimeout(() => location.reload(), 30000);</script>
</body>
</html>"""
    return HTMLResponse(content=html)


@task("rebuild_rag_index")
async def rebuild_rag_index_task(q: TaskQueue, job_id: str):  # noqa
    import logging

    from core.queue import get_global_chat_engine
    engine = get_global_chat_engine()
    if not engine:
        msg = "ChatEngine is not initialized globally."
        raise ValueError(msg)
    logger = logging.getLogger("safevixai.chatbot.tasks")
    logger.info("Starting background RAG index rebuild...")
    stats = await engine.rebuild_index()
    logger.info("Background RAG index rebuild completed successfully.")
    return stats


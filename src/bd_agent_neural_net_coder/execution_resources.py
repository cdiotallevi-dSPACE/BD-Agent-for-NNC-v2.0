"""Scoped resources; never share async transports between event loops."""
import asyncio
import hashlib
import json
from contextlib import AsyncExitStack, asynccontextmanager
from contextvars import ContextVar
from functools import wraps

import httpx

_pool = ContextVar("bda_http_pool", default=None)
_tasks = ContextVar("bda_provider_tasks", default=None)


def provider_task_scope(fn):
    @wraps(fn)
    async def wrapped(*args, **kwargs):
        tasks = []
        token = _tasks.set(tasks)
        try:
            return await fn(*args, **kwargs)
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            _tasks.reset(token)
    return wrapped


def provider_task(coroutine):
    task = asyncio.create_task(coroutine)
    _tasks.get().append(task)
    return task


def http_scope(fn):
    @wraps(fn)
    async def wrapped(*args, **kwargs):
        if _pool.get() is not None:
            return await fn(*args, **kwargs)
        async with AsyncExitStack() as stack:
            token = _pool.set((stack, {}))
            try:
                return await fn(*args, **kwargs)
            finally:
                _pool.reset(token)
    return wrapped


@asynccontextmanager
async def pooled_client(namespace, **kwargs):
    state = _pool.get()
    if state is None:
        async with httpx.AsyncClient(**kwargs) as client:
            yield client
        return
    stack, clients = state
    # Include all transport/security settings. Never log this key (headers may
    # contain credentials). Namespace separates provider cookie/auth sessions.
    key = (namespace, repr(sorted(kwargs.items())))
    if key not in clients:
        clients[key] = await stack.enter_async_context(httpx.AsyncClient(**kwargs))
    yield clients[key]


async def ordered_downloads(items, download, concurrency):
    """Bounded workers plus a bounded reorder window; yield in input order.

    Window=2*concurrency keeps a slow request from blocking the whole next batch,
    without buffering every full PDF. Budget decisions belong to the consumer.
    """
    concurrency = max(1, concurrency)
    semaphore = asyncio.Semaphore(concurrency)
    pending = {}
    iterator = iter(enumerate(items))

    async def one(item):
        async with semaphore:
            return await download(item)

    def fill():
        while len(pending) < concurrency * 2:
            try:
                index, item = next(iterator)
            except StopIteration:
                break
            pending[index] = asyncio.create_task(one(item))

    try:
        fill()
        for index in range(len(items)):
            value = await pending.pop(index)
            fill()
            yield value
    finally:
        for task in pending.values():
            task.cancel()
        await asyncio.gather(*pending.values(), return_exceptions=True)


def pdf_hashes(payload):
    """Keep historical hex-text digest byte-for-byte while adding raw SHA256.

    Incremental hex blocks avoid a whole-payload hex string and UTF-8 copy.
    Existing content_hash consumers retain historical deduplication semantics.
    """
    legacy = hashlib.sha256()
    raw = hashlib.sha256()
    view = memoryview(payload)
    for start in range(0, len(view), 65536):
        block = view[start:start + 65536]
        raw.update(block)
        legacy.update(block.hex().encode("ascii"))
    return {"content_hash": "sha256:" + legacy.hexdigest(),
            "content_hash_encoding": "hex-text-sha256-v1",
            "raw_content_hash": "sha256:" + raw.hexdigest()}


def bounded_page_text(pages, limit=2_000_000):
    """Equivalent to ' '.join(page texts)[:limit] without a huge intermediate."""
    parts = []
    remaining = limit
    for index, page in enumerate(pages):
        if index and remaining:
            parts.append(" ")
            remaining -= 1
        text = page["text"][:remaining]
        parts.append(text)
        remaining -= len(text)
        if not remaining:
            break
    return "".join(parts)

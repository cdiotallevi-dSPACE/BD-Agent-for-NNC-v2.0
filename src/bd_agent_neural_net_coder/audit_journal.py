"""Durable discovery deltas with backward-compatible periodic JSON snapshots.

Each update is appended, flushed and fsynced before acknowledgment. Snapshots
checkpoint every ten updates or five seconds (on activity), and on scope exit.
After hard termination replay the journal; only a torn LAST line is ignored.
"""
import json
import os
import time
from contextvars import ContextVar
from functools import wraps
from pathlib import Path
from .core import atomic_json

TRACKED = {"search_execution.json", "provider_results.json", "search_queries.json"}
_journal = ContextVar("bda_audit_journal", default=None)


class DiscoveryJournal:
    def __init__(self, out):
        self.out = Path(out)
        self.path = self.out / "discovery_events.jsonl"
        self.stream = self.path.open("x", encoding="utf-8")
        self.state = {}
        self.serialized = {}
        self.sequence = 0
        self.updates = 0
        self.last_checkpoint = time.monotonic()

    def append(self, event):
        self.sequence += 1
        self.stream.write(json.dumps({"sequence": self.sequence, **event}, ensure_ascii=True) + "\n")
        self.stream.flush()
        os.fsync(self.stream.fileno())

    def update(self, name, data):
        changes = []
        old = self.serialized.get(name, {})
        lengths = {}
        for field, rows in data.items():
            lengths[field] = len(rows)
            previous = old.get(field, [])
            current = [json.dumps(row, sort_keys=True, ensure_ascii=True) for row in rows]
            for index, value in enumerate(current):
                if index >= len(previous) or previous[index] != value:
                    changes.append({"field": field, "index": index, "value": json.loads(value)})
        event = {"kind": "update", "file": name, "lengths": lengths, "changes": changes}
        if not changes and name in self.state and all(len(self.state[name].get(k, [])) == n for k, n in lengths.items()):
            return
        self.append(event)
        _apply(self.state, event)
        self.serialized[name] = {key: [json.dumps(row, sort_keys=True, ensure_ascii=True) for row in rows] for key, rows in self.state[name].items()}
        self.updates += 1
        if self.updates >= 10 or time.monotonic() - self.last_checkpoint >= 5:
            self.checkpoint()

    def checkpoint(self):
        for name, data in self.state.items():
            atomic_json(self.out / name, data)
        self.updates = 0
        self.last_checkpoint = time.monotonic()


def _apply(state, event):
    if event.get("kind") != "update":
        return
    target = state.setdefault(event["file"], {})
    for field, length in event["lengths"].items():
        target.setdefault(field, [])
        target[field] = (target[field] + [None] * max(0, length - len(target[field])))[:length]
    for change in event["changes"]:
        target[change["field"]][change["index"]] = change["value"]


def replay_journal(path):
    state = {}
    with Path(path).open(encoding="utf-8") as stream:
        for line in stream:
            if not line.endswith("\n"):
                break  # uncommitted final write after a hard interruption
            _apply(state, json.loads(line))
    return state


def journaled_json(path, data):
    journal = _journal.get()
    path = Path(path)
    if journal is not None and path.parent == journal.out and path.name in TRACKED:
        journal.update(path.name, data)
    else:
        atomic_json(path, data)


def audit_event(event):
    journal = _journal.get()
    if journal is not None:
        journal.append(event)


def discovery_audit(fn):
    @wraps(fn)
    async def wrapped(root, out, *args, **kwargs):
        journal = DiscoveryJournal(out)
        token = _journal.set(journal)
        completed = False
        try:
            result = await fn(root, out, *args, **kwargs)
            completed = True
            return result
        finally:
            try:
                journal.checkpoint()
                journal.append({"kind": "discovery_finished" if completed else "discovery_interrupted"})
            finally:
                journal.stream.close()
                _journal.reset(token)
    return wrapped

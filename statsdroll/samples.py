"""固定场景，用来复现题面里的锚点。"""

import json

from . import core


def _line(obj):
    print(json.dumps(obj, ensure_ascii=False))


def run(name):
    if name == "rate":
        store = core.Store(10)
        store.feed("hits:10|c|@0.5", 0, core.Counter())
        out = store.flush(0, core.Counter())
        _line({"sum": out["hits"]["sum"]})
        return 0
    if name == "gauge":
        store = core.Store(10)
        store.feed("mem:10|g", 0, core.Counter())
        store.feed("mem:20|g", 0, core.Counter())
        out = store.flush(0, core.Counter())
        _line({"sum": out["mem"]["sum"]})
        return 0
    if name == "window":
        store = core.Store(10)
        store.feed("hits:1|c", 0, core.Counter())
        store.feed("hits:5|c", 100, core.Counter())
        out = store.flush(100, core.Counter())
        _line({"sum": out["hits"]["sum"]})
        return 0
    if name == "idem":
        store = core.Store(10)
        store.feed("hits:3|c", 0, core.Counter())
        first = store.flush(0, core.Counter())["hits"]["sum"]
        second = store.flush(0, core.Counter())["hits"]["sum"]
        _line({"first": first, "second": second})
        return 0
    if name == "work":
        store = core.Store(10)
        for i in range(2000):
            store.feed("m%04d:1|c" % i, 0, core.Counter())
        counter = core.Counter()
        for _ in range(2000):
            store.flush(0, counter)
        _line({"samples": 2000, "scanned": counter.scanned})
        return 0
    raise SystemExit("未知场景：" + name)

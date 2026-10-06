"""解析指标行并按窗口汇总。"""

from collections import deque


class Counter:
    """记录处理的样本条数。"""

    def __init__(self):
        self.scanned = 0


def parse_line(line, counter):
    counter.scanned += 1
    line = line.strip()
    if not line or ":" not in line or "|" not in line:
        return None
    head, _, rest = line.partition("|")
    name, _, raw = head.partition(":")
    parts = rest.split("|")
    mtype = parts[0].strip()
    if mtype not in ("c", "g", "ms"):
        return None
    rate = 1.0
    for part in parts[1:]:
        if part.startswith("@"):
            try:
                rate = float(part[1:])
            except ValueError:
                return None
    try:
        value = float(raw)
    except ValueError:
        return None
    if rate <= 0:
        return None
    return name.strip(), value, mtype, rate


def _new_state():
    return {"count": 0, "sum": 0.0, "max": 0.0, "values": deque()}


class Store:
    def __init__(self, window):
        self.window = window
        self.samples = deque()
        self.totals = {}
        self._pending = 0

    def feed(self, line, now, counter):
        parsed = parse_line(line, counter)
        if parsed is None:
            return
        name, value, mtype, rate = parsed
        self.samples.append(
            {"name": name, "value": value, "type": mtype, "rate": rate, "now": now, "state": "new"}
        )
        self._pending += 1

    def _adjusted(self, s):
        if s["type"] == "c":
            return s["value"] / s["rate"]
        return s["value"]

    def _add(self, s, counter):
        counter.scanned += 1
        st = self.totals.setdefault(s["name"], _new_state())
        v = self._adjusted(s)
        st["count"] += 1
        st["values"].append(v)
        if s["type"] == "g":
            st["sum"] = v
            st["max"] = v
        else:
            st["sum"] += v
            st["max"] = max(st["max"], v)

    def _remove(self, s):
        st = self.totals.get(s["name"])
        if st is None:
            return
        v = self._adjusted(s)
        st["count"] -= 1
        st["values"].popleft()
        if s["type"] == "g":
            last = st["values"][-1] if st["values"] else 0.0
            st["sum"] = last
            st["max"] = last
        else:
            st["sum"] -= v
            if not st["values"]:
                st["max"] = 0.0
            elif v >= st["max"]:
                st["max"] = max(st["values"])
        if st["count"] <= 0:
            del self.totals[s["name"]]

    def flush(self, now, counter):
        cutoff = now - self.window
        while self.samples and self.samples[0]["now"] < cutoff:
            old = self.samples.popleft()
            if old["state"] == "new":
                self._pending -= 1
            elif old["state"] == "added":
                self._remove(old)
        while self._pending:
            s = self.samples[len(self.samples) - self._pending]
            self._pending -= 1
            if s["now"] < cutoff:
                s["state"] = "skipped"
                continue
            s["state"] = "added"
            self._add(s, counter)
        return {
            name: {"count": st["count"], "sum": st["sum"], "max": st["max"]}
            for name, st in self.totals.items()
        }

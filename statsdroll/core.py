"""解析指标行并按窗口汇总。"""


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


class Store:
    def __init__(self, window):
        self.window = window
        self.samples = []
        self.totals = {}

    def feed(self, line, now, counter):
        parsed = parse_line(line, counter)
        if parsed is None:
            return
        name, value, mtype, rate = parsed
        self.samples.append({"name": name, "value": value, "type": mtype, "rate": rate, "now": now})

    def flush(self, now, counter):
        for s in self.samples:
            counter.scanned += 1
            cur = self.totals.setdefault(s["name"], {"count": 0, "sum": 0.0, "max": 0.0})
            cur["count"] += 1
            cur["sum"] += s["value"]
            cur["max"] = max(cur["max"], s["value"])
        return {name: dict(agg) for name, agg in self.totals.items()}

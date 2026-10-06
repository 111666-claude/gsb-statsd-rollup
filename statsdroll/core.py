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


class _Metric:
    """单个指标在当前窗口内的增量汇总状态。"""

    def __init__(self, mtype):
        self.mtype = mtype
        self.buf = deque()
        self.sum = 0.0
        self.maxdq = deque()

    def add(self, when, value):
        self.buf.append((when, value))
        self.sum += value
        while self.maxdq and self.maxdq[-1] < value:
            self.maxdq.pop()
        self.maxdq.append(value)

    def expire(self, cutoff, counter):
        while self.buf and self.buf[0][0] < cutoff:
            counter.scanned += 1
            _, value = self.buf.popleft()
            self.sum -= value
            if self.maxdq and self.maxdq[0] == value:
                self.maxdq.popleft()

    def snapshot(self):
        if not self.buf:
            return None
        count = len(self.buf)
        if self.mtype == "g":
            last = self.buf[-1][1]
            return {"count": count, "sum": last, "max": last}
        return {"count": count, "sum": self.sum, "max": self.maxdq[0]}


class Store:
    def __init__(self, window):
        self.window = window
        self.pending = []
        self.metrics = {}

    def feed(self, line, now, counter):
        parsed = parse_line(line, counter)
        if parsed is None:
            return
        name, value, mtype, rate = parsed
        self.pending.append((now, name, value, mtype, rate))

    def flush(self, now, counter):
        cutoff = now - self.window
        for metric in self.metrics.values():
            metric.expire(cutoff, counter)
        pending = self.pending
        self.pending = []
        for when, name, value, mtype, rate in pending:
            counter.scanned += 1
            if when < cutoff:
                continue
            metric = self.metrics.get(name)
            if metric is None:
                metric = self.metrics[name] = _Metric(mtype)
            metric.add(when, value / rate if mtype == "c" else value)
        out = {}
        for name, metric in self.metrics.items():
            snap = metric.snapshot()
            if snap is not None:
                out[name] = snap
        return out

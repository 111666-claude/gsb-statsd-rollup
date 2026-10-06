# statsd-rollup

按时间窗口汇总 statsd 指标行：计数器、仪表、计时器，带采样率修正与幂等读取。只用 Python 标准库。

```
python3 -m unittest discover -s tests
python3 -m statsdroll --sample=rate
python3 -m statsdroll --sample=gauge
python3 -m statsdroll --sample=window
python3 -m statsdroll --sample=idem
python3 -m statsdroll --sample=work
```

## 口径

- **采样率**：计数器按 `@rate` 修正，计入的是实际值除以采样率。
- **仪表**：同一窗口内取最后一个值；它的汇总值就是最后那个值。
- **计时器**：累加条数与和，取最大值。
- **窗口**：只汇总当前时刻往前一个窗口内的样本，更早的不算。
- **幂等**：没有新样本时重复读取同一时刻，结果一致。

## 不变量

- 汇总结果的条数等于窗口内该指标的样本数。
- 重复读取不改变已汇总的数字。
- `scanned` 不随样本数乘读取次数放大：两千个样本读两千次的 `scanned` 不超过 6000。

## 输出契约

每个指标汇总为 `{"count": N, "sum": X, "max": Y}`；场景打印一行 JSON。
`--sample=work` 打印 `{"samples": N, "scanned": N}`。

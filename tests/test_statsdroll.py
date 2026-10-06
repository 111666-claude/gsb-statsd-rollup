import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from statsdroll import core


class StatsdrollTest(unittest.TestCase):
    def test_counter_sum(self):
        store = core.Store(10)
        store.feed("hits:3|c", 0, core.Counter())
        self.assertEqual(store.flush(0, core.Counter())["hits"]["sum"], 3)

    def test_counter_count(self):
        store = core.Store(10)
        store.feed("hits:1|c", 0, core.Counter())
        store.feed("hits:2|c", 0, core.Counter())
        self.assertEqual(store.flush(0, core.Counter())["hits"]["count"], 2)

    def test_flush_empty(self):
        self.assertEqual(core.Store(10).flush(0, core.Counter()), {})

    def test_invalid_line_ignored(self):
        store = core.Store(10)
        store.feed("garbage", 0, core.Counter())
        self.assertEqual(store.flush(0, core.Counter()), {})

    def test_timer_max(self):
        store = core.Store(10)
        store.feed("t:5|ms", 0, core.Counter())
        store.feed("t:7|ms", 0, core.Counter())
        self.assertEqual(store.flush(0, core.Counter())["t"]["max"], 7)

    def test_counter_counts(self):
        counter = core.Counter()
        core.parse_line("hits:1|c", counter)
        self.assertGreater(counter.scanned, 0)


if __name__ == "__main__":
    unittest.main()

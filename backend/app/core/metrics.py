from collections import defaultdict
import time

REQUEST_COUNT = defaultdict(int)
REQUEST_LATENCY = defaultdict(int)
ERROR_COUNT = defaultdict(int)
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class Bench:
    pre: list[float] = field(default_factory=list)
    inf: list[float] = field(default_factory=list)
    post: list[float] = field(default_factory=list)
    total: list[float] = field(default_factory=list)
    mem: Optional[float] = None

    def to_dict(self) -> Dict:
        def avg(x):
            return round((sum(x) / len(x)) * 1000, 1) if x else 0
        return {
            "avg_preprocessing_ms": avg(self.pre),
            "avg_inference_ms": avg(self.inf),
            "avg_postprocessing_ms": avg(self.post),
            "avg_total_ms": avg(self.total),
            "throughput_fps": round(len(self.total) / sum(self.total), 1) if sum(self.total) > 0 else 0,
            "peak_memory_mb": round(self.mem, 1) if self.mem else None,
        }


def now():
    return time.perf_counter()

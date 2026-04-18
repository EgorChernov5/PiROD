from multiprocessing import RawArray
from itertools import repeat
from concurrent.futures import ProcessPoolExecutor
import math


def find_outliers(chunk: list[float], mean: float, threshold: float) -> list[float]:
    return [x for x in chunk if abs(x - mean) > threshold]


_shared_values = None


def _init_shared_values(shared_values):
    global _shared_values
    _shared_values = shared_values


def _sum_range(bounds: tuple[int, int]) -> float:
    start, end = bounds
    return sum(_shared_values[idx] for idx in range(start, end))


def _sum_sq_range(bounds: tuple[int, int], mean: float) -> float:
    start, end = bounds
    return sum((_shared_values[idx] - mean) ** 2 for idx in range(start, end))


def _find_outliers_range(bounds: tuple[int, int], mean: float, threshold: float) -> list[float]:
    start, end = bounds
    return [
        _shared_values[idx]
        for idx in range(start, end)
        if abs(_shared_values[idx] - mean) > threshold
    ]


def sequential_catch_outliers(values: list[float], k: float) -> list[float]:
    mean_values = sum(values) / len(values)
    std_values = math.sqrt(
        sum((x - mean_values) ** 2 for x in values) / len(values))
    threshold = k*std_values

    return find_outliers(values, mean_values, threshold)


def parallel_catch_outliers(values: list[float], k: float, workers: int = 4) -> list[float]:
    shared_values = RawArray("d", values)
    chunk_size = max(1, math.ceil(len(values) / workers))
    ranges = [
        (start, min(start + chunk_size, len(values)))
        for start in range(0, len(values), chunk_size)
    ]

    with ProcessPoolExecutor(
        max_workers=workers,
        initializer=_init_shared_values,
        initargs=(shared_values,),
    ) as executor:
        mean_values = sum(executor.map(_sum_range, ranges)) / len(values)
        std_values = math.sqrt(
            sum(executor.map(_sum_sq_range, ranges, repeat(mean_values))) / len(values)
        )
        threshold = k*std_values
        results = executor.map(
            _find_outliers_range,
            ranges,
            repeat(mean_values),
            repeat(threshold),
        )

    outliers = []
    for part in results:
        outliers.extend(part)

    return outliers

from itertools import repeat
from concurrent.futures import ProcessPoolExecutor
import math


def find_outliers(chunk: list[float], mean: float, threshold: float) -> list[float]:
    return [x for x in chunk if abs(x - mean) > threshold]


def squential_catch_outliers(values: list[float], k: float) -> list[float]:
    mean_values = sum(values) / len(values)
    std_values = math.sqrt(
        sum((x - mean_values) ** 2 for x in values) / len(values))
    threshold = k*std_values

    with ProcessPoolExecutor(max_workers=1) as executor:
        results = executor.map(find_outliers, [values],
                               repeat(mean_values), repeat(threshold))

    outliers = []
    for part in results:
        outliers.extend(part)

    return outliers


def parallel_catch_outliers(values: list[float], k: float, workers: int = 4) -> list[float]:
    mean_values = sum(values) / len(values)
    std_values = math.sqrt(
        sum((x - mean_values) ** 2 for x in values) / len(values))
    threshold = k*std_values

    chunk_size = max(1, math.ceil(len(values) / workers))
    chunks = [values[i:i + chunk_size]
              for i in range(0, len(values), chunk_size)]

    with ProcessPoolExecutor(max_workers=workers) as executor:
        results = executor.map(find_outliers, chunks,
                               repeat(mean_values), repeat(threshold))

    outliers = []
    for part in results:
        outliers.extend(part)

    return outliers

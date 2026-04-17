import random
from tqdm import tqdm
from time import perf_counter
from pathlib import Path
import os
import json

from outliers_catchers import squential_catch_outliers, parallel_catch_outliers
from visualizator import plot_line_graph


def generate_random_floats(values_size: int, random_seed: int = 42) -> list[float]:
    random.seed(random_seed)
    return [random.uniform(-1000.0, 1000.0) for _ in range(values_size)]


def compare_outliers_catchers(values: list[float], k: float, workers: int = 4, save_path: Path | None = None):
    start_time = perf_counter()
    squential_catch_outliers(values, k)
    sequential_time = perf_counter() - start_time

    start_time = perf_counter()
    parallel_catch_outliers(values, k, workers)
    parallel_time = perf_counter() - start_time

    speedup = sequential_time / parallel_time
    efficiency = speedup / workers

    if save_path:
        metrics = {
            "len_values": len(values),
            "k": k,
            "workers": workers,
            "sequential_time": sequential_time,
            "parallel_time": parallel_time,
            "speedup": speedup,
            "efficiency": efficiency
        }
        if os.path.exists(str(save_path)):
            with open(str(save_path), "r") as f:
                data = json.load(f)

            new_idx = int(max(data.keys(), key=lambda k: int(k)))
            new_data = {
                new_idx + 1: metrics
            }
            data.update(new_data)
        else:
            data = {
                "0": metrics
            }

        with open(str(save_path), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    else:
        print(f"Sequential time: {sequential_time:.6f} s")
        print(f"Parallel time: {parallel_time:.6f} s")
        print(f"Speedup: {speedup:.6f}")
        print(f"Efficiency: {efficiency:.6f}")


def analize_determinism(n, values, k, workers):
    x = []
    y = []
    i = 0
    while i != n:
        start_time = perf_counter()
        parallel_catch_outliers(values, k, workers)
        parallel_time = perf_counter() - start_time
        x.append(i)
        y.append(parallel_time*1000)
        i += 1

    plot_line_graph(
        x, y,
        x_label="Отсчёты",
        y_label="Время исполнения (мс)",
        title="Работа параллельной версии на одинаковых параметрах",
        save_path=Path(__file__).resolve().parent / "artifacts/parallel_catch_outliers.png",
        x_range=(0, max(x)),
        y_range=(min(y) - 100, max(y) + 100)
    )


def evaluate_outliers_catchers(list_values, list_k, list_workers):
    for values in tqdm(list_values):
        for k in list_k:
            for workers in list_workers:
                save_path = Path(__file__).resolve().parent / "artifacts/compare_logs.json"
                compare_outliers_catchers(values, k, workers, save_path)


if __name__ == "__main__":
    random_seed=42

    # 3 пункт
    # values = generate_random_floats(100000, random_seed)
    # k = 0.2
    # workers = 4
    # compare_outliers_catchers(values, k, workers)
    # 4 пункт
    # n = 200
    # values = generate_random_floats(100000, random_seed)
    # k = 0.2
    # workers = 4
    # analize_determinism(n, values, k, workers)
    # 5 пункт
    list_values = [
        generate_random_floats(100000, random_seed),
        generate_random_floats(400000, random_seed),
        generate_random_floats(700000, random_seed),
        generate_random_floats(1000000, random_seed),
        generate_random_floats(1300000, random_seed)
    ]
    list_k = [
        0.2,
        0.7
    ]
    print(f"MAX(CPU) = {os.cpu_count()}")
    list_workers = [1, 2, 3, 4, 5, 6, 7, 8, 16, 32]
    evaluate_outliers_catchers(list_values, list_k, list_workers)

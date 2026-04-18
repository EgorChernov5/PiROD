from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import matplotlib.pyplot as plt


BASE_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = BASE_DIR / "artifacts"
DATA_PATH = ARTIFACTS_DIR / "compare_logs.json"


def load_experiment_data(data_path: Path | str = DATA_PATH) -> list[dict]:
    with Path(data_path).open("r", encoding="utf-8") as file:
        raw_data = json.load(file)

    experiments = []
    for item in raw_data.values():
        experiments.append(
            {
                "len_values": int(item["len_values"]),
                "k": float(item["k"]),
                "workers": int(item["workers"]),
                "sequential_time": float(item["sequential_time"]),
                "parallel_time": float(item["parallel_time"]),
                "speedup": float(item["speedup"]),
                "efficiency": float(item["efficiency"]),
            }
        )

    return sorted(experiments, key=lambda row: (row["k"], row["len_values"], row["workers"]))


def _prepare_output_dir(output_dir: Path | str = ARTIFACTS_DIR) -> Path:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def _group_by(records: list[dict], *keys: str) -> dict[tuple, list[dict]]:
    grouped: dict[tuple, list[dict]] = defaultdict(list)
    for record in records:
        grouped[tuple(record[key] for key in keys)].append(record)
    return grouped


def plot_line_graph(x, y, x_label, y_label, title, save_path, x_range=None, y_range=None):
    plt.figure(figsize=(8, 5))
    plt.plot(x, y, marker="o", linestyle="-", color="blue", label="Line")

    plt.xlabel(x_label)
    plt.ylabel(y_label)
    plt.title(title)

    if x_range is not None:
        plt.xlim(x_range[0], x_range[1])

    if y_range is not None:
        plt.ylim(y_range[0], y_range[1])

    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig(save_path, format="png", dpi=300, bbox_inches="tight")
    plt.close()


def plot_execution_time_vs_input_size(
    data_path: Path | str = DATA_PATH, output_dir: Path | str = ARTIFACTS_DIR
) -> Path:
    records = load_experiment_data(data_path)
    output_path = _prepare_output_dir(output_dir) / "execution_time_vs_input_size.png"

    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True)
    grouped_by_k = _group_by(records, "k")

    if len(axes) == 1:
        axes = [axes]

    for axis, (k_value, group_records) in zip(axes, sorted(grouped_by_k.items())):
        grouped_by_workers = _group_by(group_records, "workers")
        baseline_records = sorted(grouped_by_workers[(1,)], key=lambda row: row["len_values"])

        axis.plot(
            [row["len_values"] for row in baseline_records],
            [row["sequential_time"] for row in baseline_records],
            marker="o",
            linewidth=2.6,
            label="Sequential baseline",
            color="black",
        )

        for workers, worker_records in sorted(grouped_by_workers.items()):
            worker_count = workers[0]
            sorted_records = sorted(worker_records, key=lambda row: row["len_values"])
            axis.plot(
                [row["len_values"] for row in sorted_records],
                [row["parallel_time"] for row in sorted_records],
                marker="o",
                linewidth=1.8,
                alpha=0.9,
                label=f"Parallel, workers={worker_count}",
            )

        axis.set_title(f"Execution time vs input size, k={k_value}")
        axis.set_xlabel("Number of elements")
        axis.grid(True, alpha=0.3)

    axes[0].set_ylabel("Time, seconds")
    axes[0].legend()
    axes[-1].legend()
    fig.tight_layout()
    fig.savefig(output_path, format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_speedup_vs_workers(
    data_path: Path | str = DATA_PATH, output_dir: Path | str = ARTIFACTS_DIR
) -> Path:
    records = load_experiment_data(data_path)
    output_path = _prepare_output_dir(output_dir) / "speedup_vs_workers.png"

    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True)
    grouped_by_k = _group_by(records, "k")

    if len(axes) == 1:
        axes = [axes]

    for axis, (k_value, group_records) in zip(axes, sorted(grouped_by_k.items())):
        grouped_by_len = _group_by(group_records, "len_values")
        all_workers = sorted({row["workers"] for row in group_records})

        axis.plot(
            all_workers,
            all_workers,
            linestyle="--",
            linewidth=1.5,
            color="gray",
            label="Ideal speedup",
        )
        axis.axhline(1.0, linestyle=":", linewidth=1.5, color="black", label="Sequential baseline")

        for len_values, len_records in sorted(grouped_by_len.items()):
            sorted_records = sorted(len_records, key=lambda row: row["workers"])
            axis.plot(
                [row["workers"] for row in sorted_records],
                [row["speedup"] for row in sorted_records],
                marker="o",
                linewidth=1.8,
                label=f"N={len_values[0]}",
            )

        axis.set_title(f"Speedup vs workers, k={k_value}")
        axis.set_xlabel("Workers")
        axis.grid(True, alpha=0.3)

    axes[0].set_ylabel("Speedup")
    axes[0].legend()
    axes[-1].legend()
    fig.tight_layout()
    fig.savefig(output_path, format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_efficiency_vs_workers(
    data_path: Path | str = DATA_PATH, output_dir: Path | str = ARTIFACTS_DIR
) -> Path:
    records = load_experiment_data(data_path)
    output_path = _prepare_output_dir(output_dir) / "efficiency_vs_workers.png"

    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True)
    grouped_by_k = _group_by(records, "k")

    if len(axes) == 1:
        axes = [axes]

    for axis, (k_value, group_records) in zip(axes, sorted(grouped_by_k.items())):
        grouped_by_len = _group_by(group_records, "len_values")

        axis.axhline(1.0, linestyle=":", linewidth=1.5, color="black", label="Sequential baseline")

        for len_values, len_records in sorted(grouped_by_len.items()):
            sorted_records = sorted(len_records, key=lambda row: row["workers"])
            axis.plot(
                [row["workers"] for row in sorted_records],
                [row["efficiency"] for row in sorted_records],
                marker="o",
                linewidth=1.8,
                label=f"N={len_values[0]}",
            )

        axis.set_title(f"Efficiency vs workers, k={k_value}")
        axis.set_xlabel("Workers")
        axis.grid(True, alpha=0.3)

    axes[0].set_ylabel("Efficiency")
    axes[0].legend()
    axes[-1].legend()
    fig.tight_layout()
    fig.savefig(output_path, format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


def plot_execution_time_vs_workers(
    data_path: Path | str = DATA_PATH, output_dir: Path | str = ARTIFACTS_DIR
) -> Path:
    records = load_experiment_data(data_path)
    output_path = _prepare_output_dir(output_dir) / "execution_time_vs_workers.png"

    fig, axes = plt.subplots(1, 2, figsize=(16, 6), sharey=True)
    grouped_by_k = _group_by(records, "k")

    if len(axes) == 1:
        axes = [axes]

    for axis, (k_value, group_records) in zip(axes, sorted(grouped_by_k.items())):
        grouped_by_len = _group_by(group_records, "len_values")

        for len_values, len_records in sorted(grouped_by_len.items()):
            sorted_records = sorted(len_records, key=lambda row: row["workers"])
            workers = [row["workers"] for row in sorted_records]
            parallel_times = [row["parallel_time"] for row in sorted_records]

            axis.plot(
                workers,
                parallel_times,
                marker="o",
                linewidth=1.8,
                label=f"Parallel, N={len_values[0]}",
            )

            baseline_time = sorted_records[0]["sequential_time"]
            axis.hlines(
                baseline_time,
                min(workers),
                max(workers),
                colors="black",
                linestyles=":",
                linewidth=1.0,
                alpha=0.6,
            )

        axis.plot([], [], color="black", linestyle=":", label="Sequential baseline")
        axis.set_title(f"Execution time vs workers, k={k_value}")
        axis.set_xlabel("Workers")
        axis.grid(True, alpha=0.3)

    axes[0].set_ylabel("Time, seconds")
    axes[0].legend()
    axes[-1].legend()
    fig.tight_layout()
    fig.savefig(output_path, format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


def generate_all_plots(
    data_path: Path | str = DATA_PATH, output_dir: Path | str = ARTIFACTS_DIR
) -> list[Path]:
    return [
        plot_execution_time_vs_input_size(data_path, output_dir),
        plot_speedup_vs_workers(data_path, output_dir),
        plot_efficiency_vs_workers(data_path, output_dir),
        plot_execution_time_vs_workers(data_path, output_dir),
    ]


if __name__ == "__main__":
    generate_all_plots()

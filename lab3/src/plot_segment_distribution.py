from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_FILE = ROOT / "data" / "segment_distribution.csv"
PERCENT_CHART = ROOT / "data" / "segment_distribution_percent.svg"
COUNT_CHART = ROOT / "data" / "segment_distribution_counts.svg"


COLORS = {
    0: "#1f77b4",
    1: "#ff7f0e",
}


def load_data() -> list[dict[str, str]]:
    with DATA_FILE.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def aggregate(rows: list[dict[str, str]]) -> list[dict[str, object]]:
    grouped: dict[str, dict[int, int]] = defaultdict(dict)
    for row in rows:
        grouped[row["table_name"]][int(row["segment_id"])] = int(row["row_count"])

    result = []
    for table_name in sorted(grouped):
        segment_counts = grouped[table_name]
        total = sum(segment_counts.values())
        average = total / len(segment_counts)
        skew_pct = ((max(segment_counts.values()) - min(segment_counts.values())) / average * 100) if average else 0.0
        result.append(
            {
                "table_name": table_name,
                "counts": segment_counts,
                "total": total,
                "skew_pct": skew_pct,
                "percentages": {
                    segment_id: (count / total * 100 if total else 0.0)
                    for segment_id, count in segment_counts.items()
                },
            }
        )
    return result


def svg_header(width: int, height: int) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<style>',
        'text { font-family: Arial, sans-serif; fill: #202124; }',
        '.title { font-size: 22px; font-weight: bold; }',
        '.axis { font-size: 12px; }',
        '.label { font-size: 13px; font-weight: bold; }',
        '.value { font-size: 12px; }',
        '.note { font-size: 11px; fill: #5f6368; }',
        '</style>',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
    ]


def save_svg(path: Path, lines: list[str]) -> None:
    lines.append("</svg>")
    path.write_text("\n".join(lines), encoding="utf-8")


def draw_percent_chart(data: list[dict[str, object]]) -> None:
    width, height = 1100, 520
    margin_left, margin_right, margin_top, margin_bottom = 180, 60, 80, 70
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    group_width = plot_width / len(data)
    bar_width = 46
    max_value = 100

    lines = svg_header(width, height)
    lines.append(f'<text x="{margin_left}" y="40" class="title">Распределение строк по сегментам, %</text>')
    lines.append(
        f'<text x="{margin_left}" y="60" class="note">Для REPLICATED-таблиц показывается доля физических копий строк на каждом сегменте.</text>'
    )

    for tick in range(0, 101, 20):
        y = margin_top + plot_height - (tick / max_value) * plot_height
        lines.append(f'<line x1="{margin_left}" y1="{y:.1f}" x2="{width - margin_right}" y2="{y:.1f}" stroke="#e0e0e0"/>')
        lines.append(f'<text x="{margin_left - 12}" y="{y + 4:.1f}" text-anchor="end" class="axis">{tick}</text>')

    lines.append(
        f'<line x1="{margin_left}" y1="{margin_top + plot_height}" x2="{width - margin_right}" y2="{margin_top + plot_height}" stroke="#202124"/>'
    )

    legend_x = width - 220
    legend_y = 34
    for offset, segment_id in enumerate(sorted(COLORS)):
        y = legend_y + offset * 22
        color = COLORS[segment_id]
        lines.append(f'<rect x="{legend_x}" y="{y - 10}" width="14" height="14" fill="{color}"/>')
        lines.append(f'<text x="{legend_x + 22}" y="{y + 2}" class="axis">segment {segment_id}</text>')

    for index, item in enumerate(data):
        table_name = item["table_name"]
        percentages = item["percentages"]
        skew_pct = item["skew_pct"]
        center_x = margin_left + group_width * index + group_width / 2
        lines.append(
            f'<text x="{center_x}" y="{height - 22}" text-anchor="middle" class="label">{table_name}</text>'
        )
        lines.append(
            f'<text x="{center_x}" y="{height - 6}" text-anchor="middle" class="note">skew={skew_pct:.2f}%</text>'
        )

        segment_ids = sorted(percentages)
        start_x = center_x - (len(segment_ids) * bar_width + (len(segment_ids) - 1) * 18) / 2
        for segment_index, segment_id in enumerate(segment_ids):
            value = percentages[segment_id]
            bar_height = (value / max_value) * plot_height
            x = start_x + segment_index * (bar_width + 18)
            y = margin_top + plot_height - bar_height
            lines.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width}" height="{bar_height:.1f}" fill="{COLORS[segment_id]}"/>'
            )
            lines.append(
                f'<text x="{x + bar_width / 2:.1f}" y="{y - 8:.1f}" text-anchor="middle" class="value">{value:.2f}%</text>'
            )

    save_svg(PERCENT_CHART, lines)


def draw_count_chart(data: list[dict[str, object]]) -> None:
    width, height = 1100, 520
    margin_left, margin_right, margin_top, margin_bottom = 180, 80, 80, 70
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    max_count = max(max(item["counts"].values()) for item in data)
    padded_max = max_count * 1.1
    group_width = plot_width / len(data)
    bar_width = 46

    lines = svg_header(width, height)
    lines.append(f'<text x="{margin_left}" y="40" class="title">Физическое число строк на сегментах</text>')
    lines.append(
        f'<text x="{margin_left}" y="60" class="note">REPLICATED-таблицы целиком присутствуют на каждом сегменте, поэтому их значения совпадают.</text>'
    )

    for fraction in range(0, 6):
        value = padded_max * fraction / 5
        y = margin_top + plot_height - (value / padded_max) * plot_height
        lines.append(f'<line x1="{margin_left}" y1="{y:.1f}" x2="{width - margin_right}" y2="{y:.1f}" stroke="#e0e0e0"/>')
        lines.append(f'<text x="{margin_left - 12}" y="{y + 4:.1f}" text-anchor="end" class="axis">{int(value):,}</text>')

    lines.append(
        f'<line x1="{margin_left}" y1="{margin_top + plot_height}" x2="{width - margin_right}" y2="{margin_top + plot_height}" stroke="#202124"/>'
    )

    legend_x = width - 220
    legend_y = 34
    for offset, segment_id in enumerate(sorted(COLORS)):
        y = legend_y + offset * 22
        color = COLORS[segment_id]
        lines.append(f'<rect x="{legend_x}" y="{y - 10}" width="14" height="14" fill="{color}"/>')
        lines.append(f'<text x="{legend_x + 22}" y="{y + 2}" class="axis">segment {segment_id}</text>')

    for index, item in enumerate(data):
        table_name = item["table_name"]
        counts = item["counts"]
        center_x = margin_left + group_width * index + group_width / 2
        lines.append(
            f'<text x="{center_x}" y="{height - 22}" text-anchor="middle" class="label">{table_name}</text>'
        )

        segment_ids = sorted(counts)
        start_x = center_x - (len(segment_ids) * bar_width + (len(segment_ids) - 1) * 18) / 2
        for segment_index, segment_id in enumerate(segment_ids):
            value = counts[segment_id]
            bar_height = (value / padded_max) * plot_height if padded_max else 0
            x = start_x + segment_index * (bar_width + 18)
            y = margin_top + plot_height - bar_height
            lines.append(
                f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width}" height="{bar_height:.1f}" fill="{COLORS[segment_id]}"/>'
            )
            lines.append(
                f'<text x="{x + bar_width / 2:.1f}" y="{y - 8:.1f}" text-anchor="middle" class="value">{value:,}</text>'
            )

    save_svg(COUNT_CHART, lines)


def main() -> None:
    rows = load_data()
    aggregated = aggregate(rows)
    draw_percent_chart(aggregated)
    draw_count_chart(aggregated)


if __name__ == "__main__":
    main()

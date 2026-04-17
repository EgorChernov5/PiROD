from __future__ import annotations

import argparse
import csv
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "segment_distribution.csv"
DEFAULT_TABLES = [
    "encounters_gp",
    "organizations_gp",
    "patients_gp",
    "payers_gp",
    "procedures_gp",
]


def run_command(command: list[str]) -> str:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def get_segments(container: str, database: str) -> list[tuple[int, int]]:
    command = [
        "docker",
        "exec",
        container,
        "su",
        "-",
        "gpadmin",
        "-c",
        (
            "psql -d {db} -At -F '|' -c "
            "\"select content, port "
            "from gp_segment_configuration "
            "where content >= 0 and role = 'p' "
            "order by content;\""
        ).format(db=database),
    ]
    output = run_command(command)
    segments = []
    for line in output.splitlines():
        content, port = line.split("|")
        segments.append((int(content), int(port)))
    return segments


def quote_table_name(table_name: str) -> str:
    return '"' + table_name.replace('"', '""') + '"'


def get_table_count(container: str, database: str, port: int, table_name: str) -> int:
    sql = f"select count(*) from {quote_table_name(table_name)};"
    command = [
        "docker",
        "exec",
        container,
        "su",
        "-",
        "gpadmin",
        "-c",
        (
            "PGOPTIONS='-c gp_session_role=utility' "
            "psql -p {port} -d {db} -At -c \"{sql}\""
        ).format(port=port, db=database, sql=sql.replace('"', '\\"')),
    ]
    output = run_command(command)
    return int(output)


def export_distribution(
    container: str,
    database: str,
    tables: list[str],
    output_path: Path,
) -> None:
    segments = get_segments(container, database)
    rows: list[dict[str, int | str]] = []

    for table_name in tables:
        for segment_id, port in segments:
            row_count = get_table_count(container, database, port, table_name)
            rows.append(
                {
                    "table_name": table_name,
                    "segment_id": segment_id,
                    "row_count": row_count,
                }
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=["table_name", "segment_id", "row_count"])
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export Greenplum row distribution by segment to CSV."
    )
    parser.add_argument(
        "--container",
        default="pirodgreenplum",
        help="Docker container name with Greenplum.",
    )
    parser.add_argument(
        "--database",
        default="lab3",
        help="Greenplum database name.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="Output CSV path.",
    )
    parser.add_argument(
        "--tables",
        nargs="+",
        default=DEFAULT_TABLES,
        help="Tables to inspect.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    export_distribution(args.container, args.database, args.tables, args.output)
    print(f"Saved segment distribution to {args.output}")


if __name__ == "__main__":
    main()

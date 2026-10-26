
import argparse
import csv
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

REQUIRED = {"complaint_id", "category", "status", "date_opened","date_closed"}

def parse_date(value):
    if not value or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("reports"))
    args = parser.parse_args([r"D:\FDM\Banking_Complaint\Bank_Complaint\complaints.csv"])

    if not args.input_file.is_file():
        print(f"Error: File not found: {args.input_file}")
        return

    try:
        with args.input_file.open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)

            if not reader.fieldnames:
                print("Error: CSV has no headers.")
                return

            missing = REQUIRED - set(reader.fieldnames)
            if missing:
                print(f"Missing required columns: {sorted(missing)}")
                return

            complaints = []
            skipped = 0

            for row in reader:
                if not row or None in row:
                    skipped += 1
                    continue

                if any(not (row.get(col) or "").strip()
                       for col in ["complaint_id", "category", "status", "date_opened"]):
                    skipped += 1
                    continue

                received = parse_date(row["date_opened"])
                if received is None:
                    skipped += 1
                    continue

                complaints.append({
                    "id": row["complaint_id"].strip(),
                    "category": row["category"].strip(),
                    "status": row["status"].strip(),
                    "received": received,
                    "closed": parse_date(row.get("date_closed", ""))
                })

    except (OSError, UnicodeError, csv.Error) as e:
        print(f"Error reading CSV: {e}")
        return

    total = len(complaints)
    status_counts = Counter(c["status"] for c in complaints)
    category_counts = Counter(c["category"] for c in complaints)

    category_rows = sorted(
        category_counts.items(),
        key=lambda x: (-x[1], x[0])
    )

    closed_counts = Counter()
    durations = defaultdict(list)

    for c in complaints:
        if c["status"].lower() == "closed":
            category = c["category"]
            closed_counts[category] += 1

            if c["closed"] is not None:
                try:
                    hours = (
                        c["closed"] - c["received"]
                    ).total_seconds() / 3600

                    if hours >= 0:
                        durations[category].append(hours)
                except TypeError:
                    pass

    output = args.output_dir
    output.mkdir(parents=True, exist_ok=True)

    def save_csv(filename, headers, rows):
        with (output / filename).open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)

    save_csv(
        "status_counts.csv",
        ["status", "count"],
        sorted(status_counts.items())
    )

    save_csv(
        "category_counts.csv",
        ["category", "count", "percentage"],
        [
            (cat, count, round(count / total * 100, 2))
            for cat, count in category_rows
        ]
    )

    resolution_rows = []

    for cat, count in category_rows:
        values = durations[cat]
        avg_hours = round(sum(values) / len(values), 2) if values else "N/A"

        resolution_rows.append((
            cat,
            count,
            closed_counts[cat],
            len(values),
            closed_counts[cat] - len(values),
            avg_hours
        ))

    save_csv(
        "resolution_by_category.csv",
        [
            "category", "total_complaints", "closed_cases",
            "measured_cases", "unmeasurable_cases",
            "avg_resolution_hours"
        ],
        resolution_rows
    )

    def markdown_table(headers, rows):
        lines = [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |"
        ]
        for row in rows:
            lines.append("| " + " | ".join(map(str, row)) + " |")
        return "\n".join(lines)

    top = category_rows[0] if category_rows else None

    report = [
        "# Complaint Analysis Report",
        "",
        f"**Total complaints:** {total}",
        f"**Skipped rows:** {skipped}",
        "",
        "## Highest-volume category",
        "",
        (
            f"{top[0]}: {top[1]} complaints "
            f"({top[1] / total * 100:.2f}%)"
            if top else "No valid complaints."
        ),
        "",
        "## Status counts",
        "",
        markdown_table(
            ["Status", "Count"],
            sorted(status_counts.items())
        ),
        "",
        "## Category counts",
        "",
        markdown_table(
            ["Category", "Count", "Percentage"],
            [
                (cat, count, f"{count / total * 100:.2f}%")
                for cat, count in category_rows
            ]
        ),
        "",
        "## Closed-case resolution",
        "",
        markdown_table(
            ["Category", "Total", "Closed", "Measured",
             "Unmeasurable", "Average hours"],
            resolution_rows
        ),
        "",
        "## Methodology",
        "",
        "- Each valid CSV row represents one complaint.",
        "- Incomplete rows and invalid received dates are skipped.",
        "- Closed cases are identified by status 'Closed'.",
        "- Resolution time = closed_at minus received_at.",
        "- Missing, negative, or incompatible durations are excluded.",
        "- Average resolution uses closed cases with valid durations.",
        "- Category percentages use total valid complaints."
    ]

    (output / "complaint_report.md").write_text(
        "\n".join(report), encoding="utf-8"
    )

    print(f"Total complaints: {total}")
    print(f"Skipped rows: {skipped}")
    print(f"Reports generated in: {output.resolve()}")

if __name__ == "__main__":
    main()

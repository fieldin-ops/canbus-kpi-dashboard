#!/usr/bin/env python3
"""
Weekly CAN Bus adoption KPI collector.

Runs the BigQuery query, saves a timestamped snapshot to data/snapshots/,
and regenerates the HTML dashboard.
"""

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data" / "snapshots"
DASHBOARD_PATH = PROJECT_ROOT / "dashboard.html"
TEMPLATE_PATH = PROJECT_ROOT / "dashboard_template.html"

BQ_QUERY = r"""
WITH sml_devices AS (
  SELECT
    d.code,
    d.company_id
  FROM prod_repl.devices_new d
  WHERE d.device_model LIKE 'sml%'
    AND d.status = 1
),
canbus_devices AS (
  SELECT DISTINCT
    a.device.code AS device_code
  FROM fieldin.fieldin_machine_shifts_sensors_analytics a
  WHERE a.engine_rpm_valid = TRUE
)
SELECT
  c.name                        AS company_name,
  UPPER(c.country)              AS country,
  COUNT(DISTINCT sd.code)       AS total_sml,
  COUNT(DISTINCT cd.device_code) AS total_sml_with_canbus
FROM sml_devices sd
INNER JOIN prod_repl.companies c
  ON sd.company_id = c.id
INNER JOIN `prod_repl.company_properties` cp
  ON c.id = cp.company_id
  AND cp.name = 'is_active'
  AND cp.latest = 1
  AND CAST(cp.value AS INT64) = 1
LEFT JOIN canbus_devices cd
  ON sd.code = cd.device_code
GROUP BY c.name, c.country
ORDER BY total_sml DESC
"""


def run_query() -> list[dict]:
    """Execute the BigQuery query via bq CLI and return parsed rows."""
    result = subprocess.run(
        [
            "bq", "query",
            "--use_legacy_sql=false",
            "--format=prettyjson",
            "--max_rows=1000",
            BQ_QUERY,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"BigQuery error:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)

    COUNTRY_LABELS = {"US": "US", "IL": "IL", "AU": "Australia", "MX": "MX", "AR": "AR", "IT": "IT", "ZA": "ZA", "CL": "CL"}
    rows = json.loads(result.stdout)
    return [
        {
            "company": r["company_name"],
            "country": COUNTRY_LABELS.get(r.get("country", ""), r.get("country", "")),
            "sml": int(r["total_sml"]),
            "canbus": int(r["total_sml_with_canbus"]),
        }
        for r in rows
    ]


def save_snapshot(rows: list[dict]) -> Path:
    """Save the query result as a dated JSON snapshot."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    now = datetime.now(timezone.utc)
    week_label = now.strftime("%Y-W%W")
    date_label = now.strftime("%Y-%m-%d")

    total_sml = sum(r["sml"] for r in rows)
    total_canbus = sum(r["canbus"] for r in rows)
    total_companies = len(rows)
    companies_with_canbus = sum(1 for r in rows if r["canbus"] > 0)

    snapshot = {
        "week": week_label,
        "date": date_label,
        "collected_at": now.isoformat(),
        "summary": {
            "total_companies": total_companies,
            "companies_with_canbus": companies_with_canbus,
            "total_sml": total_sml,
            "total_canbus": total_canbus,
            "adoption_pct": round(total_canbus / total_sml * 100, 2) if total_sml else 0,
        },
        "companies": rows,
    }

    filepath = DATA_DIR / f"{date_label}.json"
    filepath.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False))
    print(f"Snapshot saved: {filepath}")
    return filepath


def load_all_snapshots() -> list[dict]:
    """Load all historical snapshots sorted by date."""
    if not DATA_DIR.exists():
        return []
    files = sorted(DATA_DIR.glob("*.json"))
    snapshots = []
    for f in files:
        data = json.loads(f.read_text())
        snapshots.append(data)
    return snapshots


INDEX_PATH = PROJECT_ROOT / "index.html"
PAGES_URL = "https://fieldin-ops.github.io/canbus-kpi-dashboard/"


DASHBOARD_PASSWORD = os.environ.get("KPI_DASHBOARD_PASSWORD", "fieldin2024")


def build_dashboard(snapshots: list[dict]) -> None:
    """Inject snapshot data and password hash into the HTML template."""
    template = TEMPLATE_PATH.read_text()
    dashboard_data = json.dumps(snapshots, ensure_ascii=False)
    pw_hash = hashlib.sha256(DASHBOARD_PASSWORD.encode()).hexdigest()
    html = template.replace("__DASHBOARD_DATA__", dashboard_data)
    html = html.replace("__DASHBOARD_PASSWORD_HASH__", pw_hash)
    DASHBOARD_PATH.write_text(html)
    INDEX_PATH.write_text(html)
    print(f"Dashboard updated: {DASHBOARD_PATH}")


def publish() -> None:
    """Commit updated data and dashboard, push to GitHub Pages."""
    cmds = [
        ["git", "-C", str(PROJECT_ROOT), "add", "-A"],
        ["git", "-C", str(PROJECT_ROOT), "commit", "-m", f"Weekly KPI update {datetime.now(timezone.utc).strftime('%Y-%m-%d')}"],
        ["git", "-C", str(PROJECT_ROOT), "push"],
    ]
    for cmd in cmds:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 and "nothing to commit" not in result.stdout:
            print(f"Git error: {result.stderr}", file=sys.stderr)
            return
    print(f"Published to: {PAGES_URL}")


def main():
    print("Collecting CAN Bus KPI data...")
    rows = run_query()
    print(f"  {len(rows)} companies returned")

    save_snapshot(rows)

    snapshots = load_all_snapshots()
    print(f"  {len(snapshots)} total snapshots")

    build_dashboard(snapshots)
    publish()
    print("Done.")


if __name__ == "__main__":
    main()

# Automation Prompt — Weekly CAN Bus KPI

Use this prompt when creating the Cursor Automation at cursor.com/automations.

---

You are maintaining a weekly CAN Bus adoption KPI dashboard.

## Steps

1. Navigate to the project root.
2. Run `python3 collect.py`.
3. This script queries BigQuery for all active SML devices and their CAN Bus connectivity across active companies, saves a timestamped JSON snapshot under `data/snapshots/`, and regenerates `dashboard.html`.
4. Verify the script printed "Done." — if it errors, report the failure.

## Expected output

- A new file `data/snapshots/YYYY-MM-DD.json`
- An updated `dashboard.html` with the latest data and trend charts

## Important

- Do NOT modify `collect.py` or `dashboard_template.html`.
- Do NOT modify existing snapshots.
- If `bq` CLI is not authenticated, report the issue — do not attempt to fix credentials.

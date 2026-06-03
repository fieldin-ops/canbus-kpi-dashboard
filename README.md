# CAN Bus Adoption — Weekly KPI Dashboard

Automated weekly tracking of SML device fleet CAN Bus connectivity across active companies.

## How it works

1. **`collect.py`** queries BigQuery for all active SML devices and their CAN Bus status
2. Results are saved as a dated JSON snapshot in `data/snapshots/`
3. `dashboard.html` is regenerated with trend charts and full company breakdown

## Running manually

```bash
python3 collect.py
open dashboard.html
```

## Scheduling

### Option A: Cursor Automation (cloud)

Create at [cursor.com/automations](https://cursor.com/automations):

- **Trigger:** Schedule → `0 7 * * 0` (every Sunday at 7:00 AM UTC)
- **Repository:** attach the repo containing this project
- **Prompt:** see `automation-prompt.md`
- **Note:** the cloud agent needs BigQuery access — either configure a BigQuery MCP server or ensure `bq` CLI is available in the agent environment

### Option B: Local cron (this machine)

```bash
# Add to crontab:
crontab -e

# Run every Sunday at 7:00 AM local time:
0 7 * * 0 cd /Users/mac/Projects/canbus-kpi-dashboard && /usr/local/bin/python3 collect.py >> cron.log 2>&1
```

## Dashboard

Open `dashboard.html` in any browser. Share the file directly — it's fully self-contained (uses Chart.js CDN for charts).

### Features

- KPI cards with week-over-week deltas
- Adoption trend line chart
- Stacked bar chart (SML fleet breakdown)
- Companies with CAN Bus trend
- Searchable, sortable, filterable company table
- Adoption progress bars per company

## Data

Snapshots accumulate in `data/snapshots/YYYY-MM-DD.json`. Each snapshot contains:

- Summary stats (totals, adoption %, company counts)
- Per-company breakdown (SML count, CAN Bus count)

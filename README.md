# Khwezi Mining Monitor — MINN2020A Prototype

A Streamlit prototype based on the assignment brief. It demonstrates:

- Role-based login/access control (permissions follow Table 1 of the brief)
- Worker health and safety monitoring with rule-based risk levels and unsafe-condition warnings
- Safety incident database: add, view, search, filter by date/severity/status/department, update status, trend analysis
- Equipment database: add equipment, record sensor readings, reading history charts
- Condition monitoring with NORMAL / WARNING / CRITICAL messages from the latest sensor reading
- Maintenance monitoring: availability calculated with the brief's formula, due / overdue / under maintenance, excessive downtime, repeated alerts, low availability, maintenance priority ranking
- 1–5 likelihood × consequence risk assessment and risk matrix
- Automatic alerts in the Figure 1 format (temperature, vibration, downtime, overdue maintenance, components, PPE, fatigue, training, high-risk observations, critical incidents)
- Mining monitoring dashboard
- Interactive analysis answering the Appendix A business questions
- CSV and text report export

## Run locally

1. Install Python 3.10+.
2. Open a terminal in this project folder.
3. Run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open the Local URL shown in the terminal, normally `http://localhost:8501`.

## Demo accounts

| Username | Password | Name | Role |
|---|---|---|---|
| admin | admin123 | Mpho Voko | Administrator |
| safety | safety123 | Dineo Malgas | Safety Officer |
| mining | mining123 | Nhlamulo Makhubele | Mining Engineer |
| maintenance | maint123 | Nakedi Mabeba | Maintenance Engineer |
| manager | manager123 | Koketso Phiri | Manager |

The colour theme is in `.streamlit/config.toml`; the rest of the styling is the `CSS` block near the top of `app.py`.

## Assignment mapping

The app covers the brief's access control, worker safety, incident database, equipment database, condition monitoring, maintenance monitoring, risk assessment, alerts, dashboard and interactive analysis requirements.

The assignment specifies these educational prototype thresholds: temperature `<80°C` normal, `80–100°C` warning, `>100°C` critical; vibration `<5 mm/s` normal, `5–8 mm/s` warning, `>8 mm/s` critical. They are explicitly not actual manufacturer or mine safety limits.

Other prototype rules chosen for this app (all set at the top of `app.py`): PPE compliance below 80% is low; fatigue 5/5 is high; 2 or more near misses or previous incidents is a high-risk observation; more than 50 h downtime is excessive; availability below 80% is low; maintenance is due at 90% of the service interval and overdue past it; 3 or more readings outside normal limits count as repeated alerts.

## Data files

The CSV files in `data/` are sample data:

- `workers.csv`: one row per worker
- `incidents.csv`: one row per safety incident
- `equipment.csv`: one row per machine (operating time and downtime are for the current monthly reporting period)
- `readings.csv`: temperature and vibration sensor readings (several per machine); the latest reading gives the current condition

## Deploy online

Upload the project to GitHub, then use Streamlit Community Cloud to deploy `app.py`. The same `requirements.txt` and `data/` folder should be included in the repository.

For a real production system, replace the demo login with secure authentication, password hashing, a database and secrets management.

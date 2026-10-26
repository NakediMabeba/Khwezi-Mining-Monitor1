import streamlit as st
import pandas as pd
import numpy as np
from datetime import date
from pathlib import Path

st.set_page_config(page_title="Khwezi Mining Monitor", page_icon=":material/engineering:", layout="wide")

# -----------------------------
# Demo users and role permissions (Table 1 of the brief)
# -----------------------------
USERS = {
    "admin": {"password": "admin123", "role": "Administrator", "name": "Mpho Voko"},
    "safety": {"password": "safety123", "role": "Safety Officer", "name": "Dineo Malgas"},
    "mining": {"password": "mining123", "role": "Mining Engineer", "name": "Nhlamulo Makhubele"},
    "maintenance": {"password": "maint123", "role": "Maintenance Engineer", "name": "Nakedi Mabeba"},
    "manager": {"password": "manager123", "role": "Manager", "name": "Koketso Phiri"},
}

PERMISSIONS = {
    "Administrator": {"dashboard", "safety", "incidents", "equipment", "maintenance", "risk", "alerts", "analytics", "reports", "users"},
    "Safety Officer": {"dashboard", "safety", "incidents", "risk", "alerts", "analytics", "reports"},
    "Mining Engineer": {"dashboard", "safety", "incidents", "equipment", "maintenance", "risk", "alerts", "analytics", "reports"},
    "Maintenance Engineer": {"dashboard", "equipment", "maintenance", "alerts", "analytics", "reports"},
    "Manager": {"dashboard", "safety", "incidents", "equipment", "maintenance", "risk", "alerts", "analytics", "reports"},
}

# Data folder next to app.py, so it works whatever folder the app is started from
DATA_DIR = Path(__file__).parent / "data"

# Assignment prototype thresholds — NOT manufacturer/mine safety limits.
TEMP_WARNING, TEMP_CRITICAL = 80.0, 100.0
VIB_WARNING, VIB_CRITICAL = 5.0, 8.0

# Prototype rules chosen by the group for the other alerts
PPE_LOW = 80                 # PPE compliance (%) below this is low
PPE_TARGET = 90              # PPE compliance (%) the site aims for
FATIGUE_HIGH = 5             # fatigue level (1–5) at or above this is high
REPEATED_EVENTS = 2          # near misses / previous incidents at or above this is a high-risk observation
DOWNTIME_EXCESSIVE = 50      # downtime (h) in the reporting period above this is excessive
AVAILABILITY_LOW = 80        # availability (%) below this is low
SERVICE_DUE_FRACTION = 0.9   # maintenance is due once 90% of the service interval has been used
REPEATED_ALERTS = 3          # sensor readings outside normal limits at or above this count as repeated alerts

SEVERITY_WEIGHT = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
PRIORITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "WARNING": 2}

FILES = {"workers": "workers.csv", "incidents": "incidents.csv", "equipment": "equipment.csv", "readings": "readings.csv"}
COLUMNS = {
    "workers": ["Worker ID", "Department", "Job Role", "Shift", "PPE Compliance (%)", "Training Status", "Fatigue Level",
                "Safety Observations", "Near Misses", "Previous Incidents"],
    "incidents": ["Incident ID", "Date", "Time", "Shift", "Location", "Department", "Incident Type", "Severity", "Injury",
                  "Lost Time Injury", "Cause", "Corrective Action", "Status"],
    "equipment": ["Equipment ID", "Equipment Type", "Manufacturer", "Department", "Operating Hours", "Fuel Consumption (L/h)",
                  "Brake Status", "Tyre Status", "Engine Status", "Maintenance Status", "Service Interval (h)",
                  "Hours Since Service", "Operating Time (h)", "Downtime (h)"],
    "readings": ["Date", "Equipment ID", "Temperature (°C)", "Vibration (mm/s)"],
}
NUMERIC = {
    "workers": ["PPE Compliance (%)", "Fatigue Level", "Safety Observations", "Near Misses", "Previous Incidents"],
    "incidents": [],
    "equipment": ["Operating Hours", "Fuel Consumption (L/h)", "Service Interval (h)", "Hours Since Service",
                  "Operating Time (h)", "Downtime (h)"],
    "readings": ["Temperature (°C)", "Vibration (mm/s)"],
}

DEPARTMENTS = ["Production", "Plant", "Engineering", "Maintenance", "Geology", "Other"]
EQUIPMENT_TYPES = ["Haul Truck", "Loader", "Excavator", "Drilling Machine", "Bulldozer", "Scraper Winch", "Crusher",
                   "Conveyor", "Pump", "Other"]
INCIDENT_TYPES = ["Slip/Trip", "Equipment Contact", "Hand Injury", "Fall of Ground", "Vehicle Incident", "Near Miss",
                  "Dust Exposure", "Electrical", "Other"]


# -----------------------------
# Look and feel
# -----------------------------
NAVY, ACCENT, MUTED, BORDER = "#16233B", "#D9731A", "#5F6B7A", "#DDE1E6"
CHART_COLORS = ["#2E4A7D", "#D9731A", "#5B8DB8", "#8A96A3", "#3F7D5A", "#B23A2E"]
SEVERITY_COLORS = {"Low": "#3F7D5A", "Medium": "#D9A21A", "High": "#D9731A", "Critical": "#B23A2E"}

# Text colour / background for status values shown in tables
STATUS_STYLES = {
    "red": ("#9B1C1C", "#FDE8E8"), "orange": ("#9A4A0B", "#FDEBD8"),
    "amber": ("#7A5A00", "#FCF3D1"), "green": ("#1E6B43", "#E3F4EA"),
}
STATUS_GROUP = {
    "CRITICAL": "red", "Critical": "red", "Overdue": "red", "Required": "red",
    "HIGH": "orange", "High": "orange",
    "WARNING": "amber", "Medium": "amber", "Due": "amber", "Under Maintenance": "amber", "Open": "amber", "Under Review": "amber",
    "NORMAL": "green", "OK": "green", "Low": "green", "Available": "green", "Closed": "green", "On target": "green",
}
STATUS_COLUMNS = ["Priority", "Condition", "Risk Level", "Maintenance State", "Maintenance Status", "Severity", "Status", "Intervention"]

CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&display=swap');
.stApp, .stApp p, .stApp li, .stApp label, .stApp input, .stApp textarea, .stApp button, .stApp h1, .stApp h2, .stApp h3,
.stApp h4, .stApp td, .stApp th, .stApp div[data-testid="stMarkdownContainer"] {{ font-family: 'IBM Plex Sans', sans-serif; }}
#MainMenu, footer, [data-testid="stDecoration"], [data-testid="stAppDeployButton"] {{ display: none; }}
header[data-testid="stHeader"] {{ background: transparent; }}
.block-container {{ padding-top: 2rem; max-width: 1400px; }}

/* Sidebar */
section[data-testid="stSidebar"] {{ background: {NAVY}; }}
section[data-testid="stSidebar"] * {{ color: #E6EAF0; }}
section[data-testid="stSidebar"] [role="radiogroup"] {{ gap: 2px; width: 100%; }}
section[data-testid="stSidebar"] [data-testid="stRadioOption"] {{ width: 100%; max-width: 100%; padding: 9px 12px;
    border-radius: 4px; border-left: 3px solid transparent; margin: 0; }}
section[data-testid="stSidebar"] [data-testid="stRadioOption"] > div > div:not([data-testid]) {{ display: none; }}
section[data-testid="stSidebar"] [data-testid="stRadioOption"]:hover {{ background: rgba(255,255,255,0.06); }}
section[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] {{ background: rgba(255,255,255,0.10);
    border-left-color: {ACCENT}; }}
section[data-testid="stSidebar"] [data-testid="stRadioOption"][data-selected="true"] p {{ font-weight: 600; color: #FFFFFF; }}
section[data-testid="stSidebar"] .stButton button {{ background: transparent; border: 1px solid rgba(255,255,255,0.25); }}
section[data-testid="stSidebar"] .stButton button:hover {{ border-color: {ACCENT}; }}
.kh-brand {{ padding: 4px 0 18px; border-bottom: 1px solid rgba(255,255,255,0.12); margin-bottom: 16px; }}
.kh-brand-name {{ font-size: 1.15rem; font-weight: 700; letter-spacing: 0.04em; color: #FFFFFF !important; }}
.kh-brand-sub {{ font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.12em; color: #9AA7B8 !important; }}
.kh-user {{ display: flex; align-items: center; gap: 10px; padding: 10px; background: rgba(255,255,255,0.05);
    border-radius: 6px; margin-bottom: 18px; }}
.kh-avatar {{ width: 36px; height: 36px; border-radius: 50%; background: {ACCENT}; display: flex; align-items: center;
    justify-content: center; font-weight: 600; font-size: 0.85rem; color: #FFFFFF !important; flex-shrink: 0; }}
.kh-user-name {{ font-weight: 600; font-size: 0.92rem; color: #FFFFFF !important; line-height: 1.2; }}
.kh-user-role {{ font-size: 0.75rem; color: #9AA7B8 !important; }}
.kh-nav-label {{ font-size: 0.68rem; text-transform: uppercase; letter-spacing: 0.12em; color: #8593A6 !important; margin: 4px 0 6px; }}
.kh-side-foot {{ font-size: 0.72rem; color: #8593A6 !important; margin-top: 24px; line-height: 1.5; }}

/* Page header and sections */
.kh-header {{ border-bottom: 1px solid {BORDER}; padding-bottom: 14px; margin-bottom: 22px; }}
.kh-eyebrow {{ font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.12em; color: {ACCENT}; font-weight: 600; }}
.kh-title {{ font-size: 1.75rem; font-weight: 700; color: {NAVY}; margin: 2px 0 2px; }}
.kh-subtitle {{ color: {MUTED}; font-size: 0.95rem; }}
.kh-section {{ font-size: 1.0rem; font-weight: 600; color: {NAVY}; margin: 18px 0 8px; padding-left: 10px;
    border-left: 3px solid {ACCENT}; }}

/* KPI cards */
[data-testid="stMetric"] {{ background: #FFFFFF; border: 1px solid {BORDER}; border-radius: 6px; padding: 14px 16px; }}
[data-testid="stMetricLabel"] .stMarkdownEllipsis {{ overflow: visible; }}
[data-testid="stMetricLabel"] p {{ white-space: normal; overflow: visible; text-overflow: clip; line-height: 1.3; font-size: 0.74rem; text-transform: uppercase; letter-spacing: 0.06em; color: {MUTED}; }}
[data-testid="stMetricValue"] {{ font-weight: 600; color: {NAVY}; }}

/* Tabs, forms, containers */
.stTabs [data-baseweb="tab-list"] {{ gap: 4px; border-bottom: 1px solid {BORDER}; }}
.stTabs [data-baseweb="tab"] {{ padding: 8px 16px; font-weight: 500; }}
[data-testid="stForm"] {{ background: #FFFFFF; border: 1px solid {BORDER}; border-radius: 6px; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ background: #FFFFFF; }}

/* Login */
.kh-login-panel {{ background: {NAVY}; border-radius: 8px; padding: 40px 36px; min-height: 430px; border-top: 4px solid {ACCENT}; }}
.kh-login-panel * {{ color: #E6EAF0; }}
.kh-login-name {{ font-size: 2rem; font-weight: 700; color: #FFFFFF !important; letter-spacing: 0.02em; }}
.kh-login-tag {{ font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.14em; color: {ACCENT} !important; margin-bottom: 26px; }}
.kh-login-panel ul {{ padding-left: 18px; line-height: 1.9; color: #C9D2DE; }}
.kh-login-foot {{ margin-top: 30px; font-size: 0.75rem; color: #8593A6 !important; }}
</style>
"""


def apply_style():
    st.markdown(CSS, unsafe_allow_html=True)


def page_header(title, subtitle, eyebrow="Khwezi Mining Operations"):
    st.markdown(f'<div class="kh-header"><div class="kh-eyebrow">{eyebrow}</div><div class="kh-title">{title}</div>'
                f'<div class="kh-subtitle">{subtitle}</div></div>', unsafe_allow_html=True)


def section(text):
    st.markdown(f'<div class="kh-section">{text}</div>', unsafe_allow_html=True)


def status_style(value):
    group = STATUS_GROUP.get(str(value))
    if not group:
        return ""
    fg, bg = STATUS_STYLES[group]
    return f"color: {fg}; background-color: {bg}; font-weight: 600;"


def table(data, **kwargs):
    """st.dataframe with coloured status columns and one decimal place for numbers."""
    df = data.to_frame() if isinstance(data, pd.Series) else data
    cols = [c for c in STATUS_COLUMNS if c in df.columns]
    if df.index.is_unique and df.columns.is_unique and len(df):
        styler = df.style.format(precision=1)
        if cols:
            styler = styler.map(status_style, subset=cols)
        st.dataframe(styler, **kwargs)
    else:
        st.dataframe(df, **kwargs)


def bar_chart(data, color=None, **kwargs):
    n = 1 if isinstance(data, pd.Series) or data.shape[1] == 1 else data.shape[1]
    st.bar_chart(data, color=color or (CHART_COLORS[0] if n == 1 else CHART_COLORS[:n]), **kwargs)


def line_chart(data, color=None, **kwargs):
    n = 1 if isinstance(data, pd.Series) or data.shape[1] == 1 else data.shape[1]
    st.line_chart(data, color=color or (ACCENT if n == 1 else CHART_COLORS[:n]), **kwargs)


# -----------------------------
# Data loading and saving
# -----------------------------
def clean_numbers(df, name):
    for c in NUMERIC[name]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)


def load_csv(name):
    """Read one dataset. A missing/broken file or missing columns gives an empty table instead of a crash."""
    path = DATA_DIR / FILES[name]
    try:
        df = pd.read_csv(path, keep_default_na=False, na_values=[""])  # keep the text "N/A" as it is
    except Exception:
        st.error(f"Could not read data/{FILES[name]}. Check that the file exists and is a valid CSV.")
        return pd.DataFrame(columns=COLUMNS[name])
    missing = [c for c in COLUMNS[name] if c not in df.columns]
    if missing:
        st.error(f"data/{FILES[name]} is missing the columns: {', '.join(missing)}")
        return pd.DataFrame(columns=COLUMNS[name])
    df = df[COLUMNS[name]].copy()
    clean_numbers(df, name)
    return df


def add_record(name, row, label):
    """Add one row to a dataset, then try to save it to its CSV file."""
    df = DATA[name]
    df.loc[len(df)] = row
    clean_numbers(df, name)
    save_csv(name, f"{label} added.")


def save_csv(name, message):
    try:
        DATA[name].to_csv(DATA_DIR / FILES[name], index=False)
        st.success(f"{message} Note: on Streamlit Community Cloud, saved changes are lost when the app restarts.")
    except OSError:
        st.warning(f"{message} The data file could not be saved, so the change only lasts for this session.")


# Data is loaded once per session, so added records stay while the user is logged in
if "data" not in st.session_state:
    st.session_state.data = {name: load_csv(name) for name in FILES}
DATA = st.session_state.data
workers, incidents, equipment, readings = DATA["workers"], DATA["incidents"], DATA["equipment"], DATA["readings"]

# -----------------------------
# Session state / login
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""


def login_page():
    left, right = st.columns([1.15, 1], gap="large")
    with left:
        st.markdown(f"""<div class="kh-login-panel">
            <div class="kh-login-name">KHWEZI MINING</div>
            <div class="kh-login-tag">Health, Safety &amp; Equipment Monitoring</div>
            <p>One place for supervisors, engineers and managers to see the safety and equipment status of the operation.</p>
            <ul><li>Worker safety and incident tracking</li><li>Equipment condition and maintenance monitoring</li>
            <li>Risk assessment and automatic alerts</li><li>Operational dashboard and reporting</li></ul>
            <div class="kh-login-foot">MINN2020A prototype. Monitoring thresholds are educational values,
            not manufacturer or mine safety limits.</div></div>""", unsafe_allow_html=True)
    with right:
        st.markdown('<div style="height:40px"></div>', unsafe_allow_html=True)
        page_header("Sign in", "Use your Khwezi Mining account to continue.", eyebrow="Secure access")
        with st.form("login"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in", type="primary", width="stretch")
            if submitted:
                user = USERS.get(username.strip().lower())
                if user and password == user["password"]:
                    st.session_state.logged_in = True
                    st.session_state.username = username.strip().lower()
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
        with st.expander("Demo accounts"):
            table(pd.DataFrame([[k, v["password"], v["name"], v["role"]] for k, v in USERS.items()],
                               columns=["Username", "Password", "Name", "Role"]), width="stretch", hide_index=True)


def can(page):
    return page in PERMISSIONS[USERS[st.session_state.username]["role"]]


# -----------------------------
# Worker safety rules
# -----------------------------
def worker_risk(r):
    """Rule-based risk level for one worker."""
    if r["PPE Compliance (%)"] < PPE_LOW or r["Fatigue Level"] >= FATIGUE_HIGH:
        return "High"
    if (r["PPE Compliance (%)"] < PPE_TARGET or r["Fatigue Level"] >= 3 or r["Training Status"] != "Complete"
            or r["Near Misses"] >= REPEATED_EVENTS or r["Previous Incidents"] >= REPEATED_EVENTS):
        return "Medium"
    return "Low"


def worker_warnings(r):
    """List of unsafe conditions found for one worker."""
    w = []
    if r["PPE Compliance (%)"] < PPE_LOW:
        w.append(f"low PPE compliance ({r['PPE Compliance (%)']:.0f}%)")
    if r["Fatigue Level"] >= FATIGUE_HIGH:
        w.append(f"high fatigue level ({r['Fatigue Level']:.0f}/5)")
    if r["Training Status"] == "Expired":
        w.append("safety training expired")
    elif r["Training Status"] == "Pending":
        w.append("safety training pending")
    if r["Near Misses"] >= REPEATED_EVENTS:
        w.append(f"{r['Near Misses']:.0f} near misses")
    if r["Previous Incidents"] >= REPEATED_EVENTS:
        w.append(f"{r['Previous Incidents']:.0f} previous incidents")
    return w


def workers_view():
    w = workers.copy()
    records = w.to_dict("records")
    w["Risk Level"] = [worker_risk(r) for r in records]
    w["Warnings"] = [", ".join(worker_warnings(r)) or "None" for r in records]
    return w


# -----------------------------
# Equipment condition and maintenance rules
# -----------------------------
def reading_condition(t, v):
    if pd.isna(t) or pd.isna(v):
        return "NO DATA"
    if t > TEMP_CRITICAL or v > VIB_CRITICAL:
        return "CRITICAL"
    if t >= TEMP_WARNING or v >= VIB_WARNING:
        return "WARNING"
    return "NORMAL"


def condition_message(t, v):
    """Monitoring message in the format given in the brief."""
    if pd.isna(t) or pd.isna(v):
        return "NO DATA: No sensor reading recorded for this equipment."
    msgs = []
    if t > TEMP_CRITICAL:
        msgs.append("CRITICAL: Equipment temperature exceeds predefined threshold. Inspection required.")
    elif t >= TEMP_WARNING:
        msgs.append("WARNING: Equipment temperature approaching predefined threshold.")
    if v > VIB_CRITICAL:
        msgs.append("CRITICAL: Equipment vibration exceeds predefined threshold. Inspection required.")
    elif v >= VIB_WARNING:
        msgs.append("WARNING: Equipment vibration approaching predefined threshold.")
    return " ".join(msgs) or "NORMAL: Equipment operating within defined monitoring limits."


def availability(operating, downtime):
    """Availability = Operating Time / (Downtime + Operating Time) × 100"""
    total = operating + downtime
    return round(operating / total * 100, 1) if total > 0 else 0.0


def maintenance_state(r):
    if str(r["Maintenance Status"]).lower() == "under maintenance":
        return "Under Maintenance"
    if r["Hours Since Service"] > r["Service Interval (h)"]:
        return "Overdue"
    if r["Hours Since Service"] >= SERVICE_DUE_FRACTION * r["Service Interval (h)"]:
        return "Due"
    return "OK"


def component_issues(r):
    return [f"{part} {r[part + ' Status']}" for part in ["Brake", "Tyre", "Engine"]
            if str(r[part + " Status"]) not in ("Good", "N/A")]


def maintenance_flags(r):
    flags = []
    if r["Maintenance State"] != "OK":
        flags.append(r["Maintenance State"])
    if r["Downtime (h)"] > DOWNTIME_EXCESSIVE:
        flags.append("Excessive downtime")
    if r["Availability (%)"] < AVAILABILITY_LOW:
        flags.append("Low availability")
    if r["Alert Readings"] >= REPEATED_ALERTS:
        flags.append("Repeated alerts")
    flags += component_issues(r)
    return flags


def priority_score(r):
    """Points used to rank equipment for maintenance priority (higher = more urgent)."""
    score = {"CRITICAL": 3, "WARNING": 1}.get(r["Condition"], 0)
    score += {"Overdue": 3, "Due": 1}.get(r["Maintenance State"], 0)
    score += 2 if r["Alert Readings"] >= REPEATED_ALERTS else 0
    score += 1 if r["Downtime (h)"] > DOWNTIME_EXCESSIVE else 0
    score += 1 if r["Availability (%)"] < AVAILABILITY_LOW else 0
    score += len(component_issues(r))
    return score


def readings_view():
    r = readings.copy()
    r["Date"] = pd.to_datetime(r["Date"], errors="coerce")
    r["Condition"] = [reading_condition(t, v) for t, v in zip(r["Temperature (°C)"], r["Vibration (mm/s)"])]
    return r.sort_values(["Equipment ID", "Date"])


def equipment_view():
    """Equipment table with the latest reading, condition, availability and maintenance flags added."""
    e = equipment.copy()
    r = readings_view()
    latest = r.groupby("Equipment ID").tail(1).set_index("Equipment ID")
    e["Temperature (°C)"] = e["Equipment ID"].map(latest["Temperature (°C)"])
    e["Vibration (mm/s)"] = e["Equipment ID"].map(latest["Vibration (mm/s)"])
    e["Last Reading"] = e["Equipment ID"].map(latest["Date"].dt.strftime("%Y-%m-%d"))
    e["Condition"] = [reading_condition(t, v) for t, v in zip(e["Temperature (°C)"], e["Vibration (mm/s)"])]
    e["Condition Message"] = [condition_message(t, v) for t, v in zip(e["Temperature (°C)"], e["Vibration (mm/s)"])]
    e["Availability (%)"] = [availability(o, d) for o, d in zip(e["Operating Time (h)"], e["Downtime (h)"])]
    alert_counts = r[r["Condition"].isin(["WARNING", "CRITICAL"])].groupby("Equipment ID").size()
    e["Alert Readings"] = e["Equipment ID"].map(alert_counts).fillna(0).astype(int)
    e["Maintenance State"] = [maintenance_state(x) for x in e.to_dict("records")]
    records = e.to_dict("records")
    e["Maintenance Flags"] = [", ".join(maintenance_flags(x)) or "None" for x in records]
    e["Priority Score"] = [priority_score(x) for x in records]
    return e


# -----------------------------
# Alerts
# -----------------------------
def alert(priority, source_type, source, parameter, value, status, action):
    return {"Priority": priority, "Source Type": source_type, "Source": source, "Parameter": parameter,
            "Value": value, "Status": status, "Recommended Action": action}


def build_alerts():
    alerts = []
    for r in equipment_view().to_dict("records"):
        eid, t, v = r["Equipment ID"], r["Temperature (°C)"], r["Vibration (mm/s)"]
        if not pd.isna(t) and t >= TEMP_WARNING:
            crit = t > TEMP_CRITICAL
            alerts.append(alert("CRITICAL" if crit else "WARNING", "Equipment", eid, "Temperature", f"{t} °C",
                                "Above Critical Threshold" if crit else "Approaching Threshold",
                                "Inspect equipment and initiate appropriate maintenance/safety procedures."))
        if not pd.isna(v) and v >= VIB_WARNING:
            crit = v > VIB_CRITICAL
            alerts.append(alert("CRITICAL" if crit else "WARNING", "Equipment", eid, "Vibration", f"{v} mm/s",
                                "Above Critical Threshold" if crit else "Approaching Threshold",
                                "Inspect equipment and initiate appropriate maintenance/safety procedures."))
        if r["Downtime (h)"] > DOWNTIME_EXCESSIVE:
            alerts.append(alert("HIGH", "Equipment", eid, "Downtime", f"{r['Downtime (h)']:.0f} h",
                                "Excessive Downtime", "Investigate downtime causes and review the maintenance plan."))
        if r["Maintenance State"] == "Overdue":
            alerts.append(alert("HIGH", "Equipment", eid, "Hours Since Service",
                                f"{r['Hours Since Service']:.0f} h (interval {r['Service Interval (h)']:.0f} h)",
                                "Maintenance Overdue", "Schedule maintenance immediately."))
        for issue in component_issues(r):
            alerts.append(alert("WARNING", "Equipment", eid, issue.split()[0] + " Status", issue.split()[1],
                                "Component Needs Attention", "Inspect the component before the next shift."))
    for r in workers.to_dict("records"):
        wid = r["Worker ID"]
        if r["PPE Compliance (%)"] < PPE_LOW:
            alerts.append(alert("HIGH", "Worker", wid, "PPE Compliance", f"{r['PPE Compliance (%)']:.0f}%",
                                "Low PPE Compliance", "Review PPE compliance and supervisor controls."))
        if r["Fatigue Level"] >= FATIGUE_HIGH:
            alerts.append(alert("HIGH", "Worker", wid, "Fatigue Level", f"{r['Fatigue Level']:.0f}/5",
                                "High Fatigue Level", "Assess worker fitness for task and apply fatigue controls."))
        if r["Near Misses"] >= REPEATED_EVENTS or r["Previous Incidents"] >= REPEATED_EVENTS:
            alerts.append(alert("HIGH", "Worker", wid, "Safety Observations",
                                f"{r['Near Misses']:.0f} near misses, {r['Previous Incidents']:.0f} previous incidents",
                                "High-risk Safety Observation", "Supervisor follow-up and targeted coaching."))
        if r["Training Status"] == "Expired":
            alerts.append(alert("WARNING", "Worker", wid, "Safety Training", "Expired", "Training Expired",
                                "Book refresher training before the next shift."))
    for r in incidents.to_dict("records"):
        if str(r["Severity"]).lower() == "critical" and str(r["Status"]).lower() != "closed":
            alerts.append(alert("CRITICAL", "Incident", r["Incident ID"], "Severity", "Critical",
                                f"Critical Safety Incident ({r['Status']}) at {r['Location']}",
                                "Follow site emergency, investigation and corrective-action procedures."))
    df = pd.DataFrame(alerts, columns=["Priority", "Source Type", "Source", "Parameter", "Value", "Status", "Recommended Action"])
    return df.sort_values("Priority", key=lambda s: s.map(PRIORITY_ORDER), kind="stable").reset_index(drop=True)


def visible_alerts():
    """Only show alerts for data the logged-in role is allowed to see."""
    allowed = []
    if can("equipment") or can("maintenance"):
        allowed.append("Equipment")
    if can("safety"):
        allowed.append("Worker")
    if can("incidents"):
        allowed.append("Incident")
    a = build_alerts()
    return a[a["Source Type"].isin(allowed)]


def show_alert(r):
    """Alert card laid out like Figure 1 of the brief."""
    msg = (f"**[{r['Priority']}] MINING MONITORING ALERT**  \n"
           f"**{r['Source Type']} ID:** {r['Source']}  \n**Parameter:** {r['Parameter']}  \n**Value:** {r['Value']}  \n"
           f"**Status:** {r['Status']}  \n**Recommended Action:** {r['Recommended Action']}")
    if r["Priority"] == "CRITICAL": st.error(msg, icon=":material/error:")
    elif r["Priority"] == "HIGH": st.warning(msg, icon=":material/warning:")
    else: st.info(msg, icon=":material/info:")


def recommendations():
    """Plain-language recommendations generated from the monitoring results."""
    recs = []
    e, w, a = equipment_view(), workers_view(), build_alerts()
    crit = e[e["Condition"] == "CRITICAL"]["Equipment ID"].tolist()
    if crit: recs.append(f"Stop and inspect {', '.join(crit)}: temperature or vibration is above the critical threshold.")
    overdue = e[e["Maintenance State"] == "Overdue"]["Equipment ID"].tolist()
    if overdue: recs.append(f"Schedule overdue maintenance for {', '.join(overdue)}.")
    low = e[e["Availability (%)"] < AVAILABILITY_LOW]["Equipment ID"].tolist()
    if low: recs.append(f"Investigate low availability (<{AVAILABILITY_LOW}%) on {', '.join(low)}.")
    if len(w):
        lowppe = w[w["PPE Compliance (%)"] < PPE_LOW]
        if len(lowppe): recs.append(f"{len(lowppe)} worker(s) are below {PPE_LOW}% PPE compliance: increase supervisor PPE checks.")
        tired = w[w["Fatigue Level"] >= FATIGUE_HIGH]
        if len(tired): recs.append(f"{len(tired)} worker(s) report high fatigue: review shift rosters and fitness for duty.")
        expired = w[w["Training Status"] == "Expired"]
        if len(expired): recs.append(f"Book refresher safety training for {len(expired)} worker(s) with expired training.")
    open_inc = incidents[incidents["Status"] != "Closed"]
    if len(open_inc): recs.append(f"Close out {len(open_inc)} open/under-review incident(s) and confirm corrective actions.")
    if len(incidents):
        top_cause = incidents["Cause"].value_counts().idxmax()
        recs.append(f"Most common incident cause is '{top_cause}': target it in the next toolbox talks.")
        shift_counts = incidents["Shift"].value_counts()
        if len(shift_counts) > 1 and shift_counts.iloc[0] > shift_counts.iloc[1] * 1.2:
            recs.append(f"{shift_counts.index[0]} shift has noticeably more incidents: review supervision and lighting on that shift.")
    if not recs:
        recs.append("No issues found in the current data. Continue routine monitoring.")
    return recs


# -----------------------------
# Small helpers
# -----------------------------
def kpi_card(label, value, help_text=None):
    st.metric(label, value, help=help_text)


def incidents_with_dates():
    i = incidents.copy()
    i["Date"] = pd.to_datetime(i["Date"], errors="coerce")
    return i


def period_filter(key):
    """Date-range picker for incidents. Returns (start, end) dates."""
    dates = incidents_with_dates()["Date"].dropna()
    first = dates.min().date() if len(dates) else date.today()
    last = max(dates.max().date(), date.today()) if len(dates) else date.today()
    picked = st.date_input("Incident period", value=(first, last), min_value=first, max_value=last, key=key)
    if isinstance(picked, (tuple, list)):
        return (picked[0], picked[1]) if len(picked) == 2 else (picked[0], picked[0]) if picked else (first, last)
    return picked, picked


def in_period(df, start, end):
    return df[(df["Date"].dt.date >= start) & (df["Date"].dt.date <= end)]


def department_risk():
    """Safety risk per department: incidents weighted by severity plus high-risk workers."""
    i = incidents.copy()
    i["Weight"] = i["Severity"].map(SEVERITY_WEIGHT).fillna(1)
    w = workers_view()
    dept_table = pd.DataFrame({
        "Incidents": i.groupby("Department").size(),
        "Severity-weighted Incidents": i.groupby("Department")["Weight"].sum(),
        "High-risk Workers": w[w["Risk Level"] == "High"].groupby("Department").size(),
    }).fillna(0).astype(int)
    dept_table["Safety Risk Score"] = dept_table["Severity-weighted Incidents"] + 2 * dept_table["High-risk Workers"]
    return dept_table.sort_values("Safety Risk Score", ascending=False)


# -----------------------------
# Pages
# -----------------------------
def dashboard():
    page_header("Mining Monitoring Dashboard", "Current safety, incident and equipment status across the operation.")
    w, e, alerts = workers_view(), equipment_view(), build_alerts()
    eq_alerts = alerts[alerts["Source Type"] == "Equipment"]
    c = st.columns(6)
    vals = [len(w), len(incidents), int(w["Near Misses"].sum()), int((w["Risk Level"] == "High").sum()),
            f"{w['PPE Compliance (%)'].mean():.1f}%" if len(w) else "–", len(e)]
    labels = ["Workers", "Safety Incidents", "Near Misses", "High-risk Workers", "Avg PPE Compliance", "Equipment Units"]
    for col, label, value in zip(c, labels, vals):
        with col: kpi_card(label, value)
    c2 = st.columns(5)
    with c2[0]: kpi_card("Equipment Available", int((e["Maintenance Status"].str.lower() == "available").sum()))
    with c2[1]: kpi_card("Under Maintenance", int((e["Maintenance State"] == "Under Maintenance").sum()))
    with c2[2]: kpi_card("Equipment Alerts", len(eq_alerts))
    with c2[3]: kpi_card("Avg Availability", f"{e['Availability (%)'].mean():.1f}%" if len(e) else "–",
                         "Operating Time / (Downtime + Operating Time) × 100")
    with c2[4]: kpi_card("Critical Equip. Alerts", int((eq_alerts["Priority"] == "CRITICAL").sum()))
    left, right = st.columns(2, gap="large")
    with left:
        section("Incidents per month by severity")
        i = incidents_with_dates().dropna(subset=["Date"])
        if len(i):
            monthly = pd.crosstab(i["Date"].dt.strftime("%Y-%m"), i["Severity"])
            sev_cols = [c for c in SEVERITY_WEIGHT if c in monthly.columns]
            bar_chart(monthly[sev_cols], color=[SEVERITY_COLORS[c] for c in sev_cols], x_label="", y_label="Incidents", height=300)
        section("Equipment condition")
        table(e[["Equipment ID", "Equipment Type", "Temperature (°C)", "Vibration (mm/s)", "Condition",
                        "Maintenance State", "Availability (%)"]], width="stretch", hide_index=True)
    with right:
        section("Critical and high alerts")
        top = visible_alerts()
        top = top[top["Priority"].isin(["CRITICAL", "HIGH"])]
        if top.empty:
            st.success("No critical or high alerts.")
        else:
            table(top[["Priority", "Source", "Parameter", "Value", "Status"]], width="stretch", hide_index=True)
    st.caption("Prototype thresholds: temperature <80°C normal, 80–100°C warning, >100°C critical; vibration <5 mm/s normal, 5–8 warning, >8 critical. These are educational thresholds from the assignment and are not actual mine/manufacturer limits.")


def safety_page():
    page_header("Worker Health &amp; Safety", "PPE compliance, fatigue, training and risk level for each worker.")
    tab1, tab2 = st.tabs(["Worker data", "Add worker"])
    w = workers_view()
    with tab1:
        f1, f2 = st.columns(2)
        dept = f1.multiselect("Department", sorted(w["Department"].unique()))
        risk = f2.multiselect("Risk level", ["High", "Medium", "Low"])
        view = w
        if dept: view = view[view["Department"].isin(dept)]
        if risk: view = view[view["Risk Level"].isin(risk)]
        table(view, width="stretch", hide_index=True)
        section("Safety indicators")
        a, b, c, d = st.columns(4)
        a.metric("Average PPE compliance", f"{w['PPE Compliance (%)'].mean():.1f}%" if len(w) else "–")
        b.metric(f"Workers below {PPE_LOW}% PPE", int((w["PPE Compliance (%)"] < PPE_LOW).sum()))
        c.metric("High fatigue workers", int((w["Fatigue Level"] >= FATIGUE_HIGH).sum()))
        d.metric("Training expired/pending", int((w["Training Status"] != "Complete").sum()))
        section("Unsafe conditions")
        unsafe = view[view["Warnings"] != "None"]
        if unsafe.empty:
            st.success("No unsafe conditions found for the selected workers.")
        for r in unsafe.to_dict("records"):
            msg = f"**{r['Worker ID']}** ({r['Job Role']}, {r['Department']}, {r['Shift']} shift) — {r['Warnings']}."
            if r["Risk Level"] == "High": st.error(msg, icon=":material/error:")
            else: st.warning(msg, icon=":material/warning:")
        if len(w):
            section("Average PPE compliance by department")
            bar_chart(w.groupby("Department")["PPE Compliance (%)"].mean())
    with tab2:
        with st.form("add_worker", clear_on_submit=True):
            wid = st.text_input("Worker ID", placeholder="e.g. W031")
            dept2 = st.selectbox("Department", DEPARTMENTS)
            role = st.text_input("Job role")
            shift = st.selectbox("Shift", ["Day", "Night"])
            ppe = st.number_input("PPE compliance (%)", 0, 100, 100)
            training = st.selectbox("Training status", ["Complete", "Expired", "Pending"])
            fatigue = st.slider("Fatigue level (1 = rested, 5 = exhausted)", 1, 5, 1)
            obs = st.number_input("Safety observations", 0, 100, 0)
            near = st.number_input("Near misses", 0, 100, 0)
            prev = st.number_input("Previous incidents", 0, 100, 0)
            submit = st.form_submit_button("Add worker")
            if submit:
                wid = wid.strip().upper()
                if not wid or not role.strip():
                    st.error("Worker ID and job role are required.")
                elif wid in workers["Worker ID"].astype(str).str.upper().values:
                    st.error(f"Worker ID {wid} already exists.")
                else:
                    row = [wid, dept2, role.strip(), shift, ppe, training, fatigue, obs, near, prev]
                    add_record("workers", row, f"Worker {wid} (risk level {worker_risk(dict(zip(COLUMNS['workers'], row)))})")


def incidents_page():
    page_header("Safety Incident Database", "Record, search and analyse safety incidents.")
    tab1, tab2, tab3, tab4 = st.tabs(["Incident records", "Trends & analysis", "Add incident", "Update incident"])
    all_inc = incidents_with_dates()
    with tab1:
        q = st.text_input("Search incidents (any field)")
        f1, f2, f3 = st.columns(3)
        sev = f1.multiselect("Severity", ["Low", "Medium", "High", "Critical"])
        status = f2.multiselect("Status", ["Open", "Under Review", "Closed"])
        dept = f3.multiselect("Department", sorted(all_inc["Department"].unique()))
        start, end = period_filter("inc_period")
        view = in_period(all_inc, start, end)
        if q: view = view[view.astype(str).apply(lambda row: row.str.contains(q, case=False, na=False, regex=False).any(), axis=1)]
        if sev: view = view[view["Severity"].isin(sev)]
        if status: view = view[view["Status"].isin(status)]
        if dept: view = view[view["Department"].isin(dept)]
        a, b, c, d = st.columns(4)
        a.metric("Incidents shown", len(view))
        b.metric("High/Critical", int(view["Severity"].isin(["High", "Critical"]).sum()))
        c.metric("Lost-time injuries", int((view["Lost Time Injury"] == "Yes").sum()))
        d.metric("Open / under review", int((view["Status"] != "Closed").sum()))
        shown = view.copy()
        shown["Date"] = shown["Date"].dt.strftime("%Y-%m-%d")
        table(shown, width="stretch", hide_index=True)
        st.download_button("Download these incidents (CSV)", shown.to_csv(index=False).encode(), "incidents_filtered.csv", "text/csv")
    with tab2:
        start, end = period_filter("trend_period")
        view = in_period(all_inc, start, end)
        if view.empty:
            st.info("No incidents in the selected period.")
        else:
            section("Incident trend")
            monthly = pd.crosstab(view["Date"].dt.to_period("M").astype(str), view["Severity"])
            sev_cols = [c for c in SEVERITY_WEIGHT if c in monthly.columns]
            bar_chart(monthly[sev_cols], color=[SEVERITY_COLORS[c] for c in sev_cols])
            c1, c2 = st.columns(2)
            with c1:
                st.write("Incidents by department")
                bar_chart(view["Department"].value_counts())
                st.write("Most common causes")
                bar_chart(view["Cause"].value_counts().head(8))
            with c2:
                st.write("Incidents by shift")
                bar_chart(view["Shift"].value_counts())
                st.write("Incident types")
                bar_chart(view["Incident Type"].value_counts())
            st.write("Incident types by shift")
            table(pd.crosstab(view["Incident Type"], view["Shift"], margins=True, margins_name="Total"), width="stretch")
    with tab3:
        ids = incidents["Incident ID"].astype(str)
        nums = pd.to_numeric(ids.str.extract(r"(\d+)")[0], errors="coerce")
        next_id = f"I{int(nums.max()) + 1:03d}" if nums.notna().any() else "I001"
        with st.form("incident_form", clear_on_submit=True):
            iid = st.text_input("Incident ID", value=next_id)
            d = st.date_input("Date", value=date.today(), max_value=date.today())
            t = st.time_input("Time")
            shift = st.selectbox("Shift", ["Day", "Night"])
            loc = st.text_input("Location")
            dept = st.selectbox("Department", DEPARTMENTS)
            itype = st.selectbox("Incident type", INCIDENT_TYPES)
            severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
            injury = st.selectbox("Injury", ["No", "Yes"])
            lti = st.selectbox("Lost-time injury", ["No", "Yes"])
            cause = st.text_input("Cause")
            action = st.text_input("Corrective action")
            status = st.selectbox("Status", ["Open", "Under Review", "Closed"])
            submit = st.form_submit_button("Add incident")
            if submit:
                iid = iid.strip().upper()
                if not iid or not loc.strip() or not cause.strip():
                    st.error("Incident ID, location and cause are required.")
                elif iid in ids.str.upper().values:
                    st.error(f"Incident ID {iid} already exists.")
                elif lti == "Yes" and injury == "No":
                    st.error("A lost-time injury must also be recorded as an injury.")
                else:
                    add_record("incidents", [iid, str(d), str(t)[:5], shift, loc.strip(), dept, itype, severity, injury, lti,
                                             cause.strip(), action.strip(), status], f"Incident {iid}")
                    if severity == "Critical":
                        st.error("Critical incident recorded — a CRITICAL alert has been generated.", icon=":material/error:")
    with tab4:
        if incidents.empty:
            st.info("No incidents to update.")
        else:
            with st.form("update_incident"):
                iid = st.selectbox("Incident", incidents["Incident ID"].tolist())
                new_status = st.selectbox("New status", ["Open", "Under Review", "Closed"])
                new_action = st.text_input("Corrective action (leave blank to keep current)")
                if st.form_submit_button("Update incident"):
                    idx = incidents.index[incidents["Incident ID"] == iid][0]
                    incidents.loc[idx, "Status"] = new_status
                    if new_action.strip():
                        incidents.loc[idx, "Corrective Action"] = new_action.strip()
                    save_csv("incidents", f"Incident {iid} updated to '{new_status}'.")


def equipment_page():
    page_header("Equipment &amp; Condition Monitoring", "Equipment register, sensor readings and condition status.")
    tab1, tab2, tab3, tab4 = st.tabs(["Condition monitoring", "Reading history", "Record reading", "Add equipment"])
    e = equipment_view()
    with tab1:
        f1, f2 = st.columns(2)
        types = f1.multiselect("Equipment type", sorted(e["Equipment Type"].unique()))
        cond = f2.multiselect("Condition", ["CRITICAL", "WARNING", "NORMAL", "NO DATA"])
        view = e
        if types: view = view[view["Equipment Type"].isin(types)]
        if cond: view = view[view["Condition"].isin(cond)]
        counts = e["Condition"].value_counts()
        c1, c2, c3 = st.columns(3)
        c1.metric("Normal", int(counts.get("NORMAL", 0)))
        c2.metric("Warning", int(counts.get("WARNING", 0)))
        c3.metric("Critical", int(counts.get("CRITICAL", 0)))
        first = ["Equipment ID", "Equipment Type", "Temperature (°C)", "Vibration (mm/s)", "Condition", "Maintenance State",
                 "Availability (%)", "Last Reading"]
        rest = [c for c in view.columns if c not in first + ["Condition Message", "Maintenance Flags", "Priority Score"]]
        table(view[first + rest], width="stretch", hide_index=True)
        section("Monitoring messages (latest reading)")
        for r in view.sort_values("Condition", key=lambda s: s.map({"CRITICAL": 0, "WARNING": 1})).to_dict("records"):
            msg = f"**{r['Equipment ID']}** ({r['Equipment Type']}) — {r['Temperature (°C)']} °C, {r['Vibration (mm/s)']} mm/s — {r['Condition Message']}"
            if r["Condition"] == "CRITICAL": st.error(msg, icon=":material/error:")
            elif r["Condition"] == "WARNING": st.warning(msg, icon=":material/warning:")
            elif r["Condition"] == "NORMAL": st.success(msg, icon=":material/check_circle:")
            else: st.info(msg)
    with tab2:
        r = readings_view()
        if e.empty or r.empty:
            st.info("No readings recorded yet.")
        else:
            eid = st.selectbox("Equipment", e["Equipment ID"].tolist())
            hist = r[r["Equipment ID"] == eid]
            c1, c2 = st.columns(2)
            with c1:
                st.write("Temperature (°C)")
                line_chart(hist.set_index("Date")["Temperature (°C)"])
            with c2:
                st.write("Vibration (mm/s)")
                line_chart(hist.set_index("Date")["Vibration (mm/s)"])
            shown = hist.copy()
            shown["Date"] = shown["Date"].dt.strftime("%Y-%m-%d")
            table(shown, width="stretch", hide_index=True)
    with tab3:
        if e.empty:
            st.info("Add equipment first.")
        else:
            with st.form("reading_form", clear_on_submit=True):
                eid = st.selectbox("Equipment", e["Equipment ID"].tolist())
                d = st.date_input("Date", value=date.today(), max_value=date.today())
                t = st.number_input("Temperature (°C)", -20.0, 200.0, 70.0, 0.5)
                v = st.number_input("Vibration (mm/s)", 0.0, 50.0, 3.0, 0.1)
                if st.form_submit_button("Record reading"):
                    add_record("readings", [str(d), eid, t, v], f"Reading for {eid}")
                    show_reading_result(t, v)
    with tab4:
        with st.form("equipment_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            eid = c1.text_input("Equipment ID", placeholder="e.g. TRK-020")
            etype = c2.selectbox("Equipment type", EQUIPMENT_TYPES)
            maker = c1.text_input("Manufacturer")
            dept = c2.selectbox("Department", DEPARTMENTS)
            hours = c1.number_input("Operating hours (meter)", 0, 200000, 0)
            fuel = c2.number_input("Fuel consumption (L/h)", 0.0, 500.0, 0.0)
            brake = c1.selectbox("Brake status", ["Good", "Inspect", "Warning", "N/A"])
            tyre = c2.selectbox("Tyre status", ["Good", "Worn", "Inspect", "N/A"])
            engine = c1.selectbox("Engine status", ["Good", "Warning", "Inspect", "N/A"])
            mstatus = c2.selectbox("Maintenance status", ["Available", "Under Maintenance"])
            interval = c1.number_input("Service interval (h)", 1, 10000, 500)
            since = c2.number_input("Hours since last service", 0, 20000, 0)
            optime = c1.number_input("Operating time this period (h)", 0, 744, 700)
            down = c2.number_input("Downtime this period (h)", 0, 744, 0)
            t = c1.number_input("Current temperature (°C)", -20.0, 200.0, 70.0, 0.5)
            v = c2.number_input("Current vibration (mm/s)", 0.0, 50.0, 3.0, 0.1)
            if st.form_submit_button("Add equipment"):
                eid = eid.strip().upper()
                if not eid or not maker.strip():
                    st.error("Equipment ID and manufacturer are required.")
                elif eid in equipment["Equipment ID"].astype(str).str.upper().values:
                    st.error(f"Equipment ID {eid} already exists.")
                elif optime + down > 744:
                    st.error("Operating time plus downtime cannot be more than 744 h (one month).")
                else:
                    add_record("equipment", [eid, etype, maker.strip(), dept, hours, fuel, brake, tyre, engine, mstatus,
                                             interval, since, optime, down], f"Equipment {eid}")
                    add_record("readings", [str(date.today()), eid, t, v], f"First reading for {eid}")
                    st.info(f"Availability: {availability(optime, down)}%")
                    show_reading_result(t, v)


def show_reading_result(t, v):
    status, msg = reading_condition(t, v), condition_message(t, v)
    if status == "CRITICAL": st.error(msg, icon=":material/error:")
    elif status == "WARNING": st.warning(msg, icon=":material/warning:")
    else: st.success(msg, icon=":material/check_circle:")


def maintenance_page():
    page_header("Maintenance Monitoring", "Service status, downtime, availability and maintenance priority.")
    e = equipment_view()
    st.write("Availability is calculated for each machine as:")
    st.latex(r"\text{Availability} = \left(\frac{\text{Operating Time}}{\text{Downtime} + \text{Operating Time}}\right) \times 100")
    a, b, c = st.columns(3)
    a.metric("Due for maintenance", int((e["Maintenance State"] == "Due").sum()),
             help=f"At least {SERVICE_DUE_FRACTION:.0%} of the service interval used")
    b.metric("Overdue", int((e["Maintenance State"] == "Overdue").sum()), help="Hours since service exceed the service interval")
    c.metric("Under maintenance", int((e["Maintenance State"] == "Under Maintenance").sum()))
    d, f, g = st.columns(3)
    d.metric("Excessive downtime", int((e["Downtime (h)"] > DOWNTIME_EXCESSIVE).sum()), help=f"More than {DOWNTIME_EXCESSIVE} h")
    f.metric("Repeated alerts", int((e["Alert Readings"] >= REPEATED_ALERTS).sum()),
             help=f"{REPEATED_ALERTS} or more readings outside normal limits")
    g.metric("Low availability", int((e["Availability (%)"] < AVAILABILITY_LOW).sum()), help=f"Below {AVAILABILITY_LOW}%")
    state = st.multiselect("Show maintenance state", ["Overdue", "Due", "Under Maintenance", "OK"])
    view = e[e["Maintenance State"].isin(state)] if state else e
    table(view[["Equipment ID", "Equipment Type", "Maintenance Status", "Service Interval (h)", "Hours Since Service",
                       "Maintenance State", "Operating Time (h)", "Downtime (h)", "Availability (%)", "Condition",
                       "Alert Readings", "Maintenance Flags"]], width="stretch", hide_index=True)
    section("Maintenance priority")
    pri = e[e["Priority Score"] > 0].sort_values("Priority Score", ascending=False)
    if pri.empty:
        st.success("No equipment currently needs maintenance attention.")
    else:
        table(pri[["Equipment ID", "Equipment Type", "Priority Score", "Maintenance Flags", "Condition"]],
                     width="stretch", hide_index=True)
    section("Availability by equipment")
    if len(e):
        bar_chart(e.set_index("Equipment ID")["Availability (%)"])


def risk_page():
    page_header("Risk Assessment", "Score a hazard using likelihood × consequence on a 1–5 scale.")
    st.write("RiskScore = Likelihood × Consequence, using the assignment's 1–5 scale.")
    c1, c2 = st.columns(2)
    with c1: likelihood = st.slider("Likelihood (1 = rare, 5 = almost certain)", 1, 5, 3)
    with c2: consequence = st.slider("Consequence (1 = insignificant, 5 = catastrophic)", 1, 5, 3)
    score, level = risk_class(likelihood, consequence)
    st.metric("Risk score", score)
    if level == "Critical": st.error(f"CRITICAL RISK — score {score}. Immediate attention is required by the prototype rule.")
    elif level == "High": st.warning(f"HIGH RISK — score {score}. Review controls and corrective actions.")
    elif level == "Medium": st.info(f"MEDIUM RISK — score {score}. Monitor and apply controls.")
    else: st.success(f"LOW RISK — score {score}.")
    section("Classification")
    st.table(pd.DataFrame({"Score range": ["1–4", "5–9", "10–16", "17–25"], "Classification": ["Low", "Medium", "High", "Critical"]}))
    section("Risk matrix")
    matrix = pd.DataFrame([[risk_class(l, c)[0] for c in range(1, 6)] for l in range(5, 0, -1)],
                          index=[f"Likelihood {l}" for l in range(5, 0, -1)], columns=[f"Consequence {c}" for c in range(1, 6)])
    table(matrix, width="stretch")


def risk_class(likelihood, consequence):
    score = int(likelihood) * int(consequence)
    if score <= 4:
        level = "Low"
    elif score <= 9:
        level = "Medium"
    elif score <= 16:
        level = "High"
    else:
        level = "Critical"
    return score, level


def alerts_page():
    page_header("Alerts &amp; Notifications", "Automatically generated alerts from the current monitoring data.")
    alerts = visible_alerts()
    if alerts.empty:
        st.success("No active alerts.")
        return
    a, b, c = st.columns(3)
    a.metric("Critical", int((alerts["Priority"] == "CRITICAL").sum()))
    b.metric("High", int((alerts["Priority"] == "HIGH").sum()))
    c.metric("Warning", int((alerts["Priority"] == "WARNING").sum()))
    f1, f2 = st.columns(2)
    priority = f1.multiselect("Priority", ["CRITICAL", "HIGH", "WARNING"])
    source = f2.multiselect("Source", sorted(alerts["Source Type"].unique()))
    view = alerts
    if priority: view = view[view["Priority"].isin(priority)]
    if source: view = view[view["Source Type"].isin(source)]
    st.download_button("Download alerts CSV", view.to_csv(index=False).encode(), "mining_alerts.csv", "text/csv")
    for r in view.to_dict("records"):
        show_alert(r)


def analytics_page():
    page_header("Interactive Data Analysis", "Answers to key mining engineering questions from the current data.")
    categories = []
    if can("safety") or can("incidents"): categories.append("Health and Safety")
    if can("equipment"): categories.append("Equipment")
    if (can("safety") or can("incidents")) and can("equipment"): categories.append("Integrated Safety and Equipment")
    questions = {
        "Health and Safety": [
            "How many safety incidents occurred during the selected period?",
            "Which department has the highest number of incidents?",
            "Which shift records the most incidents?",
            "What percentage of workers comply with PPE requirements?",
            "How many near misses have been recorded?",
            "Which incident types occur most frequently?",
            "How many incidents are classified as high or critical?",
            "Which departments have the highest safety risk?",
            "Is there an observable difference in incidents between day and night shifts?",
            "Which safety conditions require immediate attention?",
        ],
        "Equipment": [
            "Which equipment has the highest downtime?",
            "Which equipment has the lowest availability?",
            "Which equipment has the highest vibration?",
            "Which equipment has the highest operating temperature?",
            "Which equipment has generated the most alerts?",
            "Which equipment requires maintenance?",
            "Which equipment is overdue for maintenance?",
            "What is the average equipment availability?",
            "Which equipment type has the highest downtime?",
            "Which equipment requires immediate inspection?",
        ],
        "Integrated Safety and Equipment": [
            "Are safety incidents associated with particular shifts?",
            "Which departments have both high safety risk and high equipment downtime?",
            "Which equipment should receive maintenance priority?",
            "What are the most common causes of safety incidents?",
            "Which safety indicators require management intervention?",
            "What percentage of monitored equipment is operating normally?",
            "How many critical alerts are currently active?",
            "Which areas of the operation require the greatest attention?",
            "What recommendations can be generated from the monitoring results?",
        ],
    }
    category = st.radio("Category", categories, horizontal=True)
    question = st.selectbox("Choose a mining engineering question", questions[category])
    section(question)
    w, e = workers_view(), equipment_view()
    i = incidents_with_dates()
    if category == "Health and Safety":
        start, end = period_filter("analysis_period")
        i = in_period(i, start, end)
        st.caption(f"Incident questions use incidents from {start} to {end} ({len(i)} incidents).")

    if question == "How many safety incidents occurred during the selected period?":
        a, b, c = st.columns(3)
        a.metric("Safety incidents", len(i))
        b.metric("With injury", int((i["Injury"] == "Yes").sum()))
        c.metric("Lost-time injuries", int((i["Lost Time Injury"] == "Yes").sum()))
    elif question == "Which department has the highest number of incidents?":
        counts = i["Department"].value_counts().rename("Incident Count")
        if len(counts): st.success(f"**{counts.index[0]}** has the most incidents ({counts.iloc[0]}).")
        bar_chart(counts)
    elif question == "Which shift records the most incidents?":
        counts = i["Shift"].value_counts().rename("Incident Count")
        if len(counts): st.success(f"**{counts.index[0]}** shift records the most incidents ({counts.iloc[0]}).")
        table(counts, width="stretch")
    elif question == "What percentage of workers comply with PPE requirements?":
        a, b = st.columns(2)
        a.metric(f"Workers at or above {PPE_LOW}% PPE compliance", f"{(w['PPE Compliance (%)'] >= PPE_LOW).mean() * 100:.1f}%" if len(w) else "–")
        b.metric("Average PPE compliance", f"{w['PPE Compliance (%)'].mean():.1f}%" if len(w) else "–")
        bar_chart(w.groupby("Department")["PPE Compliance (%)"].mean())
    elif question == "How many near misses have been recorded?":
        a, b = st.columns(2)
        a.metric("Near misses reported by workers", int(w["Near Misses"].sum()))
        b.metric("Near-miss incidents in the period", int((i["Incident Type"] == "Near Miss").sum()))
        bar_chart(w.groupby("Department")["Near Misses"].sum())
    elif question == "Which incident types occur most frequently?":
        counts = i["Incident Type"].value_counts().rename("Count")
        bar_chart(counts)
        table(counts, width="stretch")
    elif question == "How many incidents are classified as high or critical?":
        hc = i[i["Severity"].isin(["High", "Critical"])]
        st.metric("High/Critical incidents", len(hc), f"{len(hc) / len(i) * 100:.0f}% of incidents" if len(i) else None, delta_color="off")
        shown = hc.copy()
        shown["Date"] = shown["Date"].dt.strftime("%Y-%m-%d")
        table(shown, width="stretch", hide_index=True)
    elif question == "Which departments have the highest safety risk?":
        st.write("Safety Risk Score = severity-weighted incidents (Low 1, Medium 2, High 3, Critical 4) + 2 × high-risk workers.")
        table(department_risk(), width="stretch")
    elif question == "Is there an observable difference in incidents between day and night shifts?":
        result = i.groupby("Shift").agg(Incidents=("Incident ID", "count"),
                                       High_or_Critical=("Severity", lambda s: s.isin(["High", "Critical"]).sum()),
                                       Injuries=("Injury", lambda s: (s == "Yes").sum()))
        table(result, width="stretch")
        if len(result) == 2:
            diff = abs(result["Incidents"].iloc[0] - result["Incidents"].iloc[1])
            top = result["Incidents"].idxmax()
            st.info(f"{top} shift has {diff} more incident(s) than the other shift." if diff else "Both shifts have the same number of incidents.")
    elif question == "Which safety conditions require immediate attention?":
        a = build_alerts()
        a = a[a["Source Type"].isin(["Worker", "Incident"]) & a["Priority"].isin(["CRITICAL", "HIGH"])]
        if a.empty: st.success("No safety conditions require immediate attention.")
        for r in a.to_dict("records"): show_alert(r)
    elif question == "Which equipment has the highest downtime?":
        table(e.nlargest(5, "Downtime (h)")[["Equipment ID", "Equipment Type", "Downtime (h)"]], width="stretch", hide_index=True)
    elif question == "Which equipment has the lowest availability?":
        table(e.nsmallest(5, "Availability (%)")[["Equipment ID", "Equipment Type", "Operating Time (h)", "Downtime (h)", "Availability (%)"]], width="stretch", hide_index=True)
    elif question == "Which equipment has the highest vibration?":
        table(e.nlargest(5, "Vibration (mm/s)")[["Equipment ID", "Equipment Type", "Vibration (mm/s)", "Condition"]], width="stretch", hide_index=True)
    elif question == "Which equipment has the highest operating temperature?":
        table(e.nlargest(5, "Temperature (°C)")[["Equipment ID", "Equipment Type", "Temperature (°C)", "Condition"]], width="stretch", hide_index=True)
    elif question == "Which equipment has generated the most alerts?":
        st.write("Number of sensor readings outside normal limits in the reading history:")
        table(e.sort_values("Alert Readings", ascending=False).head(5)[["Equipment ID", "Equipment Type", "Alert Readings", "Condition"]], width="stretch", hide_index=True)
    elif question == "Which equipment requires maintenance?":
        need = e[e["Maintenance Flags"] != "None"]
        table(need[["Equipment ID", "Equipment Type", "Maintenance State", "Maintenance Flags"]], width="stretch", hide_index=True)
    elif question == "Which equipment is overdue for maintenance?":
        over = e[e["Maintenance State"] == "Overdue"]
        if over.empty: st.success("No equipment is overdue for maintenance.")
        else: table(over[["Equipment ID", "Equipment Type", "Service Interval (h)", "Hours Since Service"]], width="stretch", hide_index=True)
    elif question == "What is the average equipment availability?":
        st.metric("Average availability", f"{e['Availability (%)'].mean():.1f}%" if len(e) else "–")
        bar_chart(e.groupby("Equipment Type")["Availability (%)"].mean())
    elif question == "Which equipment type has the highest downtime?":
        table(e.groupby("Equipment Type")["Downtime (h)"].mean().sort_values(ascending=False).rename("Average Downtime (h)"), width="stretch")
    elif question == "Which equipment requires immediate inspection?":
        insp = e[(e["Condition"] == "CRITICAL") | e["Brake Status"].isin(["Inspect", "Warning"]) | e["Engine Status"].isin(["Inspect", "Warning"])]
        if insp.empty: st.success("No equipment requires immediate inspection.")
        else: table(insp[["Equipment ID", "Equipment Type", "Temperature (°C)", "Vibration (mm/s)", "Condition", "Brake Status", "Engine Status"]], width="stretch", hide_index=True)
    elif question == "Are safety incidents associated with particular shifts?":
        table(pd.crosstab(i["Incident Type"], i["Shift"], margins=True, margins_name="Total"), width="stretch")
        bar_chart(pd.crosstab(i["Shift"], i["Severity"])[[c for c in SEVERITY_WEIGHT if c in set(i["Severity"])]],
                  color=[SEVERITY_COLORS[c] for c in SEVERITY_WEIGHT if c in set(i["Severity"])])
    elif question == "Which departments have both high safety risk and high equipment downtime?":
        result = department_risk()[["Safety Risk Score"]].join(e.groupby("Department")["Downtime (h)"].sum().rename("Equipment Downtime (h)"), how="outer").fillna(0)
        both = result[(result["Safety Risk Score"] >= result["Safety Risk Score"].median()) & (result["Equipment Downtime (h)"] > 0)
                     & (result["Equipment Downtime (h)"] >= result["Equipment Downtime (h)"].median())]
        table(result.sort_values("Safety Risk Score", ascending=False), width="stretch")
        if len(both): st.warning(f"Above the median for both safety risk and downtime: **{', '.join(both.index)}**")
        else: st.success("No department is above the median for both.")
    elif question == "Which equipment should receive maintenance priority?":
        st.write("Priority points: critical condition 3, warning 1, overdue 3, due 1, repeated alerts 2, excessive downtime 1, low availability 1, each component issue 1.")
        table(e[e["Priority Score"] > 0].sort_values("Priority Score", ascending=False)[["Equipment ID", "Equipment Type", "Priority Score", "Maintenance Flags"]], width="stretch", hide_index=True)
    elif question == "What are the most common causes of safety incidents?":
        counts = i["Cause"].value_counts().rename("Incidents")
        bar_chart(counts.head(10))
    elif question == "Which safety indicators require management intervention?":
        ind = pd.DataFrame([
            ["Average PPE compliance (%)", round(w["PPE Compliance (%)"].mean(), 1) if len(w) else 0, f">= {PPE_TARGET}", (w["PPE Compliance (%)"].mean() if len(w) else 100) < PPE_TARGET],
            ["Training complete (%)", round((w["Training Status"] == "Complete").mean() * 100, 1) if len(w) else 0, "100", (w["Training Status"] != "Complete").any()],
            ["High-fatigue workers", int((w["Fatigue Level"] >= FATIGUE_HIGH).sum()), "0", (w["Fatigue Level"] >= FATIGUE_HIGH).any()],
            ["Open critical incidents", int(((incidents["Severity"] == "Critical") & (incidents["Status"] != "Closed")).sum()), "0", ((incidents["Severity"] == "Critical") & (incidents["Status"] != "Closed")).any()],
            ["Lost-time injuries", int((incidents["Lost Time Injury"] == "Yes").sum()), "0", (incidents["Lost Time Injury"] == "Yes").any()],
            ["Open / under-review incidents", int((incidents["Status"] != "Closed").sum()), "0", (incidents["Status"] != "Closed").any()],
        ], columns=["Indicator", "Current", "Target", "Intervention"])
        ind["Current"] = ind["Current"].astype(str)
        ind["Intervention"] = ind["Intervention"].map({True: "Required", False: "On target"})
        table(ind, width="stretch", hide_index=True)
    elif question == "What percentage of monitored equipment is operating normally?":
        st.metric("Normal equipment", f"{(e['Condition'] == 'NORMAL').mean() * 100:.1f}%" if len(e) else "–")
        bar_chart(e["Condition"].value_counts())
    elif question == "How many critical alerts are currently active?":
        a = build_alerts()
        crit = a[a["Priority"] == "CRITICAL"]
        st.metric("Critical alerts", len(crit))
        for r in crit.to_dict("records"): show_alert(r)
    elif question == "Which areas of the operation require the greatest attention?":
        inc = incidents.copy()
        inc["Weight"] = inc["Severity"].map(SEVERITY_WEIGHT).fillna(1)
        area = inc.groupby("Location").agg(Incidents=("Incident ID", "count"), Severity_Score=("Weight", "sum"),
                                           Open=("Status", lambda s: (s != "Closed").sum()))
        st.write("Locations ranked by severity-weighted incidents:")
        table(area.sort_values("Severity_Score", ascending=False), width="stretch")
    elif question == "What recommendations can be generated from the monitoring results?":
        for n, rec in enumerate(recommendations(), 1):
            st.write(f"{n}. {rec}")


def reports_page():
    page_header("Reports &amp; Data Export", "Download datasets and a summary report.")
    st.write("Export the datasets and a summary report for inclusion in analysis or reporting.")
    e, w, alerts = equipment_view(), workers_view(), visible_alerts()
    exports = []
    if can("safety"): exports.append(("Workers (with risk levels)", w, "workers_report.csv"))
    if can("incidents"): exports.append(("Incidents", incidents, "incidents_report.csv"))
    if can("equipment"): exports.append(("Equipment (with condition and availability)", e, "equipment_report.csv"))
    exports.append(("Alerts", alerts, "alerts_report.csv"))
    for label, df, filename in exports:
        st.download_button(f"Download {label}", df.to_csv(index=False).encode(), filename, "text/csv", key=f"dl_{filename}")
    section("Current application summary")
    summary = pd.DataFrame({"KPI": ["Total workers", "Safety incidents", "Near misses", "High-risk workers", "Total equipment",
                                    "Average PPE compliance", "Average equipment availability", "Equipment overdue for maintenance",
                                    "Critical alerts"],
                            "Value": [len(w), len(incidents), int(w["Near Misses"].sum()), int((w["Risk Level"] == "High").sum()), len(e),
                                      f"{w['PPE Compliance (%)'].mean():.1f}%" if len(w) else "–",
                                      f"{e['Availability (%)'].mean():.1f}%" if len(e) else "–",
                                      int((e["Maintenance State"] == "Overdue").sum()),
                                      int((alerts["Priority"] == "CRITICAL").sum())]})
    summary["Value"] = summary["Value"].astype(str)
    table(summary, width="stretch", hide_index=True)
    section("Recommendations")
    recs = recommendations()
    for n, rec in enumerate(recs, 1):
        st.write(f"{n}. {rec}")
    text = (f"KHWEZI MINING MONITOR — SUMMARY REPORT ({date.today()})\n\n"
            + "\n".join(f"{k}: {v}" for k, v in zip(summary["KPI"], summary["Value"]))
            + "\n\nRECOMMENDATIONS\n" + "\n".join(f"{n}. {r}" for n, r in enumerate(recs, 1)))
    st.download_button("Download summary report (TXT)", text.encode(), "khwezi_summary_report.txt", "text/plain")


def users_page():
    page_header("User Management", "System users, roles and access permissions.")
    st.warning("This is a classroom prototype. Passwords are stored in the code and are not suitable for a real production system.")
    rows = []
    for username, u in USERS.items(): rows.append([username, u["name"], u["role"], ", ".join(sorted(PERMISSIONS[u["role"]]))])
    table(pd.DataFrame(rows, columns=["Username", "Name", "Role", "Permissions"]), width="stretch", hide_index=True)


def main_app():
    user = USERS[st.session_state.username]
    initials = "".join(part[0] for part in user["name"].split()[:2]).upper()
    st.sidebar.markdown('<div class="kh-brand"><div class="kh-brand-name">KHWEZI MINING</div>'
                        '<div class="kh-brand-sub">Operations Monitor</div></div>'
                        f'<div class="kh-user"><div class="kh-avatar">{initials}</div><div>'
                        f'<div class="kh-user-name">{user["name"]}</div><div class="kh-user-role">{user["role"]}</div></div></div>'
                        '<div class="kh-nav-label">Navigation</div>', unsafe_allow_html=True)
    pages = [("Dashboard", "dashboard"), ("Worker Safety", "safety"), ("Safety Incidents", "incidents"), ("Equipment", "equipment"),
             ("Maintenance", "maintenance"), ("Risk Assessment", "risk"), ("Alerts", "alerts"), ("Analytics", "analytics"),
             ("Reports", "reports"), ("Manage Users", "users")]
    available = [(label, key) for label, key in pages if can(key)]
    selected = st.sidebar.radio("Navigation", [x[0] for x in available], label_visibility="collapsed")
    st.sidebar.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
    if st.sidebar.button("Sign out", icon=":material/logout:", width="stretch"):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
    latest = pd.to_datetime(readings["Date"], errors="coerce").max()
    st.sidebar.markdown(f'<div class="kh-side-foot">Sensor data as of {latest:%d %b %Y}<br>Khwezi Mining Monitor v1.0</div>'
                        if pd.notna(latest) else '<div class="kh-side-foot">Khwezi Mining Monitor v1.0</div>', unsafe_allow_html=True)
    fn = dict(available)[selected]
    {"dashboard": dashboard, "safety": safety_page, "incidents": incidents_page, "equipment": equipment_page,
     "maintenance": maintenance_page, "risk": risk_page, "alerts": alerts_page, "analytics": analytics_page,
     "reports": reports_page, "users": users_page}[fn]()


apply_style()
if not st.session_state.logged_in:
    login_page()
else:
    main_app()

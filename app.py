from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import tomllib

import altair as alt
import pandas as pd
import streamlit as st

from data_service import load_live_data, mask_contact


st.set_page_config(page_title="Jagran Next | Command centre", page_icon="⚡", layout="wide")


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@600;700&display=swap');
    :root { --ink:#17151f; --violet:#6c45f3; --purple:#9b65f7; --acid:#d9ff52; --mist:#f5f2fb; }
    html, body, [class*="st-"] { font-family:'DM Sans', sans-serif; }
    .stApp { background: radial-gradient(circle at 82% 0%, #eee5ff 0, transparent 28%), #fbfafc; color:var(--ink); }
    .block-container { max-width:1440px; padding-top:1.4rem; padding-bottom:3rem; }
    h1,h2,h3 { font-family:'Space Grotesk', sans-serif !important; letter-spacing:-.035em; }
    [data-testid="stSidebar"] { background:#17151f; border-right:0; }
    [data-testid="stSidebar"] * { color:#fff; }
    [data-testid="stSidebar"] hr { border-color:rgba(255,255,255,.12); }
    [data-testid="stMetric"] { background:#fff; border:1px solid #e9e3f3; border-radius:20px; padding:18px 20px; box-shadow:0 10px 35px rgba(50,32,88,.06); }
    [data-testid="stMetricLabel"] { color:#6c6579; font-size:.82rem; }
    [data-testid="stMetricValue"] { font-family:'Space Grotesk'; }
    [data-testid="stMetricValue"] > div { font-size:clamp(1.55rem,2.2vw,2.25rem); }
    [data-testid="stMetricDelta"] { font-size:.72rem; }
    div[data-testid="stVerticalBlockBorderWrapper"] { background:rgba(255,255,255,.82); border-color:#e9e3f3; border-radius:22px; box-shadow:0 12px 40px rgba(50,32,88,.05); }
    .hero { position:relative; overflow:hidden; padding:30px 34px; border-radius:28px; color:#fff; background:linear-gradient(120deg,#17151f 0%,#3a246b 60%,#7045e8 100%); margin-bottom:20px; }
    .hero:after { content:'AI'; position:absolute; right:24px; top:-48px; font:700 180px 'Space Grotesk'; color:rgba(255,255,255,.055); }
    .hero[data-project="mutual_funds"]:after { content:'MF'; }
    .hero-kicker { color:var(--acid); font-size:.76rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; }
    .hero h1 { max-width:760px; margin:.35rem 0 .45rem; font-size:clamp(2rem,4vw,3.7rem); line-height:.98; color:#fff; }
    .hero p { max-width:720px; color:#d9d1eb; margin:0; }
    .live-pill { display:inline-flex; gap:7px; align-items:center; padding:7px 12px; border-radius:999px; background:rgba(217,255,82,.12); color:var(--acid); font-size:.78rem; font-weight:700; margin-top:18px; }
    .live-dot { width:7px; height:7px; border-radius:50%; background:var(--acid); box-shadow:0 0 0 5px rgba(217,255,82,.12); }
    .section-label { color:#7a7187; font-size:.76rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; margin-bottom:2px; }
    .status-success,.status-failed,.status-pending { display:inline-block; padding:3px 9px; border-radius:999px; font-size:12px; font-weight:700; }
    .status-success { background:#e4f8eb; color:#14763a; } .status-failed { background:#fee9eb;color:#a32933; } .status-pending { background:#fff1d7;color:#895d08; }
    .privacy { font-size:.78rem; color:#9f98aa; }
    .stButton button, .stDownloadButton button { border-radius:999px; font-weight:700; }
    div[data-testid="stSegmentedControl"] { margin-bottom:.35rem; }
    div[data-testid="stSegmentedControl"] button { min-height:42px; font-weight:700; }
    </style>
    """,
    unsafe_allow_html=True,
)


def load_api_config() -> dict:
    config_path = Path(__file__).with_name("api_config.toml")
    if not config_path.exists():
        return {}
    with config_path.open("rb") as config_file:
        return tomllib.load(config_file)


def deployment_setting(name: str, config: dict, default: str = "") -> str:
    """Prefer Streamlit Cloud secrets, with api_config.toml as a local fallback."""
    try:
        value = st.secrets.get(name, config.get(name, default))
    except FileNotFoundError:
        value = config.get(name, default)
    return str(value or default).strip()


PROJECTS = {
    "AI Future Bootcamp": {
        "key": "ai_bootcamp",
        "api_config": "ai_bootcamp_api_url",
        "title": "AI Future Bootcamp",
        "date": "26 September 2026",
        "tagline": "Registrations, revenue, payment health and audience geography for the AI learning cohort.",
        "mark": "AI",
    },
    "Mutual Funds Mastery": {
        "key": "mutual_funds",
        "api_config": "mutual_funds_api_url",
        "title": "Mutual Funds Mastery",
        "date": "10 October 2026",
        "tagline": "Registrations, revenue and payment intelligence for the smart-investing workshop.",
        "mark": "MF",
    },
}


def get_live_bundle(api_url: str, page_param: str):
    """Fetch fresh API data on every Streamlit rerun."""
    return load_live_data([api_url], page_param=page_param)


project_name = st.segmented_control(
    "Program dashboard",
    list(PROJECTS),
    default="AI Future Bootcamp",
    key="active_project",
)
project = PROJECTS[project_name]


with st.sidebar:
    st.markdown("## JAGRAN :violet[NEXT]")
    st.caption(f"{project['title']} · command centre")
    st.markdown("---")
    st.markdown("#### Filters")
    status_filter = st.multiselect("Payment status", ["success", "failed", "pending"], default=[])
    mask_pii = st.toggle("Mask personal details", value=True)
    st.markdown("---")
    if st.button("Refresh data", width="stretch"):
        st.rerun()
    st.markdown('<p class="privacy">Each program loads fresh data from its own API on every dashboard rerun.</p>', unsafe_allow_html=True)


api_config = load_api_config()
api_url = deployment_setting(project["api_config"], api_config)
page_param = deployment_setting("page_param", api_config, "page") or "page"

if not api_url or "api.example.com" in api_url:
    st.markdown(
        f"""
        <section class="hero" data-project="{project['key']}">
          <div class="hero-kicker">Jagran Next · Intelligence desk</div>
          <h1>{project['title']}<br>command centre.</h1>
          <p>{project['tagline']} Workshop date: {project['date']}.</p>
          <span class="live-pill">API SETUP REQUIRED</span>
        </section>
        """,
        unsafe_allow_html=True,
    )
    st.warning(f"Add the {project['title']} endpoint to Streamlit Secrets or api_config.toml, then click Refresh data.")
    st.code(f'{project["api_config"]} = "https://your-api-endpoint"', language="toml")
    st.stop()

with st.spinner("Syncing registrations…"):
    bundle = get_live_bundle(api_url, page_param)

df = bundle.records.copy()
if df.empty:
    st.error("The APIs responded, but no registration records were found.")
    st.stop()

states = sorted(df.get("state_name", pd.Series(dtype=str)).dropna().unique().tolist())
with st.sidebar:
    selected_states = st.multiselect("Filter by state", states, placeholder="All states")
    dates = pd.to_datetime(df["created_at"], errors="coerce", utc=True).dt.date if "created_at" in df else pd.Series(dtype="object")
    min_date = dates.min() if not dates.empty else date.today() - timedelta(days=30)
    max_date = dates.max() if not dates.empty else date.today()
    date_range = st.date_input("Registration window", value=(min_date, max_date), min_value=min_date, max_value=max_date)

filtered = df.copy()
if status_filter and "payment_status" in filtered:
    filtered = filtered[filtered["payment_status"].isin(status_filter)]
if selected_states and "state_name" in filtered:
    filtered = filtered[filtered["state_name"].isin(selected_states)]
if len(date_range) == 2 and "created_at" in filtered:
    created_dates = filtered["created_at"].dt.date
    filtered = filtered[(created_dates >= date_range[0]) & (created_dates <= date_range[1])]

st.markdown(
    f"""
    <section class="hero" data-project="{project['key']}">
      <div class="hero-kicker">Jagran Next · Intelligence desk</div>
      <h1>{project['title']}<br>command centre.</h1>
      <p>{project['tagline']} Workshop date: {project['date']}.</p>
      <span class="live-pill"><span class="live-dot"></span>LIVE API · {len(filtered):,} visible records</span>
      <span style="display:none">{project['mark']}</span>
    </section>
    """,
    unsafe_allow_html=True,
)

success = filtered[filtered.get("payment_status", "") == "success"] if "payment_status" in filtered else filtered.iloc[0:0]
revenue = float(success.get("payable_amount", pd.Series(dtype=float)).sum())
success_rate = (len(success) / len(filtered) * 100) if len(filtered) else 0
avg_ticket = revenue / len(success) if len(success) else 0
coupon_orders = int(filtered.get("coupon_code", pd.Series(dtype=str)).replace("Unknown", "").fillna("").ne("").sum())

st.markdown('<div class="section-label">At a glance</div>', unsafe_allow_html=True)
metrics = st.columns(4)
metrics[0].metric("Total registrations", f"{len(filtered):,}", border=True)
metrics[1].metric("Successful payments", f"{len(success):,}", f"{success_rate:.1f}% conversion", border=True)
metrics[2].metric("Collected revenue", f"₹{revenue:,.0f}", f"₹{avg_ticket:,.0f} avg. ticket", border=True)
metrics[3].metric("Coupon orders", f"{coupon_orders:,}", f"{coupon_orders / len(filtered) * 100:.1f}% adoption" if len(filtered) else "0%", border=True)

st.space("small")
left, right = st.columns([1.55, 1], gap="medium")
with left.container(border=True):
    st.markdown("### Registration pulse")
    st.caption("Daily registrations split by payment outcome")
    trend = filtered.dropna(subset=["created_at"]).copy()
    trend["Day"] = trend["created_at"].dt.tz_convert("Asia/Kolkata").dt.floor("D").dt.tz_localize(None)
    trend = trend.groupby(["Day", "payment_status"], as_index=False).size().rename(columns={"size": "Registrations", "payment_status": "Status"})
    line = (
        alt.Chart(trend)
        .mark_area(interpolate="monotone", opacity=.2, line={"strokeWidth": 2.5})
        .encode(
            x=alt.X("Day:T", title=None, axis=alt.Axis(format="%d %b", labelAngle=0)),
            y=alt.Y("Registrations:Q", title=None),
            color=alt.Color("Status:N", scale=alt.Scale(domain=["success", "failed", "pending"], range=["#6c45f3", "#ef6270", "#efb949"]), legend=alt.Legend(orient="top")),
            tooltip=[alt.Tooltip("Day:T", format="%d %b %Y"), "Status:N", "Registrations:Q"],
        )
        .properties(height=280)
    )
    st.altair_chart(line)

with right.container(border=True):
    st.markdown("### Payment health")
    st.caption("Where every registration currently stands")
    payment = filtered.groupby("payment_status", as_index=False).size().rename(columns={"payment_status": "Status", "size": "Registrations"})
    donut = (
        alt.Chart(payment)
        .mark_arc(innerRadius=68, outerRadius=105, cornerRadius=6, padAngle=.025)
        .encode(
            theta="Registrations:Q",
            color=alt.Color("Status:N", scale=alt.Scale(domain=["success", "failed", "pending"], range=["#6c45f3", "#ef6270", "#efb949"]), legend=alt.Legend(orient="bottom")),
            tooltip=["Status:N", "Registrations:Q"],
        )
        .properties(height=280)
    )
    st.altair_chart(donut)

geo, offer = st.columns(2, gap="medium")
with geo.container(border=True):
    st.markdown("### Demand hotspots")
    st.caption("Top states by registrations")
    state_data = filtered.groupby("state_name", as_index=False).size().nlargest(8, "size").rename(columns={"state_name": "State", "size": "Registrations"})
    state_chart = alt.Chart(state_data).mark_bar(cornerRadiusEnd=7, color="#6c45f3").encode(
        x=alt.X("Registrations:Q", title=None, axis=None),
        y=alt.Y("State:N", sort="-x", title=None),
        tooltip=["State:N", "Registrations:Q"],
    ).properties(height=245)
    st.altair_chart(state_chart)

with offer.container(border=True):
    st.markdown("### Offer performance")
    st.caption("Coupon usage and revenue contribution")
    offer_data = filtered.copy()
    offer_data["Offer"] = offer_data["coupon_code"].replace({"Unknown": "No coupon", "": "No coupon"}).fillna("No coupon")
    offer_data = offer_data.groupby("Offer", as_index=False).agg(Orders=("id", "count"), Revenue=("payable_amount", "sum")).nlargest(6, "Orders")
    offer_chart = alt.Chart(offer_data).mark_bar(cornerRadiusEnd=7, color="#9b65f7").encode(
        x=alt.X("Orders:Q", title=None, axis=None), y=alt.Y("Offer:N", sort="-x", title=None), tooltip=["Offer:N", "Orders:Q", alt.Tooltip("Revenue:Q", format=",.0f")]
    ).properties(height=245)
    st.altair_chart(offer_chart)

with st.container(border=True):
    heading, action = st.columns([4, 1], vertical_alignment="center")
    with heading:
        st.markdown("### Registration explorer")
        st.caption("Search, sort and inspect participants. Personal details are masked by default.")
    search = st.text_input("Search registrations", placeholder="Name, city, organisation, order ID…", icon=":material/search:", label_visibility="collapsed")
    shown = filtered.copy()
    if search:
        searchable = shown.astype(str).agg(" ".join, axis=1)
        shown = shown[searchable.str.contains(search, case=False, na=False)]
    if "created_at" in shown:
        shown["created_at"] = pd.to_datetime(shown["created_at"], errors="coerce", utc=True)
        shown = shown.sort_values("created_at", ascending=True, na_position="last", kind="stable")
    if mask_pii:
        if "email" in shown: shown["email"] = shown["email"].map(lambda x: mask_contact(x, "email"))
        if "phone" in shown: shown["phone"] = shown["phone"].map(lambda x: mask_contact(x, "phone"))
    table_columns = [c for c in ["full_name", "created_at", "email", "phone", "age", "college_organisation", "city_name", "state_name", "payment_status", "coupon_code", "payable_amount", "batch_date"] if c in shown]
    st.dataframe(
        shown[table_columns],
        hide_index=True,
        column_config={
            "full_name": st.column_config.TextColumn("Participant", pinned=True),
            "college_organisation": "College / organisation",
            "city_name": "City", "state_name": "State", "payment_status": "Payment",
            "coupon_code": "Coupon", "batch_date": "Batch",
            "payable_amount": st.column_config.NumberColumn("Paid", format="₹ %.2f"),
            "created_at": st.column_config.DatetimeColumn("Registration date (UTC)", format="DD MMM YYYY, hh:mm:ss a"),
        },
        height=430,
    )
    export = shown[table_columns].to_csv(index=False).encode("utf-8")
    st.download_button("Download filtered CSV", export, f"{project['key']}_registrations.csv", "text/csv")

if bundle.warnings:
    with st.expander("API sync notes"):
        for warning in bundle.warnings:
            st.write(warning)
st.caption(f"Last refreshed {bundle.fetched_at.astimezone().strftime('%d %b %Y, %I:%M %p')} · Sources: {', '.join(bundle.sources)}")

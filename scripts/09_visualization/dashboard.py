"""
Kathmandu District TB Dashboard — Streamlit
============================================
Reads live data from the FHIR R4 Reference API (fhir_server.py).
Run the API first:  python3 scripts/api/fhir_server.py
Then launch:        streamlit run scripts/09_visualization/dashboard.py
"""

import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Kathmandu TB Dashboard",
    page_icon="🫁",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  h1, h2, h3 { color: #1c3761; }
  .kpi-card {
    background: #ffffff; border-radius: 10px; padding: 18px 20px;
    border: 1px solid #e5e7eb; border-left: 4px solid #1c3761;
  }
  .kpi-label { font-size: 12px; font-weight: 600; color: #6b7280; margin-bottom: 4px; }
  .kpi-value { font-size: 30px; font-weight: 800; color: #1c3761; line-height: 1.1; }
  .kpi-sub   { font-size: 11px; color: #9ca3af; margin-top: 4px; }
  .section-note { font-size: 11px; color: #9ca3af; font-style: italic; }
</style>
""", unsafe_allow_html=True)

API_BASE = "http://127.0.0.1:8000"

# ── BS month order ─────────────────────────────────────────────────────────────
MONTH_ORDER = ["Baishak", "Jestha", "Asar", "Shrawan", "Bhadra", "Ashwin",
               "Kartik", "Mangsir", "Poush", "Magh", "Falgun", "Chaitra"]

# ── Variable mapping: measure-id-suffix → dataframe column ────────────────────
RATIO_VARS = {
    "new-cases-total":   "new_cases_total",
    "new-cases-female":  "new_cases_female",
    "new-cases-male":    "new_cases_male",
    "relapse-total":     "relapse_total",
    "relapse-female":    "relapse_female",
    "relapse-male":      "relapse_male",
    "total-tb-notified": "total_tb_mf",
    "total-tb-female":   "total_tb_female",
    "total-tb-male":     "total_tb_male",
    "hiv-positive":      "tb_hiv_positive",
    "age-0to4-f":    "age_0to4_f",   "age-0to4-m":    "age_0to4_m",
    "age-5to14-f":   "age_5to14_f",  "age-5to14-m":   "age_5to14_m",
    "age-15to24-f":  "age_15to24_f", "age-15to24-m":  "age_15to24_m",
    "age-25to34-f":  "age_25to34_f", "age-25to34-m":  "age_25to34_m",
    "age-35to44-f":  "age_35to44_f", "age-35to44-m":  "age_35to44_m",
    "age-45to54-f":  "age_45to54_f", "age-45to54-m":  "age_45to54_m",
    "age-55to64-f":  "age_55to64_f", "age-55to64-m":  "age_55to64_m",
    "age-65plus-f":  "age_65plus_f", "age-65plus-m":  "age_65plus_m",
}
COHORT_VARS = {
    "pbc-reg":  "pbc_reg",
    "cured":    "cured",
    "failed":   "failed",
    "died":     "died",
    "ltfu":     "ltfu",
    "not-eval": "not_eval",
}
ALL_VARS = {**RATIO_VARS, **COHORT_VARS}

AGE_GROUPS = ["0–4", "5–14", "15–24", "25–34", "35–44", "45–54", "55–64", "65+"]
AGE_F_COLS = ["age_0to4_f","age_5to14_f","age_15to24_f","age_25to34_f",
              "age_35to44_f","age_45to54_f","age_55to64_f","age_65plus_f"]
AGE_M_COLS = ["age_0to4_m","age_5to14_m","age_15to24_m","age_25to34_m",
              "age_35to44_m","age_45to54_m","age_55to64_m","age_65plus_m"]


# ── Data loading ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    try:
        resp = requests.get(f"{API_BASE}/MeasureReport", timeout=60)
        resp.raise_for_status()
    except Exception as e:
        return pd.DataFrame(), str(e)

    entries = resp.json().get("entry", [])
    records  = {}
    pop_map  = {}

    for entry in entries:
        r = entry.get("resource", {})
        if r.get("resourceType") != "MeasureReport":
            continue

        measure_url = r.get("measure", "")
        suffix      = measure_url.split("nepal-tb-")[-1] if "nepal-tb-" in measure_url else ""
        col         = ALL_VARS.get(suffix)
        if not col:
            continue

        # Extract BS year / month from period extension
        bs_year = bs_month = None
        for ext in r.get("period", {}).get("extension", [{}])[0].get("extension", []):
            if ext.get("url") == "bs-year":  bs_year  = ext.get("valueInteger")
            if ext.get("url") == "bs-month": bs_month = ext.get("valueString")
        if not bs_year or not bs_month:
            continue

        key = (bs_year, bs_month)
        records.setdefault(key, {})

        pops = r.get("group", [{}])[0].get("population", [])

        if suffix in RATIO_VARS:
            numer = pops[0] if pops else {}
            # _count = data-absent-reason (gap month) → store None
            records[key][col] = None if "_count" in numer else numer.get("count", 0)
            if len(pops) > 1 and key not in pop_map:
                pop_map[key] = pops[1].get("count", 0)
        else:
            pop = pops[0] if pops else {}
            records[key][col] = pop.get("count", 0)

    rows = []
    for (yr, mo), cols in records.items():
        row = {"bs_year": yr, "bs_month": mo}
        row["population"] = pop_map.get((yr, mo), None)
        row.update(cols)
        rows.append(row)

    if not rows:
        return pd.DataFrame(), "No MeasureReport entries parsed"

    df = pd.DataFrame(rows)
    df["month_num"] = df["bs_month"].map({m: i for i, m in enumerate(MONTH_ORDER)})
    df = df.sort_values(["bs_year", "month_num"]).reset_index(drop=True)
    df["timeline"] = df["bs_year"].astype(str) + " " + df["bs_month"]

    # Compute derived indicators from raw counts
    df["tsr"]               = (df["cured"]  / df["pbc_reg"]).where(df["pbc_reg"] > 0)
    df["mortality_rate"]    = (df["died"]   / df["pbc_reg"]).where(df["pbc_reg"] > 0)
    df["ltfu_rate"]         = (df["ltfu"]   / df["pbc_reg"]).where(df["pbc_reg"] > 0)
    df["failure_rate"]      = (df["failed"] / df["pbc_reg"]).where(df["pbc_reg"] > 0)
    df["notification_rate"] = (df["new_cases_total"] * 12 / df["population"] * 100_000
                               ).where(df["population"].notna() & (df["population"] > 0))
    df["mf_ratio"]          = (df["new_cases_male"] / df["new_cases_female"]
                               ).where(df["new_cases_female"].notna() & (df["new_cases_female"] > 0))
    df["hiv_pct"]           = (df["tb_hiv_positive"] / df["new_cases_total"] * 100
                               ).where(df["new_cases_total"] > 0)

    return df, None


# ── Load data ─────────────────────────────────────────────────────────────────
with st.spinner("Loading FHIR data from API..."):
    df, err = load_data()

if err or df.empty:
    st.error(f"Cannot connect to FHIR API at {API_BASE}. "
             f"Start the server first:\n\n"
             f"```\ncd scripts/api && python3 fhir_server.py\n```")
    if err:
        st.caption(f"Error: {err}")
    st.stop()


# ── Sidebar ────────────────────────────────────────────────────────────────────
st.sidebar.title("Filters")
all_years = sorted(df["bs_year"].dropna().unique().astype(int).tolist())
sel_years = st.sidebar.multiselect(
    "BS Year", options=all_years, default=all_years)

if not sel_years:
    st.warning("Select at least one year.")
    st.stop()

fd = df[df["bs_year"].isin(sel_years)].copy()

st.sidebar.markdown("---")
st.sidebar.caption(
    f"**Source:** FHIR R4 API  \n"
    f"**Variables:** 32 (26 ratio + 6 cohort)  \n"
    f"**Months:** 60 (BS 2078–2082)  \n"
    f"**GAP months:** Baishak/Jestha/Asar 2078 → DAR"
)


# ── Header ─────────────────────────────────────────────────────────────────────
st.title("Kathmandu District — TB Surveillance Dashboard")
st.caption(
    f"BS {min(sel_years)}–{max(sel_years)} · "
    f"FHIR R4 · {len(fd)} months selected · "
    "Source: Nepal NTP / IIHMS DHIS2"
)
st.divider()


# ── Section 1: KPI Cards ──────────────────────────────────────────────────────
st.subheader("1. Executive Summary")

total_cases  = int(fd["new_cases_total"].sum())
avg_tsr      = fd["tsr"].mean()
avg_notif    = fd["notification_rate"].mean()
avg_mf       = fd["mf_ratio"].mean()

c1, c2, c3, c4 = st.columns(4)
for col, label, value, sub in [
    (c1, "Total New TB Cases",     f"{total_cases:,}",      f"{len(fd)} months"),
    (c2, "Treatment Success Rate", f"{avg_tsr*100:.1f}%",   "Cured / PBC registered"),
    (c3, "Notification Rate",      f"{avg_notif:.1f}",      "per 100,000 population"),
    (c4, "M:F Ratio",              f"{avg_mf:.2f}",         "Male cases / Female cases"),
]:
    col.markdown(
        f'<div class="kpi-card">'
        f'<div class="kpi-label">{label}</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-sub">{sub}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.divider()


# ── Section 2: Trends ─────────────────────────────────────────────────────────
st.subheader("2. Monthly Trends")

TREND_OPTIONS = {
    "New Cases (Total)":           ("new_cases_total",    "Count",         False),
    "New Cases — Female":          ("new_cases_female",   "Count",         False),
    "New Cases — Male":            ("new_cases_male",     "Count",         False),
    "Relapse (Total)":             ("relapse_total",      "Count",         False),
    "Total TB Notified (M+F)":     ("total_tb_mf",        "Count",         False),
    "TB-HIV Positive Count":       ("tb_hiv_positive",    "Count",         False),
    "Notification Rate (/100k)":   ("notification_rate",  "/100k",         False),
    "Treatment Success Rate (TSR)":("tsr",                "Proportion",    True),
    "Mortality Rate":              ("mortality_rate",     "Proportion",    True),
    "LTFU Rate":                   ("ltfu_rate",          "Proportion",    True),
    "M:F Notification Ratio":      ("mf_ratio",           "Ratio",         False),
    "HIV Co-infection %":          ("hiv_pct",            "%",             False),
}

t1, t2 = st.columns([2, 1])
with t1:
    selected_trend = st.selectbox("Select metric", list(TREND_OPTIONS.keys()))
with t2:
    show_all_years = st.checkbox("Compare all years (overlay)", value=False)

col_name, y_label, is_proportion = TREND_OPTIONS[selected_trend]
trend_df = fd[["timeline", "bs_year", "bs_month", col_name]].dropna(subset=[col_name])

if trend_df.empty:
    st.info("No data available for this metric in the selected period.")
else:
    y_vals = trend_df[col_name] * 100 if is_proportion else trend_df[col_name]
    y_display = f"{y_label} (%)" if is_proportion else y_label

    if show_all_years:
        trend_df = df[["timeline", "bs_year", "bs_month", col_name]].dropna(subset=[col_name])
        y_all = trend_df[col_name] * 100 if is_proportion else trend_df[col_name]
        fig = px.line(
            trend_df.assign(y=y_all),
            x="timeline", y="y",
            color="bs_year",
            markers=True,
            labels={"y": y_display, "timeline": "BS Month", "bs_year": "Year"},
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
    else:
        fig = px.line(
            trend_df.assign(y=y_vals),
            x="timeline", y="y",
            markers=True,
            labels={"y": y_display, "timeline": "BS Month"},
            color_discrete_sequence=["#1c3761"],
        )
        fig.add_hline(y=y_vals.mean(), line_dash="dot", line_color="#9ca3af",
                      annotation_text=f"Mean: {y_vals.mean():.2f}")

    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0.01)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(showgrid=False, tickangle=45),
        yaxis=dict(showgrid=True, gridcolor="#f3f4f6"),
        hovermode="x unified", showlegend=show_all_years,
    )
    st.plotly_chart(fig, use_container_width=True)

    if col_name in ["new_cases_female", "new_cases_male", "relapse_female",
                    "relapse_male"] + AGE_F_COLS + AGE_M_COLS:
        st.caption("Gap months (Baishak/Jestha/Asar 2078) excluded — "
                   "data-absent-reason: not-reported in source.")

st.divider()


# ── Section 3: Age-Sex Distribution ──────────────────────────────────────────
st.subheader("3. Age-Sex Distribution of New TB Cases")

# Aggregate across all selected years — no year filter
age_df = fd[AGE_F_COLS + AGE_M_COLS].dropna()

if age_df.empty:
    st.info("No age-sex data available for the selected period.")
else:
    f_vals  = age_df[AGE_F_COLS].sum().values.tolist()
    m_vals  = age_df[AGE_M_COLS].sum().values.tolist()
    total_f = sum(f_vals)
    total_m = sum(m_vals)

    yr_label = (f"BS {min(sel_years)}" if len(sel_years) == 1
                else f"BS {min(sel_years)}–{max(sel_years)}")

    fig_age = go.Figure()
    fig_age.add_trace(go.Bar(
        y=AGE_GROUPS, x=[-v for v in f_vals],
        name="Female", orientation="h",
        marker_color="#e879a0",
        hovertemplate="%{customdata}<extra>Female</extra>",
        customdata=f_vals,
    ))
    fig_age.add_trace(go.Bar(
        y=AGE_GROUPS, x=m_vals,
        name="Male", orientation="h",
        marker_color="#3b82f6",
        hovertemplate="%{x}<extra>Male</extra>",
    ))

    max_val = max(max(f_vals), max(m_vals))
    tick_step = 100 if max_val > 400 else 50
    ticks = list(range(0, int(max_val * 1.2), tick_step))
    tick_vals = [-t for t in reversed(ticks[1:])] + ticks
    tick_text = [str(t) for t in reversed(ticks[1:])] + [str(t) for t in ticks]

    fig_age.update_layout(
        barmode="overlay",
        title=f"{yr_label} — New TB Cases by Age Group  "
              f"(Female: {int(total_f):,} | Male: {int(total_m):,})",
        xaxis=dict(
            title="Case Count",
            tickvals=tick_vals, ticktext=tick_text,
            zeroline=True, zerolinecolor="#374151", zerolinewidth=1.5,
            showgrid=True, gridcolor="#f3f4f6",
        ),
        yaxis=dict(title="Age Group", autorange="reversed"),
        plot_bgcolor="rgba(0,0,0,0.01)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0.5,
                    xanchor="center"),
        height=380,
    )
    st.plotly_chart(fig_age, use_container_width=True)

    a1, a2 = st.columns(2)
    with a1:
        age_summary = pd.DataFrame({
            "Age Group": AGE_GROUPS,
            "Female":    [int(v) for v in f_vals],
            "Male":      [int(v) for v in m_vals],
        })
        age_summary["Total"]      = age_summary["Female"] + age_summary["Male"]
        age_summary["% of Total"] = (age_summary["Total"] /
                                     age_summary["Total"].sum() * 100
                                     ).round(1).astype(str) + "%"
        st.dataframe(age_summary, use_container_width=True, hide_index=True)
    with a2:
        peak_group = AGE_GROUPS[age_summary["Total"].idxmax()]
        peak_pct   = age_summary["% of Total"][age_summary["Total"].idxmax()]
        st.metric("Highest burden age group", peak_group, f"{peak_pct} of period total")
        st.metric("Female share", f"{total_f / (total_f + total_m) * 100:.1f}%")
        st.metric("Male share",   f"{total_m / (total_f + total_m) * 100:.1f}%")
        st.caption("Gap months (Baishak/Jestha/Asar 2078) excluded — DAR.")

st.divider()


# ── Section 4: Treatment Outcomes ────────────────────────────────────────────
st.subheader("4. Treatment Outcomes")

total_pbc  = int(fd["pbc_reg"].sum())
o_cured    = int(fd["cured"].sum())
o_failed   = int(fd["failed"].sum())
o_died     = int(fd["died"].sum())
o_ltfu     = int(fd["ltfu"].sum())
o_not_eval = int(fd["not_eval"].sum())

# ── Row 1: outcome KPI cards ──────────────────────────────────────────────────
st.caption(f"PBC Registered cohort total: **{total_pbc:,}**")
k1, k2, k3, k4, k5 = st.columns(5)
for col, label, val, color in [
    (k1, "Cured",        o_cured,    "#15803d"),
    (k2, "Failed",       o_failed,   "#dc2626"),
    (k3, "Died",         o_died,     "#d97706"),
    (k4, "LTFU",         o_ltfu,     "#7c3aed"),
    (k5, "Not Evaluated",o_not_eval, "#6b7280"),
]:
    pct = val / total_pbc * 100 if total_pbc > 0 else 0
    col.markdown(
        f'<div style="background:#fff; border-radius:8px; padding:12px 14px; '
        f'border:1px solid #e5e7eb; border-left:4px solid {color};">'
        f'<div style="font-size:11px;font-weight:600;color:{color};margin-bottom:4px;">'
        f'{label}</div>'
        f'<div style="font-size:22px;font-weight:800;color:{color};line-height:1.1;">'
        f'{val:,}</div>'
        f'<div style="font-size:11px;color:#9ca3af;margin-top:3px;">'
        f'{pct:.1f}% of cohort</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.write("")

# ── Row 2: horizontal bar + annual TSR ───────────────────────────────────────
b1, b2 = st.columns([1, 1])

with b1:
    outcomes_df = pd.DataFrame({
        "Outcome": ["Cured", "LTFU", "Not Evaluated", "Died", "Failed"],
        "Count":   [o_cured, o_ltfu, o_not_eval, o_died, o_failed],
        "Color":   ["#15803d", "#7c3aed", "#6b7280", "#d97706", "#dc2626"],
    }).sort_values("Count", ascending=True)

    fig_bar = go.Figure(go.Bar(
        x=outcomes_df["Count"],
        y=outcomes_df["Outcome"],
        orientation="h",
        marker_color=outcomes_df["Color"].tolist(),
        text=[f"{v:,}  ({v/total_pbc*100:.1f}%)" for v in outcomes_df["Count"]],
        textposition="outside",
        cliponaxis=False,
    ))
    fig_bar.update_layout(
        title="Outcome Counts (sorted)",
        xaxis=dict(
            title="Count",
            showgrid=True, gridcolor="#f3f4f6",
            range=[0, outcomes_df["Count"].max() * 1.25],
        ),
        yaxis=dict(showgrid=False),
        plot_bgcolor="rgba(0,0,0,0.01)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=80, t=40, b=10),
        height=280,
        showlegend=False,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with b2:
    yearly_tsr = fd.groupby("bs_year").apply(
        lambda g: pd.Series({
            "TSR (%)": round(g["cured"].sum() / g["pbc_reg"].sum() * 100, 1)
            if g["pbc_reg"].sum() > 0 else 0
        })
    ).reset_index()
    yearly_tsr["BS Year"] = yearly_tsr["bs_year"].astype(int)

    fig_tsr = px.bar(
        yearly_tsr, x="BS Year", y="TSR (%)",
        text_auto=".1f",
        color_discrete_sequence=["#15803d"],
        labels={"TSR (%)": "TSR (%)"},
        title="Treatment Success Rate by Year",
    )
    fig_tsr.update_traces(textposition="outside")
    fig_tsr.update_layout(
        plot_bgcolor="rgba(0,0,0,0.01)", paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=10, r=10, t=40, b=10),
        xaxis=dict(type="category", showgrid=False),
        yaxis=dict(range=[0, 100], showgrid=True, gridcolor="#f3f4f6",
                   title="TSR (%)"),
        height=280,
    )
    st.plotly_chart(fig_tsr, use_container_width=True)

st.divider()
st.caption(
    "Data source: Nepal NTP DHIS2 → FHIR R4 MeasureReport pipeline · "
    "Kathmandu District · BS 2078–2082 · "
    "FHIR canonical: https://iihms.gov.np/fhir"
)

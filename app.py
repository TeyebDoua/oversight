import streamlit as st
import pandas as pd
import plotly.express as px
import io
import os
import base64
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER

from analysis import (
    compute_variance, detect_bias_pattern, load_and_analyse,
)


st.set_page_config(
    page_title="OVERSIGHT",
    page_icon="◆",
    layout="wide",
)





# ----- global CSS (burgundy dark theme) -----
st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@1,700;1,900&family=Inter:wght@300;400;600;700&display=swap" rel="stylesheet">

<style>
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    html, body, [class*="css"] {{
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }}

    .block-container {{
        padding-top: 3rem;
        padding-bottom: 3rem;
        max-width: 1400px;
    }}

    .hero {{
        background: linear-gradient(135deg, #001f3f 0%, #5b3e0f 55%, #0a3a6b 100%);
        padding: 26px 40px;
        border-radius: 14px;
        margin-bottom: 24px;
        box-shadow: 0 10px 32px rgba(101, 1, 23, 0.45);
        border: 1px solid rgba(194, 65, 90, 0.3);
        display: flex;
        align-items: center;
        gap: 26px;
    }}
    .hero-logo-card {{
        flex-shrink: 0;
        background: #f4eef0;
        padding: 12px 18px;
        border-radius: 12px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.35);
        display: flex;
        align-items: center;
    }}
    .hero-logo-card img {{
        height: 64px;
        display: block;
    }}
    .hero-content {{
        flex-grow: 1;
    }}
    .hero-tagline {{
        color: #e8c468;
        font-size: 16px;
        margin: 0;
        font-weight: 300;
        letter-spacing: 1px;
    }}
    .hero-meta {{
        color: rgba(255,255,255,0.6);
        font-size: 11px;
        margin-top: 14px;
        letter-spacing: 2px;
        text-transform: uppercase;
        border-top: 1px solid rgba(255,255,255,0.15);
        padding-top: 10px;
    }}

    .section-header {{
        color: #eef2f7;
        font-size: 22px;
        font-weight: 700;
        margin: 24px 0 8px 0;
        padding-left: 12px;
        border-left: 4px solid #c9962e;
        letter-spacing: 0.5px;
    }}
    .section-subtitle {{
        color: #8fa3bd;
        font-size: 14px;
        font-weight: 400;
        margin-bottom: 16px;
        padding-left: 16px;
    }}

    [data-testid="stMetricValue"] {{
        font-size: 32px !important;
        font-weight: 700 !important;
        color: #eef2f7 !important;
    }}
    [data-testid="stMetricLabel"] {{
        font-size: 12px !important;
        text-transform: uppercase !important;
        letter-spacing: 1.5px !important;
        color: #8fa3bd !important;
        font-weight: 500 !important;
    }}
    [data-testid="stMetricDelta"] {{
        font-size: 13px !important;
    }}
    [data-testid="metric-container"] {{
        background: #0a1420;
        border: 1px solid #13243a;
        border-top: 3px solid #5b3e0f;
        border-radius: 8px;
        padding: 16px 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }}
    [data-testid="metric-container"]:hover {{
        border-top-color: #c9962e;
        transition: border-top-color 0.3s ease;
    }}

    [data-testid="stTabs"] [data-baseweb="tab-list"] {{
        gap: 4px;
        border-bottom: 1px solid #13243a;
        margin-bottom: 24px;
    }}
    [data-testid="stTabs"] [data-baseweb="tab"] {{
        background: transparent;
        color: #8fa3bd;
        font-size: 14px;
        font-weight: 600;
        letter-spacing: 1px;
        padding: 12px 22px;
        border-radius: 0;
        border-bottom: 3px solid transparent;
        transition: all 0.2s ease;
    }}
    [data-testid="stTabs"] [data-baseweb="tab"]:hover {{
        color: #eef2f7;
        background: rgba(194, 65, 90, 0.06);
    }}
    [data-testid="stTabs"] [aria-selected="true"] {{
        color: #c9962e !important;
        border-bottom: 3px solid #c9962e !important;
        background: transparent !important;
    }}

    [data-testid="stSidebar"] {{
        background: #0a0406;
        border-right: 1px solid #13243a;
    }}
    .sidebar-logo-card {{
        background: #f4eef0;
        padding: 12px;
        border-radius: 10px;
        margin-bottom: 18px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    }}
    .sidebar-logo-card img {{
        width: 100%;
        max-width: 160px;
        display: block;
        margin: 0 auto;
    }}
    [data-testid="stSidebar"] h2 {{
        color: #c9962e !important;
        font-size: 11px !important;
        text-transform: uppercase !important;
        letter-spacing: 2px !important;
        font-weight: 700 !important;
        margin-top: 16px !important;
        padding-bottom: 4px !important;
        border-bottom: 1px solid #13243a !important;
    }}

    .stDownloadButton button, .stButton button {{
        background: linear-gradient(135deg, #5b3e0f, #0a3a6b);
        color: white !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 10px 20px !important;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(101, 1, 23, 0.4);
    }}
    .stDownloadButton button:hover, .stButton button:hover {{
        background: linear-gradient(135deg, #0a3a6b, #c9962e) !important;
        box-shadow: 0 4px 12px rgba(194, 65, 90, 0.5) !important;
        transform: translateY(-1px);
    }}

    [data-testid="stDataFrame"] {{
        border: 1px solid #13243a;
        border-radius: 8px;
        overflow: hidden;
    }}

    hr {{ border-color: #13243a !important; }}

    .active-strip {{
        background: linear-gradient(135deg, #001f3f 0%, #5b3e0f 100%);
        color: #ffffff;
        padding: 14px 22px;
        border-radius: 8px;
        display: inline-block;
        margin: 4px 0 20px 0;
        font-size: 14px;
        border: 1px solid rgba(194, 65, 90, 0.35);
        box-shadow: 0 4px 12px rgba(101, 1, 23, 0.45);
    }}
    .active-strip-label {{
        color: rgba(255,255,255,0.7);
        font-size: 10px;
        text-transform: uppercase;
        letter-spacing: 2px;
        font-weight: 600;
    }}
    .active-strip-value {{
        font-size: 17px;
        font-weight: 700;
        margin-top: 2px;
        letter-spacing: 0.5px;
    }}
    .active-strip-meta {{
        color: rgba(255,255,255,0.6);
        font-size: 11px;
        margin-top: 6px;
        letter-spacing: 1px;
    }}

    [data-testid="stExpander"] {{
        border: 1px solid #13243a;
        border-radius: 8px;
        background: #0a1420;
    }}

    .oversight-footer {{
        text-align: center;
        color: #5c7characters;
        font-size: 11px;
        letter-spacing: 1px;
        margin-top: 40px;
        padding-top: 20px;
        border-top: 1px solid #13243a;
        text-transform: uppercase;
    }}
    .oversight-footer-brand {{
        font-family: 'Playfair Display', Georgia, serif;
        font-style: italic;
        font-weight: 900;
        color: #c9962e;
        letter-spacing: 2px;
        font-size: 14px;
    }}

    /* ---- login screen ---- */
    .login-wrap {{
        max-width: 420px;
        margin: 6vh auto 0 auto;
        background: linear-gradient(160deg, #0a1420 0%, #05080d 100%);
        border: 1px solid #13243a;
        border-radius: 16px;
        padding: 36px 36px 30px 36px;
        box-shadow: 0 16px 50px rgba(0,0,0,0.5);
        text-align: center;
    }}
    .login-logo-card {{
        background: #f4eef0;
        padding: 16px 20px;
        border-radius: 12px;
        display: inline-block;
        margin-bottom: 22px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.4);
    }}
    .login-logo-card img {{ height: 70px; display: block; }}
    .login-sub {{
        color: #8fa3bd;
        font-size: 13px;
        letter-spacing: 1px;
        margin-bottom: 26px;
    }}
    .login-foot {{
        color: #6a4a52;
        font-size: 10px;
        letter-spacing: 1px;
        margin-top: 22px;
        text-transform: uppercase;
    }}
</style>
""", unsafe_allow_html=True)


# ============================================================
# LOGIN GATE
# ============================================================
VALID_USERNAME = "auditor"
VALID_PASSWORD = "oversight2026"

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False


def render_login():
    col_x, col_y, col_z = st.columns([1, 2, 1])
    with col_y:
        try:
            st.image("logo.png", use_container_width=True)
        except Exception:
            st.markdown("## OVERSIGHT")
        st.markdown(
            '<div style="text-align:center; color:#8fa3bd; font-size:13px; '
            'letter-spacing:1px; margin-bottom:20px;">'
            'Audit-grade retrospective review of accounting estimates</div>',
            unsafe_allow_html=True,
        )

    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Sign In", use_container_width=True):
            if username == VALID_USERNAME and password == VALID_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid credentials. Please try again.")
        st.markdown(
            '<div class="login-foot">Tunis Business School · 2026</div>',
            unsafe_allow_html=True,
        )


if not st.session_state.authenticated:
    render_login()
    st.stop()


# ============================================================
# MAIN APP (only reached after login)
# ============================================================

# hero banner
hero_col1, hero_col2 = st.columns([1, 4])
with hero_col1:
    try:
        st.image("logo.png", width=200)
    except Exception:
        st.markdown("### OVERSIGHT")
with hero_col2:
    st.markdown("""
    <div style="padding-top: 18px;">
        <p style="color:#e8c468; font-size:18px; font-weight:300; letter-spacing:1px; margin:0;">
            Audit-grade retrospective review of accounting estimates
        </p>
        <p style="color:#8fa3bd; font-size:11px; letter-spacing:2px; text-transform:uppercase; margin-top:10px;">
            ◆ ISA 540 (Revised) operationalisation · Pattern detection · Statistical significance · Industry benchmarking
        </p>
    </div>
    """, unsafe_allow_html=True)

with st.expander("About OVERSIGHT"):
    st.markdown(
        """
        **What it does.** OVERSIGHT implements the retrospective review requirement of
        ISA 540 (Revised). For each accounting estimate, it compares what management
        forecasted with what actually happened, then flags estimates that miss
        consistently in the same direction year after year.

        **The three layers of OVERSIGHT:**
        - **Supervisory oversight** — supports the auditor's review function
        - **Overlooked oversight** — surfaces errors that traditional review misses
        - **Looking over time** — analyses patterns across multiple fiscal years

        **Required CSV columns:** `estimate_id`, `category`, `fy`, `mgmt_value`, `actual_value`.
        """
    )


# sidebar logo
try:
    st.sidebar.image("logo.png", use_container_width=True)
except Exception:
    st.sidebar.markdown("### OVERSIGHT")

# logout
if st.sidebar.button("Sign out"):
    st.session_state.authenticated = False
    st.rerun()


st.sidebar.header("Data Input")

uploaded_files = st.sidebar.file_uploader(
    "Upload one or more CSV files",
    type=["csv"],
    accept_multiple_files=True,
)

use_sample = st.sidebar.checkbox(
    "Use sample data instead",
    value=True if not uploaded_files else False,
)


st.sidebar.header("Materiality")

materiality = st.sidebar.number_input(
    "Materiality threshold (monetary units)",
    min_value=0, value=0, step=10000,
)





def load_companies():
    required = {"estimate_id", "category", "fy", "mgmt_value", "actual_value"}
    companies = {}

    if use_sample:
        try:
            detailed, summary = load_and_analyse("sample_estimates.csv", materiality=materiality)
            companies["Sample Company"] = (detailed, summary)
            st.sidebar.info("Using sample data")
        except Exception as e:
            st.error(f"Could not load sample data: {e}")
            st.stop()
        return companies

    if not uploaded_files:
        st.info("Please upload one or more CSV files, or check 'Use sample data instead'.")
        st.stop()

    successful = 0
    for f in uploaded_files:
        company_name = os.path.splitext(f.name)[0]
        try:
            raw = pd.read_csv(f)
        except Exception as e:
            st.sidebar.warning(f"Skipped '{f.name}': {e}")
            continue

        missing = required - set(raw.columns)
        if missing:
            st.sidebar.warning(f"Skipped '{f.name}': missing {', '.join(missing)}")
            continue

        detailed = compute_variance(raw)
        summary = detect_bias_pattern(detailed, materiality=materiality)
        companies[company_name] = (detailed, summary)
        successful += 1

    if successful == 0:
        st.error("No valid CSV files were uploaded.")
        st.stop()

    st.sidebar.success(f"Loaded {successful} compan{'y' if successful == 1 else 'ies'}")
    return companies


companies = load_companies()


st.sidebar.header("Active Company")

company_names = list(companies.keys())
selected_company = st.sidebar.selectbox("Choose a company to inspect", options=company_names)
detailed, summary = companies[selected_company]


materiality_line = f'<div class="active-strip-meta">Materiality threshold: {materiality:,.0f}</div>' if materiality > 0 else ""

st.markdown(
    f"""
    <div class="active-strip">
        <div class="active-strip-label">◆ Active Engagement</div>
        <div class="active-strip-value">{selected_company}</div>
        <div class="active-strip-meta">{len(summary)} estimate(s) under review</div>
        {materiality_line}
    </div>
    """,
    unsafe_allow_html=True,
)


st.sidebar.header("Filters")

flag_filter = st.sidebar.multiselect(
    "Show flags",
    options=["red", "amber", "green", "below_materiality"],
    default=["red", "amber", "green", "below_materiality"],
)

all_categories = sorted(summary["category"].unique().tolist())
category_filter = st.sidebar.multiselect("Categories", options=all_categories, default=all_categories)

year_min = int(detailed["fy"].min())
year_max = int(detailed["fy"].max())
if year_min < year_max:
    year_range = st.sidebar.slider(
        "Fiscal year range", min_value=year_min, max_value=year_max, value=(year_min, year_max),
    )
else:
    year_range = (year_min, year_max)


filtered_summary = summary[
    (summary["flag"].isin(flag_filter)) &
    (summary["category"].isin(category_filter))
].copy()

filtered_detailed = detailed[
    (detailed["category"].isin(category_filter)) &
    (detailed["fy"] >= year_range[0]) &
    (detailed["fy"] <= year_range[1])
].copy()


st.sidebar.header("Export")

if len(filtered_summary) > 0:
    export_df = filtered_summary.copy()
    export_df.insert(0, "company", selected_company)
    csv_buffer = io.StringIO()
    export_df.to_csv(csv_buffer, index=False)
    safe_filename = selected_company.replace(" ", "_").lower()
    st.sidebar.download_button(
        label="Download bias summary",
        data=csv_buffer.getvalue(),
        file_name=f"{safe_filename}_bias_summary.csv",
        mime="text/csv",
    )


def generate_working_paper_pdf(company_name, estimate_summary, estimate_history, materiality=0):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=1.5 * cm, leftMargin=1.5 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title", parent=styles["Heading1"], fontSize=18,
        textColor=colors.HexColor("#5b3e0f"), spaceAfter=4, alignment=TA_LEFT, leading=22)
    brand_style = ParagraphStyle("Brand", parent=styles["Normal"], fontSize=11,
        textColor=colors.HexColor("#c9962e"), spaceAfter=4, fontName="Helvetica-Bold")
    subtitle_style = ParagraphStyle("Subtitle", parent=styles["Normal"], fontSize=10,
        textColor=colors.HexColor("#666666"), spaceAfter=14)
    section_style = ParagraphStyle("Section", parent=styles["Heading3"], fontSize=11,
        textColor=colors.HexColor("#5b3e0f"), spaceBefore=8, spaceAfter=4)
    body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9.5, leading=13, spaceAfter=6)

    flag = estimate_summary["flag"]
    flag_colors_map = {
        "red": colors.HexColor("#dc2626"),
        "amber": colors.HexColor("#f59e0b"),
        "green": colors.HexColor("#10b981"),
        "below_materiality": colors.HexColor("#6b7280"),
    }
    flag_color = flag_colors_map.get(flag, colors.grey)

    elements = []
    elements.append(Paragraph("◆ OVERSIGHT", brand_style))
    elements.append(Paragraph("Audit Working Paper", title_style))
    elements.append(Paragraph(
        f"Retrospective review of accounting estimate under ISA 540 (Revised) — "
        f"generated {datetime.now().strftime('%d %B %Y')}",
        subtitle_style,
    ))

    elements.append(Paragraph("Identification", section_style))
    id_data = [
        ["Company / Engagement", str(company_name)],
        ["Estimate ID", str(estimate_summary["estimate_id"])],
        ["Estimate category", str(estimate_summary["category"])],
        ["Years analysed", str(int(estimate_summary["years_count"]))],
        ["Materiality threshold", f"{materiality:,.0f}" if materiality > 0 else "Not set"],
    ]
    id_table = Table(id_data, colWidths=[5 * cm, 11 * cm])
    id_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f8f9fa")),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#212529")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dee2e6")),
    ]))
    elements.append(id_table)

    elements.append(Spacer(1, 10))
    elements.append(Paragraph("Flag and pattern", section_style))
    flag_text = f"{flag.upper().replace('_', ' ')} – {estimate_summary['pattern_label']}"
    flag_table = Table([[flag_text]], colWidths=[16 * cm])
    flag_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), flag_color),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.white),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
    ]))
    elements.append(flag_table)

    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Statistical significance", section_style))
    p_val = estimate_summary["p_value"]
    p_text = estimate_summary["p_interpretation"]
    elements.append(Paragraph(f"<b>p-value (one-sided binomial test):</b> {p_val:.4f}", body_style))
    elements.append(Paragraph(f"<i>{p_text}</i>", body_style))

    elements.append(Paragraph("Year-by-year history", section_style))
    history_sorted = estimate_history.sort_values("fy")

    history_data = [[
        "Fiscal year", "Management estimate", "Actual outcome",
        "Variance", "Variance %", "Direction",
    ]]
    for _, row in history_sorted.iterrows():
        history_data.append([
            str(int(row["fy"])),
            f"{row['mgmt_value']:,.0f}",
            f"{row['actual_value']:,.0f}",
            f"{row['variance']:,.0f}",
            f"{row['variance_pct']:.2f}",
            str(row["direction"]),
        ])

    history_table = Table(history_data, colWidths=[
        2.4 * cm, 3.3 * cm, 3.3 * cm, 2.8 * cm, 2.0 * cm, 2.2 * cm
    ])
    history_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#5b3e0f")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ALIGN", (1, 1), (-2, -1), "RIGHT"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (-1, 0), (-1, -1), "CENTER"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dee2e6")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
    ]))
    elements.append(history_table)

    elements.append(Spacer(1, 8))
    elements.append(Paragraph("Suggested next audit procedure", section_style))

    if flag == "red":
        if estimate_summary["dominant_direction"] == "under":
            procedure_text = (
                "<b>Investigate possible income smoothing risk.</b> Management has under-estimated "
                "this allowance every year, which may indicate systematic under-reserving. "
                "ISA 540 (Revised) paragraph 32 requires the auditor to evaluate indicators of "
                "management bias.<br/><br/>"
                "<b>Suggested procedures:</b><br/>"
                "1. Interview management on the methodology and assumption-setting process.<br/>"
                "2. Recompute the estimate with an independent benchmark.<br/>"
                "3. Discuss with those charged with governance.<br/>"
                "4. Document the bias indicator and the auditor's evaluation."
            )
        elif estimate_summary["dominant_direction"] == "over":
            procedure_text = (
                "<b>Investigate possible cookie-jar reserve risk.</b> Management has over-estimated "
                "this allowance every year, which may indicate systematic over-reserving for later "
                "release. ISA 540 (Revised) paragraph 32 requires the auditor to evaluate indicators "
                "of management bias.<br/><br/>"
                "<b>Suggested procedures:</b><br/>"
                "1. Interview management on why estimates are consistently above outcomes.<br/>"
                "2. Examine subsequent-period releases of the allowance.<br/>"
                "3. Discuss with those charged with governance.<br/>"
                "4. Document the bias indicator and the auditor's evaluation."
            )
        else:
            procedure_text = (
                "<b>Investigate the directional pattern.</b> "
                "Document the auditor's evaluation under ISA 540 (Revised) paragraph 32."
            )
    elif flag == "amber":
        procedure_text = (
            "<b>Document and continue monitoring.</b> A partial directional pattern was detected. "
            "This may reflect estimation noise rather than bias, but ISA 540 (Revised) requires "
            "the auditor to remain alert.<br/><br/>"
            "<b>Suggested procedures:</b><br/>"
            "1. Document the observation in the working papers.<br/>"
            "2. Discuss with management as part of the regular estimate review.<br/>"
            "3. Re-evaluate next year to see if the pattern strengthens or dissolves."
        )
    elif flag == "below_materiality":
        procedure_text = (
            "<b>Below materiality threshold.</b> The maximum absolute variance does not exceed "
            "the set materiality. No further investigation is required at this materiality level.<br/><br/>"
            "<b>Suggested procedures:</b><br/>"
            "1. Document the conclusion that the estimate is below materiality.<br/>"
            "2. Re-evaluate if materiality is revised downward in future periods."
        )
    else:
        procedure_text = (
            "<b>No bias pattern detected.</b> Variances are within reasonable bounds and do not "
            "consistently favour one direction. Standard ISA 540 procedures apply: test the method, "
            "the assumptions, and the data underlying the current-year estimate."
        )

    elements.append(Paragraph(procedure_text, body_style))

    elements.append(Spacer(1, 14))
    sig_data = [
        ["Prepared by", "_____________________________", "Date", "_____________"],
        ["", "", "", ""],
        ["Reviewed by", "_____________________________", "Date", "_____________"],
    ]
    sig_table = Table(sig_data, colWidths=[3 * cm, 6 * cm, 1.8 * cm, 3.2 * cm])
    sig_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    elements.append(sig_table)

    elements.append(Spacer(1, 6))
    elements.append(Paragraph(
        "<i>Generated by OVERSIGHT — ISA 540 (Revised) operationalisation.</i>",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=7.5,
            textColor=colors.HexColor("#868e96"), alignment=TA_CENTER),
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()


total = len(filtered_summary)
red_count = int((filtered_summary["flag"] == "red").sum()) if total > 0 else 0
amber_count = int((filtered_summary["flag"] == "amber").sum()) if total > 0 else 0
green_count = int((filtered_summary["flag"] == "green").sum()) if total > 0 else 0
below_count = int((filtered_summary["flag"] == "below_materiality").sum()) if total > 0 else 0

red_pct = (red_count / total * 100) if total > 0 else 0
amber_pct = (amber_count / total * 100) if total > 0 else 0
green_pct = (green_count / total * 100) if total > 0 else 0

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.metric("Estimates reviewed", total)
with col2:
    st.metric("Red flags", red_count, delta=f"{red_pct:.0f}% of total", delta_color="off")
with col3:
    st.metric("Amber flags", amber_count, delta=f"{amber_pct:.0f}% of total", delta_color="off")
with col4:
    st.metric("Green", green_count, delta=f"{green_pct:.0f}% of total", delta_color="off")
with col5:
    st.metric("Below materiality", below_count)


tab_overview, tab_multi, tab_detail, tab_methodology = st.tabs(
    ["OVERVIEW", "PORTFOLIO", "DETAIL", "METHODOLOGY"]
)


with tab_overview:
    st.markdown('<div class="section-header">Bias Pattern Summary</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Each estimate is evaluated against its history of '
        'management estimates vs. actual outcomes. The p-value tests the null hypothesis of '
        'unbiased estimation — a low p-value (below 0.10) indicates the directional pattern '
        'is unlikely to be random chance.</div>',
        unsafe_allow_html=True,
    )

    def colour_flag(val):
        if val == "red":
            return "background-color: #dc2626; color: white; font-weight: bold;"
        elif val == "amber":
            return "background-color: #f59e0b; color: white; font-weight: bold;"
        elif val == "green":
            return "background-color: #10b981; color: white;"
        elif val == "below_materiality":
            return "background-color: #6b7280; color: white;"
        return ""

    if len(filtered_summary) == 0:
        st.info("No estimates match the current filters. Adjust the filters in the sidebar.")
    else:
        display_summary = filtered_summary[[
            "estimate_id", "category", "years_count",
            "dominant_direction", "pattern_score",
            "avg_variance_pct", "max_abs_variance",
            "p_value", "flag", "pattern_label",
        ]].copy()

        display_summary.columns = [
            "Estimate ID", "Category", "Years",
            "Dominant direction", "Pattern score",
            "Avg variance %", "Max abs variance",
            "p-value", "Flag", "Pattern label",
        ]

        display_summary["Max abs variance"] = display_summary["Max abs variance"].apply(
            lambda x: f"{x:,.0f}"
        )
        display_summary["p-value"] = display_summary["p-value"].apply(
            lambda x: f"{x:.4f}"
        )

        styled = display_summary.style.map(colour_flag, subset=["Flag"])
        st.dataframe(styled, use_container_width=True, hide_index=True)

        st.markdown('<div class="section-header">Variance Over Time</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-subtitle">Each panel shows one estimate. A line that stays '
            'on the same side of zero across years is the visual signature of directional bias.</div>',
            unsafe_allow_html=True,
        )

        chart_data = filtered_detailed.merge(
            filtered_summary[["estimate_id", "flag"]],
            on="estimate_id",
            how="left",
        )

        fig = px.line(
            chart_data,
            x="fy", y="variance_pct",
            color="flag", markers=True,
            facet_col="category", facet_col_wrap=3,
            color_discrete_map={
                "red": "#dc2626",
                "amber": "#f59e0b",
                "green": "#10b981",
                "below_materiality": "#6b7280",
            },
            labels={"fy": "Fiscal year", "variance_pct": "Variance (%)"},
            height=max(360, 220 * ((len(filtered_summary) + 2) // 3)),
        )

        fig.update_layout(
            plot_bgcolor="#0a1420",
            paper_bgcolor="#05080d",
            font_color="#eef2f7",
        )
        fig.add_hline(y=0, line_dash="dash", line_color="#5c7characters")
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        fig.update_xaxes(dtick=1, gridcolor="#13243a")
        fig.update_yaxes(matches=None, gridcolor="#13243a")
        fig.update_layout(showlegend=True, legend_title_text="Flag")

        st.plotly_chart(fig, use_container_width=True)




with tab_multi:
    st.markdown('<div class="section-header">Portfolio-Level Oversight</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Aggregates bias detection across every loaded company. '
        'Supports audit managers running multiple engagements in parallel.</div>',
        unsafe_allow_html=True,
    )

    if len(companies) < 2:
        st.info(
            "Only one company is currently loaded. The portfolio view activates when "
            "two or more companies are uploaded."
        )
    else:
        portfolio_rows = []
        for company_name, (det_df, sum_df) in companies.items():
            total_est = len(sum_df)
            red = int((sum_df["flag"] == "red").sum())
            amber = int((sum_df["flag"] == "amber").sum())
            green = int((sum_df["flag"] == "green").sum())
            below = int((sum_df["flag"] == "below_materiality").sum())
            red_rate = (red / total_est) if total_est > 0 else 0
            risk_score = (red * 1.0 + amber * 0.4) / total_est if total_est > 0 else 0

            portfolio_rows.append({
                "Company": company_name,
                "Estimates": total_est,
                "Red": red,
                "Amber": amber,
                "Green": green,
                "Below materiality": below,
                "Red flag rate": red_rate,
                "Risk score": risk_score,
            })

        portfolio_df = pd.DataFrame(portfolio_rows).sort_values("Risk score", ascending=False)

        st.markdown('<div class="section-header">Portfolio Summary</div>', unsafe_allow_html=True)
        total_companies_n = len(portfolio_df)
        total_estimates = int(portfolio_df["Estimates"].sum())
        total_red = int(portfolio_df["Red"].sum())
        total_amber = int(portfolio_df["Amber"].sum())
        companies_with_red = int((portfolio_df["Red"] > 0).sum())

        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.metric("Companies loaded", total_companies_n)
        with m2:
            st.metric("Total estimates", total_estimates)
        with m3:
            st.metric("Total red flags", total_red)
        with m4:
            st.metric("Total amber flags", total_amber)
        with m5:
            st.metric("Companies with red flags", companies_with_red)

        st.markdown('<div class="section-header">Per-Company Comparison</div>', unsafe_allow_html=True)

        display_portfolio = portfolio_df.copy()
        display_portfolio["Red flag rate"] = display_portfolio["Red flag rate"].apply(
            lambda x: f"{x*100:.0f}%"
        )
        display_portfolio["Risk score"] = display_portfolio["Risk score"].apply(
            lambda x: f"{x:.2f}"
        )

        def colour_red_count(val):
            if isinstance(val, (int, float)):
                if val >= 2:
                    return "background-color: #dc2626; color: white; font-weight: bold;"
                elif val == 1:
                    return "background-color: #f59e0b; color: white;"
                else:
                    return "background-color: #10b981; color: white;"
            return ""

        styled_portfolio = display_portfolio.style.map(colour_red_count, subset=["Red"])
        st.dataframe(styled_portfolio, use_container_width=True, hide_index=True)

        st.markdown('<div class="section-header">Risk Ranking</div>', unsafe_allow_html=True)
        st.caption("Risk score = (red flags × 1.0 + amber flags × 0.4) / total estimates.")

        rank_fig = px.bar(
            portfolio_df,
            x="Risk score", y="Company",
            orientation="h",
            color="Risk score",
            color_continuous_scale=[[0, "#10b981"], [0.5, "#f59e0b"], [1, "#dc2626"]],
            labels={"Risk score": "Risk score (weighted)", "Company": ""},
        )
        rank_fig.update_layout(
            plot_bgcolor="#0a1420",
            paper_bgcolor="#05080d",
            font_color="#eef2f7",
            height=max(300, 60 * len(portfolio_df)),
            coloraxis_showscale=False,
        )
        rank_fig.update_xaxes(gridcolor="#13243a")
        rank_fig.update_yaxes(categoryorder="total ascending", gridcolor="#13243a")
        st.plotly_chart(rank_fig, use_container_width=True)

        st.markdown('<div class="section-header">Categories With Bias Across Portfolio</div>', unsafe_allow_html=True)
        st.caption("Estimate categories appearing flagged across multiple companies may indicate sector-wide issues.")

        category_rows = []
        for company_name, (_, sum_df) in companies.items():
            for _, row in sum_df.iterrows():
                category_rows.append({
                    "company": company_name,
                    "category": row["category"],
                    "flag": row["flag"],
                })

        if category_rows:
            cat_df = pd.DataFrame(category_rows)
            cat_summary = cat_df.groupby("category").agg(
                companies_affected=("company", "nunique"),
                total_estimates=("category", "count"),
                red_count=("flag", lambda s: (s == "red").sum()),
                amber_count=("flag", lambda s: (s == "amber").sum()),
            ).reset_index()

            cat_summary["flag_rate"] = (
                (cat_summary["red_count"] + cat_summary["amber_count"])
                / cat_summary["total_estimates"]
            )

            cat_summary = cat_summary.sort_values(["red_count", "flag_rate"], ascending=False)

            cat_display = cat_summary.copy()
            cat_display["flag_rate"] = cat_display["flag_rate"].apply(lambda x: f"{x*100:.0f}%")
            cat_display.columns = [
                "Category", "Companies affected", "Total estimates",
                "Red count", "Amber count", "Flag rate",
            ]
            st.dataframe(cat_display, use_container_width=True, hide_index=True)


with tab_detail:
    st.markdown('<div class="section-header">Estimate Detail & Audit Procedure</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-subtitle">Drill into a single estimate to see its full history, '
        'statistical significance, and the suggested next audit procedure.</div>',
        unsafe_allow_html=True,
    )

    if len(filtered_summary) == 0:
        st.info("No estimates match the current filters.")
    else:
        filtered_summary_display = filtered_summary.copy()
        filtered_summary_display["label"] = (
            filtered_summary_display["estimate_id"] + " — " + filtered_summary_display["category"]
        )

        selected_label = st.selectbox(
            "Select an estimate to inspect",
            options=filtered_summary_display["label"].tolist(),
        )

        selected_id = selected_label.split(" — ")[0]

        estimate_summary = filtered_summary[
            filtered_summary["estimate_id"] == selected_id
        ].iloc[0]
        estimate_history = filtered_detailed[
            filtered_detailed["estimate_id"] == selected_id
        ].copy().sort_values("fy")

        flag = estimate_summary["flag"]
        flag_colors_map = {
            "red": "#dc2626",
            "amber": "#f59e0b",
            "green": "#10b981",
            "below_materiality": "#6b7280",
        }
        flag_color = flag_colors_map.get(flag, "#999999")

        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, {flag_color}99, {flag_color});
                        padding: 18px 22px; border-radius: 8px;
                        color: white; font-weight: bold; font-size: 16px;
                        margin-bottom: 12px; letter-spacing: 1px;
                        box-shadow: 0 4px 12px rgba(0,0,0,0.3);">
                ◆ {flag.upper().replace('_', ' ')} — {estimate_summary['pattern_label']}
            </div>
            """,
            unsafe_allow_html=True,
        )

        p_val = estimate_summary["p_value"]
        p_text = estimate_summary["p_interpretation"]

        if p_val < 0.05:
            p_box_color = "#2a0810"
            p_border = "#c9962e"
        elif p_val < 0.10:
            p_box_color = "#1f0a10"
            p_border = "#5b3e0f"
        else:
            p_box_color = "#0a1420"
            p_border = "#6b7280"

        st.markdown(
            f"""
            <div style="background-color: {p_box_color}; border-left: 4px solid {p_border};
                        padding: 12px 16px; border-radius: 4px; margin-bottom: 14px;
                        font-size: 14px; color: #eef2f7;">
                <b>Statistical significance:</b> p-value = {p_val:.4f}<br>
                <i style="color: #c9a6ad;">{p_text}</i>
            </div>
            """,
            unsafe_allow_html=True,
        )

        try:
            pdf_bytes = generate_working_paper_pdf(
                company_name=selected_company,
                estimate_summary=estimate_summary,
                estimate_history=estimate_history,
                materiality=materiality,
            )
            safe_company = selected_company.replace(" ", "_").lower()
            safe_estimate = selected_id.lower()
            st.download_button(
                label="Download working paper (PDF)",
                data=pdf_bytes,
                file_name=f"oversight_{safe_company}_{safe_estimate}.pdf",
                mime="application/pdf",
            )
        except Exception as e:
            st.error(f"PDF generation failed: {e}")

        st.markdown("")

        col_left, col_right = st.columns([1.1, 1])

        with col_left:
            st.markdown("**Year-by-year history**")
            history_display = estimate_history[[
                "fy", "mgmt_value", "actual_value", "variance",
                "variance_pct", "direction",
            ]].copy()
            history_display.columns = [
                "Fiscal year", "Management estimate", "Actual outcome",
                "Variance", "Variance %", "Direction",
            ]
            history_display["Variance %"] = history_display["Variance %"].round(2)
            for col in ["Management estimate", "Actual outcome", "Variance"]:
                history_display[col] = history_display[col].apply(lambda x: f"{x:,.0f}")
            st.dataframe(history_display, use_container_width=True, hide_index=True)

            st.markdown("**Variance trend**")
            detail_fig = px.line(
                estimate_history,
                x="fy", y="variance_pct",
                markers=True,
                labels={"fy": "Fiscal year", "variance_pct": "Variance (%)"},
            )
            detail_fig.add_hline(y=0, line_dash="dash", line_color="#5c7characters")
            detail_fig.update_traces(line=dict(color=flag_color, width=3))
            detail_fig.update_xaxes(dtick=1, gridcolor="#13243a")
            detail_fig.update_yaxes(gridcolor="#13243a")
            detail_fig.update_layout(
                plot_bgcolor="#0a1420",
                paper_bgcolor="#05080d",
                font_color="#eef2f7",
                height=300,
                margin=dict(t=20, b=20),
            )
            st.plotly_chart(detail_fig, use_container_width=True)

        with col_right:
            st.markdown("**Suggested next audit procedure**")
            st.caption("Working-paper bridge based on ISA 540 (Revised)")

            if flag == "red":
                if estimate_summary["dominant_direction"] == "under":
                    st.error(
                        "**Investigate possible income smoothing risk.**\n\n"
                        "Management has under-estimated this allowance every year, "
                        "which may indicate systematic under-reserving.\n\n"
                        "**ISA 540 (Revised) paragraph 32** requires the auditor "
                        "to evaluate indicators of management bias.\n\n"
                        "**Suggested procedures:**\n"
                        "1. Interview management on the methodology and assumption-setting process.\n"
                        "2. Recompute the estimate with an independent benchmark.\n"
                        "3. Discuss with those charged with governance.\n"
                        "4. Document the bias indicator and the auditor's evaluation."
                    )
                elif estimate_summary["dominant_direction"] == "over":
                    st.error(
                        "**Investigate possible cookie-jar reserve risk.**\n\n"
                        "Management has over-estimated this allowance every year, "
                        "which may indicate systematic over-reserving for later release.\n\n"
                        "**ISA 540 (Revised) paragraph 32** requires the auditor "
                        "to evaluate indicators of management bias.\n\n"
                        "**Suggested procedures:**\n"
                        "1. Interview management on why estimates are consistently above outcomes.\n"
                        "2. Examine subsequent-period releases of the allowance.\n"
                        "3. Discuss with those charged with governance.\n"
                        "4. Document the bias indicator and the auditor's evaluation."
                    )
            elif flag == "amber":
                st.warning(
                    "**Document and continue monitoring.**\n\n"
                    "A partial directional pattern was detected. This may reflect "
                    "estimation noise rather than bias, but ISA 540 (Revised) "
                    "requires the auditor to remain alert.\n\n"
                    "**Suggested procedures:**\n"
                    "1. Document the observation in the working papers.\n"
                    "2. Discuss with management as part of the regular estimate review.\n"
                    "3. Re-evaluate next year to see if the pattern strengthens or dissolves."
                )
            elif flag == "below_materiality":
                st.info(
                    "**Below materiality threshold.**\n\n"
                    "The maximum absolute variance on this estimate does not exceed "
                    "the materiality threshold set in the sidebar. No further "
                    "investigation is required at this materiality level.\n\n"
                    "**Suggested procedures:**\n"
                    "1. Document the conclusion that the estimate is below materiality.\n"
                    "2. Re-evaluate if materiality is revised downward in future periods."
                )
            else:
                st.success(
                    "**No bias pattern detected.**\n\n"
                    "Variances are within reasonable bounds and do not consistently "
                    "favour one direction.\n\n"
                    "Standard ISA 540 procedures apply: test the method, the assumptions, "
                    "and the data underlying the current-year estimate."
                )


with tab_methodology:
    st.markdown('<div class="section-header">How OVERSIGHT Detects Bias</div>', unsafe_allow_html=True)

    st.markdown(
        """
        ### Inputs

        Each row in the input CSV represents one estimate in one fiscal year:

        | Column | Description |
        |---|---|
        | `estimate_id` | Unique identifier for the estimate |
        | `category` | Type of estimate |
        | `fy` | Fiscal year |
        | `mgmt_value` | Management's estimate at year-end |
        | `actual_value` | Actual outcome observed in the subsequent period |

        Each CSV file is treated as **one company**, identified by its filename.

        ### Per-year computation

        - **variance** = `mgmt_value − actual_value`
        - **variance_pct** = variance as a percentage of the actual outcome
        - **direction** = `under`, `over`, or `on target`

        ### Statistical significance

        For each estimate, OVERSIGHT runs a **one-sided binomial test** under the
        null hypothesis that management's estimates are unbiased.

        - p < 0.05 → strong statistical evidence of directional bias
        - p < 0.10 → moderate statistical evidence
        - p < 0.20 → weak statistical evidence
        - p ≥ 0.20 → pattern consistent with random estimation noise

        ### Materiality filter

        Estimates whose maximum absolute variance does not exceed the threshold are
        labelled **below_materiality** regardless of directional consistency. Reflects ISA 320.

        ### Flag rules

        | Flag | Condition | Interpretation |
        |---|---|---|
        | Below materiality | Max abs variance < materiality threshold | Documented and dismissed |
        | Red | All years same direction (4 of 4 or 5 of 5), material | Consistent bias indicator |
        | Amber | 3 of 4 same direction, or mixed with avg variance > 15%, material | Partial pattern, document |
        | Green | Otherwise (material but no pattern) | No bias pattern detected |

       

        ### Portfolio-level view

        When two or more companies are uploaded, the Portfolio tab aggregates
        results. Each company gets a weighted risk score: (red × 1.0 + amber × 0.4) / total.

        ### PDF working paper export

        From the Detail tab, the auditor can download a one-page PDF formatted as an
        audit working paper for each flagged estimate.

        ### Standards reference

        - **ISA 540 paragraph 9** — retrospective review
        - **ISA 540 paragraph 32** — evaluation of indicators of management bias
        - **ISA 540 paragraph 39** — documentation of significant judgements and bias indicators
        - **ISA 320** — materiality

        ### Limits

        OVERSIGHT flags patterns worth investigating. It does not prove management bias
        or fraud. Any flagged estimate must be evaluated by the auditor using
        professional judgement.
        """
    )


st.markdown("""
<div class="oversight-footer">
    <span class="oversight-footer-brand">OVERSIGHT</span> &nbsp;·&nbsp;
    Tunis Business School &nbsp;·&nbsp; Bachelor's Thesis &nbsp;·&nbsp; 2026
</div>
""", unsafe_allow_html=True)

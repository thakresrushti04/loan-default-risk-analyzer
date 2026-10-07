# app.py - Loan Officer Risk Desk (Electric Cyan Theme)
from pathlib import Path

import joblib
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

BASE_DIR = Path(__file__).parent
st.set_page_config(page_title="Loan Risk Desk", page_icon="🏦", layout="wide")

# ---------- Electric Cyan Theme Palette ----------
T = {
    "BG": "#0B0F19",         # Deep Dark Charcoal
    "CARD": "#161E2E",       # Card Surface
    "BORDER": "#27354A",     # Surface Border
    "HERO2": "#1E2A3E",      # Gradient Secondary Accent
    "ACCENT": "#06B6D4",     # Electric Cyan
    "MUTED": "#94A3B8",      # Muted Slate
    "TICK": "#A5F3FC",       # Soft Light Cyan
    "TEXT": "#F8FAFC",       # Primary White
    "HEAT": [[0, "#1E2A3E"], [0.5, "#0891B2"], [1, "#06B6D4"]],
}

A, B = T["ACCENT"], T["BG"]

# Risk status colors
LOW, MED, HIGH = "#10B981", "#F59E0B", "#EF4444"

LOGO = (
    f'<svg width="46" height="46" viewBox="0 0 46 46"><rect width="46" height="46" rx="11" fill="{A}"/>'
    f'<path d="M23 9 L37 17 H9 Z" fill="{B}"/>'
    f'<rect x="13" y="19" width="4" height="12" fill="{B}"/>'
    f'<rect x="21" y="19" width="4" height="12" fill="{B}"/>'
    f'<rect x="29" y="19" width="4" height="12" fill="{B}"/>'
    f'<rect x="9" y="33" width="28" height="3" fill="{B}"/></svg>'
)

# Portfolio facts for scrolling ticker
TICKER = [
    "<b>Portfolio default rate</b> 21.9%",
    "<b>Renters</b> default at 31.6% vs 12.6% for mortgage holders and 7.5% for owners",
    "<b>Loans over 30% of income</b> default at 57-80% in most income bands",
    "<b>Model at 0.35 threshold</b> catches 77% of defaults",
    "<b>False alarms</b> 18.5% of good borrowers flagged",
    "<b>Lender grade D</b> loans default at 59% (grade is not used by this model)",
    "<b>Training data</b> 32,409 cleaned loans",
]
ticker_html = "".join(f"<span>{t}</span>" for t in TICKER) * 2

# Plain-English names for features
NICE = {
    "loan_percent_income": "Loan size vs income",
    "person_income": "Annual income",
    "loan_amnt": "Loan amount",
    "person_home_ownership_RENT": "Renting a home",
    "person_home_ownership_OWN": "Owning a home",
    "cb_person_default_on_file_Y": "Past default on file",
    "person_emp_length": "Years employed",
    "person_age": "Age",
    "cb_person_cred_hist_length": "Credit history length",
    "loan_intent_VENTURE": "Purpose: venture",
    "loan_intent_HOMEIMPROVEMENT": "Purpose: home improvement",
    "loan_intent_EDUCATION": "Purpose: education",
    "loan_intent_MEDICAL": "Purpose: medical",
    "loan_intent_PERSONAL": "Purpose: personal",
}

# ---------- CSS Overrides ----------
CSS = f"""
<style>
/* App & Sidebar Background */
.stApp, div[data-testid="stSidebar"], section[data-testid="stSidebar"] > div {{
    background-color: {T["BG"]} !important;
    color: {T["TEXT"]} !important;
}}

.block-container {{
    padding: 3rem 2rem 1rem 2rem;
    max-width: 100%;
}}

/* Hero Banner */
.hero {{
    display:flex; align-items:center; gap:16px; padding:18px 24px; margin-bottom:12px;
    border-radius:16px; border:1px solid {T["BORDER"]};
    background:linear-gradient(135deg, {T["CARD"]} 0%, {T["HERO2"]} 100%);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}}
.hero-text {{flex:1;}}
.hero-title {{font-size:28px; font-weight:800; letter-spacing: -0.02em; color:{T["TEXT"]};}}
.hero-sub {{color: #94A3B8 !important; font-size:13.5px;}}
.status {{margin-left:auto; color:{T["TICK"]}; font-size:13px; white-space:nowrap; display:flex; align-items:center;}}
.dot {{
    display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:8px;
    animation:pulse 1.8s infinite;
}}
@keyframes pulse {{
    0% {{box-shadow:0 0 0 0 rgba(6, 182, 212, 0.7);}}
    70% {{box-shadow:0 0 0 10px rgba(6, 182, 212, 0);}}
    100% {{box-shadow:0 0 0 0 rgba(6, 182, 212, 0);}}
}}

/* Ticker Styling */
.ticker {{
    overflow:hidden; white-space:nowrap; border:1px solid {T["BORDER"]}; border-radius:12px;
    background:{T["CARD"]}; padding:10px 0; margin-bottom:16px;
}}
.ticker-inner {{display:inline-block; animation:scroll 65s linear infinite;}}
.ticker-inner span {{margin-right:56px; color:{T["TICK"]}; font-size:13px;}}
.ticker-inner b {{color:{T["ACCENT"]};}}
@keyframes scroll {{0% {{transform:translateX(0);}} 100% {{transform:translateX(-50%);}}}}

/* Cards */
.card {{
    background: {T["CARD"]};
    border: 1px solid {T["BORDER"]};
    border-top: 3px solid {T["ACCENT"]};
    border-radius: 14px;
    padding: 16px 18px;
    height: 100%;
    transition: all 0.3s ease;
    box-shadow: 0 4px 16px rgba(0,0,0,0.2);
}}
.card:hover {{
    transform: translateY(-2px);
    border-color: {T["ACCENT"]};
    box-shadow: 0 8px 24px rgba(0,0,0,0.4), 0 0 12px {T["ACCENT"]}44;
}}

.kpi-label {{color:{T["MUTED"]}; font-size:11px; text-transform:uppercase; letter-spacing:0.1em; font-weight:600;}}
.kpi-value {{font-size:28px; font-weight:800; line-height:1.2; margin: 4px 0;}}
.kpi-sub {{color:{T["MUTED"]}; font-size:12px;}}
.check {{padding:8px 0; border-bottom:1px solid {T["BORDER"]}; font-size:13px;}}
.check small {{color:{T["MUTED"]};}}
.prof td {{padding:4px 16px 4px 0; font-size:13px; color:{T["TEXT"]};}}
.prof td:first-child {{color:{T["MUTED"]};}}
.note {{color:{T["MUTED"]}; font-size:12px; margin-top:6px;}}

/* Form Controls Override */
div[data-baseweb="input"] > div, div[data-baseweb="select"] > div {{
    background-color: {T["CARD"]} !important;
    border-color: {T["BORDER"]} !important;
    color: {T["TEXT"]} !important;
}}
input, select {{
    color: {T["TEXT"]} !important;
}}

/* Sidebar Buttons */
div[data-testid="stSidebar"] button {{
    border-radius: 20px !important;
    border: 1px solid {T["BORDER"]} !important;
    background: {T["CARD"]} !important;
    color: {T["TEXT"]} !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}}
div[data-testid="stSidebar"] button:hover {{
    border-color: {T["ACCENT"]} !important;
    color: {T["ACCENT"]} !important;
    transform: scale(1.03);
}}

/* Streamlit Tabs Override */
button[data-baseweb="tab"] {{
    color: #94A3B8 !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    background-color: transparent !important;
}}
button[aria-selected="true"] {{
    color: {T["ACCENT"]} !important;
    border-bottom: 2px solid {T["ACCENT"]} !important;
    font-weight: 700 !important;
}}

/* Slider Track Color */
div[data-baseweb="slider"] div {{
    background-color: {T["ACCENT"]} !important;
}}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_resource
def load_artifacts():
    model = joblib.load(BASE_DIR / "risk_model.joblib")
    meta = joblib.load(BASE_DIR / "model_meta.joblib")
    return model, meta


def card(label, value, sub="", color=None):
    color = color or T["TEXT"]
    return (
        f'<div class="card"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-value" style="color:{color}">{value}</div>'
        f'<div class="kpi-sub">{sub}</div></div>'
    )


def dark(fig, title, height=380):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color=T["TEXT"], family="sans-serif"),
        title=dict(text=f"<b>{title}</b>", font=dict(size=15, color=T["TEXT"])),
        height=height,
        margin=dict(t=50, b=35, l=40, r=20),
    )
    fig.update_xaxes(gridcolor=T["BORDER"], zerolinecolor=T["BORDER"])
    fig.update_yaxes(gridcolor=T["BORDER"], zerolinecolor=T["BORDER"])
    return fig


model, meta = load_artifacts()
cols = meta["columns"]


def build_row(age, income, home, emp_length, loan_amnt, intent, cred_hist, prior_default):
    values = dict.fromkeys(cols, 0)
    values.update(
        {
            "person_age": age,
            "person_income": income,
            "person_emp_length": emp_length,
            "loan_amnt": loan_amnt,
            "loan_percent_income": round(loan_amnt / income, 2),
            "cb_person_cred_hist_length": cred_hist,
        }
    )
    for name in [f"person_home_ownership_{home}", f"loan_intent_{intent}"]:
        if name in cols:
            values[name] = 1
    if prior_default == "Yes":
        values["cb_person_default_on_file_Y"] = 1
    return values


# ---------- State Initialization ----------
DEFAULTS = dict(
    age=30,
    income=55000,
    home=meta["home_options"][0],
    emp=float(meta["median_emp_length"]),
    loan=8000,
    intent=meta["intent_options"][0],
    cred=int(meta["median_cred_hist"]),
    prior="No",
    thr=float(meta["threshold"]),
)
for k, v in DEFAULTS.items():
    st.session_state.setdefault(k, v)

PRESETS = {
    "Safe": dict(
        age=38,
        income=95000,
        home="MORTGAGE",
        emp=10.0,
        loan=6000,
        intent="EDUCATION",
        cred=12,
        prior="No",
    ),
    "Borderline": dict(
        age=27,
        income=40000,
        home="RENT",
        emp=3.0,
        loan=12000,
        intent="MEDICAL",
        cred=4,
        prior="No",
    ),
    "Risky": dict(
        age=23,
        income=20000,
        home="RENT",
        emp=1.0,
        loan=12000,
        intent="DEBTCONSOLIDATION",
        cred=2,
        prior="Yes",
    ),
}


def apply_preset(name):
    for key, value in PRESETS[name].items():
        st.session_state[key] = value


# ---------- Sidebar ----------
with st.sidebar:
    st.header("Applicant")
    st.caption("Try a sample applicant:")
    b1, b2, b3 = st.columns(3)
    b1.button("Safe", on_click=apply_preset, args=("Safe",))
    b2.button("Med", on_click=apply_preset, args=("Borderline",))
    b3.button("Risky", on_click=apply_preset, args=("Risky",))

    age = st.number_input("Age", min_value=20, max_value=94, step=1, key="age")
    income = st.number_input(
        "Annual income", min_value=4000, max_value=2000000, step=1000, key="income"
    )
    home = st.selectbox("Home ownership", meta["home_options"], key="home")

    max_emp = float(min(41, max(0, age - 16)))
    st.session_state["emp"] = min(float(st.session_state["emp"]), max_emp)
    emp_length = st.number_input(
        "Employment length (years)",
        min_value=0.0,
        max_value=max_emp,
        step=1.0,
        key="emp",
    )
    loan_amnt = st.number_input(
        "Loan amount (max 35,000)",
        min_value=500,
        max_value=35000,
        step=500,
        key="loan",
    )
    intent = st.selectbox("Loan purpose", meta["intent_options"], key="intent")
    max_cred = int(max(2, min(30, age - 18)))
    st.session_state["cred"] = int(min(max(st.session_state["cred"], 2), max_cred))
    cred_hist = st.number_input(
        "Credit history length (years)",
        min_value=2,
        max_value=max_cred,
        step=1,
        key="cred",
    )
    prior_default = st.radio(
        "Prior default on file?", ["No", "Yes"], horizontal=True, key="prior"
    )

    st.header("Decision settings")
    threshold = st.slider(
        "Flag as risky at or above",
        min_value=0.10,
        max_value=0.70,
        step=0.05,
        key="thr",
    )
    st.caption(
        "Lower = catches more defaults but flags more good borrowers. "
        "At 0.35: catches 77%, false alarms 18.5%."
    )

# ---------- Prediction Engine ----------
loan_pct = round(loan_amnt / income, 2)
row = pd.DataFrame(
    [
        build_row(
            age,
            income,
            home,
            emp_length,
            loan_amnt,
            intent,
            cred_hist,
            prior_default,
        )
    ]
)[cols]
prob = float(model.predict_proba(row)[0, 1])
flagged = prob >= threshold

if prob < 0.20:
    band, color = "Low risk", LOW
elif prob < 0.50:
    band, color = "Medium risk", MED
else:
    band, color = "High risk", HIGH
decision_color = HIGH if flagged else LOW

# ---------- Header and Ticker ----------
st.markdown(
    f'<div class="hero">{LOGO}<div class="hero-text">'
    '<div class="hero-title">Loan Officer Risk Desk</div>'
    '<div class="hero-sub">Enter an applicant on the left → the model estimates the chance '
    "they default → the bank flags them if that chance is above its threshold.</div></div>"
    f'<div class="status"><span class="dot" style="background:{A}"></span>'
    "Scoring engine active</div></div>",
    unsafe_allow_html=True,
)
st.markdown(
    f'<div class="ticker"><div class="ticker-inner">{ticker_html}</div></div>',
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4 = st.tabs(
    ["Dashboard", "What-if", "Portfolio insights", "Model performance"]
)

# ---------- Tab 1: Dashboard ----------
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(
        card("Default probability", f"{prob:.1%}", "Model estimate", color),
        unsafe_allow_html=True,
    )
    c2.markdown(
        card("Risk status", band, "Under 20% / 20-50% / over 50%", color),
        unsafe_allow_html=True,
    )
    c3.markdown(
        card("Loan as % of income", f"{loan_pct:.0%}", "Training data maximum: 83%"),
        unsafe_allow_html=True,
    )
    c4.markdown(
        card(
            "Decision",
            f'<span class="dot" style="background:{decision_color}"></span>'
            f'{"Flag" if flagged else "Pass"}',
            f"Flag if probability is {threshold:.0%} or more",
            decision_color,
        ),
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="note">Risk status is a simple label for the probability. '
        "The Flag / Pass decision uses the threshold set in the sidebar.</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    g, k, p = st.columns([1.1, 1, 0.9])

    with g:
        gauge = go.Figure(
            go.Indicator(
                mode="gauge+number",
                value=prob * 100,
                number={"suffix": "%", "font": {"color": color}},
                gauge={
                    "axis": {"range": [0, 100]},
                    "bar": {"color": color},
                    "steps": [
                        {"range": [0, 20], "color": "#064e3b"},
                        {"range": [20, 50], "color": "#78350f"},
                        {"range": [50, 100], "color": "#7f1d1d"},
                    ],
                    "threshold": {
                        "line": {"color": "white", "width": 4},
                        "thickness": 0.8,
                        "value": threshold * 100,
                    },
                },
            )
        )
        st.plotly_chart(
            dark(gauge, "Risk gauge (white line = threshold)", 300),
            width="stretch",
        )

    with k:
        checks = [
            (
                loan_pct <= 0.30,
                "Loan size vs income",
                f"Loan is {loan_pct:.0%} of income. Defaults jump past 30%.",
            ),
            (
                income >= 38500,
                "Income level",
                f"Income is {income:,}. The bottom quarter earns under 38,500.",
            ),
            (
                home != "RENT",
                "Home ownership",
                f"{home}. Renters defaulted at 31.6% vs 12.6% for mortgage.",
            ),
            (
                prior_default == "No",
                "Prior default",
                "None on file."
                if prior_default == "No"
                else "A past default is on file.",
            ),
        ]
        html = '<div class="card"><div class="kpi-label">Risk checklist</div>'
        for ok, title, detail in checks:
            html += (
                f'<div class="check">{"✅" if ok else "⚠"} <b>{title}</b><br>'
                f"<small>{detail}</small></div>"
            )
        html += "</div>"
        st.markdown(html, unsafe_allow_html=True)

    with p:
        st.markdown(
            '<div class="card"><div class="kpi-label">Applicant profile</div><table class="prof">'
            f"<tr><td>Age</td><td>{age}</td></tr>"
            f"<tr><td>Income</td><td>{income:,}</td></tr>"
            f"<tr><td>Home</td><td>{home}</td></tr>"
            f"<tr><td>Employment</td><td>{emp_length:.0f} yrs</td></tr>"
            f"<tr><td>Loan</td><td>{loan_amnt:,}</td></tr>"
            f"<tr><td>Purpose</td><td>{intent}</td></tr>"
            f"<tr><td>Credit history</td><td>{cred_hist} yrs</td></tr>"
            f"<tr><td>Prior default</td><td>{prior_default}</td></tr></table></div>",
            unsafe_allow_html=True,
        )

    st.write("")
    if flagged:
        st.error(
            f"Flag for review: {prob:.1%} is at or above the {threshold:.2f} threshold."
        )
    else:
        st.success(f"Below threshold: {prob:.1%} is under the {threshold:.2f} cutoff.")
    if loan_pct > 0.83:
        st.warning(
            f"Loan is {loan_pct:.0%} of income, above the 83% maximum in the "
            "training data. Treat this as 'very high risk', not a precise number."
        )
    if income < 15000:
        st.warning(
            "Income is far below the typical borrower (median 55,000). The model has "
            "few similar loans to learn from, so treat this estimate as rough."
        )

    report = pd.DataFrame(
        [
            {
                "age": age,
                "annual_income": income,
                "home_ownership": home,
                "employment_years": emp_length,
                "loan_amount": loan_amnt,
                "loan_purpose": intent,
                "credit_history_years": cred_hist,
                "prior_default": prior_default,
                "loan_percent_income": loan_pct,
                "default_probability_pct": round(prob * 100, 1),
                "risk_band": band,
                "threshold": threshold,
                "decision": "Flag" if flagged else "Pass",
            }
        ]
    )
    st.download_button(
        "Download this assessment (CSV)",
        report.to_csv(index=False).encode("utf-8"),
        file_name="loan_risk_assessment.csv",
        mime="text/csv",
    )

# ---------- Tab 2: What-if ----------
with tab2:
    st.subheader("What if the loan amount changes?")
    st.caption("Same applicant, everything else fixed. Only the loan amount moves.")

    loans = list(range(500, 35001, 500))
    sweep = pd.DataFrame(
        [
            build_row(
                age,
                income,
                home,
                emp_length,
                amt,
                intent,
                cred_hist,
                prior_default,
            )
            for amt in loans
        ]
    )[cols]
    curve = model.predict_proba(sweep)[:, 1] * 100

    # First loan size where the estimate reaches the threshold
    over = [amt for amt, p in zip(loans, curve) if p >= threshold * 100]
    if over:
        crossing = (
            f"The estimate first reaches the {threshold:.0%} threshold at a loan of "
            f"{over[0]:,}. The curve is uneven, so it can dip back under and cross again."
        )
    else:
        crossing = (
            f"The estimate stays under the {threshold:.0%} threshold "
            "for every loan size up to 35,000."
        )

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=loans,
            y=curve,
            mode="lines",
            name="Default probability",
            line=dict(color=A, width=3.5),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[loan_amnt],
            y=[prob * 100],
            mode="markers",
            name="Current loan",
            marker=dict(color="#ffffff", size=13, symbol="circle"),
        )
    )
    fig.add_hline(
        y=threshold * 100,
        line=dict(color=T["MUTED"], dash="dash"),
        annotation_text=f"Decision threshold ({threshold:.0%})",
        annotation_position="top left",
    )
    fig.update_xaxes(title="Loan amount")
    fig.update_yaxes(title="Default probability (%)", range=[0, 100])

    st.plotly_chart(
        dark(fig, "Sensitivity Curve: Default Probability vs. Requested Loan Amount", 520),
        width="stretch",
    )

    st.markdown(
        f'<div class="card">'
        f'<div class="kpi-label">What-If Insights</div>'
        f'<p style="margin-top:8px; font-size:14px; color:{T["TEXT"]};">'
        f'• <b>Current request:</b> a loan of {loan_amnt:,} is <b>{loan_pct:.0%}</b> of income, '
        f'with an estimated default probability of <b>{prob:.1%}</b>.<br>'
        f'• <b>Threshold crossing:</b> {crossing}<br>'
        f'• <b>Range:</b> across loans from 500 to 35,000, the estimate runs from '
        f'<b>{min(curve):.0f}%</b> to <b>{max(curve):.0f}%</b>.<br>'
        f'• <b>Caution:</b> a rough sensitivity check from a Random Forest, '
        f'not a recommended loan limit.'
        f'</p></div>',
        unsafe_allow_html=True,
    )

# ---------- Tab 3: Portfolio Insights ----------
with tab3:
    st.subheader("What the training data showed")
    st.caption("Findings from exploratory analysis of about 32,500 loans.")

    a, b = st.columns(2)

    homes = ["OWN", "MORTGAGE", "OTHER", "RENT"]
    rates = [7.47, 12.57, 30.84, 31.57]
    fig3 = go.Figure(
        go.Bar(
            x=homes,
            y=rates,
            text=[f"{r}%" for r in rates],
            textposition="outside",
            marker=dict(
                color=rates,
                colorscale=[[0, "#1E2A3E"], [0.5, "#0891B2"], [1, "#06B6D4"]],
            ),
        )
    )
    fig3.update_yaxes(title="Default rate (%)", range=[0, 42])
    a.plotly_chart(dark(fig3, "Default rate by home ownership", 520), width="stretch")

    z = [
        [26.2, 30.5, 35.9, 79.5],
        [14.8, 15.1, 15.1, 67.3],
        [12.6, 12.1, 16.6, 64.0],
        [9.2, 11.2, 17.4, 57.3],
        [6.9, 9.1, 19.1, 39.7],
    ]
    fig4 = go.Figure(
        go.Heatmap(
            z=z,
            x=["0-10%", "10-20%", "20-30%", "30%+"],
            y=["Lowest 20%", "Lower-mid", "Middle", "Upper-mid", "Highest 20%"],
            text=[[f"{v}%" for v in r] for r in z],
            texttemplate="%{text}",
            textfont=dict(color="#ffffff", size=13),
            colorscale=T["HEAT"],
            showscale=False,
        )
    )
    fig4.update_xaxes(title="Loan as % of income")
    b.plotly_chart(
        dark(fig4, "Default rate: income band vs loan size", 520), width="stretch"
    )

    st.markdown(
        f'<div class="card">'
        f'<div class="kpi-label">Key Portfolio Takeaways</div>'
        f'<p style="margin-top:8px; font-size:14px; color:{T["TEXT"]};">'
        f'1. <b>Home Ownership Impact:</b> Renters (31.6%) default at more than 2.5x the rate of homeowners with mortgages (12.6%) and 4x the rate of outright home owners (7.5%).<br>'
        f'2. <b>The 30% Loan-to-Income Cliff:</b> In four of the five income bands, loans above 30% of income default at 57-80%. The top income band is the exception (39.7%), but it has only 58 loans, so treat that figure as unreliable.'
        f'</p></div>',
        unsafe_allow_html=True,
    )

# ---------- Tab 4: Model Performance ----------
with tab4:
    st.subheader("How well does the model work?")
    st.caption("Tested on 6,482 loans the model never saw. Decision threshold 0.35.")
    m1, m2, m3, m4 = st.columns(4)
    m1.markdown(
        card("Defaults caught", "77.0%", "About 77 of every 100 real defaults"),
        unsafe_allow_html=True,
    )
    m2.markdown(
        card("Flags that were right", "53.8%", "About 54 of every 100 flagged loans"),
        unsafe_allow_html=True,
    )
    m3.markdown(
        card("False alarms", "18.5%", "About 18 of every 100 good borrowers"),
        unsafe_allow_html=True,
    )
    m4.markdown(
        card("Ranking score (ROC-AUC)", "0.878", "Borrower data only"),
        unsafe_allow_html=True,
    )
    st.write("")

    imp = (
        pd.Series(model.feature_importances_, index=cols)
        .sort_values()
        .tail(10)
        .rename(index=lambda c: NICE.get(c, c))
    )
    fig5 = go.Figure(
        go.Bar(
            x=imp.values,
            y=imp.index,
            orientation="h",
            marker=dict(
                color=imp.values, colorscale=[[0, T["HEAT"][0][1]], [1, A]]
            ),
        )
    )
    fig5.update_xaxes(title="How much the model relies on it")
    st.plotly_chart(
        dark(fig5, "What drives the prediction (top 10)", 480), width="stretch"
    )

    st.markdown(
        "- Loan grade and interest rate were left out: the lender sets them after judging risk.\n"
        "- Importance shows what the model uses, not what causes default.\n"
        "- Estimates are noisy: a small change in one input can move the probability by several points.\n"
        "- Public Kaggle credit-risk dataset. A portfolio project, not for real lending decisions."
    )
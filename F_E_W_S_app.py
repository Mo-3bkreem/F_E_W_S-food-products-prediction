import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

st.set_page_config(page_title="FINANCIAL FINAL BOSS TERMINAL", layout="wide")

# -----------------------------
# AUTO REFRESH (FIXED)
# -----------------------------
st_autorefresh(interval=2000, key="live_refresh")

# -----------------------------
# UI STYLE
# -----------------------------
st.markdown("""
<style>
[data-testid="stAppViewContainer"] {
    background-color: #05070a;
    color: #cbd5e1;
    font-family: 'Courier New', monospace;
}

.card {
    background: rgba(255,255,255,0.03);
    border: 1px solid #1f2937;
    padding: 12px;
    border-radius: 6px;
}

.stButton>button {
    background: #111827;
    color: #e5e7eb;
    border: 1px solid #374151;
}

h1,h2,h3,p,label { color:#e5e7eb !important; }

</style>
""", unsafe_allow_html=True)

# -----------------------------
# HEADER
# -----------------------------
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.markdown(f"""
<div style='text-align:center; margin-top:10px;'>
<h1 style='color:#e5e7eb; font-size:28px; letter-spacing:2px;'>
ATLAS MARKET INTELLIGENCE TERMINAL
</h1>
<p style='color:#94a3b8;'>LIVE | {now}</p>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# DATA
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("food_prices_final.csv")
    df["date"] = pd.to_datetime(df["date"])
    return df

df = load_data()

# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.title("CONTROL MATRIX")

asset = st.sidebar.selectbox("Asset", df["product"].unique())
run_backtest = st.sidebar.button("Run Backtest")
scenario = st.sidebar.selectbox("Shock Model", ["None", "Demand Shock", "Supply Shock"])

# -----------------------------
# FILTER
# -----------------------------
df_a = df[df["product"] == asset].sort_values("date")
latest = df_a.iloc[-1]
prev = df_a.iloc[-2] if len(df_a) > 1 else df_a.iloc[-1]

# -----------------------------
# LIVE KPIS
# -----------------------------
price_change = ((latest["price"] - prev["price"]) / prev["price"]) * 100

col1, col2, col3, col4 = st.columns(4)
col1.metric("PRICE", f"{latest['price']:.2f}", f"{price_change:.2f}%")
col2.metric("FORECAST", f"{latest['forecast_3days']:.2f}")
col3.metric("RISK", int(latest['risk_score']))
col4.metric("STATE", latest['risk_level'])

# -----------------------------
# CANDLESTICK
# -----------------------------
st.markdown("### MARKET STRUCTURE ")

df_a["open"] = df_a["price"].shift(1)
df_a["close"] = df_a["price"]
df_a["high"] = df_a[["open","close"]].max(axis=1) * 1.01
df_a["low"] = df_a[["open","close"]].min(axis=1) * 0.99

fig = go.Figure(data=[go.Candlestick(
    x=df_a["date"],
    open=df_a["open"],
    high=df_a["high"],
    low=df_a["low"],
    close=df_a["close"]
)])

fig.update_layout(
    paper_bgcolor="#05070a",
    plot_bgcolor="#05070a",
    font=dict(color="#cbd5e1")
)
st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# MOMENTUM
# -----------------------------
st.markdown("### MOMENTUM SIGNALS")

df_a["momentum"] = df_a["price"].pct_change().fillna(0)
fig2 = px.bar(df_a, x="date", y="momentum")
fig2.update_layout(
    paper_bgcolor="#05070a",
    plot_bgcolor="#05070a",
    font=dict(color="#cbd5e1")
)
st.plotly_chart(fig2, use_container_width=True)

# -----------------------------
# BACKTEST ENGINE
# -----------------------------
if run_backtest:
    st.markdown("### BACKTEST ENGINE")

    df_a["signal"] = np.where(df_a["price"] > df_a["price"].rolling(5).mean(), 1, -1)
    df_a["strategy_return"] = df_a["signal"] * df_a["price"].pct_change()
    df_a["cumulative"] = df_a["strategy_return"].cumsum()

    st.line_chart(df_a["cumulative"])

# -----------------------------
# STRESS TEST
# -----------------------------
if scenario != "None":
    sim = latest.copy()

    if scenario == "Demand Shock":
        sim["price"] *= 1.4
    elif scenario == "Supply Shock":
        sim["price"] *= 1.6

    risk = (sim["price"] - latest["price"]) / latest["price"]

    if risk > 0.2:
        level = "CRITICAL"
        color = "#ef4444"
    elif risk > 0.1:
        level = "ELEVATED"
        color = "#f59e0b"
    else:
        level = "STABLE"
        color = "#22c55e"

    st.markdown(f"""
    <div style='border:1px solid {color};padding:12px;border-radius:6px;'>
        <h3 style='color:{color};'>SYSTEM ALERT: {level}</h3>
        <p>Projected Price: {sim['price']:.2f}</p>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# AI ENGINE
# -----------------------------
st.markdown("### AI MARKET ENGINE")

trend = (latest["forecast_3days"] - latest["price"]) / latest["price"]

if latest["risk_score"] > 70:
    msg = "Institutional volatility detected. Risk exposure increasing."
elif latest["risk_score"] > 40:
    msg = "Moderate instability. Monitoring required."
else:
    msg = "Stable regime detected."

if trend > 0.1:
    msg += " Bullish continuation confirmed."

st.markdown(f"<div class='card'>{msg}</div>", unsafe_allow_html=True)

# -----------------------------
# ORDER FLOW
# -----------------------------
st.markdown("### ORDER FLOW DEPTH")

price = latest["price"]
levels = 8

order_flow = pd.DataFrame({
    "bid": [price - i*0.3 for i in range(levels)],
    "bid_size": np.random.randint(10, 100, levels),
    "ask": [price + i*0.3 for i in range(levels)],
    "ask_size": np.random.randint(10, 100, levels)
})

st.dataframe(order_flow)

# -----------------------------
# CORRELATION HEATMAP
# -----------------------------
st.markdown("### CROSS-ASSET CORRELATION HEATMAP")

pivot = df.pivot_table(index="date", columns="product", values="price").ffill()
corr = pivot.pct_change().corr()

fig3 = go.Figure(data=go.Heatmap(
    z=corr.values,
    x=corr.columns,
    y=corr.columns,
    colorscale="RdBu",
    zmid=0
))

fig3.update_layout(
    paper_bgcolor="#05070a",
    font=dict(color="#cbd5e1")
)
st.plotly_chart(fig3, use_container_width=True)

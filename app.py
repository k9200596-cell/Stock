
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
import pytz

st.set_page_config(
    page_title="My US Stock Portfolio",
    page_icon="📈",
    layout="wide",
)

# -----------------------------
# Style
# -----------------------------
st.markdown("""
<style>
.block-container {padding-top: 1.0rem; padding-bottom: 1rem;}
[data-testid="stMetricValue"] {font-size: 1.7rem;}
.small-note {color:#6b7280; font-size:0.88rem;}
.card-title {font-weight:700; font-size:1.05rem; margin-bottom:0.2rem;}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Default portfolio
# -----------------------------
DEFAULT = pd.DataFrame([
    {"Ticker":"IREN", "Shares":610, "Cost_KRW":35649619},
    {"Ticker":"RKLB", "Shares":128, "Cost_KRW":12907893},
    {"Ticker":"INFQ", "Shares":192, "Cost_KRW":3472734},
    {"Ticker":"DRAM", "Shares":66, "Cost_KRW":6178803},
])

# -----------------------------
# Sidebar controls
# -----------------------------
st.sidebar.header("설정")
refresh_sec = st.sidebar.selectbox("자동 새로고침", [30, 60, 120, 300], index=1, format_func=lambda x: f"{x}초")
st_autorefresh(interval=refresh_sec * 1000, key="refresh")

fx = st.sidebar.number_input("USD/KRW 환율", value=1346.57, min_value=500.0, max_value=3000.0, step=1.0)
high_mode = st.sidebar.radio("고점 기준", ["52주 최고", "역대 최고(ATH)"], index=0)

st.sidebar.caption("아래 표에서 보유수량·매입원가를 수정할 수 있습니다.")
portfolio = st.sidebar.data_editor(
    DEFAULT,
    hide_index=True,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Ticker": st.column_config.TextColumn("티커"),
        "Shares": st.column_config.NumberColumn("수량", min_value=0.0),
        "Cost_KRW": st.column_config.NumberColumn("매입원가(원)", min_value=0.0),
    },
)

tickers = [str(x).strip().upper() for x in portfolio["Ticker"].tolist() if str(x).strip()]

@st.cache_data(ttl=30)
def fetch_snapshot(tickers):
    rows = []
    for ticker in tickers:
        t = yf.Ticker(ticker)

        # Fast info is usually the quickest path to latest price / 52w data
        fi = t.fast_info
        last = fi.get("last_price")
        day_high = fi.get("day_high")
        day_low = fi.get("day_low")
        prev_close = fi.get("previous_close")
        high_52 = fi.get("year_high")

        # Fallback to recent history if fast_info misses values
        hist5 = t.history(period="5d", interval="1d", auto_adjust=False)
        if (last is None or pd.isna(last)) and not hist5.empty:
            last = float(hist5["Close"].dropna().iloc[-1])
        if (prev_close is None or pd.isna(prev_close)) and len(hist5["Close"].dropna()) >= 2:
            prev_close = float(hist5["Close"].dropna().iloc[-2])
        if (high_52 is None or pd.isna(high_52)):
            hist1y = t.history(period="1y", interval="1d", auto_adjust=False)
            if not hist1y.empty:
                high_52 = float(hist1y["High"].max())

        rows.append({
            "Ticker": ticker,
            "Price_USD": float(last) if last is not None and not pd.isna(last) else np.nan,
            "PrevClose_USD": float(prev_close) if prev_close is not None and not pd.isna(prev_close) else np.nan,
            "DayHigh_USD": float(day_high) if day_high is not None and not pd.isna(day_high) else np.nan,
            "DayLow_USD": float(day_low) if day_low is not None and not pd.isna(day_low) else np.nan,
            "High52_USD": float(high_52) if high_52 is not None and not pd.isna(high_52) else np.nan,
        })
    return pd.DataFrame(rows)

@st.cache_data(ttl=3600)
def fetch_ath(ticker):
    try:
        h = yf.Ticker(ticker).history(period="max", interval="1d", auto_adjust=False)
        if h.empty:
            return np.nan
        return float(h["High"].max())
    except Exception:
        return np.nan

snap = fetch_snapshot(tickers)

if portfolio.empty or snap.empty:
    st.warning("보유 종목을 입력해 주세요.")
    st.stop()

df = portfolio.copy()
df["Ticker"] = df["Ticker"].astype(str).str.strip().str.upper()
df = df.merge(snap, on="Ticker", how="left")

if high_mode == "역대 최고(ATH)":
    df["ReferenceHigh_USD"] = df["Ticker"].map(fetch_ath)
    high_label = "역대 최고"
else:
    df["ReferenceHigh_USD"] = df["High52_USD"]
    high_label = "52주 최고"

df["Daily_%"] = (df["Price_USD"] / df["PrevClose_USD"] - 1) * 100
df["FromHigh_%"] = (df["Price_USD"] / df["ReferenceHigh_USD"] - 1) * 100
df["Value_KRW"] = df["Shares"] * df["Price_USD"] * fx
df["PL_KRW"] = df["Value_KRW"] - df["Cost_KRW"]
df["PL_%"] = np.where(df["Cost_KRW"] > 0, df["PL_KRW"] / df["Cost_KRW"] * 100, np.nan)
total_value = df["Value_KRW"].sum()
total_cost = df["Cost_KRW"].sum()
total_pl = total_value - total_cost
total_pl_pct = total_pl / total_cost * 100 if total_cost else np.nan
df["Weight_%"] = np.where(total_value > 0, df["Value_KRW"] / total_value * 100, 0)

kst = pytz.timezone("Asia/Seoul")
now_kst = datetime.now(kst)

st.title("📈 미국주식 포트폴리오 대시보드")
st.caption(f"최근 시세 자동 갱신 · 마지막 화면 갱신: {now_kst.strftime('%Y-%m-%d %H:%M:%S KST')} · 데이터: Yahoo Finance")

m1, m2, m3, m4 = st.columns(4)
m1.metric("총 평가액", f"{total_value/1e6:,.2f} 백만원")
m2.metric("평가손익", f"{total_pl/1e6:,.2f} 백만원", f"{total_pl_pct:+.2f}%")
m3.metric("최대 비중 종목", df.loc[df["Weight_%"].idxmax(), "Ticker"], f"{df['Weight_%'].max():.1f}%")
worst_idx = df["FromHigh_%"].idxmin()
m4.metric(f"{high_label} 대비 최대낙폭", df.loc[worst_idx, "Ticker"], f"{df.loc[worst_idx, 'FromHigh_%']:.1f}%")

st.divider()

display = df[[
    "Ticker","Shares","Price_USD","Daily_%","ReferenceHigh_USD","FromHigh_%",
    "Value_KRW","Weight_%","PL_KRW","PL_%"
]].copy()
display.columns = [
    "종목","수량","현재가($)","당일(%)",f"{high_label}($)",f"{high_label} 대비(%)",
    "평가액(원)","비중(%)","평가손익(원)","수익률(%)"
]

def color_neg_pos(val):
    if pd.isna(val):
        return ""
    return "color: #16a34a; font-weight:600;" if val > 0 else ("color: #dc2626; font-weight:600;" if val < 0 else "")

styled = (
    display.style
    .format({
        "수량":"{:,.0f}",
        "현재가($)":"${:,.2f}",
        "당일(%)":"{:+.2f}%",
        f"{high_label}($)":"${:,.2f}",
        f"{high_label} 대비(%)":"{:+.2f}%",
        "평가액(원)":"{:,.0f}",
        "비중(%)":"{:.1f}%",
        "평가손익(원)":"{:+,.0f}",
        "수익률(%)":"{:+.2f}%",
    })
    .map(color_neg_pos, subset=["당일(%)", f"{high_label} 대비(%)", "평가손익(원)", "수익률(%)"])
)
st.dataframe(styled, use_container_width=True, hide_index=True, height=250)

c1, c2 = st.columns(2)

with c1:
    fig1 = px.pie(
        df,
        names="Ticker",
        values="Value_KRW",
        hole=0.55,
        title="포트폴리오 비중"
    )
    fig1.update_traces(textposition="inside", textinfo="percent+label")
    fig1.update_layout(margin=dict(l=10,r=10,t=50,b=10))
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    dd = df.sort_values("FromHigh_%")
    fig2 = px.bar(
        dd,
        x="FromHigh_%",
        y="Ticker",
        orientation="h",
        title=f"{high_label} 대비 현재 위치",
        text=dd["FromHigh_%"].map(lambda x: f"{x:.1f}%")
    )
    fig2.update_layout(xaxis_title="고점 대비 등락률(%)", yaxis_title="", margin=dict(l=10,r=10,t=50,b=10))
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("종목별 당일 움직임")
fig3 = px.bar(
    df.sort_values("Daily_%"),
    x="Ticker",
    y="Daily_%",
    text=df.sort_values("Daily_%")["Daily_%"].map(lambda x: f"{x:+.2f}%"),
)
fig3.update_layout(yaxis_title="전일 종가 대비(%)", xaxis_title="", margin=dict(l=10,r=10,t=20,b=10))
st.plotly_chart(fig3, use_container_width=True)

st.info(
    "참고: Yahoo Finance 데이터는 거래소·종목에 따라 실시간 또는 지연 시세일 수 있습니다. "
    "초단위의 완전한 실시간 시세가 필요하면 증권사 API 또는 유료 시세 API 연결이 필요합니다."
)

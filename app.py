import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="MarketLens AI", page_icon="📈", layout="wide")
st.title("📈 MarketLens AI")
st.caption("Aandelenonderzoek en technische momentopname · Geen automatische transacties")

DEFAULT_TICKERS = ["NVDA", "MSFT", "GOOGL", "AMZN", "META", "AAPL", "PLTR", "ORCL", "O", "SCHD"]

@st.cache_data(ttl=900, show_spinner=False)
def load_history(symbol):
    data = yf.Ticker(symbol).history(period="1y", auto_adjust=True)
    if data.empty:
        raise ValueError("Geen koersdata gevonden. Controleer het tickersymbool.")
    return data

def calculate_rsi(close, period=14):
    delta = close.diff()
    gains = delta.clip(lower=0).ewm(alpha=1 / period, adjust=False).mean()
    losses = (-delta.clip(upper=0)).ewm(alpha=1 / period, adjust=False).mean()
    rs = gains / losses.replace(0, float("nan"))
    return 100 - 100 / (1 + rs)

with st.sidebar:
    st.header("Aandeel analyseren")
    symbol = st.text_input("Ticker", value="NVDA").strip().upper()
    st.caption("Voorbeelden: NVDA, MSFT, AAPL, PLTR, ORCL")
    st.divider()
    st.caption("Deze eerste versie gebruikt Yahoo Finance voor historische marktdata.")

if not symbol:
    st.info("Vul een tickersymbool in.")
    st.stop()

try:
    with st.spinner(f"Marktgegevens ophalen voor {symbol}…"):
        hist = load_history(symbol)
        info = yf.Ticker(symbol).get_info()
except Exception as exc:
    st.error(f"De gegevens voor {symbol} konden niet worden opgehaald: {exc}")
    st.stop()

close = hist["Close"].dropna()
last = float(close.iloc[-1])
daily_change = (last / float(close.iloc[-2]) - 1) * 100 if len(close) > 1 else 0
rsi_value = float(calculate_rsi(close).iloc[-1])
sma20 = float(close.rolling(20).mean().iloc[-1])
sma50 = float(close.rolling(50).mean().iloc[-1])
sma200 = float(close.rolling(200).mean().iloc[-1]) if len(close) >= 200 else None
currency = info.get("currency", "USD")
company = info.get("longName") or info.get("shortName") or symbol

st.subheader(f"{company} ({symbol})")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Laatste koers", f"{last:,.2f} {currency}", f"{daily_change:+.2f}%")
c2.metric("RSI (14)", f"{rsi_value:.1f}", "Mogelijk overgekocht" if rsi_value >= 70 else ("Mogelijk oververkocht" if rsi_value <= 30 else "Neutraal"))
c3.metric("SMA 20", f"{sma20:,.2f} {currency}")
c4.metric("SMA 50", f"{sma50:,.2f} {currency}")

st.markdown("### Koersverloop — afgelopen 12 maanden")
st.line_chart(hist[["Close"]].rename(columns={"Close": "Koers"}), height=320)

st.markdown("### Technische momentopname")
rows = [
    ("Koers tegenover SMA 20", "Boven" if last > sma20 else "Onder"),
    ("Koers tegenover SMA 50", "Boven" if last > sma50 else "Onder"),
    ("RSI (14)", "Mogelijk overgekocht" if rsi_value >= 70 else ("Mogelijk oververkocht" if rsi_value <= 30 else "Neutraal")),
]
if sma200 is not None:
    rows.append(("Koers tegenover SMA 200", "Boven" if last > sma200 else "Onder"))
st.dataframe(pd.DataFrame(rows, columns=["Indicator", "Waarneming"]), use_container_width=True, hide_index=True)

st.warning("Dit is een technische momentopname, geen koop- of verkoopadvies. De app bevat momenteel nog geen gevalideerde koersvoorspelling, fundamentele analyse of volledige TradingAgents-integratie.")

st.markdown("### Snelle watchlist")
cols = st.columns(5)
for i, ticker in enumerate(DEFAULT_TICKERS):
    with cols[i % 5]:
        st.write(ticker)

st.caption("Geen brokerkoppeling, geen toegang tot je beleggingsrekening en geen automatische orders. Yahoo Finance-data kan vertraagd of onvolledig zijn.")

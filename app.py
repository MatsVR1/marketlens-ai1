from __future__ import annotations
import json, os
from datetime import date
from typing import Any
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="MarketLens AI", page_icon="📈", layout="wide")
st.markdown("""
<style>
.stApp{background:#0b1220;color:#e8edf5}
[data-testid="stSidebar"]{background:#101827}
[data-testid="stMetric"]{background:#131f31;border:1px solid #26364d;padding:12px;border-radius:12px}
.hero{padding:18px 22px;border:1px solid #26364d;border-radius:16px;background:linear-gradient(120deg,#14243a,#101827);margin-bottom:16px}
.muted{color:#9eacc0}
</style>
""",unsafe_allow_html=True)

UNIVERSE=["NVDA","MSFT","AAPL","AMZN","GOOGL","META","AVGO","TSLA","BRK-B","LLY","JPM","V","XOM","ORCL","COST","NFLX","PLTR","AMD","CRM","ADBE","ASML","SAP","MC.PA","NESN.SW","AZN.L","SHEL.L","AIR.PA"]
PROVIDERS={"OpenAI":("openai","OPENAI_API_KEY","gpt-6-luna","gpt-6-sol"),"Google Gemini":("google","GOOGLE_API_KEY","gemini-2.5-flash","gemini-2.5-pro"),"Anthropic Claude":("anthropic","ANTHROPIC_API_KEY","claude-sonnet-4-5","claude-opus-4-1"),"DeepSeek":("deepseek","DEEPSEEK_API_KEY","deepseek-chat","deepseek-reasoner"),"Groq":("groq","GROQ_API_KEY","llama-3.3-70b-versatile","llama-3.3-70b-versatile"),"OpenRouter":("openrouter","OPENROUTER_API_KEY","deepseek/deepseek-chat","anthropic/claude-sonnet-4.5"),"Mistral":("mistral","MISTRAL_API_KEY","mistral-large-latest","mistral-large-latest")}

@st.cache_data(ttl=600,show_spinner=False)
def history(ticker,period="1y"):
    d=yf.Ticker(ticker).history(period=period,auto_adjust=True,actions=False)
    if d is None or d.empty: raise ValueError("Geen koershistoriek gevonden. Controleer de ticker.")
    return d

@st.cache_data(ttl=1800,show_spinner=False)
def info(ticker):
    try:
        x=yf.Ticker(ticker).get_info()
        return x if isinstance(x,dict) else {}
    except Exception: return {}

@st.cache_data(ttl=900,show_spinner=False)
def news(ticker):
    try: raw=yf.Ticker(ticker).news or []
    except Exception: return []
    out=[]
    for item in raw[:10]:
        c=item.get("content",item); title=c.get("title") or item.get("title")
        if title:
            url=c.get("canonicalUrl") or {}; pub=c.get("provider") or {}
            out.append((title,pub.get("displayName") or item.get("publisher","Bron"),url.get("url") or item.get("link","")))
    return out

def rsi(close,n=14):
    delta=close.diff(); gain=delta.clip(lower=0).ewm(alpha=1/n,adjust=False,min_periods=n).mean()
    loss=(-delta.clip(upper=0)).ewm(alpha=1/n,adjust=False,min_periods=n).mean()
    rs=gain/loss.replace(0,np.nan); v=100-100/(1+rs)
    return v.mask((loss==0)&(gain>0),100).mask((gain==0)&(loss>0),0)

def metrics(d):
    c=d.Close.dropna(); p=float(c.iloc[-1]); prev=float(c.iloc[-2]); rv=rsi(c).iloc[-1]
    sma=lambda n: float(c.rolling(n).mean().iloc[-1]) if len(c)>=n else None
    ret=lambda n: (p/float(c.iloc[-n-1])-1)*100 if len(c)>n else None
    return {"price":p,"day":(p/prev-1)*100 if prev else 0,"rsi":float(rv) if pd.notna(rv) else None,"sma20":sma(20),"sma50":sma(50),"sma200":sma(200),"1m":ret(21),"3m":ret(63),"6m":ret(126),"high":float(c.tail(252).max()),"low":float(c.tail(252).min())}

def signal(m):
    s=sum([m["sma20"] is not None and m["price"]>m["sma20"],m["sma50"] is not None and m["price"]>m["sma50"],m["sma200"] is not None and m["price"]>m["sma200"],m["rsi"] is not None and 45<=m["rsi"]<=68])
    if m["rsi"] is not None and m["rsi"]>75:s-=1
    return "Technisch positief" if s>=3 else ("Technisch zwak" if s<=0 else "Gemengd beeld")

def get_secret(key):
    try:return os.getenv(key) or st.secrets.get(key)
    except Exception:return os.getenv(key)

def run_agents(ticker,provider,key,quick,deep,analysts,debate,risk):
    env=PROVIDERS[provider][1]; os.environ[env]=key
    from tradingagents.default_config import DEFAULT_CONFIG
    from tradingagents.graph.trading_graph import TradingAgentsGraph
    cfg=DEFAULT_CONFIG.copy(); pid=PROVIDERS[provider][0]
    cfg.update({"llm_provider":pid,"quick_think_provider":pid,"deep_think_provider":pid,
      "quick_think_llm":quick,"deep_think_llm":deep,"output_language":"Dutch",
      "max_debate_rounds":debate,"max_risk_discuss_rounds":risk,"max_tool_rounds":8,
      "max_recur_limit":100,"checkpoint_enabled":False})
    graph=TradingAgentsGraph(selected_analysts=tuple(analysts),debug=False,config=cfg)
    return graph.propagate(ticker,date.today().isoformat())

def price(x,c="USD"):
    try:return f"{float(x):,.2f} {c}"
    except (ValueError,TypeError):return "—"

with st.sidebar:
    st.markdown("# 📈 MarketLens AI")
    st.caption("Multi-agent aandelenonderzoek")
    page=st.radio("Navigatie",["Dashboard","Aandeel analyseren","Marktscanner","AI TradingAgents","Watchlist","Instellingen"],label_visibility="collapsed")
    st.divider(); st.caption("Yahoo Finance · Geen brokerkoppeling")
if "watchlist" not in st.session_state:st.session_state.watchlist=["NVDA","MSFT","AAPL","PLTR","ORCL"]
if "agent_result" not in st.session_state:st.session_state.agent_result=None
st.markdown('<div class="hero"><h1 style="margin:0">MarketLens <span style="color:#55a7ff">AI</span></h1><p class="muted" style="margin:5px 0 0">Onderzoek. Vergelijk. Beslis geïnformeerd.</p></div>',unsafe_allow_html=True)

if page=="Dashboard":
    st.subheader("Marktoverzicht")
    cols=st.columns(4)
    for col,(name,ticker) in zip(cols,[("S&P 500","^GSPC"),("Nasdaq","^IXIC"),("Dow Jones","^DJI"),("Euro Stoxx 50","^STOXX50E")]):
        try:
            d=history(ticker,"5d"); p=float(d.Close.iloc[-1]); ch=(p/float(d.Close.iloc[-2])-1)*100
            col.metric(name,f"{p:,.2f}",f"{ch:+.2f}%")
        except Exception:col.metric(name,"Niet beschikbaar")
    st.subheader("Jouw watchlist")
    rows=[]
    for t in st.session_state.watchlist:
        try:
            d=history(t,"6mo"); m=metrics(d); inf=info(t)
            rows.append({"Ticker":t,"Bedrijf":inf.get("shortName",t),"Koers":price(m["price"],inf.get("currency","USD")),"Dag":f'{m["day"]:+.2f}%',"RSI":round(m["rsi"],1) if m["rsi"] is not None else "—","Technisch beeld":signal(m)})
        except Exception as e:rows.append({"Ticker":t,"Bedrijf":"—","Koers":"—","Dag":"—","RSI":"—","Technisch beeld":str(e)[:40]})
    st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    st.info("Technische labels zijn indicatorensamenvattingen, geen voorspellingen of koopadviezen.")

elif page=="Aandeel analyseren":
    st.subheader("Aandeel analyseren")
    c1,c2=st.columns([3,1])
    with c1:t=st.text_input("Ticker / beurscode","NVDA").strip().upper()
    with c2:
        st.write("")
        if st.button("＋ Watchlist") and t:
            if t not in st.session_state.watchlist:st.session_state.watchlist.append(t)
            st.success(f"{t} toegevoegd.")
    if t:
        try:
            d=history(t); m=metrics(d); inf=info(t); cur=inf.get("currency","USD")
            st.markdown(f"### {inf.get('longName') or inf.get('shortName') or t} ({t})")
            cols=st.columns(5)
            cols[0].metric("Koers",price(m["price"],cur),f'{m["day"]:+.2f}%')
            cols[1].metric("RSI 14",f'{m["rsi"]:.1f}' if m["rsi"] is not None else "—","Overgekocht" if m["rsi"] and m["rsi"]>=70 else ("Oververkocht" if m["rsi"] and m["rsi"]<=30 else "Neutraal"))
            cols[2].metric("Marktkapitalisatie",f'{inf["marketCap"]/1e9:.1f}B {cur}' if isinstance(inf.get("marketCap"),(int,float)) else "—")
            cols[3].metric("P/E",f'{inf["trailingPE"]:.1f}' if isinstance(inf.get("trailingPE"),(int,float)) else "—")
            cols[4].metric("Dividendrendement",f'{inf["dividendYield"]*100:.2f}%' if isinstance(inf.get("dividendYield"),(int,float)) else "—")
            fig=go.Figure()
            fig.add_trace(go.Scatter(x=d.index,y=d.Close,name="Koers",line=dict(color="#55a7ff",width=2)))
            for n,col in [(20,"#f6bd60"),(50,"#9b8cff"),(200,"#49c6a8")]:
                if len(d)>=n:fig.add_trace(go.Scatter(x=d.index,y=d.Close.rolling(n).mean(),name=f"SMA {n}",line=dict(color=col,width=1.2)))
            fig.update_layout(height=370,margin=dict(l=0,r=0,t=15,b=0),paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",font_color="#dce6f3",legend=dict(orientation="h",y=1.1))
            fig.update_yaxes(gridcolor="#26364d");fig.update_xaxes(showgrid=False)
            st.plotly_chart(fig,use_container_width=True,config={"displayModeBar":False})
            st.markdown("#### Technische analyse")
            tech=[]
            for n in (20,50,200):
                v=m[f"sma{n}"]
                if v is not None:tech.append({"Indicator":f"SMA {n}","Waarde":price(v,cur),"Koerspositie":"Boven" if m["price"]>v else "Onder"})
            tech.append({"Indicator":"RSI 14","Waarde":f'{m["rsi"]:.1f}' if m["rsi"] is not None else "—","Koerspositie":"Overgekocht" if m["rsi"] and m["rsi"]>=70 else ("Oververkocht" if m["rsi"] and m["rsi"]<=30 else "Neutraal")})
            st.dataframe(pd.DataFrame(tech),use_container_width=True,hide_index=True)
            st.markdown("#### Bedrijfsfundamenten")
            fcols=st.columns(4)
            for col,(label,key,fmt) in zip(fcols,[("Omzet TTM","totalRevenue","money"),("Winstmarge","profitMargins","pct"),("ROE","returnOnEquity","pct"),("Debt / Equity","debtToEquity","num")]):
                v=inf.get(key); shown=(f"{v/1e9:.2f}B {cur}" if fmt=="money" else (f"{v*100:.1f}%" if fmt=="pct" else f"{v:.1f}")) if isinstance(v,(int,float)) else "Niet beschikbaar"
                col.metric(label,shown)
            if inf.get("longBusinessSummary"):st.write(inf["longBusinessSummary"][:1500])
            st.markdown("#### Recent nieuws")
            items=news(t)
            if items:
                for title,publisher,url in items:
                    st.markdown(f"- [{title}]({url}) · *{publisher}*" if url else f"- {title} · *{publisher}*")
            else:st.caption("Geen nieuwsitems beschikbaar.")
        except Exception as e:st.error(str(e))
        st.caption("Yahoo Finance-data kan vertraagd, onvolledig of tijdelijk onbeschikbaar zijn. Controleer kerncijfers bij primaire bronnen.")

elif page=="Marktscanner":
    st.subheader("Marktscanner")
    st.write("Rangschik een watchlist op momentum en technische indicatoren. Dit is geen premarket voorspeller.")
    raw=st.text_area("Tickers, komma- of regelgescheiden",", ".join(UNIVERSE),height=100)
    tickers=list(dict.fromkeys(x.strip().upper() for x in raw.replace("\n",",").split(",") if x.strip()))[:50]
    if st.button("🔎 Start scan",type="primary"):
        results=[];bar=st.progress(0);status=st.empty()
        for i,t in enumerate(tickers):
            status.write(f"Scannen {t} ({i+1}/{len(tickers)})")
            try:
                d=history(t);m=metrics(d);inf=info(t);score=sum([m["sma20"] is not None and m["price"]>m["sma20"],m["sma50"] is not None and m["price"]>m["sma50"],m["sma200"] is not None and m["price"]>m["sma200"],m["rsi"] is not None and 50<=m["rsi"]<=68])-(m["rsi"] is not None and m["rsi"]>=75)
                results.append({"Ticker":t,"Bedrijf":inf.get("shortName",t),"Koers":m["price"],"Dag %":m["day"],"1m %":m["1m"],"3m %":m["3m"],"RSI":m["rsi"],"Score":int(score),"Technisch beeld":signal(m)})
            except Exception as e:results.append({"Ticker":t,"Bedrijf":"—","Koers":np.nan,"Dag %":np.nan,"1m %":np.nan,"3m %":np.nan,"RSI":np.nan,"Score":-99,"Technisch beeld":f"Fout: {str(e)[:35]}"})
            bar.progress((i+1)/len(tickers))
        status.empty();bar.empty()
        st.session_state.scan=pd.DataFrame(results).sort_values(["Score","3m %"],ascending=False,na_position="last")
    if "scan" in st.session_state:
        df=st.session_state.scan
        st.dataframe(df,use_container_width=True,hide_index=True)
        st.download_button("Download CSV",df.to_csv(index=False).encode(), "marketlens_scan.csv","text/csv")

elif page=="AI TradingAgents":
    st.subheader("Volledige multi-agentanalyse")
    st.write("De upstream-agent gebruikt analisten voor markt, nieuws, social sentiment en fundamentals, gevolgd door bullish/bearish debat, trader en risicomanagement.")
    st.warning("AI-analyses vereisen een provider-API-sleutel en kunnen kosten veroorzaken. Er worden nooit orders geplaatst.")
    with st.form("agents"):
        ticker=st.text_input("Ticker","NVDA").strip().upper()
        provider=st.selectbox("AI-provider",list(PROVIDERS))
        pid,env,quick_default,deep_default=PROVIDERS[provider]
        secret=get_secret(env)
        key=st.text_input("API-sleutel"+(" (gevonden in hosting secrets)" if secret else ""),type="password",help="Plaats de sleutel bij voorkeur in Streamlit → App settings → Secrets.")
        key=key or secret or ""
        quick=st.text_input("Snel model voor analisten",quick_default)
        deep=st.text_input("Diep model voor debat / risico",deep_default)
        analysts=st.multiselect("Analistenteams",["market","social","news","fundamentals"],default=["market","news","fundamentals"],format_func=lambda x:{"market":"Markt & technisch","social":"Social sentiment","news":"Nieuws","fundamentals":"Fundamentals"}[x])
        debate=st.slider("Debatrondes",1,3,1);risk=st.slider("Risicorondes",1,3,1)
        go=st.form_submit_button("Start volledige AI-analyse",type="primary")
    if go:
        if not ticker or not key:st.error("Vul een ticker en geldige API-sleutel in.")
        elif not analysts:st.error("Selecteer minstens één analistenteam.")
        else:
            try:
                with st.spinner("Agenten analyseren data, debatteren en beoordelen risico. Dit kan minuten duren…"):
                    state,decision=run_agents(ticker,provider,key,quick,deep,analysts,debate,risk)
                st.session_state.agent_result={"ticker":ticker,"decision":str(decision),"state":state}
                st.success("Analyse afgerond.")
            except Exception as e:st.error(f"AI-analyse mislukt: {e}")
    if st.session_state.agent_result:
        r=st.session_state.agent_result
        st.markdown(f"### Resultaat {r['ticker']}")
        st.markdown(f"**TradingAgents-signaal:** {r['decision']}")
        with st.expander("Agent-output bekijken",expanded=True):
            try:st.json(r["state"])
            except Exception:st.code(str(r["state"])[:30000])
        st.download_button("Download rapport JSON",json.dumps({"ticker":r["ticker"],"decision":r["decision"],"state":str(r["state"])},ensure_ascii=False,indent=2),f"{r['ticker']}_report.json","application/json")

elif page=="Watchlist":
    st.subheader("Watchlist")
    new=st.text_input("Ticker toevoegen",placeholder="ASML.AS").strip().upper()
    c1,c2=st.columns(2)
    if c1.button("Toevoegen") and new:
        if new not in st.session_state.watchlist:st.session_state.watchlist.append(new)
        st.rerun()
    if c2.button("Leegmaken"):st.session_state.watchlist=[];st.rerun()
    for t in list(st.session_state.watchlist):
        a,b=st.columns([4,1]);a.write(f"**{t}**")
        if b.button("Verwijder",key=f"del_{t}"):st.session_state.watchlist.remove(t);st.rerun()
    st.caption("Watchlist wordt voorlopig in de browsersessie bewaard, niet tussen apparaten gesynchroniseerd.")

elif page=="Instellingen":
    st.subheader("Instellingen & transparantie")
    st.markdown("**Databronnen**")
    st.write("- Koersen, bedrijfsprofielen en headlines: Yahoo Finance via yfinance.")
    st.write("- Multi-agentonderzoek: officiële TauricResearch TradingAgents-code.")
    st.markdown("**API-sleutels**")
    st.write("Voeg een sleutel toe bij Streamlit Community Cloud → App settings → Secrets:")
    st.code('GOOGLE_API_KEY = "jouw_api_key"\\n# of OPENAI_API_KEY / ANTHROPIC_API_KEY / GROQ_API_KEY',language="toml")
    st.warning("Zet nooit echte sleutels in GitHub. Als een sleutel openbaar werd, trek hem in en maak een nieuwe aan.")
    st.markdown("**Wat deze app niet doet**")
    st.write("- Geen brokerkoppeling, toegang tot Bolero of automatische transacties.")
    st.write("- Geen gegarandeerde rendementen of gekalibreerde kansen op toekomstige koersbewegingen.")
    st.write("- Geen gegarandeerde realtime/premarket feed.")
    st.write("- Geen persoonlijk financieel advies.")

st.divider()
st.caption("MarketLens AI is onderzoekssoftware, geen beleggingsadvies. AI kan fouten maken. Verifieer cijfers, nieuws en waarderingen bij primaire bronnen.")

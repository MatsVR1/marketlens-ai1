# MarketLens AI

Mobile-friendly stock research dashboard powered by the official [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents) multi-agent framework.

## Features
- Ticker lookup, 1-year price chart and RSI(14), SMA20/50/200
- Company profile and selected fundamentals (market cap, P/E, dividend yield, revenue, margins, ROE, debt/equity)
- Recent Yahoo Finance headlines
- Configurable scanner for up to 50 tickers, ranked by transparent technical/momentum heuristics; CSV export
- Session watchlist
- Full optional TradingAgents workflow: market, social, news and fundamentals analysts, bullish/bearish debate, trader and risk-management stages
- Dutch-language agent output
- No broker integration, account access or order execution

## Local setup
Python 3.11 or newer is required by the upstream framework.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Community Cloud
Use repository `MatsVR1/marketlens-ai1`, branch `main`, main file `app.py`. The upstream framework has a large dependency tree; cloud builds may fail due to memory or dependency limits. A deployment is not considered successful until the build completes and the app is opened and tested.

## AI provider
The market-data and technical-analysis pages need no LLM key. The multi-agent workflow does. Add one provider key under Streamlit Community Cloud → App settings → Secrets, for example:

```toml
GOOGLE_API_KEY = "your-key"
```

Other environment keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `DEEPSEEK_API_KEY`, `GROQ_API_KEY`, `OPENROUTER_API_KEY`, `MISTRAL_API_KEY`. Provider pricing, model IDs and free-tier limits can change. Agent runs may incur costs; set provider spending limits where available.

Never commit real API keys. Revoke and rotate any key that is exposed.

## Limitations and safety
Yahoo Finance data may be delayed, incomplete, rate-limited or unavailable. Scanner scores are technical/momentum summaries, not forecasts or calibrated probabilities. The app does not provide a verified premarket top-movers prediction. LLM output is non-deterministic and may be wrong; verify claims against primary sources. This is research software, not personal financial advice or a strategy with guaranteed returns.

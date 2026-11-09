# MarketLens AI — TradingAgents dashboard

Een eerste webdashboard bovenop [TauricResearch/TradingAgents](https://github.com/TauricResearch/TradingAgents).

## Wat zit in deze MVP?
- Ticker invoeren
- Yahoo Finance-koersdata ophalen
- 1-jaars koersgrafiek
- RSI(14), SMA20, SMA50 en SMA200
- Watchlist met voorbeeldtickers
- Optionele koppeling met TradingAgents (apart te installeren en te configureren)

## Installatie (Python 3.11+)

```bash
python -m venv .venv
pip install -r requirements.txt
streamlit run app.py
```

De basisapp heeft geen betaalde AI-sleutel nodig. De optionele multi-agentfunctie kan afzonderlijk worden geïnstalleerd met `pip install git+https://github.com/TauricResearch/TradingAgents.git`. Daarvoor is doorgaans een LLM-provider API-sleutel nodig; die kan kosten veroorzaken.

## Belangrijk
- Dit is een MVP, geen afgewerkt of gevalideerd handelssysteem.
- TradingAgents is een onderzoeksframework; het kan fouten maken en garandeert geen rendement.
- Yahoo Finance-data kan vertraagd, onvolledig of tijdelijk niet beschikbaar zijn.
- RSI/SMA zijn beschrijvende technische indicatoren, geen bewezen voorspellingen.
- Er zijn geen automatische transacties of brokerkoppelingen.
- Test eerst en controleer de output zelf.

API-sleutels horen in omgevingsvariabelen of hosting-secrets, nooit in GitHub.

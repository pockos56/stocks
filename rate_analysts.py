import requests
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

API_KEY = "d2os7ghr01qnhraog5c0d2os7ghr01qnhraog5cg"

def get_analyst_recommendations(ticker):
    """Fetch analyst recommendations from Finnhub."""
    url = f"https://finnhub.io/api/v1/stock/recommendation?symbol={ticker}&token={API_KEY}"
    response = requests.get(url)
    data = response.json()
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    df["ticker"] = ticker
    return df

def get_stock_data(ticker, start, end):
    """Fetch stock price history from Yahoo Finance."""
    stock = yf.Ticker(ticker)
    return stock.history(start=start, end=end)

def evaluate_recommendations(ticker, recs, window_days=30):
    """
    Score analyst recommendations by checking stock performance after N days.
    """
    results = []
    for _, rec in recs.iterrows():
        rec_date = datetime.strptime(rec["period"], "%Y-%m-%d")
        window_end = rec_date + timedelta(days=window_days)

        hist = get_stock_data(ticker, rec_date.strftime("%Y-%m-%d"), window_end.strftime("%Y-%m-%d"))
        if hist.empty:
            continue

        start_price = hist.iloc[0]["Close"]
        end_price = hist.iloc[-1]["Close"]
        perf = (end_price - start_price) / start_price * 100

        # Simplified accuracy scoring
        if rec["buy"] > rec["sell"] and perf > 0:
            score = 1
        elif rec["sell"] > rec["buy"] and perf < 0:
            score = 1
        else:
            score = 0

        results.append({
            "ticker": ticker,
            "date": rec["period"],
            "buy": rec["buy"],
            "hold": rec["hold"],
            "sell": rec["sell"],
            "strongBuy": rec["strongBuy"],
            "strongSell": rec["strongSell"],
            "perf_%": round(perf, 2),
            "score": score
        })
    return pd.DataFrame(results)

# Example: Elanco (ELAN)
ticker = "MSFT"
recs = get_analyst_recommendations(ticker)
df = evaluate_recommendations(ticker, recs)
print(df)

if not df.empty:
    print("\nOverall accuracy score:", df["score"].mean())

import requests
import pandas as pd
from bs4 import BeautifulSoup

def scrape_marketbeat(ticker):
    url = f"https://www.marketbeat.com/stocks/NYSE/{ticker}/price-target/"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")

    table = soup.find("table", {"class": "scroll-table"})
    if not table:
        return pd.DataFrame()

    rows = []
    for tr in table.find("tbody").find_all("tr"):
        cols = [td.get_text(strip=True) for td in tr.find_all("td")]
        if len(cols) >= 4:
            rows.append({
                "date": cols[0],
                "firm": cols[1],
                "rating": cols[2],
                "price_target": cols[3]
            })

    return pd.DataFrame(rows)

# Example usage
ticker = "MSFT"
elan_df = scrape_marketbeat("TSLA")
print(elan_df.head())


#!/usr/bin/env python3
"""
backtest.py
Calculates historical performance and win-rate analysis for CL's Tickers.
Updates data/backtest_results.json incrementally to prevent redundant yfinance API calls.
"""

import os
import json
from datetime import datetime, timedelta, timezone
import pytz
import yfinance as yf

# Paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
STOCK_DATA_FILE = os.path.join(CURRENT_DIR, "data", "stock_data.json")
BACKTEST_FILE = os.path.join(CURRENT_DIR, "data", "backtest_results.json")

def get_trade_week_and_friday(date_str: str):
    """
    Maps a signal date YYYY-MM-DD to its trading week identifier and Friday close date.
    - Monday to Friday: Closes on Friday of the same week.
    - Saturday to Sunday: Closes on Friday of the following week.
    """
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    weekday = dt.weekday() # 0 = Monday, 6 = Sunday
    
    if weekday >= 5: # Saturday or Sunday
        # Signal belongs to the upcoming week, closing on the upcoming Friday
        days_to_friday = 4 + (7 - weekday)
        friday_dt = dt + timedelta(days=days_to_friday)
    else:
        # Signal belongs to the current week, closing on this Friday
        days_to_friday = 4 - weekday
        friday_dt = dt + timedelta(days=days_to_friday)
        
    start_of_week = friday_dt - timedelta(days=4)
    
    week_id = f"{friday_dt.strftime('%Y-W%U')}" # e.g. 2026-W21
    week_label = f"Week {friday_dt.strftime('%U')} ({start_of_week.strftime('%b %d')} - {friday_dt.strftime('%b %d, %Y')})"
    friday_date_str = friday_dt.strftime("%Y-%m-%d")
    
    return week_id, week_label, friday_date_str

def check_is_market_hours(utc_timestamp_str: str) -> tuple[bool, datetime | None]:
    """
    Parses a UTC ISO 8601 timestamp string and checks if it fell within US market trading hours:
    Monday to Friday, 9:30 AM to 4:00 PM US Eastern Time (ET).
    """
    if not utc_timestamp_str:
        return False, None
    
    try:
        # Parse UTC time
        # Handle trailing Z or offset
        if utc_timestamp_str.endswith("Z"):
            utc_dt = datetime.fromisoformat(utc_timestamp_str.replace("Z", "+00:00"))
        else:
            utc_dt = datetime.fromisoformat(utc_timestamp_str)
            
        # Convert to Eastern Time
        eastern_tz = pytz.timezone("US/Eastern")
        et_dt = utc_dt.astimezone(eastern_tz)
        
        # Check weekday: 0 = Mon, 4 = Fri
        if et_dt.weekday() > 4:
            return False, et_dt
            
        # Check time: 9:30 AM to 4:00 PM
        market_start = et_dt.replace(hour=9, minute=30, second=0, microsecond=0)
        market_end = et_dt.replace(hour=16, minute=0, second=0, microsecond=0)
        
        is_market_hours = market_start <= et_dt <= market_end
        return is_market_hours, et_dt
    except Exception as e:
        print(f"⚠️ Error parsing timestamp {utc_timestamp_str}: {e}")
        return False, None

def get_stock_price(ticker: str, target_date_str: str, utc_timestamp_str: str = None, is_friday_close: bool = False) -> float:
    """
    Fetches the stock price from yfinance.
    - If is_friday_close: Fetches the daily close price of the target Friday (or latest available trading day before it).
    - If not is_friday_close:
        - If utc_timestamp_str was inside market hours, fetches the hourly K-line price matching that hour.
        - Otherwise, fetches the daily close price of the target date (or first available trading day after it).
    """
    # Map index symbols to liquid/tradeable ETFs for better yfinance reliability and actual close pricing
    ticker_map = {
        "SPX": "SPY",
        "SPY": "SPY",
        "COMP": "QQQ",
        "COMPX": "QQQ",
        "DJI": "DIA",
        "SOXX": "SOXX",
        "SMH": "SMH",
    }
    symbol = ticker_map.get(ticker.upper(), ticker.upper())
    
    try:
        t = yf.Ticker(symbol)
        
        # Check for Friday close
        if is_friday_close:
            target_dt = datetime.strptime(target_date_str, "%Y-%m-%d")
            # Fetch 5 days before to target_date+1 to capture the Friday close or last active trading day of that week
            start_str = (target_dt - timedelta(days=5)).strftime("%Y-%m-%d")
            end_str = (target_dt + timedelta(days=1)).strftime("%Y-%m-%d")
            hist = t.history(start=start_str, end=end_str, interval="1d")
            if not hist.empty:
                return round(float(hist.iloc[-1]["Close"]), 2)
            return 0.0
            
        # Check if intraday price is possible (inside market hours)
        is_market, et_dt = check_is_market_hours(utc_timestamp_str)
        
        if is_market and et_dt:
            # Fetch K-lines for that specific day
            day_str = et_dt.strftime("%Y-%m-%d")
            next_day_str = (et_dt + timedelta(days=1)).strftime("%Y-%m-%d")
            
            # Fetch 1-hour intervals
            hist = t.history(start=day_str, end=next_day_str, interval="1h")
            if not hist.empty:
                # Find the hour candle matching our tweet's Eastern Time hour
                tweet_hour = et_dt.hour
                for index, row in hist.iterrows():
                    # K-lines are timezone-aware Eastern
                    candle_time = index.astimezone(pytz.timezone("US/Eastern"))
                    if candle_time.hour == tweet_hour:
                        # Return the Open or Close of that hour
                        print(f"🎯 Matched hourly intraday price for {symbol} at {tweet_hour}:00 ET: ${row['Open']:.2f}")
                        return round(float(row["Open"]), 2)
                
                # If no exact hour matched, fall back to first hourly price or daily close
                print(f"ℹ️ Hourly candle match missed for {symbol} at hour {tweet_hour}. Falling back to daily close.")
        
        # Default Fallback: Daily Close Price
        target_dt = datetime.strptime(target_date_str, "%Y-%m-%d")
        start_str = target_dt.strftime("%Y-%m-%d")
        # Allow 5 days range forward to find first trading day if it was holiday/weekend
        end_str = (target_dt + timedelta(days=5)).strftime("%Y-%m-%d")
        hist = t.history(start=start_str, end=end_str, interval="1d")
        if not hist.empty:
            return round(float(hist.iloc[0]["Close"]), 2)
            
    except Exception as e:
        print(f"⚠️ yfinance error fetching {symbol} (date: {target_date_str}, timestamp: {utc_timestamp_str}): {e}")
        
    return 0.0

def run_backtest():
    """
    Main backtesting loop.
    1. Loads stock_data.json.
    2. Loads existing backtest_results.json (to preserve finalized data).
    3. Groups ALL stock_data recommendations by trading week to prevent overwriting daily records.
    4. Identifies and calculates results for unfinalized recommendations.
    5. Computes global metrics.
    6. Saves updated backtest_results.json.
    """
    print("📈 Starting CL's Tickers Historical Performance Backtest...")
    
    if not os.path.exists(STOCK_DATA_FILE):
        print("❌ Error: stock_data.json does not exist. No recommendations to backtest.")
        return
        
    with open(STOCK_DATA_FILE, "r", encoding="utf-8") as f:
        stock_data = json.load(f)
        
    # Load or initialize backtest results
    results_db = {"summary": {}, "weeks": {}}
    if os.path.exists(BACKTEST_FILE):
        try:
            with open(BACKTEST_FILE, "r", encoding="utf-8") as f:
                results_db = json.load(f)
                print(f"📂 Loaded existing backtest database with {len(results_db.get('weeks', {}))} weeks.")
        except Exception as e:
            print(f"⚠️ Failed to parse existing backtest file: {e}. Starting fresh.")
            
    if "weeks" not in results_db:
        results_db["weeks"] = {}
        
    current_time_utc = datetime.now(timezone.utc)
    
    # 1. Group all recommendations across ALL dates by their week_id first
    grouped_recs = {}
    for signal_date, date_content in stock_data.items():
        week_id, week_label, friday_date_str = get_trade_week_and_friday(signal_date)
        if week_id not in grouped_recs:
            grouped_recs[week_id] = {
                "week_label": week_label,
                "friday_date": friday_date_str,
                "recs": []
            }
            
        # Add buys
        for b in date_content.get("buy", []):
            grouped_recs[week_id]["recs"].append({
                "signal_date": signal_date,
                "ticker": b["ticker"].upper(),
                "action": "BUY"
            })
            
        # Add sells
        for s in date_content.get("sell", []):
            grouped_recs[week_id]["recs"].append({
                "signal_date": signal_date,
                "ticker": s["ticker"].upper(),
                "action": "SELL"
            })
            
    # 2. Process each week's combined list of trades
    for week_id, week_content in grouped_recs.items():
        week_label = week_content["week_label"]
        friday_date_str = week_content["friday_date"]
        
        # Check if this Friday close is finalized (Friday 8:00 PM PST / 11:00 PM EST, which is Saturday 3:00 AM UTC)
        # We define "finalized" if current time is past Saturday 4:00 AM UTC of that week's Friday
        friday_dt = datetime.strptime(friday_date_str, "%Y-%m-%d")
        finalized_cutoff = datetime(friday_dt.year, friday_dt.month, friday_dt.day, tzinfo=timezone.utc) + timedelta(days=1, hours=4)
        is_week_finalized = (current_time_utc > finalized_cutoff)
        
        # Initialize week container in database if not present
        if week_id not in results_db["weeks"]:
            results_db["weeks"][week_id] = {
                "week_label": week_label,
                "friday_date": friday_date_str,
                "trades": []
            }
            
        existing_trades = results_db["weeks"][week_id]["trades"]
        updated_trades = []
        
        for rec in week_content["recs"]:
            ticker = rec["ticker"]
            action = rec["action"]
            signal_date = rec["signal_date"]
            
            # Find exact UTC timestamp from the tweet metadata in stock_data.json
            tweet_timestamp = None
            date_items = stock_data[signal_date].get("buy" if action == "BUY" else "sell", [])
            for item in date_items:
                if item["ticker"].upper() == ticker:
                    tweets = item.get("tweets", [])
                    if tweets:
                        tweet_timestamp = tweets[0].get("created_at")
                    break
            
            # Look for existing matching trade record in this week
            matching_trade = None
            for trade in existing_trades:
                if trade["ticker"].upper() == ticker and trade["action"] == action and trade["signal_date"] == signal_date:
                    matching_trade = trade
                    break
                    
            # If the trade is already finalized, preserve it without yfinance calls!
            if matching_trade and matching_trade.get("finalized") and matching_trade.get("entry_price", 0) > 0 and matching_trade.get("friday_close", 0) > 0:
                updated_trades.append(matching_trade)
                continue
                
            # Otherwise, recalculate/fetch prices
            print(f"🔍 Processing: {ticker} ({action}) recommended on {signal_date} (timestamp: {tweet_timestamp})")
            
            # Fetch Entry Price
            entry_price = 0.0
            if matching_trade and matching_trade.get("entry_price", 0) > 0:
                entry_price = matching_trade["entry_price"]
            else:
                entry_price = get_stock_price(ticker, signal_date, tweet_timestamp, is_friday_close=False)
                
            # Fetch Friday Close Price
            friday_close = get_stock_price(ticker, friday_date_str, is_friday_close=True)
            
            # Calculate Performance
            perf_pct = 0.0
            result = "PENDING"
            
            if entry_price > 0.0 and friday_close > 0.0:
                if action == "BUY":
                    perf_pct = ((friday_close - entry_price) / entry_price) * 100
                    result = "WIN" if friday_close > entry_price else "LOSE"
                else: # SELL
                    perf_pct = ((entry_price - friday_close) / entry_price) * 100
                    result = "WIN" if friday_close < entry_price else "LOSE"
                    
                perf_pct = round(perf_pct, 2)
            
            trade_record = {
                "ticker": ticker,
                "action": action,
                "signal_date": signal_date,
                "tweet_timestamp": tweet_timestamp,
                "entry_price": entry_price,
                "friday_close": friday_close,
                "perf_pct": perf_pct,
                "result": result,
                "finalized": is_week_finalized and entry_price > 0.0 and friday_close > 0.0
            }
            
            print(f"📊 Result for {ticker}: Entry={entry_price}, Friday Close={friday_close}, Perf={perf_pct:+.2f}%, Outcome={result}")
            updated_trades.append(trade_record)
            
        results_db["weeks"][week_id]["trades"] = updated_trades
        
    # Remove empty weeks
    results_db["weeks"] = {wid: wdata for wid, wdata in results_db["weeks"].items() if len(wdata["trades"]) > 0}
    
    # 3. Calculate Global Metrics & Aggregations
    total_signals = 0
    wins = 0
    losses = 0
    total_perf = 0.0
    valid_trade_count = 0
    
    for week_id, week_data in results_db["weeks"].items():
        for trade in week_data["trades"]:
            if trade["result"] != "PENDING":
                total_signals += 1
                if trade["result"] == "WIN":
                    wins += 1
                elif trade["result"] == "LOSE":
                    losses += 1
                    
                if trade["entry_price"] > 0 and trade["friday_close"] > 0:
                    total_perf += trade["perf_pct"]
                    valid_trade_count += 1
                    
    win_rate = (wins / total_signals * 100) if total_signals > 0 else 0.0
    avg_return = (total_perf / valid_trade_count) if valid_trade_count > 0 else 0.0
    
    results_db["summary"] = {
        "total_signals": total_signals,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 2),
        "average_return": round(avg_return, 2)
    }
    
    # 4. Save back to file
    os.makedirs(os.path.dirname(BACKTEST_FILE), exist_ok=True)
    with open(BACKTEST_FILE, "w", encoding="utf-8") as f:
        json.dump(results_db, f, indent=2, ensure_ascii=False)
        
    print(f"💾 Backtest database updated successfully at: {BACKTEST_FILE}")
    print(f"📊 Summary Stats: Win Rate={win_rate:.2f}%, Avg Return={avg_return:+.2f}%, Wins={wins}, Losses={losses}")

if __name__ == "__main__":
    run_backtest()

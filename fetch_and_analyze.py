#!/usr/bin/env python3
"""
Twitter Ticker Stock Tracker & Analyzer
Fetches tweets, extracts stock tickers, classifies buy/sell, summarizes via Gemini,
and updates data/stock_data.json.
"""

import os
import json
import argparse
from datetime import datetime
from typing import List, Dict, Any, Optional
import requests
import tweepy
from pydantic import BaseModel, Field
from typing import Literal

# Try importing from google-genai
try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "stock_data.json")

# Define Pydantic schema for structured outputs
class StockAnalysis(BaseModel):
    ticker: str = Field(description="The stock ticker code, e.g., AAPL, TSLA, NVDA. Must be uppercase. Do not include $ symbol.")
    action: Literal["BUY", "SELL"] = Field(description="Whether the sentiment/action is to BUY (bullish/holding long) or SELL (bearish/shorting/taking profits).")
    summary: str = Field(description="A concise 1-2 sentence professional summary explaining the market context or reasons mentioned in the tweets.")
    tweets: List[str] = Field(description="List of raw tweet texts that support this ticker's sentiment and analysis.")

class DailyReport(BaseModel):
    analyses: List[StockAnalysis] = Field(description="List of analyzed stock tickers from the input tweets.")


def get_mock_tweets() -> List[str]:
    """Returns realistic mock tweets for testing and demo purposes."""
    print("ℹ️ Using realistic mock tweets for analysis...")
    return [
        "Just added to my $PLTR position. Palantir's new government contract is massive. Long PLTR for the next 3 years!",
        "Selling all my $BABA. Chinese consumer recovery is just too slow. Rotating funds to US tech. Bye Alibaba.",
        "Blackwell chip demand is insane. Spoke to a contact at TSMC - NVDA is taking all available capacity. Heavy buying on NVIDIA here.",
        "Taking profits on $NFLX today. Great stock but subscriber growth is hitting a wall in North America.",
        "Buying $TSLA leaps. Full Self Driving v12.5 is a game changer. The market is pricing Robotaxi as a car company when it's an AI giant.",
        "Shorting $COIN. Regulatory scrutiny increasing on stablecoins. Technical double top on the daily chart."
    ]


def fetch_tweets_from_x() -> List[str]:
    """Fetches tweets from the official X API or RapidAPI depending on environment keys."""
    # Read environment variables
    bearer_token = os.environ.get("X_BEARER_TOKEN")
    consumer_key = os.environ.get("X_API_KEY")
    consumer_secret = os.environ.get("X_API_SECRET")
    access_token = os.environ.get("X_ACCESS_TOKEN")
    access_token_secret = os.environ.get("X_ACCESS_TOKEN_SECRET")
    
    # Try RapidAPI Twitter Scraper first if configured (much cheaper/often free)
    rapidapi_key = os.environ.get("RAPIDAPI_KEY")
    target_username = os.environ.get("X_TARGET_USERNAME") # The user whose timeline we want to read
    
    if rapidapi_key and target_username:
        print(f"🔗 Attempting to fetch tweets via RapidAPI for user: {target_username}...")
        url = f"https://twitter-api45.p.rapidapi.com/user/tweets.php"
        headers = {
            "x-rapidapi-key": rapidapi_key,
            "x-rapidapi-host": "twitter-api45.p.rapidapi.com"
        }
        params = {"screenname": target_username}
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                tweets = []
                # Handle standard scraper structures
                timeline = data.get("timeline", [])
                for item in timeline:
                    text = item.get("text")
                    if text:
                        tweets.append(text)
                if tweets:
                    print(f"✅ Successfully fetched {len(tweets)} tweets via RapidAPI.")
                    return tweets
            print(f"⚠️ RapidAPI returned status {response.status_code}. Falling back to standard X API.")
        except Exception as e:
            print(f"⚠️ RapidAPI fetch failed: {e}. Falling back to standard X API.")

    # Try standard Tweepy Client (X API v2)
    if bearer_token:
        print("🔗 Authenticating with X API Bearer Token...")
        try:
            client = tweepy.Client(bearer_token=bearer_token)
            # Fetch own or target user tweets
            # Note: We first need the user ID. If target_username is provided, resolve it
            user_id = "me"
            if target_username:
                user = client.get_user(username=target_username)
                if user.data:
                    user_id = user.data.id
            
            # Fetch user timeline
            response = client.get_users_tweets(id=user_id, max_results=20, tweet_fields=["text"])
            if response.data:
                tweets = [tweet.text for tweet in response.data]
                print(f"✅ Successfully fetched {len(tweets)} tweets via X API.")
                return tweets
            print("⚠️ No tweets returned from X API.")
        except Exception as e:
            print(f"⚠️ X API Bearer Token fetch failed: {e}")

    # Try OAuth 1.0a User Context if credentials exist
    if consumer_key and consumer_secret and access_token and access_token_secret:
        print("🔗 Authenticating with X API OAuth 1.0a (User Context)...")
        try:
            client = tweepy.Client(
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                access_token=access_token,
                access_token_secret=access_token_secret
            )
            response = client.get_users_tweets(id="me", max_results=20, tweet_fields=["text"])
            if response.data:
                tweets = [tweet.text for tweet in response.data]
                print(f"✅ Successfully fetched {len(tweets)} tweets via X API (OAuth 1.0a).")
                return tweets
        except Exception as e:
            print(f"⚠️ X API OAuth 1.0a fetch failed: {e}")

    print("⚠️ No Twitter API credentials found or connection failed.")
    return []


def analyze_tweets_with_gemini(tweets: List[str]) -> Optional[DailyReport]:
    """Uses Google GenAI SDK with structured output to analyze tweets."""
    if not tweets:
        print("⚠️ No tweets to analyze.")
        return None

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY environment variable is not set.")
        return None

    if not GENAI_AVAILABLE:
        print("❌ Error: google-genai package is not installed correctly.")
        return None

    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    print(f"🧠 Initiating Gemini Analysis ({model_name})...")

    # Initialize SDK Client
    client = genai.Client(api_key=api_key)

    # Prepare Prompt
    tweets_formatted = "\n\n".join([f"Tweet {i+1}:\n{tweet}" for i, tweet in enumerate(tweets)])
    prompt = f"""
    You are a high-caliber stock market analyst and data processing engine.
    Analyze the following list of tweets. Perform the following steps:
    1. Scan each tweet to identify mentioned stock tickers (e.g. AAPL, TSLA, NVDA, PLTR, BABA). Ignore generic text and tags.
    2. Categorize each identified ticker into:
       - BUY: The user is buying, holding, highly bullish, or recommending long.
       - SELL: The user is selling, trimming, highly bearish, shorting, or recommending short.
       Ignore tickers that only have neutral mentions or spam.
    3. For each ticker, generate a professional, high-quality, concise 1-2 sentence summary explaining *why* it was mentioned, synthesizing the core catalyst or technical reason from all relevant tweets.
    4. Group and attach the exact raw tweet texts that mention this ticker.

    Here are the tweets to analyze:
    ---
    {tweets_formatted}
    ---
    """

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=DailyReport,
                system_instruction="You are an expert financial analyst. Always return a perfectly structured JSON following the schema, extracting tickers, actions, summaries, and tweets.",
                temperature=0.1
            )
        )
        # Parse the JSON response
        report = DailyReport.model_validate_json(response.text)
        print(f"✅ Gemini successfully analyzed and extracted {len(report.analyses)} tickers.")
        return report
    except Exception as e:
        print(f"❌ Gemini analysis failed: {e}")
        # Try to display raw text for debugging if response failed validation
        try:
            print("Raw response text was:", response.text)
        except:
            pass
        return None


def update_data_store(report: DailyReport, target_date: str) -> None:
    """Updates the JSON database, merging/overwriting the entry for the specified date."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

    # Load existing data
    data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            print(f"📂 Loaded existing database with {len(data)} daily entries.")
        except Exception as e:
            print(f"⚠️ Failed to parse existing data file: {e}. Starting fresh.")
    
    # Structure today's report
    buy_list = []
    sell_list = []

    for item in report.analyses:
        formatted_item = {
            "ticker": item.ticker.upper(),
            "summary": item.summary,
            "tweets": item.tweets
        }
        if item.action == "BUY":
            buy_list.append(formatted_item)
        elif item.action == "SELL":
            sell_list.append(formatted_item)

    # Save under the target date (overwrites if date exists, maintaining history)
    data[target_date] = {
        "buy": buy_list,
        "sell": sell_list
    }

    # Write back to file with pretty printing
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Database updated successfully for date: {target_date}!")
        print(f"📊 Buy tickers added: {[x['ticker'] for x in buy_list]}")
        print(f"📊 Sell tickers added: {[x['ticker'] for x in sell_list]}")
    except Exception as e:
        print(f"❌ Failed to write database: {e}")


def main():
    parser = argparse.ArgumentParser(description="Fetch and analyze tweets using Gemini.")
    parser.add_argument("--mock", action="store_true", help="Force run with mock tweets instead of fetching from X API.")
    parser.add_argument("--manual-text", type=str, help="Analyze raw tweets from a local text file instead of X API.")
    parser.add_argument("--date", type=str, help="Specific date for the report (YYYY-MM-DD). Defaults to today.")
    args = parser.parse_args()

    # Determine target date
    target_date = args.date if args.date else datetime.now().strftime("%Y-%m-%d")
    print(f"🕒 Target Date: {target_date}")

    tweets = []

    # Get inputs
    if args.mock:
        tweets = get_mock_tweets()
    elif args.manual_text:
        print(f"📂 Reading manual text file: {args.manual_text}...")
        if os.path.exists(args.manual_text):
            with open(args.manual_text, "r", encoding="utf-8") as f:
                # Split tweets by double newline or read lines
                content = f.read().strip()
                tweets = [t.strip() for t in content.split("\n\n") if t.strip()]
            print(f"📂 Loaded {len(tweets)} tweets from file.")
        else:
            print(f"❌ File not found: {args.manual_text}")
            return
    else:
        # Try fetching from X API
        tweets = fetch_tweets_from_x()
        if not tweets:
            print("⚠️ No tweets retrieved from API. Defaulting to mock mode so you can see results.")
            tweets = get_mock_tweets()

    # Analyze with Gemini
    report = analyze_tweets_with_gemini(tweets)

    # Save results
    if report:
        update_data_store(report, target_date)
    else:
        print("❌ Analysis aborted due to errors.")


if __name__ == "__main__":
    main()

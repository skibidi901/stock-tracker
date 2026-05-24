#!/usr/bin/env python3
"""
Twitter Ticker Stock Tracker & Analyzer
Fetches tweets from x.com/timeline (Home Timeline) for the current day (00:00 UTC to now),
extracts stock tickers, classifies buy/sell, summarizes via Gemini, and updates data/stock_data.json.
"""

import os
import json
import argparse
from datetime import datetime, timezone
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

# Define Pydantic schemas for structured outputs
class TweetSource(BaseModel):
    author: str = Field(description="The Twitter handle of the user who wrote the tweet, without the @ symbol.")
    tweet_id: str = Field(description="The unique ID of the tweet, or the mock ID provided in the prompt.")
    text: str = Field(description="The text content of the tweet.")

class StockAnalysis(BaseModel):
    ticker: str = Field(description="The stock ticker code, e.g., AAPL, TSLA, NVDA. Must be uppercase. Do not include $ symbol.")
    action: Literal["BUY", "SELL"] = Field(description="Whether the sentiment/action is to BUY (bullish/holding long) or SELL (bearish/shorting/taking profits).")
    summary: str = Field(description="A concise 1-2 sentence professional summary explaining the market context or reasons mentioned in the tweets.")
    tweets: List[TweetSource] = Field(description="List of tweet source objects that contributed to this analysis.")

class DailyReport(BaseModel):
    analyses: List[StockAnalysis] = Field(description="List of analyzed stock tickers from the input tweets.")


def get_mock_tweets() -> List[Dict[str, str]]:
    """Returns realistic mock tweets with metadata for testing and demo purposes."""
    print("ℹ️ Using realistic mock tweets for analysis...")
    return [
        {
            "id": "1882000000000000001",
            "author": "TechInvestor",
            "text": "Just added to my $PLTR position. Palantir's new government contract is massive. Long PLTR for the next 3 years!"
        },
        {
            "id": "1882000000000000002",
            "author": "MacroWhale",
            "text": "Selling all my $BABA. Chinese consumer recovery is just too slow. Rotating funds to US tech. Bye Alibaba."
        },
        {
            "id": "1882000000000000003",
            "author": "ChipBull",
            "text": "Blackwell chip demand is insane. Spoke to a contact at TSMC - NVDA is taking all available capacity. Heavy buying on NVIDIA here."
        },
        {
            "id": "1882000000000000004",
            "author": "ValueSeeker",
            "text": "Taking profits on $NFLX today. Great stock but subscriber growth is hitting a wall in North America."
        },
        {
            "id": "1882000000000000005",
            "author": "TeslaFanatic",
            "text": "Buying $TSLA leaps. Full Self Driving v12.5 is a game changer. The market is pricing Robotaxi as a car company when it's an AI giant."
        },
        {
            "id": "1882000000000000006",
            "author": "CryptoBear",
            "text": "Shorting $COIN. Regulatory scrutiny increasing on stablecoins. Technical double top on the daily chart."
        }
    ]


def fetch_tweets_from_x() -> List[Dict[str, str]]:
    """Fetches tweets from a specific Twitter List for the current day starting from 00:00 PST/PDT (or custom offset)."""
    # Read environment variables
    bearer_token = os.environ.get("X_BEARER_TOKEN")
    list_id = os.environ.get("X_LIST_ID", "1620537983349964800")
    
    # Calculate timezone offset (default to Pacific Time -7 hours for PDT)
    offset_hours = -7
    tz_env = os.environ.get("USER_TIMEZONE_OFFSET")
    if tz_env:
        try:
            offset_hours = int(tz_env)
        except ValueError:
            pass
            
    from datetime import timedelta
    user_tz = timezone(timedelta(hours=offset_hours))
    now_user = datetime.now(user_tz)
    
    # 00:00 AM today in user's local timezone (PST/PDT)
    start_time_user_dt = now_user.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Convert to UTC for X API query
    start_time_dt = start_time_user_dt.astimezone(timezone.utc)
    start_time_str = start_time_dt.isoformat().replace("+00:00", "Z")
    
    print(f"🕒 Target Twitter List ID: {list_id}")
    print(f"🕒 Timezone offset config: {offset_hours} hours.")
    print(f"🕒 Local today 00:00 AM: {start_time_user_dt.isoformat()}")
    print(f"🕒 X API UTC start_time: {start_time_str}")
    
    # Fetch from standard X API v2 Lists Endpoint
    if bearer_token:
        print("🔗 Authenticating with X API Bearer Token (Fetching List Tweets)...")
        try:
            client = tweepy.Client(bearer_token=bearer_token)
            
            print(f"📥 Pulling tweets from Twitter List ID: {list_id}...")
            # Using Paginator to handle fetching tweets until we reach the start of the day
            tweets = []
            paginator = tweepy.Paginator(
                client.get_list_tweets,
                id=list_id,
                max_results=100,
                tweet_fields=["text", "author_id", "created_at"],
                expansions=["author_id"]
            )
            
            reached_cutoff = False
            page_count = 0
            for response in paginator:
                page_count += 1
                if not response.data:
                    break
                
                users_map = {}
                if response.includes and "users" in response.includes:
                    users_map = {str(u.id): u.username for u in response.includes["users"]}
                
                for tweet in response.data:
                    # Time filter check
                    if tweet.created_at and tweet.created_at < start_time_dt:
                        reached_cutoff = True
                        continue
                        
                    author_name = users_map.get(str(tweet.author_id), "unknown")
                    tweets.append({
                        "id": str(tweet.id),
                        "author": author_name,
                        "text": tweet.text
                    })
                
                if reached_cutoff or page_count >= 5:
                    # List tweets are in reverse chronological order. Once we hit a tweet older than 
                    # start_time_dt, or we've fetched 5 pages (500 tweets) as a rate-limit safety net, stop.
                    break
            
            if tweets:
                print(f"✅ Successfully fetched {len(tweets)} today's list tweets via Bearer Token.")
                return tweets
            else:
                print("⚠️ List returned empty or no tweets today so far in this list.")
        except Exception as e:
            print(f"⚠️ X API List Tweets fetch failed: {e}")

    # RapidAPI Fallback (if they configure RapidAPI for lists)
    rapidapi_key = os.environ.get("RAPIDAPI_KEY")
    if rapidapi_key:
        print(f"🔗 Attempting to fetch List via RapidAPI...")
        url = "https://twitter-api45.p.rapidapi.com/list/tweets.php"
        headers = {
            "x-rapidapi-key": rapidapi_key,
            "x-rapidapi-host": "twitter-api45.p.rapidapi.com"
        }
        params = {"list_id": list_id}
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                tweets = []
                timeline = data.get("timeline", [])
                for item in timeline:
                    text = item.get("text")
                    tweet_id = item.get("id_str") or str(item.get("id"))
                    author = item.get("user", {}).get("screen_name") or "unknown"
                    created_at_raw = item.get("created_at")
                    
                    is_today = True
                    if created_at_raw:
                        try:
                            dt = datetime.strptime(created_at_raw, "%a %b %d %H:%M:%S %z %Y")
                            if dt < start_time_dt:
                                is_today = False
                        except Exception:
                            pass
                    
                    if text and tweet_id and is_today:
                        tweets.append({
                            "id": tweet_id,
                            "author": author,
                            "text": text
                        })
                if tweets:
                    print(f"✅ Successfully fetched {len(tweets)} today's list tweets via RapidAPI.")
                    return tweets
        except Exception as e:
            print(f"⚠️ RapidAPI List fetch failed: {e}")

    print("⚠️ No valid Bearer Token found or List connection failed.")
    return []

def analyze_tweets_with_gemini(tweets: List[Dict[str, str]]) -> Optional[DailyReport]:
    """Uses Google GenAI SDK with structured output to analyze tweets and retain author metadata."""
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

    # Format tweets as high-quality inputs including their metadata
    tweets_formatted = ""
    for i, t in enumerate(tweets):
        tweets_formatted += f"--- TWEET {i+1} ---\n"
        tweets_formatted += f"ID: {t['id']}\n"
        tweets_formatted += f"Author: {t['author']}\n"
        tweets_formatted += f"Text:\n{t['text']}\n\n"

    prompt = f"""
    You are a high-caliber stock market analyst and data processing engine.
    Analyze the following list of tweets. Perform the following steps:
    1. Scan each tweet to identify mentioned stock tickers (e.g. AAPL, TSLA, NVDA, PLTR, BABA). Ignore generic text and tags.
    2. Categorize each identified ticker into:
       - BUY: The user is buying, holding, highly bullish, or recommending long.
       - SELL: The user is selling, trimming, highly bearish, shorting, or recommending short.
       Ignore tickers that only have neutral mentions or spam.
    3. For each ticker, generate a professional, high-quality, concise 1-2 sentence summary explaining *why* it was mentioned, synthesizing the core catalyst or technical reason from all relevant tweets.
    4. Link the relevant tweets that contributed to this analysis. Populate the 'tweets' list in the output schema with the EXACT metadata (author, tweet_id, text) from the matching source tweets.

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
                system_instruction="You are an expert financial analyst. Always return a perfectly structured JSON following the schema, extracting tickers, actions, summaries, and associated tweet metadata (author, tweet_id, text).",
                temperature=0.1
            )
        )
        # Parse the JSON response
        report = DailyReport.model_validate_json(response.text)
        print(f"✅ Gemini successfully analyzed and extracted {len(report.analyses)} tickers.")
        return report
    except Exception as e:
        print(f"❌ Gemini analysis failed: {e}")
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
        # Convert Pydantic TweetSource back to dict
        formatted_tweets = []
        for tweet_src in item.tweets:
            formatted_tweets.append({
                "author": tweet_src.author,
                "tweet_id": tweet_src.tweet_id,
                "text": tweet_src.text
            })

        formatted_item = {
            "ticker": item.ticker.upper(),
            "summary": item.summary,
            "tweets": formatted_tweets
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
                content = f.read().strip()
                raw_segments = [t.strip() for t in content.split("\n\n") if t.strip()]
                
                # Format segments into structured dicts with mock metadata
                for idx, text in enumerate(raw_segments):
                    tweets.append({
                        "id": f"manual_{idx}_{datetime.now().strftime('%M%S')}",
                        "author": "ManualInput",
                        "text": text
                    })
            print(f"📂 Loaded {len(tweets)} tweets from file.")
        else:
            print(f"❌ File not found: {args.manual_text}")
            return
    else:
        # Try fetching from X API
        tweets = fetch_tweets_from_x()
        if not tweets:
            print("⚠️ No tweets retrieved from API. Exiting without updates.")
            return

    # Analyze with Gemini
    report = analyze_tweets_with_gemini(tweets)

    # Save results
    if report:
        update_data_store(report, target_date)
    else:
        print("❌ Analysis aborted due to errors.")


if __name__ == "__main__":
    main()

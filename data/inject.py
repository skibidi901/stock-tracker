import os
import json

CURRENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STOCK_DATA_FILE = os.path.join(CURRENT_DIR, "data", "stock_data.json")

def inject():
    if not os.path.exists(STOCK_DATA_FILE):
        data = {}
    else:
        with open(STOCK_DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
    # Inject mock historical data under 2026-05-20 (Wednesday)
    data["2026-05-20"] = {
        "buy": [
            {
                "ticker": "PLTR",
                "summary": "Heavy institutional buying on Palantir today after massive AI-driven government contract wins.",
                "tweets": [
                    {
                        "author": "TechInvestor",
                        "author_name": "Tech Investor",
                        "tweet_id": "1882000000000000001",
                        "text": "Just added to my $PLTR position. Palantir's new government contract is massive. Long PLTR for the next 3 years!",
                        "created_at": "2026-05-20T14:30:00Z"
                    }
                ]
            },
            {
                "ticker": "NVDA",
                "summary": "Blackwell chip demand is hitting astronomical highs. Capacity constraints at TSMC mean Nvidia gets all allocations.",
                "tweets": [
                    {
                        "author": "ChipBull",
                        "author_name": "Chip Bull",
                        "tweet_id": "1882000000000000003",
                        "text": "Blackwell chip demand is insane. Spoke to a contact at TSMC - NVDA is taking all available capacity. Heavy buying on NVIDIA here.",
                        "created_at": "2026-05-20T18:00:00Z"
                    }
                ]
            }
        ],
        "sell": [
            {
                "ticker": "BABA",
                "summary": "Chinese consumer spending is stagnant. Traders are rotating funds out of Alibaba and back to US tech.",
                "tweets": [
                    {
                        "author": "MacroWhale",
                        "author_name": "Macro Whale",
                        "tweet_id": "1882000000000000002",
                        "text": "Selling all my $BABA. Chinese consumer recovery is just too slow. Rotating funds to US tech. Bye Alibaba.",
                        "created_at": "2026-05-20T16:15:00Z"
                    }
                ]
            }
        ]
    }
    
    # Inject mock historical data under 2026-05-21 (Thursday)
    data["2026-05-21"] = {
        "buy": [
            {
                "ticker": "TSLA",
                "summary": "FSD v12.5 testing showing flawless performance. Model 3 Highland demand remains strong.",
                "tweets": [
                    {
                        "author": "TeslaFanatic",
                        "author_name": "Tesla Fanatic",
                        "tweet_id": "1882000000000000005",
                        "text": "Buying $TSLA leaps. Full Self Driving v12.5 is a game changer. The market is pricing Robotaxi as a car company when it's an AI giant.",
                        "created_at": "2026-05-21T19:30:00Z"
                    }
                ]
            }
        ],
        "sell": [
            {
                "ticker": "NFLX",
                "summary": "Subscriber growth plateauing in North America. Taking profits on Netflix today.",
                "tweets": [
                    {
                        "author": "ValueSeeker",
                        "author_name": "Value Seeker",
                        "tweet_id": "1882000000000000004",
                        "text": "Taking profits on $NFLX today. Great stock but subscriber growth is hitting a wall in North America.",
                        "created_at": "2026-05-21T15:00:00Z"
                    }
                ]
            },
            {
                "ticker": "COIN",
                "summary": "Regulatory scrutiny on stablecoins increases risk. Coin shows double top technical pattern.",
                "tweets": [
                    {
                        "author": "CryptoBear",
                        "author_name": "Crypto Bear",
                        "tweet_id": "1882000000000000006",
                        "text": "Shorting $COIN. Regulatory scrutiny increasing on stablecoins. Technical double top on the daily chart.",
                        "created_at": "2026-05-21T22:30:00Z"
                    }
                ]
            }
        ]
    }

    with open(STOCK_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("Successfully injected 2026-05-20 and 2026-05-21 historical records into stock_data.json!")

if __name__ == "__main__":
    inject()

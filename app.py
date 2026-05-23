import os
import json
import subprocess
from datetime import datetime
import streamlit as st
import pandas as pd

# Define paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(CURRENT_DIR, "data", "stock_data.json")

# Set Page Config with high-end dark title
st.set_page_config(
    page_title="Twitter Ticker Tracker",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Dark Glassmorphism CSS
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .stApp {
        background-color: #0f1115;
        color: #e2e8f0;
    }
    
    /* Title Accent */
    .title-gradient {
        background: linear-gradient(90deg, #38bdf8 0%, #34d399 50%, #f472b6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 3rem;
        margin-bottom: 0.5rem;
        letter-spacing: -0.05rem;
    }
    
    .subtitle-text {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2rem;
        font-weight: 300;
    }

    /* Modern Table Container */
    .table-container {
        margin-bottom: 3.5rem;
        border-radius: 16px;
        overflow: hidden;
        border: 1px solid #1e293b;
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(12px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }
    
    .date-header {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 16px 24px;
        font-size: 1.3rem;
        font-weight: 700;
        color: #f8fafc;
        border-bottom: 1px solid #334155;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .date-icon {
        color: #38bdf8;
    }

    /* Core Ticker Table Styling */
    .ticker-table {
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
    }
    
    .ticker-table th {
        padding: 14px 20px;
        font-weight: 600;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.05rem;
        border-bottom: 1px solid #334155;
    }
    
    .th-buy {
        background-color: rgba(16, 185, 129, 0.08);
        color: #34d399;
        text-align: left;
        border-right: 1px solid #334155;
    }
    
    .th-sell {
        background-color: rgba(239, 68, 68, 0.08);
        color: #f87171;
        text-align: left;
    }
    
    .ticker-table td {
        padding: 20px;
        vertical-align: top;
        border-bottom: 1px solid #1e293b;
    }
    
    .td-buy {
        border-right: 1px solid #334155;
        background-color: rgba(16, 185, 129, 0.01);
    }
    
    .td-sell {
        background-color: rgba(239, 68, 68, 0.01);
    }
    
    /* Cards inside Table Cells */
    .cell-card {
        padding: 16px;
        border-radius: 12px;
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid #1e293b;
        margin-bottom: 12px;
        transition: all 0.25s ease;
    }
    
    .cell-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
    }
    
    .buy-card {
        border-left: 4px solid #10b981;
    }
    
    .buy-card:hover {
        border-color: #34d399;
        box-shadow: 0 0 15px rgba(52, 211, 153, 0.15);
    }
    
    .sell-card {
        border-left: 4px solid #ef4444;
    }
    
    .sell-card:hover {
        border-color: #f87171;
        box-shadow: 0 0 15px rgba(248, 113, 113, 0.15);
    }
    
    /* Badges */
    .ticker-badge {
        display: inline-block;
        padding: 4px 10px;
        font-size: 0.85rem;
        font-weight: 800;
        border-radius: 6px;
        margin-bottom: 10px;
        letter-spacing: 0.02rem;
    }
    
    .badge-buy {
        background-color: rgba(16, 185, 129, 0.2);
        color: #34d399;
        border: 1px solid rgba(52, 211, 153, 0.3);
    }
    
    .badge-sell {
        background-color: rgba(239, 68, 68, 0.2);
        color: #f87171;
        border: 1px solid rgba(248, 113, 113, 0.3);
    }
    
    /* Summary Text */
    .summary-text {
        font-size: 0.95rem;
        line-height: 1.5;
        color: #cbd5e1;
        margin-bottom: 8px;
    }
    
    /* Empty Placeholder */
    .empty-state {
        color: #64748b;
        font-style: italic;
        font-size: 0.9rem;
        text-align: center;
        padding: 30px 10px;
    }
    
    /* Sidebar premium tweaks */
    div[data-testid="stSidebar"] {
        background-color: #0b0d11;
        border-right: 1px solid #1e293b;
    }
    
    /* Highlight Cards for stats */
    .stat-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        margin-bottom: 16px;
    }
    .stat-val {
        font-size: 1.8rem;
        font-weight: 800;
        color: #38bdf8;
    }
    .stat-lbl {
        font-size: 0.8rem;
        color: #94a3b8;
        text-transform: uppercase;
    }
</style>
"""

# Inject premium CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def load_data() -> dict:
    """Loads historical ticker analysis database."""
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.sidebar.error(f"Failed to load database: {e}")
        return {}


def render_html_table(date_str: str, date_data: dict) -> str:
    """Generates premium custom HTML layout for the Buy/Sell columns."""
    buy_items = date_data.get("buy", [])
    sell_items = date_data.get("sell", [])
    
    max_rows = max(len(buy_items), len(sell_items))
    
    # Parse date to human-readable form
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = dt.strftime("📅 %A, %B %d, %Y")
    except Exception:
        formatted_date = f"📅 {date_str}"
        
    html = f"""
    <div class="table-container">
        <div class="date-header">
            <span class="date-icon">⚡</span> {formatted_date}
        </div>
        <table class="ticker-table">
            <thead>
                <tr>
                    <th class="th-buy">📈 Buy (买入)</th>
                    <th class="th-sell">📉 Sell (卖出)</th>
                </tr>
            </thead>
            <tbody>
    """
    
    if max_rows == 0:
        html += """
                <tr>
                    <td class="td-buy"><div class="empty-state">No buy signals captured for this date.</div></td>
                    <td class="td-sell"><div class="empty-state">No sell signals captured for this date.</div></td>
                </tr>
        """
    else:
        for i in range(max_rows):
            html += "<tr>"
            
            # Buy Cell
            html += '<td class="td-buy">'
            if i < len(buy_items):
                item = buy_items[i]
                html += f"""
                <div class="cell-card buy-card">
                    <span class="ticker-badge badge-buy">${item['ticker']}</span>
                    <div class="summary-text">{item['summary']}</div>
                </div>
                """
            else:
                if i == 0:
                    html += '<div class="empty-state">No buy signals captured.</div>'
            html += "</td>"
            
            # Sell Cell
            html += '<td class="td-sell">'
            if i < len(sell_items):
                item = sell_items[i]
                html += f"""
                <div class="cell-card sell-card">
                    <span class="ticker-badge badge-sell">${item['ticker']}</span>
                    <div class="summary-text">{item['summary']}</div>
                </div>
                """
            else:
                if i == 0:
                    html += '<div class="empty-state">No sell signals captured.</div>'
            html += "</td>"
            
            html += "</tr>"
            
    html += """
            </tbody>
        </table>
    </div>
    """
    return html


def calculate_statistics(data: dict) -> dict:
    """Computes global metrics for stats panel."""
    total_dates = len(data)
    all_buys = []
    all_sells = []
    
    for date_key, date_data in data.items():
        for b in date_data.get("buy", []):
            all_buys.append(b["ticker"])
        for s in date_data.get("sell", []):
            all_sells.append(s["ticker"])
            
    total_buys = len(all_buys)
    total_sells = len(all_sells)
    
    # Calculate top ticker
    all_tickers = all_buys + all_sells
    top_ticker = "N/A"
    if all_tickers:
        top_ticker = max(set(all_tickers), key=all_tickers.count)
        
    return {
        "total_days": total_dates,
        "total_buys": total_buys,
        "total_sells": total_sells,
        "top_ticker": top_ticker
    }


def run_pipeline(args_list: list) -> tuple:
    """Helper to run the scraper backend in a subprocess."""
    script_path = os.path.join(CURRENT_DIR, "fetch_and_analyze.py")
    cmd = ["python", script_path] + args_list
    
    try:
        # Run and capture output
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return True, res.stdout
    except subprocess.CalledProcessError as e:
        return False, f"Error: {e.stderr}\nStdout: {e.stdout}"
    except Exception as e:
        return False, str(e)


# ==========================================
# MAIN APP BODY
# ==========================================

# Sidebar
st.sidebar.markdown("<h2 style='text-align: center; color: #38bdf8;'>🔧 Dashboard Admin</h2>", unsafe_allow_html=True)

# App Data Loading
data = load_data()
stats = calculate_statistics(data)

# Stats Displays
st.sidebar.markdown("---")
st.sidebar.subheader("📈 Quick Statistics")
stat_cols = st.sidebar.columns(2)
with stat_cols[0]:
    st.markdown(f'<div class="stat-card"><div class="stat-val">{stats["total_buys"]}</div><div class="stat-lbl">Total Buys</div></div>', unsafe_allow_html=True)
with stat_cols[1]:
    st.markdown(f'<div class="stat-card"><div class="stat-val">{stats["total_sells"]}</div><div class="stat-lbl">Total Sells</div></div>', unsafe_allow_html=True)

st.markdown(f'<div class="stat-card" style="margin-top: 10px;"><div class="stat-val" style="color: #34d399;">${stats["top_ticker"]}</div><div class="stat-lbl">Most Active Ticker</div></div>', unsafe_allow_html=True)

# Admin Console for AI Extraction (Instant Run)
st.sidebar.markdown("---")
st.sidebar.subheader("🤖 Trigger Gemini Extraction")
run_mode = st.sidebar.radio("Run Mode", ["Demo Data Mode", "Manual Input Mode", "X API Live Fetch"])

# Environment state checker
gemini_key_set = "GEMINI_API_KEY" in os.environ

if not gemini_key_set:
    st.sidebar.warning("⚠️ GEMINI_API_KEY environment variable is missing. Live AI triggers will fail. Set it in your environment or secrets.")

# Inputs based on run mode
if run_mode == "Demo Data Mode":
    st.sidebar.info("Generates mock financial tweets and runs them through Gemini API.")
    selected_date = st.sidebar.date_input("Target Date for Data", datetime.today())
    
    if st.sidebar.button("⚡ Run Demo Simulation", type="primary"):
        with st.spinner("AI is analyzing tweets..."):
            success, log = run_pipeline(["--mock", "--date", selected_date.strftime("%Y-%m-%d")])
            if success:
                st.sidebar.success("Simulation Complete! Refreshing...")
                st.rerun()
            else:
                st.sidebar.error("Execution failed.")
                st.sidebar.code(log)

elif run_mode == "Manual Input Mode":
    st.sidebar.info("Paste custom tweets or articles below. Gemini will instantly categorize tickers, buy/sell, and write them to database.")
    manual_tweets = st.sidebar.text_area("Paste Tweets here (separate multiple tweets with 2 blank lines)", 
        placeholder="AAPL is breaking out to all-time highs on high volume. Long AAPL.\n\nTrimmed my NVDA today, feels overbought in the short term.")
    selected_date = st.sidebar.date_input("Target Date for Analysis", datetime.today())
    
    if st.sidebar.button("⚡ Run AI Analysis", type="primary"):
        if not manual_tweets.strip():
            st.sidebar.error("Please enter some text first.")
        else:
            with st.spinner("AI parsing text..."):
                # Save input to a temporary text file
                temp_file = os.path.join(CURRENT_DIR, "data", "temp_tweets.txt")
                os.makedirs(os.path.dirname(temp_file), exist_ok=True)
                with open(temp_file, "w", encoding="utf-8") as f:
                    f.write(manual_tweets)
                
                success, log = run_pipeline(["--manual-text", temp_file, "--date", selected_date.strftime("%Y-%m-%d")])
                
                # Cleanup
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    
                if success:
                    st.sidebar.success("Success! Database Updated.")
                    st.rerun()
                else:
                    st.sidebar.error("AI Analysis failed.")
                    st.sidebar.code(log)

elif run_mode == "X API Live Fetch":
    st.sidebar.info("Calls standard X API or RapidAPI to fetch target timeline and run analysis.")
    target_user = st.sidebar.text_input("Target Twitter Username", placeholder="e.g. ElonMusk")
    selected_date = st.sidebar.date_input("Target Date", datetime.today())
    
    if st.sidebar.button("⚡ Fetch & Analyze", type="primary"):
        with st.spinner("Fetching X timeline & running Gemini..."):
            env_args = ["--date", selected_date.strftime("%Y-%m-%d")]
            if target_user:
                os.environ["X_TARGET_USERNAME"] = target_user
            
            success, log = run_pipeline(env_args)
            if success:
                st.sidebar.success("API Pull Complete!")
                st.rerun()
            else:
                st.sidebar.error("API Call/Analysis failed.")
                st.sidebar.code(log)


# Main Content Area
st.markdown('<div class="title-gradient">Twitter Stock Ticker Tracker</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-text">Synthesizing and classifying stock market signals from your Twitter timeline in real-time with Gemini 1.5/2.5 Flash</div>', unsafe_allow_html=True)

# Search & Filters
search_col, sort_col = st.columns([3, 1])

# Sorting dates
sorted_dates = sorted(list(data.keys()), reverse=True)

with search_col:
    search_query = st.text_input("🔍 Search stock ticker (e.g. AAPL, TSLA)", "").upper().strip()
    
with sort_col:
    date_filter = st.selectbox("📅 Filter by date", ["Show All Dates"] + sorted_dates)

# Filter data based on search and selected date
filtered_dates = sorted_dates
if date_filter != "Show All Dates":
    filtered_dates = [date_filter]

# Render Dashboard Tables
rendered_count = 0
for date_key in filtered_dates:
    date_data = data[date_key]
    
    # If search query is active, filter entries in buy/sell
    if search_query:
        buy_filtered = [b for b in date_data.get("buy", []) if search_query in b["ticker"]]
        sell_filtered = [s for s in date_data.get("sell", []) if search_query in s["ticker"]]
        
        # Skip rendering this date if nothing matches search
        if not buy_filtered and not sell_filtered:
            continue
            
        # Create temp record for rendering
        render_data = {
            "buy": buy_filtered,
            "sell": sell_filtered
        }
    else:
        render_data = date_data
        
    # Render table
    st.markdown(render_html_table(date_key, render_data), unsafe_allow_html=True)
    rendered_count += 1

if rendered_count == 0:
    st.info("💡 No matching tickers found in the database. Try searching for another ticker or add some data in the sidebar Admin Panel!")

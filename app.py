import os
import json
from datetime import datetime
import streamlit as st
import pandas as pd

# Define paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(CURRENT_DIR, "data", "stock_data.json")

# Set Page Config with high-end dark title
st.set_page_config(
    page_title="CL's Tickers",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed" # Starts with sidebar collapsed (clean dashboard)
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
        background-color: #f1f5f9; /* Premium light grey background */
        color: #1e293b; /* Deep slate gray for primary readability */
    }
    
    /* Explicit high-visibility black styling for Streamlit widget labels */
    label[data-baseweb="label"], div[data-testid="stWidgetLabel"] p {
        color: #000000 !important; /* Pure black */
        font-weight: 600 !important;
        font-size: 0.98rem !important;
        letter-spacing: 0.01rem;
    }
    
    /* Search Bar and Dropdown Backgrounds forced to Solid White */
    .stTextInput input {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }
    
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
    }

    /* Target nested containers to override default Streamlit themes */
    div[data-baseweb="input"] {
        background-color: #ffffff !important;
        border-radius: 8px !important;
    }
    
    /* Header layout styling */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        margin-bottom: 2rem;
    }
    
    /* Rich Light-Theme Title Accent */
    .title-gradient {
        background: linear-gradient(90deg, #0284c7 0%, #059669 50%, #db2777 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 2.8rem;
        margin-bottom: 0.3rem;
        letter-spacing: -0.05rem;
    }
    
    .subtitle-text {
        color: #475569;
        font-size: 1.05rem;
        font-weight: 300;
        margin-bottom: 0;
    }

    /* Modern Table Container (Light Mode) with scrollable height */
    .table-container {
        margin-bottom: 0rem;
        border-radius: 0 0 16px 16px;
        overflow-y: auto; /* Vertically scrollable */
        max-height: 480px; /* Fixed height to control page length */
        position: relative;
    }

    /* Core Ticker Table Styling */
    .ticker-table {
        width: 100%;
        border-collapse: collapse;
        table-layout: fixed;
    }
    
    /* Make table headers sticky when scrolling */
    .ticker-table th {
        position: sticky;
        top: 0;
        z-index: 10;
        padding: 14px 20px;
        font-weight: 600;
        font-size: 0.95rem;
        text-transform: uppercase;
        letter-spacing: 0.05rem;
        border-bottom: 1px solid #cbd5e1;
        box-shadow: 0 2px 5px rgba(0, 0, 0, 0.02);
    }
    
    .th-buy {
        background-color: rgba(16, 185, 129, 0.08);
        color: #047857; /* Deep readable emerald green */
        text-align: left;
        border-right: 1px solid #cbd5e1;
    }
    
    .th-sell {
        background-color: rgba(239, 68, 68, 0.08);
        color: #b91c1c; /* Deep readable dark red */
        text-align: left;
    }
    
    .ticker-table td {
        padding: 20px;
        vertical-align: top;
        border-bottom: 1px solid #cbd5e1;
    }
    
    .td-buy {
        border-right: 1px solid #cbd5e1;
        background-color: rgba(16, 185, 129, 0.01);
    }
    
    .td-sell {
        background-color: rgba(239, 68, 68, 0.01);
    }
    
    /* White Card Blocks inside Grid Cells */
    .cell-card {
        padding: 16px;
        border-radius: 12px;
        background: #ffffff; /* Crisp white card */
        border: 1px solid #cbd5e1;
        margin-bottom: 12px;
        transition: all 0.25s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.01);
    }
    
    .cell-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
    }
    
    .buy-card {
        border-left: 4px solid #10b981;
    }
    
    .buy-card:hover {
        border-color: #059669;
        box-shadow: 0 0 15px rgba(5, 150, 105, 0.08);
    }
    
    .sell-card {
        border-left: 4px solid #ef4444;
    }
    
    .sell-card:hover {
        border-color: #dc2626;
        box-shadow: 0 0 15px rgba(220, 38, 38, 0.08);
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
        background-color: rgba(16, 185, 129, 0.12);
        color: #047857;
        border: 1px solid rgba(16, 185, 129, 0.25);
    }
    
    .badge-sell {
        background-color: rgba(239, 68, 68, 0.12);
        color: #b91c1c;
        border: 1px solid rgba(239, 68, 68, 0.25);
    }
    
    /* Summary Text */
    .summary-text {
        font-size: 0.98rem;
        line-height: 1.55;
        color: #334155; /* Sharp dark grey text */
        margin-bottom: 8px;
    }
    
    /* Tweet Source Mentions Section */
    .author-section {
        margin-top: 12px;
        font-size: 0.85rem;
        color: #64748b; /* Soft grey text */
        border-top: 1px dashed #e2e8f0;
        padding-top: 8px;
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 6px;
    }
    
    .author-link {
        color: #0284c7; /* Classic blue link */
        text-decoration: none;
        font-weight: 600;
        transition: color 0.2s ease;
    }
    
    .author-link:hover {
        color: #059669;
        text-decoration: underline;
    }
    
    /* Empty Placeholder with enhanced contrast */
    .empty-state {
        color: #64748b; /* Slate grey for readability */
        font-style: italic;
        font-size: 0.95rem;
        text-align: center;
        padding: 30px 10px;
    }
    
    /* Stats Layout for Header */
    .stats-header-container {
        display: flex;
        gap: 12px;
    }
    
    .stat-card-small {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 10px 18px;
        text-align: center;
        min-width: 105px;
    }
    
    .stat-val-small {
        font-size: 1.4rem;
        font-weight: 800;
        color: #38bdf8;
        line-height: 1.1;
    }
    
    .stat-lbl-small {
        font-size: 0.72rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.02rem;
    }

    /* Streamlit Alert Glassmorphism Custom Overrides (Light Mode) */
    div[data-testid="stAlert"] {
        background-color: rgba(14, 165, 233, 0.08) !important;
        border: 1px solid rgba(14, 165, 233, 0.2) !important;
        color: #0369a1 !important;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.01);
    }
    div[data-testid="stAlert"] p {
        color: #0369a1 !important;
        font-weight: 500;
        font-size: 0.95rem;
    }

    /* Expander styling to match premium date-header layout and fold/unfold */
    div[data-testid="stExpander"] {
        border: 1px solid #cbd5e1 !important;
        border-radius: 16px !important;
        background: rgba(255, 255, 255, 0.75) !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04) !important;
        margin-bottom: 2rem !important;
        overflow: hidden !important;
    }
    
    div[data-testid="stExpander"] details summary {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%) !important;
        padding: 16px 24px !important;
        font-size: 1.25rem !important;
        font-weight: 700 !important;
        color: #000000 !important;
        border-bottom: 1px solid #cbd5e1 !important;
    }
    
    div[data-testid="stExpander"] details summary:hover {
        background: linear-gradient(135deg, #f1f5f9 0%, #cbd5e1 100%) !important;
    }
    
    div[data-testid="stExpander"] details[open] summary {
        border-bottom: 1px solid #cbd5e1 !important;
    }
    
    /* Remove default inner margins for smooth grid */
    div[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
        padding: 0 !important;
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
        st.error(f"Failed to load database: {e}")
        return {}


def render_html_table(date_data: dict) -> str:
    """Generates premium custom HTML layout for the Buy/Sell columns with author links."""
    buy_items = date_data.get("buy", [])
    sell_items = date_data.get("sell", [])
    
    max_rows = max(len(buy_items), len(sell_items))
        
    html = f"""
    <div class="table-container">
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
                
                # Format authors mentions
                mentions = []
                for tweet_src in item.get("tweets", []):
                    author = tweet_src.get("author", "unknown")
                    tid = tweet_src.get("tweet_id")
                    
                    # Generate real Twitter link if ID is valid
                    if tid and not str(tid).startswith("manual_"):
                        link = f"https://x.com/{author}/status/{tid}"
                    else:
                        link = f"https://x.com/{author}"
                        
                    mentions.append(f'<a href="{link}" target="_blank" class="author-link">@{author}</a>')
                mentions_html = ", ".join(mentions) if mentions else "Unknown"
                
                html += f"""
                <div class="cell-card buy-card">
                    <span class="ticker-badge badge-buy">${item['ticker']}</span>
                    <div class="summary-text">{item['summary']}</div>
                    <div class="author-section">
                        <span>🗣️ Mentions:</span> {mentions_html}
                    </div>
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
                
                # Format authors mentions
                mentions = []
                for tweet_src in item.get("tweets", []):
                    author = tweet_src.get("author", "unknown")
                    tid = tweet_src.get("tweet_id")
                    
                    if tid and not str(tid).startswith("manual_"):
                        link = f"https://x.com/{author}/status/{tid}"
                    else:
                        link = f"https://x.com/{author}"
                        
                    mentions.append(f'<a href="{link}" target="_blank" class="author-link">@{author}</a>')
                mentions_html = ", ".join(mentions) if mentions else "Unknown"
                
                html += f"""
                <div class="cell-card sell-card">
                    <span class="ticker-badge badge-sell">${item['ticker']}</span>
                    <div class="summary-text">{item['summary']}</div>
                    <div class="author-section">
                        <span>🗣️ Mentions:</span> {mentions_html}
                    </div>
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
    all_buys = []
    all_sells = []
    
    for date_key, date_data in data.items():
        for b in date_data.get("buy", []):
            all_buys.append(b["ticker"])
        for s in date_data.get("sell", []):
            all_sells.append(s["ticker"])
            
    return {
        "total_buys": len(all_buys),
        "total_sells": len(all_sells)
    }


# ==========================================
# MAIN APP BODY
# ==========================================

# App Data Loading
data = load_data()
stats = calculate_statistics(data)

# Header Row
st.markdown('<div class="title-gradient">CL\'s Tickers</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

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
        
    # Parse date to human-readable form for the expander label
    try:
        dt = datetime.strptime(date_key, "%Y-%m-%d")
        formatted_date = dt.strftime("⚡ %A, %B %d, %Y")
    except Exception:
        formatted_date = f"⚡ {date_key}"
        
    # Keep only the very first visible row expanded by default, fold others
    is_expanded = (rendered_count == 0)
    with st.expander(formatted_date, expanded=is_expanded):
        st.markdown(render_html_table(render_data), unsafe_allow_html=True)
        
    rendered_count += 1

if rendered_count == 0:
    st.info("💡 No matching tickers found in the database. When you post new analyses on Twitter, they will automatically appear here after the daily cycle!")

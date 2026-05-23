# 📈 Twitter Stock Ticker Tracker & Analyzer

An automated, serverless system to monitor a Twitter (X) timeline, extract stock tickers using **Gemini**, classify them into buy/sell categories, generate daily market summaries, and display them on a premium interactive Streamlit dashboard.

---

## ✨ Features

- **⚡ Serverless Architecture**: 100% free to run using GitHub Actions (cron job) and Streamlit Community Cloud.
- **🧠 Gemini-Powered Analysis**: Utilizes `google-genai` and **Structured JSON Outputs** to extract tickers and write professional market summaries.
- **💅 Premium Modern Dark Theme**: Responsive glassmorphism interface featuring emerald and crimson visual highlights.
- **🔧 Multi-Mode Scraper**:
  - **Demo Mode**: Built-in realistic historical financial data for instant out-of-the-box operation.
  - **Live Scraper**: Plugs into official X API or budget-friendly third-party Twitter APIs (RapidAPI).
  - **Manual Admin Console**: Allows you to directly paste texts to immediately invoke Gemini and save results without setting up APIs.

---

## 🛠️ Local Development & Setup

### 1. Installation

First, clone or copy the project files to your local machine. Navigate into the directory and install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Set Up Environment Variables

Create your Google AI Studio API key at [Google AI Studio](https://aistudio.google.com/). Set the variable in your terminal:

**On macOS/Linux:**
```bash
export GEMINI_API_KEY="your-gemini-api-key"
```

**On Windows (Command Prompt):**
```cmd
set GEMINI_API_KEY=your-gemini-api-key
```

### 3. Run the Dashboard Locally

Launch the Streamlit server:

```bash
streamlit run app.py
```
This opens the dashboard inside your browser at `http://localhost:8501`.

### 4. Trigger Scraper Manually

To run the Twitter fetcher and AI processor locally:

*   **Run Mock/Demo Mode (recommended for testing AI pipeline):**
    ```bash
    python fetch_and_analyze.py --mock
    ```
*   **Run Manual Input Mode (specify custom date):**
    You can directly use the sidebar panel in the Streamlit UI to write/paste tweets!

---

## 🤖 Automating with GitHub Actions & Streamlit Cloud

To host this for free and have it update automatically every day:

### Step 1: Create a GitHub Repository
1. Initialize git in this directory and push it to a new **Private or Public** repository on your GitHub account.

### Step 2: Configure Repository Secrets & Permissions
1. On GitHub, navigate to your repository **Settings** -> **Secrets and variables** -> **Actions** -> **New repository secret**.
2. Create the following secrets:
   - `GEMINI_API_KEY`: **[Required]** Your Google AI Studio API key.
   - `X_BEARER_TOKEN` or `RAPIDAPI_KEY` + `X_TARGET_USERNAME`: *[Optional]* To scrape live Twitter feeds automatically.
3. **CRITICAL STEP (Enable Commit Permission):**
   - Go to your repository **Settings** -> **Actions** -> **General**.
   - Scroll down to **Workflow permissions**.
   - Select **"Read and write permissions"** and click **Save**.
   *(This allows the GitHub Action runner to commit and push the updated `stock_data.json` back to your codebase).*

### Step 3: Deploy Frontend to Streamlit Community Cloud
1. Go to [Streamlit Community Cloud](https://streamlit.io/cloud) and sign up/sign in with your GitHub account.
2. Click **New app**.
3. Select your repository, branch (`main`), and set the Main file path to `app.py`.
4. Click **Advanced settings...** and add your `GEMINI_API_KEY="your-key-here"` under **Secrets** so the manual analysis works online too.
5. Click **Deploy!**

Now, your site is live! Every day at midnight, GitHub Actions will scrape Twitter, call Gemini, update the JSON file, and Streamlit Cloud will instantly refresh the page with the newest market intelligence.

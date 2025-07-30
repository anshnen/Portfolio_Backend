# frontend_app.py

import streamlit as st
import requests
import pandas as pd
import altair as alt
from datetime import datetime, timedelta

# --- Configuration & Styling ---
API_BASE_URL = "http://127.0.0.1:5000/api/v1"
PORTFOLIO_ID = 1

st.set_page_config(layout="wide", page_title="PortfolioPro")

# Custom CSS for a clean, Google-inspired dark theme
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Lato:wght@400;700&display=swap');

    /* General Styling */
    html, body, [class*="st-"], [class*="css-"] {
        font-family: 'Lato', sans-serif;
    }
    .stApp {
        background-color: #0E1117; /* Streamlit's default dark background */
        color: #FAFAFA;
    }
    /* Card-like containers for metrics */
    .metric-card {
        background-color: #161B22; /* Slightly lighter dark shade */
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 25px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    /* Text colors for high contrast on dark background */
    .metric-card [data-testid="stMetricLabel"] {
        color: #A0A0A0 !important; /* Lighter grey for labels */
    }
    .metric-card [data-testid="stMetricValue"] {
        color: #FAFAFA !important; /* White for values */
        font-size: 2.1rem;
    }
    .metric-card [data-testid="stMetricDelta"] {
        color: #2ECC71 !important; /* Bright green for positive */
    }
    .metric-card [data-testid="stMetricDelta"] svg {
        fill: #2ECC71 !important;
    }
    .metric-card .st-bf, .metric-card .st-e8 { /* Catches the red (negative) delta */
        color: #FF4B4B !important;
    }
    .metric-card .st-bf svg, .metric-card .st-e8 svg {
        fill: #FF4B4B !important;
    }

    /* Custom headers */
    h1, h2, h3 {
        font-family: 'Lato', sans-serif;
        font-weight: 700;
        color: #FAFAFA;
    }
    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0E1117;
        border-right: 1px solid #30363d;
    }
    [data-testid="stSidebar"] h2 {
        font-size: 1.75rem;
    }
</style>
""", unsafe_allow_html=True)


# --- API Client Functions ---
@st.cache_data(ttl=60)
def get_api_data(endpoint: str):
    """Generic function to fetch data from an API endpoint."""
    try:
        response = requests.get(f"{API_BASE_URL}/{endpoint}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: Could not connect to the backend. Is the server running? Details: {e}")
        return None

def post_api_data(endpoint: str, data: dict):
    """Generic function to post data to an API endpoint."""
    try:
        response = requests.post(f"{API_BASE_URL}/{endpoint}", json=data)
        response.raise_for_status()
        st.cache_data.clear()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_msg = e.response.json().get('error', 'An unknown error occurred') if e.response else str(e)
        st.error(f"Request Failed: {error_msg}")
        return None

def delete_api_data(endpoint: str):
    """Generic function to delete data via an API endpoint."""
    try:
        response = requests.delete(f"{API_BASE_URL}/{endpoint}")
        response.raise_for_status()
        st.cache_data.clear()
        return True
    except requests.exceptions.RequestException as e:
        error_msg = e.response.json().get('error', 'An unknown error occurred') if e.response else str(e)
        st.error(f"Delete Failed: {error_msg}")
        return None

# --- UI Page Rendering Functions ---

def render_dashboard():
    st.title("📈 Dashboard")
    st.markdown("---")

    summary_data = get_api_data(f"portfolio/{PORTFOLIO_ID}/summary")
    if not summary_data:
        return

    net_worth = summary_data.get('net_worth', 0)
    change_amount = summary_data.get('todays_change_amount', 0)
    cash_flow = summary_data.get('cash_flow', {})
    income = cash_flow.get('income', 0)
    spending = cash_flow.get('spending', 0)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f'<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Net Worth", f"${net_worth:,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card">', unsafe_allow_html=True)
        st.metric("Today's Change", f"${change_amount:,.2f}", f"{summary_data.get('todays_change_percent', 0):.2f}%")
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card">', unsafe_allow_html=True)
        st.metric("30-Day Net Cash Flow", f"${income - spending:,.2f}")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)

    # Charts
    chart_col, donut_col = st.columns([2, 1])
    with chart_col:
        st.subheader("Portfolio Performance")
        chart_data = pd.DataFrame({
            'Date': pd.to_datetime([datetime.now() - timedelta(days=i) for i in range(30)][::-1]),
            'Value': [net_worth - (change_amount * (i*0.5)) for i in range(30)][::-1]
        })
        chart = alt.Chart(chart_data).mark_area(
            line={'color':'#1E90FF'},
            color=alt.Gradient(
                gradient='linear',
                stops=[alt.GradientStop(color='#0E1117', offset=0), alt.GradientStop(color='#1E90FF', offset=1)],
                x1=1, x2=1, y1=1, y2=0
            )
        ).encode(x='Date:T', y=alt.Y('Value:Q', title='Portfolio Value ($)'), tooltip=['Date', 'Value']).properties(height=350)
        st.altair_chart(chart, use_container_width=True)

    with donut_col:
        st.subheader("Cash Flow Breakdown")
        if income > 0 or spending > 0:
            cash_flow_df = pd.DataFrame([{"Category": "Income", "Amount": income}, {"Category": "Spending", "Amount": spending}])
            donut_chart = alt.Chart(cash_flow_df).mark_arc(innerRadius=60).encode(
                theta=alt.Theta(field="Amount", type="quantitative"),
                color=alt.Color(field="Category", type="nominal", scale=alt.Scale(domain=['Income', 'Spending'], range=['#2ECC71', '#FF4B4B'])),
                tooltip=['Category', 'Amount']
            ).properties(height=350)
            st.altair_chart(donut_chart, use_container_width=True)
        else:
            st.info("No income or spending data for the last 30 days.")

def render_accounts_page():
    st.title("💰 Accounts & Holdings")
    st.markdown("---")
    summary_data = get_api_data(f"portfolio/{PORTFOLIO_ID}/summary")
    if not summary_data or 'accounts' not in summary_data:
        st.warning("Could not load account data.")
        return
    
    accounts_df = pd.DataFrame(summary_data['accounts'])
    accounts_df.rename(columns={'name': 'Account Name', 'institution': 'Institution', 'account_type': 'Type', 'balance': 'Value ($)'}, inplace=True)
    st.dataframe(accounts_df[['Account Name', 'Institution', 'Type', 'Value ($)']], use_container_width=True, hide_index=True,
                 column_config={"Value ($)": st.column_config.NumberColumn(format="$ %.2f")})

def render_watchlists_page():
    st.title("⭐ Watchlists")
    st.markdown("---")
    watchlists_data = get_api_data(f"watchlists/{PORTFOLIO_ID}")
    if not watchlists_data:
        st.info("No watchlists found. You can create one from the sidebar.")
        return

    for wl in watchlists_data:
        with st.expander(f"**{wl['name']}** ({len(wl['items'])} items)", expanded=True):
            if wl['items']:
                items_df = pd.DataFrame(wl['items'])
                items_df['Remove'] = False
                edited_df = st.data_editor(items_df, column_config={"asset_id": None, "ticker_symbol": "Ticker", "name": "Company Name", "last_price": st.column_config.NumberColumn("Last Price ($)", format="$ %.2f"), "Remove": st.column_config.CheckboxColumn(required=True)}, use_container_width=True, hide_index=True, key=f"editor_{wl['id']}")
                
                item_to_remove = edited_df[edited_df["Remove"] == True]
                if not item_to_remove.empty:
                    asset_id, ticker = item_to_remove.iloc[0]['asset_id'], item_to_remove.iloc[0]['ticker_symbol']
                    if st.button(f"Confirm Removal of {ticker}", key=f"del_{wl['id']}_{asset_id}"):
                        if delete_api_data(f"watchlists/{wl['id']}/items/{asset_id}"):
                            st.success(f"Removed {ticker} from {wl['name']}.")
                            st.rerun()
            else:
                st.write("This watchlist is empty. Add stocks from the sidebar.")

# --- Action Dialogs ---
def transaction_dialog():
    @st.dialog("Log a New Transaction")
    def _dialog():
        accounts = get_api_data("portfolio/accounts")
        if not accounts:
            st.warning("Could not load accounts. Please try again.")
            return

        with st.form("transaction_form"):
            account_options = {f"{acc['name']} ({acc['institution']})": acc['id'] for acc in accounts}
            selected_account = st.selectbox("Account", options=account_options.keys())
            ttype = st.selectbox("Type", ["DEPOSIT", "WITHDRAWAL", "BUY", "SELL", "DIVIDEND", "INTEREST", "FEE"])
            amount = st.number_input("Total Amount ($)", help="Use negative for withdrawals, buys, fees.")
            date = st.date_input("Date", value=datetime.now())
            desc = st.text_area("Description")
            st.markdown("*For BUY/SELL only:*")
            ticker = st.text_input("Asset Ticker").upper()
            qty = st.number_input("Quantity", value=0.0, format="%.4f")
            price = st.number_input("Price Per Unit ($)", value=0.0, format="%.4f")

            submitted = st.form_submit_button("Submit Transaction", use_container_width=True, type="primary")
            if submitted:
                data = {"account_id": account_options[selected_account], "transaction_type": ttype, "total_amount": amount, "transaction_date": date.strftime('%Y-%m-%d'), "asset_ticker": ticker or None, "quantity": qty or None, "price_per_unit": price or None, "description": desc}
                if post_api_data("transactions", data):
                    st.success("Transaction added!")
                    st.rerun()
    _dialog()

def watchlist_dialog():
    @st.dialog("Manage Watchlists")
    def _dialog():
        with st.form("watchlist_form"):
            st.subheader("Create New Watchlist")
            wl_name = st.text_input("New Watchlist Name")
            if st.form_submit_button("Create", use_container_width=True, type="primary"):
                if wl_name and post_api_data("watchlists", {"name": wl_name, "portfolio_id": PORTFOLIO_ID}):
                    st.success(f"Watchlist '{wl_name}' created!")
                    st.rerun()
            
            st.markdown("---")
            st.subheader("Add Stock to Watchlist")
            watchlists = get_api_data(f"watchlists/{PORTFOLIO_ID}")
            if watchlists:
                wl_options = {wl['name']: wl['id'] for wl in watchlists}
                sel_wl = st.selectbox("Select Watchlist", options=wl_options.keys())
                ticker_add = st.text_input("Stock Ticker").upper()
                if st.form_submit_button("Add Stock", use_container_width=True, type="primary"):
                    if ticker_add and post_api_data(f"watchlists/{wl_options[sel_wl]}/items", {"ticker": ticker_add}):
                        st.success(f"Added {ticker_add} to '{sel_wl}'.")
                        st.rerun()
    _dialog()

# --- Main App Execution ---
def main():
    with st.sidebar:
        st.markdown("## PortfolioPro")
        
        # Use session state for navigation
        if 'page' not in st.session_state:
            st.session_state.page = "Dashboard"

        def set_page(page_name):
            st.session_state.page = page_name

        st.button("Dashboard", on_click=set_page, args=("Dashboard",), use_container_width=True)
        st.button("Accounts", on_click=set_page, args=("Accounts",), use_container_width=True)
        st.button("Watchlists", on_click=set_page, args=("Watchlists",), use_container_width=True)
        
        st.markdown("---")
        st.header("Actions")

        if st.button("🔄 Refresh Market Data", use_container_width=True):
            if post_api_data("market-data/refresh", {}):
                st.success("Market data refresh triggered!")
                st.rerun()
        
        if st.button("✍️ Add New Transaction", use_container_width=True):
            transaction_dialog()
            
        if st.button("⭐ Manage Watchlists", use_container_width=True):
            watchlist_dialog()

    # Render the main page content based on session state
    if st.session_state.page == "Dashboard":
        render_dashboard()
    elif st.session_state.page == "Accounts":
        render_accounts_page()
    elif st.session_state.page == "Watchlists":
        render_watchlists_page()

if __name__ == "__main__":
    main()
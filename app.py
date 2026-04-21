import streamlit as st
import pandas as pd
from database import init_db, get_supabase
from components import render_forge, render_compounder
from architect import render_architect_tab
from analytics import render_analytics
from journal import render_journal_tab
from dca import render_dca_tab

# --- 1. INITIALIZE CLOUD CONNECTION ---
init_db()
supabase = get_supabase()

# --- 2. GLOBAL PAGE CONFIG ---
st.set_page_config(
    page_title="ICT_MASTER_TERMINAL_V9.0",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Institutional Styling Injection
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #111;
        border-radius: 4px 4px 0px 0px;
        gap: 1px;
        padding-top: 10px;
    }
    .stTabs [aria-selected="true"] { background-color: #FF4B4B !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

# --- 3. THE CLOUD AUTHENTICATION ---
if 'auth' not in st.session_state:
    st.session_state.auth = False
    st.session_state.user = None

if not st.session_state.auth:
    st.title("🔐 TERMINAL_ACCESS_REQUIRED")
    st.write("Institutional Trading Vault v9.0 | Multi-User Cloud Infrastructure")
    
    with st.form("login_form"):
        u_input = st.text_input("USERNAME").upper().strip()
        p_input = st.text_input("PASSWORD", type="password")
        submit = st.form_submit_button("ENTER VAULT")
        
        if submit:
            user_query = supabase.table("users").select("*").eq("username", u_input).eq("password", p_input).execute()
            if len(user_query.data) > 0:
                st.session_state.auth = True
                st.session_state.user = u_input
                st.success(f"ACCESS GRANTED: WELCOME {u_input}")
                st.rerun()
            else:
                st.error("ACCESS DENIED: INVALID CREDENTIALS.")
    st.stop()

# --- 4. DATA SYNCHRONIZATION ---
try:
    response = supabase.table("trades").select("*").eq("trader_username", st.session_state.user).execute()
    all_trades = pd.DataFrame(response.data)
except Exception as e:
    st.error(f"SYSTEM_ERROR: Unable to sync private vault data. {e}")
    all_trades = pd.DataFrame()

# --- 5. NAVIGATION (THE TABS) ---
tabs = st.tabs([
    "📐 ARCHITECT", 
    "🔥 THE_FORGE", 
    "📊 LIVE_DATA", 
    "🧪 TEST_DATA", 
    "📓 JOURNAL", 
    "📉 PORTFOLIO/DCA", 
    "📈 COMPOUNDER"
])

with tabs[0]: 
    render_architect_tab()

with tabs[1]: 
    render_forge()

with tabs[2]:
    if not all_trades.empty:
        # Filter for Live trades that are NOT study/hindsight
        live_trades = all_trades[(all_trades['type'] == 'LIVE') & (all_trades['hindsight'] == False)]
        render_analytics(live_trades, "LIVE")
    else:
        st.info("Cloud Vault is empty.")

with tabs[3]:
    if not all_trades.empty:
        # Include Hindsight and Demo in the Test/Study view
        test_trades = all_trades[(all_trades['type'] == 'BACKTEST/DEMO') | (all_trades['hindsight'] == True)]
        render_analytics(test_trades, "STUDY/TEST")
    else:
        st.info("Cloud Vault is empty.")

with tabs[4]: 
    render_journal_tab()

with tabs[5]: 
    render_dca_tab()

with tabs[6]: 
    render_compounder()

# --- 6. SIDEBAR UTILITIES ---
st.sidebar.title("TERMINAL_CONTROLS")
st.sidebar.write(f"Logged in as: **{st.session_state.user}**")

if st.sidebar.button("🔒 SECURE_LOGOUT"):
    st.session_state.auth = False
    st.session_state.user = None
    st.rerun()

st.sidebar.divider()
st.sidebar.info("v9.0 Multi-User Cloud Build | 2026 Institutional Edition")
st.sidebar.write("System Status: **🟢 ONLINE**")
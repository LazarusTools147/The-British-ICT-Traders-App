import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sqlite3

# --- 1. SETUP & DB ---
st.set_page_config(page_title="TRADING_TERMINAL_V3", layout="wide")

def init_db():
    conn = sqlite3.connect('trading_vault.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS models (name TEXT PRIMARY KEY, logic TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS trades 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, model_name TEXT, type TEXT, market TEXT, 
                  entry_info TEXT, result TEXT, risk_pc REAL, rr REAL, notes TEXT, 
                  date TEXT, screenshot BLOB)''')
    conn.commit()
    conn.close()

init_db()

# --- 2. LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 TERMINAL_ACCESS")
    if st.text_input("KEY", type="password") == "TRADER2026":
        if st.button("INITIALIZE"):
            st.session_state.auth = True
            st.rerun()
    st.stop()

# --- 3. GLOBAL NAVIGATION ---
tabs = st.tabs(["🏗️ ARCHITECT", "🔥 THE_FORGE", "📊 LIVE_DATA", "🧪 TEST_DATA", "📅 HISTORY", "📈 COMPOUNDER"])

# --- TAB 1: ARCHITECT ---
with tabs[0]:
    st.header("SYSTEM_DESIGN")
    m_name = st.text_input("MODEL_NAME").upper()
    m_logic = st.text_area("MODEL_LOGIC_&_RULES", height=300)
    if st.button("SAVE_MODEL"):
        conn = sqlite3.connect('trading_vault.db')
        conn.execute("INSERT OR REPLACE INTO models VALUES (?, ?)", (m_name, m_logic))
        conn.commit()
        st.success("MODEL_ARCHIVED")

# --- TAB 2: THE_FORGE ---
with tabs[1]:
    conn = sqlite3.connect('trading_vault.db')
    models = pd.read_sql("SELECT name FROM models", conn)['name'].tolist()
    if not models:
        st.warning("CREATE A MODEL FIRST.")
    else:
        st.header("ENTRY_STATION")
        with st.form("log_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                env = st.radio("ENVIRONMENT", ["LIVE", "BACKTEST/DEMO"], horizontal=True)
                mod = st.selectbox("MODEL", models)
                mkt = st.text_input("MARKET (e.g., NQ, OIL)").upper()
                ent = st.text_input("ENTRY_DETAILS (e.g., FVG + OB)")
            with c2:
                res = st.selectbox("RESULT", ["WIN", "LOSS", "BE"])
                rsk = st.number_input("RISK_%", step=0.1)
                rvr = st.number_input("RR_RESULT", step=0.1)
                dt = st.date_input("DATE", datetime.now())
            
            nts = st.text_area("NOTES_&_JOURNAL")
            img = st.file_uploader("UPLOAD_CHART", type=['png', 'jpg', 'jpeg'])
            
            if st.form_submit_button("SAVE_ENTRY"):
                img_data = img.read() if img else None
                conn.execute('''INSERT INTO trades (model_name, type, market, entry_info, result, 
                                risk_pc, rr, notes, date, screenshot) VALUES (?,?,?,?,?,?,?,?,?,?)''',
                             (mod, env, mkt, ent, res, rsk, rvr, nts, dt.strftime("%Y-%m-%d"), img_data))
                conn.commit()
                st.success("DATA_SECURED")

# --- TAB 3 & 4: ANALYTICS (LIVE & TEST) ---
def render_analytics(df_subset, title):
    st.header(title)
    if df_subset.empty:
        st.info("NO DATA LOGGED FOR THIS ENVIRONMENT.")
        return

    c1, c2, c3 = st.columns(3)
    with c1:
        st.plotly_chart(px.pie(df_subset, names='entry_info', title="ENTRY_TYPE_%", hole=0.4), use_container_width=True)
    with c2:
        st.plotly_chart(px.pie(df_subset, names='market', title="MARKET_%", hole=0.4), use_container_width=True)
    with c3:
        # 3rd Pie Chart: Win Rate
        st.plotly_chart(px.pie(df_subset, names='result', title="WIN_RATE_%", hole=0.4, 
                               color='result', color_discrete_map={'WIN':'#00ff00', 'LOSS':'#ff0000', 'BE':'#888888'}), use_container_width=True)

conn = sqlite3.connect('trading_vault.db')
all_trades = pd.read_sql("SELECT * FROM trades", conn)

with tabs[2]: render_analytics(all_trades[all_trades['type'] == 'LIVE'], "LIVE_PERFORMANCE")
with tabs[3]: render_analytics(all_trades[all_trades['type'] == 'BACKTEST/DEMO'], "TEST_PERFORMANCE")

# --- TAB 5: HISTORY ---
with tabs[4]:
    st.header("TRADE_HISTORY")
    f_mkt = st.sidebar.text_input("FILTER_MARKET").upper()
    hist_df = all_trades.copy()
    if f_mkt: hist_df = hist_df[hist_df['market'].str.contains(f_mkt)]
    
    for _, row in hist_df.iterrows():
        with st.expander(f"{row['date']} | {row['market']} | {row['result']}"):
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"**Entry:** {row['entry_info']} | **RR:** {row['rr']}R")
                st.write(f"**Notes:** {row['notes']}")
            with col2:
                if row['screenshot']: st.image(row['screenshot'])

# --- TAB 6: COMPOUNDER ---
with tabs[5]:
    st.header("COMPOUND_INTEREST_PROJECTOR")
    col1, col2 = st.columns([1, 2])
    with col1:
        p = st.number_input("INITIAL_INVESTMENT", value=5000)
        r = st.number_input("MONTHLY_RETURN_%", value=5.0)
        y = st.number_input("DURATION_YEARS", value=5)
    
    months = int(y * 12)
    bal = p
    chart_data = []
    for m in range(1, months + 1):
        bal *= (1 + (r / 100))
        if m % 12 == 0:
            chart_data.append({"Year": m//12, "Balance": round(bal, 2)})
    
    with col2:
        st.metric("FUTURE_VALUE", f"${round(bal, 2):,}")
        st.line_chart(pd.DataFrame(chart_data).set_index("Year"))
        st.table(pd.DataFrame(chart_data))

conn.close()
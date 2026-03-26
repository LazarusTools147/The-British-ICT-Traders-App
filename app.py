import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sqlite3
import re

# --- 1. SETUP & DATABASE REPAIR ---
st.set_page_config(page_title="TRADING_TERMINAL_V3", layout="wide")

def init_db():
    conn = sqlite3.connect('trading_vault.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS models (name TEXT PRIMARY KEY, logic TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS trades 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, model_name TEXT, type TEXT, market TEXT, 
                  entry_info TEXT, entry_time TEXT, result TEXT, risk_pc REAL, rr REAL, notes TEXT, 
                  date TEXT, screenshot BLOB)''')
    try:
        c.execute('ALTER TABLE trades ADD COLUMN entry_time TEXT')
    except:
        pass
    conn.commit()
    conn.close()

init_db()

# --- 2. LOGIN ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 TERMINAL_ACCESS")
    pwd = st.text_input("KEY", type="password")
    if st.button("INITIALIZE"):
        if pwd == "TRADER2026":
            st.session_state.auth = True
            st.rerun()
    st.stop()

if st.sidebar.button("🔒 LOGOUT"):
    st.session_state.auth = False
    st.rerun()

# --- 3. TABS ---
tabs = st.tabs(["🏗️ ARCHITECT", "🔥 THE_FORGE", "📊 LIVE_DATA", "🧪 TEST_DATA", "📅 HISTORY", "📈 COMPOUNDER"])

# --- TAB 1: ARCHITECT ---
with tabs[0]:
    st.header("SYSTEM_DESIGN")
    m_name = st.text_input("MODEL_NAME").upper()
    m_logic = st.text_area("MODEL_LOGIC_&_RULES", height=300)
    if st.button("SAVE_MODEL"):
        if m_name:
            conn = sqlite3.connect('trading_vault.db')
            conn.execute("INSERT OR REPLACE INTO models VALUES (?, ?)", (m_name, m_logic))
            conn.commit()
            st.success("MODEL_ARCHIVED")

# --- TAB 2: THE_FORGE ---
with tabs[1]:
    conn = sqlite3.connect('trading_vault.db')
    models_df = pd.read_sql("SELECT name FROM models", conn)
    models = models_df['name'].tolist()
    if not models:
        st.warning("CREATE A MODEL FIRST.")
    else:
        st.header("ENTRY_STATION")
        with st.form("log_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                env = st.radio("ENVIRONMENT", ["LIVE", "BACKTEST/DEMO"], horizontal=True)
                mod = st.selectbox("MODEL", models)
                mkt = st.text_input("MARKET (NQ, OIL, ES)").upper()
                ent_type = st.text_input("ENTRY_DETAILS (e.g. FVG + OB)")
                ent_time = st.text_input("ENTRY_TIME (e.g. 08:30 or 14:15)")
            with c2:
                res = st.selectbox("RESULT", ["WIN", "LOSS", "BE"])
                rsk = st.number_input("RISK_%", step=0.1, value=1.0)
                rvr = st.number_input("RR_RESULT", step=0.1, value=2.0)
                dt = st.date_input("DATE", datetime.now())
            
            nts = st.text_area("NOTES_&_JOURNAL")
            img = st.file_uploader("UPLOAD_CHART", type=['png', 'jpg', 'jpeg'])
            
            if st.form_submit_button("SAVE_ENTRY"):
                img_data = img.read() if img else None
                conn.execute('''INSERT INTO trades (model_name, type, market, entry_info, entry_time, result, 
                                risk_pc, rr, notes, date, screenshot) VALUES (?,?,?,?,?,?,?,?,?,?,?)''',
                             (mod, env, mkt, ent_type, ent_time.upper(), res, rsk, rvr, nts, dt.strftime("%Y-%m-%d"), img_data))
                conn.commit()
                st.success("DATA_SECURED")

# --- TAB 3 & 4: ANALYTICS ---
def render_analytics(df_subset, title):
    st.header(title)
    if df_subset.empty:
        st.info("NO DATA LOGGED.")
        return

    # FIXED 24H TIME PARSER
    def get_hour_int(t_str):
        if not t_str: return None
        match = re.search(r'(\d{1,2})', str(t_str))
        if match:
            return int(match.group(1))
        return None

    df_subset['hour'] = df_subset['entry_time'].apply(get_hour_int)
    
    # Create the 24h Frequency Bar Chart
    st.subheader("⏱️ 24-HOUR TRADE DISTRIBUTION")
    time_counts = df_subset['hour'].value_counts().reindex(range(24), fill_value=0).reset_index()
    time_counts.columns = ['Hour', 'Frequency']
    time_counts['Hour_Label'] = time_counts['Hour'].apply(lambda x: f"{x:02d}:00")

    fig_bar = px.bar(time_counts, x='Hour_Label', y='Frequency', 
                     title="Trade Frequency Across 24h Day",
                     labels={'Hour_Label': 'Time of Day', 'Frequency': 'Number of Trades'},
                     color_discrete_sequence=['#000000'])
    fig_bar.update_xaxes(tickmode='linear')
    st.plotly_chart(fig_bar, use_container_width=True)

    st.divider()

    c1, c2 = st.columns(2)
    c3, c4 = st.columns(2)
    with c1: st.plotly_chart(px.pie(df_subset, names='entry_info', title="ENTRY_TYPE_%", hole=0.4), use_container_width=True)
    with c2: st.plotly_chart(px.pie(df_subset, names='market', title="MARKET_%", hole=0.4), use_container_width=True)
    with c3: st.plotly_chart(px.pie(df_subset, names='result', title="WIN_RATE_%", hole=0.4, color='result', color_discrete_map={'WIN':'#00ff00', 'LOSS':'#ff0000', 'BE':'#888888'}), use_container_width=True)
    with c4: st.plotly_chart(px.pie(df_subset, names='entry_time', title="ALL_TIME_ENTRIES_%", hole=0.4), use_container_width=True)

conn = sqlite3.connect('trading_vault.db')
all_trades = pd.read_sql("SELECT * FROM trades", conn)

with tabs[2]: render_analytics(all_trades[all_trades['type'] == 'LIVE'], "LIVE_PERFORMANCE")
with tabs[3]: render_analytics(all_trades[all_trades['type'] == 'BACKTEST/DEMO'], "TEST_PERFORMANCE")

# --- TAB 5: HISTORY ---
with tabs[4]:
    st.header("TRADE_HISTORY")
    search_q = st.text_input("SEARCH_MARKET").upper()
    hist_df = all_trades.copy()
    if search_q: hist_df = hist_df[hist_df['market'].str.contains(search_q)]
    
    for _, row in hist_df.iterrows():
        with st.expander(f"{row['date']} | {row['entry_time']} | {row['market']} | {row['result']}"):
            col1, col2 = st.columns([2, 1])
            with col1:
                edit_key = f"edit_mode_{row['id']}"
                if edit_key not in st.session_state: st.session_state[edit_key] = False
                
                if not st.session_state[edit_key]:
                    st.write(f"**Entry:** {row['entry_info']} | **Time:** {row['entry_time']}")
                    st.write(f"**RR:** {row['rr']}R | **Notes:** {row['notes']}")
                    ca, cb = st.columns(2)
                    if ca.button("✏️ EDIT", key=f"e_{row['id']}"): 
                        st.session_state[edit_key] = True
                        st.rerun()
                    if cb.button("🗑️ DELETE", key=f"d_{row['id']}"):
                        conn.execute("DELETE FROM trades WHERE id=?", (row['id'],))
                        conn.commit()
                        st.rerun()
                else:
                    n_ent = st.text_input("Details", row['entry_info'], key=f"ne_{row['id']}")
                    n_time = st.text_input("Time", row['entry_time'], key=f"nt_{row['id']}")
                    n_rr = st.number_input("RR", value=float(row['rr']), key=f"nr_{row['id']}")
                    if st.button("SAVE", key=f"s_{row['id']}"):
                        conn.execute("UPDATE trades SET entry_info=?, entry_time=?, rr=? WHERE id=?", (n_ent, n_time.upper(), n_rr, row['id']))
                        conn.commit()
                        st.session_state[edit_key] = False
                        st.rerun()
            with col2:
                if row['screenshot']: st.image(row['screenshot'])

# --- TAB 6: COMPOUNDER ---
with tabs
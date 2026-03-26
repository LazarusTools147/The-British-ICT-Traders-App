import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sqlite3
import re

# --- 1. SETUP & DATABASE REPAIR ---
st.set_page_config(page_title="ICT_PRECISION_TERMINAL_V5.5", layout="wide")

def init_db():
    conn = sqlite3.connect('trading_vault.db', check_same_thread=False)
    c = conn.cursor()
    # Create Tables
    c.execute('CREATE TABLE IF NOT EXISTS models (name TEXT PRIMARY KEY, logic TEXT, sessions TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS trades 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, model_name TEXT, type TEXT, market TEXT, 
                  entry_info TEXT, entry_time TEXT, session TEXT, target TEXT, result TEXT, 
                  risk_pc REAL, rr REAL, notes TEXT, date TEXT, duration_mins INTEGER, 
                  news_impact TEXT, screenshot BLOB)''')
    
    # RUTHLESS REPAIR: Ensure every column exists for older database versions
    columns_to_add = [
        ('duration_mins', 'INTEGER'), 
        ('news_impact', 'TEXT'), 
        ('session', 'TEXT'), 
        ('target', 'TEXT'), 
        ('sessions', 'TEXT')
    ]
    for col_name, col_type in columns_to_add:
        try: 
            c.execute(f'ALTER TABLE trades ADD COLUMN {col_name} {col_type}')
        except: 
            pass
            
    try:
        c.execute('ALTER TABLE models ADD COLUMN sessions TEXT')
    except:
        pass
        
    conn.commit()
    conn.close()

init_db()

# --- 2. LOGIN SYSTEM ---
if 'auth' not in st.session_state:
    st.session_state.auth = False

if not st.session_state.auth:
    st.title("🔐 TERMINAL_ACCESS")
    pwd = st.text_input("ENTER ACCESS KEY", type="password")
    if st.button("INITIALIZE SYSTEM"):
        if pwd == "TRADER2026":
            st.session_state.auth = True
            st.rerun()
        else:
            st.error("ACCESS DENIED")
    st.stop()

if st.sidebar.button("🔒 LOGOUT"):
    st.session_state.auth = False
    st.rerun()

# --- 3. TAB ARCHITECTURE ---
tabs = st.tabs(["🏗️ ARCHITECT", "🔥 THE_FORGE", "📊 LIVE_DATA", "🧪 TEST_DATA", "📅 HISTORY", "📈 COMPOUNDER"])

# --- TAB 1: ARCHITECT (Model Designer) ---
with tabs[0]:
    st.header("MODEL_ARCHITECT")
    m_name = st.text_input("MODEL_NAME (e.g., SILVER_BULLET)").upper()
    m_sess_list = st.multiselect("ALLOWED_SESSIONS", ["ASIA", "LONDON", "NY AM", "NY PM"])
    m_logic = st.text_area("CORE_LOGIC_&_MACRO_RULES", height=250)
    if st.button("ARCHIVE_MODEL"):
        if m_name:
            conn = sqlite3.connect('trading_vault.db')
            conn.execute("INSERT OR REPLACE INTO models VALUES (?, ?, ?)", (m_name, m_logic, ",".join(m_sess_list)))
            conn.commit()
            conn.close()
            st.success(f"MODEL {m_name} SECURED IN DATABASE")

# --- TAB 2: THE_FORGE (Entry Station) ---
with tabs[1]:
    conn = sqlite3.connect('trading_vault.db')
    models_df = pd.read_sql("SELECT * FROM models", conn)
    models = models_df['name'].tolist()
    if not models:
        st.warning("⚠️ YOU MUST ARCHITECT A MODEL BEFORE LOGGING ENTRIES.")
    else:
        st.header("THE_FORGE: LOG_ENTRY")
        with st.form("log_form", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                env = st.radio("ENVIRONMENT", ["LIVE", "BACKTEST/DEMO"], horizontal=True)
                mod = st.selectbox("MODEL_SELECTION", models)
                mkt = st.text_input("MARKET (e.g., NQ, ES)").upper()
                ent_type = st.text_input("ENTRY_DETAILS (e.g., FVG+OB)")
            with col2:
                ent_time = st.text_input("ENTRY_TIME (HH:MM)")
                ent_sess = st.text_input("SESSION (e.g., LONDON)").upper()
                dur = st.number_input("DURATION_IN_TRADE (MINS)", min_value=1, value=15)
                news = st.selectbox("NEWS_IMPACT", ["NONE", "LOW", "MEDIUM", "HIGH (RED)"])
            with col3:
                targ = st.text_input("PRIMARY_TARGET (e.g., BSL)").upper()
                res = st.selectbox("TRADE_RESULT", ["WIN", "LOSS", "BE"])
                rsk = st.number_input("RISK_%", value=1.0, step=0.1)
                rvr = st.number_input("RR_RESULT", value=2.0, step=0.1)
                dt = st.date_input("TRADE_DATE", datetime.now())
            
            nts = st.text_area("JOURNAL_NOTES_&_PSYCHOLOGY")
            img = st.file_uploader("UPLOAD_CHART_SCREENSHOT", type=['png', 'jpg', 'jpeg'])
            
            if st.form_submit_button("SAVE_TRADE_TO_VAULT"):
                if not mkt or not ent_time:
                    st.error("MISSING DATA: Market and Time are mandatory.")
                else:
                    img_data = img.read() if img else None
                    conn = sqlite3.connect('trading_vault.db')
                    conn.execute('''INSERT INTO trades (model_name, type, market, entry_info, entry_time, session, 
                                    target, result, risk_pc, rr, notes, date, duration_mins, news_impact, screenshot) 
                                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                                 (mod, env, mkt, ent_type, ent_time, ent_sess, targ, res, rsk, rvr, nts, dt.strftime("%Y-%m-%d"), dur, news, img_data))
                    conn.commit()
                    conn.close()
                    st.success("TRADE_SECURED_IN_VAULT")

# --- TAB 3 & 4: SEGMENTED ANALYTICS (The Logic Core) ---
def render_full_segmented_analytics(df_all, suffix):
    if df_all.empty:
        st.info(f"NO DATA LOGGED FOR {suffix}.")
        return

    def get_color_cat(t_str):
        m = re.search(r'(\d{1,2})[:.]?(\d{2})', str(t_str))
        if not m: return "OTHER"
        h, mins = int(m.group(1)), int(m.group(2))
        # LONDON MACRO DEFINITIONS (2:50-3:10, 3:50-4:10, 4:50-5:10)
        if (h == 2 and mins >= 50) or (h == 3 and mins <= 10) or \
           (h == 3 and mins >= 50) or (h == 4 and mins <= 10) or \
           (h == 4 and mins >= 50) or (h == 5 and mins <= 10):
            return "GOLD_MACRO"
        return f"{h:02d}:00_Hour"

    color_map = {"GOLD_MACRO": "#FFD700", "02:00_Hour": "#1f77b4", "03:00_Hour": "#ff7f0e", 
                 "04:00_Hour": "#2ca02c", "05:00_Hour": "#d62728", "06:00_Hour": "#9467bd"}

    for result_type, title, emoji in [("WIN", "THE WINNERS' CIRCLE", "🏆"), ("BE", "THE BREAK-EVEN DEFENSE", "🛡️"), ("LOSS", "THE AUTOPSY", "💀")]:
        sub_df = df_all[df_all['result'] == result_type].copy()
        st.markdown(f"## {emoji} {title}")
        if sub_df.empty:
            st.write(f"No {result_type} trades recorded in this environment.")
        else:
            sub_df['Cat'] = sub_df['entry_time'].apply(get_color_cat)
            c1, c2 = st.columns([2, 1])
            with c1:
                fig = px.bar(sub_df.sort_values('entry_time'), x='entry_time', color='Cat', 
                             title=f"{result_type} Entry Pulse (1m Precision)", color_discrete_map=color_map)
                fig.update_layout(bargap=0.4)
                st.plotly_chart(fig, use_container_width=True, key=f"bar_{result_type}_{suffix}")
            with c2:
                st.metric(f"AVG {result_type} DURATION", f"{round(sub_df['duration_mins'].mean(), 1)}m")
                st.plotly_chart(px.pie(sub_df, names='entry_info', title="Entry Setups", hole=0.4), key=f"p_ent_{result_type}_{suffix}")
            
            p1, p2, p3, p4 = st.columns(4)
            with p1: st.plotly_chart(px.pie(sub_df, names='market', title="Markets Traded", hole=0.4), use_container_width=True, key=f"p_mkt_{result_type}_{suffix}")
            with p2: st.plotly_chart(px.pie(sub_df, names='session', title="Session Distribution", hole=0.4), use_container_width=True, key=f"p_ses_{result_type}_{suffix}")
            with p3: st.plotly_chart(px.pie(sub_df, names='target', title="Targets Hit", hole=0.4), use_container_width=True, key=f"p_tar_{result_type}_{suffix}")
            with p4: st.plotly_chart(px.pie(sub_df, names='news_impact', title="News Impact", hole=0.4), use_container_width=True, key=f"p_nws_{result_type}_{suffix}")
        st.divider()

conn = sqlite3.connect('trading_vault.db')
all_trades = pd.read_sql("SELECT * FROM trades", conn)

with tabs[2]: render_full_segmented_analytics(all_trades[all_trades['type'] == 'LIVE'], "LIVE")
with tabs[3]: render_full_segmented_analytics(all_trades[all_trades['type'] == 'BACKTEST/DEMO'], "TEST")

# --- TAB 5: HISTORY (Trade Management) ---
with tabs[4]:
    st.header("📅 COMPLETE_TRADE_HISTORY")
    search_q = st.text_input("SEARCH_BY_MARKET (e.g., NQ)").upper()
    hist_df = all_trades.copy()
    if search_q: hist_df = hist_df[hist_df['market'].str.contains(search_q)]
    
    for _, row in hist_df[::-1].iterrows(): # Show newest first
        with st.expander(f"{row['date']} | {row['entry_time']} | {row['market']} | {row['result']}"):
            col_a, col_b = st.columns([2, 1])
            with col_a:
                st.write(f"**Model:** {row['model_name']} | **Session:** {row['session']}")
                st.write(f"**Target:** {row['target']} | **Duration:** {row['duration_mins']}m")
                st.write(f"**News Impact:** {row['news_impact']}")
                st.info(f"**Notes:** {row['notes']}")
                if st.button("🗑️ PERMANENTLY_DELETE_TRADE", key=f"del_{row['id']}"):
                    conn = sqlite3.connect('trading_vault.db')
                    conn.execute("DELETE FROM trades WHERE id=?", (row['id'],))
                    conn.commit()
                    st.rerun()
            with col_b:
                if row['screenshot']:
                    st.image(row['screenshot'], caption="Trade Setup")

# --- TAB 6: COMPOUNDER (Equity Projector) ---
with tabs[5]:
    st.header("📈 COMPOUND_PROJECTOR")
    c_col1, c_col2 = st.columns([1, 2])
    with c_col1:
        p_val = st.number_input("STARTING_CAPITAL", value=5000)
        r_val = st.number_input("TARGET_MONTHLY_%", value=5.0)
        y_val = st.number_input("INVESTMENT_YEARS", value=5)
    
    months = int(y_val * 12)
    current_bal = p_val
    projection_data = []
    for m in range(1, months + 1):
        current_bal *= (1 + (r_val / 100))
        if m % 12 == 0:
            projection_data.append({"Year": m//12, "Balance": round(current_bal, 2)})
    
    with c_col2:
        st.line_chart(pd.DataFrame(projection_data).set_index("Year"))
        st.table(pd.DataFrame(projection_data))

conn.close()
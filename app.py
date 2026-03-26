import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import sqlite3
import re

# --- 1. SETUP & DATABASE REPAIR ---
st.set_page_config(page_title="ICT_PRECISION_TERMINAL_V5.3", layout="wide")

def init_db():
    conn = sqlite3.connect('trading_vault.db', check_same_thread=False)
    c = conn.cursor()
    # Ensure all tables exist
    c.execute('CREATE TABLE IF NOT EXISTS models (name TEXT PRIMARY KEY, logic TEXT, sessions TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS trades 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, model_name TEXT, type TEXT, market TEXT, 
                  entry_info TEXT, entry_time TEXT, session TEXT, target TEXT, result TEXT, 
                  risk_pc REAL, rr REAL, notes TEXT, date TEXT, duration_mins INTEGER, 
                  news_impact TEXT, screenshot BLOB)''')
    
    # RUTHLESS REPAIR: Ensure all columns exist for old databases
    cols_to_check = [
        ('duration_mins', 'INTEGER'), 
        ('news_impact', 'TEXT'), 
        ('session', 'TEXT'), 
        ('target', 'TEXT'), 
        ('sessions', 'TEXT')
    ]
    for col_name, col_type in cols_to_check:
        try:
            c.execute(f'ALTER TABLE trades ADD COLUMN {col_name} {col_type}')
        except:
            pass
    try:
        c.execute(f'ALTER TABLE models ADD COLUMN sessions TEXT')
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
    m_sessions = st.multiselect("ALLOWED_SESSIONS", ["ASIA", "LONDON", "NY AM", "NY PM"])
    m_logic = st.text_area("MODEL_LOGIC_&_RULES", height=250)
    if st.button("SAVE_MODEL"):
        if m_name:
            conn = sqlite3.connect('trading_vault.db')
            conn.execute("INSERT OR REPLACE INTO models VALUES (?, ?, ?)", (m_name, m_logic, ",".join(m_sessions)))
            conn.commit()
            conn.close()
            st.success(f"MODEL {m_name} ARCHIVED")

# --- TAB 2: THE_FORGE ---
with tabs[1]:
    conn = sqlite3.connect('trading_vault.db')
    models_df = pd.read_sql("SELECT * FROM models", conn)
    models = models_df['name'].tolist()
    if not models:
        st.warning("CREATE A MODEL FIRST.")
    else:
        st.header("ENTRY_STATION")
        with st.form("log_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                env = st.radio("ENVIRONMENT", ["LIVE", "BACKTEST/DEMO"], horizontal=True)
                mod = st.selectbox("MODEL", models)
                mkt = st.text_input("MARKET (NQ, OIL, ES)").upper()
                ent_type = st.text_input("ENTRY_DETAILS (e.g. FVG + OB)")
            with c2:
                ent_time = st.text_input("EXACT_TIME (e.g. 03:45)")
                ent_sess = st.text_input("SESSION (e.g. LONDON)").upper()
                dur = st.number_input("DURATION (MINS)", min_value=1, value=15)
                news = st.selectbox("NEWS_IMPACT", ["NONE", "LOW", "MEDIUM", "HIGH (RED)"])
            with c3:
                targ = st.text_input("TARGET (e.g. BSL)").upper()
                res = st.selectbox("RESULT", ["WIN", "LOSS", "BE"])
                rsk = st.number_input("RISK_%", value=1.0)
                rvr = st.number_input("RR_RESULT", value=2.0)
                dt = st.date_input("DATE", datetime.now())
            
            nts = st.text_area("NOTES_&_JOURNAL")
            img = st.file_uploader("UPLOAD_CHART", type=['png', 'jpg', 'jpeg'])
            
            if st.form_submit_button("SAVE_ENTRY"):
                if not mkt or not ent_type or not ent_time:
                    st.error("MISSING DATA: Market, Details, and Time are required.")
                else:
                    img_data = img.read() if img else None
                    conn = sqlite3.connect('trading_vault.db')
                    conn.execute('''INSERT INTO trades (model_name, type, market, entry_info, entry_time, session, 
                                    target, result, risk_pc, rr, notes, date, duration_mins, news_impact, screenshot) 
                                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                                 (mod, env, mkt, ent_type, ent_time, ent_sess, targ, res, rsk, rvr, nts, dt.strftime("%Y-%m-%d"), dur, news, img_data))
                    conn.commit()
                    conn.close()
                    st.success("DATA_SECURED")

# --- TAB 3 & 4: SEGMENTED ANALYTICS ---
def render_segmented_analytics(df_all, suffix):
    if df_all.empty:
        st.info(f"NO DATA LOGGED FOR {suffix}.")
        return

    def get_color_cat(t_str):
        m = re.search(r'(\d{1,2})[:.]?(\d{2})', str(t_str))
        if not m: return "OTHER"
        h, mins = int(m.group(1)), int(m.group(2))
        # Highlight London Macros: 2:50-3:10, 3:50-4:10, 4:50-5:10
        if (h == 2 and mins >= 50) or (h == 3 and mins <= 10) or \
           (h == 3 and mins >= 50) or (h == 4 and mins <= 10) or \
           (h == 4 and mins >= 50) or (h == 5 and mins <= 10):
            return "GOLD_MACRO"
        return f"{h:02d}:00 Hour"

    # Split Data
    wins_df = df_all[df_all['result'] == 'WIN'].copy()
    loss_df = df_all[df_all['result'] == 'LOSS'].copy()
    be_df = df_all[df_all['result'] == 'BE'].copy()

    color_map = {"GOLD_MACRO": "#FFD700", "02:00 Hour": "#1f77b4", "03:00 Hour": "#ff7f0e", 
                 "04:00 Hour": "#2ca02c", "05:00 Hour": "#d62728", "06:00 Hour": "#9467bd"}

    # --- WINS ---
    st.markdown("### 🏆 THE WINNERS' CIRCLE")
    if wins_df.empty: st.write("No wins recorded yet.")
    else:
        wins_df['Cat'] = wins_df['entry_time'].apply(get_color_cat)
        c1, c2 = st.columns([2, 1])
        with c1:
            fig = px.bar(wins_df.sort_values('entry_time'), x='entry_time', color='Cat', 
                         title="Winning Entry Distribution (1m)", color_discrete_map=color_map)
            fig.update_layout(bargap=0.4)
            st.plotly_chart(fig, use_container_width=True, key=f"w_b_{suffix}")
        with c2:
            st.metric("AVG WIN DURATION", f"{round(wins_df['duration_mins'].mean(), 1)}m")
            st.plotly_chart(px.pie(wins_df, names='entry_info', title="Winning Setups", hole=0.4), key=f"w_p_{suffix}")

    st.divider()

    # --- BREAK EVENS ---
    st.markdown("### 🛡️ THE BREAK-EVEN DEFENSE")
    if be_df.empty: st.write("No BE trades recorded.")
    else:
        be_df['Cat'] = be_df['entry_time'].apply(get_color_cat)
        c1, c2 = st.columns([2, 1])
        with c1:
            fig = px.bar(be_df.sort_values('entry_time'), x='entry_time', color='Cat', 
                         title="BE Entry Distribution (1m)", color_discrete_map=color_map)
            fig.update_layout(bargap=0.4)
            st.plotly_chart(fig, use_container_width=True, key=f"be_b_{suffix}")
        with c2:
            st.metric("AVG BE DURATION", f"{round(be_df['duration_mins'].mean(), 1)}m")
            st.plotly_chart(px.pie(be_df, names='session', title="BE Sessions", hole=0.4), key=f"be_p_{suffix}")

    st.divider()

    # --- LOSSES ---
    st.markdown("### 💀 THE AUTOPSY (LOSSES)")
    if loss_df.empty: st.write("Zero losses. Stay ruthless.")
    else:
        loss_df['Cat'] = loss_df['entry_time'].apply(get_color_cat)
        c1, c2 = st.columns([2, 1])
        with c1:
            fig = px.bar(loss_df.sort_values('entry_time'), x='entry_time', color='Cat', 
                         title="Losing Entry Distribution (1m)", color_discrete_map=color_map)
            fig.update_layout(bargap=0.4)
            st.plotly_chart(fig, use_container_width=True, key=f"l_b_{suffix}")
        with c2:
            st.metric("AVG LOSS DURATION", f"{round(loss_df['duration_mins'].mean(), 1)}m")
            st.plotly_chart(px.pie(loss_df, names='news_impact', title="Losses vs News", hole=0.4), key=f"l_p_{suffix}")

conn = sqlite3.connect('trading_vault.db')
all_trades = pd.read_sql("SELECT * FROM trades", conn)

with tabs[2]: render_segmented_analytics(all_trades[all_trades['type'] == 'LIVE'], "LIVE")
with tabs[3]: render_segmented_analytics(all_trades[all_trades['type'] == 'BACKTEST/DEMO'], "TEST")

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
                st.write(f"**Session:** {row['session']} | **Target:** {row['target']} | **Duration:** {row['duration_mins']}m")
                st.write(f"**News:** {row['news_impact']} | **Model:** {row['model_name']}")
                st.write(f"**Notes:** {row['notes']}")
                if st.button("🗑️ DELETE", key=f"del_{row['id']}"):
                    conn = sqlite3.connect('trading_vault.db')
                    conn.execute("DELETE FROM trades WHERE id=?", (row['id'],))
                    conn.commit()
                    st.rerun()
            with col2:
                if row['screenshot']: st.image(row['screenshot'])

# --- TAB 6: COMPOUNDER ---
with tabs[5]:
    st.header("COMPOUND_PROJECTOR")
    c_col1, c_col2 = st.columns([1, 2])
    with c_col1:
        p_val = st.number_input("INITIAL_BALANCE", value=5000)
        r_val = st.number_input("MONTHLY_PERCENT_%", value=5.0)
        y_val = st.number_input("YEARS", value=5)
    months, bal = int(y_val * 12), p_val
    data = []
    for m in range(1, months + 1):
        bal *= (1 + (r_val / 100))
        if m % 12 == 0: data.append({"Year": m//12, "Balance": round(bal, 2)})
    with c_col2:
        st.line_chart(pd.DataFrame(data).set_index("Year"))
        st.table(pd.DataFrame(data))

conn.close()
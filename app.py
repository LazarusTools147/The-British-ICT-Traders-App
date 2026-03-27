import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import sqlite3
import re

# --- 1. SETUP & PERSISTENCE ---
st.set_page_config(page_title="ICT_MASTER_TERMINAL_V7.1", layout="wide")

def get_connection():
    return sqlite3.connect('trading_vault.db', check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS models (name TEXT PRIMARY KEY, logic TEXT, sessions TEXT)')
    c.execute('''CREATE TABLE IF NOT EXISTS trades 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, model_name TEXT, model_var TEXT, type TEXT, market TEXT, 
                  entry_info TEXT, entry_time TEXT, entry_tf TEXT, session TEXT, target TEXT, result TEXT, 
                  risk_pc REAL, rr REAL, notes TEXT, date TEXT, duration_mins INTEGER, 
                  news_impact TEXT, screenshot BLOB)''')
    
    # Ensure all columns exist for Model Variation and Metadata
    cols = [('model_var', 'TEXT'), ('duration_mins', 'INTEGER'), ('news_impact', 'TEXT'), 
            ('session', 'TEXT'), ('target', 'TEXT'), ('entry_tf', 'TEXT')]
    for col, typ in cols:
        try: c.execute(f'ALTER TABLE trades ADD COLUMN {col} {typ}')
        except: pass
    conn.commit()
    conn.close()

init_db()

# --- 2. AUTHENTICATION ---
if 'auth' not in st.session_state: st.session_state.auth = False
if not st.session_state.auth:
    st.title("🔐 TERMINAL_ACCESS")
    pwd = st.text_input("ENTER ACCESS KEY", type="password")
    if pwd == "TRADER2026":
        st.session_state.auth = True
        st.rerun()
    elif pwd != "": st.error("INVALID KEY")
    st.stop()

if st.sidebar.button("🔒 LOGOUT"):
    st.session_state.auth = False
    st.rerun()

# --- 3. TABS ---
tabs = st.tabs(["🏗️ ARCHITECT", "🔥 THE_FORGE", "📊 LIVE_DATA", "🧪 TEST_DATA", "📓 JOURNAL", "📈 COMPOUNDER"])

# --- TAB 1: ARCHITECT ---
with tabs[0]:
    st.header("MODEL_ARCHITECT")
    m_name = st.text_input("MODEL_NAME").upper()
    m_sess = st.multiselect("SESSIONS", ["ASIA", "LONDON", "NY AM", "NY PM"])
    m_logic = st.text_area("CORE_LOGIC", height=150)
    if st.button("SAVE_MODEL"):
        if m_name:
            conn = get_connection()
            conn.execute("INSERT OR REPLACE INTO models VALUES (?, ?, ?)", (m_name, m_logic, ",".join(m_sess)))
            conn.commit(); conn.close(); st.success("MODEL ARCHIVED")

# --- TAB 2: THE_FORGE (With Model Variation) ---
with tabs[1]:
    conn = get_connection()
    models = pd.read_sql("SELECT name FROM models", conn)['name'].tolist()
    conn.close()
    if not models: st.warning("Create a Model in Architect first.")
    else:
        st.header("THE_FORGE: LOG_ENTRY")
        with st.form("forge_form", clear_on_submit=True):
            c1, c2, c3 = st.columns(3)
            with c1:
                env = st.radio("ENV", ["LIVE", "BACKTEST/DEMO"], horizontal=True)
                mod = st.selectbox("MODEL", models)
                mvar = st.text_input("MODEL VARIATION (e.g. v1, aggressive)").upper()
                mkt = st.text_input("MARKET").upper()
            with c2:
                tm = st.text_input("TIME (HH:MM)")
                tf = st.text_input("TF").upper()
                sess = st.text_input("SESSION").upper()
                dur = st.number_input("DURATION (MINS)", 1, 500, 15)
            with c3:
                nws = st.text_input("NEWS").upper()
                res = st.text_input("RESULT (WIN, LOSS, BE)").upper()
                rsk = st.number_input("RISK %", value=1.0)
                rr_val = st.number_input("RR", value=2.0)
                dt = st.date_input("DATE", datetime.now())
            nts = st.text_area("JOURNAL NOTES")
            img = st.file_uploader("UPLOAD CHART")
            if st.form_submit_button("SAVE_ENTRY"):
                img_data = img.read() if img else None
                conn = get_connection()
                conn.execute('''INSERT INTO trades (model_name, model_var, type, market, entry_time, entry_tf, 
                                session, result, risk_pc, rr, notes, date, duration_mins, news_impact, screenshot) 
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
                             (mod, mvar, env, mkt, tm, tf, sess, res, rsk, rr_val, nts, dt.strftime("%Y-%m-%d"), dur, nws, img_data))
                conn.commit(); conn.close(); st.success("TRADE ARCHIVED")

# --- 4. ANALYTICS (Deep Orange BE + Variations) ---
def render_analytics(df, suffix):
    if df.empty: return st.info("No Data Recorded.")
    
    st.markdown("## 📈 PERFORMANCE KPI")
    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("WIN RATE", f"{round((len(df[df['result']=='WIN'])/len(df))*100,1)}%")
    with k2: st.metric("AVG DUR", f"{round(df['duration_mins'].mean(),1)}m")
    with k3: st.metric("AVG RISK", f"{round(df['risk_pc'].mean(),2)}%")
    with k4: st.metric("AVG RR", f"{round(df['rr'].mean(),2)}R")

    st.divider()
    # Deep Orange BE (#FF8C00)
    colors = {'WIN':'#00ff00', 'LOSS':'#ff0000', 'BE':'#FF8C00'}
    c_bar, c_pie = st.columns([3, 1])
    with c_bar:
        st.plotly_chart(px.bar(df.sort_values('entry_time'), x='entry_time', y='rr', color='result', color_discrete_map=colors).update_layout(bargap=0.3), use_container_width=True)
    with c_pie:
        st.plotly_chart(px.pie(df, names='result', hole=0.5, color='result', color_discrete_map=colors), use_container_width=True)

    def draw_seg(res_t, label, emoji):
        sdf = df[df['result'] == res_t]
        if sdf.empty: return
        with st.expander(f"{emoji} {label} DEEP-DIVE ANALYSIS"):
            sk1, sk2 = st.columns([3, 1])
            with sk1:
                def get_m(t):
                    m = re.search(r'(\d{1,2})[:.]?(\d{2})', str(t))
                    if not m: return "OTHER"
                    h, mn = int(m.group(1)), int(m.group(2))
                    if (h==2 and mn>=50) or (h==3 and mn<=10) or (h==3 and mn>=50) or (h==4 and mn<=10) or (h==4 and mn>=50) or (h==5 and mn<=10): return "MACRO"
                    return f"{h:02d}:00"
                sdf['Cat'] = sdf['entry_time'].apply(get_m)
                st.plotly_chart(px.bar(sdf.sort_values('entry_time'), x='entry_time', color='Cat', color_discrete_map={"MACRO":"#FFD700"}), use_container_width=True, key=f"b_{res_t}_{suffix}")
            with sk2:
                st.metric(f"AVG {res_t} TIME", f"{round(sdf['duration_mins'].mean(), 1)}m")
                # NEW: Variation Pie Chart for each result type
                st.plotly_chart(px.pie(sdf, names='model_var', title="Model Variations"), use_container_width=True, key=f"var_{res_t}_{suffix}")
            
            p1, p2, p3, p4 = st.columns(4)
            p_args = dict(hole=0.4, width=220, height=220)
            with p1: st.plotly_chart(px.pie(sdf, names='market', title="Markets", **p_args), use_container_width=True)
            with p2: st.plotly_chart(px.pie(sdf, names='session', title="Sessions", **p_args), use_container_width=True)
            with p3: st.plotly_chart(px.pie(sdf, names='entry_tf', title="Timeframes", **p_args), use_container_width=True)
            with p4: st.plotly_chart(px.pie(sdf, names='news_impact', title="News", **p_args), use_container_width=True)

    draw_seg("WIN", "WINNERS' CIRCLE", "🏆")
    draw_seg("BE", "BREAK EVEN DEFENSE", "🛡️")
    draw_seg("LOSS", "LOSS AUTOPSY", "💀")

conn = get_connection()
all_t = pd.read_sql("SELECT * FROM trades", conn)
conn.close()

with tabs[2]: render_analytics(all_t[all_t['type']=='LIVE'], "L")
with tabs[3]: render_analytics(all_t[all_t['type']=='BACKTEST/DEMO'], "T")

# --- TAB 5: JOURNAL (EE-Style UI) ---
with tabs[4]:
    st.header("📓 THE JOURNAL")
    if all_t.empty:
        st.info("No trades to journal.")
    else:
        df_j = all_t.copy()
        df_j['date'] = pd.to_datetime(df_j['date'])
        
        # EE-Style Calendar Navigation
        st.markdown("### 📅 CALENDAR NAVIGATION")
        cal_filter = st.radio("FILTER BY", ["All Sales", "By Year", "By Month", "By Week", "By Day"], horizontal=True, label_visibility="collapsed")
        
        now = datetime.now()
        if "Year" in cal_filter: df_j = df_j[df_j['date'].dt.year == now.year]
        elif "Month" in cal_filter: df_j = df_j[(df_j['date'].dt.month == now.month) & (df_j['date'].dt.year == now.year)]
        elif "Week" in cal_filter: df_j = df_j[df_j['date'] >= (now - timedelta(days=7))]
        elif "Day" in cal_filter: df_j = df_j[df_j['date'].dt.date == now.date()]

        # Model Variation Sub-tabs
        vars_available = ["ALL VARIATIONS"] + list(df_j['model_var'].unique())
        v_select = st.selectbox("SELECT VARIATION SUB-TAB", vars_available)
        if v_select != "ALL VARIATIONS":
            df_j = df_j[df_j['model_var'] == v_select]

        st.divider()
        # CSV Backup Still here
        csv = all_t.to_csv(index=False).encode('utf-8')
        st.download_button("📂 DOWNLOAD CSV BACKUP", data=csv, file_name="journal_backup.csv", mime='text/csv')

        for _, row in df_j[::-1].iterrows():
            with st.expander(f"📁 {row['model_name']} [{row['model_var']}] — {row['date'].strftime('%Y-%m-%d')} — {row['result']}"):
                ek = f"edit_{row['id']}"
                if ek not in st.session_state: st.session_state[ek] = False
                
                if not st.session_state[ek]:
                    c1, c2 = st.columns([2, 1])
                    with c1:
                        st.write(f"**TF:** {row['entry_tf']} | **Sess:** {row['session']} | **Dur:** {row['duration_mins']}m | **News:** {row['news_impact']}")
                        st.info(f"**Journal Notes:** {row['notes']}")
                        ec, dc = st.columns(2)
                        if ec.button("✏️ EDIT JOURNAL", key=f"eb_{row['id']}"): st.session_state[ek]=True; st.rerun()
                        if dc.button("🗑️ DELETE", key=f"db_{row['id']}"):
                            conn = get_connection(); conn.execute("DELETE FROM trades WHERE id=?",(row['id'],)); conn.commit(); conn.close(); st.rerun()
                    with c2:
                        if row['screenshot']: st.image(row['screenshot'])
                else:
                    with st.form(f"edit_{row['id']}"):
                        n_nts = st.text_area("Update Notes", row['notes'])
                        n_res = st.text_input("Update Result", row['result']).upper()
                        n_var = st.text_input("Update Variation", row['model_var']).upper()
                        if st.form_submit_button("💾 SAVE CHANGES"):
                            conn = get_connection()
                            conn.execute("UPDATE trades SET notes=?, result=?, model_var=? WHERE id=?", (n_nts, n_res, n_var, row['id']))
                            conn.commit(); conn.close(); st.session_state[ek]=False; st.rerun()

with tabs[5]:
    st.header("📈 COMPOUNDER")
    p, r, y = st.number_input("START", 5000), st.number_input("%/MO", 5.0), st.number_input("YRS", 5)
    bal, data = p, []
    for m in range(1, int(y*12)+1):
        bal *= (1 + (r/100))
        if m%12==0: data.append({"Year": m//12, "Balance": round(bal, 2)})
    st.line_chart(pd.DataFrame(data).set_index("Year"))
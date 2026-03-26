import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- 1. PAGE CONFIG (EE-STYLE) ---
st.set_page_config(page_title="CORE_TERMINAL", page_icon="📈", layout="centered")

# Custom CSS for the Black & White "Brutalist" UI
st.markdown("""
    <style>
    .stApp { background-color: white; color: black; font-family: monospace; }
    div.stButton > button {
        border: 4px solid black !important;
        border-radius: 0px !important;
        background-color: black !important;
        color: white !important;
        font-weight: 900;
        width: 100%;
        padding: 15px;
        text-transform: uppercase;
    }
    .stTextInput input, .stSelectbox select, .stNumberInput input {
        border: 2px solid black !important;
        border-radius: 0px !important;
    }
    </style>
    """, unsafe_allow_value=True)

# --- 2. DATA INITIALIZATION ---
if 'models' not in st.session_state:
    st.session_state.models = {}
if 'trades' not in st.session_state:
    st.session_state.trades = []

# --- 3. SIDEBAR NAVIGATION (THE SETTINGS) ---
with st.sidebar:
    st.title("⚙️ SYSTEM_CONFIG")
    edit_mode = st.toggle("EDIT_MODE (UNLOCK BUILDER)")
    
    if edit_mode:
        st.subheader("BUILD_NEW_MODEL")
        m_name = st.text_input("MODEL_NAME").upper()
        if st.button("INITIALIZE_MODEL"):
            if m_name and m_name not in st.session_state.models:
                st.session_state.models[m_name] = {"rules": [], "variables": {}}
                st.success(f"{m_name} READY")

# --- 4. MAIN INTERFACE ---
st.header("CORE_TERMINAL_V3")

if not st.session_state.models:
    st.info("NO MODELS DETECTED. OPEN SETTINGS TO CREATE YOUR FIRST TRADING SYSTEM.")
else:
    # Model Selection (Like choosing between Sales/Objections)
    selected_model = st.selectbox("ACTIVE_SYSTEM", list(st.session_state.models.keys()))
    model_data = st.session_state.models[selected_model]

    # Tabs (Like your Tracker tabs)
    tab1, tab2 = st.tabs(["[ FORGE_ENTRY ]", "[ DATA_VAULT ]"])

    # --- TAB 1: FORGE (ENTRY LOG) ---
    with tab1:
        if edit_mode:
            st.subheader(f"CONFIGURING: {selected_model}")
            
            # Rule Building
            new_rule = st.text_input("ADD_MANDATORY_RULE (e.g. HTF BIAS)")
            if st.button("+ ADD_RULE"):
                model_data["rules"].append(new_rule.upper())
            
            # Variable Building
            st.divider()
            v_name = st.text_input("ADD_VARIABLE (e.g. PD_ARRAY, SESSION)")
            v_opts = st.text_area("OPTIONS (Comma separated: FVG, OB, NY)").split(',')
            if st.button("+ ADD_VARIABLE"):
                model_data["variables"][v_name.upper()] = [o.strip().upper() for o in v_opts if o.strip()]
            
            if st.button("DELETE_THIS_MODEL", type="secondary"):
                del st.session_state.models[selected_model]
                st.rerun()
        
        else:
            # LIVE LOGGING
            st.subheader(f"SYSTEM: {selected_model}")
            
            # 1. Hard Rules (Checklist)
            st.markdown("**_MANDATORY_VALIDATION_**")
            for rule in model_data["rules"]:
                st.checkbox(rule, key=f"rule_{rule}")
            
            st.divider()

            # 2. Dynamic Variables
            entry_data = {"MODEL": selected_model, "TIME": datetime.now().strftime("%Y-%m-%d %H:%M")}
            
            cols = st.columns(len(model_data["variables"]) if model_data["variables"] else 1)
            for i, (var, opts) in enumerate(model_data["variables"].items()):
                with cols[i % len(cols)]:
                    entry_data[var] = st.selectbox(var, opts)
            
            # 3. Numbers (RR Calc)
            c1, c2, c3 = st.columns(3)
            with c1: entry = st.number_input("ENTRY", value=0.0)
            with c2: sl = st.number_input("STOP", value=0.0)
            with c3: tp = st.number_input("TARGET", value=0.0)
            
            if entry > 0 and sl > 0:
                rr = abs(tp - entry) / abs(entry - sl)
                entry_data['RR'] = round(rr, 2)
                st.metric("PLANNED_RR", f"{round(rr, 2)}R")

            if st.button("EXECUTE_LOG"):
                st.session_state.trades.append(entry_data)
                st.balloons()
                st.success("DATA_SECURED_IN_VAULT")

    # --- TAB 2: VAULT (ANALYTICS) ---
    with tab2:
        if not st.session_state.trades:
            st.warning("VAULT_EMPTY. LOG A TRADE TO SEE ANALYTICS.")
        else:
            df = pd.DataFrame(st.session_state.trades)
            df_model = df[df['MODEL'] == selected_model]
            
            if not df_model.empty:
                st.subheader(f"{selected_model}_ANALYTICS")
                
                # Dynamic Pie Charts (Percentage included automatically by Plotly)
                chart_cols = st.columns(2)
                for i, var in enumerate(model_data["variables"].keys()):
                    with chart_cols[i % 2]:
                        fig = px.pie(df_model, names=var, title=f"{var}_%",
                                     hole=0.4, # Donut style
                                     color_discrete_sequence=px.colors.qualitative.Greys_r)
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        fig.update_layout(showlegend=False, margin=dict(t=30, b=0, l=0, r=0))
                        st.plotly_chart(fig, use_container_width=True)
                
                st.divider()
                st.markdown("**_HISTORICAL_LOGS_**")
                st.dataframe(df_model, use_container_width=True)
            else:
                st.info(f"NO DATA FOR {selected_model}")
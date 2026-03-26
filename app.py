import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- 1. PAGE CONFIG ---
st.set_page_config(page_title="CORE_TERMINAL", layout="centered")

# Simplified CSS to avoid the "Triple Quote" crash
st.markdown("<style>button { border: 4px solid black !important; }</style>", unsafe_allow_value=True)

# --- 2. DATA INITIALIZATION ---
if 'models' not in st.session_state:
    st.session_state.models = {}
if 'trades' not in st.session_state:
    st.session_state.trades = []

# --- 3. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("CONFIG")
    edit_mode = st.toggle("EDIT_MODE")
    if edit_mode:
        m_name = st.text_input("MODEL_NAME").upper()
        if st.button("CREATE"):
            if m_name and m_name not in st.session_state.models:
                st.session_state.models[m_name] = {"rules": [], "variables": {}}

# --- 4. MAIN INTERFACE ---
if not st.session_state.models:
    st.info("CREATE A MODEL IN SETTINGS.")
else:
    selected_model = st.selectbox("SYSTEM", list(st.session_state.models.keys()))
    tab1, tab2 = st.tabs(["[ FORGE ]", "[ VAULT ]"])
    model_data = st.session_state.models[selected_model]

    with tab1:
        if edit_mode:
            new_rule = st.text_input("RULE")
            if st.button("+ RULE"): model_data["rules"].append(new_rule.upper())
            v_name = st.text_input("VARIABLE")
            v_opts = st.text_area("OPTIONS (comma separated)").split(',')
            if st.button("+ VARIABLE"):
                model_data["variables"][v_name.upper()] = [o.strip().upper() for o in v_opts if o.strip()]
        else:
            for rule in model_data["rules"]: st.checkbox(rule)
            entry_data = {"MODEL": selected_model, "TIME": datetime.now()}
            for var, opts in model_data["variables"].items():
                entry_data[var] = st.selectbox(var, opts)
            if st.button("EXECUTE"):
                st.session_state.trades.append(entry_data)
                st.success("LOGGED")

    with tab2:
        if st.session_state.trades:
            df = pd.DataFrame(st.session_state.trades)
            df_model = df[df['MODEL'] == selected_model]
            if not df_model.empty:
                for var in model_data["variables"].keys():
                    fig = px.pie(df_model, names=var, title=var)
                    st.plotly_chart(fig)
                st.table(df_model)
import streamlit as st
import pandas as pd
from database import get_supabase

def render_dca_tab():
    st.header(f"📉 {st.session_state.user}'s PORTFOLIO & DCA TRACKER")
    supabase = get_supabase()

    # PRIVACY FILTER: Strictly pull assets belonging to THIS user
    try:
        response = supabase.table("portfolio").select("*").eq("trader_username", st.session_state.user).execute()
        df = pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"Error fetching portfolio: {e}")
        df = pd.DataFrame()

    with st.expander("➕ ADD NEW ASSET"):
        with st.form("dca_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                symbol = st.text_input("SYMBOL (e.g. BTC, NQ)").upper()
                amount = st.number_input("AMOUNT / CONTRACTS", min_value=0.0, step=0.00001)
            with c2:
                avg_price = st.number_input("AVG ENTRY PRICE", min_value=0.0)
                target = st.number_input("EXIT TARGET", min_value=0.0)
            
            if st.form_submit_button("SECURE TO PRIVATE PORTFOLIO"):
                if symbol:
                    data = {
                        "trader_username": st.session_state.user, # OWNER TAG
                        "symbol": symbol,
                        "amount": amount,
                        "avg_price": avg_price,
                        "exit_target": target
                    }
                    supabase.table("portfolio").upsert(data).execute()
                    st.success(f"✔️ {symbol} saved to your private vault.")
                    st.rerun()
                else:
                    st.error("Symbol required.")

    if not df.empty:
        st.subheader("CURRENT HOLDINGS")
        df['Total Cost'] = df['amount'] * df['avg_price']
        st.table(df[['symbol', 'amount', 'avg_price', 'exit_target', 'Total Cost']])
        
        for _, row in df.iterrows():
            if st.button(f"🗑️ REMOVE {row['symbol']}", key=f"del_{row['symbol']}"):
                supabase.table("portfolio").delete().eq("symbol", row['symbol']).eq("trader_username", st.session_state.user).execute()
                st.rerun()
    else:
        st.info("No assets tracked in your private portfolio yet.")
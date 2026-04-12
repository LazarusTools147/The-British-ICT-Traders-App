import streamlit as st
import pandas as pd
from database import get_supabase

def render_dca_tab():
    st.header(f"📉 {st.session_state.user}'s PORTFOLIO & DCA TRACKER")
    st.write("Track long-term holdings and asset accumulation separate from active trading.")
    supabase = get_supabase()

    # --- 1. PRIVACY FILTERED DATA FETCH ---
    # This ensures your coins stay in your pocket and Fin's stay in his.
    try:
        response = supabase.table("portfolio").select("*").eq("trader_username", st.session_state.user).execute()
        df = pd.DataFrame(response.data)
    except Exception as e:
        st.error(f"SYSTEM_ERROR: Portfolio Sync Failed. {e}")
        df = pd.DataFrame()

    # --- 2. ASSET ENTRY FORM ---
    with st.expander("➕ ADD NEW ASSET TO PORTFOLIO"):
        with st.form("dca_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                symbol = st.text_input("ASSET SYMBOL (e.g. BTC, ETH, NQ)").upper().strip()
                amount = st.number_input("AMOUNT HELD / CONTRACTS", min_value=0.0, step=0.00001, format="%.5f")
            with c2:
                avg_price = st.number_input("AVERAGE ENTRY PRICE ($)", min_value=0.0, format="%.2f")
                target = st.number_input("LONG-TERM EXIT TARGET ($)", min_value=0.0, format="%.2f")
            
            if st.form_submit_button("SECURE TO PRIVATE PORTFOLIO"):
                if symbol and amount > 0:
                    data = {
                        "trader_username": st.session_state.user, # The Multi-User Owner Stamp
                        "symbol": symbol,
                        "amount": amount,
                        "avg_price": avg_price,
                        "exit_target": target
                    }
                    try:
                        # Upsert will update the amount if the symbol/user combo exists
                        supabase.table("portfolio").upsert(data).execute()
                        st.success(f"✔️ {symbol} Successfully Secured to your Vault.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Vault Entry Failed: {e}")
                else:
                    st.warning("Please provide a valid Symbol and Amount.")

    st.divider()

    # --- 3. PORTFOLIO DISPLAY & MANAGEMENT ---
    if not df.empty:
        st.subheader("CURRENT HOLDINGS")
        
        # Calculate Total Cost Basis for the portfolio
        df['Total Cost'] = df['amount'] * df['avg_price']
        
        # Display the data table with institutional formatting
        st.table(df[['symbol', 'amount', 'avg_price', 'exit_target', 'Total Cost']])
        
        # Metric summary at the bottom
        total_value = df['Total Cost'].sum()
        st.metric("Total Portfolio Basis", f"${round(total_value, 2)}")

        st.divider()
        st.subheader("ASSET MANAGEMENT")
        # Creating individual removal buttons for each asset
        for _, row in df.iterrows():
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.write(f"**{row['symbol']}** | Amount: {row['amount']} | Avg: ${row['avg_price']}")
            with col_b:
                if st.button(f"🗑️ PURGE {row['symbol']}", key=f"del_port_{row['symbol']}"):
                    try:
                        supabase.table("portfolio").delete().eq("symbol", row['symbol']).eq("trader_username", st.session_state.user).execute()
                        st.success(f"Purged {row['symbol']}.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Purge Failed: {e}")
    else:
        st.info(f"No assets are currently being tracked in the private portfolio for {st.session_state.user}.")
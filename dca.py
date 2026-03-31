import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_connection

def render_dca_tab():
    """
    Tab 6: Long-Term DCA & Portfolio Manager.
    Allows manual input of HTF entries to calculate and archive average cost.
    """
    st.header("📉 PORTFOLIO ARCHITECT: DCA CALCULATOR")
    
    # 1. LIVE CALCULATION ENGINE (Top Section)
    st.subheader("Position Simulator")
    with st.container():
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            curr_shares = st.number_input("CURRENT SHARES", min_value=0.0, step=0.1, value=0.0)
        with c2:
            curr_avg = st.number_input("CURRENT AVG PRICE", min_value=0.0, step=0.01, value=0.0)
        with c3:
            new_shares = st.number_input("ADDITIONAL SHARES", min_value=0.0, step=0.1, value=0.0)
        with c4:
            new_price = st.number_input("NEW ENTRY PRICE", min_value=0.0, step=0.01, value=0.0)

    # Calculation Logic
    total_shares = curr_shares + new_shares
    if total_shares > 0:
        total_cost = (curr_shares * curr_avg) + (new_shares * new_price)
        new_avg = total_cost / total_shares
        
        # UI Metrics for the simulation
        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric("NEW TOTAL SHARES", f"{total_shares}")
        with m2:
            # Shows how much you've successfully "Lowered the Bar"
            delta = new_avg - curr_avg if curr_avg > 0 else 0
            st.metric("NEW AVERAGE PRICE", f"${round(new_avg, 2)}", 
                      delta=f"{round(delta, 2)}" if curr_avg > 0 else None, delta_color="inverse")
        with m3:
            total_val = total_shares * new_price
            st.metric("CURRENT POSITION VALUE", f"${round(total_val, 2)}")
            
        st.divider()

        # 2. ARCHIVE TO DATABASE (Bottom Section)
        st.subheader("Vault the Position")
        with st.form("dca_vault_form", clear_on_submit=True):
            asset_name = st.text_input("ASSET NAME (e.g. BTC, ETH, TSLA)").upper()
            
            if st.form_submit_button("ARCHIVE TO PORTFOLIO"):
                if asset_name:
                    conn = get_connection()
                    # We use INSERT OR REPLACE to keep the asset unique in the portfolio
                    conn.execute('''
                        INSERT OR REPLACE INTO portfolio (asset_name, total_shares, avg_price, last_updated)
                        VALUES (?, ?, ?, ?)
                    ''', (asset_name, total_shares, new_avg, datetime.now().strftime("%Y-%m-%d")))
                    conn.commit()
                    conn.close()
                    st.success(f"✔️ {asset_name} POSITION UPDATED IN VAULT")
                else:
                    st.error("Please provide an Asset Name.")

    # 3. PORTFOLIO OVERVIEW
    st.divider()
    st.subheader("Current Holdings")
    conn = get_connection()
    portfolio_df = pd.read_sql("SELECT * FROM portfolio", conn)
    conn.close()

    if not portfolio_df.empty:
        st.dataframe(portfolio_df, hide_index=True, use_container_width=True)
    else:
        st.info("No long-term holdings archived yet.")
import streamlit as st
import pandas as pd
from database import get_supabase

def render_dca_tab():
    st.markdown('<h2 style="color: #FF4B4B;">📈 POSITION & DCA MANAGER</h2>', unsafe_allow_html=True)
    supabase = get_supabase()

    # 1. ADD NEW ENTRY FORM
    st.write("### ➕ ADD NEW ENTRY")
    with st.form("dca_entry_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        symbol = c1.text_input("STOCK SYMBOL (e.g. TSLA)").upper()
        entry_price = c2.number_input("ENTRY PRICE", min_value=0.01, step=0.01, format="%.2f")
        amount_inv = c3.number_input("TOTAL INVESTED ($)", min_value=1.0, step=10.0)
        
        if st.form_submit_button("📥 LOG ENTRY"):
            if symbol:
                shares = amount_inv / entry_price
                new_entry = {
                    "trader_username": st.session_state.user,
                    "symbol": symbol,
                    "entry_price": entry_price,
                    "amount": amount_inv,
                    "shares": shares,
                    "type": "DCA_LOG" # Tagging it for separation
                }
                try:
                    supabase.table("dca_vault").insert(new_entry).execute()
                    st.success(f"Entry Logged for {symbol}")
                    st.rerun()
                except Exception as e: st.error(f"Error: {e}")

    # 2. FETCH DATA & ORGANIZE BY SYMBOL
    try:
        res = supabase.table("dca_vault").select("*").eq("trader_username", st.session_state.user).execute()
        df = pd.DataFrame(res.data)
    except: df = pd.DataFrame()

    if df.empty:
        st.info("No positions found. Log your first buy above."); return

    # 3. POSITION DASHBOARD
    st.divider()
    symbols = df['symbol'].unique()
    
    for stock in symbols:
        stock_df = df[df['symbol'] == stock]
        
        # MATH: Weighted Average Entry Price
        total_invested = stock_df['amount'].sum()
        total_shares = stock_df['shares'].sum()
        avg_price = total_invested / total_shares if total_shares > 0 else 0
        
        with st.expander(f"📁 {stock} | {len(stock_df)} Entries | Avg: ${avg_price:.2f}", expanded=True):
            # Manual Price Update for P/L calculation
            current_price = st.number_input(f"LIVE {stock} PRICE ($)", key=f"price_{stock}", value=avg_price, step=0.01, format="%.2f")
            
            # Overall Stats
            p_l_pct = ((current_price - avg_price) / avg_price) * 100 if avg_price > 0 else 0
            color = "green" if p_l_pct >= 0 else "red"
            
            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("TOTAL INVESTED", f"${total_invested:,.2f}")
            sc2.metric("TOTAL SHARES", f"{total_shares:.4f}")
            sc3.metric("CURRENT P/L", f"{p_l_pct:.2f}%", delta=f"{p_l_pct:.2f}%", delta_color="normal")

            # Entry-by-Entry Breakdown
            st.write("**Entry History**")
            breakdown = []
            for i, row in stock_df.iterrows():
                # Individual entry increase vs current price
                entry_inc = ((current_price - row['entry_price']) / row['entry_price']) * 100
                breakdown.append({
                    "Date": row.get('created_at', 'Unknown')[:10],
                    "Buy Price": f"${row['entry_price']:.2f}",
                    "Amount": f"${row['amount']:.2f}",
                    "Shares": f"{row['shares']:.4f}",
                    "Entry P/L %": f"{entry_inc:.2f}%"
                })
            
            st.table(pd.DataFrame(breakdown))
            
            if st.button(f"🗑️ CLEAR {stock} POSITION", key=f"del_{stock}"):
                supabase.table("dca_vault").delete().eq("symbol", stock).eq("trader_username", st.session_state.user).execute()
                st.rerun()
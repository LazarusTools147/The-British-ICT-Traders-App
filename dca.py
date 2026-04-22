import streamlit as st
import pandas as pd
from datetime import datetime
from database import get_supabase

def render_dca_tab():
    st.markdown('<h2 style="color: #FF4B4B;">📈 POSITION & DCA MANAGER</h2>', unsafe_allow_html=True)
    supabase = get_supabase()

    # --- 1. ADD NEW ENTRY FORM ---
    st.write("### ➕ ADD NEW ENTRY")
    with st.form("dca_entry_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            symbol = st.text_input("STOCK SYMBOL (e.g. TSLA)").upper()
            v_date = st.date_input("INVESTMENT DATE", datetime.now())
        with c2:
            entry_price = st.number_input("ENTRY PRICE ($)", min_value=0.01, step=0.01, format="%.2f")
            amount_inv = st.number_input("TOTAL INVESTED ($)", min_value=1.0, step=10.0)
        
        if st.form_submit_button("📥 LOG ENTRY"):
            if symbol and entry_price > 0:
                shares = amount_inv / entry_price
                new_entry = {
                    "trader_username": st.session_state.user,
                    "symbol": symbol,
                    "investment_date": str(v_date),
                    "entry_price": float(entry_price),
                    "amount": float(amount_inv),
                    "shares": float(shares),
                    "type": "DCA_LOG"
                }
                try:
                    supabase.table("dca_vault").insert(new_entry).execute()
                    st.success(f"Entry Logged for {symbol}")
                    st.rerun()
                except Exception as e: st.error(f"Error: {e}")

    # --- 2. FETCH DATA ---
    try:
        res = supabase.table("dca_vault").select("*").eq("trader_username", st.session_state.user).execute()
        df = pd.DataFrame(res.data)
    except: df = pd.DataFrame()

    if df.empty:
        st.info("No positions found. Log your first buy above."); return

    # --- 3. POSITION DASHBOARD & EDITOR ---
    st.divider()
    symbols = sorted(df['symbol'].unique())
    
    for stock in symbols:
        stock_df = df[df['symbol'] == stock].sort_values('investment_date', ascending=False)
        
        total_invested = stock_df['amount'].sum()
        total_shares = stock_df['shares'].sum()
        
        # BREAK-EVEN CALCULATION
        break_even_price = total_invested / total_shares if total_shares > 0 else 0
        
        with st.expander(f"📁 {stock} | Total Invested: ${total_invested:,.2f}", expanded=True):
            current_price = st.number_input(f"LIVE {stock} PRICE ($)", key=f"price_{stock}", value=break_even_price, step=0.01, format="%.2f")
            
            p_l_pct = ((current_price - break_even_price) / break_even_price) * 100 if break_even_price > 0 else 0
            p_l_cash = (current_price * total_shares) - total_invested
            
            sc1, sc2, sc3, sc4 = st.columns(4)
            sc1.metric("BREAK-EVEN PRICE", f"${break_even_price:.2f}")
            sc2.metric("TOTAL SHARES", f"{total_shares:.4f}")
            sc3.metric("CURRENT P/L %", f"{p_l_pct:.2f}%", delta=f"{p_l_pct:.2f}%")
            sc4.metric("P/L CASH ($)", f"${p_l_cash:,.2f}")

            st.write("---")
            st.write("**Entry History & Editor**")
            
            for _, row in stock_df.iterrows():
                entry_inc = ((current_price - row['entry_price']) / row['entry_price']) * 100
                
                if st.session_state.get('editing_dca_id') == row['id']:
                    with st.form(f"edit_dca_{row['id']}"):
                        ec1, ec2, ec3 = st.columns(3)
                        e_date = ec1.date_input("EDIT DATE", value=pd.to_datetime(row['investment_date']))
                        e_price = ec2.number_input("EDIT PRICE", value=float(row['entry_price']))
                        e_amt = ec3.number_input("EDIT AMOUNT", value=float(row['amount']))
                        
                        if st.form_submit_button("💾 SAVE CHANGES"):
                            e_shares = e_amt / e_price
                            up_data = {
                                "investment_date": str(e_date),
                                "entry_price": float(e_price),
                                "amount": float(e_amt),
                                "shares": float(e_shares)
                            }
                            supabase.table("dca_vault").update(up_data).eq("id", row['id']).execute()
                            st.session_state.editing_dca_id = None
                            st.rerun()
                    if st.button("❌ CANCEL", key=f"can_{row['id']}"):
                        st.session_state.editing_dca_id = None
                        st.rerun()
                else:
                    c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
                    c1.write(f"📅 **{row['investment_date']}**")
                    c2.write(f"💵 ${row['entry_price']:.2f} | {row['shares']:.2f} Shrs")
                    c3.write(f"📈 Entry P/L: {entry_inc:.2f}%")
                    if c4.button("✏️", key=f"ed_btn_{row['id']}"):
                        st.session_state.editing_dca_id = row['id']
                        st.rerun()

            st.write("---")
            if st.button(f"🗑️ NUKE {stock} POSITION", key=f"del_{stock}"):
                supabase.table("dca_vault").delete().eq("symbol", stock).eq("trader_username", st.session_state.user).execute()
                st.rerun()
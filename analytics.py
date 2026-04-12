import streamlit as st
import pandas as pd
import plotly.express as px

def render_analytics(df, label):
    st.header(f"📊 {label} PERFORMANCE ANALYTICS")
    
    if df.empty:
        st.info("Log trades to generate data.")
        return

    # --- 1. CORE METRICS ---
    c1, c2, c3, c4 = st.columns(4)
    total_trades = len(df)
    wins = len(df[df['result'] == 'WIN'])
    win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
    total_rr = df['rr'].sum()

    with c1: st.metric("Total Trades", total_trades)
    with c2: st.metric("Win Rate", f"{round(win_rate, 1)}%")
    with c3: st.metric("Total RR", f"{round(total_rr, 2)}R")
    with c4: st.metric("Avg RR/Trade", f"{round(total_rr/total_trades, 2)}R" if total_trades > 0 else "0R")

    # --- 2. DEEP DIVES ---
    st.divider()
    tabs = st.tabs(["💎 WINNERS", "🧨 LOSSES", "⚖️ BREAKEVEN", "🧠 HINDSIGHT", "📰 NEWS_IMPACT"])

    with tabs[0]:
        winners = df[df['result'] == 'WIN']
        if not winners.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Best Models")
                st.bar_chart(winners['model_name'].value_counts())
            with col2:
                st.subheader("Wins by Session")
                st.bar_chart(winners['session'].value_counts())
        else: st.info("No winners yet.")

    with tabs[1]:
        losses = df[df['result'] == 'LOSS']
        if not losses.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Model Failure Rate")
                st.bar_chart(losses['model_name'].value_counts())
            with col2:
                st.subheader("Losses by Session")
                st.bar_chart(losses['session'].value_counts())
        else: st.info("No losses yet.")

    with tabs[2]:
        be_trades = df[df['result'] == 'BE']
        if not be_trades.empty:
            st.bar_chart(be_trades['model_name'].value_counts())
        else: st.info("No BE trades recorded.")

    with tabs[3]:
        hindsight = df[df['hindsight'] == True]
        if not hindsight.empty:
            st.write(f"Study Count: {len(hindsight)}")
            st.bar_chart(hindsight['model_name'].value_counts())
        else: st.info("No hindsight trades marked.")

    with tabs[4]:
        if 'news_impact' in df.columns:
            st.subheader("Trade Volume by News Impact")
            fig = px.pie(df, names='news_impact', title="News Impact Distribution")
            st.plotly_chart(fig, use_container_width=True)
        else: st.info("News data not available.")

    # --- 3. EQUITY CURVE ---
    st.divider()
    st.subheader("📈 CUMULATIVE RR GROWTH")
    df = df.sort_values('date')
    df['cum_rr'] = df['rr'].cumsum()
    fig = px.line(df, x='date', y='cum_rr', title="RR Over Time")
    st.plotly_chart(fig, use_container_width=True)
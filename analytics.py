import streamlit as st
import pandas as pd
import plotly.express as px

def render_analytics(df, label):
    st.header(f"📊 {label} PERFORMANCE ANALYTICS")
    st.write(f"Comprehensive statistical breakdown for {st.session_state.user}.")
    
    if df.empty:
        st.info("Log trades in The Forge to generate performance data.")
        return

    # --- 1. CORE PERFORMANCE METRICS ---
    c1, c2, c3, c4 = st.columns(4)
    total_trades = len(df)
    wins = len(df[df['result'] == 'WIN'])
    losses = len(df[df['result'] == 'LOSS'])
    be_trades = len(df[df['result'] == 'BE'])
    
    win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0
    total_rr = df['rr'].sum()
    avg_rr = total_rr / total_trades if total_trades > 0 else 0

    with c1: 
        st.metric("Total Executions", total_trades)
    with c2: 
        st.metric("Win Rate", f"{round(win_rate, 1)}%", delta=f"{wins}W / {losses}L")
    with c3: 
        st.metric("Total RR Growth", f"{round(total_rr, 2)}R")
    with c4: 
        st.metric("Expectancy (Avg RR)", f"{round(avg_rr, 2)}R")

    # --- 2. THE DEEP DIVE TABS ---
    # We are including every specific study category you requested
    st.divider()
    tabs = st.tabs(["💎 WINNERS", "🧨 LOSSES", "⚖️ BREAKEVEN", "🧠 HINDSIGHT", "📰 NEWS_IMPACT"])

    with tabs[0]:
        st.subheader("Winner Distribution")
        winners = df[df['result'] == 'WIN']
        if not winners.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Top Performing Models (Wins)**")
                st.bar_chart(winners['model_name'].value_counts())
            with col2:
                st.write("**Winning Sessions**")
                st.bar_chart(winners['session'].value_counts())
        else:
            st.info("No winners recorded in this dataset yet.")

    with tabs[1]:
        st.subheader("Loss Distribution")
        loss_df = df[df['result'] == 'LOSS']
        if not loss_df.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Highest Failure Models**")
                st.bar_chart(loss_df['model_name'].value_counts())
            with col2:
                st.write("**Losing Sessions**")
                st.bar_chart(loss_df['session'].value_counts())
        else:
            st.info("No losses recorded. Keep protecting that capital.")

    with tabs[2]:
        st.subheader("Breakeven Analysis")
        be_df = df[df['result'] == 'BE']
        if not be_df.empty:
            st.write("**BE Frequency by Model**")
            # Bar chart showing which models result in the most BEs
            st.bar_chart(be_df['model_name'].value_counts())
            st.write(f"Total Breakeven Trades: {len(be_df)}")
        else:
            st.info("No BE trades recorded.")

    with tabs[3]:
        st.subheader("🧠 HINDSIGHT & STUDY VOLUME")
        # Filtering for trades where the Hindsight checkbox was ticked in the Forge
        hindsight_df = df[df.get('hindsight', False) == True]
        if not hindsight_df.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Studies per Model**")
                st.bar_chart(hindsight_df['model_name'].value_counts())
            with col2:
                st.write(f"**Total Hindsight Studies:** {len(hindsight_df)}")
                # Show distribution of results within hindsight studies
                st.write("**Hindsight Outcomes**")
                st.bar_chart(hindsight_df['result'].value_counts())
        else:
            st.info("No trades marked as 'Hindsight' in The Forge. Use this for chart studies.")

    with tabs[4]:
        st.subheader("News Impact Analysis")
        if 'news_impact' in df.columns:
            news_counts = df['news_impact'].value_counts().reset_index()
            news_counts.columns = ['Impact Level', 'Count']
            fig = px.pie(
                news_counts, 
                values='Count', 
                names='Impact Level', 
                title="Trade Distribution by News Volatility",
                template="plotly_dark",
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("News Impact data column missing in database.")

    # --- 3. EQUITY CURVE (RR GROWTH OVER TIME) ---
    st.divider()
    st.subheader("📈 CUMULATIVE RR GROWTH CURVE")
    
    # Sorting to ensure the time-series line is accurate
    df['date'] = pd.to_datetime(df['date'])
    curve_df = df.sort_values('date').copy()
    curve_df['cum_rr'] = curve_df['rr'].cumsum()
    
    fig_curve = px.line(
        curve_df, 
        x='date', 
        y='cum_rr', 
        title=f"Cumulative RR Growth — {st.session_state.user}",
        labels={'cum_rr': 'Cumulative RR', 'date': 'Trade Date'},
        markers=True,
        template="plotly_dark"
    )
    fig_curve.update_traces(line_color='#00FF00', line_width=2)
    st.plotly_chart(fig_curve, use_container_width=True)
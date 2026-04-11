import streamlit as st
import plotly.express as px
import pandas as pd

def render_analytics(df, suffix):
    """
    Performance visualization engine for Live and Test data.
    """
    if df.empty:
        st.info(f"📊 NO {suffix} DATA CURRENTLY IN VAULT.")
        return

    # --- 1. GLOBAL KPI SECTION ---
    st.markdown(f"## 📈 {suffix} GLOBAL KPI")
    k1, k2, k3, k4 = st.columns(4)
    
    with k1: 
        win_count = len(df[df['result'] == 'WIN'])
        win_rate = (win_count / len(df)) * 100
        st.metric("WIN RATE", f"{round(win_rate, 1)}%")
    with k2: 
        st.metric("AVG DURATION", f"{round(df['duration_mins'].mean(), 1)}m")
    with k3: 
        st.metric("AVG RISK %", f"{round(df['risk_pc'].mean(), 2)}%")
    with k4: 
        st.metric("AVG RR RATIO", f"{round(df['rr'].mean(), 2)}R")

    st.divider()

    # --- 2. MAIN CHARTS ---
    # institutional color coding
    color_map = {'WIN': '#00ff00', 'LOSS': '#ff0000', 'BE': '#FF8C00'}
    
    chart_col, pie_col = st.columns([3, 1])
    
    with chart_col:
        st.plotly_chart(
            px.bar(
                df.sort_values('entry_time'), 
                x='entry_time', 
                y='rr', 
                color='result', 
                color_discrete_map=color_map,
                title=f"{suffix}: RR Pulse Over Time"
            ).update_layout(bargap=0.3), 
            use_container_width=True, 
            key=f"bar_chart_{suffix}"
        )
        
    with pie_col:
        st.plotly_chart(
            px.pie(
                df, 
                names='result', 
                hole=0.5, 
                color='result', 
                color_discrete_map=color_map,
                title="Outcome Mix"
            ), 
            use_container_width=True, 
            key=f"pie_chart_{suffix}"
        )

    # --- 3. SEGMENTED DEEP-DIVES ---
    def render_deep_dive(result_type, label, emoji):
        segment_df = df[df['result'] == result_type]
        if segment_df.empty:
            return
            
        with st.expander(f"{emoji} {label} DEEP-DIVE"):
            col_left, col_right = st.columns([3, 1])
            
            with col_left:
                st.plotly_chart(
                    px.bar(
                        segment_df.sort_values('entry_time'), 
                        x='entry_time', 
                        title="Entry Time Precision"
                    ), 
                    use_container_width=True, 
                    key=f"time_dist_{result_type}_{suffix}"
                )
            with col_right:
                st.plotly_chart(
                    px.pie(
                        segment_df, 
                        names='model_var', 
                        title="Variation Edge"
                    ), 
                    use_container_width=True, 
                    key=f"var_dist_{result_type}_{suffix}"
                )
            
            # Symmetrical breakdown rows
            row_c1, row_c2, row_c3, row_c4 = st.columns(4)
            pie_config = dict(hole=0.4, width=220, height=220)
            
            with row_c1: 
                st.plotly_chart(px.pie(segment_df, names='market', title="Markets", **pie_config), use_container_width=True, key=f"mkt_{result_type}_{suffix}")
            with row_c2: 
                st.plotly_chart(px.pie(segment_df, names='session', title="Sessions", **pie_config), use_container_width=True, key=f"sess_{result_type}_{suffix}")
            with row_c3: 
                st.plotly_chart(px.pie(segment_df, names='entry_tf', title="Timeframes", **pie_config), use_container_width=True, key=f"tf_{result_type}_{suffix}")
            with row_c4: 
                st.plotly_chart(px.pie(segment_df, names='news_impact', title="News", **pie_config), use_container_width=True, key=f"nws_{result_type}_{suffix}")

    # Render segments for Winners, BE, and Losses
    render_deep_dive("WIN", "WINNERS", "🏆")
    render_deep_dive("BE", "BREAK EVEN", "🛡️")
    render_deep_dive("LOSS", "LOSSES", "💀")

    # --- 4. HINDSIGHT ANALYSIS (BACKTEST EXCLUSIVE) ---
    if suffix == "TEST":
        st.divider()
        st.subheader("👁️ HINDSIGHT MODEL AUDIT")
        with st.expander("OPEN HINDSIGHT DEEP-DIVE"):
            st.info("This section analyzes only 'WIN' outcomes from backtesting to reveal the 'Perfect' model execution window.")
            
            hindsight_df = df[df['result'] == 'WIN']
            
            if not hindsight_df.empty:
                h_col1, h_col2 = st.columns(2)
                with h_col1:
                    st.plotly_chart(
                        px.histogram(
                            hindsight_df, 
                            x="entry_time", 
                            title="Highest Probability Time Windows",
                            color_discrete_sequence=['#FFD700'] # Gold for hindsight
                        ), 
                        use_container_width=True, 
                        key="hindsight_hist_time"
                    )
                with h_col2:
                    st.plotly_chart(
                        px.pie(
                            hindsight_df, 
                            names="model_var", 
                            title="Most Reliable Model Variations",
                            hole=0.4
                        ), 
                        use_container_width=True, 
                        key="hindsight_pie_var"
                    )
            else:
                st.write("Logged 'WIN' trades in the TEST tab will generate this hindsight data.")
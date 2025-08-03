import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pytrends.request import TrendReq

# Init
st.set_page_config(layout="wide")
pytrends = TrendReq(hl='en-US', tz=360)

# UI Inputs
st.title("🔍 Google Trends Keyword Explorer")

keywords_input = st.text_input("Enter keywords (comma-separated):", "event management, event planning, event planner")
keywords = [kw.strip() for kw in keywords_input.split(',') if kw.strip()]
timeframes = ['today 5-y', 'today 12-m', 'today 3-m', 'today 1-m']
timeframe = st.selectbox("Select timeframe:", timeframes)
geo = st.text_input("Enter Geo code (e.g., US, IN) or leave blank for worldwide:", "")
category = '0'  # All
gprop = ''      # Web search

# Button to start
if st.button("Analyze"):
    if not keywords:
        st.warning("Enter at least one keyword.")
    else:
        # INTEREST OVER TIME for all keywords
        pytrends.build_payload(keywords, cat=category, timeframe=timeframe, geo=geo, gprop=gprop)
        trend_data = pytrends.interest_over_time()

        if trend_data.empty:
            st.error("No data returned. Try a different geo or timeframe.")
        else:
            st.subheader("📈 Interest Over Time")
            fig, ax = plt.subplots(figsize=(14, 6))
            for kw in keywords:
                if kw in trend_data.columns:
                    ax.plot(trend_data.index, trend_data[kw], label=kw)
            ax.set_title("Search Trends Over Time")
            ax.set_xlabel("Date")
            ax.set_ylabel("Interest")
            ax.legend()
            ax.grid(True)
            st.pyplot(fig)

            st.download_button(
                "📥 Download Trend Data",
                data=trend_data.to_csv().encode('utf-8'),
                file_name='interest_over_time.csv',
                mime='text/csv'
            )

        # === DASHBOARD PER KEYWORD ===
        st.subheader("📊 Per-Keyword Trend Dashboard")

        for keyword in keywords:
            with st.expander(f"🔍 {keyword}"):
                try:
                    # Build individual payload
                    pytrends.build_payload([keyword], cat=category, timeframe='today 5-y', geo=geo, gprop=gprop)
                    data = pytrends.interest_over_time()
                    if keyword not in data.columns or data.empty:
                        st.warning(f"No data for {keyword}")
                        continue

                    # --- Trend classification ---
                    five_year_avg = round(data[keyword].mean(), 2)
                    last_year_avg = round(data[keyword][-52:].mean(), 2)
                    change = round(((last_year_avg / five_year_avg) - 1) * 100, 2) if five_year_avg else 0.0

                    # === BOUNDED-RANGE CLASSIFICATION LOGIC ===
                    if five_year_avg > 75:
                        if abs(change) <= 5:
                            status = "Stable"
                        elif change > 5:
                            status = "Stable & Increasing"
                        elif change < -5:
                            status = "Stable & Decreasing"

                    elif 60 < five_year_avg <= 75:
                        if abs(change) <= 15:
                            status = "Relatively Stable"
                        elif change > 15:
                            status = "Relatively Stable & Increasing"
                        elif change < -15:
                            status = "Relatively Stable & Decreasing"

                    elif 20 < five_year_avg <= 60:
                        if abs(change) <= 15:
                            status = "Seasonal"
                        elif change > 15:
                            status = "Trending"
                        elif change < -15:
                            status = "Significantly Decreasing"

                    elif 5 < five_year_avg <= 20:
                        if abs(change) <= 15:
                            status = "Cyclical"
                        elif change > 15:
                            status = "New & Trending"
                        elif change < -15:
                            status = "Declining"

                    elif 0 < five_year_avg <= 5:
                        if change > 15:
                            status = "Very New & Spiking"
                        elif change < -15:
                            status = "Fading from Low Interest"
                        else:
                            status = "Minimal but Steady"

                    else:
                        status = "Needs Review"

                    # --- Trend chart ---
                    fig2, ax2 = plt.subplots(figsize=(12, 4))
                    ax2.plot(data.index, data[keyword], color='tab:blue')
                    ax2.set_title(f"{keyword} - Interest Over Time")
                    ax2.set_ylabel("Interest")
                    ax2.grid(True)
                    st.pyplot(fig2)

                    # --- Regional interest ---
                    region_data = pytrends.interest_by_region(resolution='COUNTRY', inc_low_vol=True, inc_geo_code=False)
                    if not region_data.empty and keyword in region_data.columns:
                        top_regions = region_data[[keyword]].sort_values(by=keyword, ascending=False).head(10)
                        st.markdown("**🌍 Top Regions**")
                        st.bar_chart(top_regions)

                        st.download_button(
                            f"📥 Download Region Data for {keyword}",
                            data=top_regions.to_csv().encode('utf-8'),
                            file_name=f"{keyword}_regions.csv",
                            mime='text/csv'
                        )

                    # --- Related queries ---
                    st.markdown("**🔗 Related Queries**")
                    related = pytrends.related_queries()
                    rising_df = related.get(keyword, {}).get('rising')
                    top_df = related.get(keyword, {}).get('top')

                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("**📈 Rising**")
                        if rising_df is not None:
                            st.dataframe(rising_df)
                        else:
                            st.write("No rising queries found.")

                    with col2:
                        st.markdown("**⭐ Top**")
                        if top_df is not None:
                            st.dataframe(top_df)
                        else:
                            st.write("No top queries found.")

                    # --- Summary box ---
                    st.markdown("### 🧮 Summary")
                    st.metric("5-Year Avg", five_year_avg)
                    st.metric("Last Year Avg", last_year_avg)
                    st.metric("Change (%)", change)
                    st.success(f"📌 Classification: **{status}**")

                except Exception as e:
                    st.error(f"Error for keyword '{keyword}': {e}")

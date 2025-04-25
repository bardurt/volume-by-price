import streamlit as st
import matplotlib.pyplot as plt
from datetime import datetime
from volume_by_price import (
    fetch_data_crypto,
    fetch_data_av,
    calculate_volume_by_price,
    calculate_monthly_changes,
    calculate_daily_percentage_changes,
    find_closest_year
)

st.set_page_config(page_title="Volume by Price", layout="wide")
st.title("📊 Volume by Price + Seasonality Viewer")

symbol = st.text_input("Enter Symbol (e.g., BTC, AAPL)", "BTC")
asset_type = st.radio("Asset Type", ["Crypto", "Stock"])
method = st.selectbox("Similarity Method", ["euclidean", "pearson"])

if st.button("Analyze"):
    if asset_type == "Crypto":
        rows = fetch_data_crypto(symbol)
    else:
        api_key = st.secrets["av_api_key"]
        rows = fetch_data_av(symbol, api_key)

    if not rows or len(rows) < 3:
        st.warning("Not enough data or error fetching it.")
    else:
        price_dict = calculate_volume_by_price(rows)
        monthly_changes = calculate_monthly_changes(rows)
        daily_changes = calculate_daily_percentage_changes(rows)
        year_end = datetime.now().year
        current_year_changes, closest_year_changes, closest_year = find_closest_year(
            daily_changes, year_end, method
        )

        st.subheader("🔹 Volume by Price")
        fig1, ax1 = plt.subplots()
        prices, volumes = zip(*sorted(price_dict.items()))
        ax1.barh(prices, volumes, color='skyblue')
        st.pyplot(fig1)

        st.subheader("🔸 Monthly Bias")
        fig2, ax2 = plt.subplots()
        months = [f"{i:02}" for i in range(1, 13)]
        month_vals = [monthly_changes.get(m, 0) for m in months]
        ax2.bar(months, month_vals, color='orange')
        st.pyplot(fig2)

        st.subheader(f"🔁 Seasonality: {year_end} vs {closest_year}")
        fig3, ax3 = plt.subplots()
        ax3.plot(current_year_changes, label=str(year_end))
        ax3.plot(closest_year_changes, label=str(closest_year))
        ax3.legend()
        st.pyplot(fig3)

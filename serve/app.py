import streamlit as st
import pandas as pd
import psycopg2 # pyright: ignore[reportMissingModuleSource] #runs in docker container, need to install psycopg2-binary in requirements.txt
from dotenv import load_dotenv
import os

# https://www.datacamp.com/tutorial/streamlit?utm_aid=196565213035&utm_loc=9215245-&utm_mtd=p-c&utm_kw=wordcloud%20python
# https://docs.streamlit.io/develop/api-reference/data/st.dataframe

# conn = psycopg2.connect(
#     host="localhost",
#     port="5432",
#     database="fx_pipeline",
#     user="postgres",
#     password="secret"
# )

load_dotenv()

conn = psycopg2.connect(
    host=os.environ.get("POSTGRES_HOST"),
    port="5432",
    database=os.environ.get("POSTGRES_DB"),
    user=os.environ.get("POSTGRES_USER"),
    password=os.environ.get("POSTGRES_PASSWORD"),
)




# fetch_query = "select * from pct_change_view"  # Fetch the last 10 rows from the table

# st.title("ForeX Pipeline")
# df = pd.read_sql(fetch_query, conn)  
# st.dataframe(df)  # Display the DataFrame in Streamlit
#streamlit run app.py

st.title("ForeX Pipeline")
df_pct_change = pd.read_sql("select * from pct_change_view", conn)
df_volatility = pd.read_sql("select * from volatility_view", conn)
df_trend = pd.read_sql("select * from trend_view ", conn)
df_trend["date"] = pd.to_datetime(df_trend["date"]) #added to run filter range in "Trend tab"
df_correlation = pd.read_sql("select * from correlation_view", conn)

tab1, tab2, tab3, tab4 = st.tabs(["Price Change", "Volatility", "Trend", "Correlation Matrix"])
with tab1:
    st.markdown("### Price Change")
    st.markdown("How much each currency gained or lost against the EUR from the first to the last available date in the dataset.")
    st.markdown(f"Data covers **{df_pct_change['start_date'].iloc[0]}** to **{df_pct_change['end_date'].iloc[0]}**.")
    
    biggest = df_pct_change.loc[df_pct_change["pct_change"].abs().idxmax()]
    st.markdown(f"For example, **{biggest['quote']}** shows the largest movement against the EUR in this dataset, at **{biggest['pct_change']:.2f}%** — a bigger absolute number here means a bigger shift in value over the period.")
    
    if biggest['pct_change'] > 0:
        st.markdown(f"**In other words:** {biggest['quote']} has lost value against the EUR — you now need more {biggest['quote']} to buy 1 EUR than at the start of the period. It buys less than it used to, compared to a currency that held steady or gained.")
    else:
        st.markdown(f"**In other words:** {biggest['quote']} has gained value against the EUR — you now need fewer {biggest['quote']} to buy 1 EUR than at the start of the period. It buys more than it used to, compared to a currency that held steady or lost.")
    
    st.write(df_pct_change)
    df_chart = df_pct_change.rename(columns={"quote": "Currency", "pct_change": "Price Change (%)"})
    st.bar_chart(df_chart, x="Currency", y="Price Change (%)")
    
    st.caption("Positive bars mean the currency weakened against the EUR over the period (needs more units per EUR); negative bars mean it strengthened.")
with tab2:
    st.markdown("### Volatility")
    st.markdown("How much each rate fluctuates over time, measured as coefficient of variation (standard deviation divided by the mean) — this makes currencies with very different scales, like JPY and GBP, directly comparable.")
    st.markdown("A higher number means the rate swings more day to day — harder to predict or plan around, more exchange-rate risk if you're holding or converting that currency. A lower number means the rate is more stable and predictable.")
    
    most_volatile = df_volatility.loc[df_volatility["volatility"].idxmax()]
    least_volatile = df_volatility.loc[df_volatility["volatility"].idxmin()]
    st.markdown(f"Here, **{most_volatile['quote']}** is the most volatile pair and **{least_volatile['quote']}** the most stable, meaning {most_volatile['quote']}'s value against the EUR jumps around more unpredictably day to day, while {least_volatile['quote']} barely moves in comparison. If you needed to exchange money on a random day, {most_volatile['quote']}'s rate on that day would be much harder to guess in advance than {least_volatile['quote']}'s.")
    
    st.write(df_volatility)
    df_chart = df_volatility.rename(columns={"quote": "Currency", "volatility": "Volatility"})
    st.bar_chart(df_chart, x="Currency", y="Volatility")
    
    st.caption("This is calculated over the full dataset, not the filtered date range on the Trend tab — it reflects overall historical volatility, not just recent movement.")
with tab3:
    st.markdown("### Trend")
    st.markdown("#### How a currency's rate against the EUR moves day by day")
    st.markdown("No averaging or aggregation here — this shows the raw daily rate, so you can see exactly when and how much a currency moved over the selected period.")
    
    st.write(df_trend)
    df_chart_trend = df_trend.rename(columns={"quote": "Currency"})
    active_cur = st.selectbox("Select Currency", df_trend["quote"].unique())
    
    data_min = df_trend["date"].min()
    data_max = df_trend["date"].max()
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start date", value=data_min, min_value=data_min, max_value=data_max)
    with col2:
        end_date = st.date_input("End date", value=data_max, min_value=data_min, max_value=data_max)

    st.markdown(f"You're viewing **{active_cur}** between **{start_date}** and **{end_date}**. A rising line means {active_cur} is weakening against the EUR in this window (more {active_cur} needed per EUR); a falling line means it's strengthening.")

    df_trend_filtered = df_trend[
        (df_trend["quote"] == active_cur) &
        (df_trend["date"] >= pd.to_datetime(start_date)) &
        (df_trend["date"] <= pd.to_datetime(end_date))
]

    st.line_chart(df_trend_filtered.set_index("date")["rate"]) #range filter
    
    st.caption("Daily rate for the selected currency and date range — use this to spot shifts or patterns over time.")
with tab4:
    st.markdown("### Correlation Matrix")
    st.markdown("How closely each pair of currencies moves together against the EUR. Values range from -1 to +1.")
    
    st.markdown("""
- **Close to +1** — the two currencies tend to move in the same direction at the same time.
- **Close to -1** — they tend to move in opposite directions: when one strengthens against the EUR, the other tends to weaken.
- **Close to 0** — little to no relationship between their movements.
""")
    st.markdown("This matters for risk: holding two currencies that move together (high positive correlation) doesn't protect you from EUR movements — they gain or lose value together. A negative correlation is what actually offsets risk, since a drop in one tends to come with a rise in the other.")
    
    # Mirror: currency_a/currency_b swapped, to fill the lower triangle
    df_mirror = df_correlation.rename(
        columns={"currency_a": "currency_b", "currency_b": "currency_a"}
    )

    # Diagonal: each currency correlated with itself = 1.0
    currencies = pd.unique(df_correlation[["currency_a", "currency_b"]].values.ravel())
    df_diagonal = pd.DataFrame({
        "currency_a": currencies,
        "currency_b": currencies,
        "correlation": 1.0,
    })

    # Combine all three pieces, then change into a 5x5 grid
    df_corr_full = pd.concat([df_correlation, df_mirror, df_diagonal], ignore_index=True)
    corr_matrix = df_corr_full.pivot(index="currency_a", columns="currency_b", values="correlation")

    st.dataframe(corr_matrix.style.background_gradient(cmap="RdBu", vmin=-1, vmax=1))
    
    most_neg = df_correlation.loc[df_correlation["correlation"].idxmin()]
    st.markdown(f"For example, **{most_neg['currency_a']}** and **{most_neg['currency_b']}** currently show the strongest negative correlation in this dataset (**{most_neg['correlation']:.2f}**) — consistent with CHF's reputation as a 'safe haven' currency that tends to move opposite to riskier ones. This will shift as more data comes in, so the specific pair and value here may change over time.")
    
    st.caption("How each currency pair moves together. Negative values — see CHF — mean opposite movement, a classic sign of safe-haven behavior.")

import streamlit as st
import pandas as pd
import psycopg2 # pyright: ignore[reportMissingModuleSource] #runs in docker container, need to install psycopg2-binary in requirements.txt

# https://www.datacamp.com/tutorial/streamlit?utm_aid=196565213035&utm_loc=9215245-&utm_mtd=p-c&utm_kw=wordcloud%20python
# https://docs.streamlit.io/develop/api-reference/data/st.dataframe

conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="fx_pipeline",
    user="postgres",
    password="secret"
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
    st.write(df_pct_change)
    df_chart = df_pct_change.rename(columns={"quote": "Currency", "pct_change": "Price Change (%)"})
    st.bar_chart(df_chart, x="Currency", y="Price Change (%)")
    
with tab2:
    st.write(df_volatility)
    df_chart_vol = df_volatility.rename(columns={"quote": "Currency", "volatility": "Volatility"})
    st.bar_chart(df_chart_vol, x="Currency", y="Volatility")
with tab3:
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

df_trend_filtered = df_trend[
    (df_trend["quote"] == active_cur) &
    (df_trend["date"] >= pd.to_datetime(start_date)) &
    (df_trend["date"] <= pd.to_datetime(end_date))
]

st.line_chart(df_trend_filtered.set_index("date")["rate"]) #range filter
with tab4:
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

    # Combine all three pieces, then pivot into a 5x5 grid
    df_corr_full = pd.concat([df_correlation, df_mirror, df_diagonal], ignore_index=True)
    corr_matrix = df_corr_full.pivot(index="currency_a", columns="currency_b", values="correlation")

    st.dataframe(corr_matrix.style.background_gradient(cmap="RdBu", vmin=-1, vmax=1))

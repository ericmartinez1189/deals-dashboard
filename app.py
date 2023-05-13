import pandas as pd
import streamlit as st
import plotly.express as px
import os

st.set_page_config(page_title="Deals Dashboard",
                   page_icon=":bar_chart:",
                   layout="wide"
                   )

@st.cache_data
def get_deals_from_sheets():
    sheet_id_deccy = os.environ['SHEET_ID_VA_DECCY']
    df_deccy = pd.read_csv(f"https://docs.google.com/spreadsheets/d/{sheet_id_deccy}/export?format=csv")

    sheet_id_liezel = os.environ['SHEET_ID_VA_LIEZEL']
    df_liezel = pd.read_csv(f"https://docs.google.com/spreadsheets/d/{sheet_id_liezel}/export?format=csv")

    # add a new column with the same value for each row
    df_deccy = df_deccy.assign(VA_Name='Deccy')
    df_liezel = df_liezel.assign(VA_Name='Liezel')

    df_data = pd.concat([df_deccy, df_liezel], ignore_index=True)
    return df_data

@st.cache_data
def get_purch_from_sheets():
    sheet_id_purch = "1yqwcodAe1Fypk3SdksajOIe_VAUPY27xaAOGyA4cFiE"
    df_purch_log_data = pd.read_csv(f"https://docs.google.com/spreadsheets/d/{sheet_id_purch}/export?format=csv")
    # convert the 'ORDER (DATE)' column to datetime format
    df_purch_log_data['ORDER (DATE)'] = pd.to_datetime(df_purch_log_data['ORDER (DATE)'], format='%Y-%m-%d')
    return df_purch_log_data


df_deals = get_deals_from_sheets()
df_purch = get_purch_from_sheets()


st.sidebar.header("Please filter here:")
status = st.sidebar.multiselect(
    "Select the status:",
    options=df_deals["Status"].unique(),
    default=df_deals["Status"].unique()
)

name = st.sidebar.multiselect(
    "Select the Name:",
    options=df_deals["VA_Name"].unique(),
    default=df_deals["VA_Name"].unique()
)

df_selection = df_deals.query(
    "Status == @status & VA_Name == @name"
)

# ------- Main Page ------
st.title(":bar_chart: Deals Dashboard")
st.markdown("##")


# formatting columns correctly

# convert the 'date' column to datetime format
df_selection['Date'] = pd.to_datetime(df_selection['Date'], format='%Y-%m-%d')

# TOP KPIS

total_number_of_deals = int(df_selection["ASIN"].count())

status_filter_ordered = df_selection["Status"] == "Ordered"
filtered_df_ordered = df_selection[status_filter_ordered]
total_number_of_ordered = int(filtered_df_ordered["ASIN"].count())

status_filter_rejected = df_selection["Status"] == "Rejected"
filtered_df_rejected = df_selection[status_filter_rejected]
total_number_of_rejected = int(filtered_df_rejected["ASIN"].count())

status_filter_cart = df_selection["Status"] == "Added to cart"
filtered_df_cart = df_selection[status_filter_cart]
total_number_of_cart = int(filtered_df_cart["ASIN"].count())

total_number_of_hold = total_number_of_deals-total_number_of_ordered-total_number_of_rejected-total_number_of_cart
success_rate = round((total_number_of_ordered + total_number_of_cart)/total_number_of_deals*100)

left_column, middle_column, right_column = st.columns(3)

with left_column:
    st.subheader(f"New Deals: {total_number_of_deals} ")
    st.subheader(f"Success rate: {success_rate} %")
with middle_column:
    st.subheader(f"Ordered: {total_number_of_ordered} ")
    st.subheader(f"Added to cart: {total_number_of_cart} ")
with right_column:
    st.subheader(f"On Hold: {total_number_of_hold}")
    st.subheader(f"Rejections: {total_number_of_rejected}")

st.markdown("---")

#DEALS BY WEEK

# calculate the week of the year
df_selection['week'] = df_selection['Date'].dt.week
df_selection['week_str'] = 'CW' + df_selection['week'].apply(lambda x: str(x).zfill(2))

deals_by_week = df_selection.groupby(by=["week_str"]).count()[["ASIN"]].sort_values(by="week_str")

fig_week_deals = px.bar(
    deals_by_week,
    x="ASIN",
    y=deals_by_week.index,
    orientation="h",
    title="<b>Deals per Week</b>",
    color_discrete_sequence=["#0083B8"] * len(deals_by_week),
    template="plotly_white",
)

fig_week_deals.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=(dict(showgrid=False))
)


#SPENDING BY WEEK

# calculate the week of the year in purch_log and the year
df_purch['week'] = df_purch['ORDER (DATE)'].dt.week
df_purch['year'] = df_purch['ORDER (DATE)'].dt.year
df_purch['week_str'] = 'CW' + df_purch['week'].apply(lambda x: str(x).zfill(2))

#filter only the data relevant to the VAs starting from CW05 2023
df_purch_filtered = df_purch[(df_purch['year'] == 2023) & (df_purch['week'] >= 5)]

# replace comma with dot in 'TOTAL PURCHASE (VAT incl)' and convert to float
df_purch_filtered['TOTAL PURCHASE (VAT incl)'] = df_purch_filtered['TOTAL PURCHASE (VAT incl)'].str.replace(',', '.').astype(float)
spend_by_week = df_purch_filtered.groupby(by=['week_str']).sum()[['TOTAL PURCHASE (VAT incl)']]

fig_week_spending = px.bar(
    spend_by_week,
    x='TOTAL PURCHASE (VAT incl)',
    y=spend_by_week.index,
    title="<b>Spending per Week</b>",
    color_discrete_sequence=["#0083B8"] * len(spend_by_week),
    template="plotly_white",
)

fig_week_spending.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    xaxis=(dict(showgrid=False))
)

left_column, right_column = st.columns(2)
left_column.plotly_chart(fig_week_deals, use_container_width=True)
right_column.plotly_chart(fig_week_spending, use_container_width=True)

# ---- HIDE STREAMLIT STYLE ----
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
from babel.numbers import format_currency
from helper import HelperDataAnalyzer, BrazilMapping
import os

# Load datasets
try:
    all_df = pd.read_csv('df.csv')
    geolocation = pd.read_csv('geolocation.csv')
except FileNotFoundError:
    st.error("Required data files are missing. Please ensure 'df.csv' and 'geolocation.csv' are available in the working directory.")
    st.stop()

# Data preparation
all_df['order_approved_at'] = pd.to_datetime(all_df['order_approved_at'])
all_df['payment_value'] = all_df['payment_value'].fillna(0)

# Define date range for filtering
date_min = all_df['order_approved_at'].min()
date_max = all_df['order_approved_at'].max()

# Sidebar configuration
st.sidebar.header("Filter")
start_date, end_date = st.sidebar.date_input(
    "Select Date Range",
    [date_min, date_max],
    min_value=date_min,
    max_value=date_max
)

# Filter data by date range
filtered_df = all_df[(all_df['order_approved_at'] >= pd.to_datetime(start_date)) & 
                     (all_df['order_approved_at'] <= pd.to_datetime(end_date))]

# Initialize HelperDataAnalyzer
helper = HelperDataAnalyzer(filtered_df)

daily_orders_df = helper.create_daily_orders_df()
sum_spend_df = helper.create_sum_spend_df()
sum_order_items_df = helper.create_sum_order_items_df()
review_scores, most_common_score = helper.review_score_df()
bystate_df, most_common_state = helper.create_bystate_df()
order_status_df, most_common_status = helper.create_order_status()

# Business Question 1: Most Sold Product
st.subheader("Most Sold Products")
if not sum_order_items_df.empty:
    st.bar_chart(sum_order_items_df.set_index('product_category_name_english')['product_count'].head(5))
else:
    st.warning("No data available to display Most Sold Products.")

# Business Question 2: Profit Comparison Between Cheap and Expensive Products
if 'price' in filtered_df.columns:
    filtered_df['price_category'] = pd.cut(
        filtered_df['price'],
        bins=[0, 50, 100, filtered_df['price'].max()],
        labels=['Cheap', 'Mid', 'Expensive']
    )
    profit_comparison = filtered_df.groupby('price_category')['payment_value'].sum()

    st.subheader("Profit by Price Category")
    if not profit_comparison.empty:
        fig, ax = plt.subplots()
        profit_comparison.plot(kind='bar', ax=ax, color=['green', 'orange', 'red'])
        ax.set_title("Profit Comparison")
        ax.set_xlabel("Price Category")
        ax.set_ylabel("Total Profit")
        st.pyplot(fig, clear_figure=True)
    else:
        st.warning("No data available to display Profit Comparison.")
else:
    st.warning("Column 'price' not found in the dataset. Skipping profit analysis.")

# Business Question 3: Geographical Distribution of Customers
st.subheader("Customer Geographical Distribution")
if not bystate_df.empty:
    fig, ax = plt.subplots()
    bystate_df.set_index('customer_state')['customer_count'].plot(kind='bar', ax=ax, color='blue')
    ax.set_title("Number of Customers by State")
    ax.set_xlabel("State")
    ax.set_ylabel("Number of Customers")
    st.pyplot(fig, clear_figure=True)
else:
    st.warning("No data available to display Customer Geographical Distribution.")

# Business Question 4: Average Spending per Customer
if not filtered_df.empty:
    average_spending = filtered_df.groupby('customer_unique_id')['payment_value'].sum().mean()
    st.subheader("Average Spending per Customer")
    st.metric(
        label="Average Spending",
        value=format_currency(average_spending, 'USD', locale='en_US')
    )
else:
    st.warning("No data available to calculate Average Spending.")

# Map Visualization
st.subheader("Geolocation Distribution")
try:
    geo_mapping = BrazilMapping(geolocation, plt, plt.imread, plt.urllib, st)
    with st.expander("Click to view Geolocation Map"):
        st.image("MapBrazil.png", caption="Geolocation Distribution", use_column_width=True)
except Exception as e:
    st.warning(f"Unable to render map visualization: {e}")

# Order Items
st.subheader("Order Items")
col1, col2 = st.columns(2)

with col1:
    total_items = sum_order_items_df["product_count"].sum()
    st.markdown(f"Total Items: **{total_items}**")

with col2:
    avg_items = sum_order_items_df["product_count"].mean()
    st.markdown(f"Average Items: **{avg_items}**")

fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(18, 12))

# Define gradient color palette
gradient_palette = sns.color_palette("YlOrBr", n_colors=len(sum_order_items_df))
sns.barplot(
    x="product_count", 
    y="product_category_name_english", 
    data=sum_order_items_df.head(5), 
    palette=gradient_palette[:5],  # Ensure the palette matches the data size
    ax=ax[0]
)
ax[0].set_ylabel(None)
ax[0].set_xlabel("Number of Sales", fontsize=15)
ax[0].set_title("Most sold products", loc="center", fontsize=15)
ax[0].tick_params(axis='y', labelsize=10)
ax[0].tick_params(axis='x', labelsize=10)

sns.barplot(
    x="product_count", 
    y="product_category_name_english", 
    data=sum_order_items_df.sort_values(by="product_count", ascending=True).head(5), 
    palette=gradient_palette[:5], 
    ax=ax[1]
)
ax[1].set_ylabel(None)
ax[1].set_xlabel("Number of Sales", fontsize=15)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Fewest products sold", loc="center", fontsize=15)
ax[1].tick_params(axis='y', labelsize=10)
ax[1].tick_params(axis='x', labelsize=10)

st.pyplot(fig, clear_figure=True)

# Review Score
st.subheader("Review Score")
col1, col2 = st.columns(2)

with col1:
    avg_review_score = review_scores.mean()
    st.markdown(f"Average Review Score: **{avg_review_score:.2f}**")

with col2:
    most_common_review_score = review_scores.idxmax()
    st.markdown(f"Most Common Review Score: **{most_common_review_score}**")

fig, ax = plt.subplots(figsize=(12, 6))
gradient_palette = sns.color_palette("YlOrBr", n_colors=len(review_scores))
sns.barplot(
    x=review_scores.index,
    y=review_scores.values,
    order=review_scores.index,
    palette=gradient_palette[:len(review_scores)],
    ax=ax
)
plt.title("Customer Review Scores for Service", fontsize=15)
plt.xlabel("Rating")
plt.ylabel("Count")
plt.xticks(fontsize=12)
plt.yticks(fontsize=12)

# Menambahkan label di atas setiap bar
for i, v in enumerate(review_scores.values):
    ax.text(i, v + 5, str(v), ha='center', va='bottom', fontsize=12, color='blue')

st.pyplot(fig, clear_figure=True)

# Customer Demographic
st.subheader("Customer Demographic")
tab1, tab2 = st.tabs(["State", "Geolocation"])

with tab1:
    most_common_state = bystate_df.loc[bystate_df['customer_count'].idxmax(), 'customer_state']
    st.markdown(f"Most Common State: **{most_common_state}**")

    fig, ax = plt.subplots(figsize=(12, 6))
    gradient_palette = sns.color_palette("YlOrBr", n_colors=len(bystate_df))
    sns.barplot(
        x=bystate_df['customer_state'],
        y=bystate_df['customer_count'],
        palette=gradient_palette[:len(bystate_df)],
        ax=ax
    )
    plt.title("Number customers from State", fontsize=15)
    plt.xlabel("State")
    plt.ylabel("Number of Customers")
    plt.xticks(fontsize=12)
    st.pyplot(fig, clear_figure=True)

st.caption('Dashboard created by Fitto Martcellindo')

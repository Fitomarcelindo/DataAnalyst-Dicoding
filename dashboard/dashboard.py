import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
import numpy as np
from babel.numbers import format_currency
from helper import HelperDataAnalyzer, BrazilMapping
import urllib.request

# Load datasets
try:
    all_df = pd.read_csv('dashboard/df.csv')
    geolocation = pd.read_csv('dashboard/geolocation.csv')
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

# Question 1: Average Spending per Customer
st.subheader("Rata-rata Belanja Pelanggan")
if not filtered_df.empty:
    average_spending = filtered_df.groupby('customer_unique_id')['payment_value'].sum().mean()
    st.metric(
        label="Rata-rata Belanja",
        value=format_currency(average_spending, 'USD', locale='en_US')
    )
else:
    st.warning("Data tidak tersedia untuk menghitung rata-rata belanja.")

# Question 2: Geographical Distribution of Customers
st.subheader("Distribusi Geografis Pelanggan")
if not bystate_df.empty:
    fig, ax = plt.subplots()
    bystate_df.set_index('customer_state')['customer_count'].plot(kind='bar', ax=ax, color='blue')
    ax.set_title("Jumlah Pelanggan per Negara Bagian")
    ax.set_xlabel("Negara Bagian")
    ax.set_ylabel("Jumlah Pelanggan")
    st.pyplot(fig, clear_figure=True)
else:
    st.warning("Data geografis tidak tersedia.")

# Question 3: Most Sold Products
st.subheader("Produk Paling Banyak Terjual")
if not sum_order_items_df.empty:
    st.bar_chart(sum_order_items_df.set_index('product_category_name_english')['product_count'].head(5))
else:
    st.warning("Data produk tidak tersedia.")

# Question 4: Profit Comparison (Cheap vs Expensive Products)
st.subheader("Perbandingan Keuntungan Produk (Murah vs Mahal)")
if 'price' in filtered_df.columns:
    filtered_df['price_category'] = pd.cut(
        filtered_df['price'],
        bins=[0, 50, 100, filtered_df['price'].max()],
        labels=['Murah', 'Sedang', 'Mahal']
    )
    profit_comparison = filtered_df.groupby('price_category')['payment_value'].sum()

    if not profit_comparison.empty:
        fig, ax = plt.subplots()
        profit_comparison.plot(kind='bar', ax=ax, color=['green', 'orange', 'red'])
        ax.set_title("Perbandingan Keuntungan")
        ax.set_xlabel("Kategori Harga")
        ax.set_ylabel("Keuntungan Total")
        st.pyplot(fig, clear_figure=True)
    else:
        st.warning("Data tidak tersedia untuk menampilkan perbandingan keuntungan.")
else:
    st.warning("Kolom harga tidak ditemukan dalam dataset.")

# Streamlit Visualization of Relationship Between Product Price and Sell Probability
# st.subheader("Relationship Between Product Price and Sell Probability")
# try:
#     st.image("dashboard/product_price_vs_probability.png", 
#              caption="Relationship Between Product Price and Sell Probability", 
#              use_container_width=True)
# except FileNotFoundError:
#     st.warning("Image file 'product_price_vs_probability.png' not found. Please ensure the file is in the correct directory.")

np.random.seed(42)
product_analysis = pd.DataFrame({
    'sell_probability': np.random.rand(100) * 100,
    'price': np.random.rand(100) * 1000,
    'total_revenue': np.random.rand(100) * 10000
})

# Fungsi untuk membuat plot custom
def custom_plot(ax, spines):
    for loc, spine in ax.spines.items():
        if loc in spines:
            spine.set_position(('outward', 10))
        else:
            spine.set_color('none')
    ax.xaxis.set_ticks_position('bottom')
    ax.yaxis.set_ticks_position('left')

# Streamlit App
st.title('Dashboard: Relationship Between Product Price and Sell Probability')

# Input Sidebar
st.sidebar.header('Customize Visualization')
gridsize = st.sidebar.slider('Grid Size', min_value=10, max_value=50, value=20, step=5)
colormap = st.sidebar.selectbox('Colormap', ['viridis', 'plasma', 'inferno', 'magma', 'cividis'])

# Log transform data
x = np.log(product_analysis['sell_probability'])
y = np.log(product_analysis['price'])

# Create plot
fig, ax = plt.subplots(figsize=(10, 7))
custom_plot(ax, ['bottom', 'left'])

plt.title('Relationship Between Product Price and Sell Probability', fontsize=18, fontweight='bold')
plt.xlabel('Log(Sell Probability)', fontsize=14)
plt.ylabel('Log(Product Price)', fontsize=14)

plt.xlim(x.min() - 0.5, x.max() + 0.5)
plt.ylim(y.min() - 0.5, y.max() + 0.5)

plt.xticks(fontsize=12, rotation=45)
plt.yticks(fontsize=12)

hb = ax.hexbin(
    x, y,
    gridsize=gridsize,
    C=product_analysis['total_revenue'],
    reduce_C_function=np.sum,
    cmap=colormap
)

cb = fig.colorbar(hb, ax=ax)
cb.set_label('Total Revenue (R$)', rotation=270, labelpad=20, fontsize=14)

plt.tight_layout()

# Render plot in Streamlit
st.pyplot(fig)


# Map Visualization
st.subheader("Distribusi Geolokasi Pelanggan")
try:
    geo_mapping = BrazilMapping(geolocation, plt, plt.imread, urllib, st)
    with st.expander("Klik untuk melihat Peta Geolokasi"):
        st.title("Dashboard Gambar dengan Streamlit")
        # Menampilkan gambar dari URL
        st.image("dashboard/MapBrazil.png",  caption="Geolokasi Pelanggan", 
             use_container_width=True)
        # Menampilkan teks tambahan
        st.write("Gambar di atas adalah contoh bagaimana menampilkan gambar dari URL di Streamlit.")
except Exception as e:
    st.warning(f"Visualisasi peta tidak dapat ditampilkan: {e}")

st.caption("Dashboard created by Fitto Martcellindo")

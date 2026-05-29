import streamlit as st
import gzip
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import zlib

# ─── Page Config ───────────────────────────────────────────────
st.set_page_config(page_title="Watches Review Dashboard", layout="wide")
st.title("⌚ Amazon Watches Review Dashboard")

# ─── Parse Function ────────────────────────────────────────────
def parse(filename):
    entry = {}
    try:
        with gzip.open(filename, 'rt', encoding='utf-8') as f:
            for l in f:
                l = l.strip()
                if not l:
                    if entry:
                        yield entry
                    entry = {}
                    continue
                colonPos = l.find(':')
                if colonPos == -1:
                    continue
                eName = l[:colonPos].strip()
                rest = l[colonPos+1:].strip()
                entry[eName] = rest
            if entry:
                yield entry
    except zlib.error as e:
        st.error(f"Error decompressing file: {e}")
    except Exception as e:
        st.error(f"Unexpected error: {e}")

# ─── Load Data ─────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.DataFrame(list(parse("Watches.txt.gz")))
    df['review/score'] = pd.to_numeric(df['review/score'], errors='coerce')
    df['review/time'] = pd.to_datetime(
        pd.to_numeric(df['review/time'], errors='coerce'), unit='s'
    )
    df = df.dropna(subset=['review/score', 'review/time'])
    df['Year'] = df['review/time'].dt.year.astype(str)
    df['Month'] = df['review/time'].dt.strftime('%b')
    df['Rating'] = df['review/score'].astype(int).astype(str) + ' ⭐'
    return df

df = load_data()

st.success(f"✅ Loaded {len(df):,} reviews successfully!")

# ─── Sidebar Filters ───────────────────────────────────────────
st.sidebar.header("🔍 Filters")
years = sorted(df['Year'].unique())
selected_years = st.sidebar.multiselect("Select Year(s)", years, default=years)
df_filtered = df[df['Year'].isin(selected_years)]

# ─── KPI Metrics ───────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
col1.metric("📝 Total Reviews", f"{len(df_filtered):,}")
col2.metric("⭐ Avg Rating", f"{df_filtered['review/score'].mean():.2f}")
col3.metric("🛍️ Unique Products", f"{df_filtered['product/productId'].nunique():,}")

st.divider()

# ─── Chart 1: Rating Distribution (Matplotlib) ─────────────────
st.subheader("📊 Rating Distribution")
rating_counts = df_filtered['review/score'].value_counts().sort_index()

fig1, ax1 = plt.subplots(figsize=(8, 4))
ax1.bar(rating_counts.index, rating_counts.values, color='steelblue', edgecolor='black')
ax1.set_title('Distribution of Review Ratings')
ax1.set_xlabel('Rating (Stars)')
ax1.set_ylabel('Number of Reviews')
ax1.set_xticks([1, 2, 3, 4, 5])
ax1.grid(axis='y', linestyle='--', alpha=0.7)
st.pyplot(fig1)          # ✅ Use st.pyplot() NOT plt.show()
plt.close(fig1)          # ✅ Always close to free memory

st.divider()

# ─── Chart 2: Reviews Over Time (Plotly) ───────────────────────
st.subheader("📈 Reviews Over Time")
df_time = df_filtered.set_index('review/time').resample('M').size().reset_index()
df_time.columns = ['Date', 'Review Count']

fig2 = px.line(
    df_time, x='Date', y='Review Count',
    markers=True, color_discrete_sequence=['darkorange']
)
st.plotly_chart(fig2, use_container_width=True)

st.divider()

# ─── Chart 3: Sunburst Chart (Plotly) ──────────────────────────
st.subheader("☀️ Sunburst: Year → Month → Rating")
sunburst_df = df_filtered.groupby(['Year', 'Month', 'Rating']).size().reset_index(name='Count')

fig3 = px.sunburst(
    sunburst_df,
    path=['Year', 'Month', 'Rating'],
    values='Count',
    color='Count',
    color_continuous_scale='RdYlGn',
)
st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ─── Chart 4: Top 10 Products ──────────────────────────────────
st.subheader("🏆 Top 10 Most Reviewed Products")
top_products = df_filtered['product/title'].value_counts().head(10).reset_index()
top_products.columns = ['Product', 'Review Count']
top_products['Product'] = top_products['Product'].str[:40] + '...'

fig4 = px.bar(
    top_products, x='Review Count', y='Product',
    orientation='h', color='Review Count',
    color_continuous_scale='Teal', text='Review Count'
)
fig4.update_layout(yaxis={'categoryorder': 'total ascending'}, plot_bgcolor='white')
st.plotly_chart(fig4, use_container_width=True)

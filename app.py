import streamlit as st
import pandas as pd
import altair as alt
import os
from io import BytesIO
from utils.dashboard_loader import (
    scan_dataset_folder,load_dashboard_data,sort_sdg_labels
)

# settingan halaman
st.set_page_config(page_title="Visualisasi Data", page_icon="📊", layout="wide")

st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        div.block-container {padding-top: 1rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Dashboard Visualisasi SDGs ITSK SOEPRAOEN")
# --- KUSTOM SIDEBAR NAVIGASI ---
st.sidebar.header("Navigasi Menu")
if st.sidebar.button("📊 Dashboard Visualisasi", use_container_width=True):
    st.switch_page("app.py")
if st.sidebar.button("📤 Upload Data", use_container_width=True):
    st.switch_page("pages/upload_data.py")
st.sidebar.markdown("---")

# --- Lokasi folder CSV ---
DATA_FOLDER = "file_excel/predicted"  
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# kode baru jam setengah 11
dataset_metadata = scan_dataset_folder(DATA_FOLDER)

# --- Sidebar: Pilih tahun ---
available_years = sorted(
    d["year"]
    for d in dataset_metadata
)
selected_years = st.multiselect(
    "📅 Tahun Dataset",
    options=available_years,
    default=available_years
)

# --- Baca file CSV sesuai pilihan ---
df = load_dashboard_data(
    selected_years,
    dataset_metadata
)

if df.empty:
    st.warning("⚠️ Tidak ada dataset untuk tahun yang dipilih.")
    st.stop()

st.toast(
    f"✅ Berhasil memuat dataset selama {len(selected_years)} tahun"
    # ,icon="🎉"
)

# cek kolom yang wajib ada
required_columns = [
    "ACCREDITATION",
    "TITLE",
    "JOURNAL",
    "AUTHORS",
    "YEAR",
    "CITATION",
    "Predicted SDG"
]

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    st.error(
        f"❌ Kolom berikut tidak ditemukan: {', '.join(missing_columns)}"
    )
    st.stop()

# mempersiapkan data
# --- Hitung jumlah masing-masing SDGs ---
sdg_count = (
    df["Predicted SDG"]
    .value_counts()
    .reset_index()
)

sdg_count.columns = [
    "Predicted SDG",
    "jumlah"
]

left_col, right_col = st.columns([1, 1.5])

with left_col:

    st.markdown("#### 🌍 SDGs")

    available_sdg = sort_sdg_labels(
        df["Predicted SDG"].dropna().unique()
    )

    selected_sdg = st.multiselect(
        "Pilih SDG",
        options=available_sdg,
        default=available_sdg,
        label_visibility="collapsed"
    )

with right_col:

    st.markdown("#### 📚 Publisher Journal")

    available_journal = sorted(
        df["JOURNAL"].dropna().unique()
    )

    selected_journal = st.multiselect(
        "Pilih Journal",
        options=available_journal,
        default=available_journal,
        label_visibility="collapsed"
    )

# terapkan filter
filtered_df = df.copy()

filtered_df = filtered_df[
    filtered_df["Predicted SDG"].isin(selected_sdg)
]

filtered_df = filtered_df[
    filtered_df["JOURNAL"].isin(selected_journal)
]
filtered_df = filtered_df.reset_index(drop=True)

# validasi
if filtered_df.empty:
    st.warning("⚠️ Tidak ada data yang sesuai filter.")
    st.stop()

# metrik box sentimen
total_data = len(filtered_df)

total_article = len(filtered_df)

total_journal = filtered_df["JOURNAL"].nunique()

total_author = (
    filtered_df["AUTHORS"]
    .fillna("")
    .str.split(";")
    .explode()
    .str.strip()
    .nunique()
)

filtered_df["CITATION"] = pd.to_numeric(
    filtered_df["CITATION"],
    errors="coerce"
)

total_citation = filtered_df["CITATION"].fillna(0).sum()
# metrik
col1,col2,col3,col4 = st.columns(4)
col1.metric(
    "📄 Total Artikel",
    total_article
)

col2.metric(
    "📚 Total Publisher Journal",
    total_journal
)

col3.metric(
    "👨‍💻 Total Author",
    total_author
)

col4.metric(
    "📖 Total Citation",
    f"{int(total_citation):,}"
)

# sdg dominan
top_sdg = (
    filtered_df["Predicted SDG"]
    .value_counts()
)

if not top_sdg.empty:

    st.info(
        f"🏆 SDG Dominan : **{top_sdg.index[0]}** ({top_sdg.iloc[0]} artikel)"
    )

# siapkan data untuk visualisasi dengan chart
# bar chart
bar_data = (
    filtered_df["JOURNAL"]
    .value_counts()
    .head(10)
    .reset_index()
)

bar_data.columns = [
    "Journal",
    "Jumlah"
]

# pie chart
pie_data = (
    filtered_df["Predicted SDG"]
    .value_counts()
    .reset_index()
)

pie_data.columns = [
    "SDG",
    "Jumlah"
]

# menjadikan satu baris
chart_col1, chart_col2 = st.columns(2)
# Bar Chart
with chart_col1:
    st.subheader("📚 Top 10 Publisher Journal")

    bar_chart = alt.Chart(bar_data).mark_bar().encode(
        x=alt.X(
            "Jumlah:Q",
            title="Jumlah Artikel"
        ),
        y=alt.Y(
            "Journal:N",
            sort="-x"
        ),
        tooltip=[
            "Journal",
            "Jumlah"
        ]
    )
    
    st.altair_chart(
        bar_chart,
        use_container_width=True
    )

# Pie Chart
with chart_col2:

    st.subheader("🌍 Distribusi SDGs")

    pie_chart = alt.Chart(pie_data).mark_arc(
    innerRadius=60
        ).encode(
            theta="Jumlah:Q",
            color="SDG:N",
            tooltip=[
                "SDG",
                "Jumlah"
            ]
        )

    st.altair_chart(
        pie_chart,
        use_container_width=True
    )

# st.divider()

# left,right = st.columns(2)

# # akreditasi
# with left:

#     st.subheader("🏅 Distribusi Accreditation")

#     accreditation = (
#         filtered_df["ACCREDITATION"]
#         .value_counts()
#         .reset_index()
#     )

#     accreditation.columns = [
#         "Accreditation",
#         "Jumlah"
#     ]

#     chart = alt.Chart(accreditation).mark_arc(
#         innerRadius=60
#     ).encode(

#         theta="Jumlah",

#         color="Accreditation",

#         tooltip=[
#             "Accreditation",
#             "Jumlah"
#         ]

#     )

#     st.altair_chart(
#         chart,
#         use_container_width=True
#     )

# # top author
# with right:

#     st.subheader("👨‍💻 Top Author")

#     authors = (
#         filtered_df["AUTHORS"]
#         .fillna("")
#         .str.split(";")
#         .explode()
#         .str.strip()
#     )

#     top_author = (
#         authors.value_counts()
#         .head(10)
#         .reset_index()
#     )

#     top_author.columns = [
#         "Author",
#         "Jumlah"
#     ]

#     chart = alt.Chart(top_author).mark_bar().encode(

#         x="Jumlah",

#         y=alt.Y(
#             "Author",
#             sort="-x"
#         ),

#         tooltip=[
#             "Author",
#             "Jumlah"
#         ]

#     )

#     st.altair_chart(
#         chart,
#         use_container_width=True
#     )

# ==========================
# Data Tren SDGs per Tahun
# ==========================
trend_df = (
    filtered_df
    .groupby(["YEAR", "Predicted SDG"])
    .size()
    .reset_index(name="Jumlah Artikel")
)
trend_df["YEAR"] = trend_df["YEAR"].astype(str)
# hanya muncul jika memilih lebih dari 1 tahun
if len(selected_years) > 1: 
    st.divider()
    st.subheader("📈 Tren Jumlah Artikel SDGs per Tahun")
    left_chart, right_chart = st.columns(2)
    # grouped bar chart
    with left_chart:
        st.markdown("#### 📊 Grouped Bar Chart")

        grouped_bar = (
            alt.Chart(trend_df)
            .mark_bar()
            .encode(
                x=alt.X(
                    "Predicted SDG:N",
                    title="SDGs",
                    sort=sort_sdg_labels(trend_df["Predicted SDG"].unique())
                ),
                y=alt.Y(
                    "Jumlah Artikel:Q",
                    title="Jumlah Artikel"
                ),
                color=alt.Color(
                    "YEAR:N",
                    title="Tahun"
                ),
                xOffset="YEAR:N",
                tooltip=[
                    "Predicted SDG",
                    "YEAR",
                    "Jumlah Artikel"
                ]
            )
            .properties(
                height=450
            )
        )

        st.altair_chart(
            grouped_bar,
            use_container_width=True
        )

    # heatmap
    with right_chart:

        st.markdown("#### 🔥 Heatmap")

        heatmap = (
            alt.Chart(trend_df)
            .mark_rect()
            .encode(
                x=alt.X(
                    "YEAR:N",
                    title="Tahun"
                ),
                y=alt.Y(
                    "Predicted SDG:N",
                    sort=sort_sdg_labels(trend_df["Predicted SDG"].unique()),
                    title="SDGs"
                ),
                color=alt.Color(
                    "Jumlah Artikel:Q",
                    title="Jumlah Artikel"
                ),
                tooltip=[
                    "Predicted SDG",
                    "YEAR",
                    "Jumlah Artikel"
                ]
            )
            .properties(
                height=450
            )
        )

        st.altair_chart(
            heatmap,
            use_container_width=True
        )

# histogram sitasi
st.divider()

st.subheader("📈 Distribusi Citation")

# Membuat kelompok citation
citation_chart = (
    filtered_df
    .groupby("Predicted SDG")["CITATION"]
    .sum()
    .sort_values(ascending=False)
    .reset_index()
)

citation_chart.columns = [
    "SDG",
    "Total Citation"
]

chart = (
    alt.Chart(citation_chart)
    .mark_bar()
    .encode(
        x=alt.X(
            "Total Citation:Q",
            title="Total Citation"
        ),
        y=alt.Y(
            "SDG:N",
            sort="-x"
        ),
        tooltip=[
            "SDG",
            "Total Citation"
        ]
    )
)
st.altair_chart(chart, use_container_width=True)

# xpander
with st.expander("📋 Lihat Detail Artikel", expanded=False):
    st.subheader("📋 Detail Artikel")
    detail_columns = [
        "TITLE",
        "JOURNAL",
        "AUTHORS",
        "YEAR",
        "CITATION",
        "Predicted SDG"
    ]

    # filter detail berdasarkan SDGs
    selected_detail_sdg = st.selectbox("Filter Detail berdasarkan SDG",["Semua SDGs"] + sorted(filtered_df["Predicted SDG"].unique()))
    detail_df = filtered_df.copy()
    if selected_detail_sdg != "Semua SDGs":
        detail_df = detail_df[detail_df["Predicted SDG"] == selected_detail_sdg]

    st.info(f"📄 {len(detail_df):,} artikel ditemukan")
    st.dataframe(
        detail_df[detail_columns]
        .sort_values("CITATION", ascending=False),
        use_container_width=True,
        hide_index=True
    )

    # tombol download buat jaga jaga
    # csv
    # download_df = detail_df[detail_columns].sort_values(
    #     "CITATION",
    #     ascending=False
    # )
    # csv = download_df.to_csv(index=False).encode("utf-8")
    # st.download_button(
    #     label="📥 Download Data",
    #     data=csv,
    #     file_name="detail_artikel.csv",
    #     mime="text/csv",
    #     type= "primary"
    # )

    # excell
    download_df = detail_df[detail_columns].sort_values(
        "CITATION",
        ascending=False
    )

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        download_df.to_excel(
            writer,
            index=False,
            sheet_name="Detail Artikel"
        )

    excel_data = output.getvalue()

    st.download_button(
        label="📥 Download Data",
        data=excel_data,
        file_name="detail_artikel.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary"
    )
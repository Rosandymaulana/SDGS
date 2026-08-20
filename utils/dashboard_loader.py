import streamlit as st
import pandas as pd
import os
import re

# bikin cache untuk menyimpan dataset yang sudah di-load
@st.cache_data(show_spinner=False)
def load_single_dataset(file_path):
    """
    Membaca satu dataset dan melakukan validasi awal.
    Hasilnya disimpan dalam cache agar file tidak dibaca berulang.
    """
    df = pd.read_excel(file_path)

    df["YEAR"] = pd.to_numeric(df["YEAR"], errors="coerce")

    df["CITATION"] = pd.to_numeric(
        df["CITATION"],
        errors="coerce"
    ).fillna(0)
    return df

# scan dataset
def scan_dataset_folder(data_folder):
    dataset_metadata = []
    for file in os.listdir(data_folder):
        if not file.endswith(".xlsx"):
            continue
        file_path = os.path.join(data_folder, file)
        try:
            temp_df = load_single_dataset(file_path)
            if temp_df.empty:
                continue
            year = int(temp_df["YEAR"].dropna().iloc[0])
            dataset_metadata.append({
                "file": file,
                "path": file_path,
                "year": year,
                "display_name": os.path.splitext(file)[0].replace("_", " ")
            })
        except Exception:
            continue
    return dataset_metadata

# fungsi utama untuk mengelompokkan berdasarkan tahun
@st.cache_data(show_spinner=False)
def load_dashboard_data(selected_years, dataset_metadata):
    """
    Menggabungkan seluruh dataset sesuai tahun yang dipilih.
    """
    selected_files = [
        d for d in dataset_metadata
        if d["year"] in selected_years
    ]

    if not selected_files:
        return pd.DataFrame()

    dfs = []

    for item in selected_files:
        dfs.append(
            load_single_dataset(item["path"])
        )

    return pd.concat(
        dfs,
        ignore_index=True
    )

# fungsi sort-nama SDGs
def sort_sdg_labels(labels):
    return sorted(
        labels,
        key=lambda x: int(re.search(r"\d+", x).group())
    )
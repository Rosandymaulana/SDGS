import streamlit as st
import os
import pandas as pd
import torch
import re
import pickle
from preprocessing import preprocess_text
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification
)

# settingan halaman
st.set_page_config(page_title="Upload Dataset", page_icon="📤", layout="wide")

# memanggil model prediksi
@st.cache_resource
def load_model():

    model_path = "model"

    tokenizer = AutoTokenizer.from_pretrained(model_path)

    model = AutoModelForSequenceClassification.from_pretrained(
        model_path
    )

    with open(
        os.path.join(model_path, "label_encoder.pkl"),
        "rb"
    ) as f:

        label_encoder = pickle.load(f)

    model.eval()

    return tokenizer, model, label_encoder

def predict_sdg(
    texts,
    tokenizer,
    model,
    label_encoder,
    batch_size=16,
    max_length=128,
    progress_bar=None,
    status_text=None
):

    predictions = []

    total_batches = (len(texts) + batch_size - 1) // batch_size

    with torch.no_grad():

        for batch_idx, start in enumerate(
            range(0, len(texts), batch_size)
        ):

            batch = texts[start:start + batch_size]

            inputs = tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=max_length,
                return_tensors="pt"
            )

            outputs = model(**inputs)

            preds = torch.argmax(
                outputs.logits,
                dim=1
            ).tolist()

            predictions.extend(
                label_encoder.inverse_transform(preds)
            )

            progress = (batch_idx + 1) / total_batches

            if progress_bar:
                progress_bar.progress(progress)

            if status_text:
                status_text.text(
                    f"🔄 Memproses batch {batch_idx + 1} dari {total_batches}"
                )

    return predictions

# --- Hilangkan sidebar bawaan Streamlit ---
st.markdown("""
    <style>
        [data-testid="stSidebarNav"] {display: none;}
        div.block-container {padding-top: 1rem;}
    </style>
""", unsafe_allow_html=True)

# --- KUSTOM SIDEBAR NAVIGASI ---
st.sidebar.header("Navigasi Menu")
if st.sidebar.button("📊 Dashboard Visualisasi", use_container_width=True):
    st.switch_page("app.py")
if st.sidebar.button("📤 Upload Data", use_container_width=True):
    st.switch_page("pages/upload_data.py")
st.sidebar.markdown("---")

st.title("📤 Upload Dataset")
st.write("Gunakan halaman ini untuk menambahkan file dataset `.xlsx` baru ke dalam sistem.")

# Folder penyimpanan dataset
RAW_FOLDER = "file_excel/raw"
PREDICTED_FOLDER = "file_excel/predicted"

os.makedirs(RAW_FOLDER, exist_ok=True)
os.makedirs(PREDICTED_FOLDER, exist_ok=True)

st.info("""
### 📌 Ketentuan Dataset:
- Format file wajib berupa **.xlsx**
- Header berada di baris ke-5 sesuai template dataset

Kolom yang harus ada di dataset:
- ACCREDITATION
- TITLE
- JOURNAL
- AUTHORS
- YEAR
- CITATION
- Kolom "Predicted SDG" dibuat otomatis oleh sistem
""")

# =======================
# Field nama dataset
# =======================
dataset_name = st.text_input(
    "📝 Nama Dataset",
    placeholder="Contoh: Scopus 2022"
)
# preview nama dataset
preview = ""
final_filename = ""
save_path = ""

if dataset_name.strip():

    preview = dataset_name.lower().strip()

    preview = re.sub(
        r"\s+",
        "_",
        preview
    )

    preview = re.sub(
        r"[^a-zA-Z0-9_-]",
        "",
        preview
    )

    # st.caption(
    #     f"📄 Nama file hasil: {preview}.xlsx"
    # )

# apa nama file sudah ada ?
predicted_path = os.path.join(
    PREDICTED_FOLDER,
    preview + ".xlsx"
)

save_path = predicted_path
final_filename = preview + ".xlsx"

overwrite_option = "Replace"

if os.path.exists(predicted_path):

    st.warning(
        "⚠️ Dataset dengan nama tersebut sudah ada."
    )

    overwrite_option = st.radio(
        "Pilih tindakan:",
        [
            "Replace dataset lama",
            "Simpan sebagai batch baru"
        ],
        horizontal=True
    )

    if overwrite_option == "Simpan sebagai batch baru":

        batch = 1

        while True:

            batch_name = (
                f"{preview}-batch{batch}.xlsx"
            )

            batch_path = os.path.join(
                PREDICTED_FOLDER,
                batch_name
            )

            if not os.path.exists(batch_path):

                save_path = batch_path
                final_filename = batch_name
                break

            batch += 1

    st.info(
        f"📄 File akan disimpan sebagai **{final_filename}**"
    )

else:

    st.caption(
        f"📄 Nama file hasil: {final_filename}"
    )
# =======================
# Form Upload Dataset
# =======================
uploaded_file = st.file_uploader(
    "📁 Pilih satu file excel untuk di-upload",
    type=["xlsx"],
    accept_multiple_files= False,
)

if st.button("⬆️ Upload dan prediksi", type="primary"):

    if uploaded_file is None:
        st.error("❌ Tidak ada file yang dipilih.")

    else:
        # apa user udh isi nama dataset ?
        if not dataset_name.strip():
            st.error(
                "Silakan isi nama dataset."
            )
            st.stop()

        with st.spinner("🤖 Memuat model..."):
            tokenizer, model, label_encoder = load_model()

        status_text = st.empty()
        file = uploaded_file
        filename = final_filename

        raw_path = os.path.join(
            RAW_FOLDER,
            filename
        )

        with open(raw_path, "wb") as f:
            f.write(file.read())

        status_text.text(
            f"📥 Membaca file {filename}"
        )

        df = pd.read_excel(raw_path,header=4)

        # mengecek kolom yang wajib ada
        required_columns = [
            "ACCREDITATION",
            "TITLE",
            "JOURNAL",
            "AUTHORS",
            "YEAR",
            "CITATION"
        ]

        missing_columns = [
            col for col in required_columns
            if col not in df.columns
        ]

        if missing_columns:
            st.error(
                f"❌ File {filename} tidak memiliki kolom: "
                f"{', '.join(missing_columns)}"
            )
            st.stop()
        # cleaning dataset (mengubah "-" jadi "tidak diketahui")
        cols = [
            "AUTHORS",
            "ACCREDITATION"
        ]

        for col in cols:

            df[col] = (
                df[col]
                .replace("-", "Tidak diketahui")
                .fillna("Tidak diketahui")
            )

        status_text.text("🧹 Membersihkan teks...")
        df["TITLE"] = (
            df["TITLE"]
            .fillna("")
            .astype(str)
        )
        df["TITLE_clean"] = df["TITLE"].apply(
            preprocess_text
        )
        
        # hapus ulasan kosong setelah preprocessing
        before_count = len(df)
        df = df[df["TITLE_clean"].str.strip() != ""]
        removed_count = before_count - len(df)
        if removed_count > 0:
            st.info(
                f"🗑️ {removed_count} ulasan kosong berhasil dihapus."
            )
        if df.empty:
            st.warning(
                f"⚠️ File {filename} tidak memiliki title valid."
            )
            st.stop()
        # Hapus judul duplikat berdasarkan hasil preprocessing
        before_duplicate = len(df)

        df = (
            df.drop_duplicates(subset=["TITLE_clean"])
            .reset_index(drop=True)
        )

        duplicate_removed = before_duplicate - len(df)

        if duplicate_removed > 0:
            st.info(
                f"🗑️ {duplicate_removed} title duplikat berhasil dihapus."
            )

        if df.empty:
            st.warning(
                "⚠️ Seluruh data merupakan duplikat."
            )
            st.stop()
        # gunakan kolom hasil preprocessing untuk prediksi:
        file_progress = st.progress(0)

        predictions = predict_sdg(
            df["TITLE_clean"].tolist(),
            tokenizer,
            model,
            label_encoder,
            batch_size=16,
            max_length=128,
            progress_bar=file_progress,
            status_text=status_text
        )

        df["Predicted SDG"] = predictions
        df.drop(columns=["TITLE_clean"], inplace=True)

        df.to_excel(
            save_path,
            index=False
        )

        file_progress.empty()

        saved_name = os.path.basename(save_path)
        st.success(
            f"✅ {saved_name} berhasil dianalisis"
        )

        display_name = (
            os.path.splitext(final_filename)[0]
            .replace("_", " ")
            .capitalize()
        )

        st.session_state["last_uploaded_file"] = display_name

        status_text.text(
            "🎉 Semua file selesai diproses"
        )

        st.session_state["upload_berhasil"] = True

# --- Tombol navigasi setelah prediksi ---
if st.session_state.get("upload_berhasil", False):
    st.info("💡 Dataset baru sudah siap! Anda bisa langsung klik tombol di bawah atau menu di sidebar untuk melihat hasilnya.")
    
    if st.button("📊 Lihat Visualisasi Data Sekarang", use_container_width=True):
        st.session_state["upload_berhasil"] = False
        st.switch_page("app.py")
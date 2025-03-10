import os
import re
import json
import PyPDF2
from docx import Document
import streamlit as st

# Konstanta untuk nama file JSON
DATA_FILE = "data_laporan.json"

# Fungsi untuk memuat dan menyimpan data JSON
def load_data():
    return json.load(open(DATA_FILE, "r")) if os.path.exists(DATA_FILE) else {}

def save_data(data):
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)

# Fungsi untuk membaca teks dari PDF dan Word
def extract_text(file, file_type):
    try:
        if file_type == "application/pdf":
            pdf_reader = PyPDF2.PdfReader(file)
            return [page.extract_text() for page in pdf_reader.pages]
        elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = Document(file)
            return [paragraph.text for paragraph in doc.paragraphs]
        else:
            st.warning(f"Format file {file.name} tidak didukung.")
            return []
    except Exception as e:
        st.error(f"Error membaca file {file.name}: {e}")
        return []

# Fungsi pencarian frasa dengan mengabaikan spasi
def search_text_ignore_spaces(doc_text, search_phrase):
    search_pattern = r"\s*".join(re.escape(word) for word in search_phrase.split())
    regex = re.compile(search_pattern, re.IGNORECASE)

    results = []
    for page_number, page_text in enumerate(doc_text, start=1):
        matches = regex.findall(page_text)
        if matches:  # Jika ada match, tambahkan halaman tersebut
            results.append((page_number, page_text, len(matches)))
    return results

# Fungsi untuk menyorot teks
def highlight_text(text, search_phrase):
    return re.sub(
        fr"({re.escape(search_phrase)})",
        r'<mark style="background-color: yellow;">\1</mark>',
        text,
        flags=re.IGNORECASE,
    )

# Muat data laporan
data_laporan = load_data()

# Konfigurasi halaman Streamlit
st.set_page_config(page_title="Laporan Interaktif", layout="wide")
st.markdown(
    "<h1 style='text-align: center; '>Pengecekan Laporan Penilaian KJPP SRR Kalibata</h1>",
    unsafe_allow_html=True
)

st.markdown(
    """

    <hr style="border: 1px solid #000; margin-top: 50px;">
    """,
    unsafe_allow_html=True
)

# Layout dengan kolom
col1, col2 = st.columns([1, 3])

with col1:
    uploaded_files_pdf = st.file_uploader("Unggah File PDF", type="pdf", accept_multiple_files=True)
    uploaded_files_word = st.file_uploader("Unggah File Word", type="docx", accept_multiple_files=True)

    selected_laporan = st.selectbox(
        "Pilih Laporan",
        options=list(data_laporan.keys()) + ["Tambah Laporan Baru"]
    )

    

    if selected_laporan and selected_laporan != "Tambah Laporan Baru":
        st.subheader(f"Wajib Cek {selected_laporan}")
        laporan_data = data_laporan[selected_laporan]
        # Toggle untuk daftar cek atau daftar biasa
        toggle_checklist = st.checkbox("Tampilkan Checklist")  # Definisi toggle_checklist

        # Menampilkan cek list untuk setiap item dalam laporan_data
        updated_data = {}
        
        if laporan_data:
            if toggle_checklist:
                # Tampilkan sebagai checklist
                for key, value in laporan_data.items():
                    st.checkbox(f"{key}: {value} kali", value=False, key=f"check_{key}")
            else:
                # Tampilkan sebagai daftar biasa
                for key, value in laporan_data.items():
                    st.write(f"- {key}: {value} kali")
        else:
            st.info("Laporan ini belum memiliki keterangan.")

    if selected_laporan == "Tambah Laporan Baru":
        new_laporan_name = st.text_input("Masukkan nama laporan baru:")
        if st.button("Tambahkan Laporan Baru") and new_laporan_name:
            if new_laporan_name not in data_laporan:
                data_laporan[new_laporan_name] = {}
                save_data(data_laporan)
                st.success(f"Laporan '{new_laporan_name}' berhasil ditambahkan!")
            else:
                st.warning(f"Laporan '{new_laporan_name}' sudah ada.")

    elif selected_laporan:
        
        # Garis tebal
        st.markdown("---")
        if st.checkbox("Tambah Keterangan"):
            keterangan = st.text_input("Jenis Keterangan:")
            jumlah = st.number_input("Jumlah Kemunculan", min_value=0, step=1)
            if st.button("Tambahkan Keterangan"):
                laporan_data[keterangan] = jumlah
                save_data(data_laporan)
                st.success(f"Keterangan '{keterangan}' berhasil ditambahkan.")

        if st.checkbox("Hapus Keterangan"):
            keterangan_to_delete = st.selectbox("Pilih keterangan untuk dihapus:", list(laporan_data.keys()))
            if st.button("Hapus Keterangan"):
                del laporan_data[keterangan_to_delete]
                save_data(data_laporan)
                st.success(f"Keterangan '{keterangan_to_delete}' berhasil dihapus.")

    

with col2:
    search_phrase = st.text_input("Masukkan frasa yang ingin dicari:")
    uploaded_files = uploaded_files_pdf + uploaded_files_word

    if search_phrase and uploaded_files:
        st.subheader("Hasil Pencarian")
        grand_total_count = 0  # Variabel untuk total frasa di semua file

        for uploaded_file in uploaded_files:
            doc_text = extract_text(uploaded_file, uploaded_file.type)
            results = search_text_ignore_spaces(doc_text, search_phrase)

            st.write(f"**{uploaded_file.name}**")
            if results:
                file_total_count = 0
                for page_number, page_text, match_count in results:
                    file_total_count += match_count
                    highlighted_text = highlight_text(page_text, search_phrase)
                    # st.markdown(f"**Halaman {page_number} (Ditemukan {match_count} kali):**", unsafe_allow_html=True)
                    st.markdown(highlighted_text, unsafe_allow_html=True)
                grand_total_count += file_total_count
                st.write(f"**Total frasa '{search_phrase}' ditemukan: {file_total_count} kali di file ini.**")
            else:
                st.write("- Tidak ditemukan.")

        st.subheader(f"**Total frasa '{search_phrase}' ditemukan di semua file: {grand_total_count} kali.**")

# Garis di bagian bawah
st.markdown(
    """
    <hr style="border: 1px solid #000; margin-top: 50px;">
    <p style="text-align: center; font-size: 14px; color: gray;">Created by HW and ChatGPT 4o</p>
    """,
    unsafe_allow_html=True
)

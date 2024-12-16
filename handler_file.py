import pandas as pd
from Crud import insert_tokens_to_db

# Daftar ID pengguna yang diperbolehkan (misalnya hanya master yang diizinkan)
ALLOWED_USERS = [764245690, 7060442428]  # Ganti dengan ID Telegram pengguna yang diizinkan

def process_file(file_path, user_id):
    # Validasi apakah pengguna memiliki izin

    if user_id not in ALLOWED_USERS:
        print(f"User {user_id} tidak memiliki izin untuk mengupload file.")
        return 0

    try:
        # Membaca file CSV atau XLSX
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            print("Format file tidak didukung.")
            return 0

        # Verifikasi apakah `df` adalah DataFrame
        if not isinstance(df, pd.DataFrame):
            print("Error: File tidak terbaca sebagai DataFrame.")
            return 0

        # Tampilkan nama kolom yang ditemukan
        print("Nama kolom yang ditemukan:", df.columns.tolist())

        # Normalisasi nama kolom: hapus spasi dan ubah ke huruf kapital
        df.columns = [col.strip().upper() for col in df.columns]

        # Validasi kolom yang diperlukan
        required_columns = ['SITE ID', 'SITE NAME', 'TOKEN BULAN', 'NOMOR TOKEN', 'KETERANGAN']

        # Periksa kolom yang hilang
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            print("Kolom berikut tidak ditemukan:", missing_columns)
            return 0

        # Konversi data ke list of tuples
        data = list(df[required_columns].itertuples(index=False, name=None))

        # Tampilkan data yang akan dimasukkan
        print("Data yang akan dimasukkan ke DB:", data)

        # Panggil fungsi untuk memasukkan ke database
        inserted_rows = insert_tokens_to_db(data)

        if isinstance(inserted_rows, int):
            print(f"{inserted_rows} baris berhasil dimasukkan ke database.")
            return inserted_rows
        else:
            print("Error: Fungsi insert_tokens_to_db tidak mengembalikan nilai yang valid.")
            return 0

    except Exception as e:
        print(f"Error processing file: {e}")
        return 0

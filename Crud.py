import mysql.connector

# Membaca file Excel yang sudah di-upload ke PythonAnywhere

# Koneksi ke MySQL di PythonAnywhere
conn = mysql.connector.connect(
    host='TselSikka.mysql.pythonanywhere-services.com',
    user='TselSikka',
    password='BranchSikka97',
    database='TselSikka$Token_Flotim'
)

cursor = conn.cursor()
def update_token_by_nomor(nomor_token, status):
    connection = None
    cursor = None
    try:
        # Koneksi ke database
        connection = mysql.connector.connect(
            host='TselSikka.mysql.pythonanywhere-services.com',
            user='TselSikka',
            password='BranchSikka97',
            database='TselSikka$Token_Flotim'
        )
        cursor = connection.cursor(buffered=True)  # Gunakan cursor buffered untuk menghindari hasil yang menggantung

        # Query untuk memperbarui status berdasarkan nomor token
        update_query = """
        UPDATE token_listrik
        SET status = %s
        WHERE nomor_token = %s
        """
        cursor.execute(update_query, (status, nomor_token))
        connection.commit()

        # Debugging: Tampilkan query yang dijalankan dan jumlah baris yang diupdate
        print(f"Query yang dijalankan: {update_query}, Nomor Token: {nomor_token}, Status: {status}")
        print(f"Baris yang diupdate: {cursor.rowcount}")

        # Mengecek apakah ada baris yang diupdate
        if cursor.rowcount == 0:
            return False, f"Tidak ada token ditemukan dengan nomor token {nomor_token}."

        # Mengambil kembali data yang diupdate
        select_query = """
        SELECT * FROM token_listrik
        WHERE nomor_token = %s
        """
        cursor.execute(select_query, (nomor_token,))
        updated_token = cursor.fetchone()  # Ambil satu baris hasil

        # Debugging: Periksa data yang diperbarui
        print(f"Data token yang diperbarui: {updated_token}")

        return True, updated_token

    except mysql.connector.Error as err:
        # Tangani error database
        print(f"Terjadi kesalahan pada database: {err}")
        return False, f"Terjadi kesalahan: {err}"

    finally:
        # Tutup koneksi dan cursor
        if cursor:
            cursor.close()
        if connection:
            connection.close()

import mysql.connector

def insert_tokens_to_db(data):
    try:
        connection = mysql.connector.connect(
            host='TselSikka.mysql.pythonanywhere-services.com',
            user='TselSikka',
            password='BranchSikka97',
            database='TselSikka$Token_Flotim'
        )
        cursor = connection.cursor()

        query = """
        INSERT INTO token_listrik (site_id, sitename, token_bulan, nomor_token, status)
        VALUES (%s, %s, %s, %s, %s)
        """

        # Menghitung jumlah token yang berhasil ditambahkan
        inserted_count = 0

        # Iterasi data
        for row in data:
            cursor.execute(query, row)  # row adalah tuple yang sudah siap digunakan

            # Increment jumlah yang berhasil dimasukkan
            inserted_count += 1

        connection.commit()
        return inserted_count  # Mengembalikan jumlah token yang berhasil ditambahkan

    except mysql.connector.Error as err:
        return False, f"Terjadi kesalahan: {err}"

    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

import aiomysql

async def delete_tokens(site_id=None):
    connection = None
    try:
        # Koneksi ke database secara asynchronous
        connection = await aiomysql.connect(
            host='TselSikka.mysql.pythonanywhere-services.com',
            user='TselSikka',
            password='BranchSikka97',
            db='TselSikka$Token_Flotim'
        )

        async with connection.cursor() as cursor:
            # Query untuk menghapus data berdasarkan site_id
            query = "DELETE FROM token_listrik WHERE site_id = %s"
            await cursor.execute(query, (site_id,))
            await connection.commit()

            # Periksa jumlah baris yang dihapus
            if cursor.rowcount == 0:
                return False, f"Tidak ada data ditemukan untuk Site ID {site_id}."
            return True, f"{cursor.rowcount} data berhasil dihapus untuk Site ID {site_id}."

    except Exception as err:
        # Menangani error yang terjadi
        return False, f"Terjadi kesalahan: {err}"

    finally:
        # Pastikan koneksi ditutup jika sudah dibuka
        if connection:
            await connection.ensure_closed()

async def delete_tokens_by_month(token_bulan=None):
    try:
        # Koneksi ke database dengan aiomysql (asynchronous MySQL driver)
        connection = await aiomysql.connect(
            host='TselSikka.mysql.pythonanywhere-services.com',
            user='TselSikka',
            password='BranchSikka97',
            db='TselSikka$Token_Flotim'
        )
        async with connection.cursor() as cursor:
            # Query untuk menghapus data berdasarkan token_bulan
            query = "DELETE FROM token_listrik WHERE token_bulan = %s"
            await cursor.execute(query, (token_bulan,))
            await connection.commit()

            if cursor.rowcount == 0:
                return False, f"Tidak ada data ditemukan untuk bulan {token_bulan}."
            return True, f"{cursor.rowcount} data berhasil dihapus untuk bulan {token_bulan}."

    except Exception as err:
        return False, f"Terjadi kesalahan: {err}"

    finally:
        connection.close()


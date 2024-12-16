from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import pymysql
import logging
import nest_asyncio
import mysql.connector
from datetime import datetime

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
nest_asyncio.apply()

# Fungsi koneksi ke database
def connect_db():
    return pymysql.connect(
        host=".",
        user="",
        password="",
        database=""
    )

db_config = {
    'host': '',
    'user': '',  # Ganti dengan username Anda
    'password': '',  # Ganti dengan password Anda
    'database': '',  # Nama database Anda
}

# Koneksi ke database
connection = mysql.connector.connect(**db_config)



def log_user_access(user_id, action):
    connection = connect_db()
    with connection.cursor() as cursor:
        cursor.execute("INSERT INTO log_access (user_id, action, timestamp) VALUES (%s, %s, NOW())", (user_id, action))
    connection.commit()
    connection.close()


def get_access_logs():
    connection = connect_db()
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM log_access")
        logs = cursor.fetchall()
    connection.close()
    return logs


def insert_token(site_id, tgl_isi, nomor_token, status, token_bulan):
    connection = connect_db()
    with connection.cursor() as cursor:
        query = """
        INSERT INTO token_listrik (site_id, tgl_isi, nomor_token, status, token_bulan)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(query, (site_id, tgl_isi, nomor_token, status, token_bulan))  # Parameterized Query
        connection.commit()  # Commit perubahan
    connection.close()

async def error_handler(update, context):
    try:
        # Cek apakah update memiliki message
        if update and hasattr(update, "message") and update.message:
            user = update.message.from_user
            chat_id = update.message.chat_id
            # Tulis pesan error ke log
            print(f"Error dari user {user.username} ({user.id}) di chat {chat_id}: {context.error}")
            # Kirim pesan error ke pengguna
            await context.bot.send_message(chat_id=chat_id, text="Maaf, terjadi error. Silakan coba lagi.")

        # Cek apakah update berasal dari callback query
        elif update and hasattr(update, "callback_query") and update.callback_query:
            user = update.callback_query.from_user
            chat_id = update.callback_query.message.chat_id
            # Tulis pesan error ke log
            print(f"Error dari callback query user {user.username} ({user.id}) di chat {chat_id}: {context.error}")
            # Kirim pesan error ke pengguna
            await context.bot.send_message(chat_id=chat_id, text="Maaf, terjadi error pada permintaan callback.")

        # Jika jenis update tidak diketahui
        else:
            print("Error tidak diketahui:", context.error)

    except Exception as e:
        print(f"Terjadi error saat menangani error: {e}")


USER_MASTER_ID = 1232143 #MASUKAN USERID UNTUK MASTER 

async def master_command(update: Update, context):
    user_id = update.message.from_user.id
    if user_id == USER_MASTER_ID:
        await update.message.reply_text('Anda adalah user master. Silakan kirim file Excel untuk mengupdate data.')
    else:
        await update.message.reply_text('Anda tidak memiliki izin untuk mengakses perintah ini.')


# Handler untuk menampilkan user ID
async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    await update.message.reply_text(f'Your User ID is: {user_id}')

from telegram import Update


# Fungsi untuk mendapatkan seluruh data token berdasarkan Site ID
def get_all_tokens_by_site(site_id):
    connection = connect_db()
    tokens = []

    if connection is not None:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT token_bulan, nomor_token, status FROM token_listrik WHERE site_id=%s", (site_id,))
                tokens = cursor.fetchall()
        except Error as e:
            print(f"Error saat menjalankan query: {e}")
        finally:
            connection.close()
    else:
        print("Tidak dapat menghubungkan ke database.")

    return tokens

from telegram.ext import ContextTypes
# Fungsi untuk mendapatkan bulan unik dari token berdasarkan Site ID
def get_unique_months_by_site(site_id):
    connection = connect_db()
    with connection.cursor() as cursor:
        cursor.execute("SELECT DISTINCT token_bulan FROM token_listrik WHERE site_id=%s", (site_id,))
        months = cursor.fetchall()
    connection.close()
    return months

# Fungsi untuk mendapatkan token berdasarkan Site ID dan bulan
def get_tokens_by_site_and_month(site_id, bulan):
    connection = connect_db()
    with connection.cursor() as cursor:
        cursor.execute("SELECT nomor_token, status FROM token_listrik WHERE site_id=%s AND token_bulan=%s", (site_id, bulan))
        tokens = cursor.fetchall()
    connection.close()
    return tokens

# Handler untuk menampilkan bulan yang memiliki token berdasarkan Site ID
async def site_id_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    site_id = update.message.text  # Mendapatkan Site ID yang dikirim pengguna
    months = get_unique_months_by_site(site_id)

    if not months:
        await update.message.reply_text(f'Tidak ada token ditemukan untuk Site ID: {site_id}.')
        return

    # Buat keyboard untuk menampilkan bulan (hanya satu kali)
    keyboard = []
    for (month,) in months:
        # Jika `month` adalah objek datetime.date, tidak perlu menggunakan `strptime`
        if isinstance(month, str):
            tanggal_objek = datetime.strptime(month, '%Y-%m-%d')
        else:
            tanggal_objek = month  # Sudah dalam format datetime.date

        format_bulan = tanggal_objek.strftime('%B %y').lower()  # Contoh: 'september 24'
        keyboard.append([InlineKeyboardButton(format_bulan, callback_data=f"bulan_{month}")])

    # Simpan Site ID ke dalam user_data agar bisa diakses di handler berikutnya
    context.user_data['site_id'] = site_id

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f"Pilih bulan untuk Site ID {site_id}:", reply_markup=reply_markup)

# Handler untuk menampilkan token berdasarkan bulan yang dipilih
async def bulan_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Ambil bulan dari callback_data
    data = query.data.split('_')
    bulan = data[1]

    # Ambil Site ID dari user_data
    site_id = context.user_data.get('site_id')

    # Ambil token berdasarkan Site ID dan bulan
    tokens = get_tokens_by_site_and_month(site_id, bulan)
    token_set = set(tokens)

    if not tokens:
        await query.message.reply_text(f'Tidak ada token ditemukan untuk Site ID: {site_id} pada bulan {bulan}.')
        return

    # Tampilkan token yang tersedia untuk bulan yang dipilih
    token_text = '\n'.join([f"Token: {nomor_token}, Status: {status}" for nomor_token, status in token_set])
    await query.message.reply_text(f"Daftar Token untuk Site ID {site_id} pada bulan {bulan}:\n\n{token_text}")

async def starter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id1 = update.message.from_user.id
    print(f"User ID: {user_id1}")  # Menampilkan user ID di konsol
    await update.message.reply_text('Haloo! Tekan /myid untuk melihat ID Kamu.')



# Fungsi untuk menangani perintah "/start" dan memberikan petunjuk
async def intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Ambil nama pengguna (bisa berupa first_name atau username)
    user_name = update.message.from_user.first_name  # Bisa juga gunakan .username
    # Buat pesan petunjuk
    welcome_message = (
        f"Selamat datang pak : {user_name},\n"
        "Cara untuk menggunakan bot ini:\n"
        "- Ketik /siteid untuk mengakses data token.\n"
        "- Jika selesai menggunakan Token Harap Melakukan Update Status.\n"
        "- Cara Update Status ketik /update 1115-3121-2432-2123, Terpakai\n"
        "- Cara untuk menghapus token /delete MME001 \n"
        "- cara Untuk menghapus Token dengan satuan bulanan /delete_month mm/yy \n"
        "- Ikuti petunjuk di setiap langkah untuk mendapatkan informasi lebih lanjut."
    )

    # Kirim pesan ke pengguna
    await update.message.reply_text(welcome_message)



# Fungsi untuk menangani kesalahan
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Log error
    print(f"Error {context.error}")

    # Informasikan pengguna bahwa terjadi kesalahan
    if update.message:
        await update.message.reply_text('Terjadi kesalahan. Silakan coba lagi nanti.')
    if update and hasattr(update, "message") and update.message:# Lakukan sesuatu dengan update.message
        user_message = update.message.text
        await context.bot.send_message(chat_id=update.message.chat_id, text="Terjadi error, silakan coba lagi.")
    elif update and hasattr(update, "callback_query") and update.callback_query:
    # Jika error berasal dari callback query
        await context.bot.send_message(chat_id=update.callback_query.message.chat_id, text="Terjadi error pada callback.")
    else:
    # Jika jenis update tidak diketahui
        print("Error tidak dapat ditangani karena jenis update tidak diketahui.")




# Handler untuk menerima foto dan caption

# Koneksi ke database
from mysql.connector import Error
connection = None
def create_connection():
    try:
        # Ganti dengan informasi koneksi Anda
        connection = mysql.connector.connect(
            host='',  # Ganti dengan username Anda
            user='',  # Ganti dengan username Anda
            password='',  # Ganti dengan password database Anda
            database=''  # Ganti dengan nama database Anda
        )
        cursor = connection.cursor()
        if connection.is_connected():
            print("Koneksi ke MySQL berhasil!")
            return connection

    except Error as e:
        print(f"Error saat koneksi ke MySQL: {e}")
        return None
    finally:
        if cursor:
            cursor.close()
        if connection:
            connection.close()

from Crud import update_token_by_nomor   # Import fungsi dari file token_crud.py

# Fungsi untuk memproses perintah /update dari bot Telegram berdasarkan nomor token
async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Mendapatkan argumen dari pesan
        args = update.message.text.split(' ', 1)[1]
        nomor_token, status = [arg.strip() for arg in args.split(',')]

        # Debugging: Tampilkan nomor token dan status
        print(f"Nomor Token: {nomor_token}, Status: {status}")

        # Memanggil fungsi untuk mengupdate status token berdasarkan nomor token
        success, result = update_token_by_nomor(nomor_token, status)

        if success:
            updated_token = result
            response_message = (
                f"Token yang terupdate dengan nomor {nomor_token}:\n"
                f"Site ID: {updated_token[1]}, Site Name: {updated_token[2]},\n"

            )
            await update.message.reply_text(response_message)
        else:
            await update.message.reply_text(result)

    except IndexError:
        await update.message.reply_text("Format tidak valid. Gunakan format: /update NomorToken, Status")
    except Exception as e:
        await update.message.reply_text(f"Terjadi kesalahan: {str(e)}")


from telegram import Update
from handler_file import process_file
import os

# Daftar ID pengguna yang diizinkan (misalnya hanya master yang diizinkan)
ALLOWED_USERS = [764245690, 7060442428]  # Ganti dengan ID Telegram pengguna yang diizinkan

async def handle_file(update: Update, context):
    user_id = update.message.from_user.id  # Mendapatkan ID pengguna yang mengirimkan pesan

    # Cek apakah ID pengguna termasuk dalam daftar pengguna yang diizinkan
    if user_id not in ALLOWED_USERS:
        await update.message.reply_text("Anda tidak memiliki izin untuk mengupload file.")
        return

    document = update.message.document
    file = await document.get_file()  # Mengambil file Telegram

    # Menentukan path untuk menyimpan file
    file_path = os.path.join('downloads', document.file_name)

    # Mengunduh file ke path lokal
    await file.download_to_drive(file_path)

    # Memproses file yang diunduh dan memasukkan data ke database
    inserted_rows = process_file(file_path, user_id)

    if inserted_rows > 0:
        await update.message.reply_text(f"Berhasil menambahkan {inserted_rows} data token.")
    else:
        await update.message.reply_text("Gagal memproses file atau format file tidak sesuai.")


from telegram.ext import ContextTypes
from Crud import delete_tokens, delete_tokens_by_month

# Daftar user master yang diizinkan (ID Telegram pengguna yang boleh mengakses fitur CRUD)
USER_MASTER = [764245690, 7060442428]  # Ganti dengan ID Telegram Anda atau yang diizinkan

async def is_master_user(update: Update) -> bool:
    """Fungsi untuk memvalidasi apakah user adalah master user."""
    user_id = update.effective_user.id
    return user_id in USER_MASTER

# Fungsi untuk menghapus berdasarkan Site ID
async def delete_site(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_master_user(update):
        await update.message.reply_text("Anda tidak bisa melakukan tindakan ini.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Gunakan format: /delete <site_id>")
        return

    site_id = args[0]

    # Konfirmasi penghapusan data
    keyboard = [
        [
            InlineKeyboardButton("Ya", callback_data=f"confirm_delete_site_{site_id}"),
            InlineKeyboardButton("Tidak", callback_data="cancel"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Apakah Anda yakin ingin menghapus data untuk Site ID {site_id}?",
        reply_markup=reply_markup,
    )

# Callback untuk konfirmasi penghapusan Site ID
async def confirm_delete_site(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("confirm_delete_site_"):
        site_id = query.data.split("_")[-1]
        result, message = await delete_tokens(site_id=site_id)
        await query.edit_message_text(message)

    elif query.data == "cancel":
        await query.edit_message_text("Hapus dibatalkan.")

# Fungsi untuk menghapus berdasarkan bulan
async def delete_by_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_master_user(update):
        await update.message.reply_text("Anda tidak memiliki izin untuk melakukan tindakan ini.")
        return

    if not context.args:
        await update.message.reply_text("Gunakan format: /delete_month <MM/YYYY>")
        return

    token_bulan = context.args[0]
    mysql_date = convert_to_mysql_date(token_bulan)

    if not mysql_date:
        await update.message.reply_text("Format bulan tidak valid. Gunakan format MM/YYYY.")
        return

    # Konfirmasi penghapusan data berdasarkan bulan
    keyboard = [
        [
            InlineKeyboardButton("Ya", callback_data=f"confirm_delete_month_{mysql_date}"),
            InlineKeyboardButton("Tidak", callback_data="cancel"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"Apakah Anda yakin ingin menghapus data untuk bulan {token_bulan}?",
        reply_markup=reply_markup,
    )

# Callback untuk konfirmasi penghapusan bulan
async def confirm_delete_month(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("confirm_delete_month_"):
        token_bulan = query.data.split("_")[-1]
        success, message = await delete_tokens_by_month(token_bulan=token_bulan)
        await query.edit_message_text(message)

    elif query.data == "cancel":
        await query.edit_message_text("Operasi dibatalkan.")

# Fungsi untuk mengonversi bulan ke format MySQL
def convert_to_mysql_date(month_year):
    try:
        from datetime import datetime
        date_obj = datetime.strptime(month_year, "%m/%Y")
        return date_obj.strftime("%Y-%m-01")
    except ValueError:
        return None


# Setup bot_______________________________________________________________________________________________________
app = ApplicationBuilder().token('MASUKAN API BOT ANDA').build()

# Tambahkan handler
app.add_handler(CommandHandler("help", intro))
app.add_handler(CommandHandler("cek", starter))
app.add_handler(CommandHandler("master",master_command))
app.add_handler(CommandHandler("site_id", site_id_handler))  # Misalnya, jika Anda memanggilnya dengan perintah /site_id
app.add_handler(CallbackQueryHandler(bulan_handler, pattern=r"bulan_"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, site_id_handler))
app.add_handler(MessageHandler(filters.Document.FileExtension("xlsx"), handle_file))
app.add_handler(CommandHandler("update", update_command))
app.add_handler(CommandHandler("myid", my_id))
app.add_handler(CommandHandler("delete", delete_site))
app.add_handler(CommandHandler("delete_month", delete_by_month))
app.add_handler(CallbackQueryHandler(confirm_delete_site, pattern="^confirm_delete_site_.*"))
app.add_handler(CallbackQueryHandler(confirm_delete_month, pattern="^confirm_delete_month_.*"))
app.add_handler(CallbackQueryHandler(confirm_delete_site, pattern="cancel"))
app.add_error_handler(error_handler)
app.add_error_handler(error_handler)
# Jalankan bot
app.run_polling()
import asyncio
import importlib

from pyrogram import filters
from pyrogram.enums import SentCodeType
from pyrogram.errors import *
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from Xadega import Ubot, bot, ubot
from Xadega.config import *
from Xadega.modules import ALL_MODULES
from Xadega.utils.data import *
from Xadega.utils.misc import extract_user, restart


@bot.on_message(filters.command("start") & filters.private)
async def start_bot(c, m):
    if m.from_user.id not in OWNER_ID:
        buat = [
            [
                InlineKeyboardButton("🔥 Buat Userbot 🔥", callback_data="add_ubot"),
            ]
        ]
    else:
        buat = [
            [
                InlineKeyboardButton("🔥 Buat Userbot 🔥", callback_data="add_ubot"),
                InlineKeyboardButton("💡 Daftar Userbot 💡", callback_data="get_ubot"),
            ]
        ]
    await m.reply(
        f"👋 Hallo {m.from_user.mention}\n\n🤖 Saya {c.me.mention}\n\n☑️ Klik Tombol Dibawah Jika Mau Membuat Userbot \n",
        reply_markup=InlineKeyboardMarkup(buat),
    )


@bot.on_callback_query(filters.regex("add_ubot"))
async def _(_, callback_query):
    user_id = callback_query.from_user.id
    if user_id not in MEMBERS and user_id not in OWNER_ID:
        admin = [
            [
                InlineKeyboardButton("🧑‍💻 Admin", url="t.me/xadega"),
            ]
        ]
        return await callback_query.message.edit(
            text=f"**{callback_query.from_user.mention} silahkan hubungi admin untuk mendapat akses membuat userbot**",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(admin),
        )
    buat = [
        [
            InlineKeyboardButton("🔥 Buat Userbot 🔥", callback_data="add_ubot"),
        ]
    ]
    await callback_query.message.delete()
    api_id_msg = await bot.ask(
        user_id, "**Tolong berikan saya API_ID**", filters=filters.text
    )
    if await is_cancel(callback_query, api_id_msg.text):
        return
    try:
        api_id = int(api_id_msg.text)
    except ValueError:
        await api_id_msg.reply(
            "Bukan API_ID yang valid (yang harus bilangan bulat). Silakan ulang kembali",
            quote=True,
            reply_markup=InlineKeyboardMarkup(buat),
        )
        return
    api_hash_msg = await bot.ask(
        user_id, "**Tolong berikan saya API_HASH**", filters=filters.text
    )
    if await is_cancel(callback_query, api_hash_msg.text):
        return
    api_hash = api_hash_msg.text
    try:
        phone = await bot.ask(
            user_id,
            (
                "**Silahkan Masukkan Nomor Telepon Telegram Anda Dengan Format Kode Negara.\nContoh: +628xxxxxxx**\n"
                "\n**Gunakan /cancel untuk Membatalkan Proses Membuat Userbot**"
            ),
            timeout=300,
        )

    except asyncio.TimeoutError:
        return await message.reply_text(
            "Batas waktu tercapai 5 menit. Proses Dibatalkan.",
            reply_markup=InlineKeyboardMarkup(buat),
        )
    if await is_cancel(callback_query, phone.text):
        return
    phone_number = phone.text
    new_client = Ubot(
        name=str(callback_query.id),
        api_id=api_id,
        api_hash=api_hash,
        in_memory=True,
    )
    await new_client.connect()
    try:
        code = await new_client.send_code(phone_number.strip())
    except Exception:
        code = await new_client.resend_code(
            phone_number.strip(), SentCodeType.EMAIL_CODE
        )
    except PhoneNumberInvalid:
        return await bot.send_message(
            user_id,
            "Nomor telepon tidak valid, silakan coba lagi",
            reply_markup=InlineKeyboardMarkup(buat),
        )
    except PhoneNumberBanned:
        return await bot.send_message(
            user_id, "Nomor telepon diblokir", reply_markup=InlineKeyboardMarkup(buat)
        )
    except PhoneNumberFlood:
        return await bot.send_message(
            user_id,
            "Nomor telepon terkena spam, harap menunggu",
            reply_markup=InlineKeyboardMarkup(buat),
        )
    except PhoneNumberUnoccupied:
        return await bot.send_message(
            user_id, "Nomor tidak terdaftar", reply_markup=InlineKeyboardMarkup(buat)
        )
    except BadRequest as error:
        return await bot.send_message(
            user_id,
            f"Terjadi kesalahan yang tidak diketahui: {error}",
            reply_markup=InlineKeyboardMarkup(buat),
        )

    try:
        otp = await bot.ask(
            user_id,
            (
                "**Silakan Periksa Kode OTP dari [Akun Telegram Resmi](tg://openmessage?user_id=777000). Kirim Kode OTP ke sini setelah membaca Format di bawah ini.**\n"
                "\nJika Kode OTP adalah `12345` Tolong **[ TAMBAHKAN SPASI ]** kirimkan Seperti ini `1 2 3 4 5`\n"
                "\n__Jika code tidak muncul silahkan cek email kamu__"
                "\n**Gunakan /cancel untuk Membatalkan Proses Membuat Userbot**"
            ),
            timeout=300,
        )

    except asyncio.TimeoutError:
        return await bot.send_message(
            user_id,
            "Batas waktu tercapai 5 menit. Proses Dibatalkan.",
            reply_markup=InlineKeyboardMarkup(buat),
        )
    if await is_cancel(callback_query, otp.text):
        return
    otp_code = otp.text
    try:
        await new_client.sign_in(
            phone_number.strip(),
            code.phone_code_hash,
            phone_code=" ".join(str(otp_code)),
        )
    except PhoneCodeInvalid:
        return await bot.send_message(
            user_id,
            "Kode yang Anda kirim tampaknya Tidak Valid, Coba lagi.",
            reply_markup=InlineKeyboardMarkup(buat),
        )
    except PhoneCodeExpired:
        return await bot.send_message(
            user_id,
            "Kode yang Anda kirim tampaknya Kedaluwarsa. Coba lagi.",
            reply_markup=InlineKeyboardMarkup(buat),
        )
    except BadRequest as error:
        return await bot.send_message(
            user_id,
            f"Terjadi kesalahan yang tidak diketahui: {error}",
            reply_markup=InlineKeyboardMarkup(buat),
        )
    except SessionPasswordNeeded:
        try:
            two_step_code = await bot.ask(
                user_id,
                "**Akun anda Telah mengaktifkan Verifikasi Dua Langkah. Silahkan Kirimkan Passwordnya.\n\nGunakan /cancel untuk Membatalkan Proses Membuat Userbot**",
                timeout=300,
            )
        except asyncio.TimeoutError:
            return await bot.send_message(
                user_id,
                "Batas waktu tercapai 5 menit.",
                reply_markup=InlineKeyboardMarkup(buat),
            )
        if await is_cancel(callback_query, two_step_code.text):
            return
        new_code = two_step_code.text
        try:
            await new_client.check_password(new_code)
        except BadRequest:
            return await bot.send_message(
                user_id,
                "Kata sandi salah, coba lagi",
                reply_markup=InlineKeyboardMarkup(buat),
            )
    session_string = await new_client.export_session_string()
    await new_client.disconnect()
    new_client.storage.session_string = session_string
    new_client.in_memory = False
    await new_client.start()
    try:
        tai = await new_client.create_supergroup(
            "Xadega-Logs", "Powered by : @xadega"
        )
        await new_client.set_chat_photo(tai.id, photo="logs/Xadega.jpg")
        await add_config(
            int(user_id),
            "https://telegra.ph//file/b7cc3bcbe25246edda7e2.jpg",
            int(tai.id),
            "on",
            "on",
        )
    except Exception as e:
        return await bot.send_message(
            user_id,
            f"**Error**: {e}",
        )
    await add_ubot(
        user_id=int(new_client.me.id),
        api_id=api_id,
        api_hash=api_hash,
        session_string=session_string,
    )
    for mod in ALL_MODULES:
        importlib.reload(importlib.import_module(f"Xadega.modules.{mod}"))

    text_done = (
        f"**🔥 {bot.me.mention} Berhasil Diaktifkan Di Akun: {new_client.me.mention}"
    )
    await bot.send_message(
        user_id,
        text_done
        + "\nSilahkan ketik .ping untuk cek userbot apakah sudah aktif apa belum",
        disable_web_page_preview=True,
    )
    buat = [
        [
            InlineKeyboardButton(
                f"🔥 Pembuat Userbot {callback_query.from_user.first_name} 🔥",
                user_id=callback_query.from_user.id,
            ),
        ]
    ]

    await bot.send_message(
        LOG_GRP,
        text_done,
        reply_markup=InlineKeyboardMarkup(buat),
        disable_web_page_preview=True,
    )


@bot.on_callback_query(filters.regex("get_ubot"))
async def _(_, callback_query):
    user_id = callback_query.from_user.id
    if user_id not in OWNER_ID:
        return
    await callback_query.message.delete()
    for ub in ubot._ubot:
        list_ubot = f"🤖 **Xadega Robot:** {bot.me.mention}\n\n"
        if ub.me.id == ubot.me.id:
            list_ubot += f"**👤 Userbot Utama:** [{ub.me.first_name}](tg://openmessage?user_id={ub.me.id})"

        else:
            list_ubot += f"**👤 Userbot:** [{ub.me.first_name}](tg://openmessage?user_id={ub.me.id})"
        msg_list_ubot = await bot.send_message(
            user_id,
            list_ubot,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "📁 Hapus Dari Database 📁",
                            callback_data=f"del_ubot {ub.me.id}",
                        )
                    ]
                ]
            ),
            disable_web_page_preview=True,
        )
        await asyncio.sleep(1)


@bot.on_callback_query(filters.regex("del_ubot"))
async def _(_, callback_query):
    user_id = callback_query.from_user.id
    del_id = callback_query.data.split()[1]
    if user_id not in OWNER_ID:
        return
    try:
        await callback_query.message.delete()
        await bot.send_message(
            user_id, f"** ✅ {del_id} Berhasil Dihapus Dari Database**"
        )
        await bot.send_message(
            int(del_id),
            "**Peringatan**‼️\n\nMasa aktif userbot anda telah habis silahkan hubungi admin untuk mengaktifkan kembali\nUntuk informasi lebih lanjut kontak kami di @XadegaSupportBot",
        )
        await remove_ubot(str(del_id))
        await asyncio.sleep(2)
        await restart()
    except BadRequest:
        await callback_query.message.delete()
        await bot.send_message(
            user_id,
            f"** ✅ {del_id} Berhasil Dihapus Dari Database**",
        )
        await bot.send_message(
            int(del_id),
            "**Peringatan**‼️\n\nMasa aktif userbot anda telah habis silahkan hubungi admin untuk mengaktifkan kembali\nUntuk informasi lebih lanjut kontak kami di @XadegaSupportBot",
        )
        await remove_ubot(srt(del_id))
        await asyncio.sleep(2)
        await restart()


async def is_cancel(callback_query, text):
    if text.startswith("/cancel"):
        await bot.send_message(callback_query.from_user.id, "**Membatalkan Proses!**")
        return True
    return False


@bot.on_message(filters.command("prem"))
@ubot.on_message(filters.command("prem", PREFIX) & filters.me)
async def add_members(c, m):
    if m.from_user.id not in OWNER_ID:
        return
    args = await extract_user(m)
    reply = m.reply_to_message
    ex = await m.reply("Processing...")
    if args:
        try:
            user = await c.get_users(args)
        except Exception:
            await ex.edit(f"__User tidak ditemukan__")
            return
    elif reply:
        user_id = reply.from_user.id
        user = await c.get_users(user_id)
    else:
        await ex.edit(f"User tidak di temukan")
        return

    try:
        if user.id in MEMBERS:
            return await ex.edit("__User sudah menjadi member__")
        MEMBERS.append(user.id)
        await ex.edit(f"{user.mention} ditambahkan ke members")

    except Exception as e:
        await ex.edit(f"**ERROR:** `{e}`")
        return


@bot.on_message(filters.command("unprem"))
@ubot.on_message(filters.command("unprem", PREFIX) & filters.me)
async def del_members(c, m):
    if m.from_user.id not in OWNER_ID:
        return
    args = await extract_user(m)
    reply = m.reply_to_message
    ex = await m.reply_text("Processing...")
    if args:
        try:
            user = await c.get_users(args)
        except Exception:
            await ex.edit(f"User tidak di temukan")
            return
    elif reply:
        user_id = reply.from_user.id
        user = await c.get_users(user_id)
    else:
        await ex.edit(f"User tidak di temukan")
        return
    try:
        if user.id not in MEMBERS:
            return await ex.edit("__User bukan bagian dari members**")
        MEMBERS.remove(user.id)
        await ex.edit(f"{user.mention} Sudah dihapus dari members")

    except Exception as e:
        await ex.edit(f"**ERROR:** `{e}`")
        return



@bot.on_message(filters.command("restart"))
async def restartbot(client, message):
    await message.reply(
        "**Apakah kamu yakin ingin memulai ulang userbot?**",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("✅ Ya", callback_data="_rest ya_restart"),
                    InlineKeyboardButton(
                        "❌ Tidak", callback_data="_rest tidak_restart"
                    ),
                ],
            ]
        ),
    )


@bot.on_callback_query(filters.regex("_rest"))
async def _(_, callback_query):
    data = callback_query.data.split()[1]
    if callback_query.from_user.id not in OWNER_ID and not await seller_info(
        callback_query.from_user.id
    ):
        return await callback_query.message.reply(
            "**Maaf perintah ini khusus pembuat dan admin**"
        )
    if data == "ya_restart":
        await callback_query.message.edit("**__Mulai merestart userbot__**")
        await restart()
    if data == "tidak_restart":
        await callback_query.message.delete()

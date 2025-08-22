# app/handlers/user.py
from telegram import Update, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from ..db import upsert_user, add_vote, audit, _db
from ..keyboards import ask_contact_kb, ask_screenshot_kb
from ..config import REGION_NAME, ADMIN_IDS

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (update.message.text or "").strip()
    if txt == "↩️ Bekor":
        context.user_data.pop("current_phone", None)
        await update.message.reply_text("Bekor qilindi.", reply_markup=ReplyKeyboardRemove())
    elif txt == "📷 Skrin yuborish":
        if not context.user_data.get("current_phone"):
            await update.message.reply_text(
                "Avval telefon raqamingizni kontakt sifatida ulashing, so‘ng skrin yuboring.",
                reply_markup=ask_contact_kb()
            )
        else:
            await update.message.reply_text("Skrin yuboring (rasm sifatida).")

async def on_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    upsert_user(u)

    phone = context.user_data.get("current_phone")
    if not phone:
        await update.message.reply_text(
            "Avval telefon raqamingizni kontakt orqali ulashing. Keyin skrin yuboring.",
            reply_markup=ask_contact_kb()
        )
        return

    file_id = update.message.photo[-1].file_id
    vote_id = add_vote(u.id, file_id, phone)

    await update.message.reply_text(
        f"Rahmat! Tasdiqlashga yuborildi. Ariza ID: #{vote_id}\n"
        f"Admin tekshiradi va natijani xabar qilamiz.",
        reply_markup=ReplyKeyboardRemove()
    )

    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve:{vote_id}"),
        InlineKeyboardButton("❌ Rad etish",  callback_data=f"reject:{vote_id}")
    ]])
    caption = (f"🆕 Yangi tasdiq so‘rovi\n"
               f"ID: #{vote_id}\n"
               f"User: {u.full_name} (@{u.username or ''}) id={u.id}\n"
               f"Hudud: {REGION_NAME}\n"
               f"Telefon: {phone}")
    for admin in ADMIN_IDS:
        try:
            await context.bot.send_photo(admin, file_id, caption=caption, reply_markup=kb)
        except Exception:
            pass

async def on_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c = update.message.contact
    upsert_user(update.effective_user, phone=c.phone_number)
    context.user_data["current_phone"] = c.phone_number
    await update.message.reply_text(
        f"Rahmat! Kontakt saqlandi: {c.phone_number}\nEndi 🖼️ skrin yuboring.",
        reply_markup=ask_screenshot_kb()
    )
    audit(update.effective_user.id, "contact_saved", c.phone_number)

# <<< SIZDA YO'Q EDI: shu ikki funksiya qo'shildi >>>
async def cmd_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # ixtiyoriy kontakt yig‘ish tugmasi
    await update.message.reply_text(
        "Eslatma uchun ixtiyoriy kontaktni ulashing. /privacy",
        reply_markup=ask_contact_kb()
    )

async def cmd_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # saqlangan telefonni bazadan tozalaymiz va sessionni tozalaymiz
    con = _db()
    con.execute("UPDATE users SET phone='' WHERE tg_id=?", (update.effective_user.id,))
    con.commit(); con.close()
    context.user_data.pop("current_phone", None)
    await update.message.reply_text("Obuna bekor qilindi, kontakt o‘chirildi. ✅", reply_markup=ReplyKeyboardRemove())

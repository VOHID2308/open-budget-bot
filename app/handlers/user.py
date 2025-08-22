from telegram import Update, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import re

from ..db import upsert_user, add_vote, audit
from ..keyboards import ask_contact_kb, ask_screenshot_kb, ask_payout_choice_kb
from ..config import REGION_NAME, ADMIN_IDS

PHONE_CHOICE = "📱 Telefon raqamga"
CARD_CHOICE  = "💳 Karta raqamga"
CANCEL_BTN   = "↩️ Bekor"

def _clean_number(s: str) -> str:
    # raqam va + belgilarini qoldiramiz
    return re.sub(r"[^\d+]", "", s or "")

def _valid_phone(s: str) -> bool:
    s = _clean_number(s)
    return len(s) >= 9  # minimal tekshiruv

def _valid_card(s: str) -> bool:
    s = re.sub(r"\s+", "", s or "")
    return s.isdigit() and 12 <= len(s) <= 20  # karta uzunligi taxminiy

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (update.message.text or "").strip()

    # Bekor
    if txt == CANCEL_BTN:
        context.user_data.pop("current_phone", None)
        context.user_data.pop("pending_proof_file_id", None)
        context.user_data.pop("payout_choice", None)
        await update.message.reply_text("Bekor qilindi.", reply_markup=ReplyKeyboardRemove())
        return

    # Skrin yuborishni qulay tugma
    if txt == "📷 Skrin yuborish":
        if not context.user_data.get("current_phone"):
            await update.message.reply_text(
                "Avval telefon raqamingizni kontakt sifatida ulashing, so‘ng skrin yuboring.",
                reply_markup=ask_contact_kb()
            )
        else:
            await update.message.reply_text("Skrin yuboring (rasm sifatida).")
        return

    # To'lov tanlovi bosqichi
    if txt in (PHONE_CHOICE, CARD_CHOICE):
        if not context.user_data.get("pending_proof_file_id"):
            await update.message.reply_text("Avval skrin yuboring.", reply_markup=ask_screenshot_kb())
            return
        context.user_data["payout_choice"] = "phone" if txt == PHONE_CHOICE else "card"
        if txt == PHONE_CHOICE:
            await update.message.reply_text(
                "Telefon raqamingizni kiriting (masalan: +99890xxxxxxx).",
                reply_markup=ReplyKeyboardRemove()
            )
        else:
            await update.message.reply_text(
                "Karta raqamingizni kiriting (raqamlar, masalan: 8600 xxxx xxxx xxxx).",
                reply_markup=ReplyKeyboardRemove()
            )
        return

    # Agar payout_choice o'rnatilgan bo'lsa — user raqam/karta yubormoqda
    if context.user_data.get("payout_choice") == "phone":
        if _valid_phone(txt):
            context.user_data["payout_value"] = _clean_number(txt)
            await _finalize_submission(update, context)
        else:
            await update.message.reply_text("Telefon raqami noto‘g‘ri. Iltimos, to‘g‘ri formatda kiriting.")
        return

    if context.user_data.get("payout_choice") == "card":
        if _valid_card(txt):
            context.user_data["payout_value"] = re.sub(r"\s+", "", txt)
            await _finalize_submission(update, context)
        else:
            await update.message.reply_text("Karta raqami noto‘g‘ri. Faqat raqam va to‘g‘ri uzunlikda kiriting.")
        return

    # Boshqa matnlar — e'tibor bermaymiz
    await update.message.reply_text(
        "Nima qilamiz? Avval kontakt yuboring, so‘ng skrin yuboring. Keyin to‘lov turini tanlaysiz.",
        reply_markup=ask_contact_kb()
    )

async def _finalize_submission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Skrin + payout tanlanganidan so'ng, ovoz yozuvini bazaga qo'shish va adminga yuborish."""
    u = update.effective_user
    pay_type = context.user_data.get("payout_choice")   # 'phone' | 'card'
    pay_value = context.user_data.get("payout_value")   # raqam/karta
    proof_file_id = context.user_data.get("pending_proof_file_id")
    phone = context.user_data.get("current_phone")

    if not (pay_type and pay_value and proof_file_id and phone):
        await update.message.reply_text("Ma’lumotlar yetarli emas. Avval kontakt va skrin yuboring.")
        return

    # Bazaga yozamiz
    vote_id = add_vote(u.id, proof_file_id, phone, pay_type, pay_value)

    # Userga bildirish
    await update.message.reply_text(
        f"Rahmat! Tasdiqlashga yuborildi. Ariza ID: #{vote_id}\n"
        f"Admin tekshiradi va natijani xabar qiladi.",
        reply_markup=ReplyKeyboardRemove()
    )

    # Adminga yuboramiz
    from ..config import REGION_NAME
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve:{vote_id}"),
        InlineKeyboardButton("❌ Rad etish",  callback_data=f"reject:{vote_id}")
    ]])
    caption = (f"🆕 Yangi tasdiq so‘rovi\n"
               f"ID: #{vote_id}\n"
               f"User: {u.full_name} (@{u.username or ''}) id={u.id}\n"
               f"Hudud: {REGION_NAME}\n"
               f"Telefon (1-mavsum nazorati): {phone}\n"
               f"To‘lov turi: {'Telefon raqam' if pay_type=='phone' else 'Karta raqam'}\n"
               f"To‘lov ma’lumoti: {pay_value}")
    for admin in ADMIN_IDS:
        try:
            await context.bot.send_photo(admin, proof_file_id, caption=caption, reply_markup=kb)
        except Exception:
            pass

    # Sessionni tozalaymiz
    context.user_data.pop("pending_proof_file_id", None)
    context.user_data.pop("payout_choice", None)
    context.user_data.pop("payout_value", None)
    audit(u.id, "vote_finalized", f"id={vote_id}, pay_type={pay_type}")

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
    # Endi darhol bazaga yozmaymiz. Avval to'lov turini so'raymiz.
    context.user_data["pending_proof_file_id"] = file_id

    await update.message.reply_text(
        "Qabul qilindi. To‘lov usulini tanlang:",
        reply_markup=ask_payout_choice_kb()
    )

async def on_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    c = update.message.contact
    upsert_user(update.effective_user, phone=c.phone_number)
    context.user_data["current_phone"] = c.phone_number
    await update.message.reply_text(
        f"Rahmat! Kontakt saqlandi: {c.phone_number}\nEndi 🖼️ skrin yuboring.",
        reply_markup=ask_screenshot_kb()
    )
    audit(update.effective_user.id, "contact_saved", c.phone_number)

# Ixtiyoriy subscribe/unsubscribe (oldingidek)
async def cmd_subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Eslatma uchun ixtiyoriy kontaktni ulashing. /privacy",
        reply_markup=ask_contact_kb()
    )

async def cmd_unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from ..db import _db
    con = _db()
    con.execute("UPDATE users SET phone='' WHERE tg_id=?", (update.effective_user.id,))
    con.commit(); con.close()
    context.user_data.pop("current_phone", None)
    await update.message.reply_text("Obuna bekor qilindi, kontakt o‘chirildi. ✅", reply_markup=ReplyKeyboardRemove())

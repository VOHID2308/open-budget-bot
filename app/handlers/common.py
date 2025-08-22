from telegram import Update
from telegram.ext import ContextTypes
import os

from ..db import upsert_user, top_rows
from ..texts import RULES_TEXT, PRIVACY_TEXT
from ..keyboards import main_menu, ask_contact_kb, ask_screenshot_kb
from .. import config  # runtime o'zgarishlar uchun modulni o'zini o'qiymiz

# /start
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    upsert_user(u, region=config.REGION_NAME)
    text = (
        f"Assalomu alaykum, {u.first_name or 'do‘st'}!\n\n"
        f"Bu bot {config.REGION_NAME} uchun **halol** ishtirokni rag‘batlantiradi:\n"
        f"1) Rasmiy sahifada ovoz bering;\n"
        f"2) Kontakt yuboring → skrin yuboring → admin tasdiqlaydi → ball olasiz;\n"
        f"3) /top da reyting.\n\n"
        f"👇 Pastdagi tugmalarni ishlating."
    )
    await update.message.reply_text(text, reply_markup=main_menu())

# /help
async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start – bosh menyu\n"
        "/vote – rasmiy sahifani ochish\n"
        "/me – mening ballarim\n"
        "/top – reyting\n"
        "/rules – qoidalar\n"
        "/privacy – maxfiylik\n"
        "/subscribe – eslatma uchun kontakt berish (ixtiyoriy)\n"
        "/unsubscribe – obunani bekor qilish\n"
        "/export_csv – (admin) foydalanuvchilar CSV\n"
        "/pending – (admin) kutayotganlar ro‘yxati\n"
        "/setseason <id> – (admin) mavsum ID\n"
        "/seturl <url> – (admin) rasmiy sahifa URL\n"
        "/myid – (admin) o‘z ID\n"
        "/voters [N] [all] – (admin) oxirgi N ta approved ovoz\n"
        "/topdetail [N] [all] – (admin) TOP foydalanuvchilar + telefonlar\n"
        "/votes_csv [all] – (admin) approved ovozlar CSV\n"
        "/debug – joriy sozlamalarni tekshirish"
    )

# Inline callbacklar (menyu tugmalari)
async def on_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    if data == "voted":
        if not context.user_data.get("current_phone"):
            await q.message.reply_text(
                "Avval telefon raqamingizni kontakt tarzida ulashing.",
                reply_markup=ask_contact_kb()
            )
        else:
            await q.message.reply_text(
                "Endi skrin yuboring (rasm sifatida).",
                reply_markup=ask_screenshot_kb()
            )
    elif data == "top":
        await send_top(q.message)
    elif data == "rules":
        await q.message.reply_text(RULES_TEXT)
    elif data == "privacy":
        await q.message.reply_text(PRIVACY_TEXT)

# /vote
async def cmd_vote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Hudud: {config.REGION_NAME}\n"
        f"Ovoz berish rasmiy sahifada amalga oshiriladi:\n{config.VOTE_URL}"
    )

# /rules
async def cmd_rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(RULES_TEXT)

# /privacy
async def cmd_privacy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(PRIVACY_TEXT)

# Ichki: reytingni yuborish
async def send_top(target_message):
    rows = top_rows()
    if not rows:
        await target_message.reply_text("Hali reyting yo‘q. Birinchi bo‘lib ball oling! 🏁")
        return
    out = ["🏆 Reyting:"]
    for i, r in enumerate(rows, 1):
        tag = f"@{r['username']}" if r["username"] else r["full_name"]
        out.append(f"{i}. {tag} — {r['score']} ball")
    await target_message.reply_text("\n".join(out))

# /top
async def cmd_top(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await send_top(update.message)

# /me
async def cmd_me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    from ..db import _db
    con = _db()
    row = con.execute("SELECT score, region FROM users WHERE tg_id=?", (u.id,)).fetchone()
    con.close()
    score = row["score"] if row else 0
    region = row["region"] if row else config.REGION_NAME
    await update.message.reply_text(
        f"👤 Siz: {u.full_name}\n📍 Hudud: {region}\n🎯 Ball: {score}\n🗓 Mavsum: {config.SEASON_ID}"
    )

# /debug — .env va config’dagi qiymatlarni ko‘rsatish
async def cmd_debug(update: Update, context: ContextTypes.DEFAULT_TYPE):
    raw_env_vote = os.getenv("VOTE_URL", "(env-da topilmadi)")
    await update.message.reply_text(
        "🔧 DEBUG\n"
        f"REGION_NAME: {config.REGION_NAME}\n"
        f"SEASON_ID:   {config.SEASON_ID}\n"
        f"VOTE_URL (config): {config.VOTE_URL}\n"
        f"VOTE_URL (.env raw): {raw_env_vote}"
    )

# /seturl <url> — ADMIN: rasmiy sahifa URL'ini runtime'da yangilash
async def cmd_seturl(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from ..config import ADMIN_IDS
    u = update.effective_user
    if u.id not in ADMIN_IDS:
        return
    parts = (update.message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("Foydalanish: /seturl https://openbudget.uz/boards/initiatives/initiative/...")
        return
    new_url = parts[1].strip()
    config.VOTE_URL = new_url  # runtime yangilanadi
    await update.message.reply_text(
        "✅ VOTE_URL yangilandi.\n"
        f"Yangi qiymat: {config.VOTE_URL}\n\n"
        "Eslatma: yangi tugmani ko‘rish uchun /start yuboring."
    )

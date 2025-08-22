import io
import csv
from telegram import Update, InputFile
from telegram.ext import ContextTypes
from ..config import ADMIN_IDS
from ..db import (
    pending_rows, approve_vote, reject_vote, _db,
    approved_votes_detail, top_users_detail, export_votes_csv
)
from .. import config
from ..db import audit

def _is_admin(u) -> bool:
    return bool(u and u.id in ADMIN_IDS)

# Inline tasdiqlash/rad etish callbacklari
async def on_admin_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not _is_admin(q.from_user):
        await q.answer("Ruxsat yo‘q.", show_alert=True)
        return

    try:
        action, sid = q.data.split(":", 1)
        vote_id = int(sid)
    except Exception:
        await q.answer("Format xato.", show_alert=True)
        return

    # Tasdiqlash/rad etishda foydalanuvchiga bildirish uchun tg_id va to'lov ma'lumotlarini olib olamiz
    con = _db()
    row = con.execute("SELECT tg_id, pay_type, pay_value FROM votes WHERE id=?", (vote_id,)).fetchone()
    con.close()
    tg_id = row["tg_id"] if row else None

    if action == "approve":
        res = approve_vote(vote_id)
        msg = {
            "ok": "Tasdiqlandi ✅",
            "dup_phone": "Bu telefon raqami shu mavsumda allaqachon tasdiqlangan.",
            "not_pending": "Bu ID pending emas.",
            "not_found": "Topilmadi."
        }.get(res, "Xatolik.")
        await q.edit_message_caption((q.message.caption or "") + f"\n\nNatija: {msg}")
        await q.answer("OK")

        # Tasdiq muvaffaqiyatli bo'lsa — foydalanuvchiga xabar beramiz
        if res == "ok" and tg_id:
            try:
                await context.bot.send_message(
                    chat_id=tg_id,
                    text="✅ Skriningiz tasdiqlandi. To‘lov 24 soat ichida amalga oshiriladi. Rahmat!"
                )
            except Exception:
                pass

    elif action == "reject":
        res = reject_vote(vote_id)
        msg = "Rad etildi ❌" if res == "ok" else "Bu ID pending emas."
        await q.edit_message_caption((q.message.caption or "") + f"\n\nNatija: {msg}")
        await q.answer("OK")

        # Rad etilganda xohlasangiz foydalanuvchiga ham xabar berishingiz mumkin (ixtiyoriy)
        # if tg_id:
        #     await context.bot.send_message(chat_id=tg_id, text="❌ Uzr, skriningiz rad etildi.")

async def cmd_pending(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user):
        return
    rows = pending_rows(30)
    if not rows:
        await update.message.reply_text("Pending yo‘q ✅")
        return
    text = "⏳ Pending ro‘yxati:\n" + "\n".join(
        [f"#{r['id']} • tg_id={r['tg_id']} • {r['created_at']}" for r in rows]
    )
    await update.message.reply_text(
        text + "\n\nTasdiqlash inline tugmalar orqali yuborilgan surat xabarida amalga oshiriladi."
    )

async def cmd_export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user):
        return
    con = _db()
    cur = con.cursor()
    cur.execute("""SELECT u.tg_id, u.full_name, u.username, u.phone, u.region, u.score
                   FROM users u ORDER BY score DESC""")
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["tg_id","full_name","username","phone","region","score"])
    for row in cur.fetchall():
        w.writerow(row)
    buf.seek(0)
    data = io.BytesIO(buf.getvalue().encode("utf-8"))
    data.name = "users_export.csv"
    await update.message.reply_document(
        document=InputFile(data, filename="users_export.csv"),
        caption="Foydalanuvchilar (CSV)"
    )
    con.close()

async def cmd_setseason(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user):
        return
    parts = update.message.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("Foydalanish: /setseason 2025-II")
        return
    config.SEASON_ID = parts[1]
    await update.message.reply_text(f"Mavsum yangilandi: {config.SEASON_ID}")

async def cmd_myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
    await update.message.reply_text(f"Sizning Telegram ID: {update.effective_user.id}")
    audit(update.effective_user.id, "asked_myid", "")

async def cmd_voters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user):
        return
    args = (update.message.text or "").split()
    limit = 30
    season_only = True
    if len(args) >= 2:
        try:
            limit = max(1, min(100, int(args[1])))
        except:
            pass
    if len(args) >= 3 and args[2].lower() == "all":
        season_only = False

    rows = approved_votes_detail(limit=limit, season_only=season_only)
    if not rows:
        await update.message.reply_text("Tasdiqlangan ovozlar topilmadi.")
        return

    header = f"📋 Approved voters (last {len(rows)}) — season={'current '+config.SEASON_ID if season_only else 'ALL'}:"
    lines = [header]
    for r in rows:
        tag = f"@{r['username']}" if r['username'] else r['full_name']
        lines.append(
            f"#{r['id']} • {tag} (tg_id={r['tg_id']}) • tel: {r['phone'] or '-'} • "
            f"pay: {r['pay_type'] or '-'}:{r['pay_value'] or '-'} • {r['created_at']}"
        )

    text = "\n".join(lines)
    for chunk in [text[i:i+3500] for i in range(0, len(text), 3500)]:
        await update.message.reply_text(chunk)

async def cmd_topdetail(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user):
        return
    args = (update.message.text or "").split()
    limit = 20
    season_only = True
    if len(args) >= 2:
        try:
            limit = max(1, min(50, int(args[1])))
        except:
            pass
    if len(args) >= 3 and args[2].lower() == "all":
        season_only = False

    rows = top_users_detail(limit=limit, season_only=season_only)
    if not rows:
        await update.message.reply_text("Hali approved ovozlar yo‘q.")
        return

    header = f"🏆 TOP detail (top {len(rows)}) — season={'current '+config.SEASON_ID if season_only else 'ALL'}:"
    lines = [header]
    for i, r in enumerate(rows, 1):
        tag = f"@{r['username']}" if r['username'] else r['full_name']
        phones = (r['phones'] or "").replace(",", ", ")
        lines.append(f"{i}. {tag} (tg_id={r['tg_id']}) — {r['votes']} ovoz — tel: [{phones}]")

    text = "\n".join(lines)
    for chunk in [text[i:i+3500] for i in range(0, len(text), 3500)]:
        await update.message.reply_text(chunk)

async def cmd_votes_csv(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update.effective_user):
        return
    args = (update.message.text or "").split()
    season_only = not (len(args) >= 2 and args[1].lower() == "all")

    csv_str = export_votes_csv(season_only=season_only)
    data = csv_str.encode("utf-8")
    bio = io.BytesIO(data)
    bio.name = "approved_votes.csv"
    caption = "Tasdiqlangan ovozlar (CSV) — " + (f"season {config.SEASON_ID}" if season_only else "ALL")
    await update.message.reply_document(document=InputFile(bio, filename=bio.name), caption=caption)

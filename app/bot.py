import logging
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters
from .config import BOT_TOKEN
from .db import init_db
from .handlers.common import (
    cmd_start, cmd_help, cmd_vote, cmd_rules, cmd_privacy,
    cmd_top, cmd_me, on_cb, cmd_debug, cmd_seturl
)
from .handlers.user import (
    on_text, on_photo, cmd_subscribe, on_contact, cmd_unsubscribe
)
from .handlers.admin import (
    on_admin_cb, cmd_pending, cmd_export, cmd_setseason, cmd_myid,
    cmd_voters, cmd_topdetail, cmd_votes_csv
)

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

def run_app():
    if not BOT_TOKEN:
        raise SystemExit("BOT_TOKEN .env da yo‘q. Iltimos to‘ldiring.")
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    # Foydalanuvchi buyruqlari
    app.add_handler(CommandHandler("start",   cmd_start))
    app.add_handler(CommandHandler("help",    cmd_help))
    app.add_handler(CommandHandler("vote",    cmd_vote))
    app.add_handler(CommandHandler("rules",   cmd_rules))
    app.add_handler(CommandHandler("privacy", cmd_privacy))
    app.add_handler(CommandHandler("top",     cmd_top))
    app.add_handler(CommandHandler("me",      cmd_me))
    app.add_handler(CommandHandler("subscribe",   cmd_subscribe))
    app.add_handler(CommandHandler("unsubscribe", cmd_unsubscribe))
    app.add_handler(CommandHandler("debug",   cmd_debug))    # diagnostika
    app.add_handler(CommandHandler("seturl",  cmd_seturl))   # ADMIN: URL yangilash

    # Admin buyruqlari
    app.add_handler(CommandHandler("pending",    cmd_pending))
    app.add_handler(CommandHandler("export_csv", cmd_export))     # users CSV
    app.add_handler(CommandHandler("setseason",  cmd_setseason))
    app.add_handler(CommandHandler("myid",       cmd_myid))
    app.add_handler(CommandHandler("voters",     cmd_voters))     # approved votes list
    app.add_handler(CommandHandler("topdetail",  cmd_topdetail))  # top users + phones
    app.add_handler(CommandHandler("votes_csv",  cmd_votes_csv))  # approved votes CSV

    # Callbacklar
    app.add_handler(CallbackQueryHandler(on_admin_cb, pattern=r"^(approve|reject):\d+$"))
    app.add_handler(CallbackQueryHandler(on_cb))

    # Xabar turlari
    app.add_handler(MessageHandler(filters.PHOTO,   on_photo))
    app.add_handler(MessageHandler(filters.CONTACT, on_contact))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))

    log.info("Bot ishga tushdi.")
    app.run_polling(allowed_updates=["message", "callback_query"])

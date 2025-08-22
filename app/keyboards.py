from telegram import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from . import config  # VOTE_URL ni runtime'da o‘qiymiz

def main_menu():
    vote_url = config.VOTE_URL  # joriy qiymat
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🗳 Rasmiy sahifa", url=vote_url)],  # WebAppInfo emas, bevosita URL
        [InlineKeyboardButton("✅ Men ovoz berdim (skrin)", callback_data="voted")],
        [InlineKeyboardButton("🏆 Reyting", callback_data="top")],
        [InlineKeyboardButton("📜 Qoidalar", callback_data="rules"),
         InlineKeyboardButton("🔒 Maxfiylik", callback_data="privacy")]
    ])

def ask_screenshot_kb():
    return ReplyKeyboardMarkup(
        [["📷 Skrin yuborish", "↩️ Bekor"]],
        resize_keyboard=True, one_time_keyboard=True
    )

def ask_contact_kb():
    return ReplyKeyboardMarkup(
        [[KeyboardButton("📞 Kontaktni ulashish", request_contact=True)],
         [KeyboardButton("↩️ Bekor")]],
        resize_keyboard=True, one_time_keyboard=True
    )

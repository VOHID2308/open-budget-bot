# OpenBudget (Urgut Gʻoʻs) – Halol Leaderboard Bot

## Funksiyalar
- WebApp tugma orqali rasmiy sahifani ochish (bot ovoz bermaydi)
- Skrin asosida admin tasdiqlashi → ball
- Reyting (/top), shaxsiy profil (/me)
- Admin: inline approve/reject, /pending, /export_csv, /setseason, /myid
- Ixtiyoriy kontakt yig‘ish (/subscribe, /unsubscribe)

## O‘rnatish
1) Python 3.10+
2) `pip install -r requirements.txt`
3) `.env.example` → `.env`, qiymatlarni to‘ldiring
4) `python run.py`

## Muhim
- `.env` dagi `VOTE_URL` Urgut Gʻoʻs uchun aniq sahifa:
  `https://openbudget.uz/boards/initiatives/initiative/48/edabbad0-9f20-49c4-a019-f601c73adccd`
- Admin ID olish: botga `/myid` yozing, chiqqan raqamni `.env` dagi `ADMIN_IDS` ga kiriting

# Open Budget Voting Bot (Telegram)

## 📌 Overview

This project is a **Telegram bot** designed to manage and track a voting process (e.g., Open Budget initiatives) with user verification, screenshot proof submission, and an admin approval system.

The bot ensures:

* Each user participates through **verified phone numbers**
* Votes are supported with **proof (screenshot)**
* Admins can **review, approve, or reject submissions**
* A **leaderboard system** tracks the most active participants
* (Optional) **payout-ready structure** for future integrations

---

## 🚀 Features

### 👤 User Side

* `/start` — Introduction and instructions
* 📊 Vote button — Starts voting process
* 📱 Phone number verification (contact sharing)
* 📸 Screenshot submission as proof
* 💳 Payment method selection:

  * Phone number
  * Card number
* 📝 Input of payment details
* ✅ Confirmation message after submission

---

### 🛡️ Admin Side

* `/pending` — View pending submissions
* Approve / Reject buttons for each vote
* `/export_csv` — Export approved votes to CSV
* `/votes_csv` — Detailed vote records
* `/top` — Leaderboard
* `/seturl` — Change voting URL
* `/setseason` — Change season ID
* `/myid` — Get your Telegram ID

---

## 🧠 Core Logic

### ✅ Voting Flow

1. User starts bot
2. Clicks “Vote”
3. Shares phone number
4. Sends screenshot proof
5. Chooses payment method
6. Enters payment details
7. Submission sent to admin

---

### 🔒 Anti-Fraud Protection

* Each **phone number can only be approved once per season**
* Duplicate phone submissions are automatically rejected
* Admin manually verifies screenshots
* Optional duplicate screenshot detection (via file_id or hash)

---

### 📊 Leaderboard System

* Each approved vote = **+1 score**
* Users ranked based on total approved votes
* Top users displayed via `/top`

---

### 💰 Payment System (Optional / Future Ready)

* Supports:

  * Phone-based payouts
  * Card-based payouts
* Default payout amount configurable (`PAYOUT_AMOUNT_UZS`)
* Currently uses **stub (simulation)** system
* Can be integrated with:

  * Payment providers (Payme, Click, etc.)
* Stores:

  * payout status
  * transaction ID
  * errors

---

## ⚙️ Installation

### 1. Clone Project

```bash
git clone <your-repo-url>
cd open-budget-bot
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

Activate:

```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Configuration

Create `.env` file:

```ini
BOT_TOKEN=your_bot_token_here
ADMIN_IDS=123456789

DB_PATH=openbudget_leaderboard.db

PORTAL_URL=https://openbudget.uz/
BOARDS_URL=https://openbudget.uz/boards

REGION_NAME=Urgut (Gus)
VOTE_URL=https://openbudget.uz/boards/initiatives/initiative/52/98a9fe5d-2824-478c-92f4-f09a309fc10e

SEASON_ID=2025-II

PAYOUT_AMOUNT_UZS=20000

PAYMENT_PROVIDER=stub
PAYMENT_API_KEY=
PAYMENT_MERCHANT_ID=
```

---

## ▶️ Run the Bot

```bash
python run.py
```

---

## 🗄️ Database Structure

### users

* tg_id
* full_name
* username
* phone
* region
* score

### votes

* id
* tg_id
* season_id
* phone
* proof_file_id
* status (pending / approved / rejected)
* pay_type (phone / card)
* pay_value
* payout_status
* payout_amount
* payout_txn_id

---

## 📦 Project Structure

```
open-budget-bot/
│
├── app/
│   ├── handlers/
│   │   ├── user.py
│   │   ├── admin.py
│   │   ├── common.py
│   │
│   ├── db.py
│   ├── config.py
│   ├── keyboards.py
│   ├── payments.py
│   ├── bot.py
│
├── run.py
├── .env
├── requirements.txt
```

---

## 🔐 Security Notes

* Never upload `.env` to GitHub
* Add `.env` and `.db` to `.gitignore`
* Do not store full card details (use tokenization in real systems)
* Rotate BOT_TOKEN if exposed

---

## 🌐 Deployment

### Option 1: Local (Windows Service)

Use **NSSM** to run bot 24/7

### Option 2: VPS (Recommended)

Use `systemd` service on Linux

---

## ⚠️ Disclaimer

* This bot does **NOT automatically verify real votes**
* Admin approval is required
* Payment system is **not active by default**
* Ensure compliance with platform rules before using payouts

---

## 💡 Future Improvements

* OCR verification for screenshots
* Duplicate image detection (hashing)
* Real payment API integration
* Web dashboard for admins
* Multi-region support

---

## 👨‍💻 Author

Developed as a freelance-ready Telegram automation project.

---

## ⭐ Summary

This bot is a **complete voting automation system** with:

* User verification
* Admin control
* Anti-fraud measures
* Leaderboard tracking
* Payment-ready architecture

Perfect for:

* Campaigns
* Voting systems
* Promotional activities

---

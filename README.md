# Telegram Payment Bot 🤖

This is a Telegram bot for **Byb Importation Class**.

## Features
- ✅ Flutterwave payment verification (auto-approve with instant invite link)  
- ✅ Manual bank transfer method (requires admin approval with receipt upload)  
- ✅ One-time invite links that expire after being used  
- ✅ Secure admin-only approval system  

## Bank Details
- Bank: Opay  
- Account Number: 9039475752  
- Account Name: Abdulsalam Sulaiman Attah  

## Deployment
### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO.git
cd YOUR_REPO
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run locally
```bash
python telegram_bot.py
```

### 4. Deploy on Heroku/Render
```bash
git add .
git commit -m "Initial commit"
git push heroku main
```

### Env Vars
- `BOT_TOKEN` = your Telegram bot token  
- `FLW_SECRET_KEY` = your Flutterwave secret key  

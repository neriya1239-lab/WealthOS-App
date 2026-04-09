import os, requests, sqlite3, gspread
from datetime import datetime
from flask import Flask, render_template_string, request
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# הגדרות המערכת שלך
TOKEN = "7850233446:AAH6v8n7A_w6b8YvY7uXz6y8u4z5X1Y2Z3"
CHAT_ID = "6144812345"
SHEET_NAME = "WealthOS Leads"

def sync_to_sheets(data):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name("creds.json", scope)
        client = gspread.authorize(creds)
        sheet = client.open(SHEET_NAME).sheet1
        sheet.append_row(data)
    except Exception as e: print(f"Sheets Error: {e}")

@app.route('/')
def index():
    return "<h1>WealthOS Online</h1><p>המערכת מחוברת לטלגרם ולגוגל שיטס.</p>"

@app.route('/vip', methods=['GET', 'POST'])
def vip():
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        income = request.form.get('income', '0')
        dt = datetime.now().strftime("%d/%m/%Y %H:%M")
        
        # שליחה לטלגרם
        msg = f"🏆 **WealthOS VIP**\n👤 שם: {name}\n📱 טלפון: {phone}\n💰 הכנסה: {income}"
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg})
        
        # סנכרון לגוגל שיטס
        sync_to_sheets([dt, name, phone, income])
        
        return "<h1>הפרטים נקלטו!</h1>"
    return "<h1>VIP Page</h1>"

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

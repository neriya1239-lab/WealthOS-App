import os, json, requests
from datetime import datetime
from flask import Flask, render_template_string, request

app = Flask(__name__)

# פרטי הבוט וה-ID שלך
TOKEN = "8561398333:AAEeTZMU9mJ3Dtinu6FKj1zpCwoELoxqzPc"
CHAT_ID = "7726128954"

@app.route('/')
def index():
    return "<h1>WealthOS Active</h1><a href='/vip'>כניסה ל-VIP</a>"

@app.route('/vip', methods=['GET', 'POST'])
def vip():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        # שליחה לבוט
        msg = f"🚀 ליד חדש!\nשם: {name}\nאימייל: {email}"
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg})
        return "<h1>נשלח בהצלחה! בדוק את הטלגרם ✅</h1>"
    return '<form method="POST"><input name="name" placeholder="שם"><input name="email" placeholder="אימייל"><button type="submit">שלח</button></form>'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

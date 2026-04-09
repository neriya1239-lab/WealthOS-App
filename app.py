import os, json, requests
from datetime import datetime
from flask import Flask, render_template_string, request

app = Flask(__name__)

# הגדרות הבוט שלך
TOKEN = "8561398333:AAEeTZMU9mJ3Dtinu6FKj1zpCwoELoxqzPc"
CHAT_ID = "7726128954"

@app.route('/')
def index():
    return """
    <div style="text-align:center; padding:50px; font-family:sans-serif;">
        <h1>WealthOS Active</h1>
        <p>המערכת האוטונומית לניהול הון</p>
        <a href='/vip' style="padding:15px; background:gold; color:black; text-decoration:none; font-weight:bold; border-radius:10px;">כניסה ל-VIP (49 ש"ח בלבד)</a>
    </div>
    """

@app.route('/vip', methods=['GET', 'POST'])
def vip():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        # הודעה לבוט בטלגרם כולל ציון שהם הסכימו למחיר
        msg = f"💰 ליד VIP חם (מוכן לשלם 49 ש"ח)!\n👤 שם: {name}\n📧 אימייל: {email}\n📱 טלפון: {phone}"
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg})
        
        return f"<div style='text-align:center; padding:50px; font-family:sans-serif;'><h1>תודה {name}! ✅</h1><p>בקשתך התקבלה. נציג יחזור אליך תוך 24 שעות להסדרת התשלום והפעלת המנוע.</p></div>"
    
    return """
    <div style="text-align:center; padding:50px; font-family:sans-serif; direction:rtl;">
        <h1>הצטרפות ל-VIP</h1>
        <p style="font-size:1.2em;">עלות המנוי: <b>49 ש"ח לחודש</b></p>
        <p>השאר פרטים ונציג יחזור אליך לסיום הרכישה:</p>
        <form method="POST">
            <input name="name" placeholder="שם מלא" required style="margin:5px; padding:10px;"><br>
            <input name="email" type="email" placeholder="אימייל" required style="margin:5px; padding:10px;"><br>
            <input name="phone" placeholder="מספר טלפון" required style="margin:5px; padding:10px;"><br>
            <button type="submit" style="padding:10px 20px; background:gold; border:none; border-radius:5px; cursor:pointer;">אני רוצה להצטרף ב-49 ש"ח</button>
        </form>
    </div>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

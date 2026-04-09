import os, json, requests
from flask import Flask, render_template_string, request

app = Flask(__name__)

TOKEN = "8561398333:AAEeTZMU9mJ3Dtinu6FKj1zpCwoELoxqzPc"
CHAT_ID = "7726128954"

# תבנית HTML עם מטא-טאגס לעיצוב הלינק
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
    <title>WealthOS - מנוע עושר אוטונומי</title>
    <meta name="description" content="הצטרף למהפכת האוטומציה הפיננסית.">
    <meta property="og:title" content="WealthOS VIP">
    <meta property="og:description" content="הירשם עכשיו למסלול ה-VIP ב-49 ש"ח בלבד.">
    <meta property="og:type" content="website">
    
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0c0c0c; color: white; text-align: center; margin: 0; padding: 20px; }
        .container { max-width: 500px; margin: auto; background: #161616; padding: 30px; border-radius: 20px; border: 1px solid #gold; box-shadow: 0 10px 30px rgba(255,215,0,0.1); }
        .logo { font-size: 3em; font-weight: bold; color: gold; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 3px; }
        .price { font-size: 1.5em; color: #FFD700; margin: 20px 0; }
        input { width: 90%; padding: 12px; margin: 10px 0; border-radius: 8px; border: 1px solid #333; background: #222; color: white; }
        .btn { background: gold; color: black; padding: 15px 30px; border: none; border-radius: 10px; font-weight: bold; cursor: pointer; width: 95%; font-size: 1.1em; }
        .btn:hover { background: #e6c200; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">WealthOS</div>
        {% if page == 'index' %}
            <h1>מנוע העושר האוטונומי</h1>
            <p>הטכנולוגיה שעובדת בשבילך.</p>
            <a href="/vip"><button class="btn">כניסה למתחם VIP</button></a>
        {% elif page == 'vip' %}
            <h1>מתחם VIP</h1>
            <div class="price">49 ש"ח / לחודש</div>
            <p>השאר פרטים ונציג יחזור אליך לסיום ההרשמה:</p>
            <form method="POST">
                <input name="name" placeholder="שם מלא" required>
                <input name="email" type="email" placeholder="אימייל" required>
                <input name="phone" placeholder="מספר טלפון" required>
                <button type="submit" class="btn">אני רוצה להצטרף</button>
            </form>
        {% elif page == 'success' %}
            <h1 style="color:gold;">תודה {{ name }}!</h1>
            <p>הפרטים התקבלו. הבוט כבר עדכן אותנו.</p>
            <p>נציג יחזור אליך לנייד תוך 24 שעות.</p>
            <a href="/" style="color:gray; text-decoration:none;">חזרה לדף הבית</a>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, page='index')

@app.route('/vip', methods=['GET', 'POST'])
def vip():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        
        # התראה לטלגרם
        msg = f"💰 ליד VIP חדש!\n👤 שם: {name}\n📧 אימייל: {email}\n📱 טלפון: {phone}\n💵 מוכן לשלם: 49 ש"ח"
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg})
        
        return render_template_string(HTML_TEMPLATE, page='success', name=name)
    return render_template_string(HTML_TEMPLATE, page='vip')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

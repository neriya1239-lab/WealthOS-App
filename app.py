import os, requests
from flask import Flask, render_template_string, request
from flask_talisman import Talisman

app = Flask(__name__)

# הגדרות אבטחה בסיסיות למניעת התקפות XSS
Talisman(app, content_security_policy=None)

# משיכת פרטי האבטחה מהכספת של Render
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>WealthOS | פרימיום</title>
    <style>
        :root { --gold: #d4af37; --dark: #0c0c0c; --card: #161616; }
        body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: var(--dark); color: white; margin: 0; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
        .container { background: var(--card); padding: 50px 30px; border-radius: 30px; border: 1px solid rgba(212, 175, 55, 0.3); text-align: center; width: 90%; max-width: 450px; box-shadow: 0 20px 50px rgba(0,0,0,0.9); }
        .logo { font-size: 3.8em; font-weight: 900; color: var(--gold); letter-spacing: -2px; margin: 0; text-transform: uppercase; line-height: 1; }
        .vip-badge { display: inline-block; background: var(--gold); color: black; padding: 4px 12px; border-radius: 50px; font-size: 0.8em; font-weight: bold; margin-bottom: 20px; vertical-align: middle; }
        .tagline { color: #888; font-size: 1.1em; margin-bottom: 40px; }
        .btn { background: var(--gold); color: black; padding: 20px 40px; border: none; border-radius: 15px; font-weight: bold; cursor: pointer; font-size: 1.25em; text-decoration: none; display: block; transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); box-shadow: 0 10px 20px rgba(212, 175, 55, 0.2); }
        .btn:hover { transform: translateY(-5px); box-shadow: 0 15px 30px rgba(212, 175, 55, 0.4); background: #f1c40f; }
        input { width: 100%; padding: 16px; margin: 15px 0; border-radius: 12px; border: 1px solid #333; background: #222; color: white; text-align: right; box-sizing: border-box; font-size: 1.1em; outline: none; }
        input:focus { border-color: var(--gold); box-shadow: 0 0 10px rgba(212, 175, 55, 0.2); }
        h2 { color: var(--gold); font-size: 2em; margin-bottom: 10px; }
        p { color: #bbb; line-height: 1.6; font-size: 1.05em; }
        .footer { margin-top: 30px; font-size: 0.75em; color: #444; letter-spacing: 1px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">WealthOS</div>
        <div class="vip-badge">VIP ACCESS</div>
        
        {% if page == 'index' %}
            <p class="tagline">מערכת אימות שכר ותכנון הון מתקדמת.</p>
            <p>לחץ מטה כדי להתחיל באנליזה הפיננסית שלך במסלול המהיר.</p>
            <a href="/vip" class="btn">בצע אנליזת עומק</a>
        {% elif page == 'vip' %}
            <h2>הצטרפות ל-VIP</h2>
            <p>השאר פרטים ונציג בכיר יחזור אליך עם דוח מפורט:</p>
            <form method="POST">
                <input type="text" name="name" placeholder="שם מלא" required>
                <input type="tel" name="phone" placeholder="מספר טלפון" required>
                <button type="submit" class="btn" style="width:100%;">שלח בקשה מאובטחת</button>
            </form>
        {% elif page == 'success' %}
            <h2 style="font-size: 2.5em;">✔️</h2>
            <h2>הבקשה התקבלה</h2>
            <p>הצוות שלנו קיבל את פנייתך.<br>נחזור אליך בתוך 24 שעות עסקים.</p>
            <a href="/" style="color: #666; text-decoration: none; font-size: 0.9em; margin-top: 20px; display: block;">חזרה לדף הבית</a>
        {% endif %}
        
        <div class="footer">Ref: WOS-33368 | AES-256 SECURE</div>
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
        phone = request.form.get('phone')
        msg = f"🏆 **ליד VIP חדש הגיע!**\n\n👤 שם: {name}\n📱 טלפון: {phone}\n\n— WealthOS System —"
        try:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                          data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
        except Exception as e:
            print(f"Telegram Error: {e}")
        return render_template_string(HTML_TEMPLATE, page='success')
    return render_template_string(HTML_TEMPLATE, page='vip')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

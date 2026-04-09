import os, requests, re, sqlite3
from datetime import datetime
from flask import Flask, render_template_string, request
from flask_talisman import Talisman

app = Flask(__name__)
Talisman(app, content_security_policy=None)

TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect('leads.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads
                 (name TEXT, phone TEXT, income TEXT, date TEXT)''')
    conn.commit()
    conn.close()

def save_lead(name, phone, income):
    try:
        conn = sqlite3.connect('leads.db')
        c = conn.cursor()
        c.execute("INSERT INTO leads VALUES (?, ?, ?, ?)",
                  (name, phone, income, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

# ---------- VALIDATION ----------
def valid_name(name):
    return 1 < len(name) < 50

def valid_phone(phone):
    return re.match(r"^0\d{8,9}$", phone)

# ---------- HTML (WealthOS Premium Design) ----------
HTML = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WealthOS VIP</title>
    <style>
        :root { --gold: #d4af37; --dark: #0c0c0c; }
        body { background: var(--dark); color: white; font-family: system-ui, sans-serif; text-align: center; margin: 0; padding: 20px; display: flex; align-items: center; justify-content: center; min-height: 100vh; }
        .container { background: #161616; padding: 40px; border-radius: 25px; border: 1px solid var(--gold); width: 100%; max-width: 400px; box-shadow: 0 10px 30px rgba(0,0,0,0.8); }
        .logo { font-size: 3em; font-weight: bold; color: var(--gold); margin-bottom: 10px; }
        input, button { width: 100%; padding: 15px; margin: 10px 0; border-radius: 12px; border: none; font-size: 1.1em; box-sizing: border-box; }
        input { background: #222; color: white; border: 1px solid #333; text-align: right; }
        button { background: var(--gold); color: black; font-weight: bold; cursor: pointer; transition: 0.3s; }
        button:hover { background: #f1c40f; transform: scale(1.02); }
        p { color: #888; line-height: 1.6; }
    </style>
</head>
<body>
<div class="container">
    <div class="logo">WealthOS</div>
    
    {% if page == 'index' %}
        <p>מערכת האנליזה הפיננסית המתקדמת בעולם.</p>
        <a href="/vip" style="text-decoration:none;"><button>בצע אנליזת VIP</button></a>

    {% elif page == 'vip' %}
        <h2>השארת פרטים</h2>
        <form method="POST">
            <input name="name" placeholder="שם מלא" required>
            <input name="phone" placeholder="טלפון (למשל 0501234567)" required>
            <input name="income" type="number" placeholder="הכנסה חודשית ממוצעת" required>
            <input name="website" style="display:none"> <button type="submit">שלח בקשת הצטרפות</button>
        </form>

    {% elif page == 'success' %}
        <h2 style="color:var(--gold);">✔️ הבקשה נקלטה!</h2>
        <p>האנליסטים שלנו בוחנים את הנתונים שלך.<br>נחזור אליך בהקדם.</p>
        <a href="/" style="color:var(--gold); text-decoration:none; font-size:0.9em;">חזרה לדף הבית</a>
    {% endif %}
</div>
</body>
</html>
"""

# ---------- ROUTES ----------
@app.route('/')
def index():
    return render_template_string(HTML, page='index')

@app.route('/vip', methods=['GET','POST'])
def vip():
    if request.method == 'POST':
        if request.form.get('website'):
            return "Blocked", 403

        name = request.form.get('name','').strip()
        phone = request.form.get('phone','').strip()
        income = request.form.get('income','').strip()

        if not valid_name(name) or not valid_phone(phone):
            return "שגיאה בנתונים: וודא שהשם תקין והטלפון בפורמט ישראלי", 400

        save_lead(name, phone, income)

        status = "🔥 לקוח חם" if (income.isdigit() and int(income) > 15000) else "❄️ לקוח קר"

        msg = f"🏆 **ליד חדש מ-WealthOS**\n\n👤 שם: {name}\n📱 טלפון: {phone}\n💰 הכנסה: {income}\n📊 סטטוס: {status}\n⏰ {datetime.now().strftime('%H:%M:%S')}"

        try:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg})
        except Exception as e:
            print(f"Telegram Error: {e}")

        return render_template_string(HTML, page='success')

    return render_template_string(HTML, page='vip')

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

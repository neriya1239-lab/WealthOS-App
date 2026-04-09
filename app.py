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
                 (name TEXT, phone TEXT, income TEXT, date TEXT, status TEXT)''')
    conn.commit()
    conn.close()

def save_lead(name, phone, income, status):
    try:
        conn = sqlite3.connect('leads.db')
        c = conn.cursor()
        c.execute("INSERT INTO leads VALUES (?, ?, ?, ?, ?)",
                  (name, phone, income, datetime.now().strftime("%d/%m/%Y %H:%M"), status))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

# ---------- VALIDATION ----------
def valid_phone(phone):
    return re.match(r"^0\d{8,9}$", phone)

# ---------- HTML TEMPLATES ----------
BASE_STYLE = """
<style>
    :root { --gold: #d4af37; --dark: #0c0c0c; --card: #161616; }
    body { background: var(--dark); color: white; font-family: system-ui, sans-serif; margin: 0; padding: 20px; direction: rtl; }
    .container { background: var(--card); padding: 30px; border-radius: 20px; border: 1px solid var(--gold); max-width: 800px; margin: auto; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
    .logo { font-size: 2.5em; font-weight: bold; color: var(--gold); text-align: center; margin-bottom: 20px; text-transform: uppercase; }
    input, button { width: 100%; padding: 15px; margin: 10px 0; border-radius: 10px; border: none; font-size: 1em; box-sizing: border-box; }
    input { background: #222; color: white; border: 1px solid #333; text-align: right; }
    button { background: var(--gold); color: black; font-weight: bold; cursor: pointer; transition: 0.3s; }
    button:hover { background: #f1c40f; transform: scale(1.02); }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { padding: 12px; border-bottom: 1px solid #333; text-align: center; }
    th { color: var(--gold); font-weight: bold; }
    .status-hot { color: #ff4d4d; font-weight: bold; }
    .status-cold { color: #4da6ff; }
</style>
"""

HTML = f"""
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WealthOS VIP</title>
    {BASE_STYLE}
</head>
<body>
<div class="container">
    <div class="logo">WealthOS</div>
    
    {% if page == 'index' %}
        <p style="text-align:center;">מערכת האנליזה הפיננסית המתקדמת.</p>
        <a href="/vip" style="text-decoration:none;"><button>בצע אנליזת VIP</button></a>

    {% elif page == 'vip' %}
        <h2 style="text-align:center;">השארת פרטים</h2>
        <form method="POST">
            <input name="name" placeholder="שם מלא" required>
            <input name="phone" placeholder="טלפון" required>
            <input name="income" type="number" placeholder="הכנסה חודשית" required>
            <input name="website" style="display:none">
            <button type="submit">שלח בקשת הצטרפות</button>
        </form>

    {% elif page == 'success' %}
        <h2 style="text-align:center; color:var(--gold);">✔️ הבקשה נקלטה</h2>
        <p style="text-align:center;">נציג WealthOS יחזור אליך בהקדם.</p>
        <a href="/" style="color:var(--gold); text-decoration:none; display:block; text-align:center;">חזרה</a>

    {% elif page == 'admin' %}
        <h2 style="text-align:center; color:var(--gold);">לוח ניהול לידים</h2>
        <table>
            <tr>
                <th>תאריך</th>
                <th>שם</th>
                <th>טלפון</th>
                <th>הכנסה</th>
                <th>סטטוס</th>
            </tr>
            {% for lead in leads %}
            <tr>
                <td>{{ lead[3] }}</td>
                <td>{{ lead[0] }}</td>
                <td>{{ lead[1] }}</td>
                <td>{{ lead[2] }} ₪</td>
                <td class="{{ 'status-hot' if 'חם' in lead[4] else 'status-cold' }}">{{ lead[4] }}</td>
            </tr>
            {% endfor %}
        </table>
        <a href="/" style="color:var(--gold); text-decoration:none; display:block; text-align:center; margin-top:20px;">חזרה לאתר</a>
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
        if request.form.get('website'): return "Blocked", 403
        name, phone, income = request.form.get('name','').strip(), request.form.get('phone','').strip(), request.form.get('income','').strip()
        
        if not valid_phone(phone):
            return "שגיאה: טלפון לא תקין", 400

        status = "🔥 חם" if (income.isdigit() and int(income) > 15000) else "❄️ קר"
        save_lead(name, phone, income, status)

        msg = f"🏆 **ליד חדש מ-WealthOS**\n\n👤 שם: {name}\n📱 טלפון: {phone}\n💰 הכנסה: {income}\n📊 סטטוס: {status}"
        try:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg})
        except: pass
        return render_template_string(HTML, page='success')
    return render_template_string(HTML, page='vip')

@app.route('/admin')
def admin():
    try:
        conn = sqlite3.connect('leads.db')
        c = conn.cursor()
        c.execute("SELECT * FROM leads ORDER BY date DESC")
        leads = c.fetchall()
        conn.close()
        return render_template_string(HTML, page='admin', leads=leads)
    except:
        return "אין עדיין נתונים במסד הנתונים."

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

import os, requests
from flask import Flask, render_template_string, request

app = Flask(__name__)

# משיכת פרטי האבטחה מהכספת של Render
TOKEN = os.environ.get("TELEGRAM_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WealthOS VIP</title>
    <style>
        body { font-family: system-ui, -apple-system, sans-serif; background: #0c0c0c; color: white; text-align: center; padding: 50px; margin: 0; }
        .container { background: #161616; padding: 40px; border-radius: 25px; border: 1px solid #d4af37; display: inline-block; width: 90%; max-width: 450px; box-shadow: 0 10px 30px rgba(0,0,0,0.8); }
        .logo { color: #d4af37; font-size: 3.5em; margin: 0; font-weight: bold; letter-spacing: 3px; text-transform: uppercase; }
        .tagline { color: #888; margin-bottom: 30px; font-size: 1.1em; border-top: 1px solid #333; padding-top: 10px; display: inline-block; }
        .btn { background: #d4af37; color: black; padding: 18px 30px; border: none; border-radius: 12px; font-weight: bold; cursor: pointer; font-size: 1.2em; text-decoration: none; display: block; margin: 20px auto; transition: 0.3s; box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3); }
        .btn:hover { background: #f1c40f; transform: scale(1.05); }
        input { width: 100%; padding: 14px; margin: 10px 0; border-radius: 8px; border: 1px solid #333; background: #222; color: white; text-align: right; box-sizing: border-box; font-size: 1em; }
        p { color: #ccc; line-height: 1.6; }
        .footer { margin-top: 20px; font-size: 0.8em; color: #444; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">WealthOS</div>
        <div class="tagline">PREMIUM FINANCIAL SYSTEMS</div>
        
        {% if page == 'index' %}
            <p>מערכת אימות שכר ותכנון הון מתקדמת.<br>הצטרף למסלול ה-VIP לקבלת אנליזה מותאמת אישית.</p>
            <a href="/vip" class="btn">בצע אנליזת עומק (VIP)</a>
        {% elif page == 'vip' %}
            <p>השאר פרטים ואחד האנליסטים שלנו יחזור אליך:</p>
            <form method="POST">
                <input type="text" name="name" placeholder="שם מלא" required>
                <input type="tel" name="phone" placeholder="מספר טלפון" required>
                <button type="submit" class="btn">שלח בקשת הצטרפות</button>
            </form>
        {% elif page == 'success' %}
            <h2 style="color:#d4af37;">הבקשה התקבלה!</h2>
            <p>מערכת ה-WealthOS עיבדה את פנייתך.<br>הבוט שלח עדכון לצוות שלנו ונחזור אליך בהקדם.</p>
            <a href="/" style="color: #666; text-decoration: none; font-size: 0.9em;">חזרה לדף הבית</a>
        {% endif %}
        <div class="footer">Ref: WOS-33368 | Secure Encryption Active</div>
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
        msg = f"💰 ליד VIP חדש מ-WealthOS\n👤 שם: {name}\n📱 טלפון: {phone}"
        try:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg})
        except Exception as e:
            print(f"Error: {e}")
        return render_template_string(HTML_TEMPLATE, page='success')
    return render_template_string(HTML_TEMPLATE, page='vip')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

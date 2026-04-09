import os, requests
from flask import Flask, render_template_string, request

app = Flask(__name__)

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
        body { font-family: sans-serif; background: #0c0c0c; color: white; text-align: center; padding: 50px; }
        .container { background: #161616; padding: 30px; border-radius: 20px; border: 1px solid gold; display: inline-block; width: 90%; max-width: 500px; }
        .btn { background: gold; color: black; padding: 15px 30px; border: none; border-radius: 10px; font-weight: bold; cursor: pointer; font-size: 1.1em; text-decoration: none; display: block; margin: 20px auto; }
        input { width: 90%; padding: 10px; margin: 10px 0; border-radius: 5px; border: 1px solid #333; background: #222; color: white; text-align: right; }
        h1 { color: gold; margin-bottom: 5px; }
        p { color: #ccc; margin-bottom: 25px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>WealthOS</h1>
        <p>מערכת אימות שכר ותכנון הון מתקדמת</p>
        {% if page == 'index' %}
            <a href="/vip" class="btn">בצע אנליזת עומק (VIP)</a>
        {% elif page == 'vip' %}
            <p>השאר פרטים למסלול ה-VIP:</p>
            <form method="POST">
                <input name="name" placeholder="שם מלא" required>
                <input name="phone" placeholder="מספר טלפון" required>
                <button type="submit" class="btn">שלח בקשה</button>
            </form>
        {% elif page == 'success' %}
            <h2 style="color:gold;">הבקשה נשלחה!</h2>
            <p>הנתונים הועברו לאנליזה, נחזור אליך בהקדם.</p>
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
        phone = request.form.get('phone')
        msg = f"💰 WealthOS VIP Lead\n👤 Name: {name}\n📱 Phone: {phone}"
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={"chat_id": CHAT_ID, "text": msg})
        return render_template_string(HTML_TEMPLATE, page='success')
    return render_template_string(HTML_TEMPLATE, page='vip')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

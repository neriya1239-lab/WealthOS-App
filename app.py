import os
from flask import Flask, render_template_string, make_response
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from bidi.algorithm import get_display

app = Flask(__name__)

# הגדרת פונט עברית מהתיקייה שיצרת
font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'NotoSansHebrew-Bold.ttf')
pdfmetrics.registerFont(TTFont('HebrewBold', font_path))

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WealthOS | ניהול הון</title>
    <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><rect width=%22100%22 height=%22100%22 rx=%2220%22 fill=%22%231a1a1a%22/><text y=%22.75em%22 x=%225%22 font-size=%2280%22 fill=%22%23FFD700%22 font-family=%22Arial%22 font-weight=%22bold%22>M</text></svg>">
    <style>
        body { font-family: sans-serif; text-align: center; background: #f4f4f4; padding: 50px; }
        .card { background: white; padding: 30px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); max-width: 400px; margin: auto; }
        button { background: #FFD700; border: none; padding: 10px 20px; font-weight: bold; border-radius: 5px; cursor: pointer; margin: 10px; }
        .vip-btn { background: #1a1a1a; color: gold; }
    </style>
</head>
<body>
    <div class="card">
        <h1>WealthOS 🚀</h1>
        <p>מערכת ניהול הון אישית</p>
        <form action="/download" method="get">
            <button type="submit">הורד דו"ח PDF בעברית</button>
        </form>
        <button class="vip-btn" onclick="trackVIP()">הצטרף ל-VIP 👑</button>
    </div>

    <script>
    function trackVIP() {
        // מעקב לחיצות (לוג פשוט למטרת מעקב)
        console.log("VIP Clicked");
        alert("ברוך הבא ל-VIP! הלחיצה שלך נרשמה במערכת הסטטיסטיקה שלנו.");
    }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download')
def download_pdf():
    response = make_response()
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=report.pdf'
    
    p = canvas.Canvas(response.stream)
    p.setFont('HebrewBold', 16)
    
    text = "WealthOS - דו\"ח ניהול הון"
    reshaped_text = get_display(text) # תיקון עברית שתהיה מימין לשמאל
    
    p.drawRightString(500, 800, reshaped_text)
    p.showPage()
    p.save()
    return response

if __name__ == '__main__':
    app.run(debug=True)

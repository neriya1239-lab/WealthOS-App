import os
from flask import Flask, render_template_string, make_response
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from bidi.algorithm import get_display

app = Flask(__name__)

# נתיב לפונט
font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'NotoSansHebrew-Bold.ttf')
if os.path.exists(font_path):
    pdfmetrics.registerFont(TTFont('HebrewBold', font_path))

# לוגו M עם חץ צמיחה (SVG)
LOGO_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><rect width='100' height='100' rx='20' fill='#1a1a1a'/><path d='M20 70 L40 40 L60 50 L85 20' stroke='#FFD700' stroke-width='4' fill='none'/><text y='.75em' x='5' font-size='70' fill='#FFD700' font-family='Arial' font-weight='bold' opacity='0.8'>M</text><path d='M75 20 L85 20 L85 30' stroke='#FFD700' stroke-width='4' fill='none'/></svg>"""

HTML_TEMPLATE = f"""
<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WealthOS | ניהול הון</title>
    <link rel="icon" href="data:image/svg+xml,{LOGO_SVG.replace('"', '%22')}">
    
    <meta name="description" content="WealthOS - המערכת המובילה לניהול הון והפקת דוחות">
    
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, sans-serif; text-align: center; background: #0f0f0f; color: white; padding: 50px; }}
        .card {{ background: #1a1a1a; padding: 40px; border-radius: 20px; border: 1px solid #333; max-width: 500px; margin: auto; }}
        .logo-container {{ width: 80px; margin: 0 auto 20px; }}
        h1 {{ color: #FFD700; margin: 0; }}
        button {{ background: #FFD700; border: none; padding: 15px 30px; font-weight: bold; border-radius: 10px; cursor: pointer; width: 100%; margin-top: 20px; }}
        .vip-btn {{ background: transparent; border: 2px solid #FFD700; color: #FFD700; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="logo-container">{LOGO_SVG}</div>
        <h1>WealthOS 🚀</h1>
        <p>ניהול הון וצמיחה פיננסית</p>
        <form action="/download" method="get">
            <button type="submit">הורד דו"ח PDF</button>
        </form>
        <a href="/vip"><button class="vip-btn">מתחם VIP 👑</button></a>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/vip')
def vip():
    return "<h1>מתחם VIP - בקרוב!</h1><a href='/'>חזרה</a>"

@app.route('/download')
def download_pdf():
    response = make_response()
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=wealth_report.pdf'
    p = canvas.Canvas(response.stream)
    if os.path.exists(font_path):
        p.setFont('HebrewBold', 18)
    text = get_display("WealthOS - דו\"ח צמיחה")
    p.drawRightString(550, 800, text)
    p.showPage()
    p.save()
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

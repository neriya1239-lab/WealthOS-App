import io, os, time, threading, random, secrets
import urllib.request
from flask import Flask, render_template, request, send_file
from bidi.algorithm import get_display

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
# פורט דינמי עבור Render
PORT = int(os.environ.get("PORT", 8080))

# ==========================================
# 1. מנוע חישוב שכר (Payroll Engine)
# ==========================================
class PayrollAuditor:
    @staticmethod
    def run_audit(data):
        try:
            bruto = max(0, min(float(data.get('b', 0)), 1000000))
            points = max(0, min(float(data.get('p', 2.25)), 20))
            
            # תוספות בכסף (חייבות במס, ללא פנסיה)
            travel = max(0, float(data.get('travel', 0)))
            cellular = max(0, float(data.get('cellular', 0)))
            other_bonus = max(0, float(data.get('other_bonus', 0)))
            cash_additions = travel + cellular + other_bonus
            
            # זקיפות שווי (למס בלבד)
            car_val = max(0, float(data.get('car', 0)))
            benefits = max(0, float(data.get('benefits', 0)))
            imputed_income = car_val + benefits
            
            # אחוזי הפרשה
            pen_emp_pct = float(data.get('pen_emp', 6.0))
            pen_boss_pct = float(data.get('pen_boss', 6.5))
            pitzuim_pct = float(data.get('pitzuim', 6.0))
            hish_emp_pct = float(data.get('hish_emp', 2.5))
            hish_boss_pct = float(data.get('hish_boss', 7.5))

            # שווי מס קרן השתלמות מעל התקרה
            hish_imputed = max(0, (bruto - 15712)) * (hish_boss_pct / 100) if hish_boss_pct > 0 else 0
            
            taxable_gross = bruto + cash_additions + imputed_income + hish_imputed
            btl_gross = bruto + cash_additions + imputed_income

            # מדרגות מס 2024/2025
            brackets = [(7010, 0.10), (10060, 0.14), (16150, 0.20), (22440, 0.31), (46690, 0.35), (60130, 0.47)]
            tax = 0
            prev = 0
            for limit, rate in brackets:
                if taxable_gross > limit:
                    tax += (limit - prev) * rate
                    prev = limit
                else:
                    tax += (taxable_gross - prev) * rate
                    break
            if taxable_gross > 60130:
                tax += (taxable_gross - 60130) * 0.50
                
            tax -= (points * 242)
            pen_emp_val = bruto * (pen_emp_pct / 100)
            tax -= (min(pen_emp_val, 679) * 0.35)
            tax = max(0, tax)
            
            btl_gross_capped = min(btl_gross, 49030)
            if btl_gross_capped <= 7522:
                social = btl_gross_capped * 0.035
            else:
                social = (7522 * 0.035) + ((btl_gross_capped - 7522) * 0.12)
                
            hish_emp_val = bruto * (hish_emp_pct / 100)
            pen_boss_val = bruto * (pen_boss_pct / 100)
            pitzuim_val = bruto * (pitzuim_pct / 100)
            hish_boss_val = bruto * (hish_boss_pct / 100)
            
            neto = bruto + cash_additions - tax - social - pen_emp_val - hish_emp_val
            btl_boss = (min(btl_gross_capped, 7522) * 0.0355) + (max(0, btl_gross_capped - 7522) * 0.076)
            cost = bruto + cash_additions + imputed_income + pen_boss_val + pitzuim_val + hish_boss_val + btl_boss
            
            return {
                "bruto": bruto, "travel": travel, "cellular": cellular, "other_bonus": other_bonus, 
                "car_val": car_val, "benefits": benefits,
                "tax": tax, "social": social,
                "pen_emp": pen_emp_val, "hish_emp": hish_emp_val, "neto": neto,
                "pen_boss": pen_boss_val, "pitzuim": pitzuim_val, "hish_boss": hish_boss_val,
                "cost": cost, "total_savings": pen_emp_val + pen_boss_val + pitzuim_val + hish_emp_val + hish_boss_val
            }
        except Exception as e:
            print(f"Error in calculation: {e}")
            return None

# ==========================================
# 2. מנוע PDF חסין תקלות (Graceful Fail)
# ==========================================
class PDF_Elite:
    @staticmethod
    def ensure_fonts():
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        font_reg = "/tmp/Assistant-Regular.ttf"
        font_bold = "/tmp/Assistant-Bold.ttf"
        
        urls = {
            font_reg: "https://raw.githubusercontent.com/googlefonts/assistant/main/fonts/ttf/Assistant-Regular.ttf",
            font_bold: "https://raw.githubusercontent.com/googlefonts/assistant/main/fonts/ttf/Assistant-Bold.ttf"
        }
        
        for file_path, url in urls.items():
            if not os.path.exists(file_path):
                try:
                    print(f"Downloading font from {url}...")
                    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                    with urllib.request.urlopen(req) as response, open(file_path, 'wb') as out_file:
                        out_file.write(response.read())
                    print("Font downloaded successfully.")
                except Exception as e:
                    print(f"Critical error downloading font: {e}")

        try:
            pdfmetrics.registerFont(TTFont('Hebrew', font_reg))
            pdfmetrics.registerFont(TTFont('Hebrew-Bold', font_bold))
            return 'Hebrew', 'Hebrew-Bold'
        except Exception as e:
            print(f"Could not register fonts, falling back to standard: {e}")
            return 'Helvetica', 'Helvetica-Bold'

    @classmethod
    def generate(cls, data_dict, is_sample=False):
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        
        font_reg, font_bold = cls.ensure_fonts()
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        w, h = A4
        
        # עיצוב PDF יוקרתי
        C_BG = colors.HexColor("#06090F")
        C_GOLD = colors.HexColor("#D4AF37")
        C_TEXT = colors.HexColor("#1A1D24")
        C_GREEN = colors.HexColor("#10B981")

        p.setFillColor(C_BG)
        p.rect(0, h-120, w, 120, fill=1)
        p.setFillColor(C_GOLD)
        p.setFont(font_bold, 36)
        p.drawRightString(w - 40, h - 65, get_display("WealthOS"))
        
        p.setFillColor(colors.white)
        p.setFont(font_reg, 14)
        doc_title = "אנליזת תלוש שכר - דוח דגימה" if is_sample else "דוח ביקורת שכר מלא (VIP)"
        p.drawRightString(w - 40, h - 90, get_display(doc_title))
        
        p.setFont(font_reg, 10)
        p.setFillColor(colors.HexColor("#888888"))
        p.drawString(40, h - 90, f"Ref: WOS-{random.getrandbits(16)}")

        y = h - 160
        p.setFillColor(C_TEXT)
        p.setFont(font_bold, 20)
        p.drawRightString(w - 40, y, get_display("פירוט נתונים פיננסיים:"))
        p.setStrokeColor(C_GOLD)
        p.setLineWidth(2)
        p.line(w - 40, y - 10, 40, y - 10)

        y -= 40
        def draw_row(label, val, is_bold=False, color=C_TEXT, size=13):
            nonlocal y
            p.setFillColor(color)
            p.setFont(font_bold if is_bold else font_reg, size)
            p.drawRightString(w - 50, y, get_display(label))
            p.drawString(90, y, val)
            y -= 25

        draw_row("שכר בסיס (לפנסיה):", data_dict['bruto'], is_bold=True, size=15)
        
        if data_dict.get('travel') and data_dict['travel'] != "₪0":
            draw_row("קצבת נסיעות:", f"+ {data_dict['travel']}")
        
        y -= 20
        p.setFillColor(colors.HexColor("#F0FDF4"))
        p.roundRect(40, y - 20, w - 80, 45, 8, fill=1, stroke=0)
        y -= 5
        draw_row("שכר נטו סופי לחשבון:", data_dict['neto'], is_bold=True, color=C_GREEN, size=18)
        
        y -= 50
        p.setFillColor(colors.HexColor("#FFFBEB"))
        p.roundRect(40, y - 20, w - 80, 45, 8, fill=1, stroke=0)
        y -= 5
        draw_row("עלות מעסיק כוללת:", data_dict['cost'], is_bold=True, color=C_GOLD, size=16)

        p.showPage()
        p.save()
        buffer.seek(0)
        return buffer

def format_currency(num):
    return f"₪{int(num):,}"

# ==========================================
# 3. נתיבי שרת (Server Routes)
# ==========================================

@app.route('/')
def home():
    try:
        # פלאסק יחפש בתיקייה templates/index.html
        return render_template('index.html')
    except Exception as e:
        return f"Template Error: {str(e)}. Make sure index.html is in 'templates' folder.", 500

@app.route('/sample', methods=['GET'])
def sample_report():
    audit = PayrollAuditor.run_audit({'b': 35000, 'p': 2.25})
    formatted_data = {
        "bruto": format_currency(audit['bruto']),
        "neto": format_currency(audit['neto']),
        "cost": format_currency(audit['cost']),
        "proj": format_currency(audit['total_savings'] * 155.2)
    }
    pdf = PDF_Elite.generate(formatted_data, is_sample=True)
    return send_file(pdf, mimetype='application/pdf', as_attachment=True, download_name="WealthOS_Sample.pdf")

@app.route('/download', methods=['POST'])
def process_secure_download():
    try:
        audit = PayrollAuditor.run_audit(request.form)
        formatted_data = {
            "bruto": format_currency(audit['bruto']),
            "tax": format_currency(audit['tax']),
            "social": format_currency(audit['social']),
            "neto": format_currency(audit['neto']),
            "cost": format_currency(audit['cost']),
            "proj": format_currency(audit['total_savings'] * 155.2)
        }
        pdf = PDF_Elite.generate(formatted_data, is_sample=False)
        return send_file(pdf, as_attachment=True, download_name="WealthOS_VIP_Audit.pdf")
    except Exception as e:
        return f"System Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)

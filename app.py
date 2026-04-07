import io, os, time, threading, random, secrets
import urllib.request
from flask import Flask, render_template, request, send_file
from bidi.algorithm import get_display

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
PORT = int(os.environ.get("PORT", 8080))

# ==========================================
# 1. CORE LOGIC & FULL PAYROLL AUDIT ENGINE
# ==========================================
class PayrollAuditor:
    @staticmethod
    def run_audit(data):
        bruto = max(0, min(float(data.get('b', 0)), 1000000))
        points = max(0, min(float(data.get('p', 2.25)), 20))
        
        # תוספות בכסף
        travel = max(0, float(data.get('travel', 0)))
        cellular = max(0, float(data.get('cellular', 0)))
        other_bonus = max(0, float(data.get('other_bonus', 0)))
        cash_additions = travel + cellular + other_bonus
        
        # זקיפות שווי
        car_val = max(0, float(data.get('car', 0)))
        benefits = max(0, float(data.get('benefits', 0)))
        imputed_income = car_val + benefits
        
        pen_emp_pct = float(data.get('pen_emp', 6.0))
        pen_boss_pct = float(data.get('pen_boss', 6.5))
        pitzuim_pct = float(data.get('pitzuim', 6.0))
        hish_emp_pct = float(data.get('hish_emp', 2.5))
        hish_boss_pct = float(data.get('hish_boss', 7.5))

        hish_imputed = max(0, (bruto - 15712)) * (hish_boss_pct / 100) if hish_boss_pct > 0 else 0
        
        taxable_gross = bruto + cash_additions + imputed_income + hish_imputed
        btl_gross = bruto + cash_additions + imputed_income

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
        
        btl_gross = min(btl_gross, 49030)
        if btl_gross <= 7522:
            social = btl_gross * 0.035
        else:
            social = (7522 * 0.035) + ((btl_gross - 7522) * 0.12)
            
        hish_emp_val = bruto * (hish_emp_pct / 100)
        pen_boss_val = bruto * (pen_boss_pct / 100)
        pitzuim_val = bruto * (pitzuim_pct / 100)
        hish_boss_val = bruto * (hish_boss_pct / 100)
        
        neto = bruto + cash_additions - tax - social - pen_emp_val - hish_emp_val
        btl_boss = (min(btl_gross, 7522) * 0.0355) + (max(0, btl_gross - 7522) * 0.076)
        cost = bruto + cash_additions + imputed_income + pen_boss_val + pitzuim_val + hish_boss_val + btl_boss
        
        return {
            "bruto": bruto, "travel": travel, "cellular": cellular, "other_bonus": other_bonus, 
            "car_val": car_val, "benefits": benefits,
            "tax": tax, "social": social,
            "pen_emp": pen_emp_val, "hish_emp": hish_emp_val, "neto": neto,
            "pen_boss": pen_boss_val, "pitzuim": pitzuim_val, "hish_boss": hish_boss_val,
            "cost": cost, "total_savings": pen_emp_val + pen_boss_val + pitzuim_val + hish_emp_val + hish_boss_val
        }

# ==========================================
# 2. LUXURY HEBREW PDF GENERATOR (Auto-Font)
# ==========================================
class PDF_Elite:
    @staticmethod
    def get_hebrew_font():
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import os, urllib.request

        # השרת של Render יחפש את הפונט בתיקייה הזמנית שלו
        font_path = "/tmp/Assistant-Bold.ttf"
        
        # אם הפונט לא קיים בשרת, הוא מוריד אותו פעם אחת מגוגל
        if not os.path.exists(font_path):
            url = "https://raw.githubusercontent.com/googlefonts/assistant/main/fonts/ttf/Assistant-Bold.ttf"
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response, open(font_path, 'wb') as out_file:
                    out_file.write(response.read())
            except:
                pass

        # רושם את הפונט כדי שה-PDF יוכל להשתמש בו לעברית
        try:
            pdfmetrics.registerFont(TTFont('Hebrew', font_path))
            return 'Hebrew'
        except:
            return 'Helvetica'

    @classmethod
    def ensure_fonts(cls):
        """Ensure we have proper fonts for Hebrew text rendering"""
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import os, urllib.request
        
        font_path = "/tmp/Assistant-Bold.ttf"
        
        # Download font if it doesn't exist
        if not os.path.exists(font_path):
            url = "https://raw.githubusercontent.com/googlefonts/assistant/main/fonts/ttf/Assistant-Bold.ttf"
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req) as response, open(font_path, 'wb') as out_file:
                    out_file.write(response.read())
            except Exception as e:
                print(f"Failed to download font: {e}")
        
        # Register fonts
        try:
            pdfmetrics.registerFont(TTFont('HebrewBold', font_path))
            font_reg = 'Helvetica'
            font_bold = 'HebrewBold'
        except Exception as e:
            print(f"Failed to register font: {e}")
            font_reg = 'Helvetica'
            font_bold = 'Helvetica-Bold'
        
        return font_reg, font_bold

    @classmethod
    def generate(cls, data_dict, is_sample=False):
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        
        # משיכת הפונטים החדים שלנו
        font_reg, font_bold = cls.ensure_fonts()
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        w, h = A4
        
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
        p.setFont(font_bold, 20)  # שימוש בפונט מודגש לכותרת - הופך את זה לחד מאוד
        p.drawRightString(w - 40, y, get_display("פירוט נתונים פיננסיים (ברמת השקל):"))
        p.setStrokeColor(C_GOLD)
        p.setLineWidth(2)
        p.line(w - 40, y - 10, 40, y - 10)

        y -= 35
        def draw_row(label, val, is_bold=False, color=C_TEXT, size=13):
            nonlocal y
            p.setFillColor(color)
            p.setFont(font_bold if is_bold else font_reg, size) # שימוש חכם בפונטים
            p.drawRightString(w - 50, y, get_display(label))
            p.drawString(90, y, val)
            y -= 25

        # חלק א': ברוטו ותוספות
        draw_row("שכר בסיס (ממנו מופרשת פנסיה):", data_dict['bruto'], is_bold=True, size=15)
        
        has_extras = False
        if data_dict['travel'] != "₪0":
            draw_row("קצבת נסיעות (ללא פנסיה):", f"+ {data_dict['travel']}")
            has_extras = True
        if data_dict['cellular'] != "₪0":
            draw_row("החזקת טלפון / סלולר:", f"+ {data_dict['cellular']}")
            has_extras = True
        if data_dict['other_bonus'] != "₪0":
            draw_row("בונוסים / עמלות / שעות נוספות:", f"+ {data_dict['other_bonus']}")
            has_extras = True
        if data_dict['car_val'] != "₪0":
            draw_row("שווי שימוש רכב (זקיפה למס בלבד):", f"+ {data_dict['car_val']}")
            has_extras = True
        if data_dict['benefits'] != "₪0":
            draw_row("שווי ארוחות / סיבוס (זקיפה למס בלבד):", f"+ {data_dict['benefits']}")
            has_extras = True
            
        if has_extras:
            y += 10
            p.setStrokeColor(colors.HexColor("#EEEEEE"))
            p.setLineWidth(1)
            p.line(w - 50, y, 90, y)
            y -= 15

        # חלק ב': ניכויים
        y -= 10
        p.setFillColor(colors.HexColor("#666666"))
        p.setFont(font_bold, 11)
        p.drawRightString(w - 50, y, get_display("ניכויי חובה והפרשות עובד:"))
        y -= 20
        
        draw_row("מס הכנסה (מדורג לאחר נקודות זיכוי):", f"- {data_dict['tax']}")
        draw_row("ביטוח לאומי ומס בריאות:", f"- {data_dict['social']}")
        draw_row("הפרשות לפנסיה (חלק עובד):", f"- {data_dict['pen_emp']}")
        draw_row("הפרשות לקרן השתלמות (חלק עובד):", f"- {data_dict['hish_emp']}")
        
        y += 10
        p.setStrokeColor(colors.HexColor("#EEEEEE"))
        p.line(w - 50, y, 90, y)
        y -= 15

        # חלק ג': הנטו האמיתי לבנק
        p.setFillColor(colors.HexColor("#F0FDF4"))
        p.roundRect(40, y - 20, w - 80, 45, 8, fill=1, stroke=0)
        y -= 5
        draw_row("שכר נטו סופי לחשבון הבנק:", data_dict['neto'], is_bold=True, color=C_GREEN, size=18)
        y -= 15

        # חלק ד': הפרשות מעסיק
        p.setFillColor(colors.HexColor("#666666"))
        p.setFont(font_bold, 11)
        p.drawRightString(w - 50, y, get_display("הפרשות מעסיק לקופות מחוץ לשכר (כסף שלך):"))
        y -= 20
        
        draw_row("פנסיה (תגמולי מעסיק):", f"+ {data_dict['pen_boss']}")
        draw_row("פיצויים (מעסיק):", f"+ {data_dict['pitzuim']}")
        draw_row("קרן השתלמות (מעסיק):", f"+ {data_dict['hish_boss']}")
        
        y += 10
        p.setStrokeColor(colors.HexColor("#EEEEEE"))
        p.line(w - 50, y, 90, y)
        y -= 15

        # חלק ה': עלות מעסיק
        p.setFillColor(colors.HexColor("#FFFBEB"))
        p.roundRect(40, y - 20, w - 80, 45, 8, fill=1, stroke=0)
        y -= 5
        draw_row("עלות מעסיק כוללת (השווי האמיתי לחברה):", data_dict['cost'], is_bold=True, color=C_GOLD, size=16)

        # חלק ו': חיסכון ארוך טווח
        y -= 45
        p.setFillColor(C_BG)
        p.roundRect(40, y - 60, w - 80, 80, 12, fill=1, stroke=0)
        p.setFillColor(colors.white)
        p.setFont(font_bold, 14)
        p.drawRightString(w - 60, y - 20, get_display("תחזית צבירת הון דריבית (10 שנים, 5% תשואה):"))
        p.setFillColor(C_GOLD)
        p.setFont(font_bold, 22)
        p.drawString(80, y - 25, data_dict['proj'])
        
        p.setFillColor(colors.HexColor("#999999"))
        p.setFont(font_reg, 9)
        p.drawCentredString(w/2, 30, get_display("WealthOS 2026 - הדוח הינו סימולציה כלכלית ואינו מהווה תחליף לייעוץ פנסיוני ומיסוי מקצועי"))

        p.showPage()
        p.save()
        buffer.seek(0)
        return buffer

def format_currency(num):
    return f"₪{int(num):,}"

# ==========================================
# 4. SERVER ROUTES
# ==========================================
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/sample', methods=['GET'])
def sample_report():
    data = {'b': 35000, 'p': 2.25, 'car': 3500, 'travel': 500, 'cellular': 150, 'other_bonus': 2000, 'pen_emp': 6, 'pen_boss': 6.5, 'pitzuim': 6, 'hish_emp': 2.5, 'hish_boss': 7.5}
    audit = PayrollAuditor.run_audit(data)
    
    formatted_data = {
        "bruto": format_currency(audit['bruto']), "travel": format_currency(audit['travel']), 
        "cellular": format_currency(audit['cellular']), "other_bonus": format_currency(audit['other_bonus']),
        "car_val": format_currency(audit['car_val']), "benefits": format_currency(audit['benefits']),
        "tax": format_currency(audit['tax']), "social": format_currency(audit['social']),
        "pen_emp": format_currency(audit['pen_emp']), "hish_emp": format_currency(audit['hish_emp']),
        "neto": format_currency(audit['neto']),
        "pen_boss": format_currency(audit['pen_boss']), "pitzuim": format_currency(audit['pitzuim']), "hish_boss": format_currency(audit['hish_boss']),
        "cost": format_currency(audit['cost']), "proj": format_currency(audit['total_savings'] * 155.2)
    }
    pdf = PDF_Elite.generate(formatted_data, is_sample=True)
    return send_file(pdf, mimetype='application/pdf', as_attachment=True, download_name="WealthOS_Sample_Report.pdf")

@app.route('/download', methods=['POST'])
def process_secure_download():
    try:
        audit = PayrollAuditor.run_audit(request.form)
        formatted_data = {
            "bruto": format_currency(audit['bruto']), "travel": format_currency(audit['travel']), 
            "cellular": format_currency(audit['cellular']), "other_bonus": format_currency(audit['other_bonus']),
            "car_val": format_currency(audit['car_val']), "benefits": format_currency(audit['benefits']),
            "tax": format_currency(audit['tax']), "social": format_currency(audit['social']),
            "pen_emp": format_currency(audit['pen_emp']), "hish_emp": format_currency(audit['hish_emp']),
            "neto": format_currency(audit['neto']),
            "pen_boss": format_currency(audit['pen_boss']), "pitzuim": format_currency(audit['pitzuim']), "hish_boss": format_currency(audit['hish_boss']),
            "cost": format_currency(audit['cost']), "proj": format_currency(audit['total_savings'] * 155.2)
        }
        pdf = PDF_Elite.generate(formatted_data, is_sample=False)
        return send_file(pdf, as_attachment=True, download_name="WealthOS_VIP_Audit.pdf")
        
    except Exception as e:
        return f"System Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT)

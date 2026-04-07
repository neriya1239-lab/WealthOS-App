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
    def ensure_fonts():
        """Download and register Hebrew-supporting fonts"""
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import os, urllib.request
        
        # Using NotoSansCJK which has excellent Hebrew support
        font_path = "/tmp/NotoSansHebrew-Bold.ttf"
        regular_path = "/tmp/NotoSansHebrew-Regular.ttf"
        
        # Download Bold font
        if not os.path.exists(font_path):
            url = "https://github.com/notofonts/noto-cjk/raw/main/Sans/SubsetOTF/Hebrew/NotoSansHebrew-Bold.otf"
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as response, open(font_path, 'wb') as out_file:
                    out_file.write(response.read())
            except Exception as e:
                print(f"Failed to download bold font: {e}")
        
        # Download Regular font
        if not os.path.exists(regular_path):
            url = "https://github.com/notofonts/noto-cjk/raw/main/Sans/SubsetOTF/Hebrew/NotoSansHebrew-Regular.otf"
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as response, open(regular_path, 'wb') as out_file:
                    out_file.write(response.read())
            except Exception as e:
                print(f"Failed to download regular font: {e}")
        
        # Register fonts
        try:
            pdfmetrics.registerFont(TTFont('HebrewBold', font_path))
            pdfmetrics.registerFont(TTFont('HebrewRegular', regular_path))
            return 'HebrewRegular', 'HebrewBold'
        except Exception as e:
            print(f"Failed to register Noto fonts: {e}")
            # Fallback - use built-in fonts
            return 'Helvetica', 'Helvetica-Bold'

    @classmethod
    def generate(cls, data_dict, is_sample=False):
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib import colors
        from reportlab.pdfbase import pdfmetrics
        
        # Get Hebrew fonts
        font_reg, font_bold = cls.ensure_fonts()
        
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        w, h = A4
        
        # Color scheme
        C_BG = colors.HexColor("#06090F")
        C_GOLD = colors.HexColor("#D4AF37")
        C_TEXT = colors.HexColor("#1A1D24")
        C_GREEN = colors.HexColor("#10B981")

        # Header section
        p.setFillColor(C_BG)
        p.rect(0, h-130, w, 130, fill=1)
        p.setFillColor(C_GOLD)
        p.setFont(font_bold, 40)
        p.drawRightString(w - 40, h - 70, get_display("WealthOS"))
        
        p.setFillColor(colors.white)
        p.setFont(font_bold, 16)
        doc_title = "אנליזת תלוש שכר - דוח דגימה" if is_sample else "דוח ביקורת שכר מלא (VIP)"
        p.drawRightString(w - 40, h - 95, get_display(doc_title))
        p.setFont(font_reg, 11)
        p.setFillColor(colors.HexColor("#AAAAAA"))
        p.drawString(40, h - 95, f"Ref: WOS-{random.getrandbits(16)}")

        y = h - 165
        p.setFillColor(C_TEXT)
        p.setFont(font_bold, 22)
        p.drawRightString(w - 40, y, get_display("פירוט נתונים פיננסיים (ברמת השקל):"))
        p.setStrokeColor(C_GOLD)
        p.setLineWidth(3)
        p.line(w - 40, y - 12, 40, y - 12)

        y -= 40
        def draw_row(label, val, is_bold=False, color=C_TEXT, size=14):
            nonlocal y
            p.setFillColor(color)
            p.setFont(font_bold if is_bold else font_reg, size)
            p.drawRightString(w - 50, y, get_display(label))
            p.setFillColor(C_TEXT)
            p.setFont(font_bold if is_bold else font_reg, size)
            p.drawString(90, y, val)
            y -= 28

        # Part A: Salary and additions
        draw_row("שכר בסיס (ממנו מופרשת פנסיה):", data_dict['bruto'], is_bold=True, size=16)
        
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
            p.setStrokeColor(colors.HexColor("#E0E0E0"))
            p.setLineWidth(1.5)
            p.line(w - 50, y, 90, y)
            y -= 18

        # Part B: Deductions
        y -= 12
        p.setFillColor(colors.HexColor("#333333"))
        p.setFont(font_bold, 13)
        p.drawRightString(w - 50, y, get_display("ניכויי חובה והפרשות עובד:"))
        y -= 28
        
        draw_row("מס הכנסה (מדורג לאחר נקודות זיכוי):", f"- {data_dict['tax']}")
        draw_row("ביטוח לאומי ומס בריאות:", f"- {data_dict['social']}")
        draw_row("הפרשות לפנסיה (חלק עובד):", f"- {data_dict['pen_emp']}")
        draw_row("הפרשות לקרן השתלמות (חלק עובד):", f"- {data_dict['hish_emp']}")
        
        y += 12
        p.setStrokeColor(colors.HexColor("#E0E0E0"))
        p.setLineWidth(1.5)
        p.line(w - 50, y, 90, y)
        y -= 18

        # Part C: Final net salary
        p.setFillColor(colors.HexColor("#F0FDF4"))
        p.roundRect(40, y - 28, w - 80, 52, 10, fill=1, stroke=0)
        y -= 8
        draw_row("שכר נטו סופי לחשבון הבנק:", data_dict['neto'], is_bold=True, color=C_GREEN, size=19)
        y -= 18

        # Part D: Employer provisions
        p.setFillColor(colors.HexColor("#333333"))
        p.setFont(font_bold, 13)
        p.drawRightString(w - 50, y, get_display("הפרשות מעסיק לקופות מחוץ לשכר (כסף שלך):"))
        y -= 28
        
        draw_row("פנסיה (תגמולי מעסיק):", f"+ {data_dict['pen_boss']}")
        draw_row("פיצויים (מעסיק):", f"+ {data_dict['pitzuim']}")
        draw_row("קרן השתלמות (מעסיק):", f"+ {data_dict['hish_boss']}")
        
        y += 12
        p.setStrokeColor(colors.HexColor("#E0E0E0"))
        p.setLineWidth(1.5)
        p.line(w - 50, y, 90, y)
        y -= 18

        # Part E: Total employer cost
        p.setFillColor(colors.HexColor("#FFFBEB"))
        p.roundRect(40, y - 28, w - 80, 52, 10, fill=1, stroke=0)
        y -= 8
        draw_row("עלות מעסיק כוללת (השווי האמיתי לחברה):", data_dict['cost'], is_bold=True, color=C_GOLD, size=18)

        # Part F: 10-year projection
        y -= 55
        p.setFillColor(C_BG)
        p.roundRect(40, y - 72, w - 80, 92, 14, fill=1, stroke=0)
        p.setFillColor(colors.white)
        p.setFont(font_bold, 15)
        p.drawRightString(w - 60, y - 25, get_display("תחזית צבירת הון דריבית (10 שנים, 5% תשואה):"))
        p.setFillColor(C_GOLD)
        p.setFont(font_bold, 26)
        p.drawString(80, y - 30, data_dict['proj'])
        
        # Footer
        p.setFillColor(colors.HexColor("#777777"))
        p.setFont(font_reg, 10)
        footer_text = get_display("WealthOS 2026 - הדוח הינו סימולציה כלכלית ואינו מהווה תחליף לייעוץ פנסיוני ומיסוי מקצועי")
        p.drawCentredString(w/2, 25, footer_text)

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

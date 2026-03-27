# -*- coding: utf-8 -*-
# ================== intrusion_detector.py ==================
# Logic ban IP hoàn chỉnh:
# - IP bị ban → chặn TOÀN BỘ web (trả trang HTML đẹp)
# - IP được mở → vào web bình thường
# - Gọi thẳng API không qua web → thông báo + gửi Telegram

import os, json, time
from flask import request, session
from geo_lookup import get_ip_info, format_location

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "intrusion_log.json")
_last_alert = {}  # throttle gửi Telegram: ip → timestamp

# ══════════════════════════════════════════════════════════════
# LẤY IP THỰC
# ══════════════════════════════════════════════════════════════
def get_real_ip():
    for h in ["CF-Connecting-IP", "X-Forwarded-For", "X-Real-IP"]:
        v = request.headers.get(h, "")
        if v:
            return v.split(",")[0].strip()
    return request.remote_addr or "unknown"

# ══════════════════════════════════════════════════════════════
# KIỂM TRA IP BỊ BAN (đọc từ DB để nhận /banip realtime)
# ══════════════════════════════════════════════════════════════
def is_banned(ip: str) -> bool:
    try:
        from config import load_db
        db   = load_db()
        info = db.get("banned_ips", {}).get(ip)
        if info:
            if time.time() < info.get("ban_until", 0):
                return True
            else:
                # Hết hạn → tự xóa
                del db["banned_ips"][ip]
                from config import save_db
                save_db(db)
    except Exception:
        pass
    return False

# ══════════════════════════════════════════════════════════════
# LƯU LOG
# ══════════════════════════════════════════════════════════════
def save_log(ip, username, path, ua):
    try:
        logs = []
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
    except Exception:
        logs = []

    # Lấy thông tin địa lý
    try:
        geo = get_ip_info(ip)
    except Exception:
        geo = {}

    logs.insert(0, {
        "time":     time.strftime("%H:%M:%S %d/%m/%Y"),
        "ip":       ip,
        "username": username or "(chưa đăng nhập)",
        "path":     path,
        "ua":       ua[:120],
        "city":     geo.get("city",""),
        "region":   geo.get("region",""),
        "country":  geo.get("country",""),
        "isp":      geo.get("isp",""),
        "lat":      geo.get("lat",0),
        "lon":      geo.get("lon",0),
        "map_url":  geo.get("map_url",""),
    })
    logs = logs[:300]
    try:
        with open(LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

# ══════════════════════════════════════════════════════════════
# GỬI CẢNH BÁO TELEGRAM (throttle 60s/IP)
# ══════════════════════════════════════════════════════════════
def send_alert(ip, username, path, ua):
    now = time.time()
    if now - _last_alert.get(ip, 0) < 60:
        return
    _last_alert[ip] = now
    try:
        from config import BOT_TOKEN, ADMIN_ID
        import requests as req

        # Lấy thông tin địa lý
        try:
            geo      = get_ip_info(ip)
            location = format_location(geo)
            isp      = geo.get("isp","Không rõ")
            map_url  = geo.get("map_url","")
        except Exception:
            location = "Không xác định"
            isp      = "Không rõ"
            map_url  = ""

        # Phân tích lý do crack rõ ràng
        game = path.replace("/api/predict/","").upper() if "/api/predict/" in path else path
        reason_detail = (
            f"Gọi thẳng API dự đoán game {game} "
            f"từ bên ngoài web (không có CSRF token) — "
            f"đang cố lấy dự đoán mà không mua key."
        )

        # Phân tích trình duyệt/tool
        ua_lower = ua.lower()
        if "python" in ua_lower:       tool = "Python script (requests/httpx)"
        elif "curl" in ua_lower:       tool = "cURL command line"
        elif "postman" in ua_lower:    tool = "Postman"
        elif "insomnia" in ua_lower:   tool = "Insomnia"
        elif "go-http" in ua_lower:    tool = "Go HTTP client"
        elif "java" in ua_lower:       tool = "Java HTTP client"
        elif "node" in ua_lower:       tool = "Node.js / axios"
        elif ua == "N/A" or not ua:    tool = "Script không có User-Agent"
        else:                          tool = "Trình duyệt / tool khác"

        msg = (
            f"🚨 PHÁT HIỆN CRACK API\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 Tài khoản: {username or '(chưa đăng nhập)'}\n"
            f"🕐 Thời gian: {time.strftime('%H:%M:%S %d/%m/%Y')}\n\n"
            f"━━ CHI TIẾT KỸ THUẬT ━━\n"
            f"📡 IP: {ip}\n"
            f"🌍 Vị trí: {location}\n"
            f"🏢 ISP/Nhà mạng: {isp}\n"
            f"🔗 Route bị gọi: {path}\n"
            f"🛠️ Công cụ dùng: {tool}\n"
            f"💻 User-Agent: {ua[:100]}\n\n"
            f"━━ LÝ DO PHÁT HIỆN ━━\n"
            f"⚠️ {reason_detail}\n"
        )
        if map_url:
            msg += f"\n📍 Vị trí ước tính trên bản đồ:\n{map_url}\n"

        msg += (
            f"\n━━ HÀNH ĐỘNG ━━\n"
            f"👉 Ban TK:  /band {username or 'N/A'}\n"
            f"👉 Ban IP:  /banip {ip}\n"
            f"👉 Chi tiết: /checkip {ip}"
        )

        req.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": ADMIN_ID, "text": msg},
            timeout=4
        )
    except Exception as e:
        print(f"[ALERT ERROR] {e}")

# ══════════════════════════════════════════════════════════════
# HTML TRANG BỊ CHẶN
# ══════════════════════════════════════════════════════════════
def _blocked_html(ip):
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Bị chặn - TOOLKIEMLAISEW.SITE</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0a1628;display:flex;align-items:center;justify-content:center;
     min-height:100vh;font-family:Arial,sans-serif;color:#fff;text-align:center;padding:20px}}
.box{{max-width:420px;width:100%}}
.icon{{font-size:80px;margin-bottom:20px}}
h1{{color:#ff4444;font-size:26px;font-weight:bold;margin-bottom:12px}}
.ip{{background:rgba(255,68,68,0.1);border:1px solid rgba(255,68,68,0.3);
     border-radius:8px;padding:10px 20px;margin:16px 0;color:#ff8888;font-size:14px}}
p{{color:#aaa;font-size:14px;line-height:1.7;margin-bottom:6px}}
a{{color:#00e6b4;font-weight:bold;text-decoration:none;font-size:15px}}
.btn{{display:inline-block;margin-top:20px;padding:12px 28px;
      background:#00e6b4;border-radius:10px;color:#0a1628;font-weight:bold;font-size:15px}}
</style></head>
<body><div class="box">
<div class="icon">🚫</div>
<h1>IP của bạn đã bị chặn</h1>
<div class="ip">📡 IP: {ip}</div>
<p>Bạn đã vi phạm điều khoản sử dụng</p>
<p>của <strong>TOOLKIEMLAISEW.SITE</strong></p>
<p style="margin-top:14px">Để khiếu nại hoặc mua key:</p>
<p><a href="https://t.me/sewdangcap">📩 t.me/sewdangcap</a></p>
</div></body></html>"""

# ══════════════════════════════════════════════════════════════
# MIDDLEWARE CHÍNH
# ══════════════════════════════════════════════════════════════
def detect_and_block():
    from flask import jsonify, make_response

    # Bỏ qua static files hoàn toàn
    if request.path.startswith("/static/"):
        return None

    ip = get_real_ip()

    # ── 1. KIỂM TRA IP BỊ BAN ─────────────────────────────────────────────
    if is_banned(ip):
        if request.path.startswith("/api/"):
            # API call → JSON
            return jsonify({
                "ok":    False,
                "error": "tuổi đéo gì mà lấy 🖕 IP bị chặn. Mua key: t.me/sewdangcap",
                "code":  403
            }), 403
        else:
            # Trang web → HTML đẹp
            return make_response(_blocked_html(ip), 403)

    # ── 2. CHỈ KIỂM TRA CRACK KHI GỌI /api/predict/* ──────────────────────
    if not request.path.startswith("/api/predict"):
        return None

    # IP không bị ban + gọi /api/predict → kiểm tra CSRF
    username = session.get("username")
    ua       = request.headers.get("User-Agent", "N/A")
    csrf     = request.headers.get("X-CSRF-Token", "").strip()

    if not csrf:
        # Gọi thẳng từ ngoài không qua web
        save_log(ip, username, request.path, ua)
        send_alert(ip, username, request.path, ua)
        print(f"[CRACK] {ip} | {username} | no CSRF")
        return jsonify({
            "ok":    False,
            "error": "tuổi đéo gì mà lấy 🖕\nMuốn dùng tool? Mua key tại: t.me/sewdangcap",
            "code":  403
        }), 403

    return None

# ══════════════════════════════════════════════════════════════
# ĐĂNG KÝ VÀO FLASK
# ══════════════════════════════════════════════════════════════
def register_intrusion_detector(app):
    @app.before_request
    def intrusion_check():
        return detect_and_block()
    print("[SECURITY] Intrusion Detector ✅")

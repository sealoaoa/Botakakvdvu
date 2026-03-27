# -*- coding: utf-8 -*-
# ================== routes.py ==================
# Tất cả route Flask

from flask import Blueprint, request, jsonify, redirect, url_for, session, render_template_string
from config import load_db, save_db, hash_password, create_key, get_vip_level, get_history_depth, VIP_LEVELS, SHOP_NAME, ADMIN_ID, BOT_TOKEN, pending_deposits
import config
from templates import (
    HTML_REGISTER, HTML_LOGIN, HTML_MENU, HTML_ACCOUNT,
    HTML_BUY_KEY, HTML_DEPOSIT, HTML_ENTER_KEY,
    GAME_TEMPLATES
)
from predict import predict, get_formatted_history, load_history, save_history, load_prediction_history, record_prediction, update_prediction_results, HIST, PREDICTION_HISTORY, STATS
from algorithms import safe_json, normalize, API_SUN, API_HIT, API_B52A, API_B52B, API_LUCK8, API_SICBO, API_789, API_68GB, API_LC79
import time, json, os, requests
import time, json, os, requests, re
from vn_time import vn_strftime, vn_date_str, vn_short, key_expires_str
from security import api_protected, csrf_required, register_security, set_session_fingerprint
from response_encrypt import encrypted_response
from nanoid import generate

bp = Blueprint('main', __name__)

@bp.route("/")
def index():
    if "username" in session:
        return redirect(url_for("main.menu"))
    return redirect(url_for("main.login"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    error = None
    success = None
    if request.method == "POST":
        try:
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            password2 = request.form.get("password2", "").strip()
            
            # Validate input not empty
            if not username or not password or not password2:
                error = "Vui lòng điền đầy đủ thông tin"
            elif len(username) < 3:
                error = "Tên đăng nhập phải có ít nhất 3 ký tự"
            elif len(password) < 6:
                error = "Mật khẩu phải có ít nhất 6 ký tự"
            elif password != password2:
                error = "Mật khẩu không khớp"
            else:
                db = load_db()
                if username in db["users"]:
                    error = "Tên đăng nhập đã tồn tại"
                else:
                    user_id = generate(size=10).upper()
                    db["users"][username] = {
                        "user_id": user_id,
                        "password": hash_password(password),
                        "balance": 0,
                        "created_at": time.time(),
                        "vip_level": "Đồng",
                        "vip_exp": 0,
                        "total_predictions": 0,
                        "correct_predictions": 0
                    }
                    save_db(db)
                    # Tự động chuyển sang trang đăng nhập
                    return redirect(url_for("main.login"))
        except Exception as e:
            print(f"❌ Lỗi đăng ký: {e}")
            error = "Lỗi hệ thống. Vui lòng thử lại sau."
    return render_template_string(HTML_REGISTER, error=error, success=success)


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        db = load_db()

        # Kiểm tra nếu user bị khóa trước khi kiểm tra password
        if username in db.get("blocked_web_login", []):
            error = "⛔ Tài khoản của bạn đã bị khóa vĩnh viễn. Vui lòng liên hệ admin để được hỗ trợ."
            return render_template_string(HTML_LOGIN, error=error)

        if username in db["users"]:
            if db["users"][username]["password"] == hash_password(password):
                session["username"] = username
                set_session_fingerprint()
                return redirect(url_for("main.menu"))
            else:
                error = "Mật khẩu không đúng"
        else:
            error = "Tài khoản không tồn tại"
    return render_template_string(HTML_LOGIN, error=error)


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.login"))


@bp.route("/menu")
def menu():
    if "username" not in session:
        return redirect(url_for("main.login"))
    db = load_db()
    username = session["username"]

    # Kiểm tra nếu user bị khóa
    if username in db.get("blocked_web_login", []):
        session.clear()
        return redirect(url_for("main.login"))

    balance = db["users"][username].get("balance", 0)

    has_active_key = False
    key_expires = ""
    active_key = db["active"].get(username)

    if active_key:
        if active_key["expiresAt"] is None:
            has_active_key = True
            key_expires = "Vĩnh viễn"
        elif active_key["expiresAt"] > time.time():
            has_active_key = True
            key_expires = key_expires_str(active_key["expiresAt"])

    return render_template_string(HTML_MENU,
                                  balance=balance,
                                  has_active_key=has_active_key,
                                  key_expires=key_expires)


@bp.route("/account")
def account():
    if "username" not in session:
        return redirect(url_for("main.login"))
    db = load_db()
    username = session["username"]

    # Kiểm tra nếu user bị khóa
    if username in db.get("blocked_web_login", []):
        session.clear()
        return redirect(url_for("main.login"))

    user = db["users"][username]
    user_id = user.get("user_id", "N/A")
    balance = user.get("balance", 0)
    created_at = vn_date_str(user.get("created_at", time.time()))

    # Lấy thông tin VIP
    vip_level = user.get("vip_level", "Đồng")
    vip_exp = user.get("vip_exp", 0)
    vip_info = VIP_LEVELS.get(vip_level, VIP_LEVELS["Đồng"])
    vip_icon = vip_info["icon"]
    vip_color = vip_info["color"]
    vip_benefits = vip_info["benefits"]
    total_predictions = user.get("total_predictions", 0)
    correct_predictions = user.get("correct_predictions", 0)

    # Lấy lịch sử giao dịch của user
    user_transactions = []
    if "transactions" in db:
        for trans in db["transactions"]:
            if trans.get("username") == username:
                trans_copy = trans.copy()
                trans_copy["time_str"] = vn_date_str(trans["time"])
                user_transactions.append(trans_copy)
        # Sắp xếp theo thời gian mới nhất
        user_transactions.sort(key=lambda x: x["time"], reverse=True)

    return render_template_string(HTML_ACCOUNT,
                                  user_id=user_id,
                                  username=username,
                                  balance=balance,
                                  created_at=created_at,
                                  vip_level=vip_level,
                                  vip_icon=vip_icon,
                                  vip_color=vip_color,
                                  vip_benefits=vip_benefits,
                                  vip_exp=vip_exp,
                                  total_predictions=total_predictions,
                                  correct_predictions=correct_predictions,
                                  transactions=user_transactions)


@bp.route("/buy-key", methods=["GET", "POST"])
def buy_key():
    if "username" not in session:
        return redirect(url_for("main.login"))

    db = load_db()
    username = session["username"]

    # Kiểm tra nếu user bị khóa
    if username in db.get("blocked_web_login", []):
        session.clear()
        return redirect(url_for("main.login"))

    balance = db["users"][username].get("balance", 0)
    error = None
    success = None

    if request.method == "POST":
        key_type = request.form.get("key_type")
        price = int(request.form.get("price"))

        if balance < price:
            error = f"Số dư không đủ! Bạn cần {price:,}đ nhưng chỉ có {balance:,}đ"
        else:
            db["users"][username]["balance"] -= price

            days = None
            if key_type == "1d":
                days = 1
            elif key_type == "1t":
                days = 7
            elif key_type == "1thang":
                days = 30
            elif key_type == "vv":
                days = None

            # --- LOGIC CỘNG DỒN THỜI GIAN (MỚI) ---
            current_active = db["active"].get(username)
            now = time.time()
            new_expires_at = None

            if days is None:
                # Mua vĩnh viễn -> Set luôn là None
                new_expires_at = None
            else:
                # Nếu đang có key vĩnh viễn -> Giữ nguyên
                if current_active and current_active.get("expiresAt") is None:
                    new_expires_at = None
                # Nếu đang có key còn hạn -> Cộng thêm vào hạn cũ
                elif current_active and current_active.get("expiresAt") and current_active["expiresAt"] > now:
                    new_expires_at = current_active["expiresAt"] + (days * 86400)
                # Nếu hết hạn hoặc chưa có -> Tính từ bây giờ
                else:
                    new_expires_at = now + (days * 86400)
            # ---------------------------------------

            new_key = create_key("LK", days, price)
            new_key["usedBy"] = username
            new_key["status"] = "used"
            new_key["expiresAt"] = new_expires_at
            db["shop_keys"].append(new_key)

            # Tự động kích hoạt key cho user với thời gian đã cộng dồn
            db["active"][username] = {
                "code": new_key["code"],
                "type": new_key["type"],
                "expiresAt": new_expires_at,
                "activatedAt": time.time()
            }

            # Lưu lịch sử mua key
            if "transactions" not in db:
                db["transactions"] = []

            transaction = {
                "type": "buy_key",
                "username": username,
                "key_code": new_key['code'],
                "key_type": key_type,
                "amount": price,
                "time": time.time(),
                "status": "completed"
            }
            db["transactions"].append(transaction)

            save_db(db)

            success = f"""✅ Mua key thành công!<br><br>
            <div style="background:rgba(0,230,180,0.1);padding:15px;border-radius:12px;margin:15px 0;text-align:center;">
                <div style="font-size:18px;font-weight:bold;color:#00e6b4;margin-bottom:10px;">🔑 Mã Key Của Bạn</div>
                <div style="display:flex;gap:10px;align-items:center;justify-content:center;">
                    <input type="text" id="keyCode" value="{new_key['code']}" readonly
                           style="padding:12px;background:rgba(0,0,0,0.3);border:1px solid rgba(0,230,180,0.3);
                                  border-radius:8px;color:#fff;font-size:16px;font-weight:bold;text-align:center;
                                  flex:1;max-width:300px;">
                    <button onclick="copyKey()" style="padding:12px 20px;background:linear-gradient(135deg,#00e6b4,#00b4d8);
                            border:none;border-radius:8px;color:#0a1628;font-weight:bold;cursor:pointer;
                            transition:all 0.3s;">
                        📋 Sao chép
                    </button>
                </div>
                <div id="copyMessage" style="margin-top:10px;color:#00ff99;font-size:14px;display:none;">
                    ✅ Đã sao chép!
                </div>
            </div>
            <script>
            function copyKey() {{
                const keyInput = document.getElementById('keyCode');
                keyInput.select();
                document.execCommand('copy');
                const msg = document.getElementById('copyMessage');
                msg.style.display = 'block';
                setTimeout(() => msg.style.display = 'none', 2000);
            }}
            </script>"""
            balance = db["users"][username]["balance"]

    return render_template_string(HTML_BUY_KEY,
                                  balance=balance,
                                  error=error,
                                  success=success)


@bp.route("/deposit", methods=["GET", "POST"])
def deposit():
    if "username" not in session:
        return redirect(url_for("main.login"))

    db = load_db()
    username = session["username"]

    if username in db.get("blocked_web_login", []):
        session.clear()
        return redirect(url_for("main.login"))

    from sepay_webhook import create_deposit_order, _load as load_pending

    error = None
    transfer_content = None
    amount_chosen = None
    balance = db["users"][username].get("balance", 0)

    if request.method == "POST":
        # Tạo đơn mới khi user chọn số tiền
        try:
            amount_chosen = int(request.form.get("amount", 0))
            if amount_chosen < 10000:
                error = "Số tiền tối thiểu là 10,000đ"
            else:
                transfer_content = create_deposit_order(username, amount_chosen)
        except (ValueError, TypeError):
            error = "Số tiền không hợp lệ"
    else:
        # GET: kiểm tra xem user có đơn chờ chưa hết hạn không → giữ nguyên
        pending = load_pending()
        now = time.time()
        for key, order in pending.items():
            if order.get("username") == username and now - order.get("created_at", 0) < 1800:
                transfer_content = key
                amount_chosen = order.get("amount", 0)
                break

    return render_template_string(
        HTML_DEPOSIT,
        username=username,
        balance=balance,
        error=error,
        transfer_content=transfer_content,
        amount_chosen=amount_chosen,
    )


@bp.route("/api/sepay-webhook", methods=["POST", "OPTIONS"])
def sepay_webhook():
    """SePay gọi endpoint này khi có giao dịch - Fix 403"""
    if request.method == "OPTIONS":
        res = jsonify({"ok": True})
        res.headers["Access-Control-Allow-Origin"] = "*"
        res.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        res.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        return res, 200
    from sepay_webhook import process_sepay_webhook
    payload = request.get_json(silent=True) or {}
    result  = process_sepay_webhook(payload)
    res = jsonify(result)
    res.headers["Access-Control-Allow-Origin"] = "*"
    return res


@bp.route("/api/check-key")
def api_check_key():
    """JS gọi mỗi 30s để kiểm tra key còn hạn không - kick ngay nếu hết"""
    if "username" not in session:
        return jsonify({"ok": False, "expired": True})
    db       = load_db()
    username = session["username"]
    active   = db["active"].get(username)
    if not active:
        return jsonify({"ok": False, "expired": True, "reason": "Chưa kích hoạt key"})
    if active["expiresAt"] is not None and active["expiresAt"] < time.time():
        del db["active"][username]
        save_db(db)
        return jsonify({"ok": False, "expired": True, "reason": "Key đã hết hạn"})
    # Trả về thời gian còn lại
    remaining = None if active["expiresAt"] is None else int(active["expiresAt"] - time.time())
    return jsonify({"ok": True, "expired": False, "remaining": remaining,
                    "expires": key_expires_str(active["expiresAt"])})


@bp.route("/api/balance")
@api_protected
def api_balance():
    """Dùng cho JS polling kiểm tra tiền đã vào chưa"""
    if "username" not in session:
        return jsonify({"ok": False, "balance": 0})
    db = load_db()
    username = session["username"]
    balance = db["users"].get(username, {}).get("balance", 0)
    return jsonify({"ok": True, "balance": balance})


@bp.route("/game/<gcode>")
def game(gcode):
    if "username" not in session:
        return redirect(url_for("main.login"))

    username = session["username"]
    db = load_db()

    # Check if user is banned from web login
    if username in db.get("blocked_web_login", []):
        session.clear()
        return redirect(url_for("main.login"))
    
    gcode = gcode.lower()

    active_key = db["active"].get(username)

    # Kiểm tra nếu có key active và còn hạn
    if not active_key:
        return redirect(url_for("main.enter_key", gcode=gcode))

    # Kiểm tra key hết hạn
    if active_key["expiresAt"] and active_key["expiresAt"] < time.time():
        # Xóa key hết hạn khỏi active
        del db["active"][username]
        save_db(db)
        return redirect(url_for("main.enter_key", gcode=gcode))

    template = GAME_TEMPLATES.get(gcode)
    if not template:
        return redirect(url_for("main.menu"))

    # FIX: Tự động cập nhật link iframe Sunwin/Sicbo mới nhất
    if gcode in ['sun', 'sicbo']:
        template = template.replace("web.sunwin.lt", "web.sunwin.ag")
        template = template.replace("web.sunwin.gg", "web.sunwin.ag")
        template = template.replace("web.sunwin.pw", "web.sunwin.ag")
        template = template.replace("web.sunwin.id", "web.sunwin.ag")

    return render_template_string(template)


@bp.route("/enter-key/<gcode>", methods=["GET", "POST"])
def enter_key(gcode):
    if "username" not in session:
        return redirect(url_for("main.login"))

    username = session["username"]
    db = load_db()

    # Kiểm tra nếu user bị khóa
    if username in db.get("blocked_web_login", []):
        session.clear()
        return redirect(url_for("main.login"))
        
    gcode = gcode.lower()
    
    game_name_map = {
        "sun": "SunWin",
        "hit": "HitClub",
        "b52": "B52",
        "luck8": "Luck8",
        "sicbo": "Sicbo SunWin",
        "789": "789Club",
        "68gb": "68 Game Bài",
        "lc79": "LC79",
        "sexy": "BCR Sexy"
    }
    game_name = game_name_map.get(gcode, "Unknown Game")
    game_logo_map = {
        "sun": "https://i.postimg.cc/q7ybsvSb/IMG-1615.jpg",
        "hit": "https://i.postimg.cc/66YHLSbG/IMG-1616.jpg",
        "b52": "https://i.postimg.cc/q7swtZCB/IMG-1617.jpg",
        "luck8": "https://i.postimg.cc/tg4Pgzzt/IMG-1702.jpg",
        "sicbo": "https://i.postimg.cc/5tLC4p8q/IMG-2048.jpg",
        "789": "https://i.postimg.cc/43HWjS37/789.webp",
        "68gb": "https://i.postimg.cc/zDQVG2DG/OIP.webp",
        "lc79": "https://i.postimg.cc/vTSzPJnm/lc79.webp",
        "sexy": "https://i.postimg.cc/j28zwGJf/sexy-baccarat.jpg"
    }
    game_logo = game_logo_map.get(gcode, "")

    error = None

    if request.method == "POST":
        key_code = request.form.get("key_code", "").strip().upper().replace("`", "").replace(" ", "")
        raw_input = request.form.get("key_code", "").strip().upper()
        # Dùng Regex xóa sạch mọi ký tự không phải chữ, số, gạch ngang (xóa cả dấu cách, tab, xuống dòng, dấu `)
        key_code = re.sub(r'[^A-Z0-9-]', '', raw_input)

        if not key_code:
            error = "Vui lòng nhập mã key"
        else:
            found_key = None
            for k in db["shop_keys"]:
                if k["code"] == key_code:
                    found_key = k
                    break

            if not found_key:
                error = "❌ Mã key không tồn tại"
                # Debug: In ra console để admin kiểm tra
                print(f"⚠️ User nhập: '{key_code}' - Không tìm thấy trong {len(db['shop_keys'])} keys hiện có.")
            elif found_key["status"] == "blocked":
                error = "❌ Key này đã bị khóa"
            elif found_key["usedBy"]:
                if found_key["usedBy"] == username:
                    error = "❌ Key này đã được kích hoạt trên tài khoản của bạn rồi"
                else:
                    error = "❌ Key đã được sử dụng bởi tài khoản khác. Mỗi key chỉ sử dụng được cho 1 tài khoản duy nhất"
            elif found_key.get("expiresAt") and found_key["expiresAt"] < time.time():
                error = "❌ Key đã hết hạn"
            else:
                now = time.time()
                
                # Logic cộng dồn thời gian khi nhập key
                current_active = db["active"].get(username)
                new_expires_at = None
                duration_days = found_key.get("duration_days")
                
                if duration_days is None and found_key.get("expiresAt") is None:
                    new_expires_at = None
                else:
                    if current_active and current_active.get("expiresAt") is None:
                        new_expires_at = None
                    else:
                        base_time = now
                        if current_active and current_active.get("expiresAt") and current_active["expiresAt"] > now:
                            base_time = current_active["expiresAt"]
                            
                        if duration_days is not None:
                            new_expires_at = base_time + (duration_days * 86400)
                        elif found_key.get("expiresAt") is not None:
                            remaining = max(0, found_key["expiresAt"] - found_key["createdAt"])
                            new_expires_at = base_time + remaining

                found_key["usedBy"] = username
                found_key["status"] = "used"
                found_key["expiresAt"] = new_expires_at

                # Lưu key vào active để lần sau không cần nhập lại
                db["active"][username] = {
                    "code": found_key["code"],
                    "type": found_key["type"],
                    "expiresAt": new_expires_at,
                    "activatedAt": time.time()
                }

                save_db(db)
                # Chuyển hướng về game luôn
                return redirect(url_for("main.game", gcode=gcode))

    return render_template_string(HTML_ENTER_KEY,
                                  game_name=game_name,
                                  gcode=gcode,
                                  game_logo=game_logo,
                                  error=error)


@bp.route("/api/predict/<game>")
def api_predict(game):
    # --- KIỂM TRA ĐĂNG NHẬP ---
    if "username" not in session:
        _alert_crack_attempt(None, request, game)
        return jsonify({"ok": False, "error": "có trình đéo mà lấy 🖕 Mua key: t.me/sewdangcap"})

    username = session["username"]
    db = load_db()

    # Kiểm tra có CSRF token không (gọi từ ngoài, không qua web)
    csrf_token = request.headers.get("X-CSRF-Token", "").strip()
    if not csrf_token:
        _alert_crack_attempt(username, request, game)
        return jsonify({"ok": False, "error": f"có trình đéo mà lấy 🖕 ({username}) Mua key: t.me/sewdangcap"})

    # Kiểm tra user bị khóa
    if username in db.get("blocked_web_login", []):
        session.clear()
        return jsonify({"ok": False, "error": "Tài khoản bị khóa"})

    # Kiểm tra có key kích hoạt không
    active_key = db["active"].get(username)
    if not active_key:
        return jsonify({"ok": False, "error": "Chưa kích hoạt key"})

    # Kiểm tra hạn sử dụng
    if active_key["expiresAt"] is not None and active_key["expiresAt"] < time.time():
        return jsonify({"ok": False, "error": "Key đã hết hạn"})

    game = game.lower()
    if game not in HIST:
        return jsonify({"ok": False, "error": "invalid game"})
    ban = request.args.get("ban", "md5")
    r = predict(game, ban=ban)
    return jsonify({"ok": bool(r), "result": r})


def _alert_crack_attempt(username, req, game):
    """Gửi cảnh báo Telegram khi phát hiện crack API"""
    try:
        ip = (req.headers.get("CF-Connecting-IP")
              or req.headers.get("X-Forwarded-For","").split(",")[0]
              or req.remote_addr or "unknown").strip()
        ua = req.headers.get("User-Agent","N/A")[:100]
        t  = __import__("time").strftime("%H:%M:%S %d/%m/%Y")

        msg = (
            f"🚨 PHÁT HIỆN CRACK API\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👤 Tài khoản: {username or '(chưa đăng nhập)'}\n"
            f"🎮 Game: {game}\n"
            f"📡 IP: {ip}\n"
            f"💻 UA: {ua}\n"
            f"🕐 {t}\n\n"
            f"👉 Ban web: /band {username}\n"
            f"👉 Ban IP:  /banip {ip}"
        )
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": ADMIN_ID, "text": msg},
            timeout=4
        )
    except Exception as e:
        print(f"[ALERT ERROR] {e}")

@bp.route("/api/prediction-stats/<game>")
@csrf_required
def api_prediction_stats(game):
    game = game.lower()
    if game not in PREDICTION_HISTORY:
        return jsonify({"ok": False, "error": "invalid game"})

    history = list(PREDICTION_HISTORY[game])
    total = len(history)
    correct = sum(1 for p in history if p.get("correct") == True)

    recent_10 = history[-10:] if len(history) >= 10 else history
    recent_correct = sum(1 for p in recent_10 if p.get("correct") == True)

    return jsonify({
        "ok": True,
        "game": game,
        "total_predictions": total,
        "correct_predictions": correct,
        "accuracy": round(correct / total * 100, 2) if total > 0 else 0,
        "recent_10_accuracy": round(recent_correct / len(recent_10) * 100, 2) if len(recent_10) > 0 else 0
    })

@bp.route("/api/save-luck8-history", methods=["POST"])
@api_protected
def save_luck8_history_api():
    try:
        data = request.get_json()
        history = data.get("history", [])

        if not history:
            return jsonify({"ok": False, "error": "No history data"})

        # Lưu lịch sử vào file để phân tích
        history_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "luck8_analysis_history.json")
        import os
        try:
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    existing_data = json.load(f)
            else:
                existing_data = {"sessions": []}

            # Cập nhật với lịch sử mới
            for item in history:
                # Kiểm tra xem session đã tồn tại chưa
                existing_session = next((s for s in existing_data["sessions"] if s.get("session") == item.get("session")), None)
                if not existing_session:
                    existing_data["sessions"].insert(0, {
                        "session": item.get("session"),
                        "prediction": item.get("prediction"),
                        "result": item.get("result"),
                        "isCorrect": item.get("isCorrect"),
                        "timestamp": time.time()
                    })

            # Giữ tối đa 100 phiên
            existing_data["sessions"] = existing_data["sessions"][:100]

            with open(history_file, 'w') as f:
                json.dump(existing_data, f, ensure_ascii=False, indent=2)

            return jsonify({"ok": True})
        except Exception as e:
            print(f"Lỗi lưu file lịch sử: {e}")
            return jsonify({"ok": False, "error": str(e)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})
@bp.route("/api/test-send-button", methods=["GET"])
def test_send_button():
    """Test gửi button duyệt cho admin"""
    import asyncio
    
    async def send_test():
        try:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Test Button", callback_data=f"approve_test123")]
            ])
            
            msg = "🧪 TEST BUTTON DUYỆT ĐƠN\n\nNếu bạn thấy button này, bot đang hoạt động!"
            
            if config.bot_app and config.bot_app.bot:
                await config.bot_app.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=msg,
                    reply_markup=keyboard
                )
                return "✅ Message gửi thành công!"
            else:
                return "❌ bot_app chưa init"
        except Exception as e:
            return f"❌ Lỗi: {str(e)}"
    
    try:
        result = asyncio.run(send_test())
        return result
    except Exception as e:
        return f"❌ Error: {str(e)}"


@bp.route("/api/confirm-deposit", methods=["POST"])
def confirm_deposit():
    if "username" not in session:
        return jsonify({"ok": False, "error": "Not logged in"})

    db = load_db()
    username = session["username"]

    # Check if user is banned from web login
    if username in db.get("blocked_web_login", []):
        session.clear()
        return jsonify({"ok": False, "error": "Tài khoản của bạn đã bị khóa."})

    data = request.get_json()
    amount = data.get("amount")

    if not amount or amount <= 0:
        return jsonify({"ok": False, "error": "Invalid amount"})

    user_id = session.get("user_id",
                          "unknown")  # Assuming user_id is stored in session

    deposit_id = f"{user_id}_{int(time.time())}"
    pending_deposits[deposit_id] = {
        "user_id": user_id,
        "user_telegram":
        username,  # Use username as fallback if no telegram username
        "user_fullname": username,  # Use username as fallback
        "username": username,
        "amount": amount,
        "time": time.time()
    }

    if config.bot_app:
        try:
            admin_msg = (f"💰 XÁC NHẬN ĐÃ CHUYỂN KHOẢN (Web)\n\n"
                         f"🎮 Tài khoản: {username}\n"
                         f"💵 Số tiền: {amount:,}đ\n"
                         f"🔑 ID: {deposit_id}\n\n"
                         f"User đã xác nhận chuyển khoản qua web!\n\n"
                         f"Duyệt: /duyet {username}")
            
            # Sử dụng requests để gửi tin nhắn tránh lỗi event loop
            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", 
                          json={"chat_id": ADMIN_ID, "text": admin_msg})
        except Exception as e:
            print(f"Error sending to admin: {e}")

    return jsonify({"ok": True})


@bp.route("/api/cancel-deposit", methods=["POST"])
@api_protected
def api_cancel_deposit():
    if "username" not in session:
        return jsonify({"ok": False, "error": "Vui lòng đăng nhập"})
    
    username = session["username"]
    
    try:
        from sepay_webhook import _load
        pending = _load()
        
        keys_to_delete = [k for k, v in pending.items() if v.get("username") == username]
        for k in keys_to_delete:
            del pending[k]
            
        if keys_to_delete:
            try:
                from sepay_webhook import _save
                _save(pending)
            except ImportError:
                pass  # Bỏ qua nếu module không có hàm _save (lưu trên ram)
            
        from config import pending_deposits
        tg_keys = [k for k, v in pending_deposits.items() if v.get("username") == username]
        for k in tg_keys:
            del pending_deposits[k]
            
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})

@bp.route("/ping")
def ping():
    """Endpoint để keep_alive tự ping, tránh Render free bị ngủ."""
    return "pong", 200


def register_routes(app):
    app.register_blueprint(bp)
    register_security(app)

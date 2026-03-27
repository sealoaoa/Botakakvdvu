# -*- coding: utf-8 -*-
# ================== csrf_token.py ==================
# CSRF Token Protection - Chặn script/curl gọi API từ bên ngoài
# Nguyên lý: Mỗi session có 1 token bí mật, JS gửi kèm header X-CSRF-Token
# Curl/python-requests không có token → bị chặn 100%

import os, hmac, hashlib, time
from flask import request, session, jsonify
from functools import wraps

SECRET = os.getenv("SECRET_KEY", "minhsang_shop_secret_2024_xK9p")

# ── Tạo token từ session username + secret ──────────────────────────────────
def generate_csrf_token() -> str:
    username = session.get("username", "anonymous")
    ts       = str(int(time.time() // 3600))          # Đổi mới mỗi 1 tiếng
    raw      = f"{username}:{ts}:{SECRET}"
    return hmac.new(SECRET.encode(), raw.encode(), hashlib.sha256).hexdigest()

# ── Xác thực token từ header X-CSRF-Token ───────────────────────────────────
def verify_csrf_token() -> bool:
    token = request.headers.get("X-CSRF-Token", "").strip()
    if not token:
        return False
    # Chấp nhận token của giờ hiện tại và giờ trước (tránh expire giữa chừng)
    username = session.get("username", "anonymous")
    for ts_offset in [0, -1]:
        ts  = str(int(time.time() // 3600) + ts_offset)
        raw = f"{username}:{ts}:{SECRET}"
        expected = hmac.new(SECRET.encode(), raw.encode(), hashlib.sha256).hexdigest()
        if hmac.compare_digest(token, expected):
            return True
    return False

# ── Decorator bảo vệ từng route ─────────────────────────────────────────────
def csrf_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not verify_csrf_token():
            return jsonify({
                "ok":    False,
                "error": "tuổi đéll mà đòi lấy 🖕 Không có quyền truy cập.",
                "code":  403
            }), 403
        return f(*args, **kwargs)
    return decorated

# ── Route trả token cho JS ───────────────────────────────────────────────────
def register_csrf_route(app):
    """Đăng ký /api/csrf-token để JS lấy token"""
    from flask import Blueprint
    bp = Blueprint("csrf", __name__)

    @bp.route("/api/csrf-token")
    def get_csrf_token():
        if "username" not in session:
            return jsonify({"ok": False}), 401
        return jsonify({"ok": True, "token": generate_csrf_token()})

    app.register_blueprint(bp)

# -*- coding: utf-8 -*-
# ================== domain_guard.py ==================
# Bao ve API - Chi cho phep truy cap tu ten mien duoc phep
# Truy cap trai phep -> 403

import os
from functools import wraps
from flask import request, jsonify

# ================== CAU HINH DOMAIN ==================
ALLOWED_DOMAINS = [
    "toolkiemlaisew.site",
    "www.toolkiemlaisew.site",
    "localhost",
    "127.0.0.1",
]

# ================== RESPONSE TU CHOI ==================
BLOCKED_RESPONSE = {
    "ok": False,
    "error": "tu\u1ed5i \u0111\u00e9ll m\u00e0 \u0111\u00f2i l\u1ea5y \U0001f595",
    "code": 403
}

# ================== WHITELIST PATHS ==================
WHITELIST_PATHS = [
    "/api/sepay-webhook",
    "/ping",
]

# ================== HAM KIEM TRA ==================
def get_request_origin():
    for header in ["Origin", "Referer"]:
        value = request.headers.get(header, "")
        if value:
            domain = value.replace("https://", "").replace("http://", "").split("/")[0].split(":")[0]
            return domain.strip()
    host = request.headers.get("Host", "")
    return host.split(":")[0].strip()


def is_allowed_origin():
    origin = get_request_origin()
    if not origin:
        return False
    for allowed in ALLOWED_DOMAINS:
        if origin == allowed or origin.endswith("." + allowed):
            return True
    return False


def is_internal_request():
    return request.remote_addr in ("127.0.0.1", "::1")


# ================== DECORATOR BAO VE TUNG ROUTE ==================
def require_domain(f):
    """
    Dung cho tung route cu the:

        @bp.route("/api/predict/<game>")
        @require_domain
        def api_predict(game):
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if is_internal_request():
            return f(*args, **kwargs)
        if not is_allowed_origin():
            origin = get_request_origin()
            print(f"[BLOCKED] Truy cap trai phep tu: '{origin}' -> {request.path}")
            return jsonify(BLOCKED_RESPONSE), 403
        return f(*args, **kwargs)
    return decorated


# ================== MIDDLEWARE TOAN CUC ==================
def register_domain_guard(app, protect_prefix="/api/"):
    """
    Bao ve TAT CA route bat dau bang protect_prefix.

    Them vao app.py:
        from domain_guard import register_domain_guard
        CORS(app)
        register_domain_guard(app, protect_prefix="/api/")
        register_routes(app)
    """
    @app.before_request
    def check_domain():
        if not request.path.startswith(protect_prefix):
            return None
        if request.path in WHITELIST_PATHS:
            return None
        if is_internal_request():
            return None
        if not is_allowed_origin():
            origin = get_request_origin()
            print(f"[GUARD] Chan '{origin}' -> {request.path}")
            return jsonify(BLOCKED_RESPONSE), 403
        return None

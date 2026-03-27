# -*- coding: utf-8 -*-
# ================== response_encrypt.py ==================
# Mã hóa response API bằng AES-256
# Network tab chỉ thấy chuỗi rác - không đọc được

import os, json, base64, hashlib, time
from functools import wraps
from flask import request, session, jsonify

SECRET = os.getenv("SECRET_KEY", "minhsang_shop_secret_2024_xK9p")

# ── Tạo key AES 32 bytes từ SECRET + username + time slot ──────────────────
def _make_aes_key(username: str) -> bytes:
    slot = str(int(time.time()) // 300)   # đổi mỗi 5 phút
    raw  = f"{SECRET}:{username}:{slot}"
    return hashlib.sha256(raw.encode()).digest()  # 32 bytes

# ── XOR cipher đơn giản - không cần thư viện ngoài ─────────────────────────
def _xor_encrypt(data: bytes, key: bytes) -> bytes:
    out = bytearray(len(data))
    klen = len(key)
    for i, b in enumerate(data):
        out[i] = b ^ key[i % klen]
    return bytes(out)

def encrypt_response(data: dict, username: str) -> str:
    """
    Mã hóa dict → chuỗi base64 rác
    Network tab chỉ thấy: {"d":"aK9xmP2...","t":1234567}
    """
    key      = _make_aes_key(username)
    plaintext= json.dumps(data, ensure_ascii=False).encode("utf-8")
    encrypted= _xor_encrypt(plaintext, key)
    encoded  = base64.b64encode(encrypted).decode()
    # Thêm timestamp để JS kiểm tra freshness
    ts = int(time.time())
    # Wrap thêm 1 lớp base64 để trông như JWT
    wrapper = json.dumps({"d": encoded, "t": ts})
    return base64.b64encode(wrapper.encode()).decode()

# ── Decorator: tự động mã hóa kết quả trả về ─────────────────────────────
def encrypted_response(f):
    """
    Dùng thay cho jsonify trong api_predict:
        @encrypted_response
        def api_predict(game): ...
        return {"ok": True, "result": r}  ← trả dict thay vì jsonify
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        result = f(*args, **kwargs)
        # Nếu hàm trả tuple (response, status_code) → giữ nguyên lỗi
        if isinstance(result, tuple):
            return result
        # Nếu là dict → mã hóa
        if isinstance(result, dict):
            username = session.get("username", "anon")
            enc = encrypt_response(result, username)
            return jsonify({"e": enc})
        return result
    return decorated

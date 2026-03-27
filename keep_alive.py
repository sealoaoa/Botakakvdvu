# -*- coding: utf-8 -*-
# ================== keep_alive.py ==================
# Tự ping server mỗi 10 phút để Render free không bị ngủ
# Thêm vào app.py: from keep_alive import start_keep_alive
#                  start_keep_alive()

import threading
import time
import os
import requests

# URL tự ping — ưu tiên dùng domain thật nếu có
_RENDER_URL = os.getenv("RENDER_EXTERNAL_URL", "")   # Render tự điền biến này
_CUSTOM_URL = os.getenv("APP_URL", "")                # Bạn tự điền nếu muốn dùng domain riêng

def _get_ping_url() -> str:
    if _CUSTOM_URL:
        return _CUSTOM_URL.rstrip("/") + "/ping"
    if _RENDER_URL:
        return _RENDER_URL.rstrip("/") + "/ping"
    return ""

PING_INTERVAL = 10 * 60   # 10 phút (Render ngủ sau 15 phút không có request)

def _ping_loop():
    # Chờ 30 giây sau khi server khởi động xong mới bắt đầu ping
    time.sleep(30)
    url = _get_ping_url()
    if not url:
        print("[KEEP_ALIVE] ⚠️  Không tìm thấy URL để ping. "
              "Hãy thêm APP_URL vào biến môi trường Render "
              "(vd: https://toolkiemlaisew.site)")
        return

    print(f"[KEEP_ALIVE] ✅ Bắt đầu tự ping mỗi {PING_INTERVAL // 60} phút → {url}")
    while True:
        try:
            r = requests.get(url, timeout=10)
            print(f"[KEEP_ALIVE] 🏓 Ping {url} → {r.status_code}")
        except Exception as e:
            print(f"[KEEP_ALIVE] ❌ Ping thất bại: {e}")
        time.sleep(PING_INTERVAL)


def start_keep_alive():
    """Gọi hàm này 1 lần trong app.py để khởi động thread ping."""
    t = threading.Thread(target=_ping_loop, daemon=True)
    t.start()

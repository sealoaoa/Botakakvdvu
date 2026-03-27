# -*- coding: utf-8 -*-
# ================== app.py ==================
# File chạy chính - khởi động Flask web + Telegram bot

import os, sys, subprocess, threading, asyncio

# Force flush log để Render hiện ngay lập tức
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

def install(package):
    print(f"⏳ Đang tự động cài đặt thư viện: {package}...", flush=True)
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Auto-install thư viện cần thiết
REQUIRED_PACKAGES = [
    ("requests", "requests"),
    ("flask", "flask"),
    ("flask-cors", "flask_cors"),
    ("python-dotenv", "dotenv"),
    ("nanoid", "nanoid"),
    ("python-telegram-bot", "telegram")
]

for package, module in REQUIRED_PACKAGES:
    try:
        __import__(module)
        if module == "telegram":
            from telegram.ext import Application
    except ImportError:
        install(package)
    except Exception as e:
        print(f"⚠️ Lỗi kiểm tra thư viện {package}: {e}", flush=True)
        install(package)

from flask import Flask
from flask_cors import CORS
from config import SECRET_KEY, PORT
from predict import load_history, load_prediction_history, load_cau_history
from routes import register_routes
from domain_guard import register_domain_guard
from intrusion_detector import register_intrusion_detector
from security import register_security  # ← Bảo mật tổng hợp cấp cao

# ================== KHỞI TẠO FLASK ==================
app = Flask(__name__)
app.secret_key = SECRET_KEY
CORS(app, origins=[
    "https://toolkiemlaisew.site",
    "https://www.toolkiemlaisew.site",
    "http://localhost",
    "http://127.0.0.1",
])

# ← ĐĂNG KÝ BẢO VỆ DOMAIN TRƯỚC KHI REGISTER ROUTES
register_intrusion_detector(app)
register_domain_guard(app, protect_prefix="/api/")
# register_security được gọi trong register_routes (routes.py)

# Đăng ký tất cả routes
register_routes(app)

# ================== WRAPPER THEO DÕI BOT THREAD ==================
def run_bot_with_watchdog():
    """Chạy bot và in log rõ ràng nếu crash"""
    import time as _time
    from telegram_bot import run_bot_in_thread
    print("[BOT-WATCHDOG] Bắt đầu theo dõi bot thread...", flush=True)
    while True:
        try:
            print("[BOT-WATCHDOG] Đang khởi động bot...", flush=True)
            run_bot_in_thread()
        except Exception as e:
            print(f"[BOT-WATCHDOG] ❌ Bot crash: {e}", flush=True)
            import traceback
            traceback.print_exc()
        print("[BOT-WATCHDOG] Bot dừng. Thử lại sau 10 giây...", flush=True)
        _time.sleep(10)

# ================== CHẠY CHƯƠNG TRÌNH ==================
if __name__ == "__main__":
    try:
        print("[START] Đang khởi động SHOP MINHSANG...", flush=True)
        print("[GUARD] Bảo vệ API - Chỉ cho phép: toolkiemlaisew.site", flush=True)
        print("[SECURITY] Intrusion Detector: bật theo dõi tấn công", flush=True)

        # Tải lịch sử
        load_history()
        load_prediction_history()
        load_cau_history()
        print("[OK] Đã tải lịch sử dự đoán và phân tích cầu", flush=True)

        # Khởi động Telegram bot trong thread riêng
        try:
            from telegram_bot import TELEGRAM_AVAILABLE
            if TELEGRAM_AVAILABLE:
                bot_thread = threading.Thread(target=run_bot_with_watchdog, daemon=True)
                bot_thread.start()
                print("[OK] Bot Telegram đang chạy song song", flush=True)
            else:
                print("[INFO] Telegram bot bị tắt - chỉ chạy web server", flush=True)
        except Exception as e:
            print(f"[WARNING] Không thể khởi động bot: {e}", flush=True)
            import traceback
            traceback.print_exc()
            print("[INFO] Website vẫn hoạt động bình thường", flush=True)

        print(f"[START] Flask chạy tại http://0.0.0.0:{PORT}", flush=True)

        # Giữ server luôn thức (tránh Render free bị ngủ)
        from keep_alive import start_keep_alive
        start_keep_alive()

        app.run(host="0.0.0.0", port=PORT, debug=False, use_reloader=False)
    except Exception as e:
        print(f"\n❌ LỖI SERVER NGHIÊM TRỌNG: {e}", flush=True)
        import traceback
        traceback.print_exc()
        print("👉 Vui lòng chụp ảnh màn hình lỗi này và gửi cho admin.", flush=True)
        input("Nhấn Enter để thoát...")

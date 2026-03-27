# -*- coding: utf-8 -*-
# ================== database.py ==================
# Lưu trữ data.json lên Supabase PostgreSQL
# Thay thế toàn bộ load_db() / save_db() trong config.py
#
# ── HƯỚNG DẪN CÀI ĐẶT ──────────────────────────────────────────────────────
#
# 1. Đăng ký Supabase tại https://supabase.com (miễn phí)
#
# 2. Vào project → SQL Editor → chạy lệnh sau để tạo bảng:
#
#    CREATE TABLE IF NOT EXISTS app_data (
#        key   TEXT PRIMARY KEY,
#        value JSONB NOT NULL,
#        updated_at TIMESTAMPTZ DEFAULT NOW()
#    );
#
# 3. Vào Project Settings → API → copy:
#    - Project URL  → SUPABASE_URL
#    - anon/public key → SUPABASE_KEY
#
# 4. Thêm vào Render Environment Variables:
#    SUPABASE_URL = https://xxxxxxxxxxxx.supabase.co
#    SUPABASE_KEY = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
#
# 5. Trong config.py, thay 2 dòng:
#    from database import load_db, save_db
#    (xóa hoặc comment toàn bộ phần load_db / save_db cũ)
#
# ────────────────────────────────────────────────────────────────────────────

import os
import json
import time
import threading
import requests as _requests

# ── Cấu hình Supabase ────────────────────────────────────────────────────────
SUPABASE_URL = os.getenv("SUPABASE_URL", "")   # bắt buộc
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")   # bắt buộc
TABLE        = "app_data"
ROW_KEY      = "shop_data"   # tất cả data lưu vào 1 row với key này

# ── Fallback: đường dẫn file JSON local (dùng khi Supabase chưa cấu hình) ──
_BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_FILE  = os.path.join(_BASE_DIR, "data.json")

# ── Lock để tránh ghi đồng thời ─────────────────────────────────────────────
DB_LOCK = threading.Lock()

# ── Cache in-memory để giảm số lần gọi API ──────────────────────────────────
_cache      = None
_cache_time = 0
CACHE_TTL   = 5   # giây - reload từ Supabase sau 5 giây

# ── Kiểm tra có Supabase không ───────────────────────────────────────────────
def _has_supabase() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)

# ── Headers cho Supabase REST API ────────────────────────────────────────────
def _headers() -> dict:
    # Ho tro ca key moi (sb_secret_) lan key cu (eyJ...)
    return {
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "return=minimal",
        "X-Client-Info": "supabase-py/2.0",
    }

# ── Giá trị mặc định khi DB trống ────────────────────────────────────────────
def _default_db() -> dict:
    return {
        "shop_keys":            [],
        "users":                {},
        "active":               {},
        "blocked_web_login":    [],
        "transactions":         [],
        "blocked_telegram_ids": [],
        "cau_history":          {},
    }

# ─────────────────────────────────────────────────────────────────────────────
# SUPABASE: đọc / ghi
# ─────────────────────────────────────────────────────────────────────────────

def _supabase_load() -> dict | None:
    """Đọc data từ Supabase. Trả về dict hoặc None nếu lỗi."""
    try:
        url = f"{SUPABASE_URL}/rest/v1/{TABLE}?key=eq.{ROW_KEY}&select=value"
        r = _requests.get(url, headers=_headers(), timeout=8)
        if r.status_code == 200:
            rows = r.json()
            if rows:
                return rows[0]["value"]
            # Row chưa tồn tại → tạo mới
            default = _default_db()
            _supabase_save(default)
            return default
        print(f"[DB] Supabase load lỗi {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"[DB] Supabase load exception: {e}")
    return None


def _supabase_save(data: dict) -> bool:
    """Ghi data lên Supabase (upsert). Trả về True nếu thành công."""
    try:
        url     = f"{SUPABASE_URL}/rest/v1/{TABLE}"
        payload = {"key": ROW_KEY, "value": data, "updated_at": "now()"}
        headers = _headers()
        headers["Prefer"] = "resolution=merge-duplicates"
        r = _requests.post(url, headers=headers, json=payload, timeout=8)
        if r.status_code in (200, 201, 204):
            return True
        print(f"[DB] Supabase save lỗi {r.status_code}: {r.text[:200]}")
    except Exception as e:
        print(f"[DB] Supabase save exception: {e}")
    return False

# ─────────────────────────────────────────────────────────────────────────────
# FILE JSON LOCAL: đọc / ghi (fallback)
# ─────────────────────────────────────────────────────────────────────────────

def _file_load() -> dict:
    default = _default_db()
    if not os.path.exists(DATA_FILE):
        _file_save(default)
        return default
    try:
        with open(DATA_FILE, encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            raise ValueError("Dữ liệu hỏng")
        for k, v in default.items():
            if k not in data:
                data[k] = v
        return data
    except Exception as e:
        print(f"[DB] Lỗi đọc file local: {e} → tạo lại")
        try:
            os.rename(DATA_FILE, f"{DATA_FILE}.bak.{int(time.time())}")
        except:
            pass
        _file_save(default)
        return default


def _file_save(data: dict):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[DB] Lỗi ghi file local: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# PUBLIC API: load_db() / save_db()  ← dùng trong toàn bộ project
# ─────────────────────────────────────────────────────────────────────────────

def load_db() -> dict:
    """
    Tải database.
    - Nếu Supabase đã cấu hình → đọc từ Supabase (có cache 5 giây)
    - Nếu chưa → đọc từ file JSON local
    """
    global _cache, _cache_time

    with DB_LOCK:
        # Dùng Supabase
        if _has_supabase():
            now = time.time()
            if _cache and (now - _cache_time) < CACHE_TTL:
                return _cache   # trả cache

            data = _supabase_load()
            if data is not None:
                _cache      = data
                _cache_time = now
                # Đồng thời ghi ra file local để backup
                _file_save(data)
                return data

            # Supabase lỗi → fallback file local
            print("[DB] ⚠️ Supabase không phản hồi, dùng file local tạm thời")
            return _file_load()

        # Chưa có Supabase → dùng file
        return _file_load()


def save_db(data: dict):
    """
    Lưu database.
    - Nếu Supabase đã cấu hình → ghi lên Supabase + cập nhật cache + backup file
    - Nếu chưa → ghi file JSON local
    """
    global _cache, _cache_time

    with DB_LOCK:
        if _has_supabase():
            ok = _supabase_save(data)
            if ok:
                _cache      = data
                _cache_time = time.time()
                _file_save(data)   # backup
            else:
                # Supabase lỗi → ghi file để không mất data
                print("[DB] ⚠️ Supabase save thất bại, ghi file local")
                _file_save(data)
        else:
            _file_save(data)


def invalidate_cache():
    """Xóa cache để lần sau đọc lại từ Supabase."""
    global _cache, _cache_time
    _cache      = None
    _cache_time = 0


def ping_supabase() -> str:
    """Kiểm tra kết nối Supabase. Trả về chuỗi status."""
    if not _has_supabase():
        return "❌ Chưa cấu hình SUPABASE_URL / SUPABASE_KEY"
    try:
        url = f"{SUPABASE_URL}/rest/v1/{TABLE}?key=eq.{ROW_KEY}&select=key"
        r = _requests.get(url, headers=_headers(), timeout=5)
        if r.status_code == 200:
            return "✅ Supabase kết nối OK"
        return f"⚠️ Supabase trả lỗi {r.status_code}"
    except Exception as e:
        return f"❌ Lỗi kết nối: {e}"

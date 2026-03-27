# -*- coding: utf-8 -*-
# ================== vn_time.py ==================
# Tiện ích thời gian Việt Nam (UTC+7)
# Dùng thay thế time.localtime() / time.strftime() trong toàn bộ project

import time as _time

VN_OFFSET = 7 * 3600  # UTC+7

def vn_time(ts=None):
    """Trả về struct_time theo giờ Việt Nam"""
    if ts is None:
        ts = _time.time()
    return _time.gmtime(ts + VN_OFFSET)

def vn_strftime(fmt, ts=None):
    """Format thời gian theo giờ VN"""
    return _time.strftime(fmt, vn_time(ts))

def vn_now_str():
    """HH:MM:SS DD/MM/YYYY theo giờ VN"""
    return vn_strftime("%H:%M:%S %d/%m/%Y")

def vn_date_str(ts=None):
    """DD/MM/YYYY HH:MM theo giờ VN"""
    return vn_strftime("%d/%m/%Y %H:%M", ts)

def vn_short(ts=None):
    """DD/MM HH:MM theo giờ VN"""
    return vn_strftime("%d/%m %H:%M", ts)

def key_expires_str(expires_at):
    """Hiển thị thời hạn key đẹp theo giờ VN"""
    if expires_at is None:
        return "Vĩnh viễn ♾️"
    remaining = expires_at - _time.time()
    if remaining <= 0:
        return "⛔ Đã hết hạn"
    days    = int(remaining // 86400)
    hours   = int((remaining % 86400) // 3600)
    minutes = int((remaining % 3600) // 60)
    expire_str = vn_strftime("%d/%m/%Y %H:%M", expires_at)
    if days > 0:
        left = f"{days} ngày {hours} giờ"
    elif hours > 0:
        left = f"{hours} giờ {minutes} phút"
    else:
        left = f"{minutes} phút"
    return f"{expire_str} (còn {left})"

# -*- coding: utf-8 -*-
# ================== sepay_webhook.py ==================
# Đặt file này ngang hàng với app.py

import time, json, os, random, string, requests
from config import load_db, save_db, BOT_TOKEN, ADMIN_ID, _BASE_DIR

# ======= CẤU HÌNH NGÂN HÀNG =======
BANK_NAME    = "MBBank"
BANK_ACCOUNT = "29888899996868"
BANK_OWNER   = "NGUYEN HUYNH NHUT QUANG"
WEBHOOK_SECRET = ""  # Không dùng xác thực
# ===================================

PENDING_FILE = os.path.join(_BASE_DIR, "pending_deposits_sepay.json")

def _load():
    if not os.path.exists(PENDING_FILE):
        return {}
    try:
        with open(PENDING_FILE, encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def _save(data):
    with open(PENDING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def create_deposit_order(username: str, amount: int) -> str:
    """Tạo đơn nạp, trả về nội dung CK vd: NAP sang A3K9B"""
    pending = _load()
    now = time.time()
    
    # Chỉ xóa đơn cũ đã HẾT HẠN (>30 phút), giữ lại đơn chưa hết hạn
    # để user reset web vẫn dùng được mã cũ
    expired = [k for k, v in pending.items() 
               if v.get("username") == username and now - v.get("created_at", 0) > 1800]
    for k in expired:
        del pending[k]
    
    # Nếu user đã có đơn chưa hết hạn → trả lại mã cũ, không tạo mới
    for k, v in pending.items():
        if v.get("username") == username and now - v.get("created_at", 0) <= 1800:
            # Cập nhật amount nếu khác
            if v.get("amount") != amount:
                v["amount"] = amount
                _save(pending)
            return k
    
    rand    = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    content = f"NAP {username} {rand}"
    pending[content] = {
        "username": username, 
        "amount": amount, 
        "created_at": time.time(),
        "code": rand
    }
    _save(pending)
    return content

def process_sepay_webhook(payload: dict) -> dict:
    """
    Gọi khi SePay POST về /api/sepay-webhook
    payload mẫu:
    {
      "id": 12345,
      "transferType": "in",
      "transferAmount": 50000,
      "content": "NAP sang A3K9B",
      "gateway": "MBBank",
      "accountNumber": "0886027767",
      "transactionDate": "2024-01-15 10:30:00"
    }
    """
    # Chỉ nhận tiền VÀO
    if payload.get("transferType") != "in":
        return {"success": True, "message": "ignored"}

    # Fix lỗi số tiền dạng string hoặc float (vd: "10000.00")
    try:
        amount = int(float(str(payload.get("transferAmount", 0))))
    except:
        amount = 0
        
    content  = (payload.get("content") or payload.get("description") or "").strip()
    txn_id   = str(payload.get("id", ""))
    gateway  = payload.get("gateway", "")
    acct     = payload.get("accountNumber", "")
    txn_date = payload.get("transactionDate", "")

    print(f"\n[SEPAY DEBUG] Nhận Webhook: {amount:,}đ | Content: {content} | ID: {txn_id}")

    if not content or amount <= 0:
        print("[SEPAY DEBUG] ❌ Lỗi: Thiếu nội dung hoặc số tiền <= 0")
        return {"success": False, "message": "missing content or amount"}

    # Dọn đơn hết hạn (15 phút)
    pending = _load()
    now     = time.time()
    expired = [k for k, v in pending.items() if now - v.get("created_at", 0) > 1800]
    for k in expired:
        del pending[k]
    if expired:
        _save(pending)

    # Tìm đơn khớp nội dung CK
    matched_key = matched_order = None
    for key, order in pending.items():
        # Cách 1: Khớp cả cụm (NAP user code)
        if key.upper() in content.upper():
            matched_key, matched_order = key, order
            break
        
        # Cách 2: Khớp mã code riêng lẻ (phòng trường hợp user quên ghi NAP)
        code = order.get("code")
        if not code: # Fallback cho data cũ
            parts = key.split()
            if parts: code = parts[-1]
        
        if code and len(code) >= 5 and code.upper() in content.upper():
            matched_key, matched_order = key, order
            break

    if not matched_order:
        print(f"[SEPAY DEBUG] ❌ Không tìm thấy đơn khớp với nội dung: {content}")
        print(f"              👉 Danh sách đơn chờ: {list(pending.keys())}")
        _notify(f"⚠️ NHẬN {amount:,}đ - KHÔNG KHỚP ĐƠN\n📝 {content}\n🏦 {gateway} | {acct}")
        return {"success": True, "message": "no matching order"}

    username = matched_order["username"]

    # Chống xử lý trùng
    db       = load_db()
    done_ids = [t.get("sepay_txn_id") for t in db.get("transactions", []) if t.get("sepay_txn_id")]
    if txn_id and txn_id in done_ids:
        print(f"[SEPAY DEBUG] ⚠️ Giao dịch {txn_id} đã được xử lý trước đó. Bỏ qua.")
        return {"success": True, "message": "already processed"}

    if username not in db["users"]:
        print(f"[SEPAY DEBUG] ❌ User {username} không tồn tại trong DB")
        return {"success": False, "message": f"user {username} not found"}

    # Cộng tiền
    db["users"][username]["balance"] = db["users"][username].get("balance", 0) + amount
    db.setdefault("transactions", []).append({
        "type": "deposit", "username": username, "amount": amount,
        "time": time.time(), "status": "completed", "method": "sepay_auto",
        "transfer_content": content, "sepay_txn_id": txn_id
    })
    save_db(db)

    # Xóa đơn đã xử lý
    del pending[matched_key]
    _save(pending)

    new_balance = db["users"][username]["balance"]

    # Thông báo admin
    _notify(
        f"✅ NẠP TIỀN TỰ ĐỘNG\n\n"
        f"👤 Tài khoản: {username}\n"
        f"💰 +{amount:,}đ\n"
        f"💎 Số dư mới: {new_balance:,}đ\n"
        f"🏦 {gateway} | {acct}\n"
        f"📝 {content}\n"
        f"🔖 TxnID: {txn_id} | {txn_date}"
    )

    # Thông báo user qua Telegram (nếu có telegram_id lưu trong DB)
    db2 = load_db()
    user_tele_id = db2["users"].get(username, {}).get("telegram_id")
    if user_tele_id:
        _send_tele(user_tele_id,
            f"🎉 NẠP TIỀN THÀNH CÔNG!\n\n"
            f"💰 Số tiền: +{amount:,}đ\n"
            f"💎 Số dư mới: {new_balance:,}đ\n"
            f"🕐 {txn_date}\n\n"
            f"Cảm ơn bạn đã sử dụng SHOP MINHSANG! 🙏"
        )
    print(f"[SEPAY] ✅ {username} +{amount:,}đ | TxnID={txn_id}")
    print(f"[SEPAY DEBUG] ✅ ĐÃ CỘNG TIỀN: {username} +{amount:,}đ | Số dư mới: {new_balance:,}đ")
    return {"success": True, "message": f"deposited {amount} for {username}"}


def _send_tele(chat_id, text: str):
    """Gửi tin nhắn Telegram cho user"""
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text},
            timeout=5
        )
    except Exception as e:
        print(f"[SEPAY] Lỗi gửi Telegram user: {e}")

def _notify(text: str):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": ADMIN_ID, "text": text},
            timeout=5
        )
    except Exception as e:
        print(f"[SEPAY] Lỗi Telegram: {e}")

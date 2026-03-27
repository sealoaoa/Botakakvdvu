# -*- coding: utf-8 -*-
# ================== telegram_bot.py ==================
# Telegram Bot - tất cả handlers và lệnh

import os, json, time, asyncio, threading
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vn_time import vn_now_str, vn_date_str, vn_short, key_expires_str
from datetime import datetime
from config import BOT_TOKEN, ADMIN_ID, SHOP_NAME, load_db, save_db, create_key, get_vip_level, VIP_LEVELS, pending_deposits
import config
from algorithms import safe_json, normalize, API_SUN, API_HIT, API_B52A, API_B52B, API_LUCK8, API_SICBO, API_789, API_68GB, API_LC79, API_SUM
from predict import PREDICTION_HISTORY

try:
    from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
    from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

async def log_all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"[DEBUG] log_all_messages được gọi!")
    if update.message:
        user = update.effective_user
        msg_text = update.message.text or "[No text]"
        print(
            f"📨 Message từ {user.username or user.first_name} (ID: {user.id}): {msg_text}"
        )

        # Check if user is banned from Telegram bot
        db = load_db()
        if user.id in db.get("blocked_telegram_ids", []):
            await update.message.reply_text(
                "⛔ Tài khoản của bạn đã bị chặn bot.")
            return

        if msg_text and "TÔI ĐÃ CHUYỂN KHOẢN" in msg_text.upper():
            user_id = user.id
            user_telegram = user.username or user.first_name
            user_fullname = user.first_name + (f" {user.last_name}"
                                               if user.last_name else "")

            found_deposit = None
            deposit_key_to_remove = None
            for deposit_id, deposit in pending_deposits.items():
                if deposit["user_id"] == user_id:
                    found_deposit = deposit
                    deposit_key_to_remove = deposit_id
                    break

            if found_deposit:
                admin_msg = (
                    f"✅ XÁC NHẬN CHUYỂN KHOẢN (Telegram)\n\n"
                    f"👤 Tên: {user_fullname}\n"
                    f"📱 Telegram: @{user_telegram} (ID: {user_id})\n"
                    f"🎮 Tài khoản: {found_deposit['username']}\n"
                    f"💵 Số tiền: {found_deposit['amount']:,}đ\n\n"
                    f"💬 User đã xác nhận chuyển khoản!\n\n"
                    f"Duyệt: /duyet {found_deposit['username']}")

                try:
                    await context.bot.send_message(chat_id=ADMIN_ID,
                                                   text=admin_msg)
                    await update.message.reply_text(
                        f"✅ Đã nhận xác nhận!\n\n"
                        f"📱 Admin sẽ kiểm tra và duyệt nạp tiền cho bạn trong giây lát.\n\n"
                        f"⏳ Vui lòng đợi...")
                    # Remove the deposit after confirmation to avoid duplicate processing
                    if deposit_key_to_remove:
                        del pending_deposits[deposit_key_to_remove]
                except Exception as e:
                    print(f"Lỗi gửi thông báo admin: {e}")
            else:
                await update.message.reply_text(
                    f"❌ Không tìm thấy yêu cầu nạp tiền!\n\n"
                    f"Vui lòng gửi lệnh /nap trước khi xác nhận chuyển khoản.")
        else:
            # Trả lời cho tất cả tin nhắn khác
            await update.message.reply_text(
                "👋 Xin chào! Tôi là bot của SHOP MINHSANG.\n\n"
                "📋 Để xem các lệnh, gửi /help\n"
                "🎰 Để nạp tiền, gửi /nap <username> <số_tiền>")
    elif update.edited_message:
        print(f"✏️ Edited message received")
    else:
        print(f"📥 Update received: {update}")


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id  = update.effective_user.id
        tg_name  = update.effective_user.username or update.effective_user.first_name
        fullname = update.effective_user.full_name or tg_name
        print(f"📥 /start từ: {tg_name} (ID: {user_id})")

        now_str = vn_now_str()

        if user_id == ADMIN_ID:
            # ── ADMIN ──────────────────────────────────────────
            msg = (
                f"👑 XIN CHÀO ADMIN!\n"
                f"{'─'*30}\n"
                f"🕐 {now_str}\n\n"
                f"⚙️ QUẢN LÝ KEY\n"
                f"  /key 1d|1t|1thang|vv — Tạo key\n"
                f"  /list — Danh sách key\n"
                f"  /block <code> — Khóa key\n"
                f"  /huykey <code> — Hủy key\n\n"
                f"💰 NẠP TIỀN\n"
                f"  /duyet <user> — Duyệt nạp\n"
                f"  /doanhthu — Doanh thu\n\n"
                f"👤 QUẢN LÝ USER\n"
                f"  /tong — Thống kê tổng\n"
                f"  /band <user> — Khóa web\n"
                f"  /xoa <user> — Xóa tài khoản\n\n"
                f"🛡️ BẢO MẬT\n"
                f"  /banip <ip> — Ban IP\n"
                f"  /unbanip <ip> — Gỡ ban IP\n"
                f"  /checkip <ip> — Xem thông tin IP\n"
                f"  /xemtancon — Log tấn công\n\n"
                f"🎮 GAME\n"
                f"  /iframegame <game> <link>\n"
                f"  /xemiframe — Xem link game"
            )
            keyboard = [[
                InlineKeyboardButton("🌐 Truy cập Tool", url="https://toolkiemlaisew.site"),
                InlineKeyboardButton("📊 Thống kê", callback_data="admin_stats")
            ]]
        else:
            # ── USER THƯỜNG ────────────────────────────────────
            # Lấy thông tin key của user (nếu có tài khoản web)
            key_info = ""
            try:
                db = load_db()
                # Tìm user web có cùng telegram username
                for uname, udata in db.get("users", {}).items():
                    active = db["active"].get(uname)
                    if active:
                        exp = active.get("expiresAt")
                        if exp is None or exp > time.time():
                            key_info = f"\n✅ Key đang active: {key_expires_str(exp)}"
                            break
            except Exception:
                pass

            msg = (
                f"╔══════════════════════════╗\n"
                f"║   🤖 TOOL AI KIẾM LÃI   ║\n"
                f"╚══════════════════════════╝\n\n"
                f"👋 Xin chào, {fullname}!\n"
                f"🕐 {now_str}\n"
                f"{key_info}\n\n"
                f"🎯 VỀ TOOL\n"
                f"  • AI dự đoán Tài/Xỉu chính xác cao\n"
                f"  • Hỗ trợ: SunWin, HitClub, B52, Luck8\n"
                f"            789Club, 68GB, LC79, Sexy\n"
                f"  • Cập nhật kết quả real-time\n\n"
                f"💎 BẢNG GIÁ KEY\n"
                f"  🥉 1 ngày  —  liên hệ admin\n"
                f"  🥈 1 tuần  —  liên hệ admin\n"
                f"  🥇 1 tháng —  liên hệ admin\n"
                f"  👑 Vĩnh viễn — liên hệ admin\n\n"
                f"📌 HƯỚNG DẪN\n"
                f"  1️⃣ Đăng ký tài khoản trên web\n"
                f"  2️⃣ Nạp tiền → mua key\n"
                f"  3️⃣ Vào game → tool tự dự đoán\n\n"
                f"💬 Hỗ trợ: @sewdangcap"
            )
            keyboard = [[
                InlineKeyboardButton("🌐 Vào Tool ngay", url="https://toolkiemlaisew.site"),
                InlineKeyboardButton("💬 Liên hệ Admin", url="https://t.me/sewdangcap")
            ],[
                InlineKeyboardButton("💰 Nạp tiền", url="https://toolkiemlaisew.site/deposit"),
                InlineKeyboardButton("🔑 Mua Key", url="https://toolkiemlaisew.site/buy-key")
            ]]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(msg, reply_markup=reply_markup)
        print(f"OK /start → {tg_name}")
    except Exception as e:
        print(f"ERROR cmd_start: {e}")
        import traceback
        traceback.print_exc()


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        await update.message.reply_text(
            "📖 LỆNH ADMIN:\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💰 NẠP TIỀN & KEY:\n"
            "/nap <user> <tiền> - Tạo lệnh nạp\n"
            "/duyet <user> - Duyệt nạp tiền\n"
            "/key <1d|1t|1thang|vv> - Tạo key\n"
            "/list - Danh sách key\n"
            "/huykey <code> - Hủy key\n"
            "/block <code> - Khóa key\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "🎮 IFRAME GAME:\n"
            "/iframegame <game> <link>\n"
            "   Đổi link iframe game\n"
            "   Ví dụ: /iframegame sun https://web.sunwin.ag\n"
            "/xemiframe - Xem link iframe hiện tại\n\n"
            "   Game: sun | hit | b52 | luck8\n"
            "         sicbo | 789 | 68gb | lc79 | sexy\n\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👤 QUẢN LÝ USER:\n"
            "/tong - Thống kê tổng quan\n"
            "/doanhthu - Xem doanh thu\n"
            "/band <user> - Khóa web login\n"
            "/unband <user> - Mở khóa web\n"
            "/ban_tg <id> - Chặn Telegram\n"
            "/unban_tg <id> - Bỏ chặn Telegram\n"
            "/xoa <user> - Xóa tài khoản\n"
            "/lichsu <game> - Lịch sử dự đoán\n"
            "/xuatdata - Xuất toàn bộ data")
    else:
        await update.message.reply_text(
            "📖 HƯỚNG DẪN SỬ DỤNG:\n\n"
            "1️⃣ Gửi lệnh nạp tiền:\n   /nap <tên_tài_khoản> <số_tiền>\n   Ví dụ: /nap Minhsang 100000\n\n"
            "2️⃣ Chuyển khoản theo thông tin:\n   - Ngân hàng: MB Bank\n   - STK: 0886027767\n   - Tên: TRAN MINH SANG\n   - Nội dung: NAP <tên_tài_khoản>\n\n"
            "3️⃣ Sau khi chuyển khoản xong, nhắn:\n   TÔI ĐÃ CHUYỂN KHOẢN\n\n"
            "4️⃣ Admin sẽ duyệt và cộng tiền\n\n"
            "💬 Hỗ trợ: @minhsangdangcap")


async def callback_approve_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý khi admin click button duyệt nạp tiền"""
    query = update.callback_query
    print(f"[DEBUG] callback_approve_deposit được gọi! callback_data: {query.data}")
    
    # Kiểm tra xem người click có phải admin không
    print(f"[DEBUG] User ID: {query.from_user.id}, ADMIN_ID: {ADMIN_ID}")
    if query.from_user.id != ADMIN_ID:
        print(f"[DEBUG] ❌ User không phải admin!")
        await query.answer("❌ Bạn không có quyền duyệt!", show_alert=True)
        return
    
    # Lấy short_id từ callback_data
    short_id = query.data.replace("approve_", "")
    print(f"[DEBUG] short_id: {short_id}")
    print(f"[DEBUG] pending_deposits keys: {list(pending_deposits.keys())}")
    
    if short_id not in pending_deposits:
        print(f"[DEBUG] ❌ short_id không tìm thấy!")
        await query.answer("❌ Yêu cầu nạp tiền không còn hiệu lực!", show_alert=True)
        return
    
    deposit = pending_deposits[short_id]
    username = deposit["username"]
    amount = deposit["amount"]
    
    print(f"[DEBUG] Duyệt nạp tiền cho {username}: {amount}đ")
    
    # Duyệt nạp tiền
    db = load_db()
    if username not in db["users"]:
        print(f"[DEBUG] ❌ Tài khoản không tồn tại!")
        await query.answer("❌ Tài khoản không tồn tại!", show_alert=True)
        return
    
    # Cộng tiền cho user
    db["users"][username]["balance"] = db["users"][username].get("balance", 0) + amount
    print(f"[DEBUG] ✅ Đã cộng tiền. Số dư mới: {db['users'][username]['balance']}")
    
    # Ghi lại giao dịch
    transaction = {
        "username": username,
        "type": "deposit",
        "amount": amount,
        "time": time.time(),
        "method": "telegram_admin"
    }
    db["transactions"].append(transaction)
    save_db(db)
    
    # Cập nhật UI
    await query.answer(f"✅ Đã duyệt nạp {amount:,}đ cho {username}!", show_alert=True)
    
    # Sửa tin nhắn để hiển thị trạng thái đã duyệt
    await query.edit_message_text(
        f"✅ XÁC NHẬN CHUYỂN KHOẢN (Telegram)\n\n"
        f"🎮 Tài khoản: {username}\n"
        f"💵 Số tiền: {amount:,}đ\n\n"
        f"✅ ĐƠNHÀNG ĐÃ ĐƯỢC DUYỆT!")
    
    # Xóa yêu cầu nạp sau khi duyệt
    del pending_deposits[short_id]
    print(f"[DEBUG] ✅ Đã xóa pending_deposits[{short_id}]")



async def callback_confirm_transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xử lý khi user click button xác nhận chuyển khoản"""
    query = update.callback_query
    print(f"[DEBUG] callback_confirm_transfer được gọi! callback_data: {query.data}")
    await query.answer()
    
    # Lấy deposit_id từ callback_data
    deposit_id = query.data.replace("confirm_transfer_", "")
    print(f"[DEBUG] deposit_id: {deposit_id}")
    print(f"[DEBUG] pending_deposits keys: {list(pending_deposits.keys())}")
    
    if deposit_id not in pending_deposits:
        print(f"[DEBUG] ❌ deposit_id không tìm thấy trong pending_deposits!")
        await query.edit_message_text("❌ Yêu cầu nạp tiền không còn hiệu lực!")
        return
    
    deposit = pending_deposits[deposit_id]
    user_id = deposit["user_id"]
    user_telegram = deposit["user_telegram"]
    user_fullname = deposit["user_fullname"]
    username = deposit["username"]
    amount = deposit["amount"]
    
    print(f"[DEBUG] Gửi message cho admin. ADMIN_ID: {ADMIN_ID}")
    
    # Gửi thông báo admin kèm button duyệt
    admin_msg = (
        f"✅ XÁC NHẬN CHUYỂN KHOẢN (Telegram)\n\n"
        f"👤 Tên: {user_fullname}\n"
        f"📱 Telegram: @{user_telegram} (ID: {user_id})\n"
        f"🎮 Tài khoản: {username}\n"
        f"💵 Số tiền: {amount:,}đ\n\n"
        f"💬 User đã xác nhận chuyển khoản!")
    
    # Tạo short ID để avoid callback_data quá dài (Telegram limit 64 bytes)
    config.deposit_counter += 1
    short_id = f"d{config.deposit_counter}"
    pending_deposits[short_id] = deposit
    # Xóa cái deposit_id cũ để tránh duplicate
    del pending_deposits[deposit_id]
    print(f"[DEBUG] Tạo short_id {short_id} từ {deposit_id}")
    
    print(f"[DEBUG] Tạo button với callback_data: approve_{short_id}")
    admin_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Duyệt nạp tiền", callback_data=f"approve_{short_id}")]
    ])
    
    try:
        print(f"[DEBUG] Đang gửi message tới admin...")
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, reply_markup=admin_keyboard)
        print(f"[DEBUG] ✅ Message gửi thành công!")
        
        await query.edit_message_text(
            f"✅ Đã nhận xác nhận!\n\n"
            f"📱 Admin sẽ kiểm tra và duyệt nạp tiền cho bạn trong giây lát.\n\n"
            f"⏳ Vui lòng đợi...")
        # Không xóa pending_deposits ở đây - chỉ xóa sau khi admin duyệt
    except Exception as e:
        print(f"[ERROR] Lỗi gửi message: {e}")
        import traceback
        traceback.print_exc()
        await query.edit_message_text(f"❌ Lỗi: {str(e)}")


async def cmd_nap(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_telegram = update.effective_user.username or update.effective_user.first_name
    user_fullname = update.effective_user.first_name + (
        f" {update.effective_user.last_name}"
        if update.effective_user.last_name else "")

    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Sai cú pháp!\n\nĐúng: /nap <tên_tài_khoản> <số_tiền>\nVí dụ: /nap Minhsang 100000")
        return

    username = context.args[0]
    try:
        amount = int(context.args[1])
        if amount <= 0:
            raise ValueError()
    except:
        await update.message.reply_text("❌ Số tiền không hợp lệ!")
        return

    db = load_db()
    if username not in db["users"]:
        await update.message.reply_text(
            f"❌ Tài khoản '{username}' không tồn tại!")
        return

    # Check if user is banned from Telegram bot
    if user_id in db.get("blocked_telegram_ids", []):
        await update.message.reply_text(
            "⛔ Tài khoản Telegram của bạn đã bị chặn bot.")
        return

    deposit_id = f"{user_id}_{int(time.time())}"
    pending_deposits[deposit_id] = {
        "user_id": user_id,
        "user_telegram": user_telegram,
        "user_fullname": user_fullname,
        "username": username,
        "amount": amount,
        "time": time.time()
    }

    # Debug log
    print(f"💰 Tạo yêu cầu nạp tiền mới:")
    print(f"  - Deposit ID: {deposit_id}")
    print(f"  - Username: {username}")
    print(f"  - Amount: {amount}")
    print(f"  - Pending deposits: {len(pending_deposits)} yêu cầu")

    admin_msg = (f"💰 YÊU CẦU NẠP TIỀN MỚI (Telegram)\n\n"
                 f"👤 Tên: {user_fullname}\n"
                 f"📱 Telegram: @{user_telegram} (ID: {user_id})\n"
                 f"🎮 Tài khoản game: {username}\n"
                 f"💵 Số tiền: {amount:,}đ\n"
                 f"🔑 ID: {deposit_id}\n\n"
                 f"⏳ Đang chờ user chuyển khoản...\n\n"
                 f"Duyệt: /duyet {username}")

    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=admin_msg)
        
        # Gửi thông tin và button xác nhận cho user
        msg = (f"✅ Đã gửi yêu cầu nạp tiền!\n\n"
               f"👤 Tài khoản: {username}\n"
               f"💵 Số tiền: {amount:,}đ\n\n"
               f"📋 THÔNG TIN CHUYỂN KHOẢN:\n"
               f"🏦 Ngân hàng: MB Bank\n"
               f"💳 STK: 0886027767\n"
               f"👤 Tên: TRAN MINH SANG\n"
               f"📝 Nội dung: NAP {username}\n\n"
               f"⏳ Sau khi chuyển khoản, bấm nút bên dưới:")
        
        # Tạo inline keyboard button
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Xác nhận đã chuyển khoản", callback_data=f"confirm_transfer_{deposit_id}")]
        ])
        
        await update.message.reply_text(msg, reply_markup=keyboard)
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi gửi thông báo: {str(e)}")


async def cmd_duyet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này"
                                        )
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Sai cú pháp!\n\nĐúng: /duyet <tên_tài_khoản>\nVí dụ: /duyet Minhsang")
        return

    username = context.args[0]
    found_deposit = None
    deposit_key = None

    # Debug: Show all pending deposits
    print(f"🔍 Tìm kiếm nạp tiền cho username: {username}")
    print(f"📋 Pending deposits hiện tại: {pending_deposits}")

    for key, deposit in pending_deposits.items():
        print(f"  - Checking: {deposit.get('username')} == {username}?")
        if deposit.get("username", "").lower() == username.lower():
            if found_deposit is None or deposit["time"] > found_deposit["time"]:
                found_deposit = deposit
                deposit_key = key
                print(f"  ✅ Found match!")

    if not found_deposit:
        # Show helpful error message
        pending_users = [
            d.get("username", "N/A") for d in pending_deposits.values()
        ]
        msg = f"❌ Không tìm thấy yêu cầu nạp tiền cho tài khoản '{username}'\n\n"
        if pending_users:
            msg += f"📋 Các yêu cầu đang chờ:\n" + "\n".join(
                [f"  • {u}" for u in pending_users])
        else:
            msg += "📋 Hiện không có yêu cầu nạp tiền nào đang chờ duyệt"
        await update.message.reply_text(msg)
        return

    db = load_db()
    if username not in db["users"]:
        await update.message.reply_text(
            f"❌ Tài khoản '{username}' không tồn tại!")
        return

    db["users"][username]["balance"] = db["users"][username].get(
        "balance", 0) + found_deposit["amount"]
    save_db(db)

    # Lưu lịch sử giao dịch
    if "transactions" not in db:
        db["transactions"] = []

    transaction = {
        "type": "deposit",
        "username": username,
        "amount": found_deposit['amount'],
        "time": time.time(),
        "status": "completed"
    }
    db["transactions"].append(transaction)
    save_db(db)

    # Remove the deposit from pending list after successful processing
    if deposit_key:
        del pending_deposits[deposit_key]

    # Format ngày giờ hiện tại
    now = datetime.now()
    ngay_gio = now.strftime("%d/%m/%Y %H:%M:%S")

    await update.message.reply_text(
        f"✅ ĐƠN DUYỆT TK{username.upper()} THÀNH CÔNG\n\n"
        f"💰 Số tiền: {found_deposit['amount']:,}đ\n"
        f"🕐 Ngày giờ: {ngay_gio}\n\n"
        f"📊 Chi tiết:\n"
        f"👤 Tên: {found_deposit.get('user_fullname', 'N/A')}\n"
        f"📱 Telegram: @{found_deposit['user_telegram']}\n"
        f"💵 Số dư mới: {db['users'][username]['balance']:,}đ")

    try:
        user_msg = (
            f"✅ NẠP TIỀN THÀNH CÔNG!\n\n"
            f"💵 Số tiền đã nạp: {found_deposit['amount']:,}đ\n"
            f"💰 Số dư hiện tại: {db['users'][username]['balance']:,}đ\n\n"
            f"🎉 Cảm ơn bạn đã sử dụng dịch vụ!")
        await context.bot.send_message(chat_id=found_deposit["user_id"],
                                       text=user_msg)
    except Exception as e:
        print(f"Không thể gửi thông báo cho user: {e}")


async def cmd_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này")
        return
    await update.message.reply_text(
        "📋 Menu Admin:\n\n"
        "/key 1d - Tạo key 1 ngày\n"
        "/key 1t - Tạo key 1 tháng\n"
        "/key vv - Tạo key vĩnh viễn\n"
        "/list - Xem tất cả key\n"
        "/block <key> - Khóa key\n"
        "/duyet <username> - Duyệt nạp tiền\n"
        "/band <username> - Khóa đăng nhập web\n"
        "/unband <username> - Mở khóa đăng nhập web\n"
        "/ban_tg <user_id> - Chặn user Telegram\n"
        "/unban_tg <user_id> - Bỏ chặn user Telegram\n"
        "/xoa <username> - Xóa tài khoản user\n"
        "/doanhthu - Thống kê doanh thu mua key\n"
        "/tong - Thống kê tổng quan hệ thống\n"
        "/lichsu <game> - Lịch sử dự đoán từng game")


async def cmd_key(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text(
            "⛔ BẠN KHÔNG CÓ QUYỀN TẠO KEY!\n\n"
            f"❌ Chỉ admin (ID: {ADMIN_ID}) mới có thể tạo key.\n"
            f"📱 ID của bạn: {user_id}\n\n"
            "💬 Liên hệ admin để được hỗ trợ.")
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Thiếu tham số\nVí dụ: /key 1d, /key 1t, /key vv")
        return

    arg = context.args[0].lower()  # Convert to lowercase for easier comparison
    days = None
    key_type_str = ""

    if arg.endswith("d"):
        try:
            days = int(arg[:-1])
            key_type_str = f"{days}d"
        except ValueError:
            await update.message.reply_text("❌ Định dạng số ngày không hợp lệ.")
            return
    elif arg.endswith("t"):
        try:
            months = int(arg[:-1])
            days = months * 30  # Approximate months to days
            key_type_str = f"{months}t"
        except ValueError:
            await update.message.reply_text(
                "❌ Định dạng số tháng không hợp lệ.")
            return
    elif arg == "vv":
        days = None
        key_type_str = "vv"
    else:
        await update.message.reply_text(
            "❌ Tham số không hợp lệ\nVí dụ: /key 1d, /key 1t, /key vv")
        return

    k = create_key("LK", days)
    db = load_db()
    db["shop_keys"].append(k)
    save_db(db)

    expires_str = "Vĩnh viễn" if days is None else f"{days} ngày"
    key_code = k['code']

    # Gửi thông báo với key có thể copy
    await update.message.reply_text(
        f"✅ KEY ĐÃ ĐƯỢC TẠO THÀNH CÔNG!\n\n"
        f"👑 Tạo bởi: Admin (ID: {ADMIN_ID})\n"
        f"🔑 Code: `{key_code}`\n"
        f"⏰ Thời hạn: {expires_str}\n\n"
        f"📋 Nhấn vào mã key bên trên để sao chép\n"
        f"💬 Hoặc copy thủ công: {key_code}",
        parse_mode='Markdown')


async def cmd_huykey(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text(
            "⛔ BẠN KHÔNG CÓ QUYỀN KHÓA KEY!\n\n"
            f"❌ Chỉ admin (ID: {ADMIN_ID}) mới có thể khóa key.\n"
            f"📱 ID của bạn: {user_id}\n\n"
            "💬 Liên hệ admin để được hỗ trợ.")
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Thiếu tham số\nVí dụ: /huykey LK-ABC123XY")
        return

    key_code = context.args[0].upper()
    db = load_db()

    # Tìm key
    key_found = None
    for k in db["shop_keys"]:
        if k["code"].upper() == key_code:
            key_found = k
            break

    if not key_found:
        await update.message.reply_text(
            f"❌ Key '{key_code}' không tồn tại!")
        return

    if key_found["status"] == "blocked":
        await update.message.reply_text(
            f"⚠️ Key '{key_code}' đã bị khóa từ trước!")
        return

    # Khóa key
    key_found["status"] = "blocked"
    save_db(db)

    # Nếu key đang được sử dụng, cấm đăng nhập user
    if key_found.get("usedBy"):
        username = key_found["usedBy"]
        if username not in db["blocked_web_login"]:
            db["blocked_web_login"].append(username)
            save_db(db)
        blocked_msg = f"\n🚫 Đã chặn đăng nhập tài khoản '{username}' trên web"
    else:
        blocked_msg = ""

    await update.message.reply_text(
        f"✅ KEY ĐÃ ĐƯỢC KHÓA THÀNH CÔNG!\n\n"
        f"🔑 Code: `{key_code}`\n"
        f"📊 Trạng thái cũ: {key_found.get('status', 'N/A')}\n"
        f"❌ Trạng thái mới: blocked\n"
        f"👤 Được sử dụng bởi: {key_found.get('usedBy', 'Chưa sử dụng')}{blocked_msg}",
        parse_mode='Markdown')


async def cmd_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này"
                                        )
        return

    db = load_db()
    if not db["shop_keys"]:
        await update.message.reply_text("📋 Chưa có key nào được tạo")
        return

    msg = "📋 DANH SÁCH KEY:\n\n"
    for idx, k in enumerate(db["shop_keys"], 1):
        # Icon trạng thái gọn
        if k["status"] == "blocked":
            status_icon = "🔴"
        elif k["status"] == "available":
            status_icon = "🟢"
        else:
            status_icon = "🟡"

        # Hết hạn gọn
        if k["status"] == "available" and k.get("duration_days") is not None:
            exp = f"{k['duration_days']} ngày"
        elif k.get("expiresAt") is None:
            if k.get("duration_days") is None:
                exp = "♾️"
            else:
                exp = f"{k['duration_days']} ngày"
        else:
            exp = vn_short(k.get("expiresAt"))

        # User gọn
        used_by = k.get("usedBy", "-")

        # Format 1 dòng gọn
        msg += f"{idx}. {status_icon} {k['code']} | {exp} | {used_by}\n"

    msg += f"\n💡 Tổng: {len(db['shop_keys'])} key"
    await update.message.reply_text(msg)


async def cmd_block(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này"
                                        )
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Sai cú pháp!\n\nĐúng: /block <key_code>\nVí dụ: /block LK-ABC123")
        return

    key_code = context.args[0]
    db = load_db()
    found = None

    for k in db["shop_keys"]:
        if k["code"] == key_code:
            found = k
            break

    if not found:
        await update.message.reply_text(f"❌ Không tìm thấy key '{key_code}'")
        return

    if found["status"] == "blocked":
        await update.message.reply_text(
            f"⚠️ Key '{key_code}' đã bị khóa từ trước!")
        return

    found["status"] = "blocked"

    # Xóa key khỏi active để user phải nhập lại key
    username_to_remove = found.get("usedBy")
    if username_to_remove and username_to_remove in db["active"]:
        if db["active"][username_to_remove]["code"] == key_code:
            del db["active"][username_to_remove]

    save_db(db)

    msg = f"✅ Đã khóa key '{key_code}' thành công!"
    if username_to_remove:
        msg += f"\n\n👤 User '{username_to_remove}' sẽ phải nhập lại key khi vào game."

    await update.message.reply_text(msg)


async def cmd_band(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này"
                                        )
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Sai cú pháp!\n\nĐúng: /band <username>\nVí dụ: /band Minhsang")
        return

    username_to_block = context.args[0]
    db = load_db()

    if "blocked_web_login" not in db:
        db["blocked_web_login"] = []

    if username_to_block in db["blocked_web_login"]:
        await update.message.reply_text(
            f"⚠️ Tài khoản '{username_to_block}' đã bị khóa đăng nhập web từ trước."
        )
        return

    db["blocked_web_login"].append(username_to_block)
    save_db(db)

    await update.message.reply_text(
        f"✅ Đã khóa tài khoản '{username_to_block}' khỏi đăng nhập web.")


async def cmd_unband(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này"
                                        )
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Sai cú pháp!\n\nĐúng: /unband <username>\nVí dụ: /unband Minhsang")
        return

    username_to_unblock = context.args[0]
    db = load_db()

    if "blocked_web_login" not in db or username_to_unblock not in db[
            "blocked_web_login"]:
        await update.message.reply_text(
            f"❌ Tài khoản '{username_to_unblock}' không bị khóa đăng nhập web."
        )
        return

    db["blocked_web_login"].remove(username_to_unblock)
    save_db(db)

    await update.message.reply_text(
        f"✅ Đã mở khóa tài khoản '{username_to_unblock}' khỏi đăng nhập web.")


async def cmd_ban_tg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này"
                                        )
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Sai cú pháp!\n\nĐúng: /ban_tg <user_id>\nVí dụ: /ban_tg 123456789")
        return

    try:
        user_id_to_ban = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ User ID không hợp lệ.")
        return

    db = load_db()
    if "blocked_telegram_ids" not in db:
        db["blocked_telegram_ids"] = []

    if user_id_to_ban in db["blocked_telegram_ids"]:
        await update.message.reply_text(
            f"⚠️ User ID {user_id_to_ban} đã bị chặn bot từ trước.")
        return

    db["blocked_telegram_ids"].append(user_id_to_ban)
    save_db(db)

    await update.message.reply_text(
        f"✅ Đã chặn User ID {user_id_to_ban} khỏi bot.")


async def cmd_unban_tg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này"
                                        )
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Sai cú pháp!\n\nĐúng: /unban_tg <user_id>\nVí dụ: /unban_tg 123456789")
        return

    try:
        user_id_to_unban = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ User ID không hợp lệ.")
        return

    db = load_db()

    if "blocked_telegram_ids" not in db or user_id_to_unban not in db[
            "blocked_telegram_ids"]:
        await update.message.reply_text(
            f"❌ User ID {user_id_to_unban} không bị chặn bot.")
        return

    db["blocked_telegram_ids"].remove(user_id_to_unban)
    save_db(db)

    await update.message.reply_text(
        f"✅ Đã bỏ chặn User ID {user_id_to_unban} khỏi bot.")


async def cmd_doanhthu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này")
        return

    db = load_db()
    transactions = db.get("transactions", [])

    total_buy_key = sum(t.get("amount", 0) for t in transactions if t.get("type") == "buy_key" and t.get("status") == "completed")
    buy_key_count = sum(1 for t in transactions if t.get("type") == "buy_key" and t.get("status") == "completed")

    msg = (
        f"💰 THỐNG KÊ DOANH THU MUA KEY\n\n"
        f"🔑 Số lượt mua key: {buy_key_count}\n"
        f"💵 Tổng doanh thu: {total_buy_key:,}đ"
    )

    await update.message.reply_text(msg)


async def cmd_tong(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này"
                                        )
        return

    db = load_db()

    # Thống kê users
    total_users = len(db.get("users", {}))
    total_balance = sum(
        user.get("balance", 0) for user in db.get("users", {}).values())

    # Thống kê keys
    total_keys = len(db.get("shop_keys", []))
    active_keys_count = len(
        [k for k in db.get("shop_keys", []) if k.get("status") == "available"])
    used_keys_count = len(
        [k for k in db.get("shop_keys", []) if k.get("status") == "used"])
    blocked_keys_count = len(
        [k for k in db.get("shop_keys", []) if k.get("status") == "blocked"])

    # Thống kê keys đang hoạt động
    active_users_with_keys = len(db.get("active", {}))

    # Thống kê user bị khóa
    blocked_web_users = len(db.get("blocked_web_login", []))
    blocked_tg_users = len(db.get("blocked_telegram_ids", []))

    # Thống kê doanh thu
    transactions = db.get("transactions", [])
    total_deposit = sum(t.get("amount", 0) for t in transactions if t.get("type") == "deposit" and t.get("status") == "completed")
    total_buy_key = sum(t.get("amount", 0) for t in transactions if t.get("type") == "buy_key" and t.get("status") == "completed")

    # Danh sách user và số dư
    user_list = ""
    for idx, (username,
              user_data) in enumerate(db.get("users", {}).items(), 1):
        balance = user_data.get("balance", 0)
        user_id = user_data.get("user_id", "N/A")
        created = time.strftime(
            "%d/%m/%y", time.localtime(user_data.get("created_at",
                                                     time.time())))

        # Kiểm tra key đang hoạt động
        has_active = "🟢" if username in db.get("active", {}) else "⚪"

        # Kiểm tra bị khóa
        is_blocked = "🔴" if username in db.get("blocked_web_login", []) else ""

        # Lấy thông tin key nếu có
        key_info = ""
        if username in db.get("active", {}):
            active_key = db["active"][username]
            if active_key.get("expiresAt") is None:
                key_info = " | ♾️ VV"
            elif active_key.get("expiresAt", 0) > time.time():
                expires = time.strftime(
                    "%d/%m", time.localtime(active_key["expiresAt"]))
                key_info = f" | 🔑 {expires}"

        user_list += f"{idx}. {has_active}{is_blocked} {username}{key_info}\n"
        user_list += f"   💰 {balance:,}đ | 🆔 {user_id} | 📅 {created}\n"

    header = f"""📊 THỐNG KÊ HỆ THỐNG

💰 DOANH THU:
━━━━━━━━━━━━━━━━━━
• Tổng nạp vào: {total_deposit:,}đ
• Tổng mua key: {total_buy_key:,}đ
• Số dư còn lại (users): {total_balance:,}đ

👥 NGƯỜI DÙNG:
━━━━━━━━━━━━━━━━━━
• Tổng số: {total_users} user
• Đang có key: {active_users_with_keys} user
• Bị khóa web: {blocked_web_users} user
• Bị chặn bot: {blocked_tg_users} user

🔑 KEYS:
━━━━━━━━━━━━━━━━━━
• Tổng số: {total_keys} key
• Còn trống: {active_keys_count} key
• Đã dùng: {used_keys_count} key
• Bị khóa: {blocked_keys_count} key

📋 CHI TIẾT USERS:
━━━━━━━━━━━━━━━━━━"""

    await update.message.reply_text(header)

    # Gửi danh sách user theo từng chunk 4000 ký tự
    if not user_list:
        await update.message.reply_text("Chưa có user nào")
    else:
        chunk = ""
        for line in user_list.splitlines(keepends=True):
            if len(chunk) + len(line) > 4000:
                await update.message.reply_text(chunk)
                chunk = ""
            chunk += line
        if chunk:
            await update.message.reply_text(chunk)

    await update.message.reply_text(
        "💡 Chú thích:\n🟢 = Có key hoạt động\n⚪ = Chưa có key\n🔴 = Bị khóa web\n♾️ VV = Key vĩnh viễn\n🔑 = Ngày hết hạn key"
    )



async def cmd_xemtancon(update, context):
    """Xem log các IP tấn công gần nhất. /xemtancon [số lượng]"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này")
        return

    import os, json
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "intrusion_log.json")

    limit = 5
    if context.args:
        try:
            limit = min(int(context.args[0]), 20)
        except Exception:
            pass

    if not os.path.exists(log_file):
        await update.message.reply_text("✅ Chưa có log tấn công nào.")
        return

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            logs = json.load(f)
    except Exception:
        await update.message.reply_text("❌ Không đọc được file log.")
        return

    if not logs:
        await update.message.reply_text("✅ Chưa có log tấn công nào.")
        return

    lines = [f"🚨 {len(logs)} lượt tấn công - Top {limit} gần nhất:\n"]
    for i, entry in enumerate(logs[:limit], 1):
        lines.append(
            f"━━━━━━━━━━━━ #{i} ━━━━━━━━━━━━\n"
            f"📡 IP: {entry.get('ip','?')}\n"
            f"⚠️ Lý do: {entry.get('reason','?')}\n"
            f"🔗 Route: {entry.get('method','?')} {entry.get('path','?')}\n"
            f"💻 UA: {str(entry.get('user_agent','?'))[:80]}\n"
            f"🌐 Ngôn ngữ: {entry.get('accept_lang','?')}\n"
            f"🕐 Thời gian: {entry.get('time','?')}\n"
            f"🔢 Tổng tấn công: {entry.get('attack_count', 1)} lần\n"
        )
    await update.message.reply_text("\n".join(lines))


async def cmd_xoalog(update, context):
    """Xóa toàn bộ log tấn công. /xoalog"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này")
        return

    import os
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "intrusion_log.json")
    try:
        if os.path.exists(log_file):
            os.remove(log_file)
        await update.message.reply_text("✅ Đã xóa toàn bộ log tấn công!")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {e}")



async def cmd_checkip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xem toàn bộ thông tin IP: địa lý, ISP, lịch sử crack, trạng thái ban."""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Không có quyền")
        return
    if not context.args:
        await update.message.reply_text("❌ Cú pháp: /checkip <ip>\nVD: /checkip 1.2.3.4")
        return

    ip = context.args[0].strip()
    import os, json
    import time as _t

    await update.message.reply_text(f"🔍 Đang tra cứu IP {ip}...")

    # Trạng thái ban
    db = load_db()
    ban_info = db.get("banned_ips", {}).get(ip)
    now = _t.time()
    if ban_info and now < ban_info.get("ban_until", 0):
        rem = ban_info["ban_until"] - now
        h = int(rem // 3600)
        m = int((rem % 3600) // 60)
        ban_status = f"🔴 ĐANG BỊ BAN — còn {h}h {m}m\n   📅 Ban lúc: {ban_info.get('banned_at','?')}"
    else:
        ban_status = "🟢 Không bị ban"

    # Tra cứu địa lý
    geo = {}
    location = "Không xác định"
    isp = "Không rõ"
    map_url = ""
    try:
        from geo_lookup import get_ip_info, format_location
        geo      = get_ip_info(ip)
        location = format_location(geo)
        isp      = geo.get("isp","Không rõ")
        map_url  = geo.get("map_url","")
    except Exception as e:
        print(f"Geo error: {e}")

    # Log crack
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "intrusion_log.json")
    crack_logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file,"r",encoding="utf-8") as f:
                crack_logs = [l for l in json.load(f) if l.get("ip") == ip]
        except Exception:
            pass

    # Danh sách TK đã dùng IP này
    unames = list(set(
        l.get("username","") for l in crack_logs
        if l.get("username") and "(chưa" not in l.get("username","")
    ))

    # Phân tích UA hay dùng nhất
    tools = {}
    for l in crack_logs:
        ua = l.get("ua","?")
        if "python" in ua.lower():   k = "Python script"
        elif "curl" in ua.lower():   k = "cURL"
        elif "postman" in ua.lower():k = "Postman"
        elif "go-http" in ua.lower():k = "Go HTTP"
        else:                        k = "Khác"
        tools[k] = tools.get(k,0) + 1

    # Build thông báo
    msg = (
        f"🔍 THÔNG TIN ĐẦY ĐỦ — IP: {ip}\n"
        f"{'='*35}\n\n"
        f"🛡️ TRẠNG THÁI\n"
        f"   {ban_status}\n\n"
        f"🌍 VỊ TRÍ ĐỊA LÝ\n"
        f"   📍 Vị trí: {location}\n"
        f"   🏢 Nhà mạng: {isp}\n"
    )
    if map_url:
        msg += f"   🗺️ Google Maps: {map_url}\n"

    msg += (
        f"\n📊 THỐNG KÊ VI PHẠM\n"
        f"   🔢 Tổng số lần crack: {len(crack_logs)} lần\n"
    )
    if unames:
        msg += f"   👤 Tài khoản đã dùng: {', '.join(unames[:5])}\n"
    if tools:
        tool_str = ", ".join(f"{k}({v})" for k,v in tools.items())
        msg += f"   🛠️ Công cụ dùng: {tool_str}\n"

    if crack_logs:
        msg += f"\n📋 LỊCH SỬ CRACK (5 gần nhất)\n"
        for i, log in enumerate(crack_logs[:5], 1):
            ua_short = log.get("ua","?")[:50]
            msg += (
                f"   ─────────────\n"
                f"   #{i} 🕐 {log.get('time','?')}\n"
                f"      👤 TK: {log.get('username','?')}\n"
                f"      🎮 Route: {log.get('path','?')}\n"
                f"      💻 Tool: {ua_short}\n"
            )

    msg += (
        f"\n⚙️ HÀNH ĐỘNG\n"
        f"   /banip {ip} — Chặn IP\n"
        f"   /unbanip {ip} — Gỡ chặn\n"
    )
    if unames:
        msg += "".join(f"   /band {u} — Khóa TK {u}\n" for u in unames[:3])

    await update.message.reply_text(msg)

async def cmd_banip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Ban IP - chặn truy cập từ IP đó.
    Cú pháp: /banip <ip> [giờ]
    Ví dụ:   /banip 1.2.3.4
             /banip 1.2.3.4 24
    """
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền dùng lệnh này")
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Sai cú pháp!\n\n"
            "✅ Đúng: /banip <ip> [số giờ]\n"
            "Ví dụ:\n"
            "/banip 1.2.3.4\n"
            "/banip 1.2.3.4 24"
        )
        return

    ip = context.args[0].strip()
    hours = 24
    if len(context.args) >= 2:
        try:
            hours = int(context.args[1])
        except ValueError:
            pass

    # Lưu vào database
    db = load_db()
    if "banned_ips" not in db:
        db["banned_ips"] = {}

    import time as _t
    ban_until = _t.time() + hours * 3600
    db["banned_ips"][ip] = {
        "ban_until": ban_until,
        "hours": hours,
        "banned_at": vn_now_str(),
        "by": "admin"
    }
    save_db(db)

    # Đồng thời báo cho intrusion_detector nếu đang chạy
    try:
        from intrusion_detector import _banned_ips
        _banned_ips[ip] = ban_until
    except Exception:
        pass

    await update.message.reply_text(
        f"✅ ĐÃ BAN IP THÀNH CÔNG!\n\n"
        f"📡 IP: {ip}\n"
        f"⏳ Thời gian: {hours} giờ\n"
        f"🕐 Hết hạn: {_t.strftime('%H:%M %d/%m/%Y', _t.localtime(ban_until))}\n\n"
        f"👉 Gỡ ban: /unbanip {ip}"
    )


async def cmd_unbanip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Gỡ ban IP. Cú pháp: /unbanip <ip>"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền dùng lệnh này")
        return

    if not context.args:
        await update.message.reply_text("❌ Cú pháp: /unbanip <ip>")
        return

    ip = context.args[0].strip()
    db = load_db()

    removed = False
    if "banned_ips" in db and ip in db["banned_ips"]:
        del db["banned_ips"][ip]
        save_db(db)
        removed = True

    try:
        from intrusion_detector import _banned_ips
        if ip in _banned_ips:
            del _banned_ips[ip]
            removed = True
    except Exception:
        pass

    if removed:
        await update.message.reply_text(f"✅ Đã gỡ ban IP: {ip}")
    else:
        await update.message.reply_text(f"❌ IP {ip} không có trong danh sách ban")


async def cmd_listbanip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xem danh sách IP đang bị ban. Cú pháp: /listbanip"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền dùng lệnh này")
        return

    import time as _t
    db = load_db()
    banned = db.get("banned_ips", {})

    if not banned:
        await update.message.reply_text("✅ Không có IP nào đang bị ban.")
        return

    now = _t.time()
    lines = [f"🚫 DANH SÁCH IP BAN ({len(banned)} IP):\n"]
    for ip, info in list(banned.items()):
        remaining = info.get("ban_until", 0) - now
        if remaining <= 0:
            # Hết hạn → xóa
            del db["banned_ips"][ip]
            continue
        hours_left = int(remaining // 3600)
        mins_left  = int((remaining % 3600) // 60)
        lines.append(f"📡 {ip} — còn {hours_left}h{mins_left}m")

    save_db(db)
    await update.message.reply_text("\n".join(lines))

async def cmd_iframegame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Đổi link iframe cho game.
    Cú pháp: /iframegame <game> <link>
    Ví dụ:   /iframegame sun https://web.sunwin.ag/?affId=Sunwin
    Game hỗ trợ: sun, hit, b52, luck8, sicbo, 789, 68gb, lc79, sexy
    """
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này")
        return

    # Kiểm tra tham số
    if not context.args or len(context.args) < 2:
        await update.message.reply_text(
            "❌ Sai cú pháp!\n\n"
            "✅ Đúng: /iframegame <game> <link>\n\n"
            "📋 Ví dụ:\n"
            "/iframegame sun https://web.sunwin.ag/?affId=Sunwin\n"
            "/iframegame hit https://m.hitclub.bio\n"
            "/iframegame b52 https://b52.trade\n\n"
            "🎮 Game hỗ trợ:\n"
            "sun | hit | b52 | luck8 | sicbo | 789 | 68gb | lc79 | sexy"
        )
        return

    game_code = context.args[0].lower().strip()
    new_link = context.args[1].strip()

    # Danh sách game và file HTML tương ứng
    GAME_FILES = {
        "sun":   "game_sun.html",
        "hit":   "game_hit.html",
        "b52":   "game_b52.html",
        "luck8": "game_luck8.html",
        "sicbo": "game_sicbo.html",
        "789":   "game_789.html",
        "68gb":  "game_68gb.html",
        "lc79":  "game_lc79.html",
        "sexy":  "game_sexy.html",
    }

    if game_code not in GAME_FILES:
        await update.message.reply_text(
            f"❌ Game '{game_code}' không tồn tại!\n\n"
            f"🎮 Game hỗ trợ: {', '.join(GAME_FILES.keys())}"
        )
        return

    # Kiểm tra link hợp lệ
    if not (new_link.startswith("http://") or new_link.startswith("https://")):
        await update.message.reply_text(
            "❌ Link không hợp lệ!\n"
            "Link phải bắt đầu bằng https:// hoặc http://"
        )
        return

    try:
        import os, re
        base_dir = os.path.dirname(os.path.abspath(__file__))
        html_path = os.path.join(base_dir, GAME_FILES[game_code])

        if not os.path.exists(html_path):
            await update.message.reply_text(f"❌ Không tìm thấy file: {GAME_FILES[game_code]}")
            return

        with open(html_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Lưu link cũ để hiển thị
        old_link_match = re.search(r'<iframe\s[^>]*src="([^"]+)"', content)
        old_link = old_link_match.group(1) if old_link_match else "(không có)"

        # Thay link iframe - xử lý cả 2 trường hợp:
        # 1. Đã có iframe src → thay link
        # 2. Có div iframe-container nhưng trống → chèn iframe mới

        # Tách link thành 3 phần để obfuscate trong JS
        proto    = 'https://' if new_link.startswith('https') else 'http://'
        link_raw = new_link.replace('https://','').replace('http://','')
        mid      = len(link_raw) // 3
        p1, p2, p3 = link_raw[:mid], link_raw[mid:mid*2], link_raw[mid*2:]
        new_parts_js = repr([p1, p2, p3])

        # Ưu tiên 1: Thay mảng _p=[...] trong JS (obfuscated link - dùng khi đã obfuscate)
        if re.search(r"var _p=\[.*?\]", content):
            new_content = re.sub(
                r"var _p=\[.*?\]",
                f"var _p={new_parts_js}",
                content,
                count=1
            )
        # Ưu tiên 2: Thay src="about:blank" thành src thật
        elif re.search(r'<iframe[^>]*src="about:blank"', content):
            new_content = re.sub(
                r'(<iframe[^>]*src=")about:blank(")',
                r'\g<1>' + new_link + r'\g<2>',
                content,
                count=1
            )
        # Ưu tiên 3: Thay src iframe thật
        elif re.search(r'<iframe[^>]*src="https?://', content):
            def _replace_src(m):
                return m.group(1) + new_link + m.group(2)
            new_content = re.sub(
                r'(<iframe[^>]*src=")[^"]*(") *',
                _replace_src,
                content,
                count=1
            )
        # Ưu tiên 4: Chèn mới vào iframe-container
        elif 'class="iframe-container"' in content:
            # Thêm JS inject link mới + mở container
            inject_js = f'''
<script>
(function(){{
  var _p={new_parts_js};
  var _u='{proto}'+_p.join('');
  var el=document.getElementById('gameFrame')||document.querySelector('iframe');
  if(el){{ el.src=_u; }}
}})();
</script>'''
            new_content = content.replace('</body>', inject_js + '\n</body>', 1)
            new_content = new_content.replace(
                'class="iframe-container" style="display:none"',
                'class="iframe-container" style="display:block"'
            )
        else:
            await update.message.reply_text(
                f"❌ Không tìm thấy vị trí iframe trong file {GAME_FILES[game_code]}"
            )
            return

        # Ghi lại file
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        # Reload template trong bộ nhớ (nếu dùng templates.py cache)
        try:
            import templates as tmpl
            import importlib
            importlib.reload(tmpl)
        except Exception:
            pass

        await update.message.reply_text(
            f"✅ ĐÃ CẬP NHẬT LINK IFRAME THÀNH CÔNG!\n\n"
            f"🎮 Game: {game_code.upper()}\n"
            f"🔗 Link cũ:\n{old_link}\n\n"
            f"🆕 Link mới:\n{new_link}\n\n"
            f"⚡ Hiệu lực ngay lập tức!"
        )
        print(f"[IFRAME] Admin đổi link {game_code}: {old_link} → {new_link}")

    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi khi cập nhật:\n{str(e)}")
        print(f"[IFRAME ERROR] {e}")
        import traceback
        traceback.print_exc()


async def cmd_xemiframe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xem link iframe hiện tại của tất cả game. Cú pháp: /xemiframe"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này")
        return

    import os, re

    GAME_FILES = {
        "sun":   "game_sun.html",
        "hit":   "game_hit.html",
        "b52":   "game_b52.html",
        "luck8": "game_luck8.html",
        "sicbo": "game_sicbo.html",
        "789":   "game_789.html",
        "68gb":  "game_68gb.html",
        "lc79":  "game_lc79.html",
        "sexy":  "game_sexy.html",
    }

    base_dir = os.path.dirname(os.path.abspath(__file__))
    lines = ["🔗 LINK IFRAME HIỆN TẠI:\n"]

    for game, filename in GAME_FILES.items():
        path = os.path.join(base_dir, filename)
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            match = re.search(r'<iframe\s[^>]*src="([^"]+)"', content)
            link = match.group(1) if match else "❌ Chưa có link"
        except Exception:
            link = "⚠️ Không đọc được file"

        lines.append(f"🎮 {game.upper()}: {link}")

    await update.message.reply_text("\n".join(lines))


async def cmd_xuatdata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Xuất toàn bộ thông tin tài khoản + số dư ra file JSON và gửi cho admin"""
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này")
        return

    db = load_db()
    users = db.get("users", {})
    transactions = db.get("transactions", [])

    # Tạo dữ liệu xuất gọn gàng
    export_data = {
        "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "tong_tai_khoan": len(users),
        "tong_so_du": sum(u.get("balance", 0) for u in users.values()),
        "tong_nap_vao": sum(t.get("amount", 0) for t in transactions if t.get("type") == "deposit" and t.get("status") == "completed"),
        "tong_mua_key": sum(t.get("amount", 0) for t in transactions if t.get("type") == "buy_key" and t.get("status") == "completed"),
        "tai_khoan": []
    }

    for username, u in users.items():
        # Lấy lịch sử giao dịch của user
        user_txns = [
            {
                "loai": t.get("type"),
                "so_tien": t.get("amount", 0),
                "thoi_gian": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(t.get("time", 0))),
                "trang_thai": t.get("status"),
            }
            for t in transactions if t.get("username") == username
        ]

        # Lấy thông tin key đang active
        active_key = db.get("active", {}).get(username)
        key_info = None
        if active_key:
            expires = active_key.get("expiresAt")
            key_info = {
                "ma_key": active_key.get("code"),
                "het_han": "Vĩnh viễn" if expires is None else time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(expires))
            }

        export_data["tai_khoan"].append({
            "username": username,
            "user_id": u.get("user_id", ""),
            "so_du": u.get("balance", 0),
            "vip": u.get("vip_level", "Đồng"),
            "ngay_tao": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(u.get("created_at", 0))),
            "bi_khoa": username in db.get("blocked_web_login", []),
            "key_active": key_info,
            "lich_su_giao_dich": user_txns
        })

    # Sắp xếp theo số dư giảm dần
    export_data["tai_khoan"].sort(key=lambda x: x["so_du"], reverse=True)

    # Ghi ra file tạm
    import os, io
    filename = f"backup_{time.strftime('%Y%m%d_%H%M%S')}.json"
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    # Gửi file cho admin
    await update.message.reply_text(
        f"📦 Đang xuất dữ liệu...\n"
        f"👥 {len(users)} tài khoản\n"
        f"💰 Tổng số dư: {export_data['tong_so_du']:,}đ"
    )
    with open(filepath, "rb") as f:
        await update.message.reply_document(
            document=f,
            filename=filename,
            caption=f"✅ Backup {time.strftime('%d/%m/%Y %H:%M:%S')}"
        )

    # Xóa file tạm sau khi gửi
    try:
        os.remove(filepath)
    except:
        pass


async def auto_backup(context):
    """Tự động backup mỗi ngày lúc 0h, gửi file cho admin"""
    import os
    db = load_db()
    users = db.get("users", {})
    transactions = db.get("transactions", [])

    export_data = {
        "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "loai": "auto_backup_hang_ngay",
        "tong_tai_khoan": len(users),
        "tong_so_du": sum(u.get("balance", 0) for u in users.values()),
        "tong_nap_vao": sum(t.get("amount", 0) for t in transactions if t.get("type") == "deposit" and t.get("status") == "completed"),
        "tong_mua_key": sum(t.get("amount", 0) for t in transactions if t.get("type") == "buy_key" and t.get("status") == "completed"),
        "tai_khoan": [
            {
                "username": uname,
                "so_du": u.get("balance", 0),
                "vip": u.get("vip_level", "Đồng"),
                "ngay_tao": time.strftime("%Y-%m-%d", time.localtime(u.get("created_at", 0))),
                "bi_khoa": uname in db.get("blocked_web_login", []),
            }
            for uname, u in users.items()
        ]
    }
    export_data["tai_khoan"].sort(key=lambda x: x["so_du"], reverse=True)

    filename = f"auto_backup_{time.strftime('%Y%m%d')}.json"
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)

    try:
        with open(filepath, "rb") as f:
            await context.bot.send_document(
                chat_id=ADMIN_ID,
                document=f,
                filename=filename,
                caption=(
                    f"🔄 AUTO BACKUP {time.strftime('%d/%m/%Y')}\n\n"
                    f"👥 {len(users)} tài khoản\n"
                    f"💰 Tổng số dư: {export_data['tong_so_du']:,}đ\n"
                    f"📥 Tổng nạp: {export_data['tong_nap_vao']:,}đ\n"
                    f"🔑 Tổng mua key: {export_data['tong_mua_key']:,}đ"
                )
            )
    except Exception as e:
        print(f"[BACKUP] Lỗi gửi backup: {e}")
    finally:
        try:
            os.remove(filepath)
        except:
            pass


async def cmd_xoa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này")
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Sai cú pháp!\n\nĐúng: /xoa <username>\nVí dụ: /xoa Minhsang")
        return

    username_to_delete = context.args[0]
    db = load_db()

    if username_to_delete not in db.get("users", {}):
        await update.message.reply_text(
            f"❌ Tài khoản '{username_to_delete}' không tồn tại!")
        return

    # Lưu thông tin user trước khi xóa để hiển thị
    user_info = db["users"][username_to_delete]
    balance = user_info.get("balance", 0)
    user_id = user_info.get("user_id", "N/A")

    # Xóa user khỏi database
    del db["users"][username_to_delete]

    # Xóa khỏi active keys nếu có
    if username_to_delete in db.get("active", {}):
        del db["active"][username_to_delete]

    # Xóa khỏi blocked_web_login nếu có
    if username_to_delete in db.get("blocked_web_login", []):
        db["blocked_web_login"].remove(username_to_delete)

    # Xóa các giao dịch của user (tùy chọn - có thể giữ lại để lưu lịch sử)
    if "transactions" in db:
        db["transactions"] = [t for t in db["transactions"] if t.get("username") != username_to_delete]

    # Giải phóng các keys đã dùng bởi user này
    for key in db.get("shop_keys", []):
        if key.get("usedBy") == username_to_delete:
            key["usedBy"] = None
            key["status"] = "available"

    save_db(db)

    await update.message.reply_text(
        f"✅ ĐÃ XÓA TÀI KHOẢN THÀNH CÔNG!\n\n"
        f"👤 Username: {username_to_delete}\n"
        f"🆔 User ID: {user_id}\n"
        f"💰 Số dư đã mất: {balance:,}đ\n\n"
        f"🔄 Các keys của user này đã được giải phóng\n"
        f"🔄 User sẽ bị đăng xuất ngay lập tức và phải đăng ký lại")


async def cmd_lichsu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("⛔ Bạn không có quyền sử dụng lệnh này")
        return

    if not context.args:
        await update.message.reply_text(
            "❌ Sai cú pháp!\n\n"
            "Đúng: /lichsu <game>\n"
            "Ví dụ: /lichsu sun\n\n"
            "Game có sẵn: sun, hit, b52, sum, luck8, sicbo")
        return

    game = context.args[0].lower()

    if game not in ["sun", "hit", "b52", "sum", "luck8", "sicbo", "789", "68gb", "lc79"]:
        await update.message.reply_text(
            "❌ Game không hợp lệ!\n\n"
            "Game có sẵn: sun, hit, b52, sum, luck8, sicbo, 789, 68gb, lc79")
        return

    game_names = {
        "sun": "SunWin",
        "hit": "HitClub",
        "b52": "B52",
        "sum": "SumClub",
        "luck8": "Luck8",
        "sicbo": "Sicbo SunWin",
        "789": "789Club",
        "68gb": "68 Game Bài",
        "lc79": "LC79"
    }
    game_name = game_names[game]

    # Lấy dữ liệu trực tiếp từ API
    api_data = None
    if game == "sun":
        api_data = safe_json(API_SUN, timeout=5)
    elif game == "hit":
        api_data = safe_json(API_HIT)
    elif game == "sum":
        api_data = safe_json(API_SUM)
    elif game == "b52":
        a = safe_json(API_B52A)
        b = safe_json(API_B52B)
        api_data = b if b and (not a or int(b.get("Phien", 0)) >= int(a.get("Phien", 0))) else a
    elif game == "luck8":
        api_data = safe_json(API_LUCK8)
    elif game == "789":
        api_data = safe_json(API_789)
    elif game == "68gb":
        api_data = safe_json(API_68GB)
    elif game == "lc79":
        api_data = safe_json(API_LC79)

    if not api_data:
        await update.message.reply_text(
            f"❌ Không thể kết nối API {game_name}!\n\n"
            f"Vui lòng thử lại sau.")
        return

    # Lấy phiên hiện tại từ API
    if game == "sun":
        current_session = api_data.get("phien", "---")
        current_result = normalize(api_data.get("ket_qua"))
    elif game == "hit":
        if "data" in api_data:
            phien_ht = api_data["data"].get("phien_hien_tai")
            current_session = str(int(phien_ht) - 1) if phien_ht else "---"
            current_result = "⏳"
        else:
            current_session = api_data.get("phien", "---")
            current_result = normalize(api_data.get("ket_qua"))
    elif game == "sum":
        current_session = api_data.get("Phien") or api_data.get("phien_hien_tai", "---")
        current_result = normalize(api_data.get("Ket_qua"))
    elif game == "b52":
        current_session = api_data.get("Phien", "---")
        current_result = normalize(api_data.get("Ket_qua"))
    elif game == "luck8":
        current_session = api_data.get("phien", "---")
        current_result = normalize(api_data.get("ketQua"))
    elif game == "789":
        current_session = api_data.get("phien", "---")
        current_result = normalize(api_data.get("ket_qua"))
    elif game == "68gb":
        current_session = api_data.get("Phien") or api_data.get("phien", "---")
        current_result = normalize(api_data.get("Ket_qua") or api_data.get("ket_qua"))

    # Lấy thống kê từ PREDICTION_HISTORY
    history = list(PREDICTION_HISTORY[game])

    if not history:
        await update.message.reply_text(
            f"📊 THỐNG KÊ SHOP MINHSANG - {game_name.upper()}\n\n"
            f"❌ Chưa có dữ liệu dự đoán")
        return

    # Tính toán thống kê shop (tổng quan)
    total = len(history)
    correct = sum(1 for p in history if p.get("correct") == True)
    wrong = sum(1 for p in history if p.get("correct") == False)
    accuracy = round(correct / (correct + wrong) * 100, 2) if (correct + wrong) > 0 else 0

    # Thống kê 30 phiên gần nhất
    recent_30 = history[-30:] if len(history) >= 30 else history
    recent_30_correct = sum(1 for p in recent_30 if p.get("correct") == True)
    recent_30_wrong = sum(1 for p in recent_30 if p.get("correct") == False)
    recent_30_total = recent_30_correct + recent_30_wrong
    recent_30_accuracy = round(recent_30_correct / recent_30_total * 100, 2) if recent_30_total > 0 else 0

    # Hiển thị 10 phiên gần nhất chi tiết
    recent_10 = history[-10:] if len(history) >= 10 else history
    recent_detail = ""

    # Đếm thắng/thua trong 10 phiên
    win_count = 0
    lose_count = 0
    pending_count = 0

    for idx, p in enumerate(reversed(recent_10), 1):
        session_raw = p.get("session", "N/A")
        session_display = session_raw
        prediction = p.get("prediction", "N/A")
        actual = p.get("actual")
        is_correct = p.get("correct")

        if actual and actual in ["Tài", "Xỉu"]:
            actual_text = actual
        else:
            actual_text = "⏳"

        if is_correct == True:
            status = "✅ THẮNG"
            win_count += 1
        elif is_correct == False:
            status = "❌ THUA"
            lose_count += 1
        else:
            status = "⏳ CHỜ"
            pending_count += 1

        recent_detail += f"{idx}. {status}\n   Phiên #{session_display} | Dự đoán: {prediction} → Kết quả: {actual_text}\n"

    # Hiển thị phiên hiện tại từ API
    next_session = "---"
    if current_session != "---":
        try:
            next_session = str(int(current_session) + 1)
        except:
            next_session = current_session

    msg = f"""📊 THỐNG KÊ SHOP MINHSANG - {game_name.upper()}

📡 API: Phiên #{current_session} | KQ: {current_result or '⏳'}
🎯 Dự đoán cho: Phiên #{next_session}

━━━━━━━━━━━━━━━━━━
📈 TỔNG QUAN:
• Tổng phiên: {total}
• Đúng: {correct} | Tỷ lệ: {accuracy}%

📊 30 PHIÊN GẦN NHẤT:
• Độ chính xác: {recent_30_accuracy}%
• Đúng: {recent_30_correct}/{recent_30_total}

📋 10 PHIÊN GẦN NHẤT:
• ✅ Thắng: {win_count}
• ❌ Thua: {lose_count}
• ⏳ Chờ KQ: {pending_count}

━━━━━━━━━━━━━━━━━━
{recent_detail}━━━━━━━━━━━━━━━━━━
💡 Tỷ lệ thắng 10 phiên: {round(win_count/(win_count+lose_count)*100, 1) if (win_count+lose_count) > 0 else 0}%"""

    await update.message.reply_text(msg)


async def start_bot_async():

    if not TELEGRAM_AVAILABLE:
        print("❌ Telegram bot bị tắt do thiếu thư viện python-telegram-bot")
        return

    print(f"🤖 Starting Telegram Bot...")
    print(f"🔑 Bot Token: {BOT_TOKEN[:20]}...")
    print(f"👑 Admin ID: {ADMIN_ID}")

    try:
        # ✅ FIX: Dùng ApplicationBuilder với job_queue tắt để tránh lỗi APScheduler
        from telegram.request import HTTPXRequest
        # Tăng timeout tránh lỗi mạng Render free tier
        http_request = HTTPXRequest(
            connection_pool_size=8,
            read_timeout=30,
            write_timeout=30,
            connect_timeout=30,
            pool_timeout=30,
        )
        builder = Application.builder().token(BOT_TOKEN).request(http_request)
        try:
            # Thử bật job_queue nếu có APScheduler
            config.bot_app = builder.build()
            job_queue_available = config.bot_app.job_queue is not None
        except Exception:
            job_queue_available = False

        bot_app = config.bot_app

        # ── Error handler: bắt NetworkError / TimedOut không crash bot ──────
        async def error_handler(update, context):
            import traceback
            from telegram.error import NetworkError, TimedOut, RetryAfter, Forbidden
            err = context.error
            if isinstance(err, (NetworkError, TimedOut)):
                print(f"[BOT] ⚠️ Network lỗi tạm thời (Render): {err} - tự tiếp tục")
                return   # Bỏ qua, polling tự thử lại
            if isinstance(err, RetryAfter):
                print(f"[BOT] ⏳ Telegram rate limit - chờ {err.retry_after}s")
                await asyncio.sleep(err.retry_after)
                return
            if isinstance(err, Forbidden):
                print(f"[BOT] 🔒 Bot bị block bởi user: {err}")
                return
            # Lỗi khác thì log đầy đủ
            print(f"[BOT] ❌ Lỗi không xử lý được: {err}")
            traceback.print_exc()

        bot_app.add_error_handler(error_handler)
        # ─────────────────────────────────────────────────────────────────────

        # Thêm command handlers TRƯỚC message handler để đảm bảo ưu tiên xử lý
        bot_app.add_handler(CommandHandler("start", cmd_start))
        print("✅ Đã đăng ký handler /start")
        bot_app.add_handler(CommandHandler("help", cmd_help))
        bot_app.add_handler(CommandHandler("nap", cmd_nap))
        bot_app.add_handler(CommandHandler("duyet", cmd_duyet))
        bot_app.add_handler(CommandHandler("menu", cmd_menu))
        bot_app.add_handler(CommandHandler("key", cmd_key))
        bot_app.add_handler(CommandHandler("huykey", cmd_huykey))
        bot_app.add_handler(CommandHandler("list", cmd_list))
        bot_app.add_handler(CommandHandler("block", cmd_block))
        bot_app.add_handler(CommandHandler("band", cmd_band))
        bot_app.add_handler(CommandHandler("unband", cmd_unband))
        bot_app.add_handler(CommandHandler("ban_tg", cmd_ban_tg))
        bot_app.add_handler(CommandHandler("unban_tg", cmd_unban_tg))
        bot_app.add_handler(CommandHandler("tong", cmd_tong))
        bot_app.add_handler(CommandHandler("doanhthu", cmd_doanhthu))
        bot_app.add_handler(CommandHandler("xoa", cmd_xoa))
        bot_app.add_handler(CommandHandler("lichsu", cmd_lichsu))
        bot_app.add_handler(CommandHandler("xuatdata", cmd_xuatdata))
        bot_app.add_handler(CommandHandler("iframegame", cmd_iframegame))
        bot_app.add_handler(CommandHandler("xemiframe", cmd_xemiframe))
        bot_app.add_handler(CommandHandler("checkip", cmd_checkip))
        bot_app.add_handler(CommandHandler("banip", cmd_banip))
        bot_app.add_handler(CommandHandler("unbanip", cmd_unbanip))
        bot_app.add_handler(CommandHandler("listbanip", cmd_listbanip))
        bot_app.add_handler(CommandHandler("xemtancon", cmd_xemtancon))
        bot_app.add_handler(CommandHandler("xoalog", cmd_xoalog))

        # ✅ FIX: Chỉ dùng job_queue nếu APScheduler được cài đặt
        if job_queue_available:
            import datetime
            bot_app.job_queue.run_daily(
                auto_backup,
                time=datetime.time(hour=0, minute=0, second=0),
                name="daily_backup"
            )
            print("✅ Auto backup hàng ngày đã được lên lịch")
        else:
            print("⚠️ job_queue không khả dụng - bỏ qua auto backup (cài 'pip install python-telegram-bot[job-queue]' để bật)")

        # Thêm callback handler cho button xác nhận chuyển khoản và duyệt đơn
        bot_app.add_handler(CallbackQueryHandler(callback_confirm_transfer, pattern="^confirm_transfer_"))
        bot_app.add_handler(CallbackQueryHandler(callback_approve_deposit, pattern="^approve_"))

        # Thêm message handler SAU command handlers với ưu tiên thấp hơn
        bot_app.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND,
                                           log_all_messages),
                            group=1)

        print("✅ Đã đăng ký tất cả handlers")
        
        async with bot_app:
            await bot_app.initialize()
            print("✅ Bot đã initialize")
            
            await bot_app.start()
            print("✅ Bot đã start")

            bot_info = await bot_app.bot.get_me()
            print(f"✅ Bot kết nối thành công!")
            print(f"📱 Bot username: @{bot_info.username}")
            print(f"🆔 Bot ID: {bot_info.id}")
            print(f"📝 Bot name: {bot_info.first_name}")
            print(f"💬 Chat tại: https://t.me/{bot_info.username}")
            
            # Xóa webhook nếu có
            await bot_app.bot.delete_webhook(drop_pending_updates=True)
            print("✅ Bắt đầu polling...")

            await bot_app.updater.start_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                poll_interval=1.0,        # poll mỗi 1 giây
                timeout=20,               # long-poll 20 giây / lần
                bootstrap_retries=5,      # thử lại 5 lần nếu Telegram lỗi khi start
            )
            print("✅ Bot đang lắng nghe tin nhắn!")

            # Keep running - in heartbeat mỗi 5 phút
            _hb = 0
            while True:
                await asyncio.sleep(10)
                _hb += 10
                if _hb >= 300:
                    print("[BOT] 💓 Heartbeat - bot vẫn đang chạy", flush=True)
                    _hb = 0

    except Exception as e:
        print(f"❌ Lỗi khi khởi động bot: {str(e)}")
        import traceback
        traceback.print_exc()
        print(
            f"⚠️ Vui lòng kiểm tra lại BOT_TOKEN trong file .env hoặc biến môi trường"
        )


def run_bot_in_thread():
    """Chạy bot trong thread riêng, tự động restart khi gặp lỗi"""
    import time as _time
    restart_count = 0
    while True:
        loop = None
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            restart_count += 1
            print(f"[BOT] 🔄 Lần khởi động #{restart_count}", flush=True)
            loop.run_until_complete(start_bot_async())
        except Exception as e:
            err = str(e)
            print(f"[BOT] ❌ Lỗi: {err}", flush=True)
            if "Conflict" in err or "terminated by other getUpdates" in err:
                wait = 30
                print(f"[BOT] ⚠️ Xung đột bot. Chờ {wait}s rồi restart...", flush=True)
            elif "Network" in err or "TimeOut" in err or "timed out" in err.lower():
                wait = 5
                print(f"[BOT] 🌐 Lỗi mạng tạm thời. Chờ {wait}s...", flush=True)
            else:
                wait = min(10 * restart_count, 60)  # backoff tối đa 60s
                print(f"[BOT] Chờ {wait}s rồi restart...", flush=True)
            _time.sleep(wait)
        finally:
            try:
                if loop and not loop.is_closed():
                    loop.close()
            except:
                pass

# -*- coding: utf-8 -*-
# ================== algorithms.py ==================
# Tất cả thuật toán dự đoán Tài/Xỉu

import os, math, random
from collections import Counter
import requests

# ================== API GAMES ==================
API_SUN = "https://crack-production-7f42.up.railway.app/api/sunwin"
LINK_SUN = "https://web.sunwin.ag/?affId=Sunwin"
API_HIT = "https://toolgameai.site/tt.php?id=hellokietne21&key=bomaylakiet&token=ditmemay&game=hithu"
API_HIT_HU = "https://toolgameai.site/tt.php?id=hellokietne21&key=bomaylakiet&token=ditmemay&game=hithu"
API_SUM = ""  # SumClub đã bỏ
LOGO_SUNWIN = "https://i.postimg.cc/q7ybsvSb/IMG-1615.jpg"
LOGO_HITCLUB = "https://i.postimg.cc/66YHLSbG/IMG-1616.jpg"
LOGO_SUMCLUB = ""
LOGO_B52 = "https://i.postimg.cc/q7swtZCB/IMG-1617.jpg"
API_B52A = "https://b52-taixiu-l69b.onrender.com/api/taixiu"
API_B52B = "https://b52-taixiu-l69b.onrender.com/api/taixiu"
API_LUCK8 = "https://luck8md5vip-4vph.onrender.com/api/taixiu"
LOGO_LUCK8 = "https://i.postimg.cc/tg4Pgzzt/IMG-1702.jpg"
API_SICBO = "https://sicsunnehahahaha.onrender.com/predict"
LINK_SICBO = "https://web.sunwin.ag/?affId=Sunwin"
LOGO_SICBO = "https://i.postimg.cc/fR36RRwD/IMG-2036.jpg"
API_789 = "https://api789hix.hacksieucap.pro/taixiuv3"
LOGO_789 = "https://i.postimg.cc/43HWjS37/789.webp"
API_68GB = "https://six8gbsew.onrender.com/all"
LOGO_68GB = "https://i.postimg.cc/zDQVG2DG/OIP.webp"
API_LC79 = "https://crack-production-7f42.up.railway.app/api/lc79"
LOGO_LC79 = "https://i.postimg.cc/vTSzPJnm/lc79.webp"

# Thuật toán dự đoán vị xúc xắc cho Sicbo
def predict_sicbo_dice_position(h, recent_totals):
    """Dự đoán vị xúc xắc dựa trên lịch sử và xu hướng - Tài (11-18), Xỉu (3-10)"""
    if len(recent_totals) < 5:
        return [10, 11, 12]  # Mặc định
    
    # Phân tích 10 phiên gần nhất
    last_10 = list(recent_totals)[-10:] if len(recent_totals) >= 10 else list(recent_totals)
    avg_total = sum(last_10) / len(last_10)
    
    # Phân tích xu hướng
    last_5 = list(recent_totals)[-5:]
    recent_avg = sum(last_5) / len(last_5)
    
    # Dự đoán dựa trên prediction
    if not h or len(h) < 1:
        return [10, 11, 12]
    
    last_prediction = h[-1] if len(h) > 0 else None
    
    # Logic dự đoán vị - ĐÚNG: Tài (11-18), Xỉu (3-10)
    if last_prediction == "Tài":
        # Tài: tổng 11-18, ưu tiên 13-15
        if recent_avg >= 16:
            return [15, 16, 17]
        elif recent_avg >= 13:
            return [13, 14, 15]
        else:
            return [11, 12, 13]
    else:  # Xỉu
        # Xỉu: tổng 3-10, ưu tiên 6-7-8
        if recent_avg <= 5:
            return [3, 4, 5]
        elif recent_avg <= 7:
            return [6, 7, 8]
        else:
            return [8, 9, 10]


def safe_json(url, timeout=5):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        r = requests.get(url, headers=headers, timeout=timeout, verify=False)
        if r.status_code == 200: 
            return r.json()
    except requests.exceptions.Timeout:
        print(f"⏱️ Timeout khi kết nối: {url}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Lỗi kết nối: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Lỗi không xác định: {str(e)}")
        return None
    return None


def normalize(s):
    if not s: return None
    s = str(s).lower()
    if "tai" in s or "tài" in s: return "Tài"
    if "xiu" in s or "xỉu" in s: return "Xỉu"
    if s in ("0", "false"): return "Xỉu"
    # Bỏ qua các giá trị không hợp lệ
    if "chua" in s or "cho" in s or "dang" in s:
        return None
    return s.capitalize()


# ================== THUẬT TOÁN DỰ ĐOÁN NÂNG CAO ==================


# 1. Thuật toán Markov Chain - Phân tích xác suất chuyển đổi
def algo_markov(h):
    if len(h) < 6: return None
    trans = {"Tài": {"Tài": 0, "Xỉu": 0}, "Xỉu": {"Tài": 0, "Xỉu": 0}}
    for i in range(len(h) - 1):
        # Bỏ qua nếu gặp giá trị không hợp lệ
        if h[i] not in trans or h[i + 1] not in trans:
            continue
        trans[h[i]][h[i + 1]] += 1
    last = h[-1]
    if last not in trans:
        return None
    a = trans[last]["Tài"]
    x = trans[last]["Xỉu"]
    if a + x == 0: return None
    return "Tài" if a > x else "Xỉu"


# 2. Thuật toán Weighted - Trọng số theo thời gian
def algo_weighted(h):
    n = min(15, len(h))
    wT = wX = 0
    for i in range(1, n + 1):
        weight = i * 1.2  # Tăng trọng số cho kết quả gần đây
        if h[-i] == "Tài": wT += weight
        else: wX += weight
    return "Tài" if wT > wX else "Xỉu"


# 3. Thuật toán Momentum - Xu hướng ngắn hạn
def algo_momentum(h):
    if len(h) < 5: return None
    recent = h[-8:]  # Tăng độ dài phân tích
    return "Tài" if recent.count("Tài") > recent.count("Xỉu") else "Xỉu"


# 4. Thuật toán Balance - Cân bằng thống kê
def algo_balance(h):
    if len(h) < 10: return None
    last = h[-25:]  # Phân tích 25 phiên gần nhất
    t = last.count("Tài")
    x = last.count("Xỉu")
    ratio = t / len(last)
    if ratio > 0.65: return "Xỉu"  # Nếu Tài quá nhiều, dự đoán Xỉu
    if ratio < 0.35: return "Tài"  # Nếu Xỉu quá nhiều, dự đoán Tài
    return None


# 5. Thuật toán Entropy - Độ hỗn loạn
def algo_entropy(h):
    seq = h[-20:] if len(h) >= 20 else h
    if not seq: return None
    pT = seq.count("Tài") / len(seq)
    pX = 1 - pT
    ent = -(pT * math.log2(pT + 1e-9) + pX * math.log2(pX + 1e-9))
    if ent > 0.95: return random.choice(["Tài", "Xỉu"])
    return None


# 6. Thuật toán Pattern - Phát hiện chuỗi lặp
def algo_pattern(h):
    if len(h) < 8: return None
    # Tìm chuỗi 3 phiên lặp lại
    pattern = h[-3:]
    for i in range(len(h) - 6, -1, -1):
        if h[i:i + 3] == pattern:
            # Nếu tìm thấy pattern giống, dự đoán phiên tiếp theo
            if i + 3 < len(h):
                return h[i + 3]
    return None


# 7. Thuật toán Streak - Phân tích chuỗi liên tiếp CẢI TIẾN
def algo_streak(h):
    if len(h) < 4: return None
    last = h[-1]
    count = 1
    for i in range(len(h) - 2, -1, -1):
        if h[i] == last:
            count += 1
        else:
            break

    # Điều chỉnh ngưỡng đảo chiều dựa trên độ dài chuỗi
    if count >= 4:
        # Chuỗi 4+ lần liên tiếp -> Rất có thể đảo chiều
        return "Xỉu" if last == "Tài" else "Tài"
    elif count == 3:
        # Chuỗi 3 lần -> Có khả năng đảo chiều
        return "Xỉu" if last == "Tài" else "Tài"
    elif count == 2:
        # Chuỗi 2 lần -> Có thể tiếp tục
        return last
    else:
        # 1 lần -> Theo xu hướng gần nhất
        if len(h) >= 5:
            recent_5 = h[-5:]
            return "Tài" if recent_5.count("Tài") > recent_5.count(
                "Xỉu") else "Xỉu"
        return last


# 8. Thuật toán Fibonacci - Cân bằng dựa trên tỷ lệ vàng
def algo_fibonacci(h):
    if len(h) < 10: return None
    fib_seq = [5, 8, 13, 21]
    for fib in fib_seq:
        if len(h) >= fib:
            segment = h[-fib:]
            t_ratio = segment.count("Tài") / len(segment)
            if t_ratio > 0.618:  # Tỷ lệ vàng
                return "Xỉu"
            elif t_ratio < 0.382:
                return "Tài"
    return None


# 9. Thuật toán Zigzag - Phát hiện dao động
def algo_zigzag(h):
    if len(h) < 6: return None
    changes = 0
    for i in range(len(h) - 5, len(h) - 1):
        if h[i] != h[i + 1]:
            changes += 1
    # Nếu dao động nhiều (>= 3/5), theo xu hướng đảo chiều
    if changes >= 3:
        return "Xỉu" if h[-1] == "Tài" else "Tài"
    return h[-1]


# 10. Thuật toán Adaptive - Thích ứng với từng game
def algo_adaptive(h, game_type):
    if len(h) < 15: return None
    recent = h[-15:]
    t_count = recent.count("Tài")
    x_count = recent.count("Xỉu")

    # Mỗi game có đặc điểm riêng
    if game_type == "sun":
        threshold = 0.55  # SunWin ít dao động
    elif game_type == "hit":
        threshold = 0.60  # HitClub dao động vừa
    elif game_type == "sum":
        threshold = 0.58  # SumClub cân bằng
    else:  # b52
        threshold = 0.62  # B52 dao động nhiều

    ratio = t_count / len(recent)
    if ratio > threshold:
        return "Xỉu"
    elif ratio < (1 - threshold):
        return "Tài"
    return None


# 11. Thuật toán Wave - Phân tích sóng dao động
def algo_wave(h):
    if len(h) < 12: return None
    recent = h[-12:]
    # Đếm số lần đổi chiều
    changes = sum(1 for i in range(len(recent) - 1)
                  if recent[i] != recent[i + 1])

    if changes >= 7:  # Dao động mạnh
        return "Xỉu" if h[-1] == "Tài" else "Tài"
    elif changes <= 3:  # Xu hướng ổn định
        return recent[-1]
    return None


# 12. Thuật toán Statistical Mean - Trung bình thống kê
def algo_statistical_mean(h):
    if len(h) < 20: return None
    recent = h[-20:]
    t_count = recent.count("Tài")
    x_count = recent.count("Xỉu")

    # Nếu lệch khỏi trung bình 50-50 quá nhiều
    if t_count >= 14:  # 70% trở lên là Tài
        return "Xỉu"
    elif x_count >= 14:  # 70% trở lên là Xỉu
        return "Tài"
    return None


# 13. Thuật toán Regression - Hồi quy về trung bình
def algo_regression(h):
    if len(h) < 30: return None
    long_term = h[-30:]
    short_term = h[-10:]

    long_t_ratio = long_term.count("Tài") / len(long_term)
    short_t_ratio = short_term.count("Tài") / len(short_term)

    # Nếu ngắn hạn lệch xa dài hạn, dự đoán hồi về
    if short_t_ratio - long_t_ratio > 0.25:
        return "Xỉu"
    elif long_t_ratio - short_t_ratio > 0.25:
        return "Tài"
    return None


# 14. Thuật toán Consecutive Balance - Cân bằng liên tiếp
def algo_consecutive_balance(h):
    if len(h) < 10: return None

    # Đếm số lần liên tiếp của kết quả hiện tại
    last = h[-1]
    count = 1
    for i in range(len(h) - 2, -1, -1):
        if h[i] == last:
            count += 1
        else:
            break

    # Nếu liên tiếp >= 3 lần, khả năng cao sẽ đảo
    if count >= 3:
        return "Xỉu" if last == "Tài" else "Tài"
    # Nếu 1-2 lần, xem xu hướng 5 phiên gần nhất
    elif len(h) >= 5:
        recent_5 = h[-5:]
        t_count = recent_5.count("Tài")
        if t_count >= 4:
            return "Xỉu"
        elif t_count <= 1:
            return "Tài"
    return None


# 15. Thuật toán Double Pattern - Phát hiện pattern kép
def algo_double_pattern(h):
    if len(h) < 10: return None
    # Tìm pattern 2 phiên lặp lại
    pattern = h[-2:]
    for i in range(len(h) - 4, -1, -1):
        if h[i:i + 2] == pattern:
            # Nếu tìm thấy, dự đoán phiên tiếp theo
            if i + 2 < len(h):
                return h[i + 2]
    return None


# 16. Thuật toán Variance - Phân tích phương sai
def algo_variance(h):
    if len(h) < 15: return None
    segments = [h[i:i + 5] for i in range(0, len(h) - 4, 5)]

    variances = []

    for seg in segments[-3:]:  # 3 đoạn gần nhất
        t_ratio = seg.count("Tài") / len(seg)
        # Phương sai từ 0.5
        variance = abs(t_ratio - 0.5)
        variances.append(variance)

    avg_variance = sum(variances) / len(variances)

    # Nếu phương sai cao (dao động nhiều), dự đoán ngược lại
    if avg_variance > 0.3:
        return "Xỉu" if h[-1] == "Tài" else "Tài"
    # Phương sai thấp, theo xu hướng
    else:
        recent = h[-5:]
        return "Tài" if recent.count("Tài") > 2 else "Xỉu"


# 17. Thuật toán Cluster - Phân cụm dữ liệu
def algo_cluster(h):
    if len(h) < 20: return None
    # Chia thành 4 cụm, mỗi cụm 5 phiên
    clusters = [h[i:i + 5] for i in range(len(h) - 20, len(h), 5)]

    tai_dominance = sum(1 for c in clusters if c.count("Tài") >= 4)
    xiu_dominance = sum(1 for c in clusters if c.count("Xỉu") >= 4)

    # Nếu cụm Tài áp đảo
    if tai_dominance >= 3:
        return "Xỉu"
    elif xiu_dominance >= 3:
        return "Tài"
    return None


# 18. Thuật toán Mean Reversion - Hồi quy về trung bình mạnh
def algo_mean_reversion(h):
    if len(h) < 15: return None

    # Phân tích 3 khung thời gian
    recent_5 = h[-5:]
    recent_10 = h[-10:]
    recent_15 = h[-15:]

    # Tính tỷ lệ Tài trong mỗi khung
    ratio_5 = recent_5.count("Tài") / len(recent_5)
    ratio_10 = recent_10.count("Tài") / len(recent_10)
    ratio_15 = recent_15.count("Tài") / len(recent_15)

    # Nếu tỷ lệ Tài trong 5 phiên gần nhất > 0.8 (4/5 hoặc 5/5)
    if ratio_5 >= 0.8:
        # Kiểm tra xu hướng dài hạn
        if ratio_15 >= 0.6:  # Dài hạn cũng lệch Tài
            return "Xỉu"  # Mạnh mẽ dự đoán Xỉu
    elif ratio_5 <= 0.2:  # 0/5 hoặc 1/5 là Tài
        if ratio_15 <= 0.4:  # Dài hạn cũng lệch Xỉu
            return "Tài"  # Mạnh mẽ dự đoán Tài

    # Kiểm tra sự chênh lệch giữa ngắn hạn và dài hạn
    if abs(ratio_5 - ratio_15) > 0.4:
        # Có sự chênh lệch lớn, hồi quy về trung bình
        if ratio_5 > ratio_15:
            return "Xỉu"
        else:
            return "Tài"

    return None


# 19. Thuật toán Anti-Streak - Chống chuỗi liên tiếp
def algo_anti_streak(h):
    if len(h) < 6: return None

    # Đếm chuỗi hiện tại
    current = h[-1]
    streak_count = 1

    for i in range(len(h) - 2, -1, -1):
        if h[i] == current:
            streak_count += 1
        else:
            break

    # Phân tích lịch sử chuỗi
    recent_20 = h[-20:] if len(h) >= 20 else h

    # Đếm số lần xuất hiện chuỗi dài
    long_streaks = 0
    i = 0
    while i < len(recent_20):
        count = 1
        while i + count < len(recent_20) and recent_20[i] == recent_20[i + count]:
            count += 1
        if count >= 3:
            long_streaks += 1
        i += count

    # Nếu chuỗi hiện tại >= 3 và ít có chuỗi dài trong lịch sử
    if streak_count >= 3:
        if long_streaks <= 2:  # Ít chuỗi dài
            # Mạnh mẽ dự đoán đảo chiều
            return "Xỉu" if current == "Tài" else "Tài"

    # Nếu chuỗi >= 4, luôn đảo chiều
    if streak_count >= 4:
        return "Xỉu" if current == "Tài" else "Tài"

    return None


# 20. Thuật toán Oscillation - Phát hiện dao động chu kỳ
def algo_oscillation(h):
    if len(h) < 12: return None

    # Phân tích pattern dao động
    recent = h[-12:]

    # Đếm số lần chuyển đổi
    changes = sum(1 for i in range(len(recent) - 1) if recent[i] != recent[i + 1])

    # Nếu dao động cao (>= 7/11 lần đổi)
    if changes >= 7:
        # Xu hướng dao động mạnh, dự đoán đảo chiều
        return "Xỉu" if h[-1] == "Tài" else "Tài"

    # Nếu dao động thấp (<= 3/11 lần đổi)
    elif changes <= 3:
        # Xu hướng ổn định, theo xu hướng
        tai_count = recent.count("Tài")
        if tai_count >= 8:
            return "Xỉu"
        elif tai_count <= 4:
            return "Tài"

    return None


# 21. Thuật toán Balance Enforcer - Cưỡng chế cân bằng
def algo_balance_enforcer(h):
    if len(h) < 20: return None

    # Phân tích trong các khung thời gian khác nhau
    windows = [10, 15, 20, 25, 30]
    imbalance_score = 0

    for window in windows:
        if len(h) >= window:
            segment = h[-window:]
            tai_ratio = segment.count("Tài") / len(segment)

            # Tính điểm mất cân bằng
            if tai_ratio >= 0.65:
                imbalance_score += (tai_ratio - 0.5) * 2
            elif tai_ratio <= 0.35:
                imbalance_score -= (0.5 - tai_ratio) * 2

    # Nếu điểm mất cân bằng cao (thiên về Tài)
    if imbalance_score > 1.0:
        return "Xỉu"
    elif imbalance_score < -1.0:
        return "Tài"

    return None


# 22. Thuật toán Recent Bias - Thiên hướng gần đây
def algo_recent_bias(h):
    if len(h) < 8: return None

    # So sánh 3 phiên gần nhất với 5 phiên trước đó
    very_recent = h[-3:]
    recent = h[-8:-3]

    very_recent_tai = very_recent.count("Tài") / len(very_recent)
    recent_tai = recent.count("Tài") / len(recent)

    # Nếu có sự thay đổi xu hướng mạnh
    diff = very_recent_tai - recent_tai

    if diff >= 0.5:  # Đột ngột tăng Tài
        return "Xỉu"
    elif diff <= -0.5:  # Đột ngột tăng Xỉu
        return "Tài"

    return None


# 23. Thuật toán Time-Weighted Pattern - Mẫu theo trọng số thời gian
def algo_time_weighted_pattern(h):
    if len(h) < 12: return None

    # Phân tích 12 phiên gần nhất với trọng số tăng dần
    recent = h[-12:]
    weighted_score = 0

    for i, result in enumerate(recent):
        weight = (i + 1) / 12  # Trọng số từ 1/12 đến 12/12
        if result == "Tài":
            weighted_score += weight * 2
        else:
            weighted_score -= weight * 2

    # Dự đoán dựa trên điểm trọng số
    if weighted_score > 5:
        return "Xỉu"  # Quá nhiều Tài gần đây
    elif weighted_score < -5:
        return "Tài"  # Quá nhiều Xỉu gần đây

    return None


# 24. Thuật toán Dynamic Threshold - Ngưỡng động
def algo_dynamic_threshold(h):
    if len(h) < 20: return None

    # Tính độ biến động trong 20 phiên gần nhất
    recent = h[-20:]
    changes = sum(1 for i in range(len(recent) - 1) if recent[i] != recent[i + 1])
    volatility = changes / (len(recent) - 1)

    # Điều chỉnh ngưỡng dựa trên độ biến động
    if volatility > 0.6:  # Biến động cao
        # Trong môi trường biến động cao, theo xu hướng ngắn hạn
        last_3 = h[-3:]
        return "Tài" if last_3.count("Tài") >= 2 else "Xỉu"
    elif volatility < 0.4:  # Biến động thấp
        # Trong môi trường ổn định, tìm điểm đảo chiều
        tai_ratio = recent.count("Tài") / len(recent)
        if tai_ratio > 0.65:
            return "Xỉu"
        elif tai_ratio < 0.35:
            return "Tài"

    return None


# 25. Thuật toán Momentum Shift - Chuyển động lượng
def algo_momentum_shift(h):
    if len(h) < 15: return None

    # So sánh 2 khung thời gian: 5 phiên xa nhất và 5 phiên gần nhất
    old_segment = h[-15:-10]
    new_segment = h[-5:]

    old_tai_ratio = old_segment.count("Tài") / len(old_segment)
    new_tai_ratio = new_segment.count("Tài") / len(new_segment)

    momentum = new_tai_ratio - old_tai_ratio

    # Nếu momentum quá mạnh về một bên, dự đoán sẽ đảo chiều
    if momentum > 0.4:  # Momentum mạnh về Tài
        return "Xỉu"
    elif momentum < -0.4:  # Momentum mạnh về Xỉu
        return "Tài"

    return None


# 26. Thuật toán Cyclical Pattern - Mẫu chu kỳ
def algo_cyclical_pattern(h):
    if len(h) < 16: return None

    # Tìm các chu kỳ lặp lại trong lịch sử
    last_4 = h[-4:]

    # Tìm kiếm pattern 4 phiên giống nhau trong quá khứ
    for i in range(len(h) - 8, -1, -1):
        if h[i:i + 4] == last_4:
            # Nếu tìm thấy pattern giống, dự đoán phiên tiếp theo
            if i + 4 < len(h):
                return h[i + 4]

    return None


# 27. Thuật toán Statistical Deviation - Độ lệch thống kê
def algo_statistical_deviation(h):
    if len(h) < 25: return None

    recent = h[-25:]
    tai_count = recent.count("Tài")
    expected = len(recent) / 2  # Kỳ vọng 50-50

    deviation = tai_count - expected

    # Nếu lệch quá xa khỏi trung bình, dự đoán hồi về
    if deviation >= 5:  # Nhiều Tài hơn 5 phiên so với kỳ vọng
        return "Xỉu"
    elif deviation <= -5:  # Nhiều Xỉu hơn 5 phiên
        return "Tài"

    return None


# 28. Thuật toán Adaptive Learning - Học thích ứng
def algo_adaptive_learning(h):
    if len(h) < 10: return None

    # Phân tích xu hướng gần đây và điều chỉnh
    recent_10 = h[-10:]
    recent_5 = h[-5:]
    last_result = h[-1]

    # Đếm chuỗi liên tiếp hiện tại
    streak = 1
    for i in range(len(h) - 2, -1, -1):
        if h[i] == last_result:
            streak += 1
        else:
            break

    tai_10 = recent_10.count("Tài")
    tai_5 = recent_5.count("Tài")

    # Logic thích ứng
    if streak >= 3:
        # Chuỗi dài, có khả năng đảo chiều
        return "Xỉu" if last_result == "Tài" else "Tài"
    elif tai_10 >= 7 and tai_5 >= 4:
        # Quá nhiều Tài cả ngắn và dài hạn
        return "Xỉu"
    elif tai_10 <= 3 and tai_5 <= 1:
        # Quá nhiều Xỉu cả ngắn và dài hạn
        return "Tài"

    return None


# 29. Thuật toán Multi-Scale Analysis - Phân tích đa cấp độ
def algo_multi_scale(h):
    if len(h) < 30: return None

    # Phân tích ở 3 cấp độ thời gian khác nhau
    short_term = h[-5:]     # Ngắn hạn
    mid_term = h[-15:]      # Trung hạn
    long_term = h[-30:]     # Dài hạn

    short_tai = short_term.count("Tài") / len(short_term)
    mid_tai = mid_term.count("Tài") / len(mid_term)
    long_tai = long_term.count("Tài") / len(long_term)

    # Nếu cả 3 cấp độ đều nghiêng về một bên
    if short_tai > 0.7 and mid_tai > 0.6 and long_tai > 0.55:
        return "Xỉu"  # Quá nhiều Tài ở mọi cấp độ
    elif short_tai < 0.3 and mid_tai < 0.4 and long_tai < 0.45:
        return "Tài"  # Quá nhiều Xỉu ở mọi cấp độ

    return None


# 30. Thuật toán Probability Distribution - Phân phối xác suất
def algo_probability_distribution(h):
    if len(h) < 20: return None

    recent = h[-20:]

    # Tính phân phối xác suất dựa trên lịch sử
    segments = [recent[i:i+4] for i in range(0, len(recent)-3, 4)]

    tai_heavy_segments = sum(1 for seg in segments if seg.count("Tài") >= 3)
    xiu_heavy_segments = sum(1 for seg in segments if seg.count("Xỉu") >= 3)

    # Dựa trên xu hướng phân đoạn
    if tai_heavy_segments > xiu_heavy_segments + 1:
        return "Xỉu"
    elif xiu_heavy_segments > tai_heavy_segments + 1:
        return "Tài"

    return None


# ================== THUẬT TOÁN PHÂN TÍCH CẦU ==================

# 31. Thuật toán Cầu Đơn - Phân tích kết quả ra 1 lần
def algo_cau_don(h):
    if len(h) < 10: return None

    # Đếm số lần xuất hiện liên tiếp của từng loại
    recent = h[-10:]
    tai_streaks = []
    xiu_streaks = []

    current_streak = 1
    for i in range(len(recent) - 1):
        if recent[i] == recent[i + 1]:
            current_streak += 1
        else:
            if recent[i] == "Tài":
                tai_streaks.append(current_streak)
            else:
                xiu_streaks.append(current_streak)
            current_streak = 1

    # Thêm streak cuối cùng
    if recent[-1] == "Tài":
        tai_streaks.append(current_streak)
    else:
        xiu_streaks.append(current_streak)

    # Nếu có nhiều cầu đơn (1 lần) của 1 bên
    tai_singles = sum(1 for s in tai_streaks if s == 1)
    xiu_singles = sum(1 for s in xiu_streaks if s == 1)

    # Nếu Tài có nhiều cầu đơn, khả năng cao sẽ ra chuỗi Xỉu
    if tai_singles >= 3:
        return "Xỉu"
    elif xiu_singles >= 3:
        return "Tài"

    return None


# 32. Thuật toán Cầu Kép - Phân tích kết quả ra 2 lần liên tiếp
def algo_cau_kep(h):
    if len(h) < 15: return None

    recent = h[-15:]

    # Đếm các chuỗi 2 lần liên tiếp
    double_tai = 0
    double_xiu = 0

    for i in range(len(recent) - 1):
        if i + 2 < len(recent):
            if recent[i] == recent[i + 1] == "Tài" and (i == 0 or recent[i - 1] != "Tài"):
                double_tai += 1
            elif recent[i] == recent[i + 1] == "Xỉu" and (i == 0 or recent[i - 1] != "Xỉu"):
                double_xiu += 1

    # Nếu có nhiều cầu kép của 1 bên, dự đoán bên kia
    if double_tai >= 3:
        return "Xỉu"
    elif double_xiu >= 3:
        return "Tài"

    return None


# 33. Thuật toán Cầu Dài - Phân tích chuỗi dài 3+ lần
def algo_cau_dai(h):
    if len(h) < 20: return None

    recent = h[-20:]

    # Đếm số lần xuất hiện chuỗi dài (3+ lần)
    long_tai = 0
    long_xiu = 0

    i = 0
    while i < len(recent):
        count = 1
        current = recent[i]

        while i + count < len(recent) and recent[i + count] == current:
            count += 1

        if count >= 3:
            if current == "Tài":
                long_tai += 1
            else:
                long_xiu += 1

        i += count

    # Nếu có nhiều cầu dài của 1 bên trong lịch sử gần đây
    if long_tai >= 2:
        # Đã có nhiều cầu dài Tài, khả năng cao sẽ chuyển sang Xỉu
        return "Xỉu"
    elif long_xiu >= 2:
        return "Tài"

    # Kiểm tra chuỗi hiện tại
    last = h[-1]
    current_streak = 1
    for i in range(len(h) - 2, -1, -1):
        if h[i] == last:
            current_streak += 1
        else:
            break

    # Nếu đang trong cầu dài (3+ lần), có thể sắp kết thúc
    if current_streak >= 4:
        return "Xỉu" if last == "Tài" else "Tài"

    return None


# 34. Thuật toán Cầu Lửng - Phân tích kết quả bỏ lửng
def algo_cau_lung(h):
    if len(h) < 12: return None

    recent = h[-12:]

    # Tìm pattern: A -> B -> A (kết quả bị "lửng" giữa 2 kết quả khác)
    lung_tai = 0
    lung_xiu = 0

    for i in range(len(recent) - 2):
        if recent[i] == recent[i + 2] and recent[i] != recent[i + 1]:
            if recent[i] == "Tài":
                lung_tai += 1
            else:
                lung_xiu += 1

    # Nếu có nhiều cầu lửng của 1 bên, dự đoán theo xu hướng
    if lung_tai >= 2:
        # Nhiều cầu lửng Tài, khả năng cao tiếp tục Tài hoặc chuyển Xỉu
        if h[-1] == "Xỉu":
            return "Tài"  # Quay về Tài
    elif lung_xiu >= 2:
        if h[-1] == "Tài":
            return "Xỉu"

    return None


# 35. Thuật toán Cầu Xiên - Phân tích pattern xen kẽ
def algo_cau_xien(h):
    if len(h) < 10: return None

    recent = h[-10:]

    # Kiểm tra pattern xen kẽ: T-X-T-X-T-X...
    alternating = True
    for i in range(len(recent) - 1):
        if recent[i] == recent[i + 1]:
            alternating = False
            break

    if alternating and len(recent) >= 5:
        # Đang trong chuỗi xen kẽ dài, dự đoán tiếp tục xen kẽ
        return "Xỉu" if h[-1] == "Tài" else "Tài"

    # Kiểm tra semi-alternating (xen kẽ 4-5 lần gần đây)
    recent_5 = h[-5:]
    changes = sum(1 for i in range(len(recent_5) - 1) if recent_5[i] != recent_5[i + 1])

    if changes == 4:  # 5 phiên, 4 lần đổi = xen kẽ hoàn toàn
        return "Xỉu" if h[-1] == "Tài" else "Tài"

    return None


# 36. Thuật toán Cầu 2 Nhánh - Phân tích 2 xu hướng song song
def algo_cau_2_nhanh(h):
    if len(h) < 16: return None

    # Phân tích làm 2 nhánh: phiên chẵn và phiên lẻ
    even_results = [h[i] for i in range(len(h)) if i % 2 == 0]
    odd_results = [h[i] for i in range(len(h)) if i % 2 == 1]

    recent_even = even_results[-5:] if len(even_results) >= 5 else even_results
    recent_odd = odd_results[-5:] if len(odd_results) >= 5 else odd_results

    # Phân tích xu hướng mỗi nhánh
    even_tai = recent_even.count("Tài")
    odd_tai = recent_odd.count("Tài")

    # Dự đoán dựa trên vị trí phiên hiện tại
    current_position = len(h)

    if current_position % 2 == 0:  # Phiên chẵn tiếp theo
        if even_tai >= 4:  # Nhánh chẵn đang thiên Tài
            return "Xỉu"
        elif even_tai <= 1:
            return "Tài"
    else:  # Phiên lẻ tiếp theo
        if odd_tai >= 4:
            return "Xỉu"
        elif odd_tai <= 1:
            return "Tài"

    return None


# 37. Thuật toán Cầu Giật - Phân tích đảo chiều đột ngột
def algo_cau_giat(h):
    if len(h) < 8: return None

    recent = h[-8:]

    # Tìm điểm đảo chiều mạnh: chuỗi dài đột ngột chuyển sang chuỗi dài ngược lại
    for i in range(len(recent) - 4):
        # Kiểm tra: 3 cùng loại -> đột ngột 3+ loại kia
        if (recent[i] == recent[i + 1] == recent[i + 2] and
                i + 5 < len(recent) and
                recent[i + 3] == recent[i + 4] == recent[i + 5] and
                recent[i] != recent[i + 3]):

            # Phát hiện pattern giật
            if recent[-1] == recent[i + 3]:
                # Đang trong chuỗi sau khi giật, có thể sắp giật lại
                current_streak = 1
                for j in range(len(recent) - 2, -1, -1):
                    if recent[j] == recent[-1]:
                        current_streak += 1
                    else:
                        break

                if current_streak >= 3:
                    return "Xỉu" if recent[-1] == "Tài" else "Tài"

    return None


# 38. Thuật toán Cầu Châu Âu - Phân tích pattern phức tạp
def algo_cau_chau_au(h):
    if len(h) < 20: return None

    recent = h[-20:]

    # Phân tích pattern phức tạp: nhóm 4 phiên
    groups = [recent[i:i + 4] for i in range(0, len(recent) - 3, 4)]

    # Đếm các loại pattern trong mỗi nhóm
    pattern_scores = {
        "tai_dominant": 0,  # 3-4 Tài trong nhóm
        "xiu_dominant": 0,  # 3-4 Xỉu trong nhóm
        "balanced": 0        # 2-2
    }

    for group in groups:
        tai_count = group.count("Tài")
        if tai_count >= 3:
            pattern_scores["tai_dominant"] += 1
        elif tai_count <= 1:
            pattern_scores["xiu_dominant"] += 1
        else:
            pattern_scores["balanced"] += 1

    # Dự đoán dựa trên pattern
    if pattern_scores["tai_dominant"] >= 3:
        # Nhiều nhóm thiên Tài, sắp chuyển sang Xỉu
        return "Xỉu"
    elif pattern_scores["xiu_dominant"] >= 3:
        return "Tài"
    elif pattern_scores["balanced"] >= 3:
        # Nhiều nhóm cân bằng, theo xu hướng ngắn hạn
        last_3 = h[-3:]
        return "Tài" if last_3.count("Tài") >= 2 else "Xỉu"

    return None


# 39. Thuật toán Phân Tích Chu Kỳ Cầu
def algo_chu_ky_cau(h):
    if len(h) < 25: return None

    # Tìm chu kỳ lặp lại của các cầu
    recent = h[-25:]

    # Phân tích chu kỳ 5 phiên
    cycle_5 = [recent[i:i + 5] for i in range(0, len(recent) - 4, 5)]

    if len(cycle_5) >= 3:
        # So sánh 2 chu kỳ gần nhất
        latest_cycle = cycle_5[-1]
        previous_cycle = cycle_5[-2]

        # Nếu 2 chu kỳ giống nhau >= 60%
        matches = sum(1 for i in range(len(latest_cycle))
                      if i < len(previous_cycle) and latest_cycle[i] == previous_cycle[i])

        if matches >= 3:  # 3/5 giống nhau
            # Chu kỳ đang lặp lại, dự đoán tiếp theo theo chu kỳ cũ
            # Nhưng có điều chỉnh vì xu hướng thay đổi
            if len(previous_cycle) > len(latest_cycle):
                next_in_cycle = previous_cycle[len(latest_cycle)]
                # Đảo chiều để tránh lặp quá nhiều
                return "Xỉu" if next_in_cycle == "Tài" else "Tài"

    return None


# 40. Thuật toán Cầu Tổng Hợp - Kết hợp nhiều loại cầu
def algo_cau_tong_hop(h):
    if len(h) < 15: return None

    recent = h[-15:]
    scores = {"Tài": 0, "Xỉu": 0}

    # Điểm từ cầu đơn
    singles = []
    current = 1
    for i in range(len(recent) - 1):
        if recent[i] == recent[i + 1]:
            current += 1
        else:
            if current == 1:
                singles.append(recent[i])
            current = 1

    if singles.count("Tài") >= 3:
        scores["Xỉu"] += 2
    if singles.count("Xỉu") >= 3:
        scores["Tài"] += 2

    # Điểm từ cầu dài
    i = 0
    while i < len(recent):
        count = 1
        current_val = recent[i]
        while i + count < len(recent) and recent[i + count] == current_val:
            count += 1

        if count >= 4:
            # Cầu dài, khả năng cao sắp đảo
            scores["Xỉu" if current_val == "Tài" else "Tài"] += 3

        i += count

    # Điểm từ xu hướng gần nhất
    last_3 = recent[-3:]
    tai_last_3 = last_3.count("Tài")
    if tai_last_3 == 3:
        scores["Xỉu"] += 1
    elif tai_last_3 == 0:
        scores["Tài"] += 1

    # Kết luận
    if scores["Tài"] > scores["Xỉu"]:
        return "Tài"
    elif scores["Xỉu"] > scores["Tài"]:
        return "Xỉu"

    return None


# ===== 15 THUẬT TOÁN PHÂN TÍCH CẦU NÂNG CAO BỔ SUNG =====

# 76. Thuật toán Cầu Theo Khung Giờ - Phân tích pattern theo thời gian
def algo_cau_theo_khung_gio(h):
    if len(h) < 20: return None

    # Chia lịch sử thành các khung 10 phiên
    segments = [h[i:i + 10] for i in range(0, len(h), 10)]

    if len(segments) < 2:
        return None

    # Phân tích 2 khung gần nhất
    prev_segment = segments[-2] if len(segments) >= 2 else []
    current_segment = segments[-1]

    if len(prev_segment) >= 10 and len(current_segment) >= 5:
        # So sánh xu hướng giữa 2 khung
        prev_tai = prev_segment.count("Tài") / len(prev_segment)
        curr_tai = current_segment.count("Tài") / len(current_segment)

        # Nếu khung trước thiên Tài mạnh, khung hiện tại có xu hướng giảm
        if prev_tai >= 0.7 and curr_tai < 0.5:
            return "Xỉu"  # Sắp đảo về Xỉu
        elif prev_tai <= 0.3 and curr_tai > 0.5:
            return "Tài"  # Sắp đảo về Tài

    return None


# 77. Thuật toán Cầu Kết Hợp - Phân tích nhiều loại cầu cùng lúc
def algo_cau_ket_hop(h):
    if len(h) < 15: return None

    recent = h[-15:]
    scores = {"Tài": 0, "Xỉu": 0}

    # Điểm từ cầu đơn
    i = 0
    while i < len(recent):
        count = 1
        current = recent[i]
        while i + count < len(recent) and recent[i + count] == current:
            count += 1

        if count == 1:  # Cầu đơn
            scores[current] += 1
        elif count == 2:  # Cầu kép
            scores[current] += 2
        elif count >= 4:  # Cầu dài, dự đoán đảo
            opposite = "Xỉu" if current == "Tài" else "Tài"
            scores[opposite] += 3

        i += count

    # Điểm từ pattern xen kẽ
    changes = sum(1 for i in range(len(recent) - 1) if recent[i] != recent[i + 1])
    if changes >= 10:  # Xen kẽ nhiều
        last = recent[-1]
        opposite = "Xỉu" if last == "Tài" else "Tài"
        scores[opposite] += 2

    # Kết luận
    if scores["Tài"] > scores["Xỉu"] + 2:
        return "Tài"
    elif scores["Xỉu"] > scores["Tài"] + 2:
        return "Xỉu"

    return None


# 78. Thuật toán Độ Mạnh Cầu - Đánh giá độ ổn định
def algo_do_manh_cau(h):
    if len(h) < 20: return None

    recent = h[-20:]

    # Tính độ mạnh dựa trên độ dài chuỗi trung bình
    streaks = []
    i = 0
    while i < len(recent):
        count = 1
        current = recent[i]
        while i + count < len(recent) and recent[i + count] == current:
            count += 1
        streaks.append({"value": current, "length": count})
        i += count

    # Tính độ dài trung bình cho mỗi bên
    tai_streaks = [s["length"] for s in streaks if s["value"] == "Tài"]
    xiu_streaks = [s["length"] for s in streaks if s["value"] == "Xỉu"]

    if tai_streaks and xiu_streaks:
        avg_tai = sum(tai_streaks) / len(tai_streaks)
        avg_xiu = sum(xiu_streaks) / len(xiu_streaks)

        # Bên có chuỗi dài hơn thường mạnh hơn
        if avg_tai > avg_xiu + 0.5:
            return "Tài"
        elif avg_xiu > avg_tai + 0.5:
            return "Xỉu"

    return None


# 79. Thuật toán Cầu Đảo Pha - Phát hiện điểm chuyển đổi
def algo_cau_dao_pha(h):
    if len(h) < 25: return None

    # So sánh 2 nửa lịch sử
    first_half = h[-25:-13]
    second_half = h[-12:]

    tai_first = first_half.count("Tài") / len(first_half)
    tai_second = second_half.count("Tài") / len(second_half)

    # Phát hiện đảo pha mạnh
    if abs(tai_first - tai_second) > 0.4:
        # Đang trong giai đoạn đảo pha
        if tai_second > 0.6:
            return "Xỉu"  # Sắp đảo về Xỉu
        elif tai_second < 0.4:
            return "Tài"  # Sắp đảo về Tài

    return None


# 80. Thuật toán Cầu Lặp Tuần Hoàn - Pattern lặp lại có chu kỳ
def algo_cau_lap_tuan_hoan(h):
    if len(h) < 30: return None

    # Tìm chu kỳ lặp 6 phiên
    recent = h[-30:]
    cycles = [recent[i:i + 6] for i in range(0, len(recent) - 5, 6)]

    if len(cycles) >= 3:
        # So sánh chu kỳ gần nhất với chu kỳ trước
        last_cycle = cycles[-1]
        prev_cycle = cycles[-2]

        # Đếm số phiên giống nhau
        matches = sum(1 for i in range(min(len(last_cycle), len(prev_cycle)))
                      if i < len(last_cycle) and i < len(prev_cycle)
                      and last_cycle[i] == prev_cycle[i])

        if matches >= 4:  # 4/6 giống nhau
            # Chu kỳ đang lặp, dự đoán tiếp tục
            tai_in_cycle = last_cycle.count("Tài")
            return "Tài" if tai_in_cycle >= 4 else "Xỉu"

    return None


# 81. Thuật toán Cầu Tăng Trưởng - Phân tích xu hướng tăng/giảm
def algo_cau_tang_truong(h):
    if len(h) < 20: return None

    # Chia thành 4 đoạn 5 phiên
    segments = [h[i:i + 5] for i in range(len(h) - 20, len(h), 5)]

    if len(segments) == 4:
        # Tính tỷ lệ Tài trong mỗi đoạn
        ratios = [seg.count("Tài") / len(seg) for seg in segments]

        # Kiểm tra xu hướng tăng trưởng
        if ratios[0] < ratios[1] < ratios[2] < ratios[3]:
            # Xu hướng Tài tăng liên tục -> sắp đảo
            return "Xỉu"
        elif ratios[0] > ratios[1] > ratios[2] > ratios[3]:
            # Xu hướng Xỉu tăng liên tục -> sắp đảo
            return "Tài"

    return None


# 82. Thuật toán Cầu Phức Tạp - Nhận diện pattern phức tạp
def algo_cau_phuc_tap(h):
    if len(h) < 16: return None

    recent = h[-16:]

    # Pattern phức tạp: A-A-B-B-A-A-B-B
    pattern_found = False
    for i in range(len(recent) - 7):
        if (recent[i] == recent[i + 1] and
                recent[i + 2] == recent[i + 3] and
                recent[i] != recent[i + 2] and
                recent[i + 4] == recent[i + 5] and
                recent[i + 6] == recent[i + 7] and
                recent[i + 4] == recent[i] and
                recent[i + 6] != recent[i]):
            pattern_found = True
            # Dự đoán tiếp tục pattern
            return recent[i]

    return None


# 83. Thuật toán Cầu Ngược Chiều - Phân tích xu hướng ngược
def algo_cau_nguoc_chieu(h):
    if len(h) < 18: return None

    recent = h[-18:]

    # Chia thành 3 đoạn 6 phiên
    seg1 = recent[:6]
    seg2 = recent[6:12]
    seg3 = recent[12:]

    tai_seg1 = seg1.count("Tài")
    tai_seg2 = seg2.count("Tài")
    tai_seg3 = seg3.count("Tài")

    # Pattern ngược chiều: cao -> thấp -> cao
    if tai_seg1 >= 4 and tai_seg2 <= 2 and tai_seg3 >= 4:
        return "Xỉu"  # Sắp xuống
    elif tai_seg1 <= 2 and tai_seg2 >= 4 and tai_seg3 <= 2:
        return "Tài"  # Sắp lên

    return None


# 84. Thuật toán Cầu Biên Độ - Phân tích biên độ dao động
def algo_cau_bien_do(h):
    if len(h) < 20: return None

    recent = h[-20:]

    # Tính biên độ dao động qua số lần đổi chiều
    changes = sum(1 for i in range(len(recent) - 1) if recent[i] != recent[i + 1])
    volatility = changes / (len(recent) - 1)

    # Phân tích theo biên độ
    if volatility > 0.7:  # Biên độ cao
        # Dao động mạnh, theo xu hướng đảo chiều
        return "Xỉu" if recent[-1] == "Tài" else "Tài"
    elif volatility < 0.3:  # Biên độ thấp
        # Ổn định, theo xu hướng chính
        tai_count = recent.count("Tài")
        return "Tài" if tai_count >= 12 else "Xỉu"

    return None


# 85. Thuật toán Cầu Trọng Số Thời Gian - Gần hơn quan trọng hơn
def algo_cau_trong_so_thoi_gian(h):
    if len(h) < 15: return None

    recent = h[-15:]
    weighted_score = 0

    # Gán trọng số tăng dần cho các phiên gần hơn
    for i, result in enumerate(recent):
        weight = (i + 1) / 15  # Trọng số từ 1/15 đến 15/15
        if result == "Tài":
            weighted_score += weight * 2
        else:
            weighted_score -= weight * 2

    # Dự đoán dựa trên điểm trọng số
    if weighted_score > 5:
        return "Xỉu"  # Quá nhiều Tài gần đây
    elif weighted_score < -5:
        return "Tài"  # Quá nhiều Xỉu gần đây

    return None


# 86. Thuật toán Cầu Tích Lũy - Phân tích tích lũy theo thời gian
def algo_cau_tich_luy(h):
    if len(h) < 25: return None

    # Tính tích lũy trong 25 phiên
    recent = h[-25:]
    cumulative = []
    tai_count = 0

    for result in recent:
        if result == "Tài":
            tai_count += 1
        cumulative.append(tai_count)

    # Phân tích tốc độ tích lũy
    early_rate = cumulative[9] / 10  # 10 phiên đầu
    late_rate = (cumulative[-1] - cumulative[14]) / 10  # 10 phiên cuối

    # Nếu tốc độ tăng nhanh ở cuối
    if late_rate > early_rate + 0.3:
        return "Xỉu"  # Tài tăng quá nhanh, sắp đảo
    elif late_rate < early_rate - 0.3:
        return "Tài"  # Xỉu tăng quá nhanh, sắp đảo

    return None


# 87. Thuật toán Cầu Ma Trận - Phân tích theo ma trận 3x3
def algo_cau_ma_tran(h):
    if len(h) < 9: return None

    # Lấy 9 phiên gần nhất tạo ma trận 3x3
    recent = h[-9:]

    # Chuyển thành ma trận
    matrix = [recent[i:i + 3] for i in range(0, 9, 3)]

    # Phân tích hàng và cột
    row_tai = [row.count("Tài") for row in matrix]
    col_tai = [sum(1 for row in matrix if row[i] == "Tài") for i in range(3)]

    # Nếu có hàng hoặc cột toàn Tài/Xỉu
    if 3 in row_tai or 3 in col_tai:
        return "Xỉu"
    elif all(r == 0 for r in row_tai) or all(c == 0 for c in col_tai):
        return "Tài"

    return None


# 88. Thuật toán Cầu Fibonacci Sequence - Dựa theo dãy Fibonacci
def algo_cau_fibonacci_seq(h):
    if len(h) < 21: return None

    # Lấy phiên theo vị trí Fibonacci: 1,2,3,5,8,13,21
    fib_positions = [1, 2, 3, 5, 8, 13, 21]
    fib_results = []

    for pos in fib_positions:
        if pos <= len(h):
            fib_results.append(h[-pos])

    if len(fib_results) >= 5:
        tai_count = fib_results.count("Tài")
        # Nếu các vị trí Fibonacci thiên về 1 bên
        if tai_count >= 5:
            return "Xỉu"
        elif tai_count <= 2:
            return "Tài"

    return None


# 89. Thuật toán Cầu Hội Tụ - Phân tích điểm hội tụ
def algo_cau_hoi_tu(h):
    if len(h) < 30: return None

    # Chia thành 3 đoạn 10 phiên
    segments = [h[i:i + 10] for i in range(len(h) - 30, len(h), 10)]

    if len(segments) == 3:
        # Tính độ lệch so với 50-50
        deviations = []
        for seg in segments:
            tai_ratio = seg.count("Tài") / len(seg)
            deviation = abs(tai_ratio - 0.5)
            deviations.append(deviation)

        # Nếu độ lệch đang giảm dần (hội tụ về cân bằng)
        if deviations[0] > deviations[1] > deviations[2]:
            # Đang cân bằng, theo xu hướng ngắn hạn
            last_5 = h[-5:]
            return "Tài" if last_5.count("Tài") >= 3 else "Xỉu"
        # Nếu độ lệch tăng dần (phân kỳ)
        elif deviations[0] < deviations[1] < deviations[2]:
            # Mất cân bằng, dự đoán đảo chiều
            last_10 = h[-10:]
            tai_count = last_10.count("Tài")
            return "Xỉu" if tai_count >= 7 else "Tài"

    return None


# 90. Thuật toán Cầu Sóng Hài - Phân tích sóng điều hòa
def algo_cau_song_hai(h):
    if len(h) < 24: return None

    recent = h[-24:]

    # Chia thành 8 đoạn 3 phiên
    segments = [recent[i:i + 3] for i in range(0, 24, 3)]

    # Đếm pattern trong mỗi đoạn
    patterns = []
    for seg in segments:
        tai_count = seg.count("Tài")
        if tai_count == 3:
            patterns.append("strong_tai")
        elif tai_count == 2:
            patterns.append("weak_tai")
        elif tai_count == 1:
            patterns.append("weak_xiu")
        else:
            patterns.append("strong_xiu")

    # Phát hiện sóng hài (pattern lặp)
    if len(patterns) >= 4:
        # Kiểm tra pattern 2 đoạn gần nhất có lặp không
        if patterns[-1] == patterns[-3] and patterns[-2] == patterns[-4]:
            # Có sóng hài, dự đoán tiếp tục
            if patterns[-1] in ["strong_tai", "weak_tai"]:
                return "Tài"
            else:
                return "Xỉu"

    return None


# ===== THUẬT TOÁN CẦU NÂNG CAO MỚI =====

# 91. Thuật toán Cầu 1-1 - Pattern đơn lẻ
def algo_cau_1_1(h):
    if len(h) < 8: return None

    # Tìm pattern 1-1 (đơn-đơn xen kẽ)
    recent = h[-8:]
    pattern_1_1_count = 0

    for i in range(len(recent) - 1):
        # Kiểm tra 2 phiên liên tiếp khác nhau (1-1 pattern)
        if recent[i] != recent[i + 1]:
            pattern_1_1_count += 1

    # Nếu có nhiều pattern 1-1, tiếp tục xen kẽ
    if pattern_1_1_count >= 5:
        return "Xỉu" if h[-1] == "Tài" else "Tài"

    return None


# 92. Thuật toán Cầu 1-2-1 - Pattern tam giác
def algo_cau_1_2_1(h):
    if len(h) < 12: return None

    recent = h[-12:]

    # Tìm pattern: 1 lần A - 2 lần B - 1 lần A
    for i in range(len(recent) - 3):
        if (recent[i] != recent[i + 1] and
                recent[i + 1] == recent[i + 2] and
                recent[i + 2] != recent[i + 3] and
                recent[i] == recent[i + 3]):
            # Phát hiện pattern 1-2-1, dự đoán tiếp theo
            if i + 4 < len(recent):
                # Theo pattern, có thể lặp lại
                return recent[i + 1]  # Trả về giá trị ở giữa

    return None


# 93. Thuật toán Cầu 1-2-3 - Pattern tăng dần
def algo_cau_1_2_3(h):
    if len(h) < 15: return None

    recent = h[-15:]

    # Tìm pattern: 1 lần - 2 lần - 3 lần cùng loại
    i = 0
    while i < len(recent) - 5:
        if (recent[i] != recent[i + 1] and  # 1 lần
                recent[i + 1] == recent[i + 2] and recent[i + 2] != recent[i + 3] and  # 2 lần
                recent[i + 3] == recent[i + 4] == recent[i + 5]):  # 3 lần
            # Pattern 1-2-3 phát hiện
            value_type = recent[i + 3]
            return value_type
        i += 1

    return None


# 94. Thuật toán Cầu 2-2 - Cặp đôi lặp
def algo_cau_2_2(h):
    if len(h) < 10: return None

    recent = h[-10:]

    # Tìm pattern 2-2: A-A-B-B hoặc lặp lại
    pair_count = {"Tài": 0, "Xỉu": 0}

    i = 0
    while i < len(recent) - 1:
        if recent[i] == recent[i + 1]:
            # Tìm thấy cặp
            if i + 1 < len(recent) - 1 and recent[i] != recent[i + 2]:
                pair_count[recent[i]] += 1
            i += 2
        else:
            i += 1

    # Nếu có nhiều pattern 2-2
    if pair_count["Tài"] >= 2:
        return "Tài"
    elif pair_count["Xỉu"] >= 2:
        return "Xỉu"

    return None


# 95. Thuật toán Cầu 3-3 - Ba ba lặp
def algo_cau_3_3(h):
    if len(h) < 12: return None

    recent = h[-12:]

    # Tìm pattern: 3 Tài - 3 Xỉu hoặc ngược lại
    for i in range(len(recent) - 5):
        if (recent[i] == recent[i + 1] == recent[i + 2] and
                recent[i + 3] == recent[i + 4] == recent[i + 5] and
                recent[i] != recent[i + 3]):
            # Pattern 3-3 phát hiện, có thể lặp
            return recent[i]  # Quay về loại đầu

    return None


# 96. Thuật toán Cầu 4-4 - Bốn bốn đối xứng
def algo_cau_4_4(h):
    if len(h) < 16: return None

    recent = h[-16:]

    # Tìm pattern: 4 cùng loại - 4 loại kia
    for i in range(len(recent) - 7):
        if (all(recent[i + j] == recent[i] for j in range(4)) and
                all(recent[i + 4 + j] == recent[i + 4] for j in range(4)) and
                recent[i] != recent[i + 4]):
            # Pattern 4-4 phát hiện, có thể lặp
            return recent[i]

    return None


# 97. Thuật toán Cầu 3-2-1 - Pattern giảm dần
def algo_cau_3_2_1(h):
    if len(h) < 12: return None

    recent = h[-12:]

    # Tìm pattern giảm dần: 3 lần - 2 lần - 1 lần
    i = 0
    while i < len(recent) - 5:
        if (recent[i] == recent[i + 1] == recent[i + 2] and  # 3 lần
                recent[i + 3] == recent[i + 4] and recent[i + 3] != recent[i] and  # 2 lần khác
                i + 5 < len(recent)):  # 1 lần
            # Pattern giảm dần, dự đoán đảo chiều
            return "Xỉu" if recent[i] == "Tài" else "Tài"
        i += 1

    return None


# 98. Thuật toán Cầu 2-1-2 - Sandwich pattern
def algo_cau_2_1_2(h):
    if len(h) < 10: return None

    recent = h[-10:]

    # Pattern: 2 lần A - 1 lần B - 2 lần A
    for i in range(len(recent) - 4):
        if (recent[i] == recent[i + 1] and
                recent[i + 2] != recent[i] and
                recent[i + 3] == recent[i + 4] == recent[i]):
            # Pattern 2-1-2 sandwich
            return recent[i]

    return None


# 99. Thuật toán Cầu Bẹt - Bẹt kéo dài
def algo_cau_bet(h):
    if len(h) < 8: return None

    # Đếm chuỗi liên tiếp hiện tại
    current = h[-1]
    streak = 1
    for i in range(len(h) - 2, -1, -1):
        if h[i] == current:
            streak += 1
        else:
            break

    # Nếu đang bẹt >= 5 lần, tiếp tục cho đến khi bẻ
    if streak >= 5:
        return current

    # Nếu bẹt đầu >= 8 lần trong 10 phiên gần nhất
    if len(h) >= 10:
        recent_10 = h[-10:]
        if recent_10.count(current) >= 8:
            return current

    return None


# 100. Thuật toán Cầu Bẹt 10 - Bẻ sau 10 lần
def algo_cau_bet_10(h):
    if len(h) < 12: return None

    current = h[-1]
    streak = 1
    for i in range(len(h) - 2, -1, -1):
        if h[i] == current:
            streak += 1
        else:
            break

    # Nếu bẹt Xỉu 10 lần, thêm 1 con Xỉu nữa rồi bẻ Tài
    if current == "Xỉu" and streak == 10:
        return "Xỉu"  # Thêm 1 con nữa
    elif current == "Xỉu" and streak == 11:
        return "Tài"  # Bẻ

    # Nếu bẹt Tài 10 lần, logic tương tự
    if current == "Tài" and streak == 10:
        return "Tài"
    elif current == "Tài" and streak == 11:
        return "Xỉu"

    return None


# 101. Thuật toán Cầu Bẹt Đầu 8 - Bẹt 8 đầu
def algo_cau_bet_dau_8(h):
    if len(h) < 10: return None

    recent_10 = h[-10:]
    first_8 = recent_10[:8]

    # Nếu 8 phiên đầu trong 10 phiên gần nhất cùng màu
    if first_8.count("Tài") >= 7:
        return "Tài"  # Tiếp tục Tài
    elif first_8.count("Xỉu") >= 7:
        return "Xỉu"  # Tiếp tục Xỉu

    return None


# 102. Thuật toán Cầu Bẹt Cuối 8 - Bẹt 8 cuối trả Tài
def algo_cau_bet_cuoi_8(h):
    if len(h) < 10: return None

    recent_10 = h[-10:]
    last_8 = recent_10[-8:]

    # Nếu 8 phiên cuối bẹt Xỉu, trả Tài
    if last_8.count("Xỉu") >= 7:
        return "Tài"
    # Nếu 8 phiên cuối bẹt Tài, trả Xỉu
    elif last_8.count("Tài") >= 7:
        return "Xỉu"

    return None


# 103. Thuật toán Bẹt 5-6 Tay - Bẻ sau 5-6 lần
def algo_cau_bet_5_6(h):
    if len(h) < 8: return None

    current = h[-1]
    streak = 1
    for i in range(len(h) - 2, -1, -1):
        if h[i] == current:
            streak += 1
        else:
            break

    # Nếu bẹt 5-6 lần, bẻ
    if 5 <= streak <= 6:
        return "Xỉu" if current == "Tài" else "Tài"

    return None


# 104. Thuật toán Cầu 8-11 Tài - Từ 8 lên 11 đi tiếp
def algo_cau_8_11_tai(h):
    if len(h) < 12: return None

    current = h[-1]
    streak = 1
    for i in range(len(h) - 2, -1, -1):
        if h[i] == current:
            streak += 1
        else:
            break

    # Nếu bẹt Tài từ 8 đến 11 lần, tiếp tục Tài
    if current == "Tài" and 8 <= streak <= 11:
        return "Tài"

    return None


# 105. Thuật toán Cầu Xen Kẽ Nâng Cao
def algo_cau_xen_ke_nang_cao(h):
    if len(h) < 12: return None

    recent = h[-12:]

    # Đếm số lần xen kẽ
    alternating_count = 0
    for i in range(len(recent) - 1):
        if recent[i] != recent[i + 1]:
            alternating_count += 1

    # Nếu xen kẽ >= 8/11 lần, tiếp tục xen kẽ
    if alternating_count >= 8:
        return "Xỉu" if h[-1] == "Tài" else "Tài"

    return None


# 106. Thuật toán Cầu Lặp - Phát hiện chuỗi lặp
def algo_cau_lap_nang_cao(h):
    if len(h) < 20: return None

    # Tìm pattern lặp 4 phiên
    last_4 = h[-4:]

    for i in range(len(h) - 8, 0, -1):
        if h[i:i + 4] == last_4:
            # Tìm thấy pattern lặp, xem kết quả tiếp theo
            if i + 4 < len(h):
                next_result = h[i + 4]
                return next_result

    return None


# 107. Thuật toán Kép Xỉu Chẵn - Bẻ Tài
def algo_kep_xiu_chan(h):
    if len(h) < 8: return None

    recent = h[-8:]

    # Đếm số cặp Xỉu
    xiu_pairs = 0
    i = 0
    while i < len(recent) - 1:
        if recent[i] == recent[i + 1] == "Xỉu":
            xiu_pairs += 1
            i += 2
        else:
            i += 1

    # Nếu số cặp Xỉu chẵn (2, 4...), bẻ Tài
    if xiu_pairs > 0 and xiu_pairs % 2 == 0:
        return "Tài"

    return None


# 108. Thuật toán Kép Xỉu Lẻ - Đi Xỉu
def algo_kep_xiu_le(h):
    if len(h) < 8: return None

    recent = h[-8:]

    # Đếm số cặp Xỉu
    xiu_pairs = 0
    i = 0
    while i < len(recent) - 1:
        if recent[i] == recent[i + 1] == "Xỉu":
            xiu_pairs += 1
            i += 2
        else:
            i += 1

    # Nếu số cặp Xỉu lẻ (1, 3, 5...), đi Xỉu
    if xiu_pairs > 0 and xiu_pairs % 2 == 1:
        return "Xỉu"

    return None


# 109. Thuật toán Kép Tài Chẵn - Đi Tài
def algo_kep_tai_chan(h):
    if len(h) < 8: return None

    recent = h[-8:]

    # Đếm số cặp Tài
    tai_pairs = 0
    i = 0
    while i < len(recent) - 1:
        if recent[i] == recent[i + 1] == "Tài":
            tai_pairs += 1
            i += 2
        else:
            i += 1

    # Nếu số cặp Tài chẵn, đi Tài
    if tai_pairs > 0 and tai_pairs % 2 == 0:
        return "Tài"

    return None


# 110. Thuật toán Kép Tài Lẻ - Bẻ Xỉu
def algo_kep_tai_le(h):
    if len(h) < 8: return None

    recent = h[-8:]

    # Đếm số cặp Tài
    tai_pairs = 0
    i = 0
    while i < len(recent) - 1:
        if recent[i] == recent[i + 1] == "Tài":
            tai_pairs += 1
            i += 2
        else:
            i += 1

    # Nếu số cặp Tài lẻ, bẻ Xỉu
    if tai_pairs > 0 and tai_pairs % 2 == 1:
        return "Xỉu"

    return None


# ===== THUẬT TOÁN CẦU NÂNG CAO MỚI =====

# 91. Thuật toán Cầu 1-1 - Pattern đơn lẻ
def algo_cau_1_1(h):
    if len(h) < 8: return None

    # Tìm pattern 1-1 (đơn-đơn xen kẽ)
    recent = h[-8:]
    pattern_1_1_count = 0

    for i in range(len(recent) - 1):
        # Kiểm tra 2 phiên liên tiếp khác nhau (1-1 pattern)
        if recent[i] != recent[i + 1]:
            pattern_1_1_count += 1

    # Nếu có nhiều pattern 1-1, tiếp tục xen kẽ
    if pattern_1_1_count >= 5:
        return "Xỉu" if h[-1] == "Tài" else "Tài"

    return None


# 92. Thuật toán Cầu 1-2-1 - Pattern tam giác
def algo_cau_1_2_1(h):
    if len(h) < 12: return None

    recent = h[-12:]

    # Tìm pattern: 1 lần A - 2 lần B - 1 lần A
    for i in range(len(recent) - 3):
        if (recent[i] != recent[i + 1] and
                recent[i + 1] == recent[i + 2] and
                recent[i + 2] != recent[i + 3] and
                recent[i] == recent[i + 3]):
            # Phát hiện pattern 1-2-1, dự đoán tiếp theo
            if i + 4 < len(recent):
                # Theo pattern, có thể lặp lại
                return recent[i + 1]  # Trả về giá trị ở giữa

    return None


# 93. Thuật toán Cầu 1-2-3 - Pattern tăng dần
def algo_cau_1_2_3(h):
    if len(h) < 15: return None

    recent = h[-15:]

    # Tìm pattern: 1 lần - 2 lần - 3 lần cùng loại
    i = 0
    while i < len(recent) - 5:
        if (recent[i] != recent[i + 1] and  # 1 lần
                recent[i + 1] == recent[i + 2] and recent[i + 2] != recent[i + 3] and  # 2 lần
                recent[i + 3] == recent[i + 4] == recent[i + 5]):  # 3 lần
            # Pattern 1-2-3 phát hiện
            value_type = recent[i + 3]
            return value_type
        i += 1

    return None


# 94. Thuật toán Cầu 2-2 - Cặp đôi lặp
def algo_cau_2_2(h):
    if len(h) < 10: return None

    recent = h[-10:]

    # Tìm pattern 2-2: A-A-B-B hoặc lặp lại
    pair_count = {"Tài": 0, "Xỉu": 0}

    i = 0
    while i < len(recent) - 1:
        if recent[i] == recent[i + 1]:
            # Tìm thấy cặp
            if i + 1 < len(recent) - 1 and recent[i] != recent[i + 2]:
                pair_count[recent[i]] += 1
            i += 2
        else:
            i += 1

    # Nếu có nhiều pattern 2-2
    if pair_count["Tài"] >= 2:
        return "Tài"
    elif pair_count["Xỉu"] >= 2:
        return "Xỉu"

    return None


# 95. Thuật toán Cầu 3-3 - Ba ba lặp
def algo_cau_3_3(h):
    if len(h) < 12: return None

    recent = h[-12:]

    # Tìm pattern: 3 Tài - 3 Xỉu hoặc ngược lại
    for i in range(len(recent) - 5):
        if (recent[i] == recent[i + 1] == recent[i + 2] and
                recent[i + 3] == recent[i + 4] == recent[i + 5] and
                recent[i] != recent[i + 3]):
            # Pattern 3-3 phát hiện, có thể lặp
            return recent[i]  # Quay về loại đầu

    return None


# 96. Thuật toán Cầu 4-4 - Bốn bốn đối xứng
def algo_cau_4_4(h):
    if len(h) < 16: return None

    recent = h[-16:]

    # Tìm pattern: 4 cùng loại - 4 loại kia
    for i in range(len(recent) - 7):
        if (all(recent[i + j] == recent[i] for j in range(4)) and
                all(recent[i + 4 + j] == recent[i + 4] for j in range(4)) and
                recent[i] != recent[i + 4]):
            # Pattern 4-4 phát hiện, có thể lặp
            return recent[i]

    return None


# 97. Thuật toán Cầu 3-2-1 - Pattern giảm dần
def algo_cau_3_2_1(h):
    if len(h) < 12: return None

    recent = h[-12:]

    # Tìm pattern giảm dần: 3 lần - 2 lần - 1 lần
    i = 0
    while i < len(recent) - 5:
        if (recent[i] == recent[i + 1] == recent[i + 2] and  # 3 lần
                recent[i + 3] == recent[i + 4] and recent[i + 3] != recent[i] and  # 2 lần khác
                i + 5 < len(recent)):  # 1 lần
            # Pattern giảm dần, dự đoán đảo chiều
            return "Xỉu" if recent[i] == "Tài" else "Tài"
        i += 1

    return None


# 98. Thuật toán Cầu 2-1-2 - Sandwich pattern
def algo_cau_2_1_2(h):
    if len(h) < 10: return None

    recent = h[-10:]

    # Pattern: 2 lần A - 1 lần B - 2 lần A
    for i in range(len(recent) - 4):
        if (recent[i] == recent[i + 1] and
                recent[i + 2] != recent[i] and
                recent[i + 3] == recent[i + 4] == recent[i]):
            # Pattern 2-1-2 sandwich
            return recent[i]

    return None


# 99. Thuật toán Cầu Bẹt - Bẹt kéo dài
def algo_cau_bet(h):
    if len(h) < 8: return None

    # Đếm chuỗi liên tiếp hiện tại
    current = h[-1]
    streak = 1
    for i in range(len(h) - 2, -1, -1):
        if h[i] == current:
            streak += 1
        else:
            break

    # Nếu đang bẹt >= 5 lần, tiếp tục cho đến khi bẻ
    if streak >= 5:
        return current

    # Nếu bẹt đầu >= 8 lần trong 10 phiên gần nhất
    if len(h) >= 10:
        recent_10 = h[-10:]
        if recent_10.count(current) >= 8:
            return current

    return None


# 100. Thuật toán Cầu Bẹt 10 - Bẻ sau 10 lần
def algo_cau_bet_10(h):
    if len(h) < 12: return None

    current = h[-1]
    streak = 1
    for i in range(len(h) - 2, -1, -1):
        if h[i] == current:
            streak += 1
        else:
            break

    # Nếu bẹt Xỉu 10 lần, thêm 1 con Xỉu nữa rồi bẻ Tài
    if current == "Xỉu" and streak == 10:
        return "Xỉu"  # Thêm 1 con nữa
    elif current == "Xỉu" and streak == 11:
        return "Tài"  # Bẻ

    # Nếu bẹt Tài 10 lần, logic tương tự
    if current == "Tài" and streak == 10:
        return "Tài"
    elif current == "Tài" and streak == 11:
        return "Xỉu"

    return None


# 101. Thuật toán Cầu Bẹt Đầu 8 - Bẹt 8 đầu
def algo_cau_bet_dau_8(h):
    if len(h) < 10: return None

    recent_10 = h[-10:]
    first_8 = recent_10[:8]

    # Nếu 8 phiên đầu trong 10 phiên gần nhất cùng màu
    if first_8.count("Tài") >= 7:
        return "Tài"  # Tiếp tục Tài
    elif first_8.count("Xỉu") >= 7:
        return "Xỉu"  # Tiếp tục Xỉu

    return None


# 102. Thuật toán Cầu Bẹt Cuối 8 - Bẹt 8 cuối trả Tài
def algo_cau_bet_cuoi_8(h):
    if len(h) < 10: return None

    recent_10 = h[-10:]
    last_8 = recent_10[-8:]

    # Nếu 8 phiên cuối bẹt Xỉu, trả Tài
    if last_8.count("Xỉu") >= 7:
        return "Tài"
    # Nếu 8 phiên cuối bẹt Tài, trả Xỉu
    elif last_8.count("Tài") >= 7:
        return "Xỉu"

    return None


# 103. Thuật toán Bẹt 5-6 Tay - Bẻ sau 5-6 lần
def algo_cau_bet_5_6(h):
    if len(h) < 8: return None

    current = h[-1]
    streak = 1
    for i in range(len(h) - 2, -1, -1):
        if h[i] == current:
            streak += 1
        else:
            break

    # Nếu bẹt 5-6 lần, bẻ
    if 5 <= streak <= 6:
        return "Xỉu" if current == "Tài" else "Tài"

    return None


# 104. Thuật toán Cầu 8-11 Tài - Từ 8 lên 11 đi tiếp
def algo_cau_8_11_tai(h):
    if len(h) < 12: return None

    current = h[-1]
    streak = 1
    for i in range(len(h) - 2, -1, -1):
        if h[i] == current:
            streak += 1
        else:
            break

    # Nếu bẹt Tài từ 8 đến 11 lần, tiếp tục Tài
    if current == "Tài" and 8 <= streak <= 11:
        return "Tài"

    return None


# 105. Thuật toán Cầu Xen Kẽ Nâng Cao
def algo_cau_xen_ke_nang_cao(h):
    if len(h) < 12: return None

    recent = h[-12:]

    # Đếm số lần xen kẽ
    alternating_count = 0
    for i in range(len(recent) - 1):
        if recent[i] != recent[i + 1]:
            alternating_count += 1

    # Nếu xen kẽ >= 8/11 lần, tiếp tục xen kẽ
    if alternating_count >= 8:
        return "Xỉu" if h[-1] == "Tài" else "Tài"

    return None


# 106. Thuật toán Cầu Lặp - Phát hiện chuỗi lặp
def algo_cau_lap_nang_cao(h):
    if len(h) < 20: return None

    # Tìm pattern lặp 4 phiên
    last_4 = h[-4:]

    for i in range(len(h) - 8, 0, -1):
        if h[i:i + 4] == last_4:
            # Tìm thấy pattern lặp, xem kết quả tiếp theo
            if i + 4 < len(h):
                next_result = h[i + 4]
                return next_result

    return None


# 107. Thuật toán Kép Xỉu Chẵn - Bẻ Tài
def algo_kep_xiu_chan(h):
    if len(h) < 8: return None

    recent = h[-8:]

    # Đếm số cặp Xỉu
    xiu_pairs = 0
    i = 0
    while i < len(recent) - 1:
        if recent[i] == recent[i + 1] == "Xỉu":
            xiu_pairs += 1
            i += 2
        else:
            i += 1

    # Nếu số cặp Xỉu chẵn (2, 4...), bẻ Tài
    if xiu_pairs > 0 and xiu_pairs % 2 == 0:
        return "Tài"

    return None


# 108. Thuật toán Kép Xỉu Lẻ - Đi Xỉu
def algo_kep_xiu_le(h):
    if len(h) < 8: return None

    recent = h[-8:]

    # Đếm số cặp Xỉu
    xiu_pairs = 0
    i = 0
    while i < len(recent) - 1:
        if recent[i] == recent[i + 1] == "Xỉu":
            xiu_pairs += 1
            i += 2
        else:
            i += 1

    # Nếu số cặp Xỉu lẻ (1, 3, 5...), đi Xỉu
    if xiu_pairs > 0 and xiu_pairs % 2 == 1:
        return "Xỉu"

    return None


# 109. Thuật toán Kép Tài Chẵn - Đi Tài
def algo_kep_tai_chan(h):
    if len(h) < 8: return None

    recent = h[-8:]

    # Đếm số cặp Tài
    tai_pairs = 0
    i = 0
    while i < len(recent) - 1:
        if recent[i] == recent[i + 1] == "Tài":
            tai_pairs += 1
            i += 2
        else:
            i += 1

    # Nếu số cặp Tài chẵn, đi Tài
    if tai_pairs > 0 and tai_pairs % 2 == 0:
        return "Tài"

    return None


# 110. Thuật toán Kép Tài Lẻ - Bẻ Xỉu
def algo_kep_tai_le(h):
    if len(h) < 8: return None

    recent = h[-8:]

    # Đếm số cặp Tài
    tai_pairs = 0
    i = 0
    while i < len(recent) - 1:
        if recent[i] == recent[i + 1] == "Tài":
            tai_pairs += 1
            i += 2
        else:
            i += 1

    # Nếu số cặp Tài lẻ, bẻ Xỉu
    if tai_pairs > 0 and tai_pairs % 2 == 1:
        return "Xỉu"

    return None


# ===== THUẬT TOÁN CẦU NÂNG CAO MỚI =====

# 111. Thuật toán Cầu 1-1 - Pattern đơn lẻ
def algo_cau_1_1(h):
    if len(h) < 8: return None

    # Tìm pattern 1-1 (đơn-đơn xen kẽ)
    recent = h[-8:]
    pattern_1_1_count = 0

    for i in range(len(recent) - 1):
        # Kiểm tra 2 phiên liên tiếp khác nhau (1-1 pattern)
        if recent[i] != recent[i + 1]:
            pattern_1_1_count += 1

    # Nếu có nhiều pattern 1-1, tiếp tục xen kẽ
    if pattern_1_1_count >= 5:
        return "Xỉu" if h[-1] == "Tài" else "Tài"

    return None


# 112. Thuật toán Cầu 1-2-1 - Pattern tam giác
def algo_cau_1_2_1(h):
    if len(h) < 12: return None

    recent = h[-12:]

    # Tìm pattern: 1 lần A - 2 lần B - 1 lần A
    for i in range(len(recent) - 3):
        if (recent[i] != recent[i + 1] and
                recent[i + 1] == recent[i + 2] and
                recent[i + 2] != recent[i + 3] and
                recent[i] == recent[i + 3]):
            # Phát hiện pattern 1-2-1, dự đoán tiếp theo
            if i + 4 < len(recent):
                # Theo pattern, có thể lặp lại
                return recent[i + 1]  # Trả về giá trị ở giữa

    return None


# 113. Thuật toán Cầu 1-2-3 - Pattern tăng dần
def algo_cau_1_2_3(h):
    if len(h) < 15: return None

    recent = h[-15:]

    # Tìm pattern: 1 lần - 2 lần - 3 lần cùng loại
    i = 0
    while i < len(recent) - 5:
        if (recent[i] != recent[i + 1] and  # 1 lần
                recent[i + 1] == recent[i + 2] and recent[i + 2] != recent[i + 3] and  # 2 lần
                recent[i + 3] == recent[i + 4] == recent[i + 5]):  # 3 lần
            # Pattern 1-2-3 phát hiện
            value_type = recent[i + 3]
            return value_type
        i += 1

    return None


# 114. Thuật toán Cầu 2-2 - Cặp đôi lặp
def algo_cau_2_2(h):
    if len(h) < 10: return None

    recent = h[-10:]

    # Tìm pattern 2-2: A-A-B-B hoặc lặp lại
    pair_count = {"Tài": 0, "Xỉu": 0}

    i = 0
    while i < len(recent) - 1:
        if recent[i] == recent[i + 1]:
            # Tìm thấy cặp
            if i + 1 < len(recent) - 1 and recent[i] != recent[i + 2]:
                pair_count[recent[i]] += 1
            i += 2
        else:
            i += 1

    # Nếu có nhiều pattern 2-2
    if pair_count["Tài"] >= 2:
        return "Tài"
    elif pair_count["Xỉu"] >= 2:
        return "Xỉu"

    return None


# 115. Thuật toán Cầu 3-3 - Ba ba lặp
def algo_cau_3_3(h):
    if len(h) < 12: return None

    recent = h[-12:]

    # Tìm pattern: 3 Tài - 3 Xỉu hoặc ngược lại
    for i in range(len(recent) - 5):
        if (recent[i] == recent[i + 1] == recent[i + 2] and
                recent[i + 3] == recent[i + 4] == recent[i + 5] and
                recent[i] != recent[i + 3]):
            # Pattern 3-3 phát hiện, có thể lặp
            return recent[i]  # Quay về loại đầu

    return None


# 116. Thuật toán Cầu 4-4 - Bốn bốn đối xứng
def algo_cau_4_4(h):
    if len(h) < 16: return None

    recent = h[-16:]

    # Tìm pattern: 4 cùng loại - 4 loại kia
    for i in range(len(recent) - 7):
        if (all(recent[i + j] == recent[i] for j in range(4)) and
                all(recent[i + 4 + j] == recent[i + 4] for j in range(4)) and
                recent[i] != recent[i + 4]):
            # Pattern 4-4 phát hiện, có thể lặp
            return recent[i]

    return None


# 117. Thuật toán Cầu 3-2-1 - Pattern giảm dần
def algo_cau_3_2_1(h):
    if len(h) < 12: return None

    recent = h[-12:]

    # Tìm pattern giảm dần: 3 lần - 2 lần - 1 lần
    i = 0
    while i < len(recent) - 5:
        if (recent[i] == recent[i + 1] == recent[i + 2] and  # 3 lần
                recent[i + 3] == recent[i + 4] and recent[i + 3] != recent[i] and  # 2 lần khác
                i + 5 < len(recent)):  # 1 lần
            # Pattern giảm dần, dự đoán đảo chiều
            return "Xỉu" if recent[i] == "Tài" else "Tài"
        i += 1

    return None


# 118. Thuật toán Cầu 2-1-2 - Sandwich pattern
def algo_cau_2_1_2(h):
    if len(h) < 10: return None

    recent = h[-10:]

    # Pattern: 2 lần A - 1 lần B - 2 lần A
    for i in range(len(recent) - 4):
        if (recent[i] == recent[i + 1] and
                recent[i + 2] != recent[i] and
                recent[i + 3] == recent[i + 4] == recent[i]):
            # Pattern 2-1-2 sandwich
            return recent[i]

    return None


# 119. Thuật toán Cầu Bẹt - Bẹt kéo dài
def algo_cau_bet(h):
    if len(h) < 8: return None

    # Đếm chuỗi liên tiếp hiện tại
    current = h[-1]
    streak = 1
    for i in range(len(h) - 2, -1, -1):
        if h[i] == current:
            streak += 1
        else:
            break

    # Nếu đang bẹt >= 5 lần, tiếp tục cho đến khi bẻ
    if streak >= 5:
        return current

    # Nếu bẹt đầu >= 8 lần trong 10 phiên gần nhất
    if len(h) >= 10:
        recent_10 = h[-10:]
        if recent_10.count(current) >= 8:
            return current

    return None


# 120. Thuật toán Cầu Bẹt 10 - Bẻ sau 10 lần
def algo_cau_bet_10(h):
    if len(h) < 12: return None

    current = h[-1]
    streak = 1
    for i in range(len(h) - 2, -1, -1):
        if h[i] == current:
            streak += 1
        else:
            break

    # Nếu bẹt Xỉu 10 lần, thêm 1 con Xỉu nữa rồi bẻ Tài
    if current == "Xỉu" and streak == 10:
        return "Xỉu"  # Thêm 1 con nữa
    elif current == "Xỉu" and streak == 11:
        return "Tài"  # Bẻ

    # Nếu bẹt Tài 10 lần, logic tương tự
    if current == "Tài" and streak == 10:
        return "Tài"
    elif current == "Tài" and streak == 11:
        return "Xỉu"

    return None


# 121. Thuật toán Cầu Bẹt Đầu 8 - Bẹt 8 đầu
def algo_cau_bet_dau_8(h):
    if len(h) < 10: return None

    recent_10 = h[-10:]
    first_8 = recent_10[:8]

    # Nếu 8 phiên đầu trong 10 phiên gần nhất cùng màu
    if first_8.count("Tài") >= 7:
        return "Tài"  # Tiếp tục Tài
    elif first_8.count("Xỉu") >= 7:
        return "Xỉu"  # Tiếp tục Xỉu

    return None


# 122. Thuật toán Cầu Bẹt Cuối 8 - Bẹt 8 cuối trả Tài
def algo_cau_bet_cuoi_8(h):
    if len(h) < 10: return None

    recent_10 = h[-10:]
    last_8 = recent_10[-8:]

    # Nếu 8 phiên cuối bẹt Xỉu, trả Tài
    if last_8.count("Xỉu") >= 7:
        return "Tài"
    # Nếu 8 phiên cuối bẹt Tài, trả Xỉu
    elif last_8.count("Tài") >= 7:
        return "Xỉu"

    return None


# 123. Thuật toán Bẹt 5-6 Tay - Bẻ sau 5-6 lần
def algo_cau_bet_5_6(h):
    if len(h) < 8: return None

    current = h[-1]
    streak = 1
    for i in range(len(h) - 2, -1, -1):
        if h[i] == current:
            streak += 1
        else:
            break

    # Nếu bẹt 5-6 lần, bẻ
    if 5 <= streak <= 6:
        return "Xỉu" if current == "Tài" else "Tài"

    return None


# 124. Thuật toán Cầu 8-11 Tài - Từ 8 lên 11 đi tiếp
def algo_cau_8_11_tai(h):
    if len(h) < 12: return None

    current = h[-1]
    streak = 1
    for i in range(len(h) - 2, -1, -1):
        if h[i] == current:
            streak += 1
        else:
            break

    # Nếu bẹt Tài từ 8 đến 11 lần, tiếp tục Tài
    if current == "Tài" and 8 <= streak <= 11:
        return "Tài"

    return None


# 125. Thuật toán Cầu Xen Kẽ Nâng Cao
def algo_cau_xen_ke_nang_cao(h):
    if len(h) < 12: return None

    recent = h[-12:]

    # Đếm số lần xen kẽ
    alternating_count = 0
    for i in range(len(recent) - 1):
        if recent[i] != recent[i + 1]:
            alternating_count += 1

    # Nếu xen kẽ >= 8/11 lần, tiếp tục xen kẽ
    if alternating_count >= 8:
        return "Xỉu" if h[-1] == "Tài" else "Tài"

    return None


# 126. Thuật toán Cầu Lặp - Phát hiện chuỗi lặp
def algo_cau_lap_nang_cao(h):
    if len(h) < 20: return None

    # Tìm pattern lặp 4 phiên
    last_4 = h[-4:]

    for i in range(len(h) - 8, 0, -1):
        if h[i:i + 4] == last_4:
            # Tìm thấy pattern lặp, xem kết quả tiếp theo
            if i + 4 < len(h):
                next_result = h[i + 4]
                return next_result

    return None


# 127. Thuật toán Kép Xỉu Chẵn - Bẻ Tài
def algo_kep_xiu_chan(h):
    if len(h) < 8: return None

    recent = h[-8:]

    # Đếm số cặp Xỉu
    xiu_pairs = 0
    i = 0
    while i < len(recent) - 1:
        if recent[i] == recent[i + 1] == "Xỉu":
            xiu_pairs += 1
            i += 2
        else:
            i += 1

    # Nếu số cặp Xỉu chẵn (2, 4...), bẻ Tài
    if xiu_pairs > 0 and xiu_pairs % 2 == 0:
        return "Tài"

    return None


# 128. Thuật toán Kép Xỉu Lẻ - Đi Xỉu
def algo_kep_xiu_le(h):
    if len(h) < 8: return None

    recent = h[-8:]

    # Đếm số cặp Xỉu
    xiu_pairs = 0
    i = 0
    while i < len(recent) - 1:
        if recent[i] == recent[i + 1] == "Xỉu":
            xiu_pairs += 1
            i += 2
        else:
            i += 1

    # Nếu số cặp Xỉu lẻ (1, 3, 5...), đi Xỉu
    if xiu_pairs > 0 and xiu_pairs % 2 == 1:
        return "Xỉu"

    return None


# 129. Thuật toán Kép Tài Chẵn - Đi Tài
def algo_kep_tai_chan(h):
    if len(h) < 8: return None

    recent = h[-8:]

    # Đếm số cặp Tài
    tai_pairs = 0
    i = 0
    while i < len(recent) - 1:
        if recent[i] == recent[i + 1] == "Tài":
            tai_pairs += 1
            i += 2
        else:
            i += 1

    # Nếu số cặp Tài chẵn, đi Tài
    if tai_pairs > 0 and tai_pairs % 2 == 0:
        return "Tài"

    return None


# 130. Thuật toán Kép Tài Lẻ - Bẻ Xỉu
def algo_kep_tai_le(h):
    if len(h) < 8: return None

    recent = h[-8:]

    # Đếm số cặp Tài
    tai_pairs = 0
    i = 0
    while i < len(recent) - 1:
        if recent[i] == recent[i + 1] == "Tài":
            tai_pairs += 1
            i += 2
        else:
            i += 1

    # Nếu số cặp Tài lẻ, bẻ Xỉu
    if tai_pairs > 0 and tai_pairs % 2 == 1:
        return "Xỉu"

    return None


# ===== 15 THUẬT TOÁN DỰ ĐOÁN CHÍNH XÁC CAO MỚI =====

# 61. Thuật toán Hidden Markov Model - Phân tích trạng thái ẩn
def algo_hidden_markov(h):
    if len(h) < 30: return None

    # Phân tích 3 trạng thái: cân bằng, thiên Tài, thiên Xỉu
    recent_30 = h[-30:]
    segments = [recent_30[i:i + 10] for i in range(0, 30, 10)]

    states = []
    for seg in segments:
        tai_ratio = seg.count("Tài") / len(seg)
        if tai_ratio > 0.6:
            states.append("tai_heavy")
        elif tai_ratio < 0.4:
            states.append("xiu_heavy")
        else:
            states.append("balanced")

    # Phân tích chuyển đổi trạng thái
    if len(states) == 3:
        # Nếu 2 đoạn liên tiếp cùng thiên về 1 bên, đoạn thứ 3 có xu hướng đảo
        if states[0] == states[1] == "tai_heavy":
            return "Xỉu"
        elif states[0] == states[1] == "xiu_heavy":
            return "Tài"
        # Nếu đang ở trạng thái cân bằng sau khi thiên 1 bên, tiếp tục cân bằng
        elif states[1] == "balanced" and states[2] == "balanced":
            last_5 = h[-5:]
            return "Xỉu" if last_5.count("Tài") >= 3 else "Tài"

    return None


# 62. Thuật toán Deep Pattern Recognition - Nhận diện mẫu sâu
def algo_deep_pattern(h):
    if len(h) < 25: return None

    # Tìm các pattern lặp lại từ 3-7 phiên
    for pattern_len in range(7, 2, -1):
        recent_pattern = h[-pattern_len:]

        # Tìm pattern này trong lịch sử
        matches = 0
        for i in range(len(h) - pattern_len - 1, pattern_len, -1):
            if h[i:i + pattern_len] == recent_pattern:
                matches += 1
                # Nếu tìm thấy pattern, xem kết quả tiếp theo
                if i + pattern_len < len(h):
                    next_result = h[i + pattern_len]
                    if matches >= 2:  # Nếu pattern lặp >= 2 lần
                        return next_result

    return None


# 63. Thuật toán Bayesian Prediction - Dự đoán Bayes
def algo_bayesian(h):
    if len(h) < 20: return None

    recent = h[-20:]

    # Tính xác suất tiên nghiệm
    prior_tai = recent.count("Tài") / len(recent)
    prior_xiu = 1 - prior_tai

    # Phân tích likelihood dựa trên kết quả trước đó
    last_3 = h[-3:]

    # Đếm số lần xuất hiện pattern tương tự trong lịch sử
    tai_after_pattern = 0
    xiu_after_pattern = 0
    total_pattern = 0

    for i in range(len(recent) - 3):
        if recent[i:i + 3] == last_3:
            total_pattern += 1
            if i + 3 < len(recent):
                if recent[i + 3] == "Tài":
                    tai_after_pattern += 1
                else:
                    xiu_after_pattern += 1

    if total_pattern > 0:
        # Tính posterior probability
        likelihood_tai = tai_after_pattern / total_pattern
        likelihood_xiu = xiu_after_pattern / total_pattern

        posterior_tai = likelihood_tai * prior_tai
        posterior_xiu = likelihood_xiu * prior_xiu

        if posterior_tai > posterior_xiu * 1.2:
            return "Tài"
        elif posterior_xiu > posterior_tai * 1.2:
            return "Xỉu"

    return None


# 64. Thuật toán Quantum Probability - Xác suất lượng tử
def algo_quantum_probability(h):
    if len(h) < 15: return None

    recent = h[-15:]

    # Phân tích superposition state - trạng thái chồng chập
    windows = [recent[i:i + 5] for i in range(0, len(recent) - 4, 5)]

    interference_score = 0
    for window in windows:
        tai_count = window.count("Tài")
        # Tính interference pattern
        if tai_count == 2 or tai_count == 3:
            interference_score += 0
        elif tai_count >= 4:
            interference_score += 1
        elif tai_count <= 1:
            interference_score -= 1

    # Collapse wavefunction dựa trên measurement
    if interference_score >= 2:
        return "Xỉu"  # Quá nhiều Tài, collapse sang Xỉu
    elif interference_score <= -2:
        return "Tài"  # Quá nhiều Xỉu, collapse sang Tài

    return None


# 65. Thuật toán Neural Network Simulation - Mô phỏng mạng neural
def algo_neural_network_sim(h):
    if len(h) < 20: return None

    # Input layer: 20 phiên gần nhất
    recent = h[-20:]

    # Hidden layer 1: Phân tích 4 features
    feature1 = recent[-5:].count("Tài") / 5  # Short-term trend
    feature2 = recent[-10:].count("Tài") / 10  # Mid-term trend
    feature3 = sum(1 for i in range(len(recent) - 1) if recent[i] != recent[i + 1]) / (
        len(recent) - 1)  # Volatility

    # Đếm chuỗi dài nhất
    max_streak = 1
    current_streak = 1
    for i in range(len(recent) - 1):
        if recent[i] == recent[i + 1]:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 1
    feature4 = max_streak / len(recent)  # Max streak ratio

    # Hidden layer 2: Weighted combination
    weights = [0.4, 0.3, 0.2, 0.1]
    hidden2 = (feature1 * weights[0] +
               feature2 * weights[1] +
               feature3 * weights[2] +
               feature4 * weights[3])

    # Output layer: Activation function
    if hidden2 > 0.6:
        return "Xỉu"  # Quá nhiều Tài
    elif hidden2 < 0.4:
        return "Tài"  # Quá nhiều Xỉu

    return None


# 66. Thuật toán Fractal Analysis - Phân tích fractal
def algo_fractal(h):
    if len(h) < 30: return None

    # Phân tích self-similarity ở nhiều scales
    scales = [5, 10, 15, 30]
    patterns = []

    for scale in scales:
        if len(h) >= scale:
            segment = h[-scale:]
            tai_ratio = segment.count("Tài") / len(segment)
            patterns.append(tai_ratio)

    # Tính fractal dimension
    if len(patterns) >= 3:
        # Kiểm tra self-similarity
        variance = sum((p - sum(patterns) / len(patterns))**2 for p in patterns) / len(patterns)

        # Nếu variance thấp (self-similar), theo xu hướng
        if variance < 0.02:
            avg_ratio = sum(patterns) / len(patterns)
            if avg_ratio > 0.55:
                return "Xỉu"
            elif avg_ratio < 0.45:
                return "Tài"
        # Nếu variance cao (chaotic), đảo chiều
        elif variance > 0.05:
            last_ratio = patterns[-1]
            if last_ratio > 0.6:
                return "Xỉu"
            elif last_ratio < 0.4:
                return "Tài"

    return None


# 67. Thuật toán Information Entropy - Entropy thông tin
def algo_information_entropy(h):
    if len(h) < 20: return None

    recent = h[-20:]

    # Tính entropy cho từng window 5 phiên
    windows = [recent[i:i + 5] for i in range(0, len(recent) - 4, 5)]
    entropies = []

    for window in windows:
        p_tai = window.count("Tài") / len(window)
        p_xiu = 1 - p_tai

        if p_tai > 0 and p_xiu > 0:
            entropy = -(p_tai * math.log2(p_tai) + p_xiu * math.log2(p_xiu))
            entropies.append(entropy)

    if len(entropies) >= 2:
        # Nếu entropy giảm (trật tự tăng), theo xu hướng
        if entropies[-1] < entropies[0] - 0.2:
            last_window = windows[-1]
            return "Tài" if last_window.count("Tài") >= 3 else "Xỉu"
        # Nếu entropy tăng (hỗn loạn tăng), đảo chiều
        elif entropies[-1] > entropies[0] + 0.2:
            return "Xỉu" if h[-1] == "Tài" else "Tài"

    return None


# 68. Thuật toán Genetic Algorithm - Thuật toán di truyền
def algo_genetic(h):
    if len(h) < 25: return None

    # Tạo nhiều "genes" (strategies) và chọn gene tốt nhất
    recent = h[-25:]

    strategies = []

    # Gene 1: Follow majority
    strategies.append(("majority", "Tài" if recent.count("Tài") > 12 else "Xỉu"))

    # Gene 2: Contrarian
    strategies.append(("contrarian", "Xỉu" if recent.count("Tài") > 15 else "Tài"))

    # Gene 3: Momentum
    last_5 = recent[-5:]
    strategies.append(("momentum", "Tài" if last_5.count("Tài") >= 3 else "Xỉu"))

    # Gene 4: Mean reversion
    tai_ratio = recent.count("Tài") / len(recent)
    strategies.append(("mean_reversion", "Xỉu" if tai_ratio > 0.6 else "Tài"))

    # Fitness function: Đánh giá performance của mỗi gene
    fitness_scores = []
    for name, prediction in strategies:
        # Test trên 15 phiên trước đó
        if len(h) >= 40:
            test_data = h[-40:-25]
            correct = 0
            for i in range(len(test_data) - 1):
                if name == "majority":
                    pred = "Tài" if test_data[:i + 1].count("Tài") > (i + 1) / 2 else "Xỉu"
                elif name == "contrarian":
                    pred = "Xỉu" if test_data[:i + 1].count("Tài") > (i + 1) * 0.6 else "Tài"
                elif name == "momentum":
                    window = test_data[max(0, i - 4):i + 1]
                    pred = "Tài" if window.count("Tài") >= len(window) / 2 else "Xỉu"
                else:  # mean_reversion
                    r = test_data[:i + 1].count("Tài") / (i + 1)
                    pred = "Xỉu" if r > 0.6 else "Tài"

                if i + 1 < len(test_data) and pred == test_data[i + 1]:
                    correct += 1

            fitness_scores.append(correct)

    # Chọn gene có fitness cao nhất
    if fitness_scores:
        best_idx = fitness_scores.index(max(fitness_scores))
        return strategies[best_idx][1]

    return None


# 69. Thuật toán Chaos Theory - Lý thuyết hỗn loạn
def algo_chaos_theory(h):
    if len(h) < 30: return None

    recent = h[-30:]

    # Tính Lyapunov exponent để đo độ hỗn loạn
    deltas = []
    for i in range(len(recent) - 1):
        # Chuyển đổi sang số: Tài=1, Xỉu=0
        val1 = 1 if recent[i] == "Tài" else 0
        val2 = 1 if recent[i + 1] == "Tài" else 0
        deltas.append(abs(val2 - val1))

    chaos_level = sum(deltas) / len(deltas)

    # Phân tích butterfly effect
    last_10 = recent[-10:]
    tai_count = last_10.count("Tài")

    # Nếu chaos cao (nhiều thay đổi)
    if chaos_level > 0.6:
        # Small change leads to big effect
        if tai_count >= 7:
            return "Xỉu"  # Đảo chiều mạnh
        elif tai_count <= 3:
            return "Tài"
    # Nếu chaos thấp (ổn định)
    elif chaos_level < 0.4:
        # Theo xu hướng
        return "Tài" if tai_count >= 5 else "Xỉu"

    return None


# 70. Thuật toán Support Vector Machine - Máy vector hỗ trợ
def algo_svm(h):
    if len(h) < 20: return None

    recent = h[-20:]

    # Tạo features
    features = []
    for i in range(10, len(recent)):
        window = recent[i - 10:i]
        feat = [
            window.count("Tài") / 10,  # Tỷ lệ Tài
            sum(1 for j in range(len(window) - 1) if window[j] != window[j + 1]) /
            9,  # Volatility
            window[-3:].count("Tài") / 3,  # Recent trend
        ]
        features.append(feat)

    if len(features) >= 5:
        # Tính margin từ hyperplane
        last_feature = features[-1]
        avg_feature = [sum(f[i] for f in features[:-1]) / (len(features) - 1) for i in range(3)]

        # Decision function
        weights = [0.5, 0.3, 0.2]
        decision_value = sum((last_feature[i] - avg_feature[i]) * weights[i] for i in range(3))

        # Classification với margin
        if decision_value > 0.15:
            return "Xỉu"  # Quá nhiều Tài
        elif decision_value < -0.15:
            return "Tài"  # Quá nhiều Xỉu

    return None


# 71. Thuật toán Random Forest - Rừng ngẫu nhiên
def algo_random_forest(h):
    if len(h) < 25: return None

    # Tạo nhiều decision trees với random features
    recent = h[-25:]
    predictions = []

    # Tree 1: Dựa trên tỷ lệ Tài/Xỉu
    tai_ratio = recent.count("Tài") / len(recent)
    if tai_ratio > 0.6:
        predictions.append("Xỉu")
    elif tai_ratio < 0.4:
        predictions.append("Tài")

    # Tree 2: Dựa trên streak
    current_streak = 1
    for i in range(len(recent) - 1, -1, -1):
        if recent[i] == recent[-1]:
            current_streak += 1
        else:
            break
    if current_streak >= 4:
        predictions.append("Xỉu" if recent[-1] == "Tài" else "Tài")

    # Tree 3: Dựa trên pattern
    last_5 = recent[-5:]
    if last_5 == ["Tài"] * 5 or last_5 == ["Xỉu"] * 5:
        predictions.append("Xỉu" if last_5[0] == "Tài" else "Tài")

    # Tree 4: Dựa trên volatility
    changes = sum(1 for i in range(len(recent) - 1) if recent[i] != recent[i + 1])
    if changes > 15:  # High volatility
        predictions.append("Xỉu" if recent[-1] == "Tài" else "Tài")
    elif changes < 10:  # Low volatility
        predictions.append(recent[-1])

    # Tree 5: Dựa trên trend
    first_half = recent[:12]
    second_half = recent[12:]
    if first_half.count("Tài") > 8 and second_half.count("Tài") > 8:
        predictions.append("Xỉu")
    elif first_half.count("Xỉu") > 8 and second_half.count("Xỉu") > 8:
        predictions.append("Tài")

    # Voting
    if len(predictions) >= 3:
        tai_votes = predictions.count("Tài")
        xiu_votes = predictions.count("Xỉu")
        if tai_votes > xiu_votes:
            return "Tài"
        elif xiu_votes > tai_votes:
            return "Xỉu"

    return None


# 72. Thuật toán Time Series Decomposition - Phân rã chuỗi thời gian
def algo_time_series_decomposition(h):
    if len(h) < 30: return None

    recent = h[-30:]

    # Chuyển đổi sang số
    numeric = [1 if x == "Tài" else 0 for x in recent]

    # Tách trend, seasonality, residual
    # Trend: Moving average
    window = 6
    trend = []
    for i in range(len(numeric) - window + 1):
        trend.append(sum(numeric[i:i + window]) / window)

    if len(trend) >= 10:
        # Phân tích trend direction
        recent_trend = trend[-5:]
        early_trend = trend[:5]

        avg_recent = sum(recent_trend) / len(recent_trend)
        avg_early = sum(early_trend) / len(early_trend)

        # Nếu trend tăng (nhiều Tài hơn)
        if avg_recent > avg_early + 0.15:
            return "Xỉu"  # Mean reversion
        # Nếu trend giảm (nhiều Xỉu hơn)
        elif avg_recent < avg_early - 0.15:
            return "Tài"
        # Nếu trend stable
        else:
            # Dựa vào residual (noise)
            if avg_recent > 0.6:
                return "Xỉu"
            elif avg_recent < 0.4:
                return "Tài"

    return None


# 73. Thuật toán Ensemble Learning - Học tập tổng hợp
def algo_ensemble(h):
    if len(h) < 20: return None

    # Kết hợp nhiều thuật toán yếu thành 1 thuật toán mạnh
    predictions = []

    # Model 1: Simple majority
    recent = h[-20:]
    predictions.append("Tài" if recent.count("Tài") > 10 else "Xỉu")

    # Model 2: Weighted recent
    last_10 = h[-10:]
    predictions.append("Tài" if last_10.count("Tài") >= 6 else "Xỉu")

    # Model 3: Anti-streak
    streak = 1
    for i in range(len(h) - 2, max(len(h) - 6, -1), -1):
        if h[i] == h[-1]:
            streak += 1
        else:
            break
    if streak >= 3:
        predictions.append("Xỉu" if h[-1] == "Tài" else "Tài")

    # Model 4: Pattern matching
    if len(h) >= 25:
        last_3 = h[-3:]
        for i in range(len(h) - 6, 2, -1):
            if h[i:i + 3] == last_3 and i + 3 < len(h):
                predictions.append(h[i + 3])
                break

    # Model 5: Cycle detection
    if len(h) >= 25:
        windows = [h[i:i + 5] for i in range(len(h) - 20, len(h) - 4, 5)]
        if len(windows) >= 3:
            last_window = windows[-1]
            predictions.append("Tài" if last_window.count("Tài") >= 3 else "Xỉu")

    # Weighted voting với confidence
    if len(predictions) >= 3:
        c = Counter(predictions)
        most_common = c.most_common(1)[0]
        if most_common[1] >= 3:  # Ít nhất 3 models đồng ý
            return most_common[0]

    return None


# 74. Thuật toán Adaptive Boost - Tăng cường thích ứng
def algo_adaptive_boost(h):
    if len(h) < 30: return None

    recent = h[-30:]

    # Tạo weak learners và tăng trọng số cho learners tốt
    learners = []
    weights = []

    # Learner 1: Last result continuation
    learners.append(h[-1])
    # Test accuracy trên 10 phiên trước
    test_correct = sum(1 for i in range(len(recent) - 11, len(recent) - 1) if
                       recent[i] == recent[i + 1])
    weights.append(test_correct / 10)

    # Learner 2: Majority vote
    majority = "Tài" if recent.count("Tài") > 15 else "Xỉu"
    learners.append(majority)
    # Test accuracy
    test_correct = sum(1 for i in range(10, len(recent)) if
                       ("Tài" if recent[:i].count("Tài") > i / 2 else "Xỉu") == recent[i])
    weights.append(test_correct / (len(recent) - 10))

    # Learner 3: Contrarian
    contrarian = "Xỉu" if recent.count("Tài") > 18 else "Tài"
    learners.append(contrarian)
    test_correct = sum(1 for i in range(10, len(recent)) if
                       ("Xỉu" if recent[:i].count("Tài") > i * 0.6 else "Tài") == recent[i])
    weights.append(test_correct / (len(recent) - 10))

    # Normalize weights
    total_weight = sum(weights)
    if total_weight > 0:
        normalized_weights = [w / total_weight for w in weights]

        # Weighted voting
        tai_weight = sum(normalized_weights[i] for i in range(len(learners)) if learners[i] == "Tài")
        xiu_weight = sum(normalized_weights[i] for i in range(len(learners)) if learners[i] == "Xỉu")

        if tai_weight > xiu_weight * 1.2:
            return "Tài"
        elif xiu_weight > tai_weight * 1.2:
            return "Xỉu"

    return None


# 75. Thuật toán Gradient Boosting - Tăng cường gradient
def algo_gradient_boosting(h):
    if len(h) < 25: return None

    recent = h[-25:]

    # Khởi tạo prediction đầu tiên
    initial_pred = "Tài" if recent.count("Tài") > 12 else "Xỉu"

    # Tính residual (sai số)
    residuals = []
    for i in range(10, len(recent)):
        pred = "Tài" if recent[:i].count("Tài") > i / 2 else "Xỉu"
        # Residual = actual - predicted (1 nếu sai, 0 nếu đúng)
        residual = 1 if pred != recent[i] else 0
        residuals.append(residual)

    # Nếu nhiều residual (nhiều sai số), cần điều chỉnh
    avg_residual = sum(residuals) / len(residuals)

    if avg_residual > 0.6:  # Model yếu, cần boost mạnh
        # Áp dụng correction mạnh
        last_10 = recent[-10:]
        if last_10.count("Tài") >= 7:
            return "Xỉu"  # Boost ngược lại
        elif last_10.count("Xỉu") >= 7:
            return "Tài"
    elif avg_residual < 0.4:  # Model tốt
        # Tin tưởng initial prediction
        return initial_pred

    # Medium residual - combine strategies
    last_5 = recent[-5:]
    if last_5.count("Tài") >= 4:
        return "Xỉu"
    elif last_5.count("Xỉu") >= 4:
        return "Tài"

    return None


# ===== 15 THUẬT TOÁN DỰ ĐOÁN CHÍNH XÁC CAO MỚI =====

# 61. Thuật toán Hidden Markov Model - Phân tích trạng thái ẩn
def algo_hidden_markov(h):
    if len(h) < 30: return None

    # Phân tích 3 trạng thái: cân bằng, thiên Tài, thiên Xỉu
    recent_30 = h[-30:]
    segments = [recent_30[i:i + 10] for i in range(0, 30, 10)]

    states = []
    for seg in segments:
        tai_ratio = seg.count("Tài") / len(seg)
        if tai_ratio > 0.6:
            states.append("tai_heavy")
        elif tai_ratio < 0.4:
            states.append("xiu_heavy")
        else:
            states.append("balanced")

    # Phân tích chuyển đổi trạng thái
    if len(states) == 3:
        # Nếu 2 đoạn liên tiếp cùng thiên về 1 bên, đoạn thứ 3 có xu hướng đảo
        if states[0] == states[1] == "tai_heavy":
            return "Xỉu"
        elif states[0] == states[1] == "xiu_heavy":
            return "Tài"
        # Nếu đang ở trạng thái cân bằng sau khi thiên 1 bên, tiếp tục cân bằng
        elif states[1] == "balanced" and states[2] == "balanced":
            last_5 = h[-5:]
            return "Xỉu" if last_5.count("Tài") >= 3 else "Tài"

    return None


# 62. Thuật toán Deep Pattern Recognition - Nhận diện mẫu sâu
def algo_deep_pattern(h):
    if len(h) < 25: return None

    # Tìm các pattern lặp lại từ 3-7 phiên
    for pattern_len in range(7, 2, -1):
        recent_pattern = h[-pattern_len:]

        # Tìm pattern này trong lịch sử
        matches = 0
        for i in range(len(h) - pattern_len - 1, pattern_len, -1):
            if h[i:i + pattern_len] == recent_pattern:
                matches += 1
                # Nếu tìm thấy pattern, xem kết quả tiếp theo
                if i + pattern_len < len(h):
                    next_result = h[i + pattern_len]
                    if matches >= 2:  # Nếu pattern lặp >= 2 lần
                        return next_result

    return None


# 63. Thuật toán Bayesian Prediction - Dự đoán Bayes
def algo_bayesian(h):
    if len(h) < 20: return None

    recent = h[-20:]

    # Tính xác suất tiên nghiệm
    prior_tai = recent.count("Tài") / len(recent)
    prior_xiu = 1 - prior_tai

    # Phân tích likelihood dựa trên kết quả trước đó
    last_3 = h[-3:]

    # Đếm số lần xuất hiện pattern tương tự trong lịch sử
    tai_after_pattern = 0
    xiu_after_pattern = 0
    total_pattern = 0

    for i in range(len(recent) - 3):
        if recent[i:i + 3] == last_3:
            total_pattern += 1
            if i + 3 < len(recent):
                if recent[i + 3] == "Tài":
                    tai_after_pattern += 1
                else:
                    xiu_after_pattern += 1

    if total_pattern > 0:
        # Tính posterior probability
        likelihood_tai = tai_after_pattern / total_pattern
        likelihood_xiu = xiu_after_pattern / total_pattern

        posterior_tai = likelihood_tai * prior_tai
        posterior_xiu = likelihood_xiu * prior_xiu

        if posterior_tai > posterior_xiu * 1.2:
            return "Tài"
        elif posterior_xiu > posterior_tai * 1.2:
            return "Xỉu"

    return None


# 64. Thuật toán Quantum Probability - Xác suất lượng tử
def algo_quantum_probability(h):
    if len(h) < 15: return None

    recent = h[-15:]

    # Phân tích superposition state - trạng thái chồng chập
    windows = [recent[i:i + 5] for i in range(0, len(recent) - 4, 5)]

    interference_score = 0
    for window in windows:
        tai_count = window.count("Tài")
        # Tính interference pattern
        if tai_count == 2 or tai_count == 3:
            interference_score += 0
        elif tai_count >= 4:
            interference_score += 1
        elif tai_count <= 1:
            interference_score -= 1

    # Collapse wavefunction dựa trên measurement
    if interference_score >= 2:
        return "Xỉu"  # Quá nhiều Tài, collapse sang Xỉu
    elif interference_score <= -2:
        return "Tài"  # Quá nhiều Xỉu, collapse sang Tài

    return None


# 65. Thuật toán Neural Network Simulation - Mô phỏng mạng neural
def algo_neural_network_sim(h):
    if len(h) < 20: return None

    # Input layer: 20 phiên gần nhất
    recent = h[-20:]

    # Hidden layer 1: Phân tích 4 features
    feature1 = recent[-5:].count("Tài") / 5  # Short-term trend
    feature2 = recent[-10:].count("Tài") / 10  # Mid-term trend
    feature3 = sum(1 for i in range(len(recent) - 1) if recent[i] != recent[i + 1]) / (
        len(recent) - 1)  # Volatility

    # Đếm chuỗi dài nhất
    max_streak = 1
    current_streak = 1
    for i in range(len(recent) - 1):
        if recent[i] == recent[i + 1]:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 1
    feature4 = max_streak / len(recent)  # Max streak ratio

    # Hidden layer 2: Weighted combination
    weights = [0.4, 0.3, 0.2, 0.1]
    hidden2 = (feature1 * weights[0] +
               feature2 * weights[1] +
               feature3 * weights[2] +
               feature4 * weights[3])

    # Output layer: Activation function
    if hidden2 > 0.6:
        return "Xỉu"  # Quá nhiều Tài
    elif hidden2 < 0.4:
        return "Tài"  # Quá nhiều Xỉu

    return None


# 66. Thuật toán Fractal Analysis - Phân tích fractal
def algo_fractal(h):
    if len(h) < 30: return None

    # Phân tích self-similarity ở nhiều scales
    scales = [5, 10, 15, 30]
    patterns = []

    for scale in scales:
        if len(h) >= scale:
            segment = h[-scale:]
            tai_ratio = segment.count("Tài") / len(segment)
            patterns.append(tai_ratio)

    # Tính fractal dimension
    if len(patterns) >= 3:
        # Kiểm tra self-similarity
        variance = sum((p - sum(patterns) / len(patterns))**2 for p in patterns) / len(patterns)

        # Nếu variance thấp (self-similar), theo xu hướng
        if variance < 0.02:
            avg_ratio = sum(patterns) / len(patterns)
            if avg_ratio > 0.55:
                return "Xỉu"
            elif avg_ratio < 0.45:
                return "Tài"
        # Nếu variance cao (chaotic), đảo chiều
        elif variance > 0.05:
            last_ratio = patterns[-1]
            if last_ratio > 0.6:
                return "Xỉu"
            elif last_ratio < 0.4:
                return "Tài"

    return None


# 67. Thuật toán Information Entropy - Entropy thông tin
def algo_information_entropy(h):
    if len(h) < 20: return None

    recent = h[-20:]

    # Tính entropy cho từng window 5 phiên
    windows = [recent[i:i + 5] for i in range(0, len(recent) - 4, 5)]
    entropies = []

    for window in windows:
        p_tai = window.count("Tài") / len(window)
        p_xiu = 1 - p_tai

        if p_tai > 0 and p_xiu > 0:
            entropy = -(p_tai * math.log2(p_tai) + p_xiu * math.log2(p_xiu))
            entropies.append(entropy)

    if len(entropies) >= 2:
        # Nếu entropy giảm (trật tự tăng), theo xu hướng
        if entropies[-1] < entropies[0] - 0.2:
            last_window = windows[-1]
            return "Tài" if last_window.count("Tài") >= 3 else "Xỉu"
        # Nếu entropy tăng (hỗn loạn tăng), đảo chiều
        elif entropies[-1] > entropies[0] + 0.2:
            return "Xỉu" if h[-1] == "Tài" else "Tài"

    return None


# 68. Thuật toán Genetic Algorithm - Thuật toán di truyền
def algo_genetic(h):
    if len(h) < 25: return None

    # Tạo nhiều "genes" (strategies) và chọn gene tốt nhất
    recent = h[-25:]

    strategies = []

    # Gene 1: Follow majority
    strategies.append(("majority", "Tài" if recent.count("Tài") > 12 else "Xỉu"))

    # Gene 2: Contrarian
    strategies.append(("contrarian", "Xỉu" if recent.count("Tài") > 15 else "Tài"))

    # Gene 3: Momentum
    last_5 = recent[-5:]
    strategies.append(("momentum", "Tài" if last_5.count("Tài") >= 3 else "Xỉu"))

    # Gene 4: Mean reversion
    tai_ratio = recent.count("Tài") / len(recent)
    strategies.append(("mean_reversion", "Xỉu" if tai_ratio > 0.6 else "Tài"))

    # Fitness function: Đánh giá performance của mỗi gene
    fitness_scores = []
    for name, prediction in strategies:
        # Test trên 15 phiên trước đó
        if len(h) >= 40:
            test_data = h[-40:-25]
            correct = 0
            for i in range(len(test_data) - 1):
                if name == "majority":
                    pred = "Tài" if test_data[:i + 1].count("Tài") > (i + 1) / 2 else "Xỉu"
                elif name == "contrarian":
                    pred = "Xỉu" if test_data[:i + 1].count("Tài") > (i + 1) * 0.6 else "Tài"
                elif name == "momentum":
                    window = test_data[max(0, i - 4):i + 1]
                    pred = "Tài" if window.count("Tài") >= len(window) / 2 else "Xỉu"
                else:  # mean_reversion
                    r = test_data[:i + 1].count("Tài") / (i + 1)
                    pred = "Xỉu" if r > 0.6 else "Tài"

                if i + 1 < len(test_data) and pred == test_data[i + 1]:
                    correct += 1

            fitness_scores.append(correct)

    # Chọn gene có fitness cao nhất
    if fitness_scores:
        best_idx = fitness_scores.index(max(fitness_scores))
        return strategies[best_idx][1]

    return None


# 69. Thuật toán Chaos Theory - Lý thuyết hỗn loạn
def algo_chaos_theory(h):
    if len(h) < 30: return None

    recent = h[-30:]

    # Tính Lyapunov exponent để đo độ hỗn loạn
    deltas = []
    for i in range(len(recent) - 1):
        # Chuyển đổi sang số: Tài=1, Xỉu=0
        val1 = 1 if recent[i] == "Tài" else 0
        val2 = 1 if recent[i + 1] == "Tài" else 0
        deltas.append(abs(val2 - val1))

    chaos_level = sum(deltas) / len(deltas)

    # Phân tích butterfly effect
    last_10 = recent[-10:]
    tai_count = last_10.count("Tài")

    # Nếu chaos cao (nhiều thay đổi)
    if chaos_level > 0.6:
        # Small change leads to big effect
        if tai_count >= 7:
            return "Xỉu"  # Đảo chiều mạnh
        elif tai_count <= 3:
            return "Tài"
    # Nếu chaos thấp (ổn định)
    elif chaos_level < 0.4:
        # Theo xu hướng
        return "Tài" if tai_count >= 5 else "Xỉu"

    return None


# 70. Thuật toán Support Vector Machine - Máy vector hỗ trợ
def algo_svm(h):
    if len(h) < 20: return None

    recent = h[-20:]

    # Tạo features
    features = []
    for i in range(10, len(recent)):
        window = recent[i - 10:i]
        feat = [
            window.count("Tài") / 10,  # Tỷ lệ Tài
            sum(1 for j in range(len(window) - 1) if window[j] != window[j + 1]) /
            9,  # Volatility
            window[-3:].count("Tài") / 3,  # Recent trend
        ]
        features.append(feat)

    if len(features) >= 5:
        # Tính margin từ hyperplane
        last_feature = features[-1]
        avg_feature = [sum(f[i] for f in features[:-1]) / (len(features) - 1) for i in range(3)]

        # Decision function
        weights = [0.5, 0.3, 0.2]
        decision_value = sum((last_feature[i] - avg_feature[i]) * weights[i] for i in range(3))

        # Classification với margin
        if decision_value > 0.15:
            return "Xỉu"  # Quá nhiều Tài
        elif decision_value < -0.15:
            return "Tài"  # Quá nhiều Xỉu

    return None


# 71. Thuật toán Random Forest - Rừng ngẫu nhiên
def algo_random_forest(h):
    if len(h) < 25: return None

    # Tạo nhiều decision trees với random features
    recent = h[-25:]
    predictions = []

    # Tree 1: Dựa trên tỷ lệ Tài/Xỉu
    tai_ratio = recent.count("Tài") / len(recent)
    if tai_ratio > 0.6:
        predictions.append("Xỉu")
    elif tai_ratio < 0.4:
        predictions.append("Tài")

    # Tree 2: Dựa trên streak
    current_streak = 1
    for i in range(len(recent) - 1, -1, -1):
        if recent[i] == recent[-1]:
            current_streak += 1
        else:
            break
    if current_streak >= 4:
        predictions.append("Xỉu" if recent[-1] == "Tài" else "Tài")

    # Tree 3: Dựa trên pattern
    last_5 = recent[-5:]
    if last_5 == ["Tài"] * 5 or last_5 == ["Xỉu"] * 5:
        predictions.append("Xỉu" if last_5[0] == "Tài" else "Tài")

    # Tree 4: Dựa trên volatility
    changes = sum(1 for i in range(len(recent) - 1) if recent[i] != recent[i + 1])
    if changes > 15:  # High volatility
        predictions.append("Xỉu" if recent[-1] == "Tài" else "Tài")
    elif changes < 10:  # Low volatility
        predictions.append(recent[-1])

    # Tree 5: Dựa trên trend
    first_half = recent[:12]
    second_half = recent[12:]
    if first_half.count("Tài") > 8 and second_half.count("Tài") > 8:
        predictions.append("Xỉu")
    elif first_half.count("Xỉu") > 8 and second_half.count("Xỉu") > 8:
        predictions.append("Tài")

    # Voting
    if len(predictions) >= 3:
        tai_votes = predictions.count("Tài")
        xiu_votes = predictions.count("Xỉu")
        if tai_votes > xiu_votes:
            return "Tài"
        elif xiu_votes > tai_votes:
            return "Xỉu"

    return None


# 72. Thuật toán Time Series Decomposition - Phân rã chuỗi thời gian
def algo_time_series_decomposition(h):
    if len(h) < 30: return None

    recent = h[-30:]

    # Chuyển đổi sang số
    numeric = [1 if x == "Tài" else 0 for x in recent]

    # Tách trend, seasonality, residual
    # Trend: Moving average
    window = 6
    trend = []
    for i in range(len(numeric) - window + 1):
        trend.append(sum(numeric[i:i + window]) / window)

    if len(trend) >= 10:
        # Phân tích trend direction
        recent_trend = trend[-5:]
        early_trend = trend[:5]

        avg_recent = sum(recent_trend) / len(recent_trend)
        avg_early = sum(early_trend) / len(early_trend)

        # Nếu trend tăng (nhiều Tài hơn)
        if avg_recent > avg_early + 0.15:
            return "Xỉu"  # Mean reversion
        # Nếu trend giảm (nhiều Xỉu hơn)
        elif avg_recent < avg_early - 0.15:
            return "Tài"
        # Nếu trend stable
        else:
            # Dựa vào residual (noise)
            if avg_recent > 0.6:
                return "Xỉu"
            elif avg_recent < 0.4:
                return "Tài"

    return None


# 73. Thuật toán Ensemble Learning - Học tập tổng hợp
def algo_ensemble(h):
    if len(h) < 20: return None

    # Kết hợp nhiều thuật toán yếu thành 1 thuật toán mạnh
    predictions = []

    # Model 1: Simple majority
    recent = h[-20:]
    predictions.append("Tài" if recent.count("Tài") > 10 else "Xỉu")

    # Model 2: Weighted recent
    last_10 = h[-10:]
    predictions.append("Tài" if last_10.count("Tài") >= 6 else "Xỉu")

    # Model 3: Anti-streak
    streak = 1
    for i in range(len(h) - 2, max(len(h) - 6, -1), -1):
        if h[i] == h[-1]:
            streak += 1
        else:
            break
    if streak >= 3:
        predictions.append("Xỉu" if h[-1] == "Tài" else "Tài")

    # Model 4: Pattern matching
    if len(h) >= 25:
        last_3 = h[-3:]
        for i in range(len(h) - 6, 2, -1):
            if h[i:i + 3] == last_3 and i + 3 < len(h):
                predictions.append(h[i + 3])
                break

    # Model 5: Cycle detection
    if len(h) >= 25:
        windows = [h[i:i + 5] for i in range(len(h) - 20, len(h) - 4, 5)]
        if len(windows) >= 3:
            last_window = windows[-1]
            predictions.append("Tài" if last_window.count("Tài") >= 3 else "Xỉu")

    # Weighted voting với confidence
    if len(predictions) >= 3:
        c = Counter(predictions)
        most_common = c.most_common(1)[0]
        if most_common[1] >= 3:  # Ít nhất 3 models đồng ý
            return most_common[0]

    return None


# 74. Thuật toán Adaptive Boost - Tăng cường thích ứng
def algo_adaptive_boost(h):
    if len(h) < 30: return None

    recent = h[-30:]

    # Tạo weak learners và tăng trọng số cho learners tốt
    learners = []
    weights = []

    # Learner 1: Last result continuation
    learners.append(h[-1])
    # Test accuracy trên 10 phiên trước
    test_correct = sum(1 for i in range(len(recent) - 11, len(recent) - 1) if
                       recent[i] == recent[i + 1])
    weights.append(test_correct / 10)

    # Learner 2: Majority vote
    majority = "Tài" if recent.count("Tài") > 15 else "Xỉu"
    learners.append(majority)
    # Test accuracy
    test_correct = sum(1 for i in range(10, len(recent)) if
                       ("Tài" if recent[:i].count("Tài") > i / 2 else "Xỉu") == recent[i])
    weights.append(test_correct / (len(recent) - 10))

    # Learner 3: Contrarian
    contrarian = "Xỉu" if recent.count("Tài") > 18 else "Tài"
    learners.append(contrarian)
    test_correct = sum(1 for i in range(10, len(recent)) if
                       ("Xỉu" if recent[:i].count("Tài") > i * 0.6 else "Tài") == recent[i])
    weights.append(test_correct / (len(recent) - 10))

    # Normalize weights
    total_weight = sum(weights)
    if total_weight > 0:
        normalized_weights = [w / total_weight for w in weights]

        # Weighted voting
        tai_weight = sum(normalized_weights[i] for i in range(len(learners)) if learners[i] == "Tài")
        xiu_weight = sum(normalized_weights[i] for i in range(len(learners)) if learners[i] == "Xỉu")

        if tai_weight > xiu_weight * 1.2:
            return "Tài"
        elif xiu_weight > tai_weight * 1.2:
            return "Xỉu"

    return None


# 75. Thuật toán Gradient Boosting - Tăng cường gradient
def algo_gradient_boosting(h):
    if len(h) < 25: return None

    recent = h[-25:]

    # Khởi tạo prediction đầu tiên
    initial_pred = "Tài" if recent.count("Tài") > 12 else "Xỉu"

    # Tính residual (sai số)
    residuals = []
    for i in range(10, len(recent)):
        pred = "Tài" if recent[:i].count("Tài") > i / 2 else "Xỉu"
        # Residual = actual - predicted (1 nếu sai, 0 nếu đúng)
        residual = 1 if pred != recent[i] else 0
        residuals.append(residual)

    # Nếu nhiều residual (nhiều sai số), cần điều chỉnh
    avg_residual = sum(residuals) / len(residuals)

    if avg_residual > 0.6:  # Model yếu, cần boost mạnh
        # Áp dụng correction mạnh
        last_10 = recent[-10:]
        if last_10.count("Tài") >= 7:
            return "Xỉu"  # Boost ngược lại
        elif last_10.count("Xỉu") >= 7:
            return "Tài"
    elif avg_residual < 0.4:  # Model tốt
        # Tin tưởng initial prediction
        return initial_pred

    # Medium residual - combine strategies
    last_5 = recent[-5:]
    if last_5.count("Tài") >= 4:
        return "Xỉu"
    elif last_5.count("Xỉu") >= 4:
        return "Tài"

    return None


# ===== THUẬT TOÁN TỪ BOT LUCK8 =====

# Thuật toán Markov cho Luck8
def algo_luck8_markov(h):
    if len(h) < 5: return None
    pairs = Counter((h[i], h[i+1]) for i in range(len(h)-1))
    last = h[-1]
    tai_next = pairs.get((last, "Tài"), 0)
    xiu_next = pairs.get((last, "Xỉu"), 0)
    total = tai_next + xiu_next
    if total == 0: return None
    return "Tài" if tai_next > xiu_next else "Xỉu"

# Thuật toán Weighted History cho Luck8
def algo_luck8_weighted(h):
    if not h: return None
    w_t, w_x = 0, 0
    n = min(20, len(h))
    for i in range(1, n+1):
        if h[-i] == "Tài": 
            w_t += i
        else: 
            w_x += i
    return "Tài" if w_t > w_x else "Xỉu"

# Thuật toán Bias (dựa trên tổng xúc xắc)
def algo_luck8_bias(totals):
    if len(totals) < 8: return None
    avg = sum(list(totals)[-8:]) / 8
    if avg >= 15: return "Tài"
    if avg <= 10: return "Xỉu"
    return None

# Thuật toán Streak cho Luck8
def algo_luck8_streak(h):
    if len(h) < 4: return None
    last, streak = h[-1], 1
    for i in range(len(h)-2, -1, -1):
        if h[i] == last: 
            streak += 1
        else: 
            break
    if streak >= 4: 
        return last
    return None

# Thuật toán Momentum cho Luck8
def algo_luck8_momentum(h):
    if len(h) < 6: return None
    last6 = list(h)[-6:]
    if last6.count("Tài") >= 5: return "Tài"
    if last6.count("Xỉu") >= 5: return "Xỉu"
    return None

# Thuật toán Cycle cho Luck8
def algo_luck8_cycle(h):
    L = len(h)
    for cycle_len in range(2, 5):
        if L >= cycle_len*2:
            if h[-cycle_len:] == h[-2*cycle_len:-cycle_len]:
                return h[-cycle_len]
    return None

# Thuật toán Balance cho Luck8
def algo_luck8_balance(h):
    if len(h) < 10: return None
    last10 = list(h)[-10:]
    tai_count = last10.count("Tài")
    xiu_count = last10.count("Xỉu")
    if tai_count >= 7: return "Xỉu"
    if xiu_count >= 7: return "Tài"
    return None

# Thuật toán Alternating cho Luck8
def algo_luck8_alt(h):
    if len(h) < 5: return None
    last5 = list(h)[-5:]
    if all(x == last5[0] for x in last5):
        return "Xỉu" if last5[0] == "Tài" else "Tài"
    return None

# Thuật toán Even Balance cho Luck8
def algo_luck8_even_balance(totals):
    if len(totals) < 10: return None
    avg = sum(totals) / len(totals)
    if avg >= 14: return "Xỉu"
    if avg <= 10: return "Tài"
    return None

# Thuật toán Mix Balance cho Luck8
def algo_luck8_mix_balance(h):
    if len(h) < 15: return None
    last15 = list(h)[-15:]
    tai = last15.count("Tài")
    xiu = last15.count("Xỉu")
    if tai >= xiu * 2: return "Xỉu"
    if xiu >= tai * 2: return "Tài"
    return None

# Thuật toán Randomize (chống bias)
def algo_luck8_randomize(votes):
    if not votes: return None
    if votes.count("Tài") >= len(votes) * 0.8:
        return "Xỉu"
    if votes.count("Xỉu") >= len(votes) * 0.8:
        return "Tài"
    return None

# ===== THUẬT TOÁN NÂNG CAO TỪ JAVASCRIPT =====

# 111. Thuật toán Phát hiện Chuỗi và Bẻ Cầu (detectStreakAndBreak)
def algo_detect_streak_and_break(h):
    if len(h) == 0:
        return None

    streak = 1
    current_result = h[-1]

    for i in range(len(h) - 2, -1, -1):
        if h[i] == current_result:
            streak += 1
        else:
            break

    last15 = h[-15:] if len(h) >= 15 else h
    if not last15:
        return None

    # Đếm số lần chuyển đổi
    switches = sum(1 for i in range(len(last15) - 1) if last15[i] != last15[i + 1])

    tai_count = last15.count("Tài")
    xiu_count = last15.count("Xỉu")
    imbalance = abs(tai_count - xiu_count) / len(last15)

    break_prob = 0

    if streak >= 8:
        break_prob = min(0.6 + switches / 15 + imbalance * 0.15, 0.9)
    elif streak >= 5:
        break_prob = min(0.35 + switches / 10 + imbalance * 0.25, 0.85)
    elif streak >= 3 and switches >= 7:
        break_prob = 0.3

    # Nếu xác suất bẻ cầu cao, dự đoán đảo chiều
    if break_prob > 0.65:
        return "Xỉu" if current_result == "Tài" else "Tài"

    return None


# 112. Thuật toán Bẻ Cầu Thông Minh (smartBridgeBreak)
def algo_smart_bridge_break(h):
    if len(h) < 3:
        return None

    # Phát hiện chuỗi
    streak = 1
    current_result = h[-1]

    for i in range(len(h) - 2, -1, -1):
        if h[i] == current_result:
            streak += 1
        else:
            break

    last20 = h[-20:] if len(h) >= 20 else h

    # Tính điểm trung bình (giả sử có score)
    avg_score = 9  # Giá trị mặc định
    score_deviation = 2

    last5 = last20[-5:]

    # Đếm các mẫu 3 phiên
    pattern_counts = {}
    for i in range(len(last20) - 2):
        pattern = ','.join(last20[i:i+3])
        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

    has_repeating_pattern = any(count >= 3 for count in pattern_counts.values())

    break_prob = 0

    if streak >= 6:
        break_prob = min(break_prob + 0.15, 0.9)
        return "Xỉu" if current_result == "Tài" else "Tài"
    elif streak >= 4 and score_deviation > 3:
        break_prob = min(break_prob + 0.1, 0.85)
        return "Xỉu" if current_result == "Tài" else "Tài"
    elif has_repeating_pattern and all(r == current_result for r in last5):
        break_prob = min(break_prob + 0.05, 0.8)
        return "Xỉu" if current_result == "Tài" else "Tài"

    return None


# 113. Thuật toán Xu Hướng và Xác Suất (trendAndProb)
def algo_trend_and_prob(h):
    if len(h) < 3:
        return None

    # Kiểm tra chuỗi
    streak = 1
    current_result = h[-1]

    for i in range(len(h) - 2, -1, -1):
        if h[i] == current_result:
            streak += 1
        else:
            break

    if streak >= 5:
        # Xác suất bẻ cầu cao
        last15 = h[-15:] if len(h) >= 15 else h
        switches = sum(1 for i in range(len(last15) - 1) if last15[i] != last15[i + 1])

        if switches > 10:
            return "Xỉu" if current_result == "Tài" else "Tài"
        return current_result

    last15 = h[-15:] if len(h) >= 15 else h

    # Tính trọng số
    tai_weight = 0
    xiu_weight = 0

    for i, result in enumerate(last15):
        weight = pow(1.2, i)
        if result == "Tài":
            tai_weight += weight
        else:
            xiu_weight += weight

    total_weight = tai_weight + xiu_weight

    # Phát hiện mẫu
    last10 = last15[-10:] if len(last15) >= 10 else last15

    if len(last10) >= 4:
        patterns = []
        for i in range(len(last10) - 3):
            patterns.append(','.join(last10[i:i+4]))

        pattern_counts = {}
        for pattern in patterns:
            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

        most_common = max(pattern_counts.items(), key=lambda x: x[1]) if pattern_counts else None

        if most_common and most_common[1] >= 3:
            pattern_parts = most_common[0].split(',')
            if pattern_parts[-1] != last10[-1]:
                return "Tài"
            else:
                return "Xỉu"

    if total_weight > 0 and abs(tai_weight - xiu_weight) / total_weight >= 0.25:
        return "Xỉu" if tai_weight > xiu_weight else "Tài"

    return "Tài" if last15[-1] == "Xỉu" else "Xỉu"


# 114. Thuật toán Mẫu Ngắn (shortPattern)
def algo_short_pattern(h):
    if len(h) < 3:
        return None

    # Kiểm tra chuỗi
    streak = 1
    current_result = h[-1]

    for i in range(len(h) - 2, -1, -1):
        if h[i] == current_result:
            streak += 1
        else:
            break

    if streak >= 4:
        # Xác suất bẻ cầu
        return "Xỉu" if current_result == "Tài" else "Tài"

    last8 = h[-8:]

    # Phát hiện mẫu 3 phiên
    patterns = []
    for i in range(len(last8) - 2):
        patterns.append(','.join(last8[i:i+3]))

    pattern_counts = {}
    for pattern in patterns:
        pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

    most_common = max(pattern_counts.items(), key=lambda x: x[1]) if pattern_counts else None

    if most_common and most_common[1] >= 2:
        pattern_parts = most_common[0].split(',')
        if pattern_parts[-1] != last8[-1]:
            return "Tài"
        else:
            return "Xỉu"

    return "Tài" if last8[-1] == "Xỉu" else "Xỉu"


# 115. Thuật toán Độ Lệch Trung Bình (meanDeviation)
def algo_mean_deviation(h):
    if len(h) < 3:
        return None

    streak = 1
    current_result = h[-1]

    for i in range(len(h) - 2, -1, -1):
        if h[i] == current_result:
            streak += 1
        else:
            break

    if streak >= 4:
        return "Xỉu" if current_result == "Tài" else "Tài"

    last12 = h[-12:]

    tai_count = last12.count("Tài")
    xiu_count = len(last12) - tai_count
    imbalance = abs(tai_count - xiu_count) / len(last12)

    if imbalance < 0.35:
        return "Tài" if last12[-1] == "Xỉu" else "Xỉu"

    return "Tài" if xiu_count > tai_count else "Xỉu"


# 116. Thuật toán Chuyển Đổi Gần Đây (recentSwitch)
def algo_recent_switch(h):
    if len(h) < 3:
        return None

    streak = 1
    current_result = h[-1]

    for i in range(len(h) - 2, -1, -1):
        if h[i] == current_result:
            streak += 1
        else:
            break

    if streak >= 4:
        return "Xỉu" if current_result == "Tài" else "Tài"

    last10 = h[-10:]

    switches = sum(1 for i in range(len(last10) - 1) if last10[i] != last10[i + 1])

    if switches >= 6:
        return "Tài" if last10[-1] == "Xỉu" else "Xỉu"

    return "Tài" if last10[-1] == "Xỉu" else "Xỉu"


# 117. Thuật toán AI HTDD Logic
def algo_ai_htdd_logic(h):
    if len(h) < 3:
        return None

    last5 = h[-5:]
    tai_count = last5.count("Tài")
    xiu_count = last5.count("Xỉu")

    # Kiểm tra mẫu 1T1X
    if len(h) >= 3:
        last3 = h[-3:]
        if last3 == ["Tài", "Xỉu", "Tài"]:
            return "Xỉu"
        elif last3 == ["Xỉu", "Tài", "Xỉu"]:
            return "Tài"

    # Kiểm tra mẫu 2T2X
    if len(h) >= 4:
        last4 = h[-4:]
        if last4 == ["Tài", "Tài", "Xỉu", "Xỉu"]:
            return "Tài"
        elif last4 == ["Xỉu", "Xỉu", "Tài", "Tài"]:
            return "Xỉu"

    # Kiểm tra chuỗi dài
    if len(h) >= 9:
        if all(r == "Tài" for r in h[-6:]):
            return "Xỉu"
        elif all(r == "Xỉu" for r in h[-6:]):
            return "Tài"

    # Phân tích tổng thể
    if tai_count > xiu_count + 1:
        return "Xỉu"
    elif xiu_count > tai_count + 1:
        return "Tài"
    else:
        total_tai = h.count("Tài")
        total_xiu = h.count("Xỉu")

        if total_tai > total_xiu + 2:
            return "Xỉu"
        elif total_xiu > total_tai + 2:
            return "Tài"

    return None


# Lưu trữ lịch sử và thống kê (maxlen tăng lên 10000 cho cấp Huyền Thoại)

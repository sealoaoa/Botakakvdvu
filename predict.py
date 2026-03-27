# -*- coding: utf-8 -*-
# ================== predict.py ==================
# Hàm analyze, predict, lưu/tải lịch sử

import os, json, time, random
from collections import deque
from datetime import datetime
from config import DATA_FILE, _BASE_DIR
from algorithms import *

# Đường dẫn các file lịch sử
HISTORY_FILE     = os.path.join(_BASE_DIR, "history.json")
PRED_HISTORY_FILE = os.path.join(_BASE_DIR, "prediction_history.json")
CAU_HISTORY_FILE  = os.path.join(_BASE_DIR, "cau_history.json")
HIST = {
    "sun": deque(maxlen=10000),
    "hit": deque(maxlen=10000),
    "sum": deque(maxlen=10000),
    "b52": deque(maxlen=10000),
    "luck8": deque(maxlen=30),  # Luck8 chỉ giữ 30 phiên để tự động reset
    "sicbo": deque(maxlen=10000),
    "789": deque(maxlen=10000),
    "68gb": deque(maxlen=10000),
    "lc79": deque(maxlen=10000),
    "sexy": deque(maxlen=10000)
}

# Lưu trữ tổng xúc xắc cho Luck8 và Sicbo
LUCK8_TOTALS = deque(maxlen=30)
SICBO_TOTALS = deque(maxlen=30)

# Lưu trữ lịch sử dự đoán chi tiết
PREDICTION_HISTORY = {
    "sun": deque(maxlen=10),
    "hit": deque(maxlen=10),
    "sum": deque(maxlen=10),
    "b52": deque(maxlen=10),
    "luck8": deque(maxlen=10),
    "sicbo": deque(maxlen=10),
    "789": deque(maxlen=10),
    "68gb": deque(maxlen=10),
    "lc79": deque(maxlen=10),
    "sexy": deque(maxlen=10)
}

STATS = {
    "sun": {
        "correct": 0,
        "total": 0
    },
    "hit": {
        "correct": 0,
        "total": 0
    },
    "sum": {
        "correct": 0,
        "total": 0
    },
    "b52": {
        "correct": 0,
        "total": 0
    },
    "luck8": {
        "correct": 0,
        "total": 0
    },
    "sicbo": {
        "correct": 0,
        "total": 0
    },
    "789": {
        "correct": 0,
        "total": 0
    },
    "68gb": {
        "correct": 0,
        "total": 0
    },
    "lc79": {
        "correct": 0,
        "total": 0
    },
    "sexy": {
        "correct": 0,
        "total": 0
    }
}

# Lưu trữ lịch sử cầu chi tiết cho từng game
CAU_HISTORY = {
    "sun": {"don": [], "kep": [], "dai": [], "xien": [], "lung": []},
    "hit": {"don": [], "kep": [], "dai": [], "xien": [], "lung": []},
    "sum": {"don": [], "kep": [], "dai": [], "xien": [], "lung": []},
    "b52": {"don": [], "kep": [], "dai": [], "xien": [], "lung": []},
    "luck8": {"don": [], "kep": [], "dai": [], "xien": [], "lung": []},
    "sicbo": {"don": [], "kep": [], "dai": [], "xien": [], "lung": []},
    "789": {"don": [], "kep": [], "dai": [], "xien": [], "lung": []},
    "68gb": {"don": [], "kep": [], "dai": [], "xien": [], "lung": []},
    "lc79": {"don": [], "kep": [], "dai": [], "xien": [], "lung": []},
    "sexy": {"don": [], "kep": [], "dai": [], "xien": [], "lung": []}
}

# Hàm phân tích và lưu pattern cầu
def analyze_and_save_cau_patterns(h, game_type):
    """Phân tích và lưu các pattern cầu từ lịch sử"""
    if len(h) < 3:
        return

    patterns = {"don": [], "kep": [], "dai": [], "xien": [], "lung": []}

    i = 0
    while i < len(h):
        current = h[i]
        streak_count = 1

        # Đếm chuỗi liên tiếp
        while i + streak_count < len(h) and h[i + streak_count] == current:
            streak_count += 1

        # Phân loại cầu
        if streak_count == 1:
            patterns["don"].append({"value": current, "pos": i, "time": time.time()})
        elif streak_count == 2:
            patterns["kep"].append({"value": current, "pos": i, "count": 2, "time": time.time()})
        elif streak_count >= 3:
            patterns["dai"].append({"value": current, "pos": i, "count": streak_count, "time": time.time()})

        i += streak_count

    # Phát hiện cầu xên kẽ
    for i in range(len(h) - 3):
        if h[i] != h[i + 1] and h[i + 1] != h[i + 2] and h[i + 2] != h[i + 3]:
            patterns["xien"].append({"start_pos": i, "length": 4, "time": time.time()})

    # Phát hiện cầu lửng (A-B-A pattern)
    for i in range(len(h) - 2):
        if h[i] == h[i + 2] and h[i] != h[i + 1]:
            patterns["lung"].append({"value": h[i], "pos": i, "time": time.time()})

    # Lưu vào history (giữ 50 pattern gần nhất mỗi loại)
    for key in patterns:
        CAU_HISTORY[game_type][key].extend(patterns[key])
        CAU_HISTORY[game_type][key] = CAU_HISTORY[game_type][key][-50:]

    save_cau_history()

# Hàm lưu lịch sử cầu
def save_cau_history():
    try:
        with open(CAU_HISTORY_FILE, "w") as f:
            json.dump(CAU_HISTORY, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Lỗi lưu lịch sử cầu: {e}")

# Hàm tải lịch sử cầu
def load_cau_history():
    try:
        if os.path.exists(CAU_HISTORY_FILE):
            with open(CAU_HISTORY_FILE) as f:
                data = json.load(f)
                for game in ["sun", "hit", "sum", "b52", "luck8", "sicbo", "789", "68gb", "lc79", "sexy"]:
                    if game in data:
                        CAU_HISTORY[game] = data[game]
    except Exception as e:
        print(f"Lỗi tải lịch sử cầu: {e}")

# Hàm lưu lịch sử tự động
def save_history():
    try:
        history_data = {
            "sun": list(HIST["sun"]),
            "hit": list(HIST["hit"]),
            "sum": list(HIST["sum"]),
            "b52": list(HIST["b52"]),
            "luck8": list(HIST["luck8"]),
            "sicbo": list(HIST["sicbo"]),
            "789": list(HIST["789"]),
            "68gb": list(HIST["68gb"]),
            "lc79": list(HIST["lc79"]),
            "sexy": list(HIST["sexy"]),
            "stats": STATS,
            "last_update": time.time()
        }
        with open(HISTORY_FILE, "w") as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Lỗi lưu lịch sử: {e}")


# Hàm tải lịch sử
def load_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE) as f:
                data = json.load(f)
                for game in ["sun", "hit", "sum", "b52", "luck8", "sicbo", "789", "68gb", "lc79", "sexy"]:
                    maxlen = 30 if game == "luck8" else 10000
                    HIST[game] = deque(data.get(game, []), maxlen=maxlen)
                    if game in data.get("stats", {}):
                        STATS[game] = data["stats"][game]
    except Exception as e:
        print(f"Lỗi tải lịch sử: {e}")

# Hàm lưu lịch sử dự đoán chi tiết
def save_prediction_history():
    try:
        pred_data = {
            "sun": list(PREDICTION_HISTORY["sun"]),
            "hit": list(PREDICTION_HISTORY["hit"]),
            "sum": list(PREDICTION_HISTORY["sum"]),
            "b52": list(PREDICTION_HISTORY["b52"]),
            "luck8": list(PREDICTION_HISTORY["luck8"]),
            "sicbo": list(PREDICTION_HISTORY["sicbo"]),
            "789": list(PREDICTION_HISTORY["789"]),
            "68gb": list(PREDICTION_HISTORY["68gb"]),
            "lc79": list(PREDICTION_HISTORY["lc79"]),
            "sexy": list(PREDICTION_HISTORY["sexy"]),
            "last_update": time.time()
        }
        with open(PRED_HISTORY_FILE, "w") as f:
            json.dump(pred_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Lỗi lưu lịch sử dự đoán: {e}")

# Hàm tải lịch sử dự đoán
def load_prediction_history():
    try:
        if os.path.exists(PRED_HISTORY_FILE):
            with open(PRED_HISTORY_FILE) as f:
                data = json.load(f)
                for game in ["sun", "hit", "sum", "b52", "luck8", "sicbo", "789", "68gb", "lc79", "sexy"]:
                    PREDICTION_HISTORY[game] = deque(data.get(game, []), maxlen=10)
    except Exception as e:
        print(f"Lỗi tải lịch sử dự đoán: {e}")

# Hàm ghi lại dự đoán để phân tích sau này
def record_prediction(game, session_id, prediction, confidence, actual_result=None):
    try:
        # Kiểm tra session_id hợp lệ
        if not session_id or session_id == "---":
            return

        # Tìm record của phiên này
        existing_record = None
        for r in PREDICTION_HISTORY[game]:
            if r.get("session") == str(session_id):
                existing_record = r
                break

        if existing_record:
            # Cập nhật dự đoán mới nhất nếu chưa có kết quả (Fix lỗi hiển thị sai lịch sử)
            if not existing_record.get("counted") and actual_result is None:
                if existing_record["prediction"] != prediction:
                    existing_record["prediction"] = prediction
                    existing_record["confidence"] = confidence
                    existing_record["last_update"] = time.time()
                    save_prediction_history()

            # Đã có record - cập nhật kết quả nếu có
            if actual_result and actual_result in ["Tài", "Xỉu"]:
                # Chỉ cập nhật nếu chưa có kết quả hoặc kết quả thay đổi
                if existing_record.get("actual") != actual_result:
                    existing_record["actual"] = actual_result
                    existing_record["correct"] = (existing_record["prediction"] == actual_result)
                    existing_record["last_update"] = time.time()

                    # Tính stats nếu chưa tính
                    if not existing_record.get("counted"):
                        STATS[game]["total"] += 1
                        if existing_record["correct"]:
                            STATS[game]["correct"] += 1
                        existing_record["counted"] = True
                        save_history()
                        print(f"📊 {game.upper()}: Phiên #{session_id}: {existing_record['prediction']} → {actual_result} {'✅' if existing_record['correct'] else '❌'}")

                    save_prediction_history()
        else:
            # Tạo record mới
            record = {
                "timestamp": time.time(),
                "last_update": time.time(),
                "session": str(session_id),
                "prediction": prediction,
                "confidence": confidence,
                "actual": actual_result if actual_result in ["Tài", "Xỉu"] else None,
                "correct": (prediction == actual_result) if actual_result in ["Tài", "Xỉu"] else None,
                "counted": False
            }
            PREDICTION_HISTORY[game].append(record)

            # Nếu đã có kết quả, tính stats luôn
            if actual_result and actual_result in ["Tài", "Xỉu"]:
                STATS[game]["total"] += 1
                if prediction == actual_result:
                    STATS[game]["correct"] += 1
                record["counted"] = True
                save_history()
                print(f"📊 {game.upper()}: Phiên #{session_id}: {prediction} → {actual_result} {'✅' if record['correct'] else '❌'}")
            else:
                print(f"📝 {game.upper()}: Dự đoán phiên #{session_id}: {prediction} (độ tin cậy: {confidence:.0%})")

            save_prediction_history()

    except Exception as e:
        print(f"❌ Lỗi ghi dự đoán: {e}")

# Hàm cập nhật kết quả cho các phiên đã dự đoán
def update_prediction_results(game, session_id, actual_result):
    """Cập nhật kết quả thực tế cho phiên đã dự đoán"""
    if not actual_result or actual_result not in ["Tài", "Xỉu"]:
        return

    # Chuyển session_id sang string để so sánh chính xác
    str_session_id = str(session_id)

    for record in PREDICTION_HISTORY[game]:
        if record.get("session") == str_session_id and not record.get("counted"):
            record["actual"] = actual_result
            record["correct"] = (record["prediction"] == actual_result)
            record["last_update"] = time.time()

            # Cập nhật thống kê
            STATS[game]["total"] += 1
            if record["correct"]:
                STATS[game]["correct"] += 1
            record["counted"] = True

            save_history()
            save_prediction_history()
            print(f"📊 {game.upper()}: Cập nhật kết quả phiên #{session_id}: {record['prediction']} → {actual_result} {'✅' if record['correct'] else '❌'}")
            break


# ===== THUẬT TOÁN ENSEMBLE CHO LUCK8 (PHIÊN BẢN TỐI ƯU) =====
def ensemble_predict_luck8(h, totals):
    """Ensemble prediction tối ưu cho Luck8 dựa trên phân tích lịch sử"""

    if len(h) < 2:
        return random.choice(["Tài", "Xỉu"]), 0.50

    # Phân tích đơn giản nhưng hiệu quả
    recent_10 = list(h)[-10:] if len(h) >= 10 else list(h)
    recent_5 = list(h)[-5:] if len(h) >= 5 else list(h)
    last = h[-1]

    # Đếm chuỗi
    streak = 1
    for i in range(len(h)-2, -1, -1):
        if h[i] == last:
            streak += 1
        else:
            break

    tai_10 = recent_10.count("Tài")
    tai_5 = recent_5.count("Tài")

    # LOGIC TỐI ƯU CHO LUCK8:

    # 1. Chuỗi dài >= 5: Bẻ mạnh
    if streak >= 5:
        prediction = "Xỉu" if last == "Tài" else "Tài"
        confidence = 0.70 + (streak - 5) * 0.04
        return prediction, min(confidence, 0.82)

    # 2. Chuỗi 3-4: Bẻ vừa phải
    if 3 <= streak <= 4:
        prediction = "Xỉu" if last == "Tài" else "Tài"
        return prediction, 0.65

    # 3. Xu hướng 5 phiên: Nếu lệch >= 4 cùng loại
    if tai_5 >= 4:
        return "Xỉu", 0.68
    elif tai_5 <= 1:
        return "Tài", 0.68

    # 4. Xu hướng 10 phiên: Hồi về cân bằng
    if tai_10 >= 8:
        return "Xỉu", 0.75
    elif tai_10 <= 2:
        return "Tài", 0.75

    # 5. Phân tích tổng xúc xắc (nếu có)
    if len(totals) >= 8:
        avg_total = sum(list(totals)[-8:]) / 8
        if avg_total >= 15:
            # Tổng cao -> xu hướng Tài -> bẻ Xỉu
            return "Xỉu", 0.62
        elif avg_total <= 10:
            # Tổng thấp -> xu hướng Xỉu -> bẻ Tài
            return "Tài", 0.62

    # 6. Pattern xen kẽ
    if len(h) >= 3 and h[-1] != h[-2] and h[-2] != h[-3]:
        return "Xỉu" if last == "Tài" else "Tài", 0.60

    # 7. Mặc định: Ngược với kết quả cuối
    return "Xỉu" if last == "Tài" else "Tài", 0.56

# Phân tích pattern từ chuỗi pattern của API
def analyze_api_pattern(pattern_str):
    if not pattern_str or len(pattern_str) < 3:
        return None, 0.5

    # Phân tích pattern
    t_count = pattern_str.count('t')
    x_count = pattern_str.count('x')
    total = len(pattern_str)

    if total == 0:
        return None, 0.5

    # Tính tỷ lệ
    t_ratio = t_count / total

    # Phân tích xu hướng
    recent_3 = pattern_str[-3:] if len(pattern_str) >= 3 else pattern_str
    recent_5 = pattern_str[-5:] if len(pattern_str) >= 5 else pattern_str

    # Đếm chuỗi liên tiếp cuối
    last_char = pattern_str[-1]
    streak = 1
    for i in range(len(pattern_str)-2, -1, -1):
        if pattern_str[i] == last_char:
            streak += 1
        else:
            break

    # Logic dự đoán dựa trên pattern
    # 1. Chuỗi dài >= 4: Bẻ ngược
    if streak >= 4:
        prediction = 'x' if last_char == 't' else 't'
        confidence = 0.65 + (streak - 4) * 0.03
        return prediction, min(confidence, 0.78)

    # 2. Xu hướng mạnh trong 5 phiên gần
    t_in_5 = recent_5.count('t')
    if t_in_5 >= 4:
        return 'x', 0.68
    elif t_in_5 <= 1:
        return 't', 0.68

    # 3. Cân bằng tổng thể
    if t_ratio > 0.65:
        return 'x', 0.65
    elif t_ratio < 0.35:
        return 't', 0.65

    # 4. Pattern xen kẽ
    if len(recent_3) == 3 and recent_3[0] != recent_3[1] and recent_3[1] != recent_3[2]:
        prediction = 'x' if last_char == 't' else 't'
        return prediction, 0.62

    # Mặc định: ngược với kết quả cuối
    prediction = 'x' if last_char == 't' else 't'
    return prediction, 0.58

# Phân tích tổng hợp - LUÔN LUÔN LẤY TỪ API
def analyze(h, game_type="sum", api_prediction=None, api_pattern=None):
    # ===== THUẬT TOÁN ĐẶC BIỆT CHO LUCK8 =====
    if game_type == "luck8" and not api_prediction:
        return ensemble_predict_luck8(list(h), LUCK8_TOTALS)

    # ===== LUÔN LẤY DỰ ĐOÁN TỪ API =====
    if api_prediction and api_prediction in ["Tài", "Xỉu"]:
        # Tính độ tin cậy dựa trên pattern
        conf = 0.75  # Mặc định tin cậy API cao

        if api_pattern:
            lower_pattern = api_pattern.lower()
            t_count = lower_pattern.count('t')
            x_count = lower_pattern.count('x')
            total = len(api_pattern)
            if total > 0:
                ratio = max(t_count, x_count) / total
                if ratio > 0.7:
                    conf = 0.85  # Pattern rất mạnh
                elif ratio > 0.6:
                    conf = 0.78
                else:
                    conf = 0.72

        print(f"✅ API Prediction: {api_prediction} (độ tin cậy: {conf:.0%})")
        return api_prediction, conf

    # ===== NẾU API KHÔNG CÓ - SỬ DỤNG THUẬT TOÁN LOCAL =====
    print(f"⚠️ API không có dự đoán, sử dụng thuật toán phân tích nội bộ...")
    
    preds = []

    # Nhóm 5: Thuật toán nâng cao cho SunWin
    if game_type == "sun":
        time_weighted = algo_time_weighted_pattern(h)
        if time_weighted:
            preds.extend([time_weighted] * 2)

        dynamic_threshold = algo_dynamic_threshold(h)
        if dynamic_threshold:
            preds.extend([dynamic_threshold] * 2)

        momentum_shift = algo_momentum_shift(h)
        if momentum_shift:
            preds.extend([momentum_shift] * 2)

        cyclical = algo_cyclical_pattern(h)
        if cyclical:
            preds.extend([cyclical] * 2)

        statistical_dev = algo_statistical_deviation(h)
        if statistical_dev:
            preds.extend([statistical_dev] * 3)

        adaptive = algo_adaptive_learning(h)
        if adaptive:
            preds.extend([adaptive] * 2)

        multi_scale = algo_multi_scale(h)
        if multi_scale:
            preds.extend([multi_scale] * 3)

        prob_dist = algo_probability_distribution(h)
        if prob_dist:
            preds.extend([prob_dist] * 2)

        # ===== THUẬT TOÁN PHÂN TÍCH CẦU CHO SUNWIN =====
        cau_don = algo_cau_don(h)
        if cau_don:
            preds.extend([cau_don] * 3)  # Trọng số cao

        cau_kep = algo_cau_kep(h)
        if cau_kep:
            preds.extend([cau_kep] * 3)

        cau_dai = algo_cau_dai(h)
        if cau_dai:
            preds.extend([cau_dai] * 4)  # Trọng số rất cao

        cau_lung = algo_cau_lung(h)
        if cau_lung:
            preds.extend([cau_lung] * 2)

        cau_xien = algo_cau_xien(h)
        if cau_xien:
            preds.extend([cau_xien] * 3)

        cau_2_nhanh = algo_cau_2_nhanh(h)
        if cau_2_nhanh:
            preds.extend([cau_2_nhanh] * 2)

        cau_giat = algo_cau_giat(h)
        if cau_giat:
            preds.extend([cau_giat] * 3)

        cau_chau_au = algo_cau_chau_au(h)
        if cau_chau_au:
            preds.extend([cau_chau_au] * 2)

        chu_ky_cau = algo_chu_ky_cau(h)
        if chu_ky_cau:
            preds.extend([chu_ky_cau] * 2)

        cau_tong_hop = algo_cau_tong_hop(h)
        if cau_tong_hop:
            preds.extend([cau_tong_hop] * 4)  # Trọng số rất cao

        # ===== THUẬT TOÁN CẦU NÂNG CAO MỚI =====

        cau_1_1 = algo_cau_1_1(h)
        if cau_1_1:
            preds.extend([cau_1_1] * 3)  # Trọng số cao cho pattern xen kẽ

        cau_1_2_1 = algo_cau_1_2_1(h)
        if cau_1_2_1:
            preds.extend([cau_1_2_1] * 2)

        cau_1_2_3 = algo_cau_1_2_3(h)
        if cau_1_2_3:
            preds.extend([cau_1_2_3] * 2)

        cau_2_2 = algo_cau_2_2(h)
        if cau_2_2:
            preds.extend([cau_2_2] * 3)

        cau_3_3 = algo_cau_3_3(h)
        if cau_3_3:
            preds.extend([cau_3_3] * 3)

        cau_4_4 = algo_cau_4_4(h)
        if cau_4_4:
            preds.extend([cau_4_4] * 3)

        cau_3_2_1 = algo_cau_3_2_1(h)
        if cau_3_2_1:
            preds.extend([cau_3_2_1] * 2)

        cau_2_1_2 = algo_cau_2_1_2(h)
        if cau_2_1_2:
            preds.extend([cau_2_1_2] * 2)

        # Thuật toán bẹt - Trọng số rất cao
        cau_bet = algo_cau_bet(h)
        if cau_bet:
            preds.extend([cau_bet] * 5)  # Rất tin cậy

        cau_bet_10 = algo_cau_bet_10(h)
        if cau_bet_10:
            preds.extend([cau_bet_10] * 6)  # Cực kỳ tin cậy

        cau_bet_dau_8 = algo_cau_bet_dau_8(h)
        if cau_bet_dau_8:
            preds.extend([cau_bet_dau_8] * 4)

        cau_bet_cuoi_8 = algo_cau_bet_cuoi_8(h)
        if cau_bet_cuoi_8:
            preds.extend([cau_bet_cuoi_8] * 4)

        cau_bet_5_6 = algo_cau_bet_5_6(h)
        if cau_bet_5_6:
            preds.extend([cau_bet_5_6] * 4)

        cau_8_11_tai = algo_cau_8_11_tai(h)
        if cau_8_11_tai:
            preds.extend([cau_8_11_tai] * 5)

        # Thuật toán xen kẽ và lặp
        cau_xen_ke_nc = algo_cau_xen_ke_nang_cao(h)
        if cau_xen_ke_nc:
            preds.extend([cau_xen_ke_nc] * 4)

        cau_lap_nc = algo_cau_lap_nang_cao(h)
        if cau_lap_nc:
            preds.extend([cau_lap_nc] * 4)

        # Thuật toán kép chẵn/lẻ
        kep_xiu_chan = algo_kep_xiu_chan(h)
        if kep_xiu_chan:
            preds.extend([kep_xiu_chan] * 3)

        kep_xiu_le = algo_kep_xiu_le(h)
        if kep_xiu_le:
            preds.extend([kep_xiu_le] * 3)

        kep_tai_chan = algo_kep_tai_chan(h)
        if kep_tai_chan:
            preds.extend([kep_tai_chan] * 3)

        kep_tai_le = algo_kep_tai_le(h)
        if kep_tai_le:
            preds.extend([kep_tai_le] * 3)

    # Nhóm 6: Thuật toán phân tích cầu cho HitClub
    if game_type in ["hit", "789", "68gb"]:
        cau_don = algo_cau_don(h)
        if cau_don:
            preds.extend([cau_don] * 2)

        cau_kep = algo_cau_kep(h)
        if cau_kep:
            preds.extend([cau_kep] * 2)

        cau_dai = algo_cau_dai(h)
        if cau_dai:
            preds.extend([cau_dai] * 3)

        cau_xien = algo_cau_xien(h)
        if cau_xien:
            preds.extend([cau_xien] * 2)

        cau_giat = algo_cau_giat(h)
        if cau_giat:
            preds.extend([cau_giat] * 2)

        cau_tong_hop = algo_cau_tong_hop(h)
        if cau_tong_hop:
            preds.extend([cau_tong_hop] * 3)

        # Thuật toán mới cho HitClub
        cau_chu_ky = algo_cau_chu_ky_thoi_gian(h)
        if cau_chu_ky:
            preds.extend([cau_chu_ky] * 2)

        cau_bong = algo_cau_bong(h)
        if cau_bong:
            preds.extend([cau_bong] * 2)

        cau_song_hanh = algo_cau_song_hanh(h)
        if cau_song_hanh:
            preds.extend([cau_song_hanh] * 2)

        cau_nhay = algo_cau_nhay(h)
        if cau_nhay:
            preds.extend([cau_nhay] * 2)

    # Nhóm 7: Thuật toán phân tích cầu cho B52
    if game_type == "b52":
        cau_roi = algo_cau_roi(h)
        if cau_roi:
            preds.extend([cau_roi] * 2)

        cau_cung = algo_cau_cung(h)
        if cau_cung:
            preds.extend([cau_cung] * 2)

        cau_don_b52 = algo_cau_don_chay(h)
        if cau_don_b52:
            preds.extend([cau_don_b52] * 2)

        cau_thang = algo_cau_thang(h)
        if cau_thang:
            preds.extend([cau_thang] * 2)

        cau_dao_dong = algo_cau_dao_dong_quy_luat(h)
        if cau_dao_dong:
            preds.extend([cau_dao_dong] * 2)

    # Nhóm 8: Thuật toán phân tích cầu cho SumClub
    if game_type == "sum":
        cau_moi = algo_cau_moi(h)
        if cau_moi:
            preds.extend([cau_moi] * 2)

        cau_cheo = algo_cau_cheo(h)
        if cau_cheo:
            preds.extend([cau_cheo] * 2)

        cau_chia_doi = algo_cau_chia_doi(h)
        if cau_chia_doi:
            preds.extend([cau_chia_doi] * 2)

        cau_tam_giac = algo_cau_tam_giac(h)
        if cau_tam_giac:
            preds.extend([cau_tam_giac] * 2)

        cau_song_ngan = algo_cau_song_ngan(h)
        if cau_song_ngan:
            preds.extend([cau_song_ngan] * 2)

    # Nhóm 9: Thuật toán chung cho tất cả game
    cau_doi_xung = algo_cau_doi_xung(h)
    if cau_doi_xung:
        preds.extend([cau_doi_xung] * 2)

    cau_xoan_oc = algo_cau_xoan_oc(h)
    if cau_xoan_oc:
        preds.extend([cau_xoan_oc] * 2)

    cau_phan_xa = algo_cau_phan_xa(h)
    if cau_phan_xa:
        preds.extend([cau_phan_xa] * 2)

    cau_boi_so = algo_cau_boi_so(h)
    if cau_boi_so:
        preds.extend([cau_boi_so] * 2)

    cau_dot_pha = algo_cau_dot_pha(h)
    if cau_dot_pha:
        preds.extend([cau_dot_pha] * 2)

    cau_kep_3 = algo_cau_kep_3(h)
    if cau_kep_3:
        preds.extend([cau_kep_3] * 2)

    # ===== THUẬT TOÁN CẦU NÂNG CAO BỔ SUNG =====

    cau_khung_gio = algo_cau_theo_khung_gio(h)
    if cau_khung_gio:
        preds.extend([cau_khung_gio] * 3)

    cau_ket_hop = algo_cau_ket_hop(h)
    if cau_ket_hop:
        preds.extend([cau_ket_hop] * 4)  # Trọng số cao vì kết hợp nhiều yếu tố

    do_manh_cau = algo_do_manh_cau(h)
    if do_manh_cau:
        preds.extend([do_manh_cau] * 3)

    cau_dao_pha = algo_cau_dao_pha(h)
    if cau_dao_pha:
        preds.extend([cau_dao_pha] * 3)

    cau_lap_tuan_hoan = algo_cau_lap_tuan_hoan(h)
    if cau_lap_tuan_hoan:
        preds.extend([cau_lap_tuan_hoan] * 3)

    cau_tang_truong = algo_cau_tang_truong(h)
    if cau_tang_truong:
        preds.extend([cau_tang_truong] * 2)

    cau_phuc_tap = algo_cau_phuc_tap(h)
    if cau_phuc_tap:
        preds.extend([cau_phuc_tap] * 2)

    cau_nguoc_chieu = algo_cau_nguoc_chieu(h)
    if cau_nguoc_chieu:
        preds.extend([cau_nguoc_chieu] * 2)

    cau_bien_do = algo_cau_bien_do(h)
    if cau_bien_do:
        preds.extend([cau_bien_do] * 3)

    cau_trong_so = algo_cau_trong_so_thoi_gian(h)
    if cau_trong_so:
        preds.extend([cau_trong_so] * 3)

    cau_tich_luy = algo_cau_tich_luy(h)
    if cau_tich_luy:
        preds.extend([cau_tich_luy] * 2)

    cau_ma_tran = algo_cau_ma_tran(h)
    if cau_ma_tran:
        preds.extend([cau_ma_tran] * 2)

    cau_fibonacci = algo_cau_fibonacci_seq(h)
    if cau_fibonacci:
        preds.extend([cau_fibonacci] * 2)

    # ===== THUẬT TOÁN CẦU NÂNG CAO MỚI =====

    cau_1_1 = algo_cau_1_1(h)
    if cau_1_1:
        preds.extend([cau_1_1] * 3)  # Trọng số cao cho pattern xen kẽ

    cau_1_2_1 = algo_cau_1_2_1(h)
    if cau_1_2_1:
        preds.extend([cau_1_2_1] * 2)

    cau_1_2_3 = algo_cau_1_2_3(h)
    if cau_1_2_3:
        preds.extend([cau_1_2_3] * 2)

    cau_2_2 = algo_cau_2_2(h)
    if cau_2_2:
        preds.extend([cau_2_2] * 3)

    cau_3_3 = algo_cau_3_3(h)
    if cau_3_3:
        preds.extend([cau_3_3] * 3)

    cau_4_4 = algo_cau_4_4(h)
    if cau_4_4:
        preds.extend([cau_4_4] * 3)

    cau_3_2_1 = algo_cau_3_2_1(h)
    if cau_3_2_1:
        preds.extend([cau_3_2_1] * 2)

    cau_2_1_2 = algo_cau_2_1_2(h)
    if cau_2_1_2:
        preds.extend([cau_2_1_2] * 2)

    # Thuật toán bẹt - Trọng số rất cao
    cau_bet = algo_cau_bet(h)
    if cau_bet:
        preds.extend([cau_bet] * 5)  # Rất tin cậy

    cau_bet_10 = algo_cau_bet_10(h)
    if cau_bet_10:
        preds.extend([cau_bet_10] * 6)  # Cực kỳ tin cậy

    cau_bet_dau_8 = algo_cau_bet_dau_8(h)
    if cau_bet_dau_8:
        preds.extend([cau_bet_dau_8] * 4)

    cau_bet_cuoi_8 = algo_cau_bet_cuoi_8(h)
    if cau_bet_cuoi_8:
        preds.extend([cau_bet_cuoi_8] * 4)

    cau_bet_5_6 = algo_cau_bet_5_6(h)
    if cau_bet_5_6:
        preds.extend([cau_bet_5_6] * 4)

    cau_8_11_tai = algo_cau_8_11_tai(h)
    if cau_8_11_tai:
        preds.extend([cau_8_11_tai] * 5)

    # Thuật toán xen kẽ và lặp
    cau_xen_ke_nc = algo_cau_xen_ke_nang_cao(h)
    if cau_xen_ke_nc:
        preds.extend([cau_xen_ke_nc] * 4)

    cau_lap_nc = algo_cau_lap_nang_cao(h)
    if cau_lap_nc:
        preds.extend([cau_lap_nc] * 4)

    # Thuật toán kép chẵn/lẻ
    kep_xiu_chan = algo_kep_xiu_chan(h)
    if kep_xiu_chan:
        preds.extend([kep_xiu_chan] * 3)

    kep_xiu_le = algo_kep_xiu_le(h)
    if kep_xiu_le:
        preds.extend([kep_xiu_le] * 3)

    kep_tai_chan = algo_kep_tai_chan(h)
    if kep_tai_chan:
        preds.extend([kep_tai_chan] * 3)

    kep_tai_le = algo_kep_tai_le(h)
    if kep_tai_le:
        preds.extend([kep_tai_le] * 3)

    # ===== THUẬT TOÁN DỰ ĐOÁN CHÍNH XÁC CAO =====

    # Nhóm 10: Thuật toán Machine Learning
    hidden_markov = algo_hidden_markov(h)
    if hidden_markov:
        preds.extend([hidden_markov] * 4)  # Trọng số rất cao

    deep_pattern = algo_deep_pattern(h)
    if deep_pattern:
        preds.extend([deep_pattern] * 5)  # Trọng số cực cao

    bayesian = algo_bayesian(h)
    if bayesian:
        preds.extend([bayesian] * 4)

    neural_net = algo_neural_network_sim(h)
    if neural_net:
        preds.extend([neural_net] * 4)

    random_forest = algo_random_forest(h)
    if random_forest:
        preds.extend([random_forest] * 5)  # Rất tin cậy

    # Nhóm 11: Thuật toán Advanced Analytics
    fractal = algo_fractal(h)
    if fractal:
        preds.extend([fractal] * 3)

    info_entropy = algo_information_entropy(h)
    if info_entropy:
        preds.extend([info_entropy] * 3)

    chaos = algo_chaos_theory(h)
    if chaos:
        preds.extend([chaos] * 3)

    # Nhóm 12: Thuật toán Ensemble
    ensemble = algo_ensemble(h)
    if ensemble:
        preds.extend([ensemble] * 6)  # Trọng số cực cao - kết hợp nhiều models

    adaptive_boost = algo_adaptive_boost(h)
    if adaptive_boost:
        preds.extend([adaptive_boost] * 4)

    gradient_boost = algo_gradient_boosting(h)
    if gradient_boost:
        preds.extend([gradient_boost] * 4)

    # Nhóm 13: Thuật toán khác
    quantum = algo_quantum_probability(h)
    if quantum:
        preds.extend([quantum] * 2)

    genetic = algo_genetic(h)
    if genetic:
        preds.extend([genetic] * 3)

    svm = algo_svm(h)
    if svm:
        preds.extend([svm] * 3)

    time_series = algo_time_series_decomposition(h)
    if time_series:
        preds.extend([time_series] * 3)

    # Voting logic
    if not preds:
        return random.choice(["Tài", "Xỉu"]), 0.50
        
    tai_count = preds.count("Tài")
    xiu_count = preds.count("Xỉu")
    total = len(preds)
    
    if tai_count > xiu_count:
        confidence = 0.5 + (tai_count / total - 0.5)
        return "Tài", min(0.95, confidence)
    elif xiu_count > tai_count:
        confidence = 0.5 + (xiu_count / total - 0.5)
        return "Xỉu", min(0.95, confidence)
    else:
        return random.choice(["Tài", "Xỉu"]), 0.50

def get_formatted_history(game):
    if game not in PREDICTION_HISTORY: return []
    hist = list(PREDICTION_HISTORY[game])
    # Lấy 10 phiên gần nhất
    recent = hist[-10:] if len(hist) >= 10 else hist
    formatted = []
    for item in reversed(recent):
        formatted.append({
            "session": item.get("session"),
            "prediction": item.get("prediction"),
            "result": item.get("actual"),
            "correct": item.get("correct")
        })
    return formatted

def predict(game, ban="md5"):
    h = HIST[game]

    if game == "sun":
        # Sử dụng API mới
        raw = safe_json(API_SUN, timeout=5)

        if not raw:
            pattern_history = list(h)[-17:] if len(h) >= 17 else list(h)
            pattern = "".join(["t" if x == "Tài" else "x" for x in pattern_history])
            return {
                "phien": "---",
                "phien_du_doan": "---",
                "ket_qua": "Chờ kết nối...",
                "xuc_xac": [0, 0, 0],
                "tong_xuc_xac": 0,
                "du_doan_tiep_theo": random.choice(["Tài", "Xỉu"]),
                "loai_cau": "Đang tải",
                "thuat_toan": "Đang kết nối",
                "so_lan_dung": STATS['sun']['correct'],
                "so_lan_sai": STATS['sun']['total'] - STATS['sun']['correct'] if STATS['sun']['total'] > 0 else 0,
                "pattern": pattern,
                "tong_lich_su": len(pattern_history),
                "id": "@minhsangdangcap",
                "link_iframe": LINK_SUN,
                "history": get_formatted_history("sun")
            }

        # Lấy dữ liệu từ API (Format mới: xuc_xac_1, xuc_xac_2, tong, du_doan...)
        # API mới: {"phien": 289090, "du_doan": "Xỉu", "ket_qua": ..., "do_tin_cay": ...}
        phien = str(raw.get("phien") or raw.get("Phien") or raw.get("phien_hien_tai") or "---")
        ket = normalize(raw.get("ket_qua") or raw.get("Ket_qua"))
        api_du_doan = normalize(raw.get("du_doan"))
        api_pattern = raw.get("pattern", "")
        
        # Parse confidence
        raw_conf = raw.get("do_tin_cay")
        api_conf = None
        try:
            if raw_conf is not None:
                conf_val = float(str(raw_conf).replace('%', '').replace(',', '.'))
                api_conf = conf_val / 100 if conf_val > 1 else conf_val
        except: pass

        # Lấy thông tin xúc xắc và tổng
        tong_xuc_xac = raw.get("Tong") or raw.get("tong")
        
        x1 = raw.get("Xuc_xac_1") or raw.get("xuc_xac_1")
        x2 = raw.get("Xuc_xac_2") or raw.get("xuc_xac_2")
        x3 = raw.get("Xuc_xac_3") or raw.get("xuc_xac_3")
        if x1 is not None and x2 is not None and x3 is not None:
            xuc_xac = [x1, x2, x3]
        else:
            xuc_xac = raw.get("xuc_xac", [0, 0, 0])

        loai_cau = raw.get("loai_cau", "")
        thuat_toan = raw.get("thuat_toan", "")
        so_dung = raw.get("so_lan_dung", 0)
        so_sai = raw.get("so_lan_sai", 0)

        if not phien or phien == "---":
            return None

        # **QUAN TRỌNG: Lưu kết quả NGAY từ API vào lịch sử**
        if ket and ket in ["Tài", "Xỉu"]:
            # Cập nhật stats cho phiên vừa kết thúc (gọi luôn để đảm bảo cập nhật)
            update_prediction_results("sun", phien, ket)
            
            # Kiểm tra xem kết quả này đã được lưu chưa
            if not h or h[-1] != ket:
                # Lưu vào lịch sử ngay lập tức
                h.append(ket)
                save_history()
                analyze_and_save_cau_patterns(list(h), "sun")
                print(f"✅ SunWin #{phien}: Lưu kết quả - {ket} | Xúc xắc: {xuc_xac} | Tổng: {tong_xuc_xac}")

        # Dự đoán cho phiên tiếp theo (API phiên + 1)
        phien_tiep_theo = raw.get("phien_du_doan")
        if phien_tiep_theo:
            phien_tiep_theo = str(phien_tiep_theo)
        else:
            try:
                phien_tiep_theo = str(int(phien) + 1) if phien != "---" else "---"
            except:
                phien_tiep_theo = "---"

        # Luôn truyền dự đoán từ API vào analyze để ưu tiên
        du, conf = analyze(list(h), "sun", api_prediction=api_du_doan, api_pattern=api_pattern)
        
        if api_conf is not None:
            conf = api_conf
            
        record_prediction("sun", phien_tiep_theo, du, conf)

        # Tạo pattern từ lịch sử (17 phiên gần nhất)
        pattern_history = list(h)[-17:] if len(h) >= 17 else list(h)
        pattern = "".join(["t" if x == "Tài" else "x" for x in pattern_history])

        return {
            "phien": phien,
            "phien_du_doan": phien_tiep_theo,
            "ket_qua": ket or "Đang chờ...",
            "xuc_xac": xuc_xac if xuc_xac else [0, 0, 0],
            "tong_xuc_xac": tong_xuc_xac if tong_xuc_xac else 0,
            "du_doan_tiep_theo": du,
            "do_tin_cay": conf,
            "loai_cau": loai_cau if loai_cau else "Cầu thường",
            "thuat_toan": thuat_toan if thuat_toan else "HYBRID+",
            "so_lan_dung": STATS['sun']['correct'],
            "so_lan_sai": STATS['sun']['total'] - STATS['sun']['correct'] if STATS['sun']['total'] > 0 else 0,
            "pattern": pattern,
            "tong_lich_su": len(pattern_history),
            "id": "@minhsangdangcap",
            "link_iframe": LINK_SUN,
            "history": get_formatted_history("sun")
        }

    if game == "hit":
        if ban == "hu":
            raw_response = safe_json(API_HIT_HU)
            if not raw_response or not raw_response.get("success"): return None
            raw = raw_response.get("data", {})
            
            phien_hien_tai = raw.get("phien_hien_tai")
            phien = str(int(phien_hien_tai) - 1) if phien_hien_tai else "---"
            ket = None  # API hũ không có kết quả phiên trước
            phien_tiep_theo = str(phien_hien_tai) if phien_hien_tai else "---"
            api_du = normalize(raw.get("du_doan"))
            raw_conf = raw.get("confidence")
        else:
            raw_response = safe_json(API_HIT)
            if not raw_response: return None
            
            if "success" in raw_response and "data" in raw_response:
                raw = raw_response.get("data", {})
                phien_hien_tai = raw.get("phien_hien_tai")
                phien = str(int(phien_hien_tai) - 1) if phien_hien_tai else "---"
                ket = None
                phien_tiep_theo = str(phien_hien_tai) if phien_hien_tai else "---"
                api_du = normalize(raw.get("du_doan"))
                raw_conf = raw.get("confidence")
            else:
                raw = raw_response
                phien = str(raw.get("Phien") or raw.get("phien", "---"))
                ket = normalize(raw.get("Ket_qua") or raw.get("ket_qua"))
                phien_tiep_theo = str(int(phien) + 1) if phien and phien != "---" else "---"
                api_du = normalize(raw.get("Du_doan") or raw.get("du_doan"))
                raw_conf = raw.get("Do_tin_cay") or raw.get("do_tin_cay")

        # Lưu kết quả NGAY từ API
        if ket and ket in ["Tài", "Xỉu"]:
            update_prediction_results("hit", phien, ket)
            if not h or h[-1] != ket:
                h.append(ket)
                save_history()
                analyze_and_save_cau_patterns(list(h), "hit")

        # Parse confidence
        try:
            if raw_conf:
                conf_val = float(str(raw_conf).replace('%', '').replace(',', '.'))
                api_conf = conf_val / 100 if conf_val > 1 else conf_val
            else:
                api_conf = None
        except:
            api_conf = None

        # Luôn truyền API prediction vào analyze
        du, conf = analyze(list(h), "hit", api_prediction=api_du)
        
        if api_conf is not None:
            conf = api_conf
            
        record_prediction("hit", phien_tiep_theo, du, conf)

        return {
            "game": "HitClub",
            "phien": phien,
            "phien_du_doan": phien_tiep_theo,
            "ket_qua": ket or "Đang chờ...",
            "du_doan": du,
            "do_tin_cay": conf,
            "ban": ban,
            "accuracy": f"{STATS['hit']['correct']}/{STATS['hit']['total']}" if STATS['hit']['total'] > 0 else "0/0",
            "history": get_formatted_history("hit")
        }

    if game == "789":
        raw = safe_json(API_789)
        if not raw: return None
        
        # New JSON format support
        phien = raw.get("phien")
        ket = normalize(raw.get("ket_qua_hien_tai") or raw.get("ket_qua"))

        # Lưu kết quả NGAY từ API
        if ket and ket in ["Tài", "Xỉu"]:
            update_prediction_results("789", phien, ket)
            if not h or h[-1] != ket:
                h.append(ket)
                save_history()
                analyze_and_save_cau_patterns(list(h), "789")

        # Dự đoán cho phiên tiếp theo
        phien_tiep_theo = str(raw.get("phien_dudoan")) if raw.get("phien_dudoan") else (str(int(phien) + 1) if phien else phien)
        api_du = normalize(raw.get("du_doan_van_sau") or raw.get("du_doan"))
        
        # Parse confidence
        raw_conf = raw.get("do_tin_cay")
        api_conf = None
        if raw_conf == "Cao": api_conf = 0.85
        elif raw_conf == "Trung bình": api_conf = 0.65
        elif raw_conf == "Thấp": api_conf = 0.50

        # Luôn truyền API prediction vào analyze
        du, conf = analyze(list(h), "789", api_prediction=api_du)
        
        if api_conf is not None:
            conf = api_conf
            
        record_prediction("789", phien_tiep_theo, du, conf)

        return {
            "game": "789Club",
            "phien": phien,
            "ket_qua": ket or "Đang chờ...",
            "du_doan": du,
            "do_tin_cay": conf,
            "accuracy": f"{STATS['789']['correct']}/{STATS['789']['total']}" if STATS['789']['total'] > 0 else "0/0",
            "history": get_formatted_history("789")
        }

    if game == "68gb":
        # API mới trả về {"data": [...]} - lọc lấy bàn xanh "key": "banxanh"
        raw_all = safe_json(API_68GB)
        raw = None
        if raw_all:
            data_list = raw_all.get("data", [])
            if isinstance(data_list, list):
                for item in data_list:
                    if item.get("key") == "banxanh" or item.get("game","").upper() == "BÀN XANH":
                        raw = item
                        break
            # Fallback: nếu API trả thẳng object (không có data wrapper)
            if not raw and raw_all.get("key") == "banxanh":
                raw = raw_all
        if not raw:
            # Fallback: Dự đoán từ lịch sử nội bộ nếu API lỗi
            du, conf = analyze(list(HIST["68gb"]), "68gb")
            
            # Tạo phiên giả lập để giao diện không bị treo
            fake_phien = "---"
            if PREDICTION_HISTORY["68gb"]:
                last_rec = PREDICTION_HISTORY["68gb"][-1]
                if last_rec.get("session") and str(last_rec.get("session")).isdigit():
                    fake_phien = str(int(last_rec["session"]) - 1)
            
            return {
                "game": "68 Game Bài",
                "phien": fake_phien if fake_phien != "---" else str(int(time.time())),
                "phien_du_doan": "---",
                "ket_qua": "Mất kết nối",
                "xuc_xac": [0, 0, 0],
                "tong_xuc_xac": 0,
                "du_doan": du,
                "do_tin_cay": conf,
                "accuracy": f"{STATS['68gb']['correct']}/{STATS['68gb']['total']}" if STATS['68gb']['total'] > 0 else "0/0",
                "history": get_formatted_history("68gb")
            }
            
        # API 68GB: "phien" = phiên đang dự đoán (tiếp theo), "du_doan" = kết quả dự đoán
        # Phiên hiện tại = phien - 1
        phien_du_doan = str(raw.get("phien") or "---")
        try:
            phien_hien_tai = str(int(phien_du_doan) - 1) if phien_du_doan.isdigit() else "---"
        except:
            phien_hien_tai = "---"

        phien = phien_hien_tai  # phiên hiện tại để lưu lịch sử
        phien_tiep_theo = phien_du_doan  # phiên đang dự đoán

        ket = normalize(raw.get("ket_qua") or raw.get("Ket_qua"))

        if ket and ket in ["Tài", "Xỉu"]:
            update_prediction_results("68gb", phien, ket)
            if not h or h[-1] != ket:
                h.append(ket)
                save_history()
                analyze_and_save_cau_patterns(list(h), "68gb")

        api_du = normalize(raw.get("du_doan") or raw.get("Du_doan") or raw.get("predict"))
        
        # Parse confidence
        raw_conf = raw.get("do_tin_cay") or raw.get("Do_tin_cay") or raw.get("confidence")
        api_conf = None
        try:
            if raw_conf:
                conf_val = float(str(raw_conf).replace('%', '').replace(',', '.'))
                api_conf = conf_val / 100 if conf_val > 1 else conf_val
        except: pass

        du, conf = analyze(list(h), "68gb", api_prediction=api_du)
        if api_conf is not None: conf = api_conf
        
        record_prediction("68gb", phien_tiep_theo, du, conf)

        x1 = raw.get("Xuc_xac_1") or raw.get("xuc_xac_1")
        x2 = raw.get("Xuc_xac_2") or raw.get("xuc_xac_2")
        x3 = raw.get("Xuc_xac_3") or raw.get("xuc_xac_3")
        tong = raw.get("Tong") or raw.get("tong")
        xuc_xac = [x1, x2, x3] if (x1 is not None and x2 is not None and x3 is not None) else [0, 0, 0]

        return {
            "game": "68 Game Bài",
            "phien": phien,
            "phien_du_doan": phien_tiep_theo,
            "ket_qua": ket or "Đang chờ...",
            "xuc_xac": xuc_xac,
            "tong_xuc_xac": tong if tong is not None else 0,
            "du_doan": du,
            "do_tin_cay": conf,
            "accuracy": f"{STATS['68gb']['correct']}/{STATS['68gb']['total']}" if STATS['68gb']['total'] > 0 else "0/0",
            "history": get_formatted_history("68gb")
        }

    if game == "lc79":
        raw = safe_json(API_LC79)
        if not raw:
            # Fallback: Dự đoán từ lịch sử nội bộ nếu API lỗi
            du, conf = analyze(list(HIST["lc79"]), "lc79")
            return {
                "game": "LC79",
                "phien": "---",
                "phien_du_doan": "---",
                "ket_qua": "Mất kết nối",
                "xuc_xac": [0, 0, 0],
                "tong_xuc_xac": 0,
                "du_doan": du,
                "do_tin_cay": conf,
                "loai_cau": "Đang tải...",
                "pattern": "",
                "accuracy": f"{STATS['lc79']['correct']}/{STATS['lc79']['total']}" if STATS['lc79']['total'] > 0 else "0/0",
                "history": get_formatted_history("lc79")
            }

        # Xử lý JSON format mới
        phien = str(raw.get("Phien") or raw.get("phien_hien_tai") or raw.get("phien", "---"))
        
        # Xử lý kết quả từ xúc xắc (ưu tiên) hoặc trường ket_qua
        x1 = raw.get("Xuc_xac_1") or raw.get("xuc_xac_1")
        x2 = raw.get("Xuc_xac_2") or raw.get("xuc_xac_2")
        x3 = raw.get("Xuc_xac_3") or raw.get("xuc_xac_3")
        if x1 is not None and x2 is not None and x3 is not None:
            xuc_xac = [x1, x2, x3]
        else:
            xuc_xac = raw.get("xuc_xac", [0, 0, 0])
            
        tong_xuc_xac = raw.get("Tong") or raw.get("tong")
        if tong_xuc_xac is None:
            tong_xuc_xac = sum(xuc_xac) if xuc_xac and len(xuc_xac) == 3 else 0
        
        ket = normalize(raw.get("Ket_qua") or raw.get("ket_qua"))
        if not ket and tong_xuc_xac > 0:
            ket = "Tài" if tong_xuc_xac > 10 else "Xỉu"

        if ket and ket in ["Tài", "Xỉu"]:
            update_prediction_results("lc79", phien, ket)
            if not h or h[-1] != ket:
                h.append(ket)
                save_history()
                analyze_and_save_cau_patterns(list(h), "lc79")

        # Dự đoán phiên tiếp theo
        # API mới đã có sẵn phien_du_doan, dùng đúng như API - KHÔNG cộng 1
        phien_tiep_theo = raw.get("phien_du_doan") or raw.get("phien_tiep_theo")
        if phien_tiep_theo:
            phien_tiep_theo = str(phien_tiep_theo)
        else:
            # Nếu API không có phien_du_doan thì dùng phien hiện tại luôn (không cộng 1)
            phien_tiep_theo = phien
            
        api_du = normalize(raw.get("du_doan"))
        
        # Parse confidence "92%"
        raw_conf = raw.get("do_tin_cay") or raw.get("ty_le_dd")
        try:
            if raw_conf:
                conf_val = float(str(raw_conf).replace('%', '').replace(',', '.'))
                api_conf = conf_val / 100 if conf_val > 1 else conf_val
            else:
                api_conf = None
        except:
            api_conf = None
            
        # Lấy thêm thông tin hiển thị
        loai_cau = raw.get("loai_cau", "")
        pattern = raw.get("pattern", "")
            
        du, conf = analyze(list(h), "lc79", api_prediction=api_du, api_pattern=pattern)
        if api_conf is not None:
            conf = api_conf
            
        record_prediction("lc79", phien_tiep_theo, du, conf)

        return {
            "game": "LC79",
            "phien": phien,
            "phien_du_doan": phien_tiep_theo,
            "ket_qua": ket or "Đang chờ...",
            "xuc_xac": xuc_xac,
            "tong_xuc_xac": tong_xuc_xac,
            "du_doan": du,
            "do_tin_cay": conf,
            "loai_cau": loai_cau,
            "pattern": pattern,
            "accuracy": f"{STATS['lc79']['correct']}/{STATS['lc79']['total']}" if STATS['lc79']['total'] > 0 else "0/0",
            "history": get_formatted_history("lc79")
        }

    if game == "sexy":
        # Placeholder cho BCR Sexy nếu cần API backend
        # Hiện tại game này chạy client-side random
        return {
            "phien": "---",
            "ket_qua": "---",
            "du_doan": random.choice(["B", "P", "T"]),
            "do_tin_cay": 0.75,
            "thuat_toan": "BCR Sexy AI",
            "so_lan_dung": STATS['sexy']['correct'],
            "so_lan_sai": STATS['sexy']['total'] - STATS['sexy']['correct'] if STATS['sexy']['total'] > 0 else 0,
            "history": get_formatted_history("sexy")
        }

    if game == "sum":
        raw = safe_json(API_SUM)
        if not raw: return None
        phien = raw.get("Phien") or raw.get("phien_hien_tai")
        ket = normalize(raw.get("Ket_qua"))

        # Lưu kết quả NGAY từ API
        if ket and ket in ["Tài", "Xỉu"]:
            update_prediction_results("sum", phien, ket)
            if not h or h[-1] != ket:
                h.append(ket)
                save_history()
                analyze_and_save_cau_patterns(list(h), "sum")

        # Dự đoán cho phiên tiếp theo
        phien_tiep_theo = str(int(phien) + 1) if phien else phien
        api_du = normalize(raw.get("du_doan"))

        # Luôn truyền API prediction vào analyze
        du, conf = analyze(list(h), "sum", api_prediction=api_du)
        record_prediction("sum", phien_tiep_theo, du, conf)

        return {
            "game": "SumClub",
            "phien": phien,
            "ket_qua": ket or "Đang chờ...",
            "du_doan": du,
            "do_tin_cay": conf,
            "accuracy": f"{STATS['sum']['correct']}/{STATS['sum']['total']}" if STATS['sum']['total'] > 0 else "0/0",
            "history": get_formatted_history("sum")
        }

    if game == "b52":
        a = safe_json(API_B52A)
        b = safe_json(API_B52B)
        
        def get_p(d):
            if not d: return 0
            return int(d.get("phien") or d.get("Phien") or 0)
            
        raw = b if b and (not a or get_p(b) >= get_p(a)) else a
        if not raw: return None
        
        # Xử lý JSON format mới (B52)
        if "phien_hien_tai" in raw or "Phien" in raw:
            phien = str(raw.get("Phien") or raw.get("phien"))
            ket = normalize(raw.get("Ket_qua") or raw.get("ket_qua"))
            phien_tiep_theo = str(raw.get("phien_hien_tai")) if raw.get("phien_hien_tai") else (str(int(phien) + 1) if phien and phien.isdigit() else "---")
            api_du = normalize(raw.get("Du_doan") or raw.get("du_doan"))
            api_conf_raw = raw.get("Do_tin_cay") or raw.get("do_tin_cay")
        else:
            phien = str(raw.get("Phien") or raw.get("phien"))
            ket = normalize(raw.get("Ket_qua") or raw.get("ket_qua"))
            phien_tiep_theo = str(int(phien) + 1) if phien and phien.isdigit() else "---"
            api_du = normalize(raw.get("Du_doan") or raw.get("du_doan"))
            api_conf_raw = None

        # Lưu kết quả NGAY từ API
        if ket and ket in ["Tài", "Xỉu"]:
            update_prediction_results("b52", phien, ket)
            if not h or h[-1] != ket:
                h.append(ket)
                save_history()
                analyze_and_save_cau_patterns(list(h), "b52")

        # Luôn truyền API prediction vào analyze
        du, conf = analyze(list(h), "b52", api_prediction=api_du)
        
        # Sử dụng độ tin cậy từ API nếu có
        if api_conf_raw is not None:
            try:
                if float(str(api_conf_raw).replace('%', '').replace(',', '.')) > 1:
                    conf = float(str(api_conf_raw).replace('%', '').replace(',', '.')) / 100
                else:
                    conf = float(str(api_conf_raw).replace('%', '').replace(',', '.'))
            except:
                pass
                
        record_prediction("b52", phien_tiep_theo, du, conf)

        return {
            "game": "B52",
            "phien": phien,
            "ket_qua": ket or "Đang chờ...",
            "du_doan": du,
            "do_tin_cay": conf,
            "accuracy": f"{STATS['b52']['correct']}/{STATS['b52']['total']}" if STATS['b52']['total'] > 0 else "0/0",
            "history": get_formatted_history("b52")
        }

    if game == "luck8":
        raw = safe_json(API_LUCK8)
        if not raw: return None
        
        phien = raw.get("phien")
        ket = normalize(raw.get("ketQua"))

        # Lưu tổng xúc xắc
        try:
            xuc_xac = raw.get("xucXac", [])
            total_dice = sum(xuc_xac) if len(xuc_xac) == 3 else 0
                
            if not LUCK8_TOTALS or total_dice != LUCK8_TOTALS[-1]:
                LUCK8_TOTALS.append(total_dice)
                if len(LUCK8_TOTALS) >= 30:
                    h.clear()
                    LUCK8_TOTALS.clear()
                    PREDICTION_HISTORY["luck8"].clear()
        except:
            pass

        # Lưu kết quả NGAY từ API
        if ket and ket in ["Tài", "Xỉu"]:
            update_prediction_results("luck8", phien, ket)
            if not h or h[-1] != ket:
                h.append(ket)
                save_history()
                analyze_and_save_cau_patterns(list(h), "luck8")

        # Dự đoán cho phiên tiếp theo
        phien_tiep_theo = raw.get("phienHienTai")
        if not phien_tiep_theo and phien:
            phien_tiep_theo = str(int(phien) + 1)
            
        api_du = normalize(raw.get("duDoan"))
        api_pattern = raw.get("pattern", "")
        
        # Parse confidence
        raw_conf = raw.get("doTinCay")
        api_conf = None
        try:
            if raw_conf and isinstance(raw_conf, str) and "%" in raw_conf:
                api_conf = float(raw_conf.replace("%", "")) / 100
            elif isinstance(raw_conf, (int, float)):
                api_conf = float(raw_conf) / 100 if raw_conf > 1 else float(raw_conf)
        except: pass

        du, conf = analyze(list(h), "luck8", api_prediction=api_du, api_pattern=api_pattern)
        if api_conf is not None: conf = api_conf
        
        record_prediction("luck8", phien_tiep_theo, du, conf)

        return {
            "game": "Luck8",
            "phien": phien,
            "ket_qua": ket or "Đang chờ...",
            "du_doan": du,
            "do_tin_cay": conf,
            "accuracy": f"{STATS['luck8']['correct']}/{STATS['luck8']['total']}" if STATS['luck8']['total'] > 0 else "0/0",
            "history": get_formatted_history("luck8")
        }

    if game == "sicbo":
        raw = safe_json(API_SICBO)
        if not raw: return None
        
        # Xử lý JSON format mới (Sunwin Sicbo)
        if "⚜️ Phiên Trước" in raw or ("phien_hien_tai" in raw and "dudoan_vi" in raw):
            phien_ket_qua = str(raw.get("⚜️ Phiên Trước") or raw.get("phien", "---")) # Phiên vừa có kết quả
            phien_tiep_theo_api = str(raw.get("🎯 Phiên Dự Đoán") or raw.get("phien_hien_tai", "---")) # Phiên đang chạy
            
            ket = normalize(raw.get("📊 Kết Quả") or raw.get("ket_qua"))
            api_du_doan = normalize(raw.get("🔮 Lựa Chọn AI") or raw.get("du_doan"))
            
            # Parse dice
            raw_dice = raw.get("🎲 Xúc Xắc")
            if raw_dice:
                try:
                    xuc_xac = [int(p) for p in str(raw_dice).split(" - ")]
                except:
                    xuc_xac = [0, 0, 0]
            else:
                x1 = raw.get("xuc_xac_1", 0)
                x2 = raw.get("xuc_xac_2", 0)
                x3 = raw.get("xuc_xac_3", 0)
                xuc_xac = [x1, x2, x3]
            
            tong_diem = raw.get("📈 Tổng Điểm") or raw.get("tong", 0)
            
            # Parse vi
            raw_vi = raw.get("🔢 Gợi Ý Vị")
            if raw_vi:
                try:
                    vi_du_doan_api = [int(x.strip()) for x in str(raw_vi).split("|")]
                except:
                    vi_du_doan_api = [10, 11, 12]
            else:
                vi_du_doan_api = raw.get("dudoan_vi", [10, 11, 12])
                
            do_tin_cay = raw.get("💎 Độ Tin Cậy") or raw.get("do_tin_cay", 63)
            
            # Gán phien_hien_tai (biến cũ dùng để update kết quả) bằng phiên vừa kết thúc
            phien_hien_tai = phien_ket_qua
        else:
            # Format cũ (Fallback)
            phien_hien_tai = raw.get("Phiên hiện tại", "---")
            if phien_hien_tai and phien_hien_tai.startswith("#"):
                phien_hien_tai = phien_hien_tai[1:]
            
            phien_tiep_theo_api = raw.get("Phiên tiếp theo", "---")
            if phien_tiep_theo_api and phien_tiep_theo_api.startswith("#"):
                phien_tiep_theo_api = phien_tiep_theo_api[1:]
            
            ket = normalize(raw.get("Kết quả"))
            api_du_doan = normalize(raw.get("Dự đoán"))
            xuc_xac = raw.get("Xúc xắc", [0, 0, 0])
            tong_diem = raw.get("Tổng điểm", 0)
            vi_du_doan_api = raw.get("Vị dự đoán", [10, 11, 12])
            do_tin_cay = raw.get("Độ tin cậy", "63%")
            
        loai_cau = raw.get("Loại cầu", raw.get("Ghi_chu", ""))
        
        if not phien_hien_tai or phien_hien_tai == "---":
            return None

        # Lưu tổng điểm vào SICBO_TOTALS để phân tích
        if tong_diem and tong_diem > 0:
            if not SICBO_TOTALS or SICBO_TOTALS[-1] != tong_diem:
                SICBO_TOTALS.append(tong_diem)

        # Lưu kết quả NGAY từ API
        if ket and ket in ["Tài", "Xỉu"]:
            update_prediction_results("sicbo", phien_hien_tai, ket)
            if not h or h[-1] != ket:
                h.append(ket)
                save_history()
                analyze_and_save_cau_patterns(list(h), "sicbo")
                print(f"✅ Sicbo #{phien_hien_tai}: Lưu kết quả - {ket} | Xúc xắc: {xuc_xac} | Tổng: {tong_diem}")

        # Dự đoán cho phiên tiếp theo
        du, conf = analyze(list(h), "sicbo", api_prediction=api_du_doan)
        record_prediction("sicbo", phien_tiep_theo_api, du, conf)

        # Dự đoán vị xúc xắc
        vi_du_doan = vi_du_doan_api

        # Parse độ tin cậy
        try:
            if isinstance(do_tin_cay, (int, float)):
                conf_percent = int(do_tin_cay)
            else:
                conf_percent = int(str(do_tin_cay).replace("%", ""))
        except:
            conf_percent = int(conf * 100)

        return {
            "phien_hien_tai": phien_hien_tai,
            "phien_tiep_theo": phien_tiep_theo_api,
            "ket_qua": ket or "Đang chờ...",
            "xuc_xac": xuc_xac if xuc_xac else [0, 0, 0],
            "tong_xuc_xac": tong_diem if tong_diem else 0,
            "du_doan": du,
            "vi_du_doan": vi_du_doan,
            "loai_cau": loai_cau if loai_cau else "Cầu thường",
            "thuat_toan": "HYBRID AI",
            "so_lan_dung": STATS['sicbo']['correct'],
            "so_lan_sai": STATS['sicbo']['total'] - STATS['sicbo']['correct'] if STATS['sicbo']['total'] > 0 else 0,
            "do_tin_cay": conf_percent,
            "id": "@minhsangdangcap",
            "link_iframe": LINK_SICBO,
            "history": get_formatted_history("sicbo")
        }

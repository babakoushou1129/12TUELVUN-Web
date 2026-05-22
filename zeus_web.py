import streamlit as st
import csv
from collections import defaultdict
import os
import urllib.request
import urllib.error
import json
import ssl
import gdown

# ==========================================
# ⚙️ システム中枢設定
# ==========================================
DRIVE_FILE_ID = "1z2UYWOa_4BymBuOPm0cm9rLAaj2lKgbo"
API_KEY = "AIzaSyBrxbZASJs9sJfEWp3_q9OfUMw0KQpdXTg"
# ==========================================

CSV_FILE = f"ZEUS_MASTER_CLEANED_{DRIVE_FILE_ID}.csv"

st.set_page_config(page_title="12TUELVUN", page_icon="⚡", layout="centered")

def sync_database_from_cloud():
    if not DRIVE_FILE_ID:
        st.error("⚠️ コード内にGoogleドライブのIDが設定されていません。")
        return False
    if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 1024 * 1024:
        return True

    with st.spinner("☁️ マスターデータをクラウドから読み込み中...（初回のみ1〜3分）"):
        try:
            gdown.download(id=DRIVE_FILE_ID, output=CSV_FILE, quiet=False)
            if os.path.exists(CSV_FILE):
                with open(CSV_FILE, "r", encoding="utf-8", errors="ignore") as f:
                    head = f.read(500)
                    if "<html" in head.lower() or "<!doctype html>" in head.lower():
                        st.error("❌ 【アクセス拒否エラー】Googleのログイン画面を読み込みました。個人用アカウントのドライブでリンクを作り直してください。")
                        os.remove(CSV_FILE)
                        return False
                return True
            else:
                st.error("❌ ダウンロードに失敗しました。")
                return False
        except Exception as e:
            st.error(f"❌ 通信エラー: {e}")
            return False

database_ready = sync_database_from_cloud()

# 💡【最強機能】文字化けを絶対に防ぐ自動エンコード判定
def detect_encoding(file_path):
    for enc in ['utf-8-sig', 'utf-8', 'shift_jis', 'cp932']:
        try:
            with open(file_path, "r", encoding=enc) as f:
                text = f.read(2000)
                if any(v in text for v in ["桐生", "戸田", "江戸川", "平和島", "多摩川", "浜名湖", "蒲郡", "常滑", "津", "三国", "びわこ", "住之江", "尼崎", "鳴門", "丸亀", "児島", "宮島", "徳山", "下関", "若松", "芦屋", "福岡", "唐津", "大村", "着", "艇"]):
                    return enc
        except:
            pass
    return 'shift_jis'

# 💡【最強機能】列名がズレていても強引に値を拾うファジーマッチ
def get_val(row_dict, possible_keys):
    for pk in possible_keys:
        for k, v in row_dict.items():
            if pk in k: return str(v).strip()
    return ""

VENUE_WATER_MAP = {
    "桐生": "淡水", "戸田": "淡水", "江戸川": "汽水", "平和島": "海水", "多摩川": "淡水", "浜名湖": "汽水", "蒲郡": "汽水", "常滑": "海水", 
    "津": "汽水", "三国": "淡水", "びわこ": "淡水", "住之江": "淡水", "尼崎": "淡水", "鳴門": "海水", "丸亀": "海水", "児島": "海水", 
    "宮島": "海水", "徳山": "海水", "下関": "海水", "若松": "海水", "芦屋": "淡水", "福岡": "汽水", "唐津": "淡水", "大村": "海水"
}
VENUE_WIND_MAP = {
    "桐生": {"tail": ["北", "北西", "北東"], "head": ["南", "南西", "南東"]}, "戸田": {"tail": ["北", "北西", "北東"], "head": ["南", "南西", "南東"]},
    "江戸川": {"tail": ["北", "北西"], "head": ["南", "南東"]}, "平和島": {"tail": ["北", "北東"], "head": ["南", "南西"]},
    "多摩川": {"tail": ["北", "北西"], "head": ["南", "南東"]}, "浜名湖": {"tail": ["北", "北西"], "head": ["南", "南東"]},
    "蒲郡": {"tail": ["北", "北西"], "head": ["南", "南東"]}, "常滑": {"tail": ["北", "北西"], "head": ["南", "南東"]},
    "津": {"tail": ["北", "北西"], "head": ["南", "南東"]}, "三国": {"tail": ["北", "北西", "西"], "head": ["南", "南東", "東"]},
    "びわこ": {"tail": ["北", "北東"], "head": ["南", "南西"]}, "住之江": {"tail": ["北", "北西"], "head": ["南", "南東"]},
    "尼崎": {"tail": ["北", "北西"], "head": ["南", "南東"]}, "鳴門": {"tail": ["北", "北西"], "head": ["南", "南東"]},
    "丸亀": {"tail": ["北", "北西"], "head": ["南", "南東"]}, "児島": {"tail": ["北", "北西"], "head": ["南", "南東"]},
    "宮島": {"tail": ["北", "北東"], "head": ["南", "南西"]}, "徳山": {"tail": ["西", "北西"], "head": ["東", "南東"]},
    "下関": {"tail": ["西", "北西"], "head": ["東", "南東"]}, "若松": {"tail": ["北", "北西"], "head": ["南", "南東"]},
    "芦屋": {"tail": ["北", "北西"], "head": ["南", "南東"]}, "福岡": {"tail": ["北", "北東"], "head": ["南", "南西"]},
    "唐津": {"tail": ["西", "北西", "南西"], "head": ["東", "南東", "北東"]}, "大村": {"tail": ["北", "北西", "北東"], "head": ["南", "南西", "南東"]}
}

def get_wind_type(venue, raw_dir):
    if not raw_dir: return "無風/横風"
    raw_dir = str(raw_dir).strip()
    numeric_wind_map = {"1": "北", "2": "北北東", "3": "北東", "4": "東北東", "5": "東", "6": "東南東", "7": "南東", "8": "南南東", "9": "南", "10": "南南西", "11": "南西", "12": "西南西", "13": "西", "14": "西北西", "15": "北西", "16": "北北西"}
    if raw_dir in numeric_wind_map: raw_dir = numeric_wind_map[raw_dir]
    if raw_dir == "無風" or raw_dir == "0": return "無風/横風"
    v_map = VENUE_WIND_MAP.get(venue)
    if not v_map: return "無風/横風"
    for t_dir in v_map["tail"]:
        if t_dir in raw_dir: return "追い風"
    for h_dir in v_map["head"]:
        if h_dir in raw_dir: return "向かい風"
    return "無風/横風"

def safe_float(val):
    try: return float(str(val).strip().translate(str.maketrans('１２３４５６７８９０．', '1234567890.')))
    except: return None

def safe_int(val):
    try:
        c = str(val).strip().translate(str.maketrans('１２３４５６７８９０', '1234567890'))
        if c.endswith('.0'): c = c[:-2]
        return int(c)
    except: return None

st.markdown("<h1 style='text-align: center; color: #facc15;'>⚡ 12TUELVUN</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>大衆の予想を出し抜き、己の力で水面を支配するための絶対領域。</p>", unsafe_allow_html=True)
st.divider()

venue_options = ["桐生", "戸田", "江戸川", "平和島", "多摩川", "浜名湖", "蒲郡", "常滑", "津", "三国", "びわこ", "住之江", "尼崎", "鳴門", "丸亀", "児島", "宮島", "徳山", "下関", "若松", "芦屋", "福岡", "唐津", "大村"]
venue = st.selectbox("🏁 レース場", venue_options, index=venue_options.index("福岡"))

default_water = "汽水" if "汽水" in VENUE_WATER_MAP.get(venue, "") else "淡水" if "淡水" in VENUE_WATER_MAP.get(venue, "") else "海水"
water_opts = ["海水 (浮力大/体重差減/柔らかい)", "淡水 (浮力小/体重差大/硬い)", "汽水 (混合/時間帯で変化)", "指定なし (全水質)"]
tide_opts = ["大潮・満潮 (水面不安定/イン・差し)", "大潮・干潮 (水面フラット/まくり)", "中潮/小潮 (標準的な潮位)", "潮の影響なし (淡水プール等)", "指定なし (全潮位)"]

col1, col2 = st.columns(2)
with col1:
    time_raw = st.selectbox("⌚ 時間帯", ["モーニング (朝 / イン堅守)", "デイ (昼 / モーター垂れ)", "サンセット (夕暮れ / 西日魔境)", "ナイター (夜 / モーター覚醒)", "指定なし (全時間帯)"], index=1)
    season_raw = st.selectbox("🌡️ 気温", ["30度以上 (猛暑)", "25〜30度 (夏)", "20〜25度 (初夏/秋口)", "15〜20度 (春/秋)", "10〜15度 (冬/春先)", "5〜10度 (真冬)", "5度未満 (極寒)", "指定なし (全気温)"], index=3)
    water_temp_raw = st.selectbox("🧊 水温", ["5度未満 (極冷/モーター超抜)", "5〜10度 (冷/モーター好調)", "10〜15度 (やや冷)", "15〜20度 (標準)", "20〜25度 (やや温)", "25〜30度 (温/モーター垂れ)", "30度以上 (極温/ダッシュ絶望)", "指定なし (全水温)"], index=3)
    weather_raw = st.selectbox("☔ 天候", ["晴 (良水面)", "曇 (良水面)", "雨 (視界不良/波乱)", "雪 (極寒/大波乱)", "指定なし (全天候)"])
    press_raw = st.selectbox("☁️ 気圧", ["1000hPa未満 (台風級)", "1000〜1005hPa (低気圧)", "1005〜1010hPa (やや低気圧)", "1010〜1015hPa (標準)", "1015〜1020hPa (やや高気圧)", "1020hPa以上 (高気圧)", "指定なし (全気圧)"], index=3)
    humidity_raw = st.selectbox("💧 湿度", ["30%未満 (超乾燥)", "30〜45% (乾燥)", "45〜60% (標準)", "60〜75% (やや多湿)", "75%以上 (多湿/雨天)", "指定なし (全湿度)"], index=2)
with col2:
    water_qual_raw = st.selectbox("🧪 水質", water_opts, index=0 if default_water=="海水" else 1 if default_water=="淡水" else 2)
    def_tide_idx = 3 if default_water=="淡水" else 2
    tide_raw = st.selectbox("🌊 潮見", tide_opts, index=def_tide_idx)
    wind_spd_raw = st.selectbox("💨 風速", ["0m (無風)", "1m (微風)", "2m (弱風)", "3m (普通)", "4m (やや強風)", "5m (強風)", "6m (超強風)", "7m以上 (暴風)", "指定なし (全風速)"], index=2)
    wind_dir_raw = st.selectbox("🧭 風向", ["向かい風", "追い風", "横風/無風", "指定なし (全風向)"])
    wave_raw = st.selectbox("🌊 波高", ["0cm (ベタ水面)", "1cm (穏やか)", "2cm (微波)", "3cm (やや波)", "4cm (波あり)", "5cm (荒波)", "6cm以上 (大荒れ)", "指定なし (全波高)"], index=2)
    exhibit_raw = st.selectbox("📊 展示トップ", ["1号艇が展示トップ", "2号艇が展示トップ", "3号艇が展示トップ", "4号艇が展示トップ", "5号艇が展示トップ", "6号艇が展示トップ", "指定なし (全レース)"], index=6)

st.markdown("<br>", unsafe_allow_html=True)

if database_ready:
    if st.button("⚡ 12TUELVUN 解析を実行", use_container_width=True):
        stats_exact = {str(i): {"count": 0, "wins": 0, "kimarite": defaultdict(int)} for i in range(1, 7)}
        stats_broad = {str(i): {"count": 0, "wins": 0, "kimarite": defaultdict(int)} for i in range(1, 7)}
        venue_baseline = {str(i): {"count": 0, "wins": 0} for i in range(1, 7)}
        match_counts = {"exact": 0, "broad": 0}
        venue_rows_count = 0

        with st.spinner("🔍 強靭なセンサーでデータをスキャン中..."):
            try:
                races_in_memory = defaultdict(list)
                detected_enc = detect_encoding(CSV_FILE)
                
                with open(CSV_FILE, "r", encoding=detected_enc, errors="replace") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # 💡 BOMや余計な空白を完全除去したクリーン辞書を作成
                        clean_r = {str(k).strip('\ufeff').strip(): str(v).strip() for k, v in row.items() if k}
                        
                        # 💡 センサー1：列名がわからなくても、値の中に「福岡」があれば強引に拾う
                        v_match = False
                        for val in clean_r.values():
                            if venue in str(val):
                                v_match = True
                                break
                        if not v_match: continue
                        
                        venue_rows_count += 1
                        
                        # 💡 センサー2：日付とレース番号を強引に特定する
                        d_val, r_val = "", ""
                        for k, v in clean_r.items():
                            if "日" in k: d_val = v
                            elif "レース番" in k or "R" in k or "番" in k: r_val = v
                        if not d_val: d_val = "unknown_date"
                        if not r_val: r_val = "unknown_race"
                        
                        r_id = f"{d_val}_{r_val}"
                        races_in_memory[r_id].append(clean_r)

                if venue_rows_count == 0:
                    st.error(f"🚨 【致命的エラー】データの中に「{venue}」のレースが1件も見つかりませんでした。データが空か、異常な文字化けを起こしています。")
                    with st.expander("🛠️ 読み込んだ生データの一部を確認する（原因特定用）"):
                        with open(CSV_FILE, "r", encoding=detected_enc, errors="replace") as f:
                            st.text(f.read(1000))
                    st.stop()

                for r_id, rows in races_in_memory.items():
                    if not rows: continue
                    first_row = rows[0]
                    
                    for r in rows:
                        b_num = get_val(r, ["艇番", "号艇", "艇", "枠"])
                        b_num = re.search(r'[1-6]', b_num).group(0) if re.search(r'[1-6]', b_num) else ""
                        is_win = ("1" in get_val(r, ["着順", "着"]))
                        
                        if b_num in venue_baseline:
                            venue_baseline[b_num]["count"] += 1
                            if is_win: venue_baseline[b_num]["wins"] += 1
                    
                    temp = safe_float(get_val(first_row, ["気温", "気"]))
                    w_temp = safe_float(get_val(first_row, ["水温", "水"]))
                    press = safe_float(get_val(first_row, ["気圧", "圧"]))
                    humidity = safe_float(get_val(first_row, ["湿度", "湿"]))
                    wind_speed = safe_int(get_val(first_row, ["風速", "速"]))
                    wave = safe_int(get_val(first_row, ["波高", "波"]))
                    actual_weather = str(get_val(first_row, ["天候", "天"]))
                    raw_wind_direction = str(get_val(first_row, ["風向", "向"]))
                    
                    if wind_speed is None: wind_speed = 0
                    if wave is None: wave = 0

                    times = []
                    for r in rows:
                        b = get_val(r, ["艇番", "号艇", "艇", "枠"])
                        b = re.search(r'[1-6]', b).group(0) if re.search(r'[1-6]', b) else ""
                        t = safe_float(get_val(r, ["展示", "展"]))
                        if b and t is not None: times.append((b, t))
                    times.sort(key=lambda x: x[1])
                    fastest_boat = times[0][0] if times else None

                    is_broad_match = True
                    if "指定なし" not in wind_dir_raw:
                        translated_dir = get_wind_type(venue, raw_wind_direction)
                        if "向かい風" in wind_dir_raw and translated_dir != "向かい風": is_broad_match = False
                        elif "追い風" in wind_dir_raw and translated_dir != "追い風": is_broad_match = False
                        elif "横風" in wind_dir_raw and translated_dir != "無風/横風": is_broad_match = False

                    if "指定なし" not in exhibit_raw:
                        target_boat = exhibit_raw.split("号艇")[0]
                        if fastest_boat != target_boat: is_broad_match = False

                    is_exact_match = is_broad_match
                    if is_exact_match:
                        if "指定なし" not in wave_raw:
                            wave_num_str = wave_raw.split("cm")[0]
                            if "以上" in wave_raw:
                                if wave < float(wave_num_str): is_exact_match = False
                            else:
                                if wave != float(wave_num_str): is_exact_match = False
                        if "指定なし" not in season_raw:
                            if temp is None: is_exact_match = False
                            elif "未満" in season_raw and temp >= 5.0: is_exact_match = False
                            elif "5〜10度" in season_raw and not (5.0 <= temp < 10.0): is_exact_match = False
                            elif "10〜15度" in season_raw and not (10.0 <= temp < 15.0): is_exact_match = False
                            elif "15〜20度" in season_raw and not (15.0 <= temp < 20.0): is_exact_match = False
                            elif "20〜25度" in season_raw and not (20.0 <= temp < 25.0): is_exact_match = False
                            elif "25〜30度" in season_raw and not (25.0 <= temp < 30.0): is_exact_match = False
                            elif "30度以上" in season_raw and temp < 30.0: is_exact_match = False
                        if "指定なし" not in water_temp_raw:
                            if w_temp is None: is_exact_match = False
                            elif "未満" in water_temp_raw and w_temp >= 5.0: is_exact_match = False
                            elif "5〜10度" in water_temp_raw and not (5.0 <= w_temp < 10.0): is_exact_match = False
                            elif "10〜15度" in water_temp_raw and not (10.0 <= w_temp < 15.0): is_exact_match = False
                            elif "15〜20度" in water_temp_raw and not (15.0 <= w_temp < 20.0): is_exact_match = False
                            elif "20〜25度" in water_temp_raw and not (20.0 <= w_temp < 25.0): is_exact_match = False
                            elif "25〜30度" in water_temp_raw and not (25.0 <= w_temp < 30.0): is_exact_match = False
                            elif "30度以上" in water_temp_raw and w_temp < 30.0: is_exact_match = False
                        if "指定なし" not in weather_raw:
                            if "晴" in weather_raw and "晴" not in actual_weather: is_exact_match = False
                            if "曇" in weather_raw and "曇" not in actual_weather: is_exact_match = False
                            if "雨" in weather_raw and "雨" not in actual_weather: is_exact_match = False
                            if "雪" in weather_raw and "雪" not in actual_weather: is_exact_match = False
                        if "指定なし" not in press_raw:
                            if press is None: is_exact_match = False
                            elif "1000hPa未満" in press_raw and press >= 1000.0: is_exact_match = False
                            elif "1000〜1005" in press_raw and not (1000.0 <= press < 1005.0): is_exact_match = False
                            elif "1005〜1010" in press_raw and not (1005.0 <= press < 1010.0): is_exact_match = False
                            elif "1010〜1015" in press_raw and not (1010.0 <= press < 1015.0): is_exact_match = False
                            elif "1015〜1020" in press_raw and not (1015.0 <= press < 1020.0): is_exact_match = False
                            elif "1020hPa以上" in press_raw and press < 1020.0: is_exact_match = False
                        if "指定なし" not in humidity_raw:
                            if humidity is None: is_exact_match = False
                            elif "30%未満" in humidity_raw and humidity >= 30.0: is_exact_match = False
                            elif "30〜45%" in humidity_raw and not (30.0 <= humidity < 45.0): is_exact_match = False
                            elif "45〜60%" in humidity_raw and not (45.0 <= humidity < 60.0): is_exact_match = False
                            elif "60〜75%" in humidity_raw and not (60.0 <= humidity < 75.0): is_exact_match = False
                            elif "75%以上" in humidity_raw and humidity < 75.0: is_exact_match = False
                        if "指定なし" not in wind_spd_raw:
                            wind_num = wind_spd_raw.split("m")[0]
                            if "以上" in wind_spd_raw:
                                if wind_speed < float(wind_num): is_exact_match = False
                            else:
                                if wind_speed != float(wind_num): is_exact_match = False

                    if is_broad_match: match_counts["broad"] += 1
                    if is_exact_match: match_counts["exact"] += 1

                    if is_broad_match or is_exact_match:
                        for r in rows:
                            b_num = get_val(r, ["艇番", "号艇", "艇", "枠"])
                            b_num = re.search(r'[1-6]', b_num).group(0) if re.search(r'[1-6]', b_num) else ""
                            if not b_num: continue
                            is_win = ("1" in get_val(r, ["着順", "着"]))
                            k = get_val(r, ["決まり手", "決"])
                            if is_broad_match:
                                stats_broad[b_num]["count"] += 1
                                if is_win:
                                    stats_broad[b_num]["wins"] += 1
                                    if k and k != "不明": stats_broad[b_num]["kimarite"][k] += 1
                            if is_exact_match:
                                stats_exact[b_num]["count"] += 1
                                if is_win:
                                    stats_exact[b_num]["wins"] += 1
                                    if k and k != "不明": stats_exact[b_num]["kimarite"][k] += 1

                final_stats = stats_exact
                fallback_used = False
                total_hits_races = match_counts["exact"]

                if total_hits_races < 30:
                    if match_counts["broad"] > 0:
                        final_stats = stats_broad
                        fallback_used = True
                        total_hits_races = match_counts["broad"]

                total_wins = 0
                all_kimarite = defaultdict(int)
                for b, s in final_stats.items():
                    total_wins += s["wins"]
                    for k, v in s["kimarite"].items():
                        all_kimarite[k] += v
                
                top_kimarite = sorted(all_kimarite.items(), key=lambda x: x[1], reverse=True)[:3]
                k_str = "、".join([f"{k}({round(c/total_wins*100)}%)" for k, c in top_kimarite]) if total_wins > 0 else "過去データ該当なし"

                ai_time = time_raw.split(' ')[0]
                ai_season = season_raw.split(' ')[0]
                ai_w_temp = water_temp_raw.split(' ')[0]
                ai_w_qual = water_qual_raw.split(' ')[0]
                ai_press = press_raw.split(' ')[0]
                ai_humid = humidity_raw.split(' ')[0]
                ai_wind_spd = wind_spd_raw.split(' ')[0]
                ai_wave = wave_raw.split(' ')[0]
                ai_tide = tide_raw.split(' ')[0]

                profiling_html = []
                def add_prof(title, desc, color="#d1d5db"):
                    profiling_html.append(f"<div style='margin-bottom: 8px;'><strong style='color:#fcd34d;'>{title}</strong><br><span style='color:{color};'>└ {desc}</span></div>")
                
                add_prof(f"📍 レース場 【{venue}】", "うねりと独特の風が複雑に絡む超・難水面。1マークの振り幅が大きく、ダッシュ勢のまくり・まくり差しが炸裂する。" if venue == "福岡" else "")
                
                if "指定なし" not in time_raw:
                    if "モーニング" in time_raw: add_prof(f"⌚ 時間帯 【{time_raw}】", f"【{ai_time}の特性】 気温が上がり切る前の特有の静けさが支配する水面です。モーターの体積効率が良く、セオリー通りイン逃げが決まりやすいベース条件となります。")
                    elif "デイ" in time_raw: add_prof(f"⌚ 時間帯 【{time_raw}】", f"【{ai_time}の特性】 気温と水温がピークに達し、モーターが最も『ダレる』過酷な時間帯です。スロー勢の出足が甘くなりやすく、波乱の引き金が引かれやすい環境です。")
                    elif "サンセット" in time_raw: add_prof(f"⌚ 時間帯 【{time_raw}】", f"⚠️ 【{ai_time}の魔境】 強烈な西日が水面に乱反射し、大時計とスリットラインの視認性を極端に奪います。選手のスタート勘が狂い、予期せぬドカ遅れ（凹み）が多発する魔の時間帯です。", "#ef4444")
                    elif "ナイター" in time_raw: add_prof(f"⌚ 時間帯 【{time_raw}】", f"【{ai_time}の特性】 日没とともに気温が急低下。冷えた空気を吸い込むことでモーターの体積効率が限界突破し、出足・行き足が復活します。インの信頼度が増すと同時に、強烈なスピード戦が展開されます。", "#22d3ee")
                else: add_prof(f"⌚ 時間帯 【{time_raw}】", "時間帯による条件の絞り込みを行わず、全時間帯を対象に分析しています。")

                if "指定なし" not in water_qual_raw:
                    if "海水" in water_qual_raw: add_prof(f"🧪 水質・比重 【{water_qual_raw}】", f"【{ai_w_qual}の物理特性】 塩分による浮力が大きく、体重の重い選手でも不利になりにくい環境です。水質が柔らかいため、スピードに乗った思い切った全速ターンが決まりやすくなります。")
                    elif "淡水" in water_qual_raw: add_prof(f"🧪 水質・比重 【{water_qual_raw}】", f"【{ai_w_qual}の物理特性】 浮力が小さいため体重差がモロに出ます。水質が硬く艇が跳ねやすいため、モーターの『乗り心地』や『回り足』の差が露骨に結果を左右するシビアな水面です。")
                    elif "汽水" in water_qual_raw: add_prof(f"🧪 水質・比重 【{water_qual_raw}】", f"【{ai_w_qual}の物理特性】 海水と淡水が混ざり合い、時間帯や潮の満ち引きによって水面の硬さや浮力が変化する、極めて難解でテクニカルな水面です。")
                else: add_prof(f"🧪 水質・比重 【{water_qual_raw}】", "水質による条件の絞り込みを行わず、全水質を対象に分析しています。")

                if "指定なし" not in season_raw:
                    if "25" in season_raw or "30" in season_raw: add_prof(f"🌡️ 気温 【{season_raw}】", f"【{ai_season}の環境】 空気体積が膨張し密度が低下。モーターの燃焼効率が落ち、ダッシュ勢の行き足がつきにくい過酷な条件です。")
                    elif "15" in season_raw or "20" in season_raw: add_prof(f"🌡️ 気温 【{season_raw}】", f"【{ai_season}の環境】 モーター調整がしやすく、選手間の機力差がそのまま結果に直結しやすいフラットなベース条件です。")
                    else: add_prof(f"🌡️ 気温 【{season_raw}】", f"【{ai_season}の環境】 空気が収縮して密度が上がり、燃焼効率が最大化。全艇のパワーが底上げされスピード戦になりやすい条件です。")
                else: add_prof(f"🌡️ 気温 【{season_raw}】", "気温による条件の絞り込みを行わず、すべての季節を対象に分析しています。")

                if "指定なし" not in water_temp_raw:
                    if "25" in water_temp_raw or "30" in water_temp_raw: add_prof(f"🧊 水温 【{water_temp_raw}】", f"【{ai_w_temp}の熱力学】 水温が高く、モーターの冷却効率が著しく低下します。エンジンの体積効率が下がり『ダレる』ため、特に助走の短いインコースの出足に深刻なダメージを与えます。")
                    elif "15" in water_temp_raw or "20" in water_temp_raw: add_prof(f"🧊 水温 【{water_temp_raw}】", f"【{ai_w_temp}の熱力学】 水温として標準的であり、モーターの冷却効率に極端な偏りは出ません。機力の素性が素直に反映されます。")
                    else: add_prof(f"🧊 水温 【{water_temp_raw}】", f"【{ai_w_temp}の熱力学】 水が冷たく、モーターがキンキンに冷却されます。シリンダー内の体積効率が限界まで高まり、出足から行き足にかけてのパワーが底上げされるため、内枠が強力なアドバンテージを得ます。")
                else: add_prof(f"🧊 水温 【{water_temp_raw}】", "水温による条件の絞り込みを行わず、全水温を対象に分析しています。")

                if "向かい風" in wind_dir_raw: add_prof(f"💨 風向・風速 【{wind_dir_raw} / {wind_spd_raw}】", f"⚠️ 【{ai_wind_spd}の向かい風】 スタートラインに向かって吹く風がスローの初速を殺します。逆に助走を取ったダッシュ勢はトップスピードでスリットを通過するため、強烈な『まくり』のベクトルが働きます。", "#ef4444")
                elif "追い風" in wind_dir_raw: add_prof(f"💨 風向・風速 【{wind_dir_raw} / {wind_spd_raw}】", f"⚠️ 【{ai_wind_spd}の追い風】 インコースが加速しやすい反面、第1ターンマークでブレーキが利かず外に膨らむ物理法則が働きます。その懐を突く『差し』『まくり差し』に警戒が必要です。", "#fcd34d")
                else: add_prof(f"💨 風向・風速 【{wind_dir_raw} / {wind_spd_raw}】", f"【{ai_wind_spd}の風】 風の影響は限定的であり、純粋なモーター機力とコースのセオリー勝負になります。")

                if "指定なし" not in exhibit_raw:
                    keyman = exhibit_raw.split('が')[0]
                    add_prof(f"⏱️ 展示トップ 【{exhibit_raw}】", f"上記の複雑な環境下で、【{keyman}】が最速の行き足を叩き出しています。この艇の仕掛けが最大のトリガーです。", "#22d3ee")

                ai_story = "【AIドラマ生成中...】"
                if API_KEY:
                    try:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
                        prompt = f"""
                        あなたは水面の「事実」だけを刻む独自の予測システム【12TUELVUN】のコアAIです。
                        レース場: {venue}, 時間帯: 【{ai_time}】, 気温: 【{ai_season}】, 水温: 【{ai_w_temp}】, 水質: 【{ai_w_qual}】, 気圧: 【{ai_press}】, 湿度: 【{ai_humid}】, 風向: 【{wind_dir_raw}】, 風速: 【{ai_wind_spd}】, 波高: 【{ai_wave}】, 潮回り: 【{ai_tide}】, 展示トップ: {exhibit_raw}, 頻発する決まり手: {k_str}

                        1. 冒頭は「今、ひとりでこの分析画面を見つめているあなたなら、もう気づいているはずだ。毎日ただ単純な予想に頼り、思考停止で負け続ける日々はもう終わりにしよう。12TUELVUNは過去10年以上の膨大なデータと物理法則から、プロの環境認識を完全に代行する。」で始めること。
                        2. 指定された時間帯、水温、水質、気圧、風速、潮回りの数値を必ず文章内で使って解説。
                        3. お金や賭けの用語は一切使わず、純粋な水面のドラマとして500文字程度で出力。
                        4. 最後は「他人の予想にすがるのは、もう終わりにしよう。スリットを通過するまでの『12秒間』。己の決断だけを信じ、あの絶対領域を支配しろ。プロの視座とあなたの直感が交差した時、究極の一撃が水面を切り裂く。さあ、極限の没入を味わえ。」で締めくくること。
                        """
                        data = {"contents": [{"parts": [{"text": prompt}]}]}
                        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')
                        ctx_ai = ssl.create_default_context()
                        ctx_ai.check_hostname = False
                        ctx_ai.verify_mode = ssl.CERT_NONE
                        with urllib.request.urlopen(req, context=ctx_ai) as response:
                            result = json.loads(response.read().decode('utf-8'))
                            ai_story = result['candidates'][0]['content']['parts'][0]['text']
                    except urllib.error.HTTPError as e:
                        err_body = e.read().decode('utf-8')
                        ai_story = f"⚠️ 【AI通信エラー】GoogleのAIが混み合っているか、拒否されました。\n[詳細]:\n{err_body}"
                    except Exception as e:
                        ai_story = f"⚠️ 【AI通信エラー】通信に失敗しました。\n[詳細]: {str(e)}"
                else:
                    ai_story = "⚠️ 【AI待機中】システム設定のコード内にAPIキーが設定されていません。"

            except Exception as e:
                st.error(f"データ解析中にエラーが発生しました: {str(e)}")
                st.stop()

        st.markdown("---")
        st.subheader("👁️‍🗨️ 12TUELVUN: ABSOLUTE DOMAIN")
        
        if total_hits_races == 0:
            st.warning("⚠️ 【データ未観測領域】 過去10年に存在しない極限数値です。理論値プロファイリングのみを実行します。")
        elif fallback_used:
            st.info(f"⚠️ 【広域データ抽出】 完全一致データが少なかったため、勝敗を分ける核となる【風向・展示】の事実を広域抽出しました。")
        if venue_rows_count > 0:
            st.success(f"📊 データベース: {venue}の全 {venue_rows_count:,} レースから抽出完了 / 類似環境抽出 {total_hits_races:,} レース")

        st.markdown("#### 【🎓 環境プロファイリング（数値解析）】")
        for p_html in profiling_html:
            st.markdown(p_html, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 【🔥 極限展開予測】")
        st.write(ai_story)

        st.markdown("---")
        st.markdown("#### ▼ 水面の事実（特異勝率データ）")
        
        for b_num in range(1, 7):
            s = final_stats[str(b_num)]
            win_rate = round(s["wins"] / s["count"] * 100, 1) if s["count"] > 0 else 0.0
            
            base_s = venue_baseline[str(b_num)]
            base_win_rate = round(base_s["wins"] / base_s["count"] * 100, 1) if base_s["count"] > 0 else 0.0
            
            diff = round(win_rate - base_win_rate, 1)
            diff_str = f"+{diff}" if diff > 0 else str(diff)

            if total_hits_races == 0:
                st.markdown(f"**🚤 [ {b_num}号艇 ]** | 該当データなし")
            else:
                color = "#4ade80" if diff > 0 else "#94a3b8"
                st.markdown(f"<span style='color:{color}; font-weight:bold;'>🚤 [ {b_num}号艇 ] | この条件下の勝率: {win_rate}% (平常時: {base_win_rate}% [{diff_str}%])</span>", unsafe_allow_html=True)
                if s["wins"] > 0:
                    kimarite_sorted = sorted(s["kimarite"].items(), key=lambda x: x[1], reverse=True)[:2]
                    k_text = " / ".join([f"{k}({round(c/s['wins']*100)}%)" for k, c in kimarite_sorted])
                    st.caption(f"└─ 特異決まり手: {k_text}")
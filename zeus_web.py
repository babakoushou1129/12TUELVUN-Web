import streamlit as st
import csv
from collections import defaultdict
import os
import urllib.request
import urllib.error
import json
import ssl
import gdown

# --- 究極クラウド設定 ---
DRIVE_FILE_ID = "1tWVFol3GauZdrUIJ_w_OKM9AZSQLbswG"
CSV_FILE = "ZEUS_10Years_Master_FINAL_PERFECT.csv"

st.set_page_config(page_title="12TUELVUN", page_icon="⚡", layout="centered")

# 💡 サイドバーにAIキー入力欄を設置
with st.sidebar:
    st.markdown("### 🔑 システム設定")
    st.markdown("セキュリティ保護のため、AIキーはここに入力してください。")
    API_KEY = st.text_input("Gemini APIキー", type="password").strip()

# --- 巨大データ自動同期ロジック ---
def sync_database_from_cloud():
    if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 100 * 1024 * 1024:
        return True
        
    with st.spinner("☁️ クラウドの特大データベース（541MB）と同期中...（約1〜3分）"):
        try:
            gdown.download(id=DRIVE_FILE_ID, output=CSV_FILE, quiet=False)
            if os.path.exists(CSV_FILE) and os.path.getsize(CSV_FILE) > 100 * 1024 * 1024:
                return True
            else:
                st.error("❌ ダウンロードが不完全です。再読み込みしてください。")
                if os.path.exists(CSV_FILE):
                    os.remove(CSV_FILE)
                return False
        except Exception as e:
            st.error(f"❌ クラウドデータの同期に失敗しました。[エラー詳細]: {e}")
            return False

database_ready = sync_database_from_cloud()

# --- 💡 強制データクレンジング関数（どんな汚れたCSVデータも正確に読み取る） ---
def clean_boat_num(val):
    if not val: return None
    v = str(val).strip().translate(str.maketrans('１２３４５６', '123456'))
    if v.endswith('.0'): v = v[:-2]
    return v if v in ["1", "2", "3", "4", "5", "6"] else None

def is_winning_rank(val):
    if not val: return False
    v = str(val).strip().translate(str.maketrans('１２３４５６７８９０', '1234567890'))
    if v.endswith('.0'): v = v[:-2]
    return v in ["1", "01"]

# --- マスターデータ ---
VENUE_WATER_MAP = {
    "桐生": "淡水 (浮力小/体重差大/硬い)", "戸田": "淡水 (浮力小/体重差大/硬い)", 
    "江戸川": "汽水 (混合/時間帯で変化)", "平和島": "海水 (浮力大/体重差減/柔らかい)", 
    "多摩川": "淡水 (浮力小/体重差大/硬い)", "浜名湖": "汽水 (混合/時間帯で変化)", 
    "蒲郡": "汽水 (混合/時間帯で変化)", "常滑": "海水 (浮力大/体重差減/柔らかい)", 
    "津": "汽水 (混合/時間帯で変化)", "三国": "淡水 (浮力小/体重差大/硬い)", 
    "びわこ": "淡水 (浮力小/体重差大/硬い)", "住之江": "淡水 (浮力小/体重差大/硬い)", 
    "尼崎": "淡水 (浮力小/体重差大/硬い)", "鳴門": "海水 (浮力大/体重差減/柔らかい)", 
    "丸亀": "海水 (浮力大/体重差減/柔らかい)", "児島": "海水 (浮力大/体重差減/柔らかい)", 
    "宮島": "海水 (浮力大/体重差減/柔らかい)", "徳山": "海水 (浮力大/体重差減/柔らかい)", 
    "下関": "海水 (浮力大/体重差減/柔らかい)", "若松": "海水 (浮力大/体重差減/柔らかい)", 
    "芦屋": "淡水 (浮力小/体重差大/硬い)", "福岡": "汽水 (混合/時間帯で変化)", 
    "唐津": "淡水 (浮力小/体重差大/硬い)", "大村": "海水 (浮力大/体重差減/柔らかい)"
}

VENUE_WIND_MAP = {
    "桐生": {"tail": ["北", "北西", "北東"], "head": ["南", "南西", "南東"]},
    "戸田": {"tail": ["北", "北西", "北東"], "head": ["南", "南西", "南東"]},
    "江戸川": {"tail": ["北", "北西"], "head": ["南", "南東"]},
    "平和島": {"tail": ["北", "北東"], "head": ["南", "南西"]},
    "多摩川": {"tail": ["北", "北西"], "head": ["南", "南東"]},
    "浜名湖": {"tail": ["北", "北西"], "head": ["南", "南東"]},
    "蒲郡": {"tail": ["北", "北西"], "head": ["南", "南東"]},
    "常滑": {"tail": ["北", "北西"], "head": ["南", "南東"]},
    "津": {"tail": ["北", "北西"], "head": ["南", "南東"]},
    "三国": {"tail": ["北", "北西", "西"], "head": ["南", "南東", "東"]},
    "びわこ": {"tail": ["北", "北東"], "head": ["南", "南西"]},
    "住之江": {"tail": ["北", "北西"], "head": ["南", "南東"]},
    "尼崎": {"tail": ["北", "北西"], "head": ["南", "南東"]},
    "鳴門": {"tail": ["北", "北西"], "head": ["南", "南東"]},
    "丸亀": {"tail": ["北", "北西"], "head": ["南", "南東"]},
    "児島": {"tail": ["北", "北西"], "head": ["南", "南東"]},
    "宮島": {"tail": ["北", "北東"], "head": ["南", "南西"]},
    "徳山": {"tail": ["西", "北西"], "head": ["東", "南東"]},
    "下関": {"tail": ["西", "北西"], "head": ["東", "南東"]},
    "若松": {"tail": ["北", "北西"], "head": ["南", "南東"]},
    "芦屋": {"tail": ["北", "北西"], "head": ["南", "南東"]},
    "福岡": {"tail": ["北", "北東"], "head": ["南", "南西"]},
    "唐津": {"tail": ["西", "北西", "南西"], "head": ["東", "南東", "北東"]},
    "大村": {"tail": ["北", "北西", "北東"], "head": ["南", "南西", "南東"]}
}

VENUE_PROFILE = {
    "桐生": "標高が高くモーターパワーが落ちる「標高マジック」あり。イン勝率は低めで、センターからの攻めが届きやすい。",
    "戸田": "コース幅が日本一狭く、1マークがスタンド側に寄っているためイン激弱。3・4コースからの強襲が頻発する波乱水面。",
    "江戸川": "河川を利用した日本屈指の難水面。潮の満ち引きと風が複雑に絡み、選手の「波乗り技術」が勝敗を分ける。",
    "平和島": "ビル風が舞う水面。イン勝率が全国ワーストクラスに低く、ダッシュ勢の「まくり差し」が全国一決まりやすい。",
    "多摩川": "日本一の静水面。スピード戦になりやすく全速ターンが決まるため、モーター素性とスピードがモロに結果に出る。",
    "浜名湖": "広大な汽水水面。スピードに乗ったダイナミックな旋回が多く、枠を問わず機力上位の選手が台頭しやすい。",
    "蒲郡": "ナイター開催で気温が下がりやすくモーターの出足が良い。インも強いが、スピード戦のまくりも決まるハイレベルな水面。",
    "常滑": "伊勢湾の海風が吹き込む。イン逃げが比較的強いが、向かい風が強まるとセンター勢の出番が急増する。",
    "津": "伊勢湾からの強風が吹き荒れる「風の津」。夏は追い風、冬は向かい風で展開がガラリと変わる荒れ水面。",
    "三国": "日本海側の強風と波の影響を受けやすい。イン勝率が高めだが、荒れ水面になるとベテランの差しが不気味に台頭する。",
    "びわこ": "標高が高く特有の「うねり」が発生。インが弱く、センター勢の強烈なまくりが飛び出す。",
    "住之江": "ボートレースの聖地。工業用水で水が硬くモーター差が出やすい。ナイター特有のインの強さが顕著。",
    "尼崎": "センターの「まくり」が決まりにくい静水面。インと2コースの差しが強く、堅い決着が多い本命党向け。",
    "鳴門": "潮の干満差が激しく、1マークが狭いためインが難しい。スロー勢がもたつくとアウトからの強襲が刺さる。",
    "丸亀": "満潮時はイン有利、干潮時はセンター有利と、時間帯で水面が豹変し狙い目が変わる。",
    "児島": "瀬戸内海の海水で干満差が2メートル以上。満潮時はイン逃げ・差し、干潮時はアウトのまくりがセオリー。",
    "宮島": "干満差が全国最大クラス。潮の動きでスタート勘が狂いやすく、思わぬダッシュからの波乱が起きる。",
    "徳山": "笠戸湾に面し風の影響を防ぐためイン勝率が非常に高い。「モーニング＝イン逃げ」が絶対的セオリー。",
    "下関": "LED照明が明るいナイター。海水だが波は穏やかで、イン勝率が全国トップクラスに高い「大本命水面」。",
    "若松": "潮の満ち引きがある海水ナイター。満潮はイン、干潮はまくり。時間帯と潮見表の確認が必須のテクニカル水面。",
    "芦屋": "1マークのバック側が広く、インが全速で余裕を持って回れるためイン勝率が極めて高い。本命党向け。",
    "福岡": "うねりと独特の風が複雑に絡む超・難水面。1マークの振り幅が大きく、ダッシュ勢のまくり・まくり差しが炸裂する。",
    "唐津": "ピットから1マークまでの距離が全国一遠く、助走が長いため「行き足」が超重要。モーニング特有のインの強さがある。",
    "大村": "全国No.1のイン勝率を誇る「絶対的イン天国」。風や波がよほど荒れない限り、イン逃げからどう絞るかの勝負。"
}

def get_wind_type(venue, raw_dir):
    if not raw_dir: return "無風/横風"
    raw_dir = str(raw_dir).strip()
    numeric_wind_map = {
        "1": "北", "2": "北北東", "3": "北東", "4": "東北東",
        "5": "東", "6": "東南東", "7": "南東", "8": "南南東",
        "9": "南", "10": "南南西", "11": "南西", "12": "西南西",
        "13": "西", "14": "西北西", "15": "北西", "16": "北北西"
    }
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
    try:
        clean_str = str(val).strip().translate(str.maketrans('１２３４５６７８９０．', '1234567890.'))
        return float(clean_str)
    except: return None

def safe_int(val):
    try:
        clean_str = str(val).strip().translate(str.maketrans('１２３４５６７８９０', '1234567890'))
        if clean_str.endswith('.0'): clean_str = clean_str[:-2]
        return int(clean_str)
    except: return None

# --- UIレイアウト構築 ---
st.markdown("<h1 style='text-align: center; color: #facc15;'>⚡ 12TUELVUN</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>大衆の予想を出し抜き、己の力で水面を支配するための絶対領域。</p>", unsafe_allow_html=True)
st.divider()

venue_options = ["桐生", "戸田", "江戸川", "平和島", "多摩川", "浜名湖", "蒲郡", "常滑", "津", "三国", "びわこ", "住之江", "尼崎", "鳴門", "丸亀", "児島", "宮島", "徳山", "下関", "若松", "芦屋", "福岡", "唐津", "大村"]
venue = st.selectbox("🏁 レース場", venue_options, index=1)

default_water = VENUE_WATER_MAP.get(venue, "淡水 (浮力小/体重差大/硬い)")
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
    water_qual_raw = st.selectbox("🧪 水質", water_opts, index=water_opts.index(default_water))
    def_tide_idx = 3 if "淡水" in default_water else 2
    tide_raw = st.selectbox("🌊 潮見", tide_opts, index=def_tide_idx)
    wind_spd_raw = st.selectbox("💨 風速", ["0m (無風)", "1m (微風)", "2m (弱風)", "3m (普通)", "4m (やや強風)", "5m (強風)", "6m (超強風)", "7m以上 (暴風)", "指定なし (全風速)"], index=2)
    wind_dir_raw = st.selectbox("🧭 風向", ["向かい風", "追い風", "横風/無風", "指定なし (全風向)"])
    wave_raw = st.selectbox("🌊 波高", ["0cm (ベタ水面)", "1cm (穏やか)", "2cm (微波)", "3cm (やや波)", "4cm (波あり)", "5cm (荒波)", "6cm以上 (大荒れ)", "指定なし (全波高)"], index=2)
    exhibit_raw = st.selectbox("📊 展示トップ", ["1号艇が展示トップ", "2号艇が展示トップ", "3号艇が展示トップ", "4号艇が展示トップ", "5号艇が展示トップ", "6号艇が展示トップ", "指定なし (全レース)"], index=6)

st.markdown("<br>", unsafe_allow_html=True)

if not database_ready:
    st.error("⚠️ データベースの同期が完了するまで、解析は実行できません。")
else:
    if st.button("⚡ 12TUELVUN 解析を実行", use_container_width=True):
        stats_exact = {str(i): {"count": 0, "wins": 0, "kimarite": defaultdict(int)} for i in range(1, 7)}
        stats_broad = {str(i): {"count": 0, "wins": 0, "kimarite": defaultdict(int)} for i in range(1, 7)}
        venue_baseline = {str(i): {"count": 0, "wins": 0} for i in range(1, 7)}
        
        matched_races_exact = 0
        matched_races_broad = 0

        with st.spinner("🔍 過去10年以上・339万件のデータをスキャン中..."):
            try:
                with open(CSV_FILE, "r", encoding="shift_jis", errors="replace") as f:
                    reader = csv.DictReader(f)
                    current_race_id = None
                    race_buffer = []

                    def analyze_buffered_race(rows):
                        global matched_races_exact, matched_races_broad
                        if not rows or rows[0].get("レース場") != venue: return
                        
                        first_row = rows[0]
                        # ベースライン集計
                        for r in rows:
                            b_num = clean_boat_num(r.get("艇番"))
                            if b_num in venue_baseline:
                                venue_baseline[b_num]["count"] += 1
                                if is_winning_rank(r.get("着順")):
                                    venue_baseline[b_num]["wins"] += 1
                        
                        temp = safe_float(first_row.get("気温"))
                        w_temp = safe_float(first_row.get("水温"))
                        press = safe_float(first_row.get("気圧"))
                        humidity = safe_float(first_row.get("湿度"))
                        wind_speed = safe_int(first_row.get("風速"))
                        wave = safe_int(first_row.get("波高"))
                        actual_weather = str(first_row.get("天候", ""))
                        raw_wind_direction = first_row.get("風向", "")

                        if wind_speed is None: wind_speed = 0
                        if wave is None: wave = 0

                        times = []
                        for r in rows:
                            b = clean_boat_num(r.get("艇番"))
                            t = safe_float(r.get("展示"))
                            if b and t is not None: times.append((b, t))
                        
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

                        if is_broad_match:
                            globals()['matched_races_broad'] += 1
                        if is_exact_match:
                            globals()['matched_races_exact'] += 1

                        if is_broad_match or is_exact_match:
                            for r in rows:
                                b_num = clean_boat_num(r.get("艇番"))
                                if not b_num: continue
                                is_win = is_winning_rank(r.get("着順"))
                                k = str(r.get("決まり手", "不明")).strip()
                                
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

                    for row in reader:
                        race_id = f"{row.get('日付')}_{row.get('レース場')}_{row.get('レース番号')}"
                        if current_race_id != race_id:
                            if race_buffer: analyze_buffered_race(race_buffer)
                            current_race_id = race_id
                            race_buffer = []
                        race_buffer.append(row)
                    if race_buffer: analyze_buffered_race(race_buffer)

                final_stats = stats_exact
                fallback_used = False
                total_hits_races = globals()['matched_races_exact']

                if total_hits_races < 30:
                    if globals()['matched_races_broad'] > 0:
                        final_stats = stats_broad
                        fallback_used = True
                        total_hits_races = globals()['matched_races_broad']

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
                
                add_prof(f"📍 レース場 【{venue}】", VENUE_PROFILE.get(venue, ""))
                
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

                is_tidal = venue in ["江戸川", "平和島", "浜名湖", "常滑", "鳴門", "丸亀", "児島", "宮島", "徳山", "下関", "若松", "福岡", "大村"]
                if not is_tidal: add_prof(f"🌊 潮回り・潮位 【{tide_raw}】", "【影響なし】 このレース場は淡水（プール等）のため、潮の干満による水面への直接的な影響はありません。風や気圧のデータを最優先に展開を構築します。", "#94a3b8")
                else:
                    if "指定なし" not in tide_raw:
                        if "満潮" in tide_raw: add_prof(f"🌊 潮回り・潮位 【{tide_raw}】", f"【{ai_tide}の影響】 水位が上がり、うねりや波が発生しやすい不安定な水面になります。ターンがバタつくため全速のまくりが外に流れやすく、インの『逃げ』や内を差す『差し』が圧倒的に有利な条件です。")
                        elif "干潮" in tide_raw: add_prof(f"🌊 潮回り・潮位 【{tide_raw}】", f"【{ai_tide}の影響】 水位が下がり、水面がフラットで穏やかになります。スピードに乗った全速ターンがバシバシ決まるため、センター〜アウトからの強烈な『まくり』が台頭する絶好の条件です。", "#ef4444")
                        else: add_prof(f"🌊 潮回り・潮位 【{tide_raw}】", f"【{ai_tide}の影響】 標準的な潮位であり、潮による極端な有利不利は発生しにくい水面状況です。")
                    else: add_prof(f"🌊 潮回り・潮位 【{tide_raw}】", "潮位による条件の絞り込みを行わず、全潮位を対象に分析しています。")

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

                if "指定なし" not in press_raw:
                    if "1000" in press_raw or "1005" in press_raw: add_prof(f"☁️ 気圧 【{press_raw}】", f"【{ai_press}の環境】 キャブレターの酸素吸入量が物理的に低下。スロットルを握った瞬間の『初速（出足）』がスカスカになる波乱水面です。")
                    elif "1015" in press_raw or "1020" in press_raw: add_prof(f"☁️ 気圧 【{press_raw}】", f"【{ai_press}の環境】 燃焼爆発力が最大化し、出足から行き足にかけてのパンチ力が桁違いになります。イン逃げが鉄板化しやすい条件です。")
                    else: add_prof(f"☁️ 気圧 【{press_raw}】", f"【{ai_press}の環境】 キャブレターへの吸気効率に極端な偏りはなく、モーター本来のパワー勝負になります。")
                else: add_prof(f"☁️ 気圧 【{press_raw}】", "気圧による条件の絞り込みを行わず、全気圧を対象に分析しています。")

                if "指定なし" not in humidity_raw:
                    if "60" in humidity_raw or "75" in humidity_raw: add_prof(f"💧 湿度 【{humidity_raw}】", f"【{ai_humid}の環境】 水分が酸素スペースを奪うため燃焼パワーが減衰。引き波を超えるパワーが求められるスロー勢には深刻なマイナス材料です。")
                    elif "30" in humidity_raw or "45" in humidity_raw: add_prof(f"💧 湿度 【{humidity_raw}】", f"【{ai_humid}の環境】 乾いた空気を吸い込むことで燃焼効率が上がり、インコースの初動加速を強烈に後押しする条件です。")
                    else: add_prof(f"💧 湿度 【{humidity_raw}】", f"【{ai_humid}の環境】 湿気によるパワー減衰は少なく、モーターの素性が素直に出やすい環境です。")
                else: add_prof(f"💧 湿度 【{humidity_raw}】", "湿度による条件の絞り込みを行わず、全湿度を対象に分析しています。")

                if "向かい風" in wind_dir_raw: add_prof(f"💨 風向・風速 【{wind_dir_raw} / {wind_spd_raw}】", f"⚠️ 【{ai_wind_spd}の向かい風】 スタートラインに向かって吹く風がスローの初速を殺します。逆に助走を取ったダッシュ勢はトップスピードでスリットを通過するため、強烈な『まくり』のベクトルが働きます。", "#ef4444")
                elif "追い風" in wind_dir_raw: add_prof(f"💨 風向・風速 【{wind_dir_raw} / {wind_spd_raw}】", f"⚠️ 【{ai_wind_spd}の追い風】 インコースが加速しやすい反面、第1ターンマークでブレーキが利かず外に膨らむ物理法則が働きます。その懐を突く『差し』『まくり差し』に警戒が必要です。", "#fcd34d")
                else: add_prof(f"💨 風向・風速 【{wind_dir_raw} / {wind_spd_raw}】", f"【{ai_wind_spd}の風】 風の影響は限定的であり、純粋なモーター機力とコースのセオリー勝負になります。")

                if "指定なし" not in wave_raw:
                    if "4" in wave_raw or "5" in wave_raw or "6" in wave_raw: add_prof(f"🌊 波高 【{wave_raw}】", f"【{ai_wave}の難水面】 艇がバウンドしやすく、全速ターンは弾かれて空転を起こしやすくなります。引き波を縫う『差し』が台頭します。", "#fcd34d")
                    elif "2" in wave_raw or "3" in wave_raw: add_prof(f"🌊 波高 【{wave_raw}】", f"【{ai_wave}の水面】 少しバタつくためターンの精度が問われます。荒れ水面を苦にしない選手の技量とモーターの『乗り心地』がモロに出ます。")
                    else: add_prof(f"🌊 波高 【{wave_raw}】", f"【{ai_wave}のベタ水面】 水面抵抗が極小。スピードに乗った全速ターンが決まりやすく、機力上位のまくり・まくり差しが美しく決まります。")

                if "指定なし" not in exhibit_raw:
                    keyman = exhibit_raw.split('が')[0]
                    add_prof(f"⏱️ 展示トップ 【{exhibit_raw}】", f"上記の複雑な環境下で、【{keyman}】が最速の行き足を叩き出しています。この艇の仕掛けが最大のトリガーです。", "#22d3ee")

                ai_story = "【AIドラマ生成中...】"
                if API_KEY:
                    try:
                        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={API_KEY}"
                        prompt = f"""
                        あなたは水面の「事実」だけを刻む独自の予測システム【12TUELVUN】のコアAIです。
                        レース場: {venue}
                        時間帯: 【{ai_time}】
                        気温: 【{ai_season}】
                        水温: 【{ai_w_temp}】
                        水質: 【{ai_w_qual}】
                        気圧: 【{ai_press}】
                        湿度: 【{ai_humid}】
                        風向: 【{wind_dir_raw}】
                        風速: 【{ai_wind_spd}】
                        波高: 【{ai_wave}】
                        潮回り: 【{ai_tide}】
                        展示トップ: {exhibit_raw}
                        頻発する決まり手: {k_str}

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
                        ai_story = f"⚠️ 【AI通信エラー】\nAPIキーの形式がおかしいか、Google側で拒否されました。\n\n[Googleからの返答]:\n{err_body}"
                    except Exception as e:
                        ai_story = f"⚠️ 【AI通信エラー】\n通信に失敗しました。\n\n[詳細]: {str(e)}"
                else:
                    ai_story = "⚠️ 【AI待機中】\n画面左側のメニュー（スマホの場合は左上の「＞」マーク）から、AI用のAPIキーを入力してください。"

            except Exception as e:
                st.error(f"データ解析中にエラーが発生しました: {str(e)}")
                st.stop()

        # --- 結果表示 ---
        st.markdown("---")
        st.subheader("👁️‍🗨️ 12TUELVUN: ABSOLUTE DOMAIN")
        
        if total_hits_races == 0:
            st.warning("⚠️ 【データ未観測領域】 過去10年に存在しない極限数値です。理論値プロファイリングのみを実行します。")
        elif fallback_used:
            st.info(f"⚠️ 【広域データ抽出】 完全一致データが少なかったため、過去10年以上の全339万レースから、勝敗を分ける核となる【風向・展示】の事実を広域抽出しました。")
        if total_hits_races > 0:
            st.success(f"📊 データベース: 過去10年以上・全339万レース以上 / 類似環境抽出 {total_hits_races:,} レース")

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
            # 💡 欠場等で母数が減るケースを考慮し、レース数ではなく「その艇が出走した数」を正確な分母にする
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
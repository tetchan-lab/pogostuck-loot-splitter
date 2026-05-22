import mss
import pytesseract
from PIL import Image
import socket
import time
import re

# === 設定 ===
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# @ の後の数字が表示されている領域（座標はキャリブレーション後に調整）
# top, left はウィンドウタイトルバー含む絶対座標
CAPTURE_REGION = {"top": 73, "left": 245, "width": 250, "height": 30}

# LiveSplit Server設定
LIVESPLIT_HOST = "localhost"
LIVESPLIT_PORT = 16834

MAX_LEVEL = 10    # 監視するレベル範囲
STABLE_COUNT = 2  # 同じ値がN回連続で出たら確定（誤認識フィルタ）

# ===========================

def send_livesplit(command: str):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((LIVESPLIT_HOST, LIVESPLIT_PORT))
            s.sendall((command + "\r\n").encode())
            print(f"  → LiveSplit送信: {command}")
    except Exception as e:
        print(f"[LiveSplit接続エラー] {e}")

def get_current_level(sct) -> int | None:
    screenshot = sct.grab(CAPTURE_REGION)
    img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

    # ★ 黄色テキストだけを白に、それ以外を黒にマスク
    import numpy as np
    arr = np.array(img)
    # ゲームUIの黄色: R>180, G>150, B<80
    yellow_mask = (arr[:,:,0] > 180) & (arr[:,:,1] > 150) & (arr[:,:,2] < 80)
    masked = np.zeros_like(arr)
    masked[yellow_mask] = [255, 255, 255]  # 黄色 → 白
    img = Image.fromarray(masked.astype(np.uint8), 'RGB')

    # 拡大してOCR精度UP
    img = img.resize((img.width * 3, img.height * 3), Image.NEAREST)

    text = pytesseract.image_to_string(
        img,
        config="--psm 7 -c tessedit_char_whitelist=0123456789@| "
    )

    print(f"[OCR raw] '{text.strip()}'")

    # ★ @ あり: "@ 1 |"
    match = re.search(r'@\s*(\d{1,2})\s*\|', text)
    if match:
        level = int(match.group(1))
        if 1 <= level <= MAX_LEVEL + 2:
            return level

    # ★ @ なし fallback: "数字 | 数字" の最初の1〜2桁
    # ただし行頭の "1)" の "1" を拾わないよう | の直前を優先
    match2 = re.search(r'(\d{1,2})\s*\|\s*\d', text)
    if match2:
        level = int(match2.group(1))
        if 1 <= level <= MAX_LEVEL + 2:
            return level

    return None

def do_start(last_split_level):
    print("[ACTION] タイマー開始")
    send_livesplit("reset")
    time.sleep(0.1)
    send_livesplit("starttimer")
    return 1  # last_split_level を 1 に

def main():
    print("=== Pogostuck Loot Mode オートスプリッター起動 ===")
    print("LiveSplitを起動してTCP Serverを開始してください。")
    print("ゲームを開始したら自動でスプリットが始まります。")
    print("Ctrl+C で終了\n")

    confirmed_level = None
    candidate_level = None
    candidate_count = 0
    last_split_level = 0

    with mss.MSS() as sct:
        while True:
            raw = get_current_level(sct)

            # ★ None は無視（揺れの原因なのでスキップ）
            if raw is None:
                time.sleep(0.5)
                continue

            # --- 安定化フィルタ ---
            if raw == candidate_level:
                candidate_count += 1
            else:
                candidate_level = raw
                candidate_count = 1

            if candidate_count >= STABLE_COUNT and candidate_level != confirmed_level:
                prev = confirmed_level
                confirmed_level = candidate_level
                print(f"[確定] レベル: {prev} → {confirmed_level}")

                # ── ゲーム開始（初回）──
                if confirmed_level == 1 and last_split_level == 0:
                    last_split_level = do_start(last_split_level)

                # ── リセット検知：Level1に戻ってきた ──
                elif confirmed_level == 1 and last_split_level > 1:
                    print("[ACTION] リセット検知 → タイマーリセット＆再スタート")
                    last_split_level = do_start(last_split_level)

                # ── レベルアップ → Split ──
                elif confirmed_level > last_split_level and 1 < confirmed_level <= MAX_LEVEL:
                    print(f"[ACTION] Split! Level {last_split_level} → {confirmed_level}")
                    send_livesplit("split")
                    last_split_level = confirmed_level

                # ── MAX_LEVEL 到達 → 最終Split ──
                elif confirmed_level > MAX_LEVEL and last_split_level == MAX_LEVEL:
                    print("[ACTION] 最終Split！")
                    send_livesplit("split")
                    last_split_level = confirmed_level

            time.sleep(0.5)

if __name__ == "__main__":
    main()
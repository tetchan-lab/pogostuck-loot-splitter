import mss
import pytesseract
from PIL import Image, ImageFilter
import socket
import time
import re

# === 設定 ===
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# @ の後の数字が表示されている領域（座標はキャリブレーション後に調整）
# top, left はウィンドウタイトルバー含む絶対座標
CAPTURE_REGION = {"top": 60, "left": 0, "width": 450, "height": 40}

# LiveSplit Server設定
LIVESPLIT_HOST = "localhost"
LIVESPLIT_PORT = 16834

# 監視するレベル範囲
MAX_LEVEL = 10

# ===========================

def send_livesplit(command: str):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((LIVESPLIT_HOST, LIVESPLIT_PORT))
            s.sendall((command + "\r\n").encode())
    except Exception as e:
        print(f"[LiveSplit接続エラー] {e}")

def get_current_level(sct) -> int | None:
    screenshot = sct.grab(CAPTURE_REGION)
    img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

    # 黄色テキストを強調（黒背景に黄色文字）
    img = img.resize((img.width * 2, img.height * 2), Image.NEAREST)  # 拡大してOCR精度UP

    text = pytesseract.image_to_string(img, config="--psm 7 -c tessedit_char_whitelist=0123456789@| ")
    
    # "@ X" のXを抽出
    match = re.search(r'@\s*(\d+)', text)
    if match:
        return int(match.group(1))
    return None

def main():
    print("=== Pogostuck Loot Mode オートスプリッター起動 ===")
    print("LiveSplitを起動してServerを開始してください。")
    print("ゲームを開始したら自動でスプリットが始まります。")
    print("Ctrl+C で終了\n")

    current_level = None
    last_split_level = 0

    with mss.mss() as sct:
        while True:
            level = get_current_level(sct)

            if level is not None and level != current_level:
                print(f"[検知] レベル変化: {current_level} → {level}")
                current_level = level

                # レベル1になったらタイマーリセット＆スタート
                if level == 1 and last_split_level == 0:
                    print("[ACTION] タイマー開始")
                    send_livesplit("reset")
                    time.sleep(0.1)
                    send_livesplit("starttimer")
                    last_split_level = 1

                # レベルが上がったらスプリット
                elif level > last_split_level and level <= MAX_LEVEL:
                    print(f"[ACTION] Split! → Level {level}")
                    send_livesplit("split")
                    last_split_level = level

                # MAX_LEVELを超えたら最終スプリット
                elif level > MAX_LEVEL and last_split_level == MAX_LEVEL:
                    print("[ACTION] 最終Split！")
                    send_livesplit("split")
                    last_split_level = level

            time.sleep(0.5)  # 0.5秒ごとに確認（負荷ほぼゼロ）

if __name__ == "__main__":
    main()
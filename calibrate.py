import mss
from PIL import Image

# ゲームを起動した状態で実行してください
with mss.mss() as sct:
    # 左上の広めの領域をキャプチャ
    region = {"top": 73, "left": 0, "width": 450, "height": 30}
    screenshot = sct.grab(region)
    img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
    img.save("calibrate_check.png")
    print("calibrate_check.png を保存しました。画像を開いて @ の数字の座標を確認してください。")
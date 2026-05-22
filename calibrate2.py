import mss
from PIL import Image

with mss.MSS() as sct:
    # まず広めに取る
    region = {"top": 73, "left": 245, "width": 350, "height": 50}
    screenshot = sct.grab(region)
    img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
    img = img.resize((img.width * 2, img.height * 2), Image.NEAREST)
    img.save("calibrate2.png")
    print("calibrate2.png を保存しました")
    print(f"画像サイズ: {img.size}")
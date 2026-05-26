# Pogostuck Loot Mode オートスプリッター

Pogostuck の Loot Mode において、画面 OCR でレベル・スコアを読み取り、LiveSplit のタイマーを自動制御するスクリプトです。

## 概要

ゲーム画面左上に表示されるプレイヤー情報（例: `三つ編みひなみ_てっちゃん @ 5 | 120`）を 0.5 秒ごとキャプチャ・OCR し、レベルアップを検知するとLiveSplitへ `split` コマンドを送信します。

```
プレイヤー名 @ レベル | スコア（コイン枚数）
```

## ダウンロード方法

プログラミングの知識がなくても、以下の手順でファイルをダウンロードできます。

1. このページ上部の緑色の **`<> Code`** ボタンをクリックする
2. メニューの一番下にある **`Download ZIP`** をクリックする
3. ZIP ファイルがダウンロードされるので、好きな場所に解凍（展開）する

> **解凍方法（Windows）**  
> ダウンロードした ZIP ファイルを右クリック → **「すべて展開」** を選択してください。

解凍したフォルダの中にある `pogostuck-loot-splitter` フォルダが使用するフォルダです。

---

## ファイル構成

| ファイル | 説明 |
|---|---|
| `pogo_autosplit_lobby.py` | **複数人ロビー対応版**（推奨）Level 20 まで対応。自分の行（黄色テキスト）だけを認識 |
| `pogo_autosplit.py` | シングルプレイヤー版。Level 10 まで対応 |
| `calibrate.py` | キャプチャ領域を確認するためのキャリブレーションツール |
| `calibrate2.py` | キャプチャ領域を拡大表示して確認するキャリブレーションツール |
| `LiveSpilitLayout.lsl` | LiveSplit レイアウトファイル |
| `Pogostuck Rage With Your Friends - Loot.lss` | LiveSplit スプリットファイル |

## 必要環境

### Python ライブラリ

```bash
pip install mss pytesseract Pillow numpy
```

| ライブラリ | 用途 |
|---|---|
| `mss` | 画面の指定領域を高速キャプチャ |
| `pytesseract` | Python から Tesseract OCR を呼び出す橋渡し |
| `Pillow (PIL)` | 画像の拡大・加工（OCR 精度向上） |
| `numpy` | 黄色ピクセルだけを抽出するピクセル操作 |

※ `socket`, `time`, `re` は Python 標準ライブラリのため別途インストール不要

### 外部ツール

| ツール | 入手先 | 用途 |
|---|---|---|
| Python 3.10 以上 | https://www.python.org/downloads/ | スクリプトの実行環境 |
| Tesseract OCR | https://github.com/UB-Mannheim/tesseract/wiki | 画像から文字を読み取るエンジン |
| LiveSplit | https://livesplit.org/ | タイマー表示・スプリット管理 |

> **Tesseract のインストールパス**  
> デフォルトは `C:\Program Files\Tesseract-OCR\tesseract.exe`。  
> インストール先を変えた場合はスクリプト冒頭の `pytesseract.tesseract_cmd` を修正してください。

## LiveSplit の設定

| 設定 | 手順 |
|---|---|
| LiveSplit Server の追加 | 最新版はデフォルトで入っている |
| TCP Server の起動 | LiveSplit を右クリック → `Settings` → `Startup Behavior` で `Start TCP Server` を選択 |
| ポート | デフォルト `16834`（スクリプトの `LIVESPLIT_PORT` と合わせること） |

付属の `.lsl` / `.lss` ファイルを読み込むと、レイアウトとスプリット設定が即座に利用できます。

> ※1 .lss スプリットファイルは **Lvel1～20** で設定してあります。  
> ※2 .lsl レイアウトファイルはOBSの配信上に乗せるため、背景をマゼンダにしてあり、更に透過してあります。  
> お好みで設定を変更してください。

## セットアップ手順

### 1. キャリブレーション（初回・解像度変更時）

ゲームを起動した状態で以下を実行し、キャプチャ領域を確認します。

```bash
python calibrate.py
# → calibrate_check.png が生成される
```

生成された画像を開き、`@ レベル | スコア` の文字が含まれていることを確認してください。  
含まれていない場合は、スクリプト上部の `CAPTURE_REGION` の値を調整します。

```python
CAPTURE_REGION = {"top": 73, "left": 245, "width": 350, "height": 150}
```

より精細に確認したい場合は `calibrate2.py`（2倍拡大版）を使用してください。

### 2. スクリプトの起動

```bash
python pogo_autosplit_lobby.py
```

### 3. ゲーム開始

LiveSplit の TCP Server が起動済みの状態でゲームを始めると、自動でタイマーがスタートします。

## 動作フロー

```
① 0.5秒ごとに画面の指定領域をキャプチャ
      ↓
② numpy で黄色ピクセルのみを白に変換（他プレイヤーの白テキストを除外）
      ↓
③ 画像を3倍に拡大（OCR 精度向上）
      ↓
④ Tesseract OCR で文字認識（whitelist: 0123456789@| ）
      ↓
⑤ 正規表現で「@ レベル | スコア」を抽出
      ↓
⑥ 同じ値が STABLE_COUNT 回連続で出たら確定（誤認識フィルタ）
      ↓
⑦ レベルアップ検知 → LiveSplit へ "split" 送信
   リセット検知    → LiveSplit へ "reset" + "starttimer" 送信
```

## 設定値

スクリプト冒頭の定数で動作を調整できます。

| 定数 | デフォルト | 説明 |
|---|---|---|
| `CAPTURE_REGION` | `top:73, left:245, width:350, height:150` | キャプチャする画面領域 |
| `MAX_LEVEL` | `20` | 監視するレベルの上限 |
| `STABLE_COUNT` | `2` | 確定に必要な連続一致回数（誤認識フィルタ） |
| `DEBUG_SAVE_OCR_IMAGE` | `True` | OCR 前処理画像を `debug_ocr.png` として保存 |
| `LIVESPLIT_PORT` | `16834` | LiveSplit Server の TCP ポート |

## デバッグ

`DEBUG_SAVE_OCR_IMAGE = True` にすると、OCR に渡す直前の画像が `debug_ocr.png` として保存されます。OCR がうまく認識できない場合はこの画像を確認し、黄色テキストが白く抽出されているかを確認してください。

コンソールには以下のような出力が表示されます。

```
[OCR raw] '@ 5 | 120'
[確定] レベル: 4 → 5, スコア: 95 → 120
[ACTION] Split! Level 4 → 5
  → LiveSplit送信: split
```

## リセット検知ロジック

| 検知条件 | 動作 |
|---|---|
| `confirmed_level == 1` かつ `last_split_level > 1` | レベルが 1 に戻った → リセット |
| `confirmed_score == 0` かつ `last_confirmed_score > 0` かつ Level 1 中 | スコアが 0 に戻った → Level 1 中のリセット |

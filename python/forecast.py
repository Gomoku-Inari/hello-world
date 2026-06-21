import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import requests
from geopy.geocoders import Nominatim
import math
import re

def tile_coords(lat, lon, zoom):
    """
    緯度経度から地理院タイル座標（x, y）を計算する関数
    """
    n = 2 ** zoom
    x_tile = int(n * ((lon + 180) / 360))
    lat_rad = math.radians(lat)
    y_tile = int(n * (1 - (math.log(math.tan(lat_rad) + 1 / math.cos(lat_rad)) / math.pi)) / 2)
    return x_tile, y_tile

def download_gsi_map(zoom_level):
    """
    国土地理院から日本地図のタイルをダウンロードし、結合して一枚の画像を生成する関数
    """
    # 関東地方をカバーするおおよその緯度・経度範囲に変更
    lat_min, lat_max = 34.5, 37.5
    lon_min, lon_max = 138, 141

    x_min, y_max = tile_coords(lat_min, lon_min, zoom_level)
    x_max, y_min = tile_coords(lat_max, lon_max, zoom_level)

    total_width = (x_max - x_min + 1) * 256
    total_height = (y_max - y_min + 1) * 256
    
    combined_img = Image.new('RGB', (total_width, total_height))

    print(f"ズームレベル {zoom_level} で地図をダウンロードしています...")
    for x in range(x_min, x_max + 1):
        for y in range(y_min, y_max + 1):
            url = f"https://maps.gsi.go.jp/xyz/std/{zoom_level}/{x}/{y}.png"
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    tile_img = Image.open(requests.get(url, stream=True).raw)
                    paste_x = (x - x_min) * 256
                    paste_y = (y - y_min) * 256
                    combined_img.paste(tile_img, (paste_x, paste_y))
                else:
                    print(f"タイルが見つかりません: {url}")
            except Exception as e:
                print(f"タイルのダウンロードエラー: {url} - {e}")

    temp_file = "temp_gsi_map.png"
    combined_img.save(temp_file)
    print("地図のダウンロードが完了しました。")
    return combined_img, x_min, y_min

def get_prefecture_from_coords(lat, lon):
    """
    経度・緯度から都道府県名を取得する関数
    """
    geolocator = Nominatim(user_agent="gsi_map_weather_app")
    print(f"クリック座標の緯度経度: {lat}, {lon}")
    try:
        location = geolocator.reverse(f"{lat}, {lon}", exactly_one=True, language="ja")
        if location:
            print(f"geopyが取得した住所: {location.address}")
            address_parts = location.address.split(', ')
            print(f"取得したアドレスの部品数: {len(address_parts)}")
            for part in address_parts:
                prefMatch = re.match(r'.*(都|県|府|道)$', part)
                if prefMatch:
                    return part
            return None
    except Exception as e:
        print(f"ジオコーディングエラー: {e}")
        return None

def get_jma_weather_data(prefecture_name):
    """
    気象庁のウェブサイトから指定された都道府県の天気予報を取得する関数
    """
    prefecture_codes = {
        "北海道": "016000", "青森県": "020000", "岩手県": "030000", "宮城県": "040000",
        "秋田県": "050000", "山形県": "060000", "福島県": "070000", "茨城県": "080000",
        "栃木県": "090000", "群馬県": "100000", "埼玉県": "110000", "千葉県": "120000",
        "東京都": "130000", "神奈川県": "140000", "新潟県": "150000", "富山県": "160000",
        "石川県": "170000", "福井県": "180000", "山梨県": "190000", "長野県": "200000",
        "岐阜県": "210000", "静岡県": "220000", "愛知県": "230000", "三重県": "240000",
        "滋賀県": "250000", "京都府": "260000", "大阪府": "270000", "兵庫県": "280000",
        "奈良県": "290000", "和歌山県": "300000", "鳥取県": "310000", "島根県": "320000",
        "岡山県": "330000", "広島県": "340000", "山口県": "350000", "徳島県": "360000",
        "香川県": "370000", "愛媛県": "380000", "高知県": "390000", "福岡県": "400000",
        "佐賀県": "410000", "長崎県": "420000", "熊本県": "430000", "大分県": "440000",
        "宮崎県": "450000", "鹿児島県": "460000", "沖縄県": "470000"
    }
    code = prefecture_codes.get(prefecture_name)
    if not code:
        return f"対応する気象庁の地域コードが見つかりません: {prefecture_name}"
    url = f"https://www.jma.go.jp/bosai/forecast/data/overview_forecast/{code}.json"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        report_time = data.get("reportDatetime")
        headline_text = data.get("headlineText")
        text = data.get("text")
        return (f"--- {prefecture_name} の天気予報 ---\n"
                f"発表日時: {report_time}\n"
                f"見出し: {headline_text}\n"
                f"詳細: {text}\n"
                f"----------------------------")
    except requests.exceptions.RequestException as e:
        return f"エラーが発生しました: {e}"
    except Exception as e:
        return f"データの解析中にエラーが発生しました: {e}"

def show_weather_info(event):
    """
    マップクリック時のイベントハンドラ
    """
    global canvas, combined_img, zoom_level, x_min, y_min

    # クリック位置のピクセル座標
    x, y = event.x, event.y
    
    # リサイズ前の元の画像サイズ
    map_width, map_height = combined_img.size
    
    # クリック位置を元の画像サイズに変換
    x_original = x * (map_width / canvas.winfo_width())
    y_original = y * (map_height / canvas.winfo_height())
    
    # タイル内の相対座標
    x_rel = x_original / 256.0
    y_rel = y_original / 256.0
    
    # 全体におけるタイルの絶対座標
    x_abs = x_min + x_rel
    y_abs = y_min + y_rel

    n = 2 ** zoom_level
    lon = (x_abs / n) * 360 - 180
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y_abs / n)))
    lat = math.degrees(lat_rad)

    prefecture_name = get_prefecture_from_coords(lat, lon)
    
    if prefecture_name:
        weather_info = get_jma_weather_data(prefecture_name)
        messagebox.showinfo("天気予報", weather_info)
    else:
        messagebox.showwarning("情報なし", "この場所の都道府県名を取得できませんでした。海の近くや、geopyが正確な住所を返せなかった可能性があります。")

def main():
    """
    メインのウィンドウを作成し、イベントを設定
    """
    global canvas, combined_img, zoom_level, x_min, y_min
    
    # ズームレベル。値を大きくすると詳細になるが、処理が重くなる
    zoom_level = 8
    
    root = tk.Tk()
    root.title("国土地理院地図から天気予報")
    
    # 地図をダウンロードして結合
    combined_img, x_min, y_min = download_gsi_map(zoom_level)
    if combined_img is None:
        root.destroy()
        return

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    map_ratio = combined_img.width / combined_img.height
    screen_ratio = screen_width / screen_height
    
    zoom_factor = 1.2

    if map_ratio > screen_ratio:
        display_width = int(screen_width * 0.8 * zoom_factor)
        display_height = int(display_width / map_ratio)
    else:
        display_height = int(screen_height * 0.8 * zoom_factor)
        display_width = int(display_height * map_ratio)
    
    resized_img = combined_img.resize((display_width, display_height), Image.LANCZOS)
    photo_img = ImageTk.PhotoImage(resized_img)
    
    canvas = tk.Canvas(root, width=display_width, height=display_height)
    canvas.pack()
    canvas.create_image(0, 0, anchor=tk.NW, image=photo_img)
    
    canvas.bind("<Button-1>", show_weather_info)
    
    instruction_label = tk.Label(root, text="地図上の任意の場所をクリックしてください。")
    instruction_label.pack()
    
    root.mainloop()

if __name__ == "__main__":
    main()

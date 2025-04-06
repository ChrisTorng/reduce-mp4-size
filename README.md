# reduce-mp4-size

這是一個用於縮減 MP4 影片檔案大小的工具，能依據指定的目標大小自動調整解析度及位元率，讓輸出影片符合您的需求。

## 功能特點

- 自動計算並調整影片解析度和位元率
- 支援指定影片剪輯的開始和結束時間
- 顯示原始影片的資訊（解析度、位元率、檔案大小等）
- 在多次嘗試後自動找到符合目標大小範圍的最佳設定
- 輸出檔案大小控制在目標的 95%~100% 之間
- 播放完成後支援清理中間處理檔案

## 安裝步驟

### 安裝前置需求

- Python 3.6+
- FFmpeg (需要在系統路徑中)

### 使用 uv 建立虛擬環境 (Windows)

1. **安裝 uv**

   ```powershell
   powershell -ExecutionPolicy Bypass -c "irm https://github.com/astral-sh/uv/releases/download/0.6.12/uv-installer.ps1 | iex"
   ```
   
   配置環境變數:
   ```cmd
   # 在 CMD 中：
   set Path=C:\Users\使用者名稱\.local\bin;%Path%
   
   # 或在 PowerShell 中：
   $env:Path = "C:\Users\使用者名稱\.local\bin;$env:Path"
   ```

2. **建立及啟動虛擬環境**

   ```cmd
   uv venv
   .venv\Scripts\activate
   ```

3. **安裝相依套件**

   本專案沒有額外相依套件，但需要確保系統已安裝 FFmpeg，並將其加入到系統路徑。

## 使用方法

```
python reduce_mp4.py [目標大小] [輸入檔案] [開始時間(選用)] [結束時間(選用)]
```

### 參數說明

- **目標大小**: 指定想要的檔案大小，支援格式如 `10m`(10MB)、`1g`(1GB) 或直接以位元組數表示
- **輸入檔案**: 要處理的 MP4 影片檔案路徑
- **開始時間**: (選用) 指定影片的開始時間，格式為 `分:秒.小數` 或純秒數
- **結束時間**: (選用) 指定影片的結束時間，格式同上

### 輸出

程式會產生類似 `原檔名_解析度_位元率.mp4` 格式的輸出檔案。

## 使用範例

```cmd
# 將影片縮減為 10MB 大小
python reduce_mp4.py 10m input.mp4

# 將影片的 1分30秒到 5分45秒部分縮減為 20MB
python reduce_mp4.py 20m input.mp4 1:30 5:45

# 將影片的前 60 秒縮減為 5MB
python reduce_mp4.py 5m input.mp4 0 60
```

## 處理流程

1. 分析原始影片的參數（解析度、位元率、時長等）
2. 根據目標大小計算新的解析度和位元率
3. 使用 FFmpeg 處理影片
4. 檢查輸出檔案大小，若不符合目標範圍 (95%~100%)，則自動調整參數再試
5. 完成後使用系統預設播放器播放結果影片
6. 詢問是否刪除中間處理檔案

## 授權

[MIT LICENSE](LICENSE)
底下為建立此專案之所有提示訊息及指令:

1. Agent: 請建立 py 檔，接收第一個參數是目標檔案大小，可用 10m/1g 這樣的單位，第二個參數是 mp4 檔名，之後的可選參數可以用 m:s.f 這樣的格式指定開始時間及結束時間，或超過 60 的秒數亦可，沒指定就是預設到開頭或到結束。
   該程式使用 ffmpeg 函式庫，先顯示目前 mp4 的各樣與輸出檔案大小相關的參數，包括解析度、位元速率、預計每秒及每分鐘檔案大小等。然後依指定目標檔案大小的限制，估算預計每秒/每分鐘檔案大小，並自動調整解析度及位元速率輸出檔案。輸出檔名為輸入檔名後附加解析度及位元速率值。若輸出檔案超過目標大小，則再自動估算新的值並再輸出。若輸出檔案小於目標太多，也再自動估算新的值並再輸出。也就是允許的目標檔案大小為指定大小的 95%~100% 之間。
   已確定完成後，請直接以系統播放器播放該目標 mp4，播放完畢後詢問是否刪除先前嘗試過但未在目標大小範圍內的失敗輸出檔。

   => 建立 reduce-mp4.py

2. Ask: Windows 下 uv 如何安裝，如何建立虛擬環境，如何安裝相依套件，如何執行程式?

   ```cmd
   powershell -ExecutionPolicy Bypass -c "irm https://github.com/astral-sh/uv/releases/download/0.6.12/uv-installer.ps1 | iex"
   set Path=C:\Users\ChrisTorng\.local\bin;%Path%   (cmd)
   $env:Path = "C:\Users\ChrisTorng\.local\bin;$env:Path"   (powershell)
   ```

   ```ps
   Set-ExecutionPolicy RemoteSigned
   uv venv
   .venv\Scripts\activate
   uv pip install
   python reduce-mp4.py
   ```

3. Agent: 執行結果如下，讀取原始檔案之解析度、時間長度、檔案大小資訊都是完全不正確，後面自然也錯得離譜，請詳細檢查:

   => 改用 JSON 讀 ffprobe 輸出

4. Agent: 請參考目前程式及提示檔，為我建立 README.md。

   => 建立 README.md
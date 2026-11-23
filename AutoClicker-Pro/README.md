# AutoClicker Pro — Windows

以 Python、Tkinter 與 pynput 製作的 Windows 10/11 圖形化滑鼠自動點擊工具。

## 功能

- 單點 A 或雙點 A → B 操作模式
- 分別設定 A、B 點擊次數、同位置點擊間隔、移動時間與每輪等待時間（單位：秒）
- 循環輪數：`0` 表示無限循環
- F6 開始／暫停、F7 記錄 A、F8 結束、F9 記錄 B
- 視窗置頂、狀態與點擊計數顯示
- 自動保存設定至 `%APPDATA%\AutoClicker_Pro\settings.json`（不保存座標）
- 將滑鼠移到主螢幕左上角 `(0,0)`，可在下一次點擊前觸發緊急停止檢查

## 使用方式（免安裝版）

從 GitHub Releases 下載 `AutoClicker_Pro.exe`，雙擊啟動。使用者不需另外安裝 Python 或 pynput。Windows SmartScreen 或防毒軟體可能對未簽署的 EXE 提示警告；請自行核對來源，不應盲目略過安全警示。

1. 按 F7 記錄 A 點；雙點模式再按 F9 記錄 B 點。
2. 設定每輪等待時間、點擊次數、間隔、移動時間及循環輪數。
3. 按 F6 開始或暫停；F8 結束。

## 從原始碼執行（開發者）

在 Windows 安裝 Python 後：

```powershell
py -m pip install -r requirements.txt
py src/auto_clicker_pro.py
```

## 建立 Windows 單檔 EXE（開發者）

在 **Windows 電腦** 雙擊 `build_windows.bat`，或執行：

```powershell
py -m pip install pyinstaller pynput
py -m PyInstaller --noconfirm --clean --onefile --windowed --name AutoClicker_Pro src/auto_clicker_pro.py
```

輸出為 `dist/AutoClicker_Pro.exe`。建議先在 Windows 10/11 實機測試，再上傳至 GitHub Releases。

## 專案狀態

Windows 為主要維護平台；macOS 移植曾嘗試但已暫停。此儲存庫包含 Windows 原始碼與打包工具，不預先包含經實機驗證的 EXE。

## 使用注意

自動滑鼠操作可能作用於當前視窗。使用前請確認座標與執行參數，並遵守所使用軟體或服務的規範。

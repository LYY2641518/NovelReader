# 小說爬蟲閱讀器 (Novel Crawler Reader)

一個功能完整的小說爬蟲與離線閱讀應用，支援線上搜尋、批次下載、本地書庫管理與互動式閱讀。

## ✨ 主要功能

### 🔍 線上搜尋
- 在 https://m.wfxs.tw 搜尋小說
- 實時搜尋結果展示
- 檢視書籍詳情（作者、摘要、章節列表）

### 📥 智能下載
- **智能分頁計算**：根據總章節數自動計算需要的分頁數量
- 批次下載整部小說
- 支援下載進度回調與取消功能
- 自動重試機制
- 隨機延遲避免被封 IP

### 📚 本地書庫
- 已下載書籍管理
- 記錄最後閱讀進度
- 離線存取已下載內容
- 快速查看書籍資訊

### 📖 互動式閱讀器
- 加載本地或線上章節
- 上一章/下一章導航
- 可摺疊章節列表
- 顯示當前閱讀進度
- 自動保存最後閱讀位置

## 🛠️ 技術棧

| 模組 | 用途 | 套件 |
|------|------|------|
| **UI 層** | 跨平台圖形界面 | Kivy |
| **爬蟲層** | HTML 解析、網頁下載 | BeautifulSoup4, Requests |
| **業務層** | 搜尋、下載、書庫管理 | 自訂邏輯 |
| **多執行緒** | 非阻塞下載、搜尋 | threading |
| **配置管理** | 路徑、字體、設定 | pathlib, sys |

## 📁 專案架構

```
src/
├── main.py                  # 程式入口
├── novel_service.py         # 業務邏輯（搜尋、下載、管理）
├── app/
│   └── app.py              # Kivy 應用主框架
├── core/
│   └── setting.py          # 全域設定（BASE_DIR、字體路徑）
├── services/
│   └── novel_search.py     # 爬蟲層（HTML 解析、分頁處理）
├── ui/
│   ├── screens/
│   │   ├── search_screen.py      # 搜尋頁面
│   │   ├── book_screen.py        # 書籍詳情頁
│   │   ├── reader_screen.py      # 章節閱讀器
│   │   └── library_screen.py     # 書庫頁面
│   └── widgets/
│       ├── search_bar.py         # 搜尋條元件
│       └── result_area.py        # 結果區域
├── utils/
│   └── logger.py           # 日誌系統
downloads/                  # 已下載小說儲存目錄
font/                       # 中文字體
```

## 🚀 快速開始

### 安裝依賴

```bash
# 建立虛擬環境（可選）
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate  # Windows

# 安裝依賴
pip install requests beautifulsoup4 kivy pygame-ce
```

### 執行應用

```bash
python src/main.py
```

## 💻 使用指南

### 1. 搜尋與下載
1. 在搜尋欄輸入小說名稱
2. 點擊搜尋結果查看書籍詳情
3. 檢視章節列表後點擊「下載全部」開始下載
4. 下載完成後可在書庫查看

### 2. 閱讀已下載小說
1. 從導航欄進入「書庫」
2. 選擇已下載的書籍
3. 點擊要閱讀的章節
4. 使用上一章/下一章導航

### 3. 線上閱讀
- 搜尋結果中點擊未下載的章節可直接線上閱讀

## 🔧 開發說明

### 核心業務邏輯

```python
import novel_service

# 搜尋小說
results = novel_service.search('流浪地球')

# 下載小說
folder = novel_service.download_book(index_url, '流浪地球')

# 列出已下載書籍
books = novel_service.list_books()

# 讀取章節
content = novel_service.read_chapter('流浪地球', '第1章.txt')

# 獲取總章節數
total = novel_service.get_total_chapters(index_url)
```

### 下載進度監聽

```python
def progress_callback(done, total, chapter_title):
    print(f"進度: {done}/{total} - {chapter_title}")

novel_service.download_book(
    index_url, 
    title,
    progress_callback=progress_callback
)
```

### 下載取消

```python
from threading import Event

cancel_event = Event()
novel_service.download_book(index_url, title, cancel_event=cancel_event)
# 要取消時：
cancel_event.set()
```

## 📝 資料儲存

- **已下載小說**：`downloads/{書名}/` 目錄
- **章節文件**：`downloads/{書名}/{章名}.txt`
- **書籍元數據**：`downloads/{書名}/meta.json`（記錄最後閱讀章節）
- **HTML 快取**：`downloads/{書名}/index_page.html`、`menu.html`

## ⚙️ 配置

編輯 `src/core/setting.py` 調整：
- 應用基礎路徑 (`BASE_DIR`)
- 中文字體位置 (`FONT_TW_SERIF`)

## 🌐 支援網站

目前支援：
- https://m.wfxs.tw （無限小說）

## 📋 依賴清單

- **requests** - HTTP 請求庫
- **beautifulsoup4** - HTML 解析
- **kivy** - UI 框架
- **pygame-ce** - Kivy 後端

## 📄 授權

MIT License


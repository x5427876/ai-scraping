# 🤖 AI 智能爬蟲與社群媒體內容生成器

這是一個強大的 AI 驅動工具，能夠自動爬取網路內容並生成適合社群媒體發布的貼文。

## ✨ 主要功能

- 🔍 智能網頁爬蟲
  - 支援 Google 搜尋結果爬取
  - 自動提取網頁主要內容
  - 支援圖片、標籤等多媒體內容

- 🎯 AI 內容處理
  - 使用 OpenAI API 智能處理內容
  - 自動生成吸引人的標題和摘要
  - 多平台內容格式支援

- 📱 社群媒體最佳化
  - 統一的跨平台貼文格式
  - 智能標籤推薦
  - 視覺內容建議
  - 互動策略生成

## 🚀 快速開始

### 前置需求

- Python 3.8+
- pip 套件管理器
- OpenAI API 金鑰
- Google Custom Search API 金鑰

### 安裝步驟

1. 克隆專案：
```bash
git clone [你的專案URL]
cd ai-scraping
```

2. 安裝依賴：
```bash
pip install -r requirements.txt
```

3. 安裝瀏覽器驅動：
```bash
playwright install
```

4. 設定環境變數：
```bash
cp .env.example .env
# 編輯 .env 文件，填入你的 API 金鑰
```

### 🔧 配置說明

在 `.env` 文件中設定以下必要參數：

- `OPENAI_API_KEY`: OpenAI API 金鑰
- `GOOGLE_API_KEY`: Google API 金鑰
- `GOOGLE_CSE_ID`: Google 自訂搜尋引擎 ID

### 📖 使用方法

1. 執行爬蟲和內容生成：
```python
from src.crawler_client import CrawlerClient
from src.openai_processor import OpenAIProcessor

# 初始化客戶端
with CrawlerClient() as crawler:
    # 執行搜尋
    results = crawler.search("你的搜尋關鍵字", num_results=5)
    
    # 處理結果
    processor = OpenAIProcessor()
    content = processor.process_search_results(results)
    print(content)
```

## 📝 輸出格式

生成的內容將包含：

1. 核心內容
   - 標題（20字以內）
   - 導語（50字以內）
   - 正文（500字以內）
   - 結語
   - 核心標籤

2. 視覺建議
   - 主圖建議
   - 配圖建議
   - 視覺重點

3. 互動策略
   - 互動問題
   - 分享建議
   - 延伸標籤

## 🤝 貢獻指南

歡迎提交 Pull Requests 和 Issues！

## 📄 授權條款

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 文件 
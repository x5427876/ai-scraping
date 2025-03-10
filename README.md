# 🔍 AI 搜尋與內容分析工具

這是一個強大的 AI 驅動工具，能夠自動搜尋網路內容、深度分析結果，並生成結構化的內容摘要。該工具特別適合研究人員、內容創作者和需要快速獲取網路信息的專業人士。

## ✨ 主要功能

- 🌐 **智能網頁搜尋與爬取**
  - 整合 Google 搜尋 API，獲取高質量搜尋結果
  - 自動提取網頁主要內容，過濾雜訊
  - 支援多種內容類型（文字、圖片、標籤等）

- 🧠 **AI 驅動的內容分析**
  - 使用 OpenAI API 進行深度內容分析
  - 自動生成結構化摘要和關鍵洞見
  - 支援自定義分析提示詞

- 📊 **API 使用統計**
  - 精確追踪 token 使用量
  - 實時計算 API 調用成本
  - 基於最新 OpenAI 定價的成本估算

## 🛠️ 技術架構

- **搜尋引擎**: Google Custom Search API
- **爬蟲引擎**: Crawl4AI
- **AI 模型**: OpenAI API (預設使用 o3-mini)
- **開發語言**: Python 3.8+

## 🚀 快速開始

### 前置需求

- Python 3.8+
- pip 套件管理器
- OpenAI API 金鑰
- Google Custom Search API 金鑰和 CSE ID

### 安裝步驟

1. **克隆專案**:
   ```bash
   git clone https://github.com/yourusername/ai-scraping.git
   cd ai-scraping
   ```

2. **創建虛擬環境**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # 在 Windows 上使用: venv\Scripts\activate
   ```

3. **安裝依賴**:
   ```bash
   pip install -r requirements.txt
   ```

4. **設定環境變數**:
   ```bash
   cp .env.example .env
   # 編輯 .env 文件，填入你的 API 金鑰
   ```

### 環境變數配置

在 `.env` 文件中設定以下必要參數:

```
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_google_cse_id
OPENAI_MODEL=o3-mini  # 可選，預設為 o3-mini
```

## 📖 使用方法

### 命令行運行

直接運行主程式:

```bash
source venv/bin/activate  # 激活虛擬環境
python src/main.py
```

程式將引導您:
1. 輸入搜尋關鍵字
2. 指定需要的結果數量
3. 自動搜尋並分析內容
4. 顯示 AI 分析結果和 API 使用統計
5. 選擇是否保存結果到文件

### 程式化使用

您也可以在自己的 Python 程式中使用此工具:

```python
from src.crawler_client import CrawlerClient
from src.openai_processor import OpenAIProcessor

# 初始化客戶端
with CrawlerClient() as crawler_client:
    # 初始化 OpenAI 處理器
    openai_processor = OpenAIProcessor()
    
    # 執行搜尋
    search_results = crawler_client.search("人工智能最新發展", num_results=5)
    
    # AI 分析結果
    analysis = openai_processor.process_search_results(search_results)
    
    # 獲取 token 使用統計
    token_usage = openai_processor.get_token_usage()
    print(f"總計使用 {token_usage['total_tokens']} tokens")
    print(f"估計成本: ${token_usage['cost_usd']:.6f} USD")
```

## 📊 API 使用統計

本工具會自動追踪和計算 OpenAI API 的使用情況:

- **輸入 tokens**: 發送給 API 的文本量
- **輸出 tokens**: API 返回的文本量
- **總計 tokens**: 輸入和輸出的總和
- **成本**: 基於最新 OpenAI 定價的美元成本

當前支援的模型價格 (每百萬 tokens):
- o3-mini: 輸入 $1.10, 輸出 $4.40

## 🔧 自定義與擴展

### 自定義提示詞

您可以通過修改 `src/openai_processor.py` 中的 `prompt_template` 來自定義 AI 分析的提示詞。

### 添加新的模型

在 `src/openai_processor.py` 中的 `model_prices` 字典中添加新模型的價格信息。

## 📝 輸出示例

AI 分析結果通常包含:

- 主題摘要
- 關鍵觀點和洞見
- 相關建議和延伸閱讀
- 視覺內容建議

## 🤝 貢獻指南

歡迎提交 Pull Requests 和 Issues！請確保您的代碼符合項目的編碼風格和測試要求。

## 📄 授權條款

本專案採用 MIT 授權條款 - 詳見 [LICENSE](LICENSE) 文件 
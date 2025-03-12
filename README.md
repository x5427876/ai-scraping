# 🔍 AI 文章生成工具

這是一個強大的 AI 驅動工具，能夠自動搜尋網路內容、深度分析結果，並生成高質量的文章。適合內容創作者、自媒體運營者和需要快速獲取網路資訊的專業人士使用。

## ✨ 核心功能

- 🌐 **智能網頁搜尋與爬取**

  - 整合 Google 搜尋 API，獲取高質量搜尋結果
  - 使用 Crawl4AI 自動提取網頁主要內容
  - 支援多種內容類型（文字、圖片、標籤等）

- 🧠 **AI 驅動的內容分析與生成**

  - 使用 OpenAI API 進行深度內容分析
  - 自動生成結構化、高質量的文章
  - 支援自定義分析提示詞
  - 可選生成相關圖像內容

- 📊 **API 使用統計**
  - 精確追踪 token 使用量
  - 實時計算 API 調用成本

## 🛠️ 技術架構

- **搜尋引擎**: Google Custom Search API
- **爬蟲引擎**: Crawl4AI
- **AI 模型**: OpenAI API (預設使用 o3-mini)
- **開發語言**: Python 3.8+
- **Web 框架**: FastAPI

## 🚀 快速開始

### 前置需求

- Python 3.8+
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
# OpenAI API 配置
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=o3-mini

# Google Search API 配置
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_CSE_ID=your_google_custom_search_engine_id_here
```

## 📖 使用方法

### 啟動 API 服務

運行以下命令啟動 API 服務:

```bash
source venv/bin/activate  # 激活虛擬環境
python src/main.py
```

服務將在 http://0.0.0.0:8000 啟動，你可以訪問 http://localhost:8000 使用 API。

### API 端點

#### 生成文章

**端點:** `POST /generate_article`

**請求參數:**

```json
{
  "keyword": "搜尋關鍵字",
  "scraping_number": 10,
  "isNeedImage": true,
  "custom_prompt": "自定義提示詞（可選）",
  "return_json": false
}
```

**響應格式:**

- 當 `return_json=false` 時，返回 Markdown 文件下載
- 當 `return_json=true` 時，返回 JSON 格式:

```json
{
  "status": "success",
  "message": "文章生成成功",
  "content": "生成的文章內容",
  "token_usage": {
    "prompt_tokens": 123,
    "completion_tokens": 456,
    "total_tokens": 579,
    "cost_usd": 0.123
  }
}
```

### 程式化使用

您也可以在自己的 Python 程式中使用此工具:

```python
from src.crawler_client import CrawlerClient
from src.openai_processor import OpenAIProcessor

# 初始化客戶端
with CrawlerClient() as crawler:
    # 執行搜尋
    search_results = crawler.get_search_urls("人工智能最新發展", num_results=5)

    # 爬取內容
    enriched_results = []
    for result in search_results:
        crawled_data = await crawler._crawl_url_async(result['link'])
        enriched_result = {
            'title': result['title'],
            'link': result['link'],
            'snippet': result['snippet'],
            'content': crawled_data['content']
        }
        enriched_results.append(enriched_result)

    # 初始化 OpenAI 處理器
    openai_processor = OpenAIProcessor()

    # AI 分析結果
    analysis = openai_processor.process_search_results(enriched_results)

    # 獲取 token 使用統計
    token_usage = openai_processor.get_token_usage()
    print(f"總計使用 {token_usage['total_tokens']} tokens")
    print(f"估計成本: ${token_usage['cost_usd']:.6f} USD")
```

## 🔧 自定義與擴展

### 自定義提示詞

您可以通過修改 `src/openai_processor.py` 中的 `process_search_results` 方法來自定義 AI 分析的提示詞。

### 添加新的模型

在 `src/openai_processor.py` 中的 `model_prices` 字典中添加新模型的價格信息:

```python
self.model_prices = {
    "o3-mini": {"input": 1.10, "output": 4.40},
    "your-new-model": {"input": X.XX, "output": Y.YY},
}
```

### 圖像生成

本工具支援使用 OpenAI 的 DALL-E 模型生成相關圖像:

```python
image_result = openai_processor.generate_image(
    prompt="相關圖像描述",
    size="1792x1024",
    quality="standard"
)
image_url = image_result.get("url")
```

## 📝 輸出示例

生成的文章通常包含:

- 吸引人的標題
- 結構清晰的內容（五個部分，每部分有小標題）
- 實用的建議和小技巧
- 適當的表情符號和互動式語言
- 行動號召和讀者互動
- 相關標籤

## 📄 授權條款

本專案採用 MIT 授權條款

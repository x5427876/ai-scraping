import os
from openai import OpenAI
from dotenv import load_dotenv
import json
import re

load_dotenv()

class OpenAIProcessor:
    """
    OpenAI 處理器類別，負責使用 OpenAI 模型分析搜尋結果
    """
    
    def __init__(self):
        """初始化 OpenAI 處理器"""
        # 檢查是否使用自訂 API 端點
        base_url = os.getenv('OPENAI_API_BASE', "https://api.openai.com/v1")
        
        # 初始化 OpenAI 客戶端
        self.client = OpenAI(
            api_key=os.getenv('OPENAI_API_KEY'),
            base_url=base_url
        )
        
        # 設定模型
        self.model = os.getenv('OPENAI_MODEL', "o3-mini")
        self.is_o3_model = "o3" in self.model.lower()
        
        # 初始化 token 計數和成本
        self.last_prompt_tokens = 0
        self.last_completion_tokens = 0
        self.last_total_tokens = 0
        self.last_cost = 0.0
        
        # 設定模型價格 (每 1,000,000 tokens 的美元價格)
        # 價格參考: https://openai.com/api/pricing/
        self.model_prices = {
            # OpenAI 模型
            "o3-mini": {"input": 1.10, "output": 4.40},
        }
        
        # 獲取當前模型的價格，如果未定義則使用默認價格
        model_key = self.model.lower()
        for key in self.model_prices.keys():
            if key in model_key:
                model_key = key
                break
        
        self.current_price = self.model_prices.get(
            model_key, 
            {"input": 0.01, "output": 0.02}  # 默認價格
        )
        
        print(f"初始化 OpenAI 處理器完成，使用模型: {self.model}")

    def process_search_results(self, search_results, prompt_template=None):
        """
        使用 OpenAI 處理搜尋結果
        
        Args:
            search_results (list): Google 搜尋結果列表
            prompt_template (str, optional): 自定義提示模板
            
        Returns:
            str: OpenAI 處理後的結果
        """
        # 設定默認提示模板
        if not prompt_template:
            prompt_template = """
            請根據以下搜尋結果，撰寫一篇約 3000 字的自媒體文章，目標讀者為青年與中年群體。文章必須直接面對讀者，不可出現「來源X」或「參考資料X」這種字眼，請將所有資訊自然融入文章中。

            {search_content}

            請遵循以下要求：

            1. 結構清晰：
               - 文章需包含五個部分，每個部分圍繞一個核心點展開
               - 各部分之間邏輯順暢、前後呼應
               - 每個部分都有明確的小標題，使用純 Markdown 格式（如 ## 標題）
               - 不要在標題中使用數字編號（如 1.1、2.1）或中文數字編號（如一、二）
               - 開頭需有吸引人的標題（使用 # 格式，25字以內）和引人入勝的導語
               - 結尾需有有力的總結和行動號召

            2. 語言風格：
               - 使用對話式、輕鬆隨意的語言
               - 避免過於正式與銷售化的表達
               - 少用術語，詞句簡潔明瞭
               - 適當使用表情符號增加親和力
               - 適當加入問句與讀者互動

            3. SEO優化：
               - 確保內容針對搜尋引擎優化
               - 合理使用關鍵字但不要過度堆砌
               - 標題和小標題中包含關鍵詞
               - 適當使用長尾關鍵詞

            4. 實用性與吸引力：
               - 每個部分提供有價值的資訊
               - 結合實例與應用技巧或故事
               - 加入2-3個實用建議或小技巧
               - 引用觀點或數據，但不要直接提及「來源」
               - 增強讀者的參與感

            5. 節奏與可讀性：
               - 段落簡短，每段不超過5行
               - 適當使用項目符號或數字列表
               - 避免長篇大論
               - 確保文章明快、易於閱讀
               - 適當使用粗體、引號等強調重點

            6. 原創性：
               - 內容必須完全原創
               - 不得抄襲或複製其他來源
               - 使用主動語態，增強文章的吸引力
               - 提供獨特的觀點和見解

            7. 行動號召：
               - 在文章結尾邀請讀者與作者互動
               - 鼓勵讀者在下方留言分享自己的看法和經驗
               - 提出1-2個與主題相關的問題，引導讀者回應
               - 邀請讀者分享文章給可能感興趣的朋友
               - 使用親切、直接的語氣與讀者對話

            格式要求：
            - 使用繁體中文
            - 以Markdown格式撰寫，便於閱讀與排版
            - 主標題使用 # 格式
            - 小標題使用 ## 格式，不要加入任何形式的編號（如 2.1、一、等）
            - 加入5-8個相關標籤（使用#開頭）
            - 確保輸出中沒有 '/n' 字符
            - 非常重要：請不要在輸出中使用原始的換行符號 \n，而是使用適當的 Markdown 格式，如段落之間空一行，或使用 <br> 標籤
            """

        # 準備搜尋內容
        search_content_parts = []
        
        for i, result in enumerate(search_results):
            # 格式化來源信息
            source_info = (
                f"參考資料 {i+1}:\n"
                f"標題: {result['title']}\n"
                f"網址: {result['link']}\n"
                f"發布日期: {result.get('date', '未知')}\n"
                f"作者: {result.get('author', '未知')}\n"
                f"標籤: {', '.join(result.get('tags', []))}\n"
                f"內容摘要: {result.get('content', '無法獲取內容')}\n"
                f"可用圖片數量: {len(result.get('images', []))}"
            )
            
            search_content_parts.append(source_info)
        
        # 合併所有來源信息
        search_content = "\n\n".join(search_content_parts)

        try:
            print(f"使用模型: {self.model}")
            
            # 準備消息
            messages = [
                {
                    "role": "system", 
                    "content": "你是一位專業的自媒體內容創作者，擅長將各種資訊轉化為吸引人的長篇文章。你了解青年與中年讀者的需求和興趣，知道如何製作能夠引發思考、分享和互動的內容。你的文章結構清晰、邏輯嚴謹，同時語言風格輕鬆對話，善於使用生動的例子和故事增加文章的吸引力。請使用繁體中文，並注意保持內容的原創性、實用性和啟發性的平衡。請確保文章直接面對讀者，不出現「來源」或「參考資料」等字眼，而是將資訊自然融入文章中。非常重要：請不要在輸出中使用原始的換行符號 \\n，而是使用適當的 Markdown 格式，如段落之間空一行，或使用 <br> 標籤。"
                },
                {
                    "role": "user", 
                    "content": prompt_template.format(search_content=search_content)
                }
            ]
            
            # 準備基本參數
            params = {
                "model": self.model,
                "messages": messages
            }
            
            # 根據模型類型添加不同的參數
            if self.is_o3_model:
                params["max_completion_tokens"] = 4000
            else:
                params["max_tokens"] = 4000
                params["temperature"] = 0.7
            
            # 輸出參數信息，方便調試
            print("使用參數:", ", ".join(params.keys()))
            
            # 調用 API
            response = self.client.chat.completions.create(**params)
            
            # 記錄 token 使用量
            self.last_prompt_tokens = response.usage.prompt_tokens
            self.last_completion_tokens = response.usage.completion_tokens
            self.last_total_tokens = response.usage.total_tokens
            
            # 計算成本 (美元)
            input_cost = (self.last_prompt_tokens / 1000000) * self.current_price["input"]
            output_cost = (self.last_completion_tokens / 1000000) * self.current_price["output"]
            self.last_cost = input_cost + output_cost
            
            # 獲取原始內容
            raw_content = response.choices[0].message.content
            
            # 使用正則表達式處理內容，移除所有換行符
            processed_content = re.sub(r'\\n+', '', raw_content)
            
            # 返回處理後的結果
            return processed_content
            
        except Exception as e:
            print(f"OpenAI 處理時發生錯誤: {str(e)}")
            print(f"詳細錯誤信息: {e}")
            # 重置 token 計數和成本
            self.last_prompt_tokens = 0
            self.last_completion_tokens = 0
            self.last_total_tokens = 0
            self.last_cost = 0.0
            return None
            
    def get_token_usage(self):
        """
        獲取最近一次 API 調用的 token 使用量
        
        Returns:
            dict: 包含 token 使用量和成本的字典
        """
        return {
            "prompt_tokens": self.last_prompt_tokens,
            "completion_tokens": self.last_completion_tokens,
            "total_tokens": self.last_total_tokens,
            "cost_usd": self.last_cost
        }
        
    def generate_image(self, prompt, size="1024x1024", quality="standard", filename=None):
        """
        使用 DALL-E 3 生成圖片
        
        Args:
            prompt (str): 圖片生成提示詞
            size (str): 圖片尺寸，可選值為 "1024x1024"、"1792x1024" 或 "1024x1792"
            quality (str): 圖片品質，可選值為 "standard" 或 "hd"
            
        Returns:
            dict: 包含圖片 URL 的字典
        """
        try:
            # 確保提示詞不超過 DALL-E 3 的限制
            if len(prompt) > 4000:
                prompt = prompt[:4000]
            
            # 調用 DALL-E 3 API
            response = self.client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size=size,
                quality=quality,
                n=1
            )
            
            # 獲取圖片 URL
            image_url = response.data[0].url
            
            return {
                "url": image_url
            }
            
        except Exception as e:
            print(f"生成圖片時發生錯誤: {str(e)}")
            return None 
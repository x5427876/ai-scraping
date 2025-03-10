import os
from openai import OpenAI
from dotenv import load_dotenv
import json

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
            請根據以下搜尋結果，生成一份統一格式的社群媒體貼文內容，可以直接用於各大平台（包括 Instagram 和 Threads）。

            {search_content}

            請按照以下統一格式生成內容：

            1. 核心內容（適用於所有平台）：
               - 標題：20字以內的引人注目標題
               - 導語：50字以內的引言，抓住讀者興趣
               - 正文：500字以內的主要內容（分3-4個段落）
               - 結語：30字以內的總結或行動呼籲
               - 3-5個核心標籤（中英對照）

            2. 視覺建議：
               - 主圖建議：描述最適合的主要圖片類型
               - 配圖建議：2-3張輔助圖片的建議
               - 視覺重點：需要強調的視覺元素

            3. 互動策略：
               - 互動問題：1個引發討論的問題
               - 分享建議：最佳發布時間和分享文案
               - 延伸標籤：2-3個相關話題標籤

            格式要求：
            - 使用繁體中文
            - 每個段落使用1-2個合適的表情符號
            - 確保內容精簡但完整
            - 保持專業但親和的語調
            - 適合跨平台使用
            - 重點標示使用「」或【】
            """

        # 準備搜尋內容
        search_content_parts = []
        
        for i, result in enumerate(search_results):
            # 格式化來源信息
            source_info = (
                f"來源 {i+1}:\n"
                f"標題: {result['title']}\n"
                f"網址: {result['link']}\n"
                f"發布日期: {result.get('date', '未知')}\n"
                f"作者: {result.get('author', '未知')}\n"
                f"標籤: {', '.join(result.get('tags', []))}\n"
                f"內容: {result.get('content', '無法獲取內容')}\n"
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
                    "content": "你是一位專業的社群媒體內容策劃師，擅長將新聞和時事轉化為吸引人的社群媒體貼文。你了解 Instagram 和 Threads 的特性，知道如何製作能夠引發討論和分享的內容。請使用繁體中文，並注意保持內容的準確性和趣味性的平衡。"
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
            
            # 返回結果
            return response.choices[0].message.content
            
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
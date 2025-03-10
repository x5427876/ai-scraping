from googleapiclient.discovery import build
import os
from dotenv import load_dotenv

load_dotenv()

class GoogleSearchClient:
    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.cse_id = os.getenv('GOOGLE_CSE_ID')
        self.service = build('customsearch', 'v1', developerKey=self.api_key)

    def search(self, query, num_results=10):
        """
        使用 Google Custom Search API 進行搜尋
        
        Args:
            query (str): 搜尋關鍵字
            num_results (int): 需要返回的結果數量
            
        Returns:
            list: 搜尋結果列表
        """
        try:
            results = []
            start_index = 1
            
            while len(results) < num_results:
                # 計算本次需要的結果數量（Google API 每次最多返回 10 個結果）
                current_num = min(10, num_results - len(results))
                
                search_results = self.service.cse().list(
                    q=query,
                    cx=self.cse_id,
                    start=start_index,
                    num=current_num  # 添加這個參數指定要返回的結果數量
                ).execute()

                if 'items' not in search_results:
                    break

                for item in search_results['items']:
                    if len(results) >= num_results:
                        break
                    
                    result = {
                        'title': item.get('title', ''),
                        'link': item.get('link', ''),
                        'snippet': item.get('snippet', ''),
                    }
                    results.append(result)

                start_index += current_num  # 更新為實際請求的數量
                if start_index > 100:  # Google CSE 限制
                    break

            return results
            
        except Exception as e:
            print(f"搜尋時發生錯誤: {str(e)}")
            return [] 
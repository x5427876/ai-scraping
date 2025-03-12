import os
import asyncio
from typing import List, Dict, Optional, Set
from urllib.parse import quote_plus, urljoin, urlparse
import time
import random
from googleapiclient.discovery import build
from dotenv import load_dotenv
from collections import deque
from crawl4ai import AsyncWebCrawler

class CrawlerClient:
    """
    爬蟲客戶端類別，使用 Crawl4AI 進行爬取
    """
    
    def __init__(self):
        """初始化爬蟲客戶端"""
        # 載入環境變數
        load_dotenv()
        
        # 初始化 Google API 客戶端
        self._init_google_api()
        
        # Crawl4AI 爬蟲實例
        self.crawler = None
        self.loop = None
    
    async def __aenter__(self):
        """異步上下文管理器進入方法"""
        self.crawler = AsyncWebCrawler()
        await self.crawler.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """異步上下文管理器退出方法"""
        if self.crawler:
            await self.crawler.__aexit__(exc_type, exc_val, exc_tb)
    
    def __enter__(self):
        """同步上下文管理器進入方法 (創建事件循環並運行異步進入方法)"""
        # 檢查是否已經有事件循環
        try:
            self.loop = asyncio.get_event_loop()
            if self.loop.is_closed():
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
        except RuntimeError:
            # 如果沒有事件循環，創建一個新的
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
        
        # 運行異步進入方法
        self.loop.run_until_complete(self.__aenter__())
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """同步上下文管理器退出方法 (運行異步退出方法並關閉事件循環)"""
        if self.loop:
            self.loop.run_until_complete(self.__aexit__(exc_type, exc_val, exc_tb))
            # 不要關閉事件循環，因為它可能是由 FastAPI 創建的
            # self.loop.close()
    
    def _init_google_api(self):
        """初始化 Google API 客戶端"""
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.cse_id = os.getenv('GOOGLE_CSE_ID')
        
        if self.api_key and self.cse_id:
            self.google_service = build('customsearch', 'v1', developerKey=self.api_key)
            print("Google API 客戶端初始化成功")
        else:
            print("警告：Google API 配置未完成，將使用直接爬蟲方式")
            self.google_service = None

    def get_search_urls(self, query: str, num_results: int = 10) -> List[Dict[str, str]]:
        """
        使用 Google Custom Search API 獲取搜尋結果
        
        Args:
            query (str): 搜尋關鍵字
            num_results (int): 需要返回的結果數量
            
        Returns:
            list: 搜尋結果列表
        """
        if not self.google_service:
            print("Google API 未配置，無法使用 API 搜尋")
            return []
            
        try:
            print(f"使用 Google API 搜尋: '{query}'，需要 {num_results} 個結果")
            search_results = []
            start_index = 1
            
            while len(search_results) < num_results:
                # 計算本次需要的結果數量
                current_num = min(10, num_results - len(search_results))
                
                # 調用 Google API
                response = self.google_service.cse().list(
                    q=query,
                    cx=self.cse_id,
                    start=start_index,
                    num=current_num  # 指定本次要返回的結果數量
                ).execute()

                # 檢查是否有結果
                if 'items' not in response:
                    print("Google API 未返回搜尋結果")
                    break

                # 處理每個搜尋結果
                for item in response['items']:
                    if len(search_results) >= num_results:
                        break
                        
                    result = {
                        'title': item.get('title', ''),
                        'link': item.get('link', ''),
                        'snippet': item.get('snippet', '')
                    }
                    search_results.append(result)

                # 如果已經獲取足夠的結果，就退出
                if len(search_results) >= num_results:
                    break

                # 更新起始索引，準備獲取下一頁結果
                start_index += current_num
                if start_index > 100:  # Google CSE 限制
                    break

            print(f"Google API 搜尋完成，找到 {len(search_results)} 個結果")
            return search_results
            
        except Exception as e:
            print(f"Google API 搜尋時發生錯誤: {str(e)}")
            return []

    async def _crawl_url_async(self, url: str) -> Dict[str, any]:
        """
        使用 Crawl4AI 異步爬取 URL 內容
        
        Args:
            url (str): 要爬取的 URL
            
        Returns:
            dict: 爬取結果
        """
        try:
            print(f"正在爬取: {url}")
            
            # 使用 Crawl4AI 爬取頁面，加入更多配置
            result = await self.crawler.arun(
                url=url,
                max_pages=1,  # 只爬取當前頁面
                content_selection="main, article, .content, body, .post-content, .article-content",  # 選擇主要內容區域
                respect_robots_txt=True,  # 尊重網站爬蟲規則
                timeout=30,  # 設置超時時間
                wait_for_selector="body",  # 等待頁面主體載入
                extract_rules={
                    "title": "h1, title, .post-title, .article-title",  # 標題選擇器
                    "content": "main, article, .content, body, .post-content, .article-content",  # 內容選擇器
                    "links": "a[href]",  # 連結選擇器
                    "images": "img[src]",  # 圖片選擇器
                    "date": "time, .date, .post-date, meta[property='article:published_time']",  # 日期選擇器
                    "author": ".author, .writer, meta[name='author']",  # 作者選擇器
                    "tags": ".tags, .categories, meta[property='article:tag']"  # 標籤選擇器
                }
            )
            
            # 檢查結果格式
            if result is None:
                print(f"爬取失敗，結果為 None: {url}")
                return {'content': '', 'title': url, 'links': [], 'images': [], 'date': '', 'author': '', 'tags': []}
            
            # 根據結果類型處理
            if isinstance(result, dict):
                content = result.get('content', '')
                if not content:
                    content = result.get('markdown', '')
                title = result.get('title', url)
                raw_links = result.get('links', [])
                images = result.get('images', [])
                date = result.get('date', '')
                author = result.get('author', '')
                tags = result.get('tags', [])
            else:
                # 嘗試直接訪問屬性
                try:
                    content = getattr(result, 'content', '') or getattr(result, 'markdown', '')
                    title = getattr(result, 'title', url)
                    raw_links = getattr(result, 'links', [])
                    images = getattr(result, 'images', [])
                    date = getattr(result, 'date', '')
                    author = getattr(result, 'author', '')
                    tags = getattr(result, 'tags', [])
                except Exception as e:
                    print(f"無法從結果中提取內容: {e}")
                    return {'content': '', 'title': url, 'links': [], 'images': [], 'date': '', 'author': '', 'tags': []}
            
            # 處理連結
            links = []
            if raw_links:
                base_domain = urlparse(url).netloc
                for link in raw_links:
                    if isinstance(link, str):
                        try:
                            if urlparse(link).netloc == base_domain:
                                links.append(link)
                        except Exception:
                            continue
            
            # 確保內容不為空
            if not content:
                print(f"警告：未能提取到內容: {url}")
                content = f"無法提取內容 - {url}"
            
            # 處理圖片 URL
            processed_images = []
            for img in images:
                if isinstance(img, str):
                    if img.startswith('//'):
                        img = 'https:' + img
                    elif not img.startswith(('http://', 'https://')):
                        img = urljoin(url, img)
                    processed_images.append(img)
            
            return {
                'content': content,
                'title': title,
                'links': links,
                'images': processed_images[:5],  # 限制圖片數量
                'date': date,
                'author': author,
                'tags': tags,
                'source_url': url
            }
            
        except Exception as e:
            print(f"爬取 URL 時發生錯誤 ({url}): {str(e)}")
            import traceback
            print(traceback.format_exc())
            return {'content': '', 'title': url, 'links': [], 'images': [], 'date': '', 'author': '', 'tags': []} 
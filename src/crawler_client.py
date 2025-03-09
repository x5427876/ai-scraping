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
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.__aenter__())
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """同步上下文管理器退出方法 (運行異步退出方法並關閉事件循環)"""
        self.loop.run_until_complete(self.__aexit__(exc_type, exc_val, exc_tb))
        self.loop.close()
    
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
    
    def crawl_url(self, url: str) -> Dict[str, any]:
        """
        同步包裝的 URL 爬取方法
        
        Args:
            url (str): 要爬取的 URL
            
        Returns:
            dict: 爬取結果
        """
        return self.loop.run_until_complete(self._crawl_url_async(url))

    def search(self, query: str, num_results: int = 10) -> List[Dict[str, str]]:
        """
        結合 Google API 和 Crawl4AI 進行搜尋
        
        Args:
            query (str): 搜尋關鍵字
            num_results (int): 需要返回的結果數量
            
        Returns:
            list: 搜尋結果列表
        """
        try:
            # 首先使用 Google API 獲取搜尋結果
            search_results = self.get_search_urls(query, num_results)
            
            # 如果 API 搜尋失敗，使用備用的爬蟲方法
            if not search_results:
                print("使用備用爬蟲方法...")
                search_results = self._fallback_search(query, num_results)
            
            # 對每個搜尋結果進行深度爬取
            enriched_results = []
            for i, result in enumerate(search_results[:num_results], 1):
                try:
                    print(f"\n處理搜尋結果 {i}/{min(len(search_results), num_results)}")
                    
                    # 爬取頁面內容
                    crawled_data = self.crawl_url(result['link'])
                    
                    # 合併結果
                    enriched_result = {
                        'title': result['title'],
                        'link': result['link'],
                        'snippet': result['snippet'],
                        'content': crawled_data['content'] if crawled_data['content'] else result['snippet']
                    }
                    enriched_results.append(enriched_result)
                    
                except Exception as e:
                    print(f"處理搜尋結果時發生錯誤: {str(e)}")
                    continue
            
            return enriched_results
            
        except Exception as e:
            print(f"搜尋過程中發生錯誤: {str(e)}")
            return []
    
    async def _search_with_bfs_async(self, query: str, max_pages: int = 10, max_depth: int = 2) -> List[Dict[str, str]]:
        """
        使用 BFS 策略進行異步搜尋和爬取
        
        Args:
            query (str): 搜尋關鍵字
            max_pages (int): 最大爬取頁面數
            max_depth (int): 最大爬取深度
            
        Returns:
            list: 搜尋結果列表
        """
        try:
            print(f"使用 BFS 策略搜尋: '{query}'，最大頁面數: {max_pages}，最大深度: {max_depth}")
            
            # 首先獲取初始搜尋結果
            initial_results = self.get_search_urls(query, min(5, max_pages))
            if not initial_results:
                print("無法獲取初始搜尋結果")
                return []
            
            # 初始化 BFS 所需的數據結構
            queue = deque()  # 待爬取的 URL 隊列
            visited = set()  # 已爬取的 URL 集合
            results = []     # 爬取結果
            url_to_depth = {}  # URL 對應的深度
            
            # 將初始搜尋結果加入隊列
            for result in initial_results:
                url = result['link']
                queue.append(url)
                url_to_depth[url] = 0  # 初始深度為 0
            
            # 開始 BFS 爬取
            while queue and len(results) < max_pages:
                # 從隊列中取出一個 URL
                current_url = queue.popleft()
                current_depth = url_to_depth[current_url]
                
                # 如果已經訪問過，跳過
                if current_url in visited:
                    continue
                
                # 標記為已訪問
                visited.add(current_url)
                
                print(f"\n爬取 URL: {current_url} (深度: {current_depth})")
                
                # 爬取頁面內容
                crawled_data = await self._crawl_url_async(current_url)
                
                # 添加到結果列表
                if crawled_data['content']:
                    result = {
                        'title': crawled_data.get('title', current_url),
                        'link': current_url,
                        'snippet': crawled_data['content'][:200] + "...",
                        'content': crawled_data['content']
                    }
                    results.append(result)
                    print(f"已添加結果 {len(results)}/{max_pages}")
                
                # 如果還沒達到最大深度，將連結加入隊列
                if current_depth < max_depth:
                    for link in crawled_data.get('links', []):
                        if link not in visited and link not in queue:
                            queue.append(link)
                            url_to_depth[link] = current_depth + 1
                            print(f"添加連結到隊列: {link} (深度: {current_depth + 1})")
            
            print(f"BFS 搜尋完成，共爬取 {len(results)} 個頁面")
            return results
            
        except Exception as e:
            print(f"BFS 搜尋過程中發生錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def search_with_bfs(self, query: str, max_pages: int = 10, max_depth: int = 2) -> List[Dict[str, str]]:
        """
        使用 BFS 策略進行搜尋和爬取 (同步包裝)
        
        Args:
            query (str): 搜尋關鍵字
            max_pages (int): 最大爬取頁面數
            max_depth (int): 最大爬取深度
            
        Returns:
            list: 搜尋結果列表
        """
        return self.loop.run_until_complete(self._search_with_bfs_async(query, max_pages, max_depth))
    
    def _fallback_search(self, query: str, num_results: int) -> List[Dict[str, str]]:
        """備用的搜尋方法 (直接使用 Crawl4AI 搜尋)"""
        try:
            print(f"使用 Crawl4AI 直接搜尋: {query}")
            
            # 構建搜尋 URL
            encoded_query = quote_plus(query)
            search_url = f"https://www.google.com/search?q={encoded_query}&num={num_results}"
            
            # 使用 Crawl4AI 爬取搜尋結果頁面
            crawled_data = self.crawl_url(search_url)
            
            # 從爬取結果中提取搜尋結果
            search_results = []
            
            # 簡單解析 markdown 內容，提取標題和連結
            lines = crawled_data['content'].split('\n')
            current_title = None
            current_link = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('# ') or line.startswith('## '):
                    # 如果有之前的結果，添加到列表
                    if current_title and current_link:
                        search_results.append({
                            'title': current_title,
                            'link': current_link,
                            'snippet': ''  # 無法從 markdown 中提取摘要
                        })
                    
                    # 開始新的結果
                    current_title = line.lstrip('#').strip()
                    current_link = None
                elif line.startswith('http') and current_title:
                    current_link = line
            
            # 添加最後一個結果
            if current_title and current_link and len(search_results) < num_results:
                search_results.append({
                    'title': current_title,
                    'link': current_link,
                    'snippet': ''
                })
            
            print(f"備用搜尋完成，找到 {len(search_results)} 個結果")
            return search_results[:num_results]
            
        except Exception as e:
            print(f"備用搜尋過程中發生錯誤: {str(e)}")
            return [] 
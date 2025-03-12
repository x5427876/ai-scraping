import os
import sys
from crawler_client import CrawlerClient
from openai_processor import OpenAIProcessor
from dotenv import load_dotenv
import time
import re
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field
from typing import List, Optional
import uvicorn
from crawl4ai import AsyncWebCrawler

# 初始化 FastAPI 應用
app = FastAPI(
    title="AI 文章生成 API",
    description="基於搜尋結果生成 AI 文章的 API 服務",
    version="1.0.0"
)

class GenerateArticleRequest(BaseModel):
    """文章生成請求模型"""
    keyword: str = Field(..., description="搜尋關鍵字")
    scraping_number: int = Field(default=10, ge=1, le=50, description="爬取結果數量")
    isNeedImage: bool = Field(default=True, description="是否需要生成圖片")
    custom_prompt: Optional[str] = Field(None, description="自定義提示詞")
    return_json: bool = Field(default=False, description="是否返回 JSON 格式 (默認返回 Markdown 文件)")

class TokenUsage(BaseModel):
    """Token 使用統計模型"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    cost_usd: float

class GenerateArticleResponse(BaseModel):
    """文章生成響應模型"""
    status: str
    message: str
    content: str
    token_usage: TokenUsage

def check_environment():
    """檢查環境變數是否正確設置"""
    # 載入環境變數
    load_dotenv()
    
    # 檢查必要的環境變數
    required_env_vars = {
        'GOOGLE_API_KEY': os.getenv('GOOGLE_API_KEY'),
        'GOOGLE_CSE_ID': os.getenv('GOOGLE_CSE_ID'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY')
    }
    
    missing_vars = []
    for var_name, var_value in required_env_vars.items():
        if not var_value:
            missing_vars.append(var_name)
    
    if missing_vars:
        raise ValueError(f"缺少必要的環境變數：{', '.join(missing_vars)}")
    
    return True

def generate_and_insert_image(openai_processor, article_text):
    """從文章標題生成圖片並將其插入到文章中"""
    # 從文章中提取標題 (使用 # 開頭的第一行)
    title_match = re.search(r'^#\s+(.+?)$', article_text, re.MULTILINE)
    if not title_match:
        title = "文章主題圖片"
    else:
        title = title_match.group(1).strip()
    
    # 生成圖片提示詞
    image_prompt = f"為以下標題創建一張高品質、吸引人的圖片，適合作為文章封面：「{title}」。圖片應該視覺上吸引人，與標題主題相關，並具有專業的外觀。請使用明亮、清晰的風格，適合在社交媒體上分享。"
    
    # 調用 OpenAI 生成圖片
    image_result = openai_processor.generate_image(
        prompt=image_prompt,
        size="1792x1024",
        quality="standard"
    )
    
    if not image_result:
        return article_text
    
    # 直接使用 DALL-E 3 提供的圖片 URL
    image_url = image_result.get("url")
    if not image_url:
        return article_text
    
    # 創建 Markdown 圖片標記
    image_markdown = f"\n\n![{title}]({image_url})\n\n"
    
    # 在標題後插入圖片
    if title_match:
        title_end_pos = title_match.end()
        modified_article = article_text[:title_end_pos] + image_markdown + article_text[title_end_pos:]
    else:
        # 如果找不到標題，則在文章開頭插入圖片
        modified_article = image_markdown + article_text
    
    return modified_article

@app.post("/generate_article")
async def generate_article(request: GenerateArticleRequest):
    """生成文章的 API 端點"""
    try:
        # 檢查環境設置
        check_environment()
        
        # 初始化 OpenAI 處理器
        openai_processor = OpenAIProcessor()
        
        # 使用 Google API 直接獲取搜尋結果，不使用 CrawlerClient 的上下文管理器
        crawler = CrawlerClient()
        crawler.crawler = AsyncWebCrawler()
        await crawler.crawler.__aenter__()
        
        try:
            # 執行搜尋和爬取
            search_results = crawler.get_search_urls(
                query=request.keyword,
                num_results=request.scraping_number
            )
            
            # 如果 API 搜尋失敗，返回空列表
            if not search_results:
                raise HTTPException(status_code=500, detail="搜尋結果為空")
            
            # 對每個搜尋結果進行深度爬取
            enriched_results = []
            for i, result in enumerate(search_results[:request.scraping_number], 1):
                try:
                    print(f"\n處理搜尋結果 {i}/{min(len(search_results), request.scraping_number)}")
                    
                    # 爬取頁面內容
                    crawled_data = await crawler._crawl_url_async(result['link'])
                    
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
            
            if not enriched_results:
                raise HTTPException(status_code=500, detail="爬取結果為空")
            
            # 使用 OpenAI 處理結果
            analysis = openai_processor.process_search_results(
                enriched_results,
                request.custom_prompt
            )
            
            if not analysis:
                raise HTTPException(status_code=500, detail="文章生成失敗")
            
            # 根據 isNeedImage 參數決定是否生成圖片
            if request.isNeedImage:
                analysis = generate_and_insert_image(openai_processor, analysis)
            
            # 獲取 token 使用量
            token_usage = openai_processor.get_token_usage()
            
            # 確保內容不包含原始的 \n 字符
            if analysis:
                analysis = re.sub(r'\\n+', '', analysis)
            
            # 根據 return_json 參數決定返回格式
            if request.return_json:
                # 返回 JSON 格式
                return GenerateArticleResponse(
                    status="success",
                    message="文章生成成功",
                    content=analysis,
                    token_usage=TokenUsage(
                        prompt_tokens=token_usage["prompt_tokens"],
                        completion_tokens=token_usage["completion_tokens"],
                        total_tokens=token_usage["total_tokens"],
                        cost_usd=token_usage["cost_usd"]
                    )
                )
            else:
                # 返回 Markdown 文件
                # 生成文件名
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                safe_query = request.keyword.replace(' ', '_').replace('/', '_').replace('\\', '_')[:30]
                filename = f"article_{safe_query}_{timestamp}.md"
                
                # 設置響應頭，使瀏覽器將其作為文件下載
                headers = {
                    'Content-Disposition': f'attachment; filename="{filename}"',
                    'Content-Type': 'text/markdown; charset=utf-8'
                }
                
                # 直接返回 Markdown 內容
                return Response(content=analysis, headers=headers)
        finally:
            # 確保爬蟲資源被釋放
            if crawler.crawler:
                await crawler.crawler.__aexit__(None, None, None)
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        import traceback
        print(f"生成文章時發生錯誤: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 
import os
import sys
from crawler_client import CrawlerClient
from openai_processor import OpenAIProcessor
from dotenv import load_dotenv

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
    
    print("環境變數檢查：")
    missing_vars = []
    
    for var_name, var_value in required_env_vars.items():
        status = '已設置' if var_value else '未設置'
        print(f"{var_name}: {status}")
        if not var_value:
            missing_vars.append(var_name)
    
    if missing_vars:
        raise ValueError(f"缺少必要的環境變數：{', '.join(missing_vars)}")
    
    return True

def get_user_input():
    """獲取使用者輸入的搜尋參數"""
    # 獲取搜尋關鍵字
    query = input("\n請輸入搜尋關鍵字: ")
    if not query.strip():
        print("錯誤：搜尋關鍵字不能為空")
        return None, None, None
    
    # 獲取結果數量
    num_results = input("請輸入需要的結果數量 (預設: 5): ")
    num_results = int(num_results) if num_results.strip() else 5
    
    # 獲取爬蟲策略
    print("\n請選擇爬蟲策略:")
    print("1. 標準搜尋 (僅爬取搜尋結果頁面)")
    print("2. BFS 策略 (廣度優先搜尋，爬取相關頁面)")
    strategy = input("請選擇 (1/2，預設: 1): ")
    
    if strategy == "2":
        # 如果選擇 BFS 策略，獲取更多參數
        max_pages = input("請輸入最大爬取頁面數 (預設: 10): ")
        max_pages = int(max_pages) if max_pages.strip() else 10
        
        max_depth = input("請輸入最大爬取深度 (預設: 2): ")
        max_depth = int(max_depth) if max_depth.strip() else 2
        
        return query, num_results, {
            "strategy": "bfs",
            "max_pages": max_pages,
            "max_depth": max_depth
        }
    else:
        return query, num_results, {"strategy": "standard"}

def display_results(search_results):
    """顯示搜尋結果概覽"""
    if not search_results:
        print("未找到搜尋結果或發生錯誤")
        return False
    
    print(f"\n找到並分析了 {len(search_results)} 個結果")
    print("\n搜尋結果概覽：")
    
    for i, result in enumerate(search_results, 1):
        title = result['title']
        link = result['link']
        content_length = len(result.get('content', ''))
        
        print(f"\n{i}. {title}")
        print(f"   網址: {link}")
        print(f"   內容長度: {content_length}")
    
    return True

def main():
    """主程式入口點"""
    try:
        # 檢查環境設置
        check_environment()
        
        # 初始化客戶端
        print("\n正在初始化爬蟲客戶端...")
        with CrawlerClient() as crawler_client:
            print("正在初始化 OpenAI 處理器...")
            openai_processor = OpenAIProcessor()
            
            # 獲取使用者輸入
            query, num_results, crawl_options = get_user_input()
            if not query:
                return
            
            # 執行搜尋和爬取
            print(f"\n正在搜尋並分析 '{query}'...")
            print("這可能需要一些時間，因為我們需要深入分析每個網頁...")
            
            # 根據選擇的策略執行不同的搜尋方法
            if crawl_options["strategy"] == "bfs":
                print(f"使用 BFS 策略，最大頁面數: {crawl_options['max_pages']}，最大深度: {crawl_options['max_depth']}")
                search_results = crawler_client.search_with_bfs(
                    query, 
                    max_pages=crawl_options['max_pages'], 
                    max_depth=crawl_options['max_depth']
                )
            else:
                print("使用標準搜尋策略")
                search_results = crawler_client.search(query, num_results)
            
            # 顯示搜尋結果
            if not display_results(search_results):
                return
            
            # 使用 OpenAI 處理結果
            print("\n正在使用 AI 進行深度分析...")
            analysis = openai_processor.process_search_results(search_results)
            
            # 顯示分析結果
            if analysis:
                print("\n分析結果：")
                print("=" * 80)
                print(analysis)
                print("=" * 80)
                
                # 保存分析結果到文件
                save_option = input("\n是否要保存分析結果到文件？(y/n): ")
                if save_option.lower() == 'y':
                    filename = f"analysis_{query.replace(' ', '_')}.txt"
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(f"搜尋關鍵字: {query}\n")
                        f.write(f"爬蟲策略: {crawl_options['strategy']}\n")
                        f.write(f"分析結果:\n{analysis}")
                    print(f"分析結果已保存到 {filename}")
            else:
                print("AI 分析過程中發生錯誤")
                
    except ValueError as ve:
        print(f"\n配置錯誤: {str(ve)}")
    except KeyboardInterrupt:
        print("\n程式已被使用者中斷")
    except Exception as e:
        print(f"\n程式執行時發生錯誤：{str(e)}")
        import traceback
        print("\n詳細錯誤訊息：")
        print(traceback.format_exc())

if __name__ == "__main__":
    main() 
import os
import sys
from crawler_client import CrawlerClient
from openai_processor import OpenAIProcessor
from dotenv import load_dotenv
import time

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
    """
    獲取使用者輸入的搜尋參數
    
    Returns:
        tuple: (查詢關鍵字, 結果數量, 爬蟲選項字典)
    """
    # 步驟 1: 獲取搜尋關鍵字
    # -----------------------------
    query = input("\n請輸入搜尋關鍵字: ")
    if not query.strip():
        print("錯誤：搜尋關鍵字不能為空")
        return None, None, None
    
    # 步驟 2: 獲取結果數量
    # -----------------------------
    num_results = input("請輸入需要的結果數量 (預設: 10): ")
    num_results = int(num_results) if num_results.strip() else 10
    
    # 返回標準搜尋策略的參數
    return query, num_results, {"strategy": "standard"}

def display_results(search_results):
    """
    格式化搜尋結果列表
    
    將搜尋結果格式化為易於閱讀的文本格式，包含標題、網址和內容長度等信息。
    
    Args:
        search_results (list): 搜尋結果列表，每個結果應為包含 title、link 和 content 的字典
        
    Returns:
        str: 格式化的結果字符串，如果沒有結果則返回 None
    """
    # 檢查是否有搜尋結果
    if not search_results:
        return None
    
    # 初始化結果字符串
    result_str = ""
    
    # 遍歷每個搜尋結果並格式化
    for i, result in enumerate(search_results, 1):
        # 提取結果信息
        title = result.get('title', '無標題')
        link = result.get('link', '無連結')
        content = result.get('content', '')
        content_length = len(content)
        
        # 格式化單個結果
        result_str += f"\n{i}. {title}\n"
        result_str += f"   網址: {link}\n"
        result_str += f"   內容長度: {content_length:,} 字符\n"
    
    return result_str

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
            
            # 顯示搜尋配置
            print(f"\n搜尋配置:")
            print(f"- 結果數量: {num_results}")
            
            # 執行標準搜尋
            search_results = crawler_client.search(query=query, num_results=num_results)
            
            # 格式化搜尋結果
            result_overview = display_results(search_results)
            if result_overview is None:
                print("未找到搜尋結果或發生錯誤")
                return
            
            # 使用 OpenAI 處理結果
            print("\n正在使用 AI 進行深度分析...")
            analysis = openai_processor.process_search_results(search_results)
            
            # 獲取 token 使用量和成本
            token_usage = openai_processor.get_token_usage()
            
            # 顯示搜尋結果和分析結果
            if analysis:
                # 定義分隔線和標題格式
                separator = "=" * 60
                section_separator = "-" * 50
                
                # 顯示主標題
                print(f"\n{separator}")
                print(f"   AI 分析結果: '{query}'")
                print(f"{separator}")
                
                # 顯示 token 使用量和成本
                print(f"\n【API 使用統計】")
                print(section_separator)
                print(f"模型: {openai_processor.model}")
                print(f"輸入 tokens: {token_usage['prompt_tokens']:,}")
                print(f"輸出 tokens: {token_usage['completion_tokens']:,}")
                print(f"總計 tokens: {token_usage['total_tokens']:,}")
                print(f"成本: ${token_usage['cost_usd']:.6f} USD")
                print(section_separator)
                
                # 顯示 AI 分析部分
                print(f"\n【AI 分析結果】")
                print(section_separator)
                print(analysis)
                print(section_separator)
                
                # 保存結果到文件選項
                save_option = input("\n是否要保存分析結果到文件？(y/n): ")
                if save_option.lower() == 'y':
                    # 生成文件名
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    safe_query = query.replace(' ', '_').replace('/', '_').replace('\\', '_')[:30]
                    filename = f"analysis_{safe_query}_{timestamp}.txt"
                    
                    # 寫入文件
                    try:
                        with open(filename, 'w', encoding='utf-8') as f:
                            # 寫入標題和基本信息
                            f.write(f"{separator}\n")
                            f.write(f"   AI 分析結果: '{query}'\n")
                            f.write(f"{separator}\n\n")
                            
                            f.write(f"搜尋時間: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                            f.write(f"搜尋關鍵字: {query}\n")
                            f.write(f"結果數量: {num_results}\n\n")
                            
                            # 寫入 token 使用量和成本
                            f.write(f"【API 使用統計】\n")
                            f.write(f"{section_separator}\n")
                            f.write(f"模型: {openai_processor.model}\n")
                            f.write(f"輸入 tokens: {token_usage['prompt_tokens']:,}\n")
                            f.write(f"輸出 tokens: {token_usage['completion_tokens']:,}\n")
                            f.write(f"總計 tokens: {token_usage['total_tokens']:,}\n")
                            f.write(f"成本: ${token_usage['cost_usd']:.6f} USD\n")
                            f.write(f"{section_separator}\n\n")
                            
                            # 寫入分析結果
                            f.write(f"【AI 分析結果】\n")
                            f.write(f"{section_separator}\n")
                            f.write(analysis + "\n")
                            f.write(f"{section_separator}\n")
                        
                        print(f"\n✓ 分析結果已成功保存到: {filename}")
                    except Exception as e:
                        print(f"\n✗ 保存文件時發生錯誤: {str(e)}")
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
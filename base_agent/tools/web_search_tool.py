import os
from langchain.tools import tool
from tavily import TavilyClient
from dotenv import load_dotenv
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

@dataclass
class SearchResult:
    """搜索结果数据类"""
    title: str
    url: str
    content: str
    score: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "title": self.title,                  # 标题
            "url": self.url,                      # 网页地址
            "content": self.content,              # 网页内容
            "score": self.score                   # 搜索相似度得分
        }

@tool
def web_search_tool(query: str, limit: int = 5) -> List[SearchResult]:
    """searches the web for the query and returns the results

    args:
        query (str): the query to search for
        limit (int): the number of results to return

    """
    load_dotenv(override=True)

    web_api_key = os.getenv("TAVILY_API_KEY")
    if not web_api_key:
        raise ValueError("Tavily API Key未找到！请设置TAVILY_API_KEY环境变量或在初始化时提供")
    
    web_search_client = TavilyClient(api_key=web_api_key)

    try:
        response = web_search_client.search(query = query, max_results = limit)
        results = []
        if 'results' in response:
            for item in response['results']:
                result = SearchResult(
                    title=item.get('title', ''),
                    url=item.get('url', ''),
                    content=item.get('content', ''),
                    score=item.get('score')
                )
                results.append(result)

        return results
    except Exception as e:
        print(f"搜索错误: {str(e)}")
        return []


# web_search("大连")


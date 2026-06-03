"""
novel_search.py
描述:
    小說爬蟲程式

流程:
    1.提供小說目錄頁面 URL，爬取該頁面並儲存為 index_page.html。
    2.從 index_page.html 解析章節，
    3.抓取每一章內容並儲存為 txt 檔。
注意事項:
    - 目前程式只爬取前 10 章，避免過度爬取造成網站負擔。
    - 爬取過程中加入隨機延遲，模擬人類行為，減少被封鎖的風險。
    - 已加入延遲和重試機制，提升爬取穩定性。
"""
import os
import time
import random
import requests as rq
from bs4 import BeautifulSoup

PRINT_ARG = True
def Decorator_Arguments(func):
    def wrapper(*args, **kwargs):
        if PRINT_ARG:
            print(f"Call Function : {func.__name__} Arguments: {args}, {kwargs}")
        return func(*args, **kwargs)
    return wrapper


@Decorator_Arguments
def fetch_index(url, retries=3)->tuple[bool, str ]:
    """ 
        爬取小說目錄頁面，並返回 HTML 內容。
    """
    for i in range(retries):
        try:
            _Res = rq.get(url, timeout=10)
            _Res.encoding = "utf-8"
            return True, _Res.text
        except Exception as e:
            _wait = random.uniform(1, 3)
            print(f'Error fetching {url}: {e}\nFailed to fetch {url} after {i} attempts. \nRetrying in {_wait:.2f} seconds...')
            time.sleep(_wait)
    print(f"Failed to fetch {url} after {retries} attempts.")
    return False, ""

# index_page = rq.request("GET", "https://m.wfxs.tw/xs-99423/")
# with open("index_page.html", "w", encoding="utf-8") as f:
#     f.write(index_page.text)
@Decorator_Arguments
def parse_index(file_path):
    """ 
        解析 index_page.html，提取章節標題和 URL。
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            _index = BeautifulSoup(f,"html.parser")
            print(f)
    except Exception as e:
        print(f"Error reading index file: {e}")
        return []

    _ChapterList = []
    # 找到所有章節連結
    _Links = _index.select("div.list ul.list li a")
    print(f"Found {len(_Links)} chapter links.")
    for _A in _Links:
        _Title = _A.text.strip()
        _Href = _A.get("href")
        _ChapterList.append({
            "title": _Title,
            "url": _Href
        })
    return _ChapterList
    
@Decorator_Arguments   
def parse_chapter(data):
    """ 
        解析章節內容，提取章節標題和正文。
    """
    _Soup = BeautifulSoup(data, "html.parser")
    _Title = _Soup.find("h1").text.strip()
    _ContentDiv = _Soup.find("div", id="content")
    _Paragraphs = _ContentDiv.find_all("p")

    _Lines = []
    for _P in _Paragraphs:
        _Text = _P.get_text(strip=True)
        if _Text:
            _Lines.append(_Text)
    _Content = "\n".join(_Lines)

    return _Title, _Content

@Decorator_Arguments
def fetch_chapter(iUrl,retries=3)->tuple[bool, str , str ]:
    """
    下載章節內容，返回章節標題和內容。
    """
    for _ in range(retries):
        try:
            _Res = rq.get(iUrl, timeout=10)
            _Res.encoding = "utf-8"
            connect = True
            break
        except Exception as e:
            _wait = random.uniform(1, 3)
            print(f"Error fetching {iUrl}: {e}")
            time.sleep(_wait)
    if not connect:
        print(f"Failed to fetch {iUrl} after {retries} attempts.")
        return False,"", ""
    _Title, _Content = parse_chapter(_Res.text)
    return True, _Title, _Content

@Decorator_Arguments
def fetch_full_novel(index_url,folder_path):
    """
    抓取指定小說，儲存為 txt 檔
    
    參數
        小說目錄url 與儲存路徑
    """
    if not os.path.exists(os.path.join(folder_path, "index_page.html")):
    #小說目錄.html不存在 沒抓過的小說
        res ,index_f= fetch_index(index_url)
        if res:
            print("Index page fetched successfully.")

        else:
            print("Failed to fetch index page.")
            return
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        with open(os.path.join(folder_path, "index_page.html"), "w", encoding="utf-8") as f:
            f.write(index_f)
    else:
        print("Index page already exists. Skipping fetch.")
        
    _ChapList = parse_index(os.path.join(folder_path, "index_page.html"))

    print(f"Found {len(_ChapList)} chapters.")
    for _Chapter in _ChapList:
        #_res,_title, _content = fetch_chapter(f"https://m.wfxs.tw{_Chapter['url']}")
        _res,_title, _content = fetch_chapter(_Chapter['url'])
        if not _res:
            print(f"Failed to fetch chapter: {_Chapter['title']}")
            continue
        with open(os.path.join(folder_path, _title), "w", encoding="utf-8") as f:
            f.write(_title + "\n")
            f.write(_content + "\n\n")
        print(f"Fetched: {_title}")
        time.sleep(random.uniform(2.5, 5.5))
    print("Done!")
    
@Decorator_Arguments
def fetch_single_chapter(chapter_url, folder_path):
    """
    抓取單一章節，儲存為 txt 檔
    
    參數
        章節url 與儲存路徑
    """
    res, title, content = fetch_chapter(chapter_url)
    if not res:
        print(f"Failed to fetch chapter: {chapter_url}")
        return
    _title,article = parse_chapter(content)
    
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    with open(os.path.join(folder_path, _title), "w", encoding="utf-8") as f:
        f.write(_title + "\n")
        f.write(article + "\n\n")
    print(f"Fetched: {_title}")

if __name__ == "__main__":
    fetch_full_novel("https://m.wfxs.tw/xiaoshuo/99423/", os.path.join(os.getcwd(), "仙本純良"))

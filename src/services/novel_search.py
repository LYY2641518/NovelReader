"""
novel_search.py (moved to services)
小說爬蟲程式
"""
import os
import time
import random
import requests as rq
from bs4 import BeautifulSoup
from urllib.parse import urljoin

PRINT_ARG = True
def Decorator_Arguments(func):
    def wrapper(*args, **kwargs):
        if PRINT_ARG:
            print(f"Call Function : {func.__name__} Arguments: {args}, {kwargs}")
        return func(*args, **kwargs)
    return wrapper


@Decorator_Arguments
def fetch_index(url, retries=3)->tuple[bool, str ]:
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


@Decorator_Arguments
def parse_index(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            _index = BeautifulSoup(f, "html.parser")
    except Exception as e:
        print(f"Error reading index file: {e}")
        return []

    _ChapterList = []
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
    # be defensive: handle bytes, BOM and multiple possible content containers
    if not data:
        return "", ""
    if isinstance(data, bytes):
        try:
            data = data.decode('utf-8')
        except Exception:
            data = data.decode('utf-8', errors='ignore')

    # strip BOM if present
    data = data.lstrip('\ufeff')

    soup = BeautifulSoup(data, "html.parser")

    # Title: prefer <h1> or h1.title, fallback to <title>
    title = None
    h1 = soup.find('h1')
    if h1 and h1.get_text(strip=True):
        title = h1.get_text(strip=True)
    else:
        h1c = soup.find('h1', class_='title')
        if h1c and h1c.get_text(strip=True):
            title = h1c.get_text(strip=True)
    if not title and soup.title and soup.title.string:
        title = soup.title.string.strip()
    if not title:
        title = ''

    # Content: try several common containers used by sites
    content_div = None
    selectors = [
        ("div", {"id": "content"}),
        ("div", {"id": "read_conent_box"}),
        ("div", {"class": "read-content"}),
        ("div", {"class": "entry"}),
        ("article", {}),
        ("div", {"class": "article-box"}),
    ]
    for tag, attrs in selectors:
        try:
            if attrs:
                content_div = soup.find(tag, attrs)
            else:
                content_div = soup.find(tag)
        except Exception:
            content_div = None
        if content_div:
            break

    paragraphs = []
    if content_div:
        # collect text from p and direct text nodes
        for p in content_div.find_all(['p', 'div']):
            txt = p.get_text(separator=' ', strip=True)
            if txt:
                paragraphs.append(txt)
    else:
        # fallback: gather all <p> in body
        for p in soup.find_all('p'):
            txt = p.get_text(separator=' ', strip=True)
            if txt:
                paragraphs.append(txt)

    content = "\n".join(paragraphs).strip()
    return title, content

@Decorator_Arguments
def fetch_chapter(iUrl,retries=3)->tuple[bool, str , str ]:
    # normalize to absolute URL
    base = 'https://m.wfxs.tw'
    try:
        abs_url = urljoin(base, iUrl)
    except Exception:
        abs_url = iUrl

    connect = False
    for _ in range(retries):
        try:
            _Res = rq.get(abs_url, timeout=10)
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
def fetch_full_novel(index_url,folder_path, cancel_event=None, progress_callback=None, max_chapters=None):
    if not os.path.exists(os.path.join(folder_path, "index_page.html")):
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
        
    # 嘗試從 index_page.html 取出 #sort_box 中的 active booklist 連結，進入並儲存為 menu.html
    index_path = os.path.join(folder_path, "index_page.html")
    menu_path = os.path.join(folder_path, "menu.html")
    menu_fetched = False
    try:
        with open(index_path, 'r', encoding='utf-8') as f:
            index_soup = BeautifulSoup(f.read(), 'html.parser')
        sort_box = index_soup.find(id='sort_box')
        if sort_box:
            a_active = sort_box.find('a', class_=lambda x: x and 'active' in x)
            if a_active and a_active.get('href') and 'booklist' in a_active.get('href'):
                href = a_active.get('href')
                if href.startswith('http'):
                    list_url = href
                else:
                    list_url = 'https://m.wfxs.tw' + href
                # fetch menu (may be paginated); fetch page 1 then subsequent pages to build full menu
                try:
                    import re
                    # attempt to extract book id
                    m = re.search(r'/booklist/(\d+)(?:/(\d+)\.html|\.html)?', list_url)
                    bid = m.group(1) if m else None
                    pages = []
                    # page 1: either /booklist/<id>.html or provided list_url
                    if bid:
                        pages.append('https://m.wfxs.tw' + f'/booklist/{bid}.html')
                    else:
                        pages.append(list_url)
                    # fetch sequential pages until empty
                    page = 2
                    while True:
                        if not bid:
                            break
                        purl = 'https://m.wfxs.tw' + f'/booklist/{bid}/{page}.html'
                        try:
                            rtest = rq.get(purl, timeout=8)
                            if rtest.status_code != 200:
                                break
                            pages.append(purl)
                        except Exception:
                            break
                        page += 1

                    # combine pages into menu_path content
                    combined = ''
                    for p in pages:
                        r = rq.get(p, timeout=10)
                        r.encoding = 'utf-8'
                        combined += '\n' + r.text
                    with open(menu_path, 'w', encoding='utf-8') as mf:
                        mf.write(combined)
                    menu_fetched = True
                except Exception as e:
                    print(f'Failed to fetch paginated menu: {e}')
    except Exception as e:
        print(f"Failed to fetch menu from index: {e}")

    # 如果 index_url 本身就是 booklist，也把 index_page.html 當作 menu.html
    if not menu_fetched and 'booklist' in index_url:
        try:
            # copy index to menu
            with open(index_path, 'r', encoding='utf-8') as src, open(menu_path, 'w', encoding='utf-8') as dst:
                dst.write(src.read())
            menu_fetched = True
        except Exception:
            menu_fetched = False

    # 以 menu.html 解析章節清單為優先，否則退回 parse_index
    if menu_fetched and os.path.exists(menu_path):
        _ChapList = []
        try:
            with open(menu_path, 'r', encoding='utf-8') as f:
                msoup = BeautifulSoup(f.read(), 'html.parser')
            # 常見章節列在 ul#html_box
            links = msoup.select('ul#html_box li a')
            if not links:
                links = msoup.select('div.entry ul li a')
            for a in links:
                t = a.get_text(strip=True)
                h = a.get('href')
                _ChapList.append({'title': t, 'url': h})
        except Exception as e:
            print(f"Failed to parse menu.html: {e}")
            _ChapList = parse_index(index_path)
    else:
        _ChapList = parse_index(index_path)

    total = len(_ChapList)
    print(f"Found {total} chapters.")
    if max_chapters is not None:
        _ChapList = _ChapList[:max_chapters]

    for idx, _Chapter in enumerate(_ChapList):
        # check cancellation
        if cancel_event is not None and getattr(cancel_event, 'is_set', lambda: False)():
            print("Download cancelled by user.")
            break

        _res,_title, _content = fetch_chapter(_Chapter['url'])
        if not _res:
            print(f"Failed to fetch chapter: {_Chapter.get('title')}")
            continue
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        with open(os.path.join(folder_path, _title), "w", encoding="utf-8") as f:
            f.write(_title + "\n")
            f.write(_content + "\n\n")

        # progress callback
        if progress_callback:
            try:
                progress_callback(idx+1, total, _title)
            except Exception:
                pass

        print(f"Fetched: {_title}")
        # small delay and check cancel during sleep
        for _ in range(int(random.uniform(1,3) * 10)):
            if cancel_event is not None and getattr(cancel_event, 'is_set', lambda: False)():
                break
            time.sleep(0.1)
    print("Done!")

@Decorator_Arguments
def fetch_single_chapter(chapter_url, folder_path):
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

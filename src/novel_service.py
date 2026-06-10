from pathlib import Path
import os
from core.setting import DATA_DIR
from services import novel_search
import requests as rq
from bs4 import BeautifulSoup
import re


DOWNLOAD_DIR = Path(DATA_DIR) / "downloads"


def ensure_download_dir():
    if not DOWNLOAD_DIR.exists():
        DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _abs_url(base: str, href: str):
    if not href:
        return href
    if href.startswith('http'):
        return href
    return base.rstrip('/') + '/' + href.lstrip('/')


def search(keyword: str):
    """
    在 https://m.wfxs.tw/s/ 執行實際搜尋，回傳 list of {title, index_url}
    """
    base = 'https://m.wfxs.tw'
    session = rq.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })

    try:
        resp = session.get(f"{base}/s/", timeout=10)
        resp.encoding = 'utf-8'
    except Exception:
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    input_elem = soup.find(id='searchInput')
    form = input_elem.find_parent('form') if input_elem else None

    action = form.get('action') if form and form.get('action') else '/s/'
    method = (form.get('method') or 'get').lower() if form else 'get'
    input_name = input_elem.get('name') if input_elem and input_elem.get('name') else 'searchkey'

    url = action if action.startswith('http') else _abs_url(base, action)

    try:
        if method == 'post':
            r = session.post(url, data={input_name: keyword}, timeout=10)
        else:
            r = session.get(url, params={input_name: keyword}, timeout=10)
        r.encoding = 'utf-8'
    except Exception:
        return []

    s2 = BeautifulSoup(r.text, 'html.parser')
    results = []
    for a in s2.select('a.book-title'):
        title = a.get_text(strip=True)
        href = a.get('href')
        book_url = _abs_url(base, href)
        results.append({'title': title, 'index_url': book_url})

    return results


def download_book(index_url: str, title: str, cancel_event=None, progress_callback=None, max_chapters=None):
    """從書籍頁(index_url)取得目錄連結，然後呼叫 services.novel_search.fetch_full_novel 下載章節到 downloads/title
    支援傳入 cancel_event 與 progress_callback。"""
    ensure_download_dir()
    folder = DOWNLOAD_DIR / title

    base = 'https://m.wfxs.tw'
    try:
        resp = rq.get(index_url, timeout=10)
        resp.encoding = 'utf-8'
    except Exception:
        # fallback: try using provided index_url directly (may already be booklist)
        novel_search.fetch_full_novel(index_url, str(folder), cancel_event=cancel_event, progress_callback=progress_callback, max_chapters=max_chapters)
        return str(folder)

    soup = BeautifulSoup(resp.text, 'html.parser')
    list_url = None

    # 1) 若 index_url 本身就是 booklist，直接使用
    if 'booklist' in index_url:
        list_url = index_url if index_url.startswith('http') else _abs_url(base, index_url)

    # 2) 優先在 #sort_box 中尋找帶 .active 的 booklist 連結
    if not list_url:
        sort_box = soup.find(id='sort_box')
        if sort_box:
            a_active = sort_box.find('a', class_=re.compile(r'active'))
            if a_active and a_active.get('href') and 'booklist' in a_active.get('href'):
                list_url = _abs_url(base, a_active.get('href'))

    # 3) 若未找到，退回尋找任一包含 booklist 的連結
    if not list_url:
        a = soup.find('a', href=re.compile(r'booklist'))
        if a and a.get('href'):
            list_url = _abs_url(base, a.get('href'))

    if not list_url:
        # 找不到 booklist，就不要冒然下載，回報錯誤
        raise RuntimeError(f"找不到書籍目錄 (booklist) 於 {index_url}")

    # 確認 list_url 包含 booklist，再開始下載
    if 'booklist' not in list_url:
        raise RuntimeError(f"解析出的目錄連結不是 booklist：{list_url}")

    # 呼叫爬蟲下載整本（services.novel_search 會處理 index/menu 解析）
    novel_search.fetch_full_novel(list_url, str(folder), cancel_event=cancel_event, progress_callback=progress_callback, max_chapters=max_chapters)
    return str(folder)


def list_books():
    ensure_download_dir()
    return [p.name for p in DOWNLOAD_DIR.iterdir() if p.is_dir()]


def list_chapters(book_title: str):
    folder = DOWNLOAD_DIR / book_title
    if not folder.exists():
        return []
    files = [f.name for f in folder.iterdir() if f.is_file() and f.name != "index_page.html"]
    return sorted(files)


def read_chapter(book_title: str, chapter_filename: str):
    folder = DOWNLOAD_DIR / book_title
    file_path = folder / chapter_filename
    if not file_path.exists():
        return ""
    return file_path.read_text(encoding="utf-8")


def _meta_path(book_title: str):
    folder = DOWNLOAD_DIR / book_title
    return folder / 'meta.json'


def set_last_read(book_title: str, chapter_title: str):
    """Store last-read chapter title in downloads/{book}/meta.json"""
    try:
        folder = DOWNLOAD_DIR / book_title
        folder.mkdir(parents=True, exist_ok=True)
        meta = {}
        mp = _meta_path(book_title)
        if mp.exists():
            import json
            meta = json.loads(mp.read_text(encoding='utf-8') or '{}')
        meta['last_read'] = chapter_title
        mp.write_text(__import__('json').dumps(meta, ensure_ascii=False), encoding='utf-8')
    except Exception:
        pass


def get_last_read(book_title: str):
    """Return last-read chapter title or None"""
    try:
        mp = _meta_path(book_title)
        if not mp.exists():
            return None
        import json
        meta = json.loads(mp.read_text(encoding='utf-8') or '{}')
        return meta.get('last_read')
    except Exception:
        return None


def get_total_chapters(index_url: str):
    """嘗試從 index_url 或其 booklist 取得章節總數，回傳 int 或 None"""
    try:
        resp = rq.get(index_url, timeout=10)
        resp.encoding = 'utf-8'
    except Exception:
        return None

    soup = BeautifulSoup(resp.text, 'html.parser')
    # 檢查 id=bh_chat_count
    el = soup.find(id='bh_chat_count')
    if el and el.get_text(strip=True).isdigit():
        return int(el.get_text(strip=True))

    # 檢查 meta property 或其他位置
    meta = soup.find('meta', {'property': 'og:novel:book_name'})
    # fallback: search for "共...章"
    m = soup.find(text=lambda t: t and '共' in t and '章' in t)
    if m:
        import re
        rr = re.search(r'共\s*(\d+)\s*章', m)
        if rr:
            try:
                return int(rr.group(1))
            except Exception:
                pass

    # try booklist link
    sort_box = soup.find(id='sort_box')
    if sort_box:
        a_active = sort_box.find('a', class_=lambda x: x and 'active' in x)
        if a_active and a_active.get('href') and 'booklist' in a_active.get('href'):
            href = a_active.get('href')
            if href.startswith('http'):
                list_url = href
            else:
                list_url = 'https://m.wfxs.tw' + href
            try:
                r2 = rq.get(list_url, timeout=10)
                r2.encoding = 'utf-8'
                s2 = BeautifulSoup(r2.text, 'html.parser')
                el2 = s2.find(id='bh_chat_count')
                if el2 and el2.get_text(strip=True).isdigit():
                    return int(el2.get_text(strip=True))
            except Exception:
                return None

    return None


def get_book_details(index_url: str):
    """回傳書籍摘要與章節清單（不下載章節）。
    回傳 dict: {title, author, summary, total, chapters:[{title,url}, ...]}
    """
    try:
        resp = rq.get(index_url, timeout=10)
        resp.encoding = 'utf-8'
    except Exception:
        return None

    soup = BeautifulSoup(resp.text, 'html.parser')
    data = {'title': None, 'author': None, 'summary': None, 'total': None, 'chapters': []}
    # title
    h2 = soup.find('h2')
    if h2:
        data['title'] = h2.get_text(strip=True)

    # author and summary — be flexible for class names like 'synopsis bor-top'
    syn = soup.find(lambda tag: tag.name == 'div' and tag.get('class') and any('synopsis' in c for c in tag.get('class')))
    if not syn:
        # try alternative common class
        syn = soup.find('div', class_=lambda c: c and 'synopsis' in c)
    if syn:
        # try to find author from spans inside .item or direct spans
        author = None
        item_div = syn.find('div', class_=lambda c: c and 'item' in c) or syn
        for sp in item_div.find_all('span'):
            txt = sp.get_text(strip=True)
            if '作者' in txt:
                author = txt.replace('作者：', '').replace('作者:', '').strip()
                break
        if author:
            data['author'] = author

        # summary paragraph may be inside a <p> within synopsis
        p = syn.find('p')
        if p:
            data['summary'] = p.get_text(separator=' ', strip=True)

    # total
    el = soup.find(id='bh_chat_count')
    if el and el.get_text(strip=True).isdigit():
        data['total'] = int(el.get_text(strip=True))

    # find menu (booklist) and parse chapters without downloading content
    list_url = None
    sort_box = soup.find(id='sort_box')
    if sort_box:
        a_active = sort_box.find('a', class_=lambda x: x and 'active' in x)
        if a_active and a_active.get('href') and 'booklist' in a_active.get('href'):
            href = a_active.get('href')
            list_url = href if href.startswith('http') else _abs_url('https://m.wfxs.tw', href)

    # helper: fetch chapters across paginated booklist pages
    def _gather_booklist_pages(base_url):
        def _extract_total_chapters(soup):
            el = soup.find(id='bh_chat_count')
            if el and el.get_text(strip=True).isdigit():
                return int(el.get_text(strip=True))
            m = soup.find(text=lambda t: t and '共' in t and '章' in t)
            if m:
                rr = re.search(r'共\s*(\d+)\s*章', m)
                if rr:
                    try:
                        return int(rr.group(1))
                    except Exception:
                        pass
            return None

        chapters = []
        try:
            parsed = rq.utils.urlparse(base_url)
        except Exception:
            parsed = None
        # try extract book id from path
        bid = None
        if parsed:
            m = re.search(r'/booklist/(\d+)(?:/(\d+)\.html|\.html)?', parsed.path)
            if m:
                bid = m.group(1)

        page = 1
        seen = set()
        total_pages = None
        while True:
            if page == 1:
                # try /booklist/<id>.html first
                if bid:
                    page_url = 'https://m.wfxs.tw' + f'/booklist/{bid}.html'
                else:
                    page_url = base_url
            else:
                if bid:
                    page_url = 'https://m.wfxs.tw' + f'/booklist/{bid}/{page}.html'
                else:
                    # append page suffix to provided url
                    if base_url.endswith('.html'):
                        page_url = base_url.replace('.html', f'/{page}.html')
                    else:
                        page_url = base_url.rstrip('/') + f'/{page}.html'
            try:
                r = rq.get(page_url, timeout=10)
                if r.status_code != 200:
                    break
                r.encoding = 'utf-8'
                msoup = BeautifulSoup(r.text, 'html.parser')
                links = msoup.select('ul#html_box li a') or msoup.select('div.entry ul li a') or msoup.select('div.catalog ul li a')
                if not links:
                    break
                if page == 1:
                    total_chapters = _extract_total_chapters(msoup)
                    per_page = len(links)
                    if total_chapters and per_page:
                        total_pages = -(-total_chapters // per_page)
                added = 0
                for a in links:
                    t = a.get_text(strip=True)
                    h = a.get('href')
                    key = (t, h)
                    if key in seen:
                        continue
                    seen.add(key)
                    chapters.append({'title': t, 'url': _abs_url('https://m.wfxs.tw', h)})
                    added += 1
                if added == 0:
                    break
            except Exception:
                break
            page += 1
            if total_pages is not None and page > total_pages:
                break
            # safety cap
            if page > 1000:
                break
        return chapters

    # if we have list_url fetch and parse (support pagination)
    if list_url:
        try:
            gathered = _gather_booklist_pages(list_url)
            if gathered:
                data['chapters'].extend(gathered)
                if not data['total']:
                    # try fetch count from first page
                    try:
                        r2 = rq.get(list_url, timeout=10)
                        r2.encoding = 'utf-8'
                        el2 = BeautifulSoup(r2.text, 'html.parser').find(id='bh_chat_count')
                        if el2 and el2.get_text(strip=True).isdigit():
                            data['total'] = int(el2.get_text(strip=True))
                    except Exception:
                        pass
        except Exception:
            pass

    # fallback: try parse index page chapters
    if not data['chapters']:
        # try multiple selectors including catalog blocks
        selectors = [
            'ul#html_box li a',
            'div.entry ul li a',
            'div.catalog div.entry ul li a',
            'div.catalog ul li a',
            'div.list ul.list li a'
        ]
        links = []
        for sel in selectors:
            found = soup.select(sel)
            if found:
                links = found
                break
        for a in links:
            t = a.get_text(strip=True)
            h = a.get('href')
            data['chapters'].append({'title': t, 'url': _abs_url('https://m.wfxs.tw', h)})

    return data


def fetch_chapter_online(iUrl):
    """呼叫 services.novel_search.fetch_chapter 取得單章內容（title, content）"""
    try:
        res, title, content = __import__('services.novel_search', fromlist=['fetch_chapter']).fetch_chapter(iUrl)
        if res:
            return title, content
    except Exception:
        pass
    return None, None

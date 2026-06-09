from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.app import App

import novel_service
from core.setting import FONT_TW_SERIF
from urllib.parse import urlparse, urljoin
from threading import Thread
from kivy.clock import Clock


class BookScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')

        # header: title / author
        self.header = BoxLayout(orientation='horizontal', size_hint_y=None, height=100)
        self.info = Label(text='尚未選擇書籍', halign='left', valign='top', text_size=(400, None), font_name=str(FONT_TW_SERIF))
        self.header.add_widget(self.info)

        self.btn_box = BoxLayout(orientation='vertical', size_hint_x=0.35)
        self.dl_btn = Button(text='下載全部', size_hint_y=None, height=40, font_name=str(FONT_TW_SERIF))
        self.back_btn = Button(text='返回搜尋', size_hint_y=None, height=40, font_name=str(FONT_TW_SERIF))
        self.btn_box.add_widget(self.dl_btn)
        self.btn_box.add_widget(self.back_btn)
        self.header.add_widget(self.btn_box)

        self.layout.add_widget(self.header)

        # total
        self.total_lbl = Label(text='總章節數: 0', size_hint_y=None, height=30, font_name=str(FONT_TW_SERIF))
        self.layout.add_widget(self.total_lbl)

        # chapters list
        self.ch_scroll = ScrollView()
        self.ch_grid = GridLayout(cols=1, size_hint_y=None)
        self.ch_grid.bind(minimum_height=self.ch_grid.setter('height'))
        self.ch_scroll.add_widget(self.ch_grid)
        self.layout.add_widget(self.ch_scroll)

        self.add_widget(self.layout)

        self.current = None

        self.back_btn.bind(on_press=self._back_to_search)
        self.dl_btn.bind(on_press=self._on_download_all)

    def load_details(self, title, index_url, details):
        # prefer booklist page when available: convert /xiaoshuo/<id> -> /booklist/<id>.html
        self.current = {'title': title, 'index_url': index_url, 'details': details}

        # if index_url looks like the mobile index (/xiaoshuo/...), try to derive the booklist URL
        try:
            if index_url and 'booklist' not in index_url and 'xiaoshuo' in index_url:
                parsed = urlparse(index_url)
                # try find numeric book id in path: prefer the segment after 'xiaoshuo'
                parts = [p for p in parsed.path.rstrip('/').split('/') if p]
                book_id = None
                try:
                    low_parts = [p.lower() for p in parts]
                    if 'xiaoshuo' in low_parts:
                        i = low_parts.index('xiaoshuo')
                        # next segment should be the book id
                        if i + 1 < len(parts) and parts[i + 1].isdigit():
                            book_id = parts[i + 1]
                    # fallback: find the first numeric segment that looks like a book id (avoid chapter-level ids)
                    if not book_id:
                        for p in parts:
                            if p.isdigit() and len(p) <= 6:
                                book_id = p
                                break
                except Exception:
                    book_id = None
                if book_id:
                    booklist_url = urljoin(f"{parsed.scheme}://{parsed.netloc}", f"/booklist/{book_id}.html")
                    # always prefer to fetch details from the canonical booklist URL when possible
                    try:
                        fetched = novel_service.get_book_details(booklist_url)
                        if fetched:
                            details = fetched
                            self.current['index_url'] = booklist_url
                            self.current['details'] = details
                    except Exception:
                        # keep original details if fetching booklist fails
                        pass
        except Exception:
            pass

        # update info: only show book title (no summary)
        title_text = (details or {}).get('title', '')
        self.info.text = title_text
        total = (details or {}).get('total') or len((details or {}).get('chapters', []))
        self.total_lbl.text = f"總章節數: {total}"

        # populate chapters
        self.ch_grid.clear_widgets()
        downloaded = novel_service.list_chapters(title) if title in novel_service.list_books() else []
        for ch in (details or {}).get('chapters', []):
            ch_title = ch.get('title')
            ch_url = ch.get('url')
            text = ch_title
            if ch_title in downloaded:
                text = f"{ch_title} (已離線)"
            b = Button(text=text, size_hint_y=None, height=40, font_name=str(FONT_TW_SERIF))
            b.bind(on_press=lambda inst, u=ch_url, t=ch_title: self._open_chapter(u, t))
            self.ch_grid.add_widget(b)

    def _open_chapter(self, chapter_url, chapter_title):
        # open chapter: if offline exists, open local; else fetch online
        title = self.current.get('title') if self.current else None
        downloaded = novel_service.list_chapters(title) if title in novel_service.list_books() else []
        app = App.get_running_app()

        if chapter_title in downloaded:
            if app and hasattr(app, 'screen_manager'):
                reader = app.screen_manager.get_screen('reader')
                reader.load_book(title)
                reader.load_chapter(chapter_title)
                app.screen_manager.current = 'reader'
            return

        def _worker():
            t, content = novel_service.fetch_chapter_online(chapter_url)
            def _ui(dt):
                if not content:
                    # let search screen log
                    ss = app.screen_manager.get_screen('search')
                    if hasattr(ss, '_log'):
                        ss._log('無法載入章節')
                    return
                if app and hasattr(app, 'screen_manager'):
                    reader = app.screen_manager.get_screen('reader')
                    # set content and switch to reader
                    reader.content_label.text = content
                    app.screen_manager.current = 'reader'
            Clock.schedule_once(_ui, 0)

        # pre-populate reader with chapter list synchronously so prev/next work immediately
        try:
            if app and hasattr(app, 'screen_manager'):
                reader = app.screen_manager.get_screen('reader')
                reader.title_label.text = title
                reader.current_book = title
                details = (self.current.get('details') if getattr(self, 'current', None) else None)
                if details and details.get('chapters'):
                    try:
                        reader.chapters = details.get('chapters')
                    except Exception:
                        reader.chapters = []
                    try:
                        idx = next(i for i,c in enumerate(reader.chapters) if c.get('title') == chapter_title)
                        reader.current_chapter_idx = idx
                    except Exception:
                        reader.current_chapter_idx = -1
                    reader._refresh_chapter_btns()
                    reader._update_nav_info()
        except Exception:
            pass

        Thread(target=_worker, daemon=True).start()

    def _on_download_all(self, instance):
        if not self.current:
            return
        index_url = self.current.get('index_url')
        title = self.current.get('title')
        # reuse SearchScreen download mechanics by calling its method
        app = App.get_running_app()
        if app and hasattr(app, 'screen_manager'):
            ss = app.screen_manager.get_screen('search')
            # create a fake button to pass if needed
            fake_btn = self.dl_btn
            ss._start_download_from_details(index_url, title, fake_btn)

    def _back_to_search(self, instance):
        app = App.get_running_app()
        if app and hasattr(app, 'screen_manager'):
            app.screen_manager.current = 'search'
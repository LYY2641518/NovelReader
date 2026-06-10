from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button

from ui.widgets.search_bar import SearchBarWidget
import novel_service
from kivy.app import App
from core.setting import FONT_TW_SERIF
from threading import Thread, Event
from kivy.clock import Clock


class SearchScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = BoxLayout(orientation="vertical")

        # track active downloads: title -> {event, thread, button}
        self.active_downloads = {}

        self._build_ui()

        self.add_widget(self.layout)

    def _build_ui(self):

        top_bar = BoxLayout(size_hint_y=0.08)
        top_bar.add_widget(Label(text="小說閱讀器", font_name=str(FONT_TW_SERIF)))
        lib_btn = Button(text='書庫', size_hint_x=0.2, font_name=str(FONT_TW_SERIF))
        lib_btn.bind(on_press=lambda inst: self._open_library())
        top_bar.add_widget(lib_btn)

        # keep reference so we can hide/show it when viewing book details
        self.search_bar = SearchBarWidget(
            on_search=self.on_search,
            size_hint_y=0.10
        )

        # details area (hidden until a book selected)
        self.details_box = BoxLayout(orientation='vertical', size_hint_y=0.3)

        # result area with scroll
        self.result_scroll = ScrollView(size_hint_y=0.4)
        self.result_grid = GridLayout(cols=1, size_hint_y=None)
        self.result_grid.bind(minimum_height=self.result_grid.setter('height'))
        self.result_scroll.add_widget(self.result_grid)

        # Log Panel
        self.log_panel = Label(
            text="準備就緒",
            size_hint_y=0.12,
            font_name=str(FONT_TW_SERIF)
        )

        self.layout.add_widget(top_bar)
        self.layout.add_widget(self.search_bar)
        self.layout.add_widget(self.details_box)
        self.layout.add_widget(self.result_scroll)
        self.layout.add_widget(self.log_panel)

    # ======================================
    # EVENT HANDLER (SearchBar → Screen)
    # ======================================

    def on_search(self, keyword: str):
        self._log(f"收到搜尋請求: {keyword}")

        result = novel_service.search(keyword)

        self._update_result(result)

    # ======================================
    # UI UPDATE
    # ======================================

    def _update_result(self, result_list):
        # clear existing
        self.result_grid.clear_widgets()

        for item in result_list:
            btn = Button(text=item.get('title'), size_hint_y=None, height=40, font_name=str(FONT_TW_SERIF))
            btn.bind(on_press=lambda inst, it=item: self._show_book_details(it, inst))
            self.result_grid.add_widget(btn)

        self._log(f"搜尋完成，共 {len(result_list)} 筆")

    def _on_result_selected(self, item, btn):
        # deprecated: downloads are started via the details panel's download button
        pass

    def _log(self, message: str):
        self.log_panel.text = message

    # ======================
    # Book details UI
    # ======================
    def _show_book_details(self, item, inst_button):
        # load details in background
        index_url = item.get('index_url')
        title = item.get('title')

        def _worker():
            details = novel_service.get_book_details(index_url)

            def _ui(dt):
                # open BookScreen and populate it
                app = App.get_running_app()
                if app and hasattr(app, 'screen_manager'):
                    try:
                        book_screen = app.screen_manager.get_screen('book')
                        book_screen.load_details(title, index_url, details)
                        app.screen_manager.current = 'book'
                    except Exception:
                        # fallback to inline details box
                        self._populate_details(title, index_url, details)
            Clock.schedule_once(_ui, 0)

        self._log(f"載入書籍資訊: {title}")
        t = Thread(target=_worker, daemon=True)
        t.start()

    def _populate_details(self, title, index_url, details):
        # clear details box and hide search/results to maximize details view
        self.details_box.clear_widgets()
        try:
            self.search_bar.opacity = 0
            self.search_bar.disabled = True
        except Exception:
            pass
        try:
            self.result_scroll.size_hint_y = 0
        except Exception:
            pass

        # remember current details for returning from reader
        self.current_details = {'title': title, 'index_url': index_url, 'details': details}

        if not details:
            self.details_box.add_widget(Label(text='無法取得書籍資訊', font_name=str(FONT_TW_SERIF)))
            return

        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=80)
        info = Label(text=f"{details.get('title','')}\n作者: {details.get('author','未知')}\n{details.get('summary','')}", halign='left', valign='top', text_size=(self.width*0.6, None), font_name=str(FONT_TW_SERIF))
        header.add_widget(info)

        # download button
        dl_btn = Button(text='下載全部', size_hint_x=0.2, font_name=str(FONT_TW_SERIF))
        header.add_widget(dl_btn)

        # return to search button
        back_btn = Button(text='返回搜尋', size_hint_x=0.2, font_name=str(FONT_TW_SERIF))
        back_btn.bind(on_press=lambda inst: self._close_details())
        header.add_widget(back_btn)

        self.details_box.add_widget(header)

        # total
        total = details.get('total') or len(details.get('chapters', []))
        total_lbl = Label(text=f"總章節數: {total}", size_hint_y=None, height=30, font_name=str(FONT_TW_SERIF))
        self.details_box.add_widget(total_lbl)

        # chapter list
        ch_scroll = ScrollView()
        ch_grid = GridLayout(cols=1, size_hint_y=None)
        ch_grid.bind(minimum_height=ch_grid.setter('height'))

        # check downloaded chapters for this book
        downloaded = novel_service.list_chapters(title) if title in novel_service.list_books() else []

        for ch in details.get('chapters', []):
            ch_title = ch.get('title')
            ch_url = ch.get('url')
            text = ch_title
            # mark offline
            if ch_title in downloaded:
                text = f"{ch_title} (已離線)"
            b = Button(text=text, size_hint_y=None, height=36, font_name=str(FONT_TW_SERIF))
            b.bind(on_press=lambda inst, u=ch_url, t=ch_title: self._on_chapter_clicked(title, u, t))
            ch_grid.add_widget(b)

        ch_scroll.add_widget(ch_grid)
        self.details_box.add_widget(ch_scroll)

        # bind download button
        dl_btn.bind(on_press=lambda inst: self._start_download_from_details(index_url, title, dl_btn))

    def _on_chapter_clicked(self, book_title, chapter_url, chapter_title):
        # if offline exists, open offline; else fetch online
        downloaded = novel_service.list_chapters(book_title) if book_title in novel_service.list_books() else []
        if chapter_title in downloaded:
            app = App.get_running_app()
            if app and hasattr(app, 'screen_manager'):
                reader = app.screen_manager.get_screen('reader')
                reader.load_book(book_title)
                reader.load_chapter(chapter_title)
                app.screen_manager.current = 'reader'
            return

        # fetch online in background
        def _worker():
            t, content = novel_service.fetch_chapter_online(chapter_url)
            def _ui(dt):
                if not content:
                    self._log('無法載入章節')
                    return
                app = App.get_running_app()
                if app and hasattr(app, 'screen_manager'):
                    reader = app.screen_manager.get_screen('reader')
                    reader.load_book(book_title)
                    reader.content_label.text = content
                    app.screen_manager.current = 'reader'
            Clock.schedule_once(_ui, 0)

        self._log(f"載入章節: {chapter_title}")
        t = Thread(target=_worker, daemon=True)
        t.start()

    def _start_download_from_details(self, index_url, title, dl_btn):
        # reuse existing active_downloads mechanics
        if title in self.active_downloads:
            ev = self.active_downloads[title]['event']
            ev.set()
            self._log(f"已發出取消: {title}")
            return

        cancel_event = Event()
        self.active_downloads[title] = {'event': cancel_event, 'thread': None, 'button': dl_btn}

        def progress_callback(done, total, chapter_title):
            def _ui(dt):
                if title in self.active_downloads:
                    b = self.active_downloads[title]['button']
                    b.text = f"下載中 {done}/{total}"
            Clock.schedule_once(_ui, 0)

        def _worker():
            try:
                folder = novel_service.download_book(index_url, title, cancel_event=cancel_event, progress_callback=progress_callback)
                def _on_done(dt):
                    self.active_downloads.pop(title, None)
                    dl_btn.text = '下載完成'
                    self._log(f"下載完成: {title} 存於 {folder}")
                Clock.schedule_once(_on_done, 0)
            except Exception as e:
                err_msg = str(e)
                def _on_err(dt):
                    self.active_downloads.pop(title, None)
                    dl_btn.text = '下載失敗'
                    self._log(f"下載失敗: {title}，錯誤: {err_msg}")
                Clock.schedule_once(_on_err, 0)

        dl_btn.text = '開始下載'
        t = Thread(target=_worker, daemon=True)
        self.active_downloads[title]['thread'] = t
        t.start()

    def _open_library(self):
        app = App.get_running_app()
        if app and hasattr(app, 'screen_manager'):
            app.screen_manager.current = 'library'

    def _close_details(self):
        # restore search bar and results
        try:
            self.search_bar.opacity = 1
            self.search_bar.disabled = False
        except Exception:
            pass
        try:
            self.result_scroll.size_hint_y = 0.4
        except Exception:
            pass
        # clear details box
        self.details_box.clear_widgets()
        self.current_details = None

    def show_details_for(self, book_title: str):
        """Populate details for a book (used when returning from reader).
        If we have cached details, reuse them; otherwise fetch anew."""
        if getattr(self, 'current_details', None) and self.current_details.get('title') == book_title:
            cd = self.current_details
            self._populate_details(cd['title'], cd['index_url'], cd['details'])
            return

        # otherwise fetch details in background
        def _worker():
            details = novel_service.get_book_details(f'https://m.wfxs.tw/xiaoshuo/')
            def _ui(dt):
                self._populate_details(book_title, None, details)
            Clock.schedule_once(_ui, 0)

        t = Thread(target=_worker, daemon=True)
        t.start()
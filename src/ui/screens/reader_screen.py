from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.app import App
from kivy.clock import Clock

import novel_service
from core.setting import FONT_TW_SERIF


class ReaderScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = BoxLayout(orientation='vertical')

        # top bar: menu, title, 返回書籍, 返回搜尋
        top_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)

        self.menu_btn = Button(text='☰ 章節', size_hint_x=0.10, font_name=str(FONT_TW_SERIF), font_size='14sp')
        self.menu_btn.bind(on_press=self._toggle_chapter_list)
        top_layout.add_widget(self.menu_btn)

        self.title_label = Label(text='尚未選擇書籍', size_hint_x=0.50, font_name=str(FONT_TW_SERIF))
        top_layout.add_widget(self.title_label)
        self.back_to_book_btn = Button(text='返回書籍', size_hint_x=0.20, font_name=str(FONT_TW_SERIF), font_size='16sp', height=40)
        self.back_to_book_btn.bind(on_press=self._back_to_book)
        top_layout.add_widget(self.back_to_book_btn)
        self.back_btn = Button(text='返回搜尋', size_hint_x=0.20, font_name=str(FONT_TW_SERIF), font_size='16sp', height=40)
        self.back_btn.bind(on_press=self._back_to_search)
        top_layout.add_widget(self.back_btn)
        
        # chapter list (initially hidden)
        self.ch_scroll = ScrollView(size_hint_y=0.25)
        self.ch_grid = GridLayout(cols=1, size_hint_y=None)
        self.ch_grid.bind(minimum_height=self.ch_grid.setter('height'))
        self.ch_scroll.add_widget(self.ch_grid)
        self.ch_scroll.size_hint_y = 0  # hidden by default

        # content area (maximized)
        self.content_scroll = ScrollView(size_hint_y=1)
        # left-aligned, top-aligned label that will wrap to the scroll width
        self.content_label = Label(text='請選擇章節', size_hint_y=None, font_name=str(FONT_TW_SERIF), halign='left', valign='top')
        self.content_label.bind(texture_size=self._update_content_height)
        self.content_scroll.add_widget(self.content_label)

        # nav controls (prev/current/next) at bottom
        nav_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=45)
        self.prev_btn = Button(text='← 上一章', size_hint_x=0.2, font_name=str(FONT_TW_SERIF))
        self.prev_btn.bind(on_press=self._prev_chapter)
        nav_layout.add_widget(self.prev_btn)

        self.ch_info = Label(text='未開始', size_hint_x=0.6, font_name=str(FONT_TW_SERIF))
        nav_layout.add_widget(self.ch_info)

        self.next_btn = Button(text='下一章 →', size_hint_x=0.2, font_name=str(FONT_TW_SERIF))
        self.next_btn.bind(on_press=self._next_chapter)
        nav_layout.add_widget(self.next_btn)
        
        self.layout.add_widget(top_layout)
        self.layout.add_widget(self.ch_scroll)
        self.layout.add_widget(self.content_scroll)
        self.layout.add_widget(nav_layout)

        self.add_widget(self.layout)

        # track current chapter
        self.current_book = None
        # chapters is a list of dicts: {'title':..., 'filename':...} for offline or {'title':..., 'url':...} for online
        self.chapters = []
        self.current_chapter_idx = -1
        self.ch_list_visible = False

    def _update_content_height(self, instance, value):
        instance.height = instance.texture_size[1]
        # use the full width of the content scroll (so text reaches left and right edges)
        instance.text_size = (self.content_scroll.width, None)

    def _toggle_chapter_list(self, instance):
        """Show/hide chapter list"""
        if self.ch_list_visible:
            self.ch_scroll.size_hint_y = 0
            self.menu_btn.text = '☰ 章節'
            self.ch_list_visible = False
        else:
            self.ch_scroll.size_hint_y = 0.25
            self.menu_btn.text = '✕ 關閉'
            self.ch_list_visible = True

    def load_book(self, book_title: str):
        self.title_label.text = f"{book_title}"
        self.current_book = book_title
        self.current_chapter_idx = -1
        self.ch_list_visible = False
        self.ch_scroll.size_hint_y = 0  # start with hidden
        self._populate_chapters()

    def _populate_chapters(self):
        self.ch_grid.clear_widgets()
        files = novel_service.list_chapters(self.current_book)
        if not files:
            lbl = Label(text='找不到章節', size_hint_y=None, height=40, font_name=str(FONT_TW_SERIF))
            self.ch_grid.add_widget(lbl)
            return
        # convert filenames to chapter dicts
        self.chapters = [{'title': f, 'filename': f} for f in files]
        for idx, ch in enumerate(self.chapters):
            title = ch.get('title')
            btn = Button(text=title, size_hint_y=None, height=36, font_name=str(FONT_TW_SERIF),
                        background_color=(0.2, 0.2, 0.2, 1) if idx == self.current_chapter_idx else (0.4, 0.4, 0.4, 1))
            btn.bind(on_press=lambda inst, i=idx: self._on_chapter_btn_clicked(i))
            self.ch_grid.add_widget(btn)

    def _on_chapter_btn_clicked(self, idx: int):
        self.current_chapter_idx = idx
        self.load_chapter_impl(self.chapters[idx])
        self._refresh_chapter_btns()

    def load_chapter(self, chapter_identifier):
        """This is called from search_screen. chapter_identifier may be index, title, or chapter dict."""
        idx = -1
        if isinstance(chapter_identifier, int):
            idx = chapter_identifier
        elif isinstance(chapter_identifier, dict):
            for i, c in enumerate(self.chapters):
                if c.get('title') == chapter_identifier.get('title'):
                    idx = i
                    break
        else:
            # assume title string
            for i, c in enumerate(self.chapters):
                if c.get('title') == chapter_identifier:
                    idx = i
                    break
        if idx >= 0:
            self.current_chapter_idx = idx
            self.load_chapter_impl(self.chapters[idx])
        else:
            # fallback: try to load by string as before
            self.load_chapter_impl({'title': str(chapter_identifier)})
        self._refresh_chapter_btns()

    def load_chapter_impl(self, chapter):
        """Internal: Load and display chapter content. chapter is a dict with 'filename' or 'url' and 'title'."""
        content = None
        # offline
        if chapter and chapter.get('filename'):
            content = novel_service.read_chapter(self.current_book, chapter.get('filename'))
        # online
        elif chapter and chapter.get('url'):
            try:
                t, content = novel_service.fetch_chapter_online(chapter.get('url'))
            except Exception:
                content = None

        if not content:
            self.content_label.text = '無法讀取章節。'
        else:
            # set text then ensure wrapping uses current ScrollView width
            self.content_label.text = content
            try:
                self.content_label.text_size = (self.content_scroll.width, None)
            except Exception:
                pass
            # schedule height update on next frame to apply texture changes
            Clock.schedule_once(lambda dt: self._update_content_height(self.content_label, self.content_label.texture_size), 0)
            # record last-read
            try:
                if self.current_book and isinstance(chapter, dict):
                    novel_service.set_last_read(self.current_book, chapter.get('title'))
            except Exception:
                pass
        self._update_nav_info()

    def _refresh_chapter_btns(self):
        """Mark current chapter button"""
        self.ch_grid.clear_widgets()
        for idx, ch in enumerate(self.chapters):
            is_current = (idx == self.current_chapter_idx)
            title = ch.get('title') if isinstance(ch, dict) else str(ch)
            btn = Button(text=title, size_hint_y=None, height=36, font_name=str(FONT_TW_SERIF),
                        background_color=(0.1, 0.5, 0.1, 1) if is_current else (0.4, 0.4, 0.4, 1))
            btn.bind(on_press=lambda inst, i=idx: self._on_chapter_btn_clicked(i))
            self.ch_grid.add_widget(btn)

    def _prev_chapter(self, instance):
        """Navigate to previous chapter"""
        if self.current_chapter_idx > 0:
            self.current_chapter_idx -= 1
            ch = self.chapters[self.current_chapter_idx]
            self.load_chapter_impl(ch)
            self._refresh_chapter_btns()

    def _next_chapter(self, instance):
        """Navigate to next chapter"""
        if self.current_chapter_idx < len(self.chapters) - 1:
            self.current_chapter_idx += 1
            ch = self.chapters[self.current_chapter_idx]
            self.load_chapter_impl(ch)
            self._refresh_chapter_btns()

    def _update_nav_info(self):
        """Update navigation info label"""
        if self.current_chapter_idx >= 0 and self.current_chapter_idx < len(self.chapters):
            pos = self.current_chapter_idx + 1
            total = len(self.chapters)
            ch_name = self.chapters[self.current_chapter_idx].get('title') if isinstance(self.chapters[self.current_chapter_idx], dict) else str(self.chapters[self.current_chapter_idx])
            self.ch_info.text = f'{pos}/{total}'
        else:
            self.ch_info.text = '未開始'

    def _back_to_search(self, instance):
        app = App.get_running_app()
        if app and hasattr(app, 'screen_manager'):
            app.screen_manager.current = 'search'
            try:
                search_screen = app.screen_manager.get_screen('search')
                if hasattr(search_screen, 'show_details_for') and self.current_book:
                    # schedule to ensure screen switch finished
                    from kivy.clock import Clock
                    Clock.schedule_once(lambda dt: search_screen.show_details_for(self.current_book), 0.1)
            except Exception:
                pass

    def _back_to_book(self, instance):
        """Switch to BookScreen and populate it using cached details or by fetching index_url."""
        app = App.get_running_app()
        if not (app and hasattr(app, 'screen_manager')):
            return

        search_screen = None
        try:
            search_screen = app.screen_manager.get_screen('search')
        except Exception:
            search_screen = None

        details = None
        index_url = None
        # try cached details in search screen
        if search_screen and getattr(search_screen, 'current_details', None) and search_screen.current_details.get('title') == self.current_book:
            details = search_screen.current_details.get('details')
            index_url = search_screen.current_details.get('index_url')

        # if not, try to search by book title to get index_url
        if not index_url and self.current_book:
            try:
                results = novel_service.search(self.current_book)
                if results:
                    index_url = results[0].get('index_url')
            except Exception:
                index_url = None

        # if we have an index_url but no details, fetch details
        if index_url and not details:
            try:
                details = novel_service.get_book_details(index_url)
            except Exception:
                details = None

        # switch to book screen and populate
        try:
            book_screen = app.screen_manager.get_screen('book')
            book_screen.load_details(self.current_book or '', index_url, details or {})
            app.screen_manager.current = 'book'
        except Exception:
            # fallback: go to search screen
            app.screen_manager.current = 'search'

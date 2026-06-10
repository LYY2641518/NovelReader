from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.app import App

import novel_service
from core.setting import FONT_TW_SERIF
from kivy.clock import Clock


class LibraryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.layout = BoxLayout(orientation='vertical')

        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=48)
        header.add_widget(Label(text='書庫', font_name=str(FONT_TW_SERIF),size_hint_x=0.8))
        back = Button(text='返回搜尋', size_hint_x=0.2, font_name=str(FONT_TW_SERIF))
        back.bind(on_press=lambda inst: self._back_to_search())
        header.add_widget(back)
        self.layout.add_widget(header)

        self.scroll = ScrollView()
        self.grid = GridLayout(cols=1, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)
        self.layout.add_widget(self.scroll)

        self.add_widget(self.layout)

    def on_enter(self):
        # populate downloaded books
        Clock.schedule_once(lambda dt: self._populate())

    def _populate(self):
        self.grid.clear_widgets()
        books = novel_service.list_books()
        if not books:
            self.grid.add_widget(Label(text='尚無已下載書籍', font_name=str(FONT_TW_SERIF), size_hint_y=None, height=40))
            return
        for b in books:
            last = novel_service.get_last_read(b) or '尚未閱讀'
            btn = Button(text=f"{b} — 上次: {last}", size_hint_y=None, height=44, font_name=str(FONT_TW_SERIF))
            btn.bind(on_press=lambda inst, title=b: self._open_book(title))
            self.grid.add_widget(btn)

    def _open_book(self, title: str):
        # open reader at last-read chapter if available
        last = novel_service.get_last_read(title)
        app = App.get_running_app()
        if app and hasattr(app, 'screen_manager'):
            reader = app.screen_manager.get_screen('reader')
            reader.load_book(title)
            if last:
                reader.load_chapter(last)
            else:
                # open book screen to pick chapter
                try:
                    book_screen = app.screen_manager.get_screen('book')
                    # load details from saved index page (index_page.html) if exists
                    # fallback: just show book screen without details
                    book_screen.load_details(title, None, {})
                    app.screen_manager.current = 'book'
                    return
                except Exception:
                    pass
            app.screen_manager.current = 'reader'

    def _back_to_search(self):
        app = App.get_running_app()
        if app and hasattr(app, 'screen_manager'):
            app.screen_manager.current = 'search'

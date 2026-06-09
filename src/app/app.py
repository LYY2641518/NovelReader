from kivy.app import App
from kivy.core.text import LabelBase
from kivy.uix.screenmanager import ScreenManager
from core.setting import FONT_TW_SERIF

from ui.screens.search_screen import SearchScreen
from ui.screens.book_screen import BookScreen
from ui.screens.reader_screen import ReaderScreen
from ui.screens.library_screen import LibraryScreen


class NovelCrawlerApp(App):
    def build(self):
        # 註冊中文字體
        LabelBase.register(name='ChineseFont', fn_regular=str(FONT_TW_SERIF))

        self.screen_manager = ScreenManager()

        self.screen_manager.add_widget(SearchScreen(name='search'))
        self.screen_manager.add_widget(BookScreen(name='book'))
        self.screen_manager.add_widget(LibraryScreen(name='library'))
        self.screen_manager.add_widget(ReaderScreen(name='reader'))

        return self.screen_manager
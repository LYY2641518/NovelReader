from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.core.text import LabelBase
from kivy.uix.screenmanager import ScreenManager
from core.setting import FONT_TW_SERIF
#from ui.screens.search_screen import SearchScreen


def onclick(instance):
    print(f"{instance.text}>按鈕被點擊")
    

# def updatesize(*args):
#     print(f"WindowSize:{Window.size}")
class NovelCrawlerApp(App):
    # def build(self):
    #     screen_manager = ScreenManager()

    #     screen_manager.add_widget(SearchScreen(name="search"))

    #     return screen_manager
    def build(self):
        # 註冊中文字體
        print(type(FONT_TW_SERIF))
        print(FONT_TW_SERIF)
        LabelBase.register(name='ChineseFont', fn_regular=str(FONT_TW_SERIF))
        layout = BoxLayout(orientation="vertical")
        label_debug = Label(text="我是輸出",size_hint=(0.5,0.5),size=(200,80), font_name="ChineseFont")


        layout.add_widget(label_debug)
        btn_test = Button(text="中文測試",size_hint=(0,0),size=(200,80), font_name="ChineseFont")
        btn_test.bind(on_press = onclick)
        layout.add_widget(btn_test)
        layout.add_widget(Button(text="Test B",size_hint=(1,1),size=(200,80), font_name="ChineseFont"))

        return layout
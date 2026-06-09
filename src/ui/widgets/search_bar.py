# src/ui/widgets/search_bar.py

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from core.setting import FONT_TW_SERIF


class SearchBarWidget(BoxLayout):
    """
    SearchBarWidget
    ----------------
    負責：
    - keyword input
    - search button
    - trigger callback (not logic)
    """

    def __init__(self, on_search=None, **kwargs):
        super().__init__(**kwargs)

        # 外部注入 callback（重點設計）
        self.on_search = on_search

        self.orientation = "horizontal"
        self.size_hint_y = 0.1

        self._build_ui()

    def _build_ui(self):
        # 1. 輸入框
        self.input = TextInput(
            hint_text="輸入小說名稱 / 關鍵字",
            multiline=False,
            size_hint_x=0.8,
            font_name=str(FONT_TW_SERIF)
        )

        # 2. 搜尋按鈕
        self.button = Button(
            text="搜尋",
            size_hint_x=0.2
        )
        self.button.font_name = str(FONT_TW_SERIF)

        # bind event
        self.button.bind(on_press=self._on_button_press)

        # Enter 鍵觸發搜尋（提升 UX）
        self.input.bind(on_text_validate=self._on_enter)

        self.add_widget(self.input)
        self.add_widget(self.button)

    # -------------------------
    # Event Handlers
    # -------------------------

    def _on_button_press(self, instance):
        self._trigger_search()

    def _on_enter(self, instance):
        self._trigger_search()

    def _trigger_search(self):
        keyword = self.input.text.strip()

        if not keyword:
            return

        # ★ 關鍵設計：只丟事件，不做邏輯
        if self.on_search:
            self.on_search(keyword)
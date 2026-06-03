from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label

from ui.widgets.search_bar import SearchBarWidget


class SearchScreen(Screen):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = BoxLayout(orientation="vertical")

        self._build_ui()

        self.add_widget(self.layout)

    def _build_ui(self):

        # -----------------------
        # Top Bar
        # -----------------------
        top_bar = Label(
            text="Novel Crawler",
            size_hint_y=0.1
        )

        # -----------------------
        # Search Bar (核心改動)
        # -----------------------
        search_bar = SearchBarWidget(
            on_search=self.on_search
        )

        # -----------------------
        # Result Area (先 placeholder)
        # -----------------------
        self.result_area = Label(
            text="Result Area",
            size_hint_y=0.6
        )

        # -----------------------
        # Log Panel
        # -----------------------
        self.log_panel = Label(
            text="Log Panel",
            size_hint_y=0.2
        )

        self.layout.add_widget(top_bar)
        self.layout.add_widget(search_bar)
        self.layout.add_widget(self.result_area)
        self.layout.add_widget(self.log_panel)

    # ======================================
    # EVENT HANDLER (SearchBar → Screen)
    # ======================================

    def on_search(self, keyword: str):
        """
        UI event entry point
        """

        self._log(f"收到搜尋請求: {keyword}")

        # 👉 模擬 Service Layer
        result = self.mock_service_search(keyword)

        self._update_result(result)

    # ======================================
    # MOCK SERVICE LAYER（之後會抽出去）
    # ======================================

    def mock_service_search(self, keyword: str):
        """
        模擬 crawler 回傳
        """
        return [
            f"{keyword} - Chapter 1",
            f"{keyword} - Chapter 2",
            f"{keyword} - Chapter 3",
        ]

    # ======================================
    # UI UPDATE
    # ======================================

    def _update_result(self, result_list):
        self.result_area.text = "\n".join(result_list)

        self._log(f"搜尋完成，共 {len(result_list)} 筆")

    def _log(self, message: str):
        self.log_panel.text = message
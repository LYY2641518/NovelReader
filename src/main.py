from utils.logger import setup_logger

from app.app import NovelCrawlerApp

if __name__ == "__main__":
    setup_logger()
    NovelCrawlerApp().run()
    
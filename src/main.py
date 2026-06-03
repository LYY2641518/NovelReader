from utils.logger import setup_logger
setup_logger()

from app.app import NovelCrawlerApp

if __name__ == "__main__":
    NovelCrawlerApp().run()
    
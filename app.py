from functions import YahooFinanceNewsScraper


def data_collection_for_news():
    scraper = YahooFinanceNewsScraper()
    news_data = scraper.get_news_data()
    return news_data


if __name__ == "__main__":

    latest_stock_market_news_df = data_collection_for_news()
    print(latest_stock_market_news_df)
    print("test")


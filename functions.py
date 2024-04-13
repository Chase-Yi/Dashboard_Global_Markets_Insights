import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import pandas as pd


########################################################################################################################
# News~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class YahooFinanceNewsScraper:
    def __init__(self):
        self.url = "https://finance.yahoo.com/topic/stock-market-news/"

    @staticmethod
    def scrape_data(url):
        response = requests.get(url)
        html_content = response.content
        soup = BeautifulSoup(html_content, "html.parser")
        articles = soup.find_all("li", class_="js-stream-content")
        data = []
        for article in articles:
            title = article.find("h3").text.strip()
            article_url = article.find("a")["href"]
            full_url = urljoin(url, article_url)
            data.append({"News Title": title, "URL": full_url})
        return data

    def get_news_content(self, data):
        for item in data:
            article_url = item["URL"]
            try:
                article_response = requests.get(article_url)
                article_html_content = article_response.content
                article_soup = BeautifulSoup(article_html_content, "html.parser")
                if article_soup.find("div", class_="caas-body"):
                    full_content = article_soup.find("div", class_="caas-body").text.strip()
                else:
                    full_content = ""
                item["News Content"] = full_content
            except Exception as e:
                print("Error occurred:", e)
                print("Retrying after 5 seconds...")
                time.sleep(5)
                return self.get_news_content(data)
        return data

    def get_news_data(self):
        df_cleaned = pd.DataFrame()
        while df_cleaned.empty:
            data = self.scrape_data(self.url)
            data_with_content = self.get_news_content(data)
            df = pd.DataFrame(data_with_content)
            df_cleaned = df[df['News Content'] != ''].copy()
            df_cleaned.drop_duplicates(inplace=True)
            df_cleaned.reset_index(drop=True, inplace=True)
        return df_cleaned

########################################################################################################################
# Macroeconomic indicators~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class WorldBankData:
    print("WorldBankData")

########################################################################################################################
# Financial markets~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class YahooFinanceData:
    print("YahooFinanceData")

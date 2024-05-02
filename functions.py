import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timedelta
import yfinance as yf
from yahooquery import Ticker
import pandas as pd

########################################################################################################################
# News~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class YahooFinanceNewsScraper:
    def __init__(self):
        self.url1 = "https://finance.yahoo.com/topic/latest-news/"
        self.url2 = "https://finance.yahoo.com/topic/stock-market-news/"

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
            data1 = self.scrape_data(self.url1)
            data_with_content1 = pd.DataFrame(self.get_news_content(data1))
            data2 = self.scrape_data(self.url2)
            data_with_content2 = pd.DataFrame(self.get_news_content(data2))
            data_with_content = pd.concat([data_with_content1,data_with_content2],axis='rows')
            df = data_with_content.copy()
            df_cleaned = df[df['News Content'] != ''].copy()
            df_cleaned.drop_duplicates(inplace=True)
            df_cleaned.reset_index(drop=True, inplace=True)
        return df_cleaned

########################################################################################################################
# Financial markets~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
class YahooFinanceData:
    def __init__(self, index_info, etf_info):
        self.index_info_df = pd.DataFrame(index_info)
        self.etf_info_df = pd.DataFrame(etf_info)
        self.end_date = datetime.now().strftime('%Y-%m-%d')
        self.start_date = datetime.strptime(self.end_date, '%Y-%m-%d') - timedelta(days=365 * 10)
        self.start_date = self.start_date.strftime('%Y-%m-%d')

    def _get_hist_data(self, tickers):
        yf_tickers = yf.Tickers(tickers)
        hist_data = yf_tickers.history(start=self.start_date, end=self.end_date, period='max')
        hist_data = hist_data.stack(level=1).rename_axis(['Date', 'Ticker']).reset_index(level=1)
        hist_data = hist_data.reset_index()
        hist_data = hist_data.sort_values(by=['Ticker', 'Date'])
        hist_data['Date'] = hist_data['Date'].dt.strftime('%Y-%m-%d')
        return hist_data

    def get_index_hist(self):
        index_tickers = self.index_info_df['index_symbol'].tolist()
        index_hist = self._get_hist_data(index_tickers)
        index_hist = pd.merge(index_hist, self.index_info_df.rename(columns={'index_symbol': 'Ticker', 'index_name': 'Name'}), on='Ticker', how='left')
        index_hist = index_hist[['Date', 'Ticker', 'Name', 'Close', 'Volume']]
        return index_hist

    def get_etf_hist(self):
        etf_tickers = self.etf_info_df['etf_symbol'].tolist()
        etf_hist = self._get_hist_data(etf_tickers)
        etf_hist = pd.merge(etf_hist, self.etf_info_df.rename(columns={'etf_symbol': 'Ticker', 'etf_name': 'Name'}), on='Ticker', how='left')
        etf_hist = etf_hist[['Date', 'Ticker', 'Name', 'Close', 'Volume']]
        return etf_hist

    def get_index_etf_info(self):
        return pd.concat([self.index_info_df, self.etf_info_df], axis='columns')

    def get_etf_sector_weightings(self):
        etf_ticker_list = self.etf_info_df['etf_symbol'].unique().tolist()
        etfs = Ticker(etf_ticker_list)
        etfs_sector_weightings = etfs.fund_sector_weightings.T
        etfs_sector_weightings = etfs_sector_weightings.reset_index()
        etfs_sector_weightings.rename(columns={'index': 'etf_symbol'}, inplace=True)
        etfs_sector_weightings = pd.merge(etfs_sector_weightings, self.etf_info_df, on='etf_symbol', how='left')
        etfs_sector_weightings = etfs_sector_weightings[['etf_symbol', 'etf_name', 'realestate', 'consumer_cyclical',
                                                         'basic_materials', 'consumer_defensive', 'technology',
                                                         'communication_services', 'financial_services', 'utilities',
                                                         'industrials', 'energy', 'healthcare']]
        return etfs_sector_weightings

    def get_etf_top_holdings(self):
        etf_ticker_list = self.etf_info_df['etf_symbol'].unique().tolist()
        etfs_top_holdings = []
        for each_etf_ticker in etf_ticker_list:
            each_etf = Ticker(each_etf_ticker)
            each_etf_top_holdings = each_etf.fund_top_holdings
            etfs_top_holdings.append(each_etf_top_holdings)
        etfs_top_holdings_df = pd.concat(etfs_top_holdings, axis='index')
        etfs_top_holdings_df.index.names = ['etf_symbol', 'holdingRanking']
        etfs_top_holdings_df.rename(columns={'symbol': 'holdingSymbol'}, inplace=True)
        etfs_top_holdings_df = etfs_top_holdings_df.reset_index()
        etfs_top_holdings_df['holdingRanking'] = etfs_top_holdings_df['holdingRanking'] + 1
        etfs_top_holdings_df = pd.merge(etfs_top_holdings_df, self.etf_info_df, on='etf_symbol', how='left')
        etfs_top_holdings_df = etfs_top_holdings_df[['etf_symbol', 'etf_name', 'holdingRanking', 'holdingSymbol', 'holdingName', 'holdingPercent']]
        stock_ticker_name = etfs_top_holdings_df[['holdingSymbol', 'holdingName']]
        stock_ticker_name.columns = ['stock_ticker', 'stock_name']
        stock_ticker_name = stock_ticker_name.drop_duplicates(subset='stock_ticker', keep='first')
        return etfs_top_holdings_df,stock_ticker_name

    def get_stock_hist(self,stock_ticker_name):
        stock_ticker_list = stock_ticker_name['stock_ticker'].unique().tolist()
        stocks = yf.Tickers(stock_ticker_list)
        stocks_hist = stocks.history(start=self.start_date, end=self.end_date, period='max')
        stocks_hist = stocks_hist.stack(level=1).rename_axis(['Date', 'Ticker']).reset_index(level=1)
        stocks_hist = stocks_hist.reset_index()
        stocks_hist = stocks_hist.sort_values(by=['Ticker', 'Date'])
        stocks_hist['Date'] = stocks_hist['Date'].dt.strftime('%Y-%m-%d')
        stocks_hist = stocks_hist[['Date', 'Ticker', 'Close', 'Volume']]
        stocks_hist = pd.merge(stocks_hist, stock_ticker_name.rename(columns={'stock_ticker': 'Ticker', 'stock_name': 'Name'}), on='Ticker', how='left')
        stocks_hist = stocks_hist[['Date', 'Ticker', 'Name', 'Close', 'Volume']]
        return stocks_hist

    def get_stock_recommendation_trend(self,stock_ticker_name):
        stock_ticker_list = stock_ticker_name['stock_ticker'].unique().tolist()
        recommendation_trend_list = []
        for each_stock_ticker in stock_ticker_list:
            each_stock = Ticker(each_stock_ticker)
            recommendation_trend = each_stock.recommendation_trend
            if not recommendation_trend.empty:
                recommendation_trend.index.names = ['stock_ticker', 'row']
                recommendation_trend = recommendation_trend.reset_index().drop(columns='row')
                recommendation_trend_list.append(recommendation_trend)
        stock_recommendation_trend_df = pd.concat(recommendation_trend_list, axis='index').reset_index(drop=True)
        return stock_recommendation_trend_df


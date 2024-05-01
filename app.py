import time
from functions import YahooFinanceNewsScraper
from functions import YahooFinanceData

if __name__ == "__main__":
    def get_data_with_retry():
        max_retries = 3
        retries = 0
        while retries < max_retries:
            try:
                latest_stock_market_news_df = YahooFinanceNewsScraper().get_news_data()

                index_info = {'index_name': ['CSI 300 Index',
                                             'S&P 500',
                                             'CAC 40',
                                             'FTSE 100',
                                             'Dow Jones Industrial Average',
                                             'NASDAQ 100',
                                             'Russell 2000',
                                             'HANG SENG INDEX',
                                             'Nikkei 225',
                                             'TSEC weighted index',
                                             'S&P BSE SENSEX',
                                             'DAX PERFORMANCE-INDEX',
                                             'ESTX 50 PR.EUR'],
                              'index_symbol': ['000300.SS',
                                               '^GSPC',
                                               '^FCHI',
                                               '^FTSE',
                                               '^DJI',
                                               '^NDX',
                                               '^RUT',
                                               '^HSI',
                                               '^N225',
                                               '^TWII',
                                               '^BSESN',
                                               '^GDAXI',
                                               '^STOXX50E']}

                etf_info = {'etf_name': ['Xtrackers Harvest CSI 300 China A-Shares ETF',
                                         'Vanguard S&P 500 ETF',
                                         'Amundi CAC 40 UCITS ETF Dist',
                                         'BetaShares FTSE 100 ETF',
                                         'SPDR Dow Jones Industrial Average ETF Trust',
                                         'Invesco EQQQ NASDAQ-100 UCITS ETF',
                                         'iShares Russell 2000 ETF',
                                         'iShares MSCI Hong Kong ETF',
                                         'iShares Core Nikkei 225 ETF',
                                         'iShares MSCI Taiwan ETF',
                                         'iShares Core S&P BSE SENSEX India ETF',
                                         'Xtrackers DAX UCITS ETF 1C',
                                         'Xtrackers Euro Stoxx 50 UCITS ETF 1C'],
                            'etf_symbol': ['ASHR',
                                           'VOO',
                                           'CACX.L',
                                           'F100.AX',
                                           'DIA',
                                           'EQQQ.L',
                                           'IWM',
                                           'EWH',
                                           '1329.T',
                                           'EWT',
                                           '9836.HK',
                                           'DBXD.DE',
                                           'XESC.DE']}

                yahoo_data = YahooFinanceData(index_info, etf_info)

                index_hist = yahoo_data.get_index_hist()
                etf_hist = yahoo_data.get_etf_hist()
                index_etf_info = yahoo_data.get_index_etf_info()
                etf_sector_weightings = yahoo_data.get_etf_sector_weightings()
                etf_top_holdings, stock_ticker_name = yahoo_data.get_etf_top_holdings()
                stock_hist = yahoo_data.get_stock_hist(stock_ticker_name)

                return latest_stock_market_news_df,index_hist,etf_hist,index_etf_info,etf_sector_weightings,etf_top_holdings,stock_ticker_name,stock_hist

                break

            except Exception as e:
                print(f"Error occurred: {e}")
                print("Retrying after 5 seconds...")
                time.sleep(5)
                retries += 1

        else:
            print("Failed to retrieve data after max retries.")

    latest_stock_market_news_df,index_hist,etf_hist,index_etf_info,etf_sector_weightings,etf_top_holdings,stock_ticker_name,stock_hist = get_data_with_retry()

    print("test")




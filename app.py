import time
from functions import YahooFinanceNewsScraper
from functions import YahooFinanceData

import pandas as pd
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template
import plotly.express as px
import plotly.io as pio
pio.renderers.default = "browser"

########################################################################################################################
def get_data_with_retry():
    max_retries = 3
    retries = 0
    while retries < max_retries:
        try:
            latest_stock_market_news_df = YahooFinanceNewsScraper().get_news_data()

            index_info = {
            'index_name': ['CSI 300 Index',
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

            etf_info = {'etf_name': [
            'Xtrackers Harvest CSI 300 China A-Shares ETF',
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

            'etf_symbol': [
            'ASHR',
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
            stock_recommendation_trend_df = yahoo_data.get_stock_recommendation_trend(stock_ticker_name)

            return latest_stock_market_news_df,index_hist,etf_hist,index_etf_info,etf_sector_weightings,etf_top_holdings,stock_ticker_name,stock_hist,stock_recommendation_trend_df

            break

        except Exception as e:
            print(f"Error occurred: {e}")
            print("Retrying after 5 seconds...")
            time.sleep(5)
            retries += 1

    else:
        print("Failed to retrieve data after max retries.")

(latest_stock_market_news_df,index_hist,etf_hist,index_etf_info,etf_sector_weightings,etf_top_holdings,
 stock_ticker_name,stock_hist,stock_recommendation_trend_df) = get_data_with_retry()

########################################################################################################################
def nav_df(hist_df):
    close_df = hist_df[['Date','Name','Close']]
    pivot_df = close_df.pivot_table(index='Date', columns='Name', values='Close')
    pivot_df_new = pivot_df.ffill()
    ret_df = pivot_df_new.pct_change()
    nav_df = (ret_df.fillna(0)+1).cumprod()
    return nav_df

index_nav = nav_df(index_hist)
etf_nav = nav_df(etf_hist)

def nav_df_filter(nav_df,x):
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    today = datetime.today()

    if x == '1M': target_date = today - relativedelta(months=1)
    if x == '3M': target_date = today - relativedelta(months=3)
    if x == '6M': target_date = today - relativedelta(months=6)
    if x == 'YTD': target_date = datetime(today.year, 1, 1)
    if x == '1Y': target_date = today - relativedelta(years=1)
    if x == '3Y': target_date = today - relativedelta(years=3)
    if x == '5Y': target_date = today - relativedelta(years=5)
    if x == '10Y': target_date = today - relativedelta(years=10)

    target_date = target_date.strftime('%Y-%m-%d')

    dates = nav_df.index.to_frame().reset_index(drop=True)
    dates_list = dates['Date'].unique().tolist()

    def find_nearest_trading_day(target_date_str, dates_list):
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
        min_diff = None
        nearest_date = None
        for date_str in dates_list:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            diff = abs((date - target_date).days)
            if min_diff is None or diff < min_diff:
                min_diff = diff
                nearest_date = date_str
        return nearest_date

    nearest_trading_day = find_nearest_trading_day(target_date, dates_list)
    nav_filtered = nav_df.loc[nearest_trading_day:,:]
    nav_filtered = nav_filtered / nav_filtered.iloc[0,:]
    return nav_filtered

########################################################################################################################
print("test")

if __name__ == "__main__":

    load_figure_template("darkly")

    app = Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

    app.layout = html.Div([
        html.Label(['ETF & Index - Cumulative Returns Comparison'],style={'font-weight': 'bold', 'color': 'white'}),
        html.Hr(style={'border-top': '1px solid white'}),

        dbc.RadioItems(id='Index-ETF', options=[{'label': 'Stock Market Index', 'value': 'Stock Market Index'},
                                                {'label': 'ETF', 'value': 'ETF'}],
            value='Stock Market Index', inline=True,
            labelStyle={"margin": "1rem"}, labelCheckedStyle={'color':'crimson'},
            style={'background-color': '#2c2c2c', 'border': '1px solid #2c2c2c', 'color': 'white',
            'box-shadow': '2px 2px 4px #888', 'font-size': '16px'}),

        dbc.RadioItems(id='Time-Choice', options=[
            {'label': '1M',  'value': '1M'},
            {'label': '3M',  'value': '3M'},
            {'label': '6M',  'value': '6M'},
            {'label': 'YTD', 'value': 'YTD'},
            {'label': '1Y',  'value': '1Y'},
            {'label': '3Y',  'value': '3Y'},
            {'label': '5Y',  'value': '5Y'},
            {'label': '10Y', 'value': '10Y'}],
            value='10Y', inline=True,
            labelStyle={"margin": "1rem"}, labelCheckedStyle={'color':'crimson'},
            style={'background-color': '#2c2c2c', 'border': '1px solid #2c2c2c', 'color': 'white',
            'box-shadow': '2px 2px 4px #888', 'font-size': '14px'}),

        html.Div([
            html.Div(dcc.Graph(id='Graph1'), style={'width': '100%', 'display': 'flex', "justifyContent": "center"}),
            html.Div(dcc.Graph(id='Graph2'), style={'width': '100%', 'display': 'flex', "justifyContent": "center"})
        ])
    ])

    @app.callback([Output('Graph1', 'figure'),
    Output('Graph2', 'figure')],
    [Input('Index-ETF', 'value'),
    Input('Time-Choice', 'value')])
    def update_line_chart(choice1, choice2):
        time_choice = choice2

        if choice1 == 'Stock Market Index':
            nav_filtered = nav_df_filter(index_nav, time_choice)
        else:
            nav_filtered = nav_df_filter(etf_nav, time_choice)

        fig1 = px.line(
            nav_filtered.reset_index(),
            x='Date',
            y=nav_filtered.columns.tolist(),
            color_discrete_map={name: color for name, color in zip(nav_filtered.columns, px.colors.qualitative.Light24)},
            template='plotly_dark',
            title= f'{choice1}: {choice2} - Cumulative Returns Comparison',height=800,width=1650)
        fig1.update_layout(hovermode="x", hoverlabel=dict(font_color='black', font_size=12.5, bordercolor='white'))

        fig2 = px.area(
            nav_filtered,
            facet_col='Name',
            facet_col_wrap=7,
            color_discrete_map={name: color for name, color in zip(nav_filtered.columns, px.colors.qualitative.Light24)},
            template='plotly_dark',height=800,width=1650)
        fig2.update_layout(font_size=7)

        return fig1, fig2

    app.run_server()
    print("app_test")

'''

'''

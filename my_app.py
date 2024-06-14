from functions import YahooFinanceNewsScraper
from functions import YahooFinanceData

import pandas as pd
import numpy as np

from dash import Dash, dcc, html, Input, Output, dash_table
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template

import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
pio.renderers.default = "browser"

########################################################################################################################
def get_data():

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
    'ESTX 50 PR EUR'],

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
    index_list = index_hist['Ticker'].unique().tolist()
    etf_hist = yahoo_data.get_etf_hist()
    etf_list = etf_hist['Ticker'].unique().tolist()

    while len(index_list)!=13 or len(etf_list)!=13:
        index_hist = yahoo_data.get_index_hist()
        index_list = index_hist['Ticker'].unique().tolist()
        etf_hist = yahoo_data.get_etf_hist()
        etf_list = etf_hist['Ticker'].unique().tolist()

    index_etf_info = yahoo_data.get_index_etf_info()
    etf_sector_weightings = yahoo_data.get_etf_sector_weightings()
    etf_top_holdings, stock_ticker_name = yahoo_data.get_etf_top_holdings()
    stock_hist = yahoo_data.get_stock_hist(stock_ticker_name)
    stock_recommendation_trend_df = yahoo_data.get_stock_recommendation_trend(stock_ticker_name)

    return (latest_stock_market_news_df,index_hist,etf_hist,index_etf_info,
            etf_sector_weightings,etf_top_holdings,stock_ticker_name,stock_hist,stock_recommendation_trend_df)

(latest_stock_market_news_df,index_hist,etf_hist,index_etf_info,etf_sector_weightings,etf_top_holdings,
stock_ticker_name,stock_hist,stock_recommendation_trend_df) = get_data()

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
    target_date = None

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
index_hist2 = index_hist.copy()
index_hist2['Type'] = 'Stock Market Index'
etf_hist2 = etf_hist.copy()
etf_hist2['Type'] = 'ETF'

index_close_hist_pivot =  index_hist2.pivot_table(index='Date',columns='Name',values='Close')
index_return_hist_pivot = index_close_hist_pivot.pct_change(fill_method=None)
etf_close_hist_pivot = etf_hist2.pivot_table(index='Date',columns='Name',values='Close')
etf_return_hist_pivot = etf_close_hist_pivot.pct_change(fill_method=None)
close_volume_hist2 = pd.concat([index_hist2,etf_hist2],axis='index')

close_volume_hist = pd.concat([index_hist,etf_hist],axis='index')
close_volume_hist = close_volume_hist.round({'Close': 2})
close_volume_hist_with_ticker = close_volume_hist.copy()
close_volume_hist = close_volume_hist.drop(columns='Ticker')
close_hist_pivot = close_volume_hist.pivot_table(index='Date',columns='Name',values='Close')

def one_close_volume_hist(close_volume_hist,name):
    one_close_volume_hist_df = close_volume_hist.query(f"Name == '{name}' ")
    one_close_volume_hist_df = one_close_volume_hist_df[['Date','Close','Volume']].copy()
    one_close_volume_hist_df = one_close_volume_hist_df.set_index('Date')
    one_close_volume_hist_df.rename(columns={'Close':name+'_Close','Volume':name+'_Volume'},inplace=True)
    return one_close_volume_hist_df

index_names = index_etf_info[['index_name']].copy()
index_name = index_names.rename(columns={'index_name':'Name'})
etf_names = index_etf_info[['etf_name']].copy()
etf_name = etf_names.rename(columns={'etf_name':'Name'})
index_etf_names = pd.concat([index_name,etf_name],axis='index')

index_ticker_name = index_etf_info[['index_symbol','index_name']].copy()
index_ticker_name = index_ticker_name.rename(columns={'index_symbol':'Ticker','index_name':'Name'})
etf_ticker_name = index_etf_info[['etf_symbol','etf_name']].copy()
etf_ticker_name = etf_ticker_name.rename(columns={'etf_symbol':'Ticker','etf_name':'Name'})
index_etf_ticker_name = pd.concat([index_ticker_name,etf_ticker_name],axis='index')
index_etf_ticker_name = index_etf_ticker_name.reset_index(drop=True)

ticker_hyperlink = pd.DataFrame(index=index_etf_ticker_name['Ticker'].tolist())
for each_ticker in ticker_hyperlink.index.tolist():
    if '^' in each_ticker:
        ticker_hyperlink.loc[each_ticker,'URL'] = 'https://finance.yahoo.com/quote/%5E'+each_ticker[1:]
    else:
        ticker_hyperlink.loc[each_ticker,'URL'] = f'https://finance.yahoo.com/quote/{each_ticker}'
ticker_hyperlink = ticker_hyperlink.reset_index()
ticker_hyperlink = ticker_hyperlink.rename(columns={'index':'Ticker'})
index_etf_ticker_name = pd.merge(index_etf_ticker_name,ticker_hyperlink,how='left',on='Ticker')
index_etf_ticker_name['Ticker_URL'] = '['+index_etf_ticker_name['Ticker']+']'+'('+index_etf_ticker_name['URL']+')'
index_etf_ticker_name = index_etf_ticker_name[['Ticker_URL','Name']]
index_etf_ticker_name = index_etf_ticker_name.rename(columns={'Ticker_URL':'Ticker'})

index_etf_pair = []
for i in range(len(index_etf_info)):
    index_etf_pair.append(index_etf_info.loc[i,'etf_name'] + ' {VS} ' + index_etf_info.loc[i,'index_name'])

########################################################################################################################
stock_recommendation_trend_df_1m = stock_recommendation_trend_df.query("period=='-1m'")
stock_recommendation_trend_df_1m = pd.merge(stock_recommendation_trend_df_1m,stock_ticker_name,
                                how='left',on='stock_ticker')
stock_recommendation_trend_df_1m = stock_recommendation_trend_df_1m[['stock_ticker', 'stock_name', 'period',
                                'strongBuy', 'buy', 'hold', 'sell', 'strongSell']]

stock_recommendation_trend_df_1m_url = stock_recommendation_trend_df_1m.set_index('stock_ticker').copy()
for each_stock_ticker in stock_recommendation_trend_df_1m['stock_ticker'].unique().tolist():
    each_stock_url = f'https://finance.yahoo.com/quote/{each_stock_ticker}'
    each_stock_ticker_url = '['+each_stock_ticker+']'+'('+each_stock_url+')'
    stock_recommendation_trend_df_1m_url.loc[each_stock_ticker,'stock_ticker_url'] = each_stock_ticker_url
stock_recommendation_trend_df_1m_url = stock_recommendation_trend_df_1m_url.reset_index(drop=True)
stock_recommendation_trend_df_1m_url = stock_recommendation_trend_df_1m_url[['stock_ticker_url', 'stock_name',
                                'period', 'strongBuy', 'buy', 'hold', 'sell', 'strongSell']].copy()
stock_recommendation_trend_df_1m_url = stock_recommendation_trend_df_1m_url.rename(columns=
                                {'stock_ticker_url':'stock_ticker'})

########################################################################################################################
load_figure_template("darkly")

external_stylesheets = [dbc.themes.DARKLY, dbc.icons.BOOTSTRAP,
                        "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.2/dbc.min.css"]
app = Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

items = []
for each_name in index_etf_names['Name'].unique().tolist():
    items.append(each_name)

double_items = []
for num in range(len(index_etf_info)):
    each_index = index_etf_info.loc[num, 'index_name']
    each_etf = index_etf_info.loc[num, 'etf_name']
    double_items.append(each_index + '  {VS}  ' + each_etf)

min_date = close_hist_pivot.index[1]
max_date = close_hist_pivot.index[-2]

min_date_etf = etf_return_hist_pivot.index[1]
max_date_etf = etf_return_hist_pivot.index[-2]

news = []
for each_news_title in latest_stock_market_news_df['News Title'].unique().tolist():
    news.append(each_news_title)

app.layout = html.Div([

    html.Div([
        html.A('ETF & Index - %Change',
                href='#ETF & Index - %Change', className='sidebar-link',
                style={'display': 'block', 'border': 'solid 1px #fff', 'padding': '10px', 'color': 'white'}),
        html.Br(),
        html.A('ETF & Index - Closing Price & Trading Volume',
                href='#ETF & Index - Closing Price & Trading Volume', className='sidebar-link',
                style={'display': 'block', 'border': 'solid 1px #fff', 'padding': '10px', 'color': 'white'}),
        html.Br(),
        html.A('ETF & Index - Data Tables',
                href='#ETF & Index - Data Tables', className='sidebar-link',
                style={'display': 'block', 'border': 'solid 1px #fff', 'padding': '10px', 'color': 'white'}),
        html.Br(),
        html.A('ETF & Index - NAV Comparison - Starting from 1',
                href='#ETF & Index - NAV Comparison - Starting from 1', className='sidebar-link',
                style={'display': 'block', 'border': 'solid 1px #fff', 'padding': '10px', 'color': 'white'}),
        html.Br(),
        html.A('ETF & Index - Daily Cumulative Returns & Indicators',
                href='#ETF & Index - Daily Cumulative Returns & Indicators', className='sidebar-link',
                style={'display': 'block', 'border': 'solid 1px #fff', 'padding': '10px', 'color': 'white'}),
        html.Br(),
        html.A('ETF & Index - Correlation',
                href='#ETF & Index - Correlation', className='sidebar-link',
                style={'display': 'block', 'border': 'solid 1px #fff', 'padding': '10px', 'color': 'white'}),
        html.Br(),
        html.A('ETF - Top Holdings & Sector Weightings',
                href='#ETF - Top Holdings & Sector Weightings', className='sidebar-link',
                style={'display': 'block', 'border': 'solid 1px #fff', 'padding': '10px', 'color': 'white'}),
        html.Br(),
        html.A('News', href='#News', className='sidebar-link',
                style={'display': 'block', 'border': 'solid 1px #fff', 'padding': '10px', 'color': 'white'}),

    ], className='sidebar', style={'position': 'fixed',
                                'top': 0, 'right': 0, 'width': '400px',
                                'background-color': '#1e1e1e', 'color': '#fff', 'padding': '20px'}),

    html.Div([
        html.Label(['ETF & Index - %Change'],
                id='ETF & Index - %Change',
                style={'font-weight': 'bold', 'color': 'white', 'border': '1px white solid', 'font-size': '20px'}),
        html.Br(),
        html.Br(),
        dcc.DatePickerSingle(id='date-picker',
                            min_date_allowed=min_date, max_date_allowed=max_date,
                            date=max_date, display_format='YY-MM-DD'),
        html.Div([
            html.Div(dcc.Graph(id='Graph_first'),
                    style={'width': '100%', 'display': 'flex', "justifyContent": "center"})
        ]),

        html.Br(),
        html.Label(['ETF & Index - Closing Price & Trading Volume'],
                id='ETF & Index - Closing Price & Trading Volume',
                style={'font-weight': 'bold', 'color': 'white', 'border': '1px white solid', 'font-size': '20px'}),
        dcc.Dropdown(id='Index-ETF-Close-Volume', options=items, placeholder="Select an ETF or Index",
                    className='dbc', value='NASDAQ 100'),
        html.Div([
            html.Div(dcc.Graph(id='Graph0'), style={'width': '100%', 'display': 'flex',
                                                    "justifyContent": "center"}),
            html.Div(dcc.Graph(id='Graph00'), style={'width': '100%', 'display': 'flex',
                                                    "justifyContent": "center"})
        ]),

        html.Br(),
        html.Label(['ETF & Index - Data Tables'],
                id='ETF & Index - Data Tables',
                style={'font-weight': 'bold', 'color': 'white', 'border': '1px white solid', 'font-size': '20px'}),
        dash_table.DataTable(data=index_etf_ticker_name.to_dict('records'),
                            columns=[{'id': c, 'name': c,
                                    'presentation': 'markdown', 'selectable': True} for c in
                                    index_etf_ticker_name.columns],
                            css=[dict(selector="p", rule="margin: 0; text-align: center")],
                            style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
                            style_data={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white'},
                            style_table={'overflowX': 'auto', 'margin': 'auto', 'width': '50%'},
                            style_cell={'textAlign': 'center'},
                            cell_selectable=False),
        html.Br(),
        dash_table.DataTable(data=close_volume_hist_with_ticker.to_dict('records'),
                            columns=[{'id': c, 'name': c, "selectable": True} for c in
                                    close_volume_hist_with_ticker.columns],
                            filter_action="native",
                            sort_action="native",
                            sort_mode='multi',
                            style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
                            style_data={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white'},
                            style_filter={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
                            style_table={'overflowX': 'auto', 'margin': 'auto', 'width': '50%'},
                            style_cell={'textAlign': 'center'},
                            page_current=0,
                            page_size=25,
                            cell_selectable=False),

        html.Br(),
        html.Label(['ETF & Index - NAV Comparison - Starting from 1'],
                id='ETF & Index - NAV Comparison - Starting from 1',
                style={'font-weight': 'bold', 'color': 'white', 'border': '1px white solid', 'font-size': '20px'}),
        dbc.RadioItems(id='Index-ETF-NAV', options=[
            {'label': 'Stock Market Index', 'value': 'Stock Market Index'},
            {'label': 'ETF', 'value': 'ETF'}],
                    value='Stock Market Index', inline=True,
                    labelStyle={"margin": "1rem"}, labelCheckedStyle={'color': 'crimson'},
                    style={'background-color': '#2c2c2c', 'border': '1px solid #2c2c2c', 'color': 'white',
                            'box-shadow': '2px 2px 4px #888', 'font-size': '16px'}),
        dbc.RadioItems(id='Time-Choice', options=[
            {'label': '1M', 'value': '1M'},
            {'label': '3M', 'value': '3M'},
            {'label': '6M', 'value': '6M'},
            {'label': 'YTD', 'value': 'YTD'},
            {'label': '1Y', 'value': '1Y'},
            {'label': '3Y', 'value': '3Y'},
            {'label': '5Y', 'value': '5Y'},
            {'label': '10Y', 'value': '10Y'}],
                    value='10Y', inline=True,
                    labelStyle={"margin": "1rem"}, labelCheckedStyle={'color': 'crimson'},
                    style={'background-color': '#2c2c2c', 'border': '1px solid #2c2c2c', 'color': 'white',
                            'box-shadow': '2px 2px 4px #888', 'font-size': '14px'}),
        html.Div([
            html.Div(dcc.Graph(id='Graph1'), style={'width': '100%', 'display': 'flex',
                                                    "justifyContent": "center"}),
            html.Div(dcc.Graph(id='Graph2'), style={'width': '100%', 'display': 'flex',
                                                    "justifyContent": "center"})
        ]),

        html.Br(),
        html.Label(['ETF & Index - Daily Cumulative Returns & Indicators'],
                id='ETF & Index - Daily Cumulative Returns & Indicators',
                style={'font-weight': 'bold', 'color': 'white', 'border': '1px white solid', 'font-size': '20px'}),
        dcc.Dropdown(id='ETF-Index-Pair', options=index_etf_pair, placeholder='Select an ETF and a Benchmark',
                    className='dbc', value='Invesco EQQQ NASDAQ-100 UCITS ETF {VS} NASDAQ 100'),
        html.Br(),
        html.Div([
            html.Div(dcc.Graph(id='DCR'), style={'width': '100%', 'display': 'flex',
                                                "justifyContent": "center"}),
            html.Br(),
            html.Div(dash_table.DataTable(id='update_table',
                                        css=[dict(selector="p", rule="margin: 0; text-align: center")],
                                        style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
                                        style_data={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white'},
                                        style_table={'overflowX': 'auto', 'margin': 'auto', 'width': '50%'},
                                        style_cell={'textAlign': 'center'},
                                        cell_selectable=False)),
            html.Br(),
        ]),

        html.Br(),
        html.Label(['ETF & Index - Correlation'],
                id='ETF & Index - Correlation',
                style={'font-weight': 'bold', 'color': 'white', 'border': '1px white solid', 'font-size': '20px'}),
        dbc.RadioItems(id='Index-ETF-Correlation', options=[
            {'label': 'Stock Market Index', 'value': 'Stock Market Index'},
            {'label': 'ETF', 'value': 'ETF'},
        ], value='Stock Market Index', inline=True,
                    labelStyle={"margin": "1rem"}, labelCheckedStyle={'color': 'crimson'},
                    style={'background-color': '#2c2c2c', 'border': '1px solid #2c2c2c', 'color': 'white',
                            'box-shadow': '2px 2px 4px #888', 'font-size': '14px'}),
        html.Div([
            html.Div(dcc.Graph(id='Graph3'), style={'width': '100%', 'display': 'flex', "justifyContent": "center"})
        ]),

        html.Br(),
        html.Label(['ETF - Top Holdings & Sector Weightings'],
                id='ETF - Top Holdings & Sector Weightings',
                style={'font-weight': 'bold', 'color': 'white', 'border': '1px white solid', 'font-size': '20px'}),
        dcc.Dropdown(id='ETF-Detail', options=etf_names['etf_name'].tolist(), placeholder="Select an ETF",
                    className='dbc', value='Invesco EQQQ NASDAQ-100 UCITS ETF'),
        html.Br(),
        html.Br(),
        dcc.DatePickerSingle(id='etf-date-picker',
                        min_date_allowed=min_date_etf, max_date_allowed=max_date_etf,
                        date=max_date_etf, display_format='YY-MM-DD'),
        html.Div([
            html.Div(dcc.Graph(id='Graph4'), style={'width': '100%', 'display': 'flex', "justifyContent": "center"}),
            html.Br(),
            html.Div(dash_table.DataTable(id='stock_recommendation',
                                        columns=[{'id': c, 'name': c, 'presentation': 'markdown', 'selectable': True}
                                                for c in stock_recommendation_trend_df_1m_url.columns],
                                        css=[dict(selector="p", rule="margin: 0; text-align: center")],
                                        style_header={'backgroundColor': 'rgb(30, 30, 30)', 'color': 'white'},
                                        style_data={'backgroundColor': 'rgb(50, 50, 50)', 'color': 'white'},
                                        style_table={'overflowX': 'auto', 'margin': 'auto', 'width': '50%'},
                                        style_cell={'textAlign': 'center'},
                                        cell_selectable=False)),
            html.Br(),
            html.Div(dcc.Graph(id='Graph5'), style={'width': '100%', 'display': 'flex', "justifyContent": "center"}),
            html.Div(dcc.Graph(id='Graph6'), style={'width': '100%', 'display': 'flex', "justifyContent": "center"})
        ]),

        html.Br(),
        html.Label(['News'], id='News',
                style={'font-weight': 'bold', 'color': 'white', 'border': '1px white solid', 'font-size': '20px'}),
        dcc.Dropdown(
            id='dropdown',
            options=[{'label': title, 'value': title} for title in latest_stock_market_news_df['News Title']],
            placeholder="Choose Your News",
            className='dbc',
            value=latest_stock_market_news_df['News Title'].iloc[0]),
        html.Br(),
        html.Div(dbc.Card([dbc.CardHeader(id="card-header"),
                        dbc.CardBody([
                            html.P(id="card-text", className="card-text"),
                            dcc.Markdown(id="dynamic-link", link_target='_blank')])],
                        style={"width": "100rem"}, color="dark", inverse=True),
                style={'width': '100%', 'display': 'flex', "justifyContent": "center"})

    ], className='content', style={'margin-right': '100px'})

], style={'width': '80%', 'height': '80%'})


@app.callback(Output('Graph_first', 'figure'),
            Input('date-picker', 'date'))
def Figure_indicator(date_selected):
    if date_selected not in close_hist_pivot.index.tolist():
        raise PreventUpdate

    fig_indicator = go.Figure()
    index_etf_names_list = []
    for i in range(len(index_etf_info)):
        each_index_name = index_etf_info.loc[i, 'index_name']
        each_etf_name = index_etf_info.loc[i, 'etf_name']
        index_etf_names_list.append([each_index_name, each_etf_name])
    num_cols = 2
    column_width = 1 / num_cols
    row_height = 1 / len(index_etf_names_list)
    for j in range(len(index_etf_names_list)):
        temp_list = index_etf_names_list[j]
        for k in range(num_cols):
            temp_name = temp_list[k]
            temp_close_df = close_hist_pivot[[temp_name]].reset_index()
            fig_indicator.add_trace(go.Indicator(
                mode="number+delta",
                value=temp_close_df.loc[
                    temp_close_df[temp_close_df['Date'] == date_selected].index, temp_name].values[0],
                number={"prefix": "<span style='font-size:4rem;color:white'>",
                        "suffix": "</span>", "valueformat": ".2f"},
                title={"text": f"{temp_name}<br><span style='font-size:1em;color:gray'>"
                            f"{date_selected}</span><br><span style='font-size:1em;color:white'>"},
                delta={'reference': temp_close_df.loc[
                    temp_close_df[temp_close_df['Date'] == date_selected].index - 1, temp_name].values[0],
                    'relative': True, 'valueformat': '.2%', 'font': {'size': 20}},
                domain={'x': [k * column_width, (k + 1) * column_width],
                        'y': [1 - (j + 1) * row_height, 1 - j * row_height]}))
    fig_indicator.update_layout(height=3500, width=1500, template='plotly_dark')
    return fig_indicator


@app.callback([Output('Graph0', 'figure'),
            Output('Graph00', 'figure')],
            Input('Index-ETF-Close-Volume', 'value'))
def Update_graph_CLOSE(item_name):
    if not item_name:
        raise PreventUpdate
    one_close_volume_hist_df = one_close_volume_hist(close_volume_hist, item_name)
    one_close_hist_df = one_close_volume_hist_df[[item_name + '_Close']].copy()
    one_volume_hist_df = one_close_volume_hist_df[[item_name + '_Volume']].copy()
    fig_close = px.line(one_close_hist_df.reset_index(),
                        x='Date', y=one_close_hist_df.columns.tolist(), template='plotly_dark',
                        title=f'{item_name} - Closing Price', height=800, width=1500)
    fig_close.update_traces(line_color='ghostwhite')
    fig_close.update_xaxes(
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=3, label="3M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(count=3, label="3Y", step="year", stepmode="backward"),
                dict(count=5, label="5Y", step="year", stepmode="backward"),
                dict(label='All', step="all")])))
    fig_close.update_layout(template='plotly_dark',
                            xaxis_rangeselector_font_color='white',
                            xaxis_rangeselector_activecolor='red',
                            xaxis_rangeselector_bgcolor='green')
    fig_volume = px.bar(one_volume_hist_df.reset_index(),
                        x='Date', y=one_volume_hist_df.columns.tolist(), template='plotly_dark',
                        title=f'{item_name} - Trading Volume', height=800, width=1500)
    fig_volume.update_traces(marker_color='ghostwhite', marker_line_color='ghostwhite')
    fig_volume.update_xaxes(
        rangeselector=dict(
            buttons=list([
                dict(count=1, label="1M", step="month", stepmode="backward"),
                dict(count=3, label="3M", step="month", stepmode="backward"),
                dict(count=6, label="6M", step="month", stepmode="backward"),
                dict(count=1, label="YTD", step="year", stepmode="todate"),
                dict(count=1, label="1Y", step="year", stepmode="backward"),
                dict(count=3, label="3Y", step="year", stepmode="backward"),
                dict(count=5, label="5Y", step="year", stepmode="backward"),
                dict(label='All', step="all")])))
    fig_volume.update_layout(template='plotly_dark', hovermode='x unified',
                            xaxis_rangeselector_font_color='white',
                            xaxis_rangeselector_activecolor='red',
                            xaxis_rangeselector_bgcolor='green')
    return fig_close, fig_volume


@app.callback([Output('Graph1', 'figure'),
            Output('Graph2', 'figure')],
            [Input('Index-ETF-NAV', 'value'),
            Input('Time-Choice', 'value')])
def Update_graph_NAV(choice1, choice2):
    time_choice = choice2
    if choice1 == 'Stock Market Index':
        nav_filtered = nav_df_filter(index_nav, time_choice)
    else:
        nav_filtered = nav_df_filter(etf_nav, time_choice)
    fig1 = px.line(
        nav_filtered.reset_index(),
        x='Date',
        y=nav_filtered.columns.tolist(),
        color_discrete_map={name: color for name, color in zip(nav_filtered.columns,
                                                            px.colors.qualitative.Light24)},
        template='plotly_dark',
        title=f'{choice1}: {choice2} - Net Asset Value Comparison - Starting from 1', height=800, width=1500)
    fig1.update_layout(hovermode="x", hoverlabel=dict(font_color='black', font_size=12.5, bordercolor='white'))
    fig2 = px.area(
        nav_filtered,
        facet_col='Name',
        facet_col_wrap=7,
        color_discrete_map={name: color for name, color in zip(nav_filtered.columns,
                                                            px.colors.qualitative.Light24)},
        template='plotly_dark', height=800, width=1500)
    fig2.update_layout(font_size=7)
    return fig1, fig2


@app.callback([Output('DCR', 'figure'),
            Output('update_table', 'data')],
            Input('ETF-Index-Pair', 'value'))
def Update_etf_index_graph_table(etf_index_pair):
    if not etf_index_pair:
        raise PreventUpdate
    etf_index_pair_split = etf_index_pair.split(' {VS} ')
    etf_index_list = [part.strip() for part in etf_index_pair_split]
    etf_index_close_df = close_hist_pivot[etf_index_list].copy()
    etf_index_return_df = etf_index_close_df.pct_change(fill_method=None)
    etf_index_cum_return_df = (1 + etf_index_return_df.fillna(0)).cumprod() - 1
    etf_index_cum_return_df = etf_index_cum_return_df.round(4) * 100
    etf_index_cum_return_df.index = pd.to_datetime(etf_index_cum_return_df.index)
    etf_index_cum_return_df.index = etf_index_cum_return_df.index.strftime('%Y%m%d')
    fig_etf_index = px.line(etf_index_cum_return_df.reset_index(), x='Date',
                            y=etf_index_cum_return_df.columns.tolist(),
                            title=etf_index_pair + ' - Daily Cumulative Returns - Starting from 0%',
                            labels={'value': 'Returns (%)'}, template='plotly_dark',
                            height=800, width=1500)
    fig_etf_index.update_layout(
        xaxis_rangeselector_font_color='white',
        xaxis_rangeselector_activecolor='red',
        xaxis_rangeselector_bgcolor='green')
    fig_etf_index.update_layout(hovermode="x", hoverlabel=dict(font_color='white',
                                                            font_size=12.5, bordercolor='white'))

    etf_index_close_available = etf_index_close_df.dropna(how='any')
    etf_close = etf_index_close_available[[etf_index_list[0]]].copy()
    bmk_close = etf_index_close_available[[etf_index_list[1]]].copy()

    etf_index_return_available = etf_index_return_df.dropna(how='any')
    available_start_date = etf_index_return_available.index[0]
    available_end_date = etf_index_return_available.index[-1]
    etf_ret = etf_index_return_available[[etf_index_list[0]]].copy()
    bmk_ret = etf_index_return_available[[etf_index_list[1]]].copy()

    def each_indicator_df(each_close_df, each_ret_df, bmk_ret_df, start_date, end_date):
        indicator_df = pd.DataFrame(columns=[each_ret_df.columns[0]],
                                    index=['Max Daily Return', 'Min Daily Return',
                                        'Daily Volatility', 'Annualized Volatility',
                                        'Max Drawdown', 'Annualized Tracking Error'])
        indicator_df = indicator_df.reset_index().rename(columns={'index': start_date + ' ----> ' + end_date})
        indicator_df = indicator_df.set_index(start_date + ' ----> ' + end_date)
        each_ticker_name = indicator_df.columns[0]

        indicator_df.loc['Max Daily Return', each_ticker_name] = each_ret_df[each_ticker_name].max()
        indicator_df.loc['Min Daily Return', each_ticker_name] = each_ret_df[each_ticker_name].min()

        indicator_df.loc['Daily Volatility', each_ticker_name] = each_ret_df[each_ticker_name].std()
        indicator_df.loc['Annualized Volatility', each_ticker_name] = (
                each_ret_df[each_ticker_name].std() * np.sqrt(252))

        mdd = (each_close_df / each_close_df.expanding(min_periods=0).max()).min() - 1
        indicator_df.loc['Max Drawdown', each_ticker_name] = mdd.values[0]

        etf_return_df = each_ret_df.copy()
        etf_return_df.columns = ['Portfolio_Returns']
        bmk_return_df = bmk_ret_df.copy()
        bmk_return_df.columns = ['Benchmark_Returns']

        etf_bmk_return_df = pd.concat([etf_return_df, bmk_return_df], axis='columns')
        etf_bmk_return_df['Tracking_Difference_Returns'] = (
                etf_bmk_return_df['Portfolio_Returns'] - etf_bmk_return_df['Benchmark_Returns'])

        indicator_df.loc['Annualized Tracking Error', each_ticker_name] = (
                etf_bmk_return_df['Tracking_Difference_Returns'].std() * np.sqrt(252))

        indicator_df[each_ret_df.columns[0]] = indicator_df[each_ret_df.columns[0]] * 100
        indicator_df[each_ret_df.columns[0]] = indicator_df[each_ret_df.columns[0]].astype(int)

        indicator_df = indicator_df.reset_index()

        return indicator_df

    etf_indicator_df = each_indicator_df(etf_close, etf_ret, bmk_ret, available_start_date, available_end_date)
    index_indicator_df = each_indicator_df(bmk_close, bmk_ret, bmk_ret, available_start_date, available_end_date)
    etf_index_indicators = pd.concat([etf_indicator_df, index_indicator_df], axis='columns')
    etf_index_indicators = etf_index_indicators.loc[:, ~etf_index_indicators.columns.duplicated()]
    etf_index_indicators = etf_index_indicators.astype(str)
    etf_index_indicators.iloc[:, 1:] = etf_index_indicators.iloc[:, 1:] + '%'

    return fig_etf_index, etf_index_indicators.to_dict('records')


@app.callback(Output('Graph3', 'figure'),
            Input('Index-ETF-Correlation', 'value'))
def Update_Correlation_Heatmap(choice3):
    close_volume_hist2_df = close_volume_hist2[close_volume_hist2['Type'] == choice3].copy()
    close_hist_pivot2 = close_volume_hist2_df.pivot_table(index='Date', columns='Name', values='Close')
    ret_hist_df = close_hist_pivot2.pct_change(fill_method=None)
    corr_df = ret_hist_df.corr()
    fig = px.imshow(corr_df, text_auto=".2f", aspect="auto", template='plotly_dark',
                    color_continuous_scale='geyser', height=800, width=1500)
    return fig


@app.callback([Output('Graph4', 'figure'),
            Output('stock_recommendation', 'data'),
            Output('Graph5', 'figure'),
            Output('Graph6', 'figure')],
            [Input('ETF-Detail', 'value'),
            Input('etf-date-picker', 'date')])
def Update_ETF_Graphs(etf_selected, date_selected):
    if not etf_selected:
        raise PreventUpdate
    if date_selected not in etf_return_hist_pivot.index.tolist():
        raise PreventUpdate

    temp_etf_close = etf_close_hist_pivot[[etf_selected]].copy()
    temp_etf_close = temp_etf_close.reset_index()
    temp_etf_top_holdings = etf_top_holdings[etf_top_holdings['etf_name'] == etf_selected].copy()
    top_holdings_list = temp_etf_top_holdings['holdingName'].tolist()
    temp_top_stocks_close = stock_hist[stock_hist['Name'].isin(top_holdings_list)].copy()
    temp_top_stocks_close_pivot = temp_top_stocks_close.pivot_table(index='Date', columns='Name', values='Close')
    temp_top_stocks_return_pivot = temp_top_stocks_close_pivot.pct_change(fill_method=None).T

    each_top_stocks_return = temp_top_stocks_return_pivot[[date_selected]].copy()
    each_top_stocks_return = round(each_top_stocks_return * 100, 2)
    each_top_stocks_return_descending = each_top_stocks_return.sort_values(
        by=date_selected, ascending=False).copy()

    temp_stock_recommendation = stock_recommendation_trend_df_1m_url[
        stock_recommendation_trend_df_1m_url['stock_name'].isin(top_holdings_list)].copy()

    fig_bar_chart_with_indicator = go.Figure(px.bar(data_frame=each_top_stocks_return_descending.reset_index(),
                                    text_auto='.2f',
                                    x='Name',
                                    y=date_selected,
                                    color='Name',
                                    template='plotly_dark', height=800, width=1500,
                                    labels={date_selected: 'Return %', 'x': 'Name'},
                                    title=date_selected + '  ' + etf_selected + ': ' + 'Top Holdings Performance'))
    fig_bar_chart_with_indicator.update_traces(width=0.5, textfont_size=12,
                                            textangle=0, textposition="outside")
    fig_bar_chart_with_indicator.add_trace(go.Indicator(
        mode="number+delta",
        value=temp_etf_close.loc[
            temp_etf_close[temp_etf_close['Date'] == date_selected].index, etf_selected].values[0],
        number={"prefix": "<span style='font-size:4rem;color:white'>",
                "suffix": "</span>", "valueformat": ".2f"},
        title={"text": f"{etf_selected}<br><span style='font-size:1em;color:gray'>"
                    f"{date_selected}</span><br><span style='font-size:1em;color:gray'>"},
        delta={'reference': temp_etf_close.loc[
            temp_etf_close[temp_etf_close['Date'] == date_selected].index - 1, etf_selected].values[0],
            'relative': True, 'valueformat': '.2%', 'font': {'size': 20}},
        domain={'y': [0.9, 1], 'x': [0.8, 0.9]}))

    temp_etf_top_holdings_df = temp_etf_top_holdings[['holdingName', 'holdingPercent']].copy()
    percent_total = round(temp_etf_top_holdings_df['holdingPercent'].sum() * 100, 2)
    temp_etf_top_holdings_df['holdingPercent'] = temp_etf_top_holdings_df['holdingPercent'] * 100

    fig_radar_chart = px.line_polar(temp_etf_top_holdings_df, r='holdingPercent',
                                    theta='holdingName', line_close=True, template='plotly_dark', height=800,
                                    width=1500, markers=True,
                                    title=etf_selected + ': ' + f'Top Holdings ({percent_total}% of Total Assets)')
    fig_radar_chart.update_traces(fill='toself', line_color='snow')

    temp_etf_sector_weightings = etf_sector_weightings.query(f"etf_name=='{etf_selected}'").copy()
    temp_etf_sector_weightings = temp_etf_sector_weightings.drop(columns='etf_symbol')
    temp_etf_sector_weightings = temp_etf_sector_weightings.set_index('etf_name').T.reset_index()
    temp_etf_sector_weightings.columns = ['Sector', '%']
    temp_etf_sector_weightings['%'] = temp_etf_sector_weightings['%'].round(4)
    temp_etf_sector_weightings['%'] = temp_etf_sector_weightings['%'] * 100
    fig_pie_chart = px.pie(temp_etf_sector_weightings, values='%', names='Sector', hole=.3,
                        title=etf_selected + ': ' + 'Sector Weightings', template='plotly_dark', height=800,
                        width=1500)
    fig_pie_chart.update_traces(textposition='outside', textinfo='percent+label')

    return (fig_bar_chart_with_indicator, temp_stock_recommendation.to_dict('records'),
            fig_radar_chart, fig_pie_chart)


@app.callback([Output("card-header", "children"),
            Output("card-text", "children"),
            Output("dynamic-link", "children")],
            [Input("dropdown", "value")])
def Update_card(selected_title):
    if not selected_title:
        raise PreventUpdate
    news_row = latest_stock_market_news_df[latest_stock_market_news_df['News Title'] == selected_title].copy()
    news_content = news_row['News Content'].values[0]
    news_url = news_row['URL'].values[0]
    dynamic_link = f"[External Link]({news_url})"
    return [html.I(className="bi bi-newspaper me-2"), selected_title], news_content, dynamic_link


if __name__ == "__main__":

    app.run_server(debug=False)

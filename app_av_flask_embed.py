from threading import Thread

from flask import Flask, render_template
from tornado.ioloop import IOLoop

from bokeh.embed import server_document
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Slider
from bokeh.plotting import figure
from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature
from bokeh.server.server import Server
from bokeh.themes import Theme

import requests
import pandas as pd
import numpy as np
from tqdm import tqdm
from datetime import timedelta
from datetime import datetime
import time
import os

app = Flask(__name__)

api_key=os.getenv(ALPHAVANTAGE_API_KEY)

def request_stock_price_hist_for_100days(symbol, token, sample = False):
    if sample == False:
        q_string = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={}&outputsize=full&apikey={}'
    else:
        q_string = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={}&apikey={}'

    print("Retrieving stock price data from Alpha Vantage (This may take a while)...")

    r = requests.get(q_string.format(symbol, token))
    print("Data has been successfully downloaded...")
    date = []
    colnames = list(range(0, 7))
    df = pd.DataFrame(columns = colnames)
    print("Sorting the retrieved data into a dataframe...")
    for i in tqdm(r.json()['Time Series (Daily)'].keys()):
        date.append(i)
        row = pd.DataFrame.from_dict(r.json()['Time Series (Daily)'][i], orient='index').reset_index().T[1:]
        df = pd.concat([df, row], ignore_index=True)
    df.columns = ["open", "high", "low", "close", "adjusted close", "volume", "dividend amount", "split cf"]
    df['date'] = date
    df = df[0:100]
    return df

def bkapp(doc):

    def update_plot(doc):

    def update_ticker():
        global TICKER
        TICKER = ticker_textbox.value
        price_plot.title.text = "Closing Price: " + ticker_textbox.value
        return TICKER

    data_list = ["open", "high", "low", "close", "adjusted close"]

    def update(attr,old,new):
# ##Callback
         print("update triggered")

    #     #Get selection of lines to display
         selection = list()
         for i in wg_chk.active:
             selection.append(data_list[i])
         print(selection)

    wg_chk = CheckboxGroup(labels = ["open", "high", "low", "close", "adjusted close"], active = [0]*len(data_list))
    wg_chk.on_change('active', update)

    ticker_textbox = TextInput(placeholder="Ticker")
    update_button = Button(label="Update")
    ticker_pass = update_button.on_click(update_ticker)

    inputs = column([ticker_textbox, update_button, wg_chk], width=200)

    price_plot = figure(plot_width=800,
                    plot_height=400,
                    x_axis_type='datetime',
                    title="Stock Price Plot")


    #TICKER = ticker_pass
    TICKER = "AAPL"
    data = request_stock_price_hist_for_100days(TICKER, api_key)

    price_plot.line(source=data, x='date', y="close")
    price_plot.xaxis.axis_label = "Time"
    price_plot.yaxis.axis_label = "Closing Price"
    price_plot.title.text = "Recent Stock Price: " + TICKER

    doc().add_root(row(inputs, price_plot, width=1600))
    doc().title = "Stock Price Plot"

    doc.theme = Theme(filename="theme.yaml")


@app.route('/', methods=['GET'])
def bkapp_page():
    script = server_document('http://localhost:5006/bkapp')
    return render_template("embed.html", script=script, template="Flask")


def bk_worker():
    # Can't pass num_procs > 1 in this configuration. If you need to run multiple
    # processes, see e.g. flask_gunicorn_embed.py
    server = Server({'/bkapp': bkapp}, io_loop=IOLoop(), allow_websocket_origin=["localhost:8000"])
    server.start()
    server.io_loop.start()

Thread(target=bk_worker).start()

if __name__ == '__main__':
    print('Opening single process Flask app with embedded Bokeh application on http://localhost:8000/')
    print()
    print('Multiple connections may block the Bokeh app in this configuration!')
    print('See "flask_gunicorn_embed.py" for one way to run multi-process')
    app.run(port=8000)

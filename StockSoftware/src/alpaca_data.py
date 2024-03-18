from alpaca.trading.client import TradingClient
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass
from alpaca.broker.client import BrokerClient
from alpaca.trading.enums import AssetExchange
import os
import concurrent.futures
import csv
import pandas as pd
import numpy as np
import datetime

from alpha import AlphaVantage

class AlpacaTrade():
    def __init__(self,isPaper):
        if isPaper:
            self.key = 'CK5AO4SR28HE8UR15NZH'
            self.secret = 'BX6zeHCeUD5tyIldlsd0AFtuKKkd922DoQ9gXmMz'
        else:
            self.key = 'AKDX2DA2DMK5WOJKG24H'
            self.secret = 'MXD6dJWx8JDLeqq0uy0ougHR8jLrW3AH2i0o9sDy'
        
        self.account_id = '569e75cc-eaf8-4185-a1e9-6facda0c3475'
        self.api = TradingClient(self.key,self.secret,paper=isPaper)
        self.ALPHA = AlphaVantage()
        self.broker = BrokerClient(api_key=self.key,secret_key=self.secret,sandbox=False)
        self.assets = self.api.get_all_positions()
        self.all_symbols = []

        self.directory = os.path.dirname(os.path.abspath(__file__))

        with open(self.get_path('symbols.csv'),"r") as f:
            reader = csv.reader(f)
            for symbol in reader:
                self.all_symbols.append(symbol[0])

    def get_path(self,filename):
        return os.path.join(self.directory, filename)

    def update_list(self):
        file = open(self.get_path('symbols.csv'),"a+")
        writer = csv.writer(file)
        all_assets = self.api.get_all_assets(GetAssetsRequest(asset_class=AssetClass.US_EQUITY,exchange=AssetExchange.NYSE))
        symbols = []

        for line in all_assets.__str__().split(","):
            line_split = line.split(": ")
            if 'symbol' in line_split[0]:
                symbols.append(line_split[1].strip("'"))
        for symbol in symbols:
            try:
                self.get_latest_price(symbol)
                if symbol not in self.all_symbols:
                    print("Symbol added: {0}".format(symbol))
                    writer.writerow([symbol])
            except Exception as e: {}

        self.all_symbols = []
        with open(self.get_path('symbols.csv'),"r") as f:
            reader = csv.reader(f)
            for symbol in reader:
                self.all_symbols.append(symbol[0])

    def update_assets(self):
        self.assets = self.api.get_all_positions()

    def get_active_symbols(self):
        return self.ALPHA.most_active_symbols()

    def is_owned(self,symbol):
        for position in self.assets:
            if symbol == position.symbol:
                return True
            
        return False
            
    def get_price(self,symbol,days):
        parameters = StockBarsRequest(
                        symbol_or_symbols=symbol,
                        timeframe=TimeFrame.Day,
                        start=datetime.datetime.now()-datetime.timedelta(days=days)
                    )
        quotes = StockHistoricalDataClient(self.key,self.secret).get_stock_bars(parameters).df.tz_convert('America/New_York',level=1)
        all_prices = []
        for price in quotes['close']:
            all_prices.append(price)
        quotes = pd.DataFrame({'Stock Prices': all_prices})
        return quotes

    def SMA(self,symbol,price_dframe):
        total_price = np.average(price_dframe)
        return total_price
    
    def EMA(self,symbol,price_dframe):
        return price_dframe.ewm(com=0.5).mean()
    
    def get_latest_price(self,symbol):
        parameters = StockLatestQuoteRequest(symbol_or_symbols=symbol)
        latest_quote = StockHistoricalDataClient(self.key,self.secret).get_stock_latest_trade(parameters)
        return latest_quote[symbol].__dict__['price']
        
        
    def verify_symbol(self,symbol):
        try:
            
            display_not_owned = True

            if isinstance(symbol,str):
                dframe = self.get_price(symbol,days=200)
                last_idx = dframe.last_valid_index()
                sma_200 = self.SMA(symbol,dframe['Stock Prices'])
                sma_50 = self.SMA(symbol,dframe['Stock Prices'].loc[(last_idx-50):last_idx])
                ema = self.EMA(symbol,dframe['Stock Prices'].loc[(last_idx-15):last_idx])
                ema = ema[ema.last_valid_index()]
            elif isinstance(symbol,list):
                sma_200 = float(symbol[1])
                sma_50 = float(symbol[2])
                ema = float(symbol[4])

                symbol = symbol[0]

            latest_price = self.get_latest_price(symbol)
            owned = self.is_owned(symbol)
            
            print("\nSymbol: {0}\nSMA 200: ${1:.2f} | SMA 50: ${2:.2f} {3}\nEMA 15: ${4:.2f} {5}\nLatest Price: ${6:.2f}".format(symbol,sma_200, sma_50, 'Buy' if sma_200 < sma_50 else ('Sell' if owned else 'Dont Buy'),ema,'Buy' if ema <= latest_price else ('Sell' if owned else 'Dont Buy'),latest_price))
            csv_list = [symbol,sma_200.__str__(),sma_50.__str__(),('Buy' if sma_200 < sma_50 else ('Sell' if owned else 'Dont Buy')),ema,('Buy' if ema <= latest_price else ('Sell' if owned else 'Dont Buy')),latest_price.__str__()]
            file = open(self.get_path('worksheet.csv'),'a+')
            writer = csv.writer(file)
            writer.writerow(csv_list)
            file.close()
            return csv_list
        
        except Exception as e:
            if e == '{"message": "too many requests."}':
                print("running again")
                self.verify_symbol(symbol)
        

    
    def verify_all_symbols(self,check_sameday):
        
        file = open(self.get_path('worksheet.csv'),'r')
        reader = csv.reader(file)
        reader.__next__()
        date = reader.__next__()
        file.close()

        now = datetime.datetime.now()
        today = datetime.datetime.today()

        sameday = True
        if now.hour >= 15 and datetime.datetime.strftime(today,"%m/%d/%Y") != date:
            sameday = False
        
        if sameday or check_sameday:
            today = today - datetime.timedelta(days=1)

        if sameday and check_sameday: 

            file = open(self.get_path('worksheet.csv'),'r')
            reader = csv.reader(file)
            reader.__next__()
            reader.__next__()
            data = []
            for row in reader:
                data.append(row)
            file.close()

            file = open(self.get_path('worksheet.csv'),'a+')
            writer = csv.writer(file)
            file.truncate(0)
            writer.writerow(["Symbol","SMA 200","SMA 50","Decision","EMA","Decision","Latest Price"])
            writer.writerow([datetime.datetime.strftime(today,"%m/%d/%Y")])
            file.close()
            with concurrent.futures.ThreadPoolExecutor(max_workers=12) as self.executor:
                self.executor.map(self.verify_symbol,data)
            
                self.executor.shutdown(True)
            
        else:
            file = open(self.get_path('worksheet.csv'),'a+')
            writer = csv.writer(file)
            file.truncate(0)
            writer.writerow(["Symbol","SMA 200","SMA 50","Decision","EMA","Decision","Latest Price"])
            writer.writerow([datetime.datetime.strftime(today,"%m/%d/%Y")])
            file.close()
            with concurrent.futures.ThreadPoolExecutor(max_workers=12) as self.executor:
                self.executor.map(self.verify_symbol,self.all_symbols)
            
                self.executor.shutdown(True)
        
        
        print('')

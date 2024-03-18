import requests
import json
import datetime
import os

class AlphaVantage():

    def __init__(self):
        self.key = 'I20LORTUZB1PT4KG'
        self.directory = os.path.dirname(os.path.abspath(__file__))

    def get_path(self,filename):
        return os.path.join(self.directory, filename)
    def get_url(self,request):
        return ('https://www.alphavantage.co/query?function={0}&apikey={1}').format(request,self.key)
    def get_request(self,request):
        return requests.get(self.get_url(request))
    def most_active(self):
        file = open(self.get_path('active.json'),'r+')
        data = json.loads(file.read())
        
        if datetime.datetime.now().hour >= 15 and data[0]['date']['day'] != datetime.datetime.strftime(datetime.datetime.today(),'%m/%d/%Y'):
            file.close()
            file = open(self.get_path('active.json'),'w+')
            json_obj = []
            json_obj.append(json.loads(datetime.datetime.today().strftime('{"date": {"day": "%m/%d/%Y"}}')))
            json_obj.append(self.get_request('TOP_GAINERS_LOSERS').json())
            json.dump(json_obj,file,indent=4)
            file.close()
        elif datetime.datetime.now().hour < 15 and data[0]['date']['day'] != datetime.datetime.strftime((datetime.datetime.today()-datetime.timedelta(days=1)),'%m/%d/%Y'):
            file.close()
            file = open(self.get_path('active.json'),'w+')
            json_obj = []
            json_obj.append(json.loads((datetime.datetime.today()-datetime.timedelta(days=1)).strftime('{"date": {"day": "%m/%d/%Y"}}')))
            json_obj.append(self.get_request('TOP_GAINERS_LOSERS').json())
            json.dump(json_obj,file,indent=4)
            file.close()
        file = open(self.get_path('active.json'),'r+')
        data = json.loads(file.read())
        file.close()
        return data[1]
    
    def most_active_symbols(self):
        most = self.most_active()
        most_symbols = []

        for stocks in most['top_gainers']:
            most_symbols.append(stocks['ticker'])
        for stocks in most['top_losers']:
            most_symbols.append(stocks['ticker'])
        for stocks in most['most_actively_traded']:
            most_symbols.append(stocks['ticker'])

        return most_symbols
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import json
from statsmodels.tsa.arima.model import ARIMA
from pmdarima.arima import auto_arima

NODE_NAME = "node-1"
STREAM_FILE_PATH = 'data.txt'

class PredictComponent:

    def __init__(self, data, treshold=0.35):
        self.data = data.copy()
        self.treshold = treshold
        self.train()
    
    def predict(self, step):
        return self.trained_model.forecast(steps=step)
    
    def forecast(self, second):
        p = self.trained_model.forecast(steps=second)
        return (p.index[-1], p.iloc[-1])
    
    def train(self):
        start = time.time()
        self.automodel = auto_arima(self.data, trace=False, suppress_warnings=True, maxiter=1000, max_p=25, max_q=25, max_P=25, max_Q=25, stepwise=True)
        self.order = self.automodel.order
        self.model = ARIMA(self.data, order=self.order)
        self.trained_model = self.model.fit()
        end = time.time()
        print(f"Training time: {round((end-start)*1000,3)}ms")
        self.next_retrain = int(len(self.data) * self.treshold)
    
    def add_data(self, new_data):
        new_data_copied = new_data.copy()
        self.data = pd.concat([self.data, new_data_copied])
        self.train()
    
    def update(self, new_data):
        self.next_retrain = self.next_retrain - len(new_data)
        if self.next_retrain < 0:
            self.add_data(new_data)
        else:
            start = time.time()
            new_data_copied = new_data.copy()
            self.data = pd.concat([self.data, new_data_copied])
            self.model.update(new_data_copied)
            end = time.time()
            print(f"Update time: {round((end-start)*1000,3)}ms, Next Retrain: {self.next_retrain}")
    
    def last_index(self):
        return self.trained_model.nobs
    
    def __str__(self):
        return f"ARIMA {self.order}"

# np.random.seed(0)
# data = pd.Series(np.random.randn(30), index=pd.date_range('2000-01-01', periods=30))
# print(data)
# x = PredictComponent(data)
# print(x.last_index())

def read_from_file():
    with open(STREAM_FILE_PATH, 'r') as file:
        lines = file.readlines()
        if lines:
            result = []
            for line in lines:
                data = json.loads(line)
                result.append(data)
            with open(STREAM_FILE_PATH, 'w') as file:
                file.write('')
            for i in range(len(result)):
                result[i] = (to_vector(result[i][NODE_NAME]))
            return result
    return []

def to_vector(stats_data):
    result = [stats_data["timestamp"], stats_data["write_load"]]
    order = ["index", "get", "query", "fetch", "scroll", "suggest", "bulk", "flush", "refresh"]
    for o in order:
        total = stats_data["delta_total"][o]
        time = stats_data["delta_time"][o]
        if total > 0:
            val = time/total
        else:
            val = 0
        result.append(val)
    result.append(stats_data["cpu"]["percent"])
    result.append(stats_data["cpu"]["load_avg_1m"])
    result.append(stats_data["cpu"]["load_avg_5m"])
    result.append(stats_data["cpu"]["load_avg_15m"])
    result.append(stats_data["mem"]["used_percent"])
    return np.asarray(result)

def create_dataframe(data):
    df = pd.DataFrame(data, columns=['Time', 'WriteLoad', 'Index', 'Get', 'Query', 'Fetch', 'Scroll', 'Suggest', 'Bulk', 'Flush', 'Refresh', 'CPUPercent', 'LoadAvg1m', 'LoadAvg5m', 'LoadAvg15m', 'MemUsedPercent'])
    df['Time'] = pd.to_datetime(df['Time'], unit='ms')
    df['Time'] = df['Time'].dt.round('S')
    df.set_index('Time', inplace=True)
    df.index = pd.DatetimeIndex(df.index).to_period('S')
    df.dropna(inplace=True)
    #print(df.to_string())
    return df

data = read_from_file()
df = create_dataframe(data)
model_cpupercent = PredictComponent(df['CPUPercent'])
while True:
    currdata = read_from_file()
    if len(currdata) > 0:
        currdf = create_dataframe(currdata)
        model_cpupercent.update(currdf['CPUPercent'])
        for each in currdata:
            data.append(each)
    else:
        print(f"No new data found, current data={len(data)}")
    print(f"Next 60s: {model_cpupercent.forecast(60)}")
    print(f"Next 120s: {model_cpupercent.forecast(120)}")
    time.sleep(5)

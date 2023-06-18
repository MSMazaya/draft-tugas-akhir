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

    def __init__(self, data):
        self.automodel = auto_arima(data, trace=False, suppress_warnings=True)
        self.order = self.automodel.order
        self.model = ARIMA(data, order=self.order)
        self.trained_model = self.model.fit()
    
    def predict(self, step):
        return self.trained_model.forecast(steps=step)
    
    def last_index(self):
        return self.trained_model.nobs

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

data = []
while True:
    currdata = read_from_file()
    if len(currdata) > 0:
        for each in currdata:
            data.append(each)
    else:
        print(f"Skipping training, current data={len(data)}")
        time.sleep(10)
        continue
    df = create_dataframe(data)
    x = PredictComponent(df['CPUPercent'])
    print(x.predict(60))
    time.sleep(5)

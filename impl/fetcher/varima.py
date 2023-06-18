import time
import json
import numpy as np
from numpy import linalg
import pandas as pd
from pmdarima import auto_arima
from statsmodels.tsa.statespace.varmax import VARMAX

NODE_NAME = "node-1"
STREAM_FILE_PATH = 'data.txt'

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
    # order = ["index", "query", "fetch"]
    # for o in order:
    #     total = stats_data["delta_total"][o]
    #     time = stats_data["delta_time"][o]
    #     if total > 0:
    #         val = time/total
    #     else:
    #         val = 0.01
    #     result.append(val)
    result.append(stats_data["cpu"]["percent"])
    result.append(stats_data["cpu"]["load_avg_1m"])
    result.append(stats_data["cpu"]["load_avg_5m"])
    result.append(stats_data["cpu"]["load_avg_15m"])
    result.append(stats_data["mem"]["used_percent"])
    #print(result)
    return np.asarray(result)

def create_dataframe(data):
    # 'Var7', 'Var8', 'Var9'
    df = pd.DataFrame(data, columns=['Time', 'Var1', 'Var2', 'Var3', 'Var4', 'Var5', 'Var6'])
    ctnrmlz = ['Var1', 'Var2', 'Var3', 'Var4', 'Var5', 'Var6']
    print(df.head())
    mean = df[ctnrmlz].mean()
    std = df[ctnrmlz].std()
    df[ctnrmlz] = (df[ctnrmlz] - mean) / std
    df['Time'] = pd.to_datetime(df['Time'], unit='ms')
    df.set_index('Time', inplace=True)
    df = df.fillna(0.01)
    #df = df.asfreq('s')
    return df, mean, std

def create_model(data):
    df, mean, std = create_dataframe(data)
    model = VARMAX(df, order=(1, 0), enforce_stationarity=False)
    model_fit = model.fit(disp=False)
    return model_fit, mean, std

data = read_from_file()
while True:
    currdata = read_from_file()
    if len(currdata) > 0:
        for each in currdata:
            data.append(each)
    else:
        print(f"Skipping training, current data={len(data)}")
        time.sleep(5)
        continue
    try:
        model, mean, std = create_model(data)
    except linalg.LinAlgError as e:
        print(f"Failed to train model, current data={len(data)}, error: {e}")
        time.sleep(5)
        continue
    fc = model.forecast(steps=20)
    fc = fc*std+mean
    fc = fc.applymap(lambda x: 0 if x < 0 else x)
    print(fc)
    time.sleep(1)
    break


import time
from configuration import DEBUG, STREAM_FILE_PATH, NODE_NAME, MODEL_FILE_PATH, TIMEZONE, SAVE_MODEL
import pandas as pd
import numpy as np
import json
import pickle

def save_model(model):
    if (not SAVE_MODEL):
        return
    with open(MODEL_FILE_PATH, 'wb') as file:
        pickle.dump(model, file)

def timings(precision=3):
    start = time.time()
    def end():
        return round((time.time()-start)*1000,precision)
    return end

def printd(*args):
    if DEBUG:
        print(*args)

def read_from_file():
    with open(STREAM_FILE_PATH, 'r') as file:
        lines = file.readlines()
        if lines:
            result = []
            for line in lines:
                data = json.loads(line)
                result.append(data)
            # with open(STREAM_FILE_PATH, 'w') as file:
            #     file.write('')
            #     pass
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
    df['Time'] = pd.to_datetime(df['Time']).dt.tz_localize('UTC')
    df['Time'] = df['Time'].dt.tz_convert(TIMEZONE)
    df.set_index('Time', inplace=True)
    df.index = pd.DatetimeIndex(df.index).to_period('S')
    df.dropna(inplace=True)
    #print(df.to_string())
    #print(df.columns.tolist())
    return df
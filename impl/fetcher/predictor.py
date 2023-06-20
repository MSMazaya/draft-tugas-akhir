import pandas as pd
import time
import pickle
import os
import warnings
from utils import printd, read_from_file, save_model, create_dataframe
from configuration import WARNING, MODEL_FILE_PATH, PREDICTOR_INTERVAL_SEC
from predictcomponent import PredictComponent, PredictComponentFactory

if not WARNING:
    warnings.filterwarnings("ignore")

data = read_from_file()
df = create_dataframe(data)
# pcf = PredictComponentFactory(df, ['WriteLoad', 'Index', 'Get', 'Query', 'Fetch', 'Scroll', 'Suggest', 'Bulk', 'Flush', 'Refresh', 'CPUPercent', 'LoadAvg1m', 'LoadAvg5m', 'LoadAvg15m', 'MemUsedPercent'], 0.75)
# buildtime = timings()
# pcs = pcf.build()
# printd(f"Build time: {buildtime()}ms")
# printd([str(x) for x in pcs])
# for each in pcs:
#     printd(f"{each.name} Prediction:")
#     printd(f"Next 60s: {each.forecast(60)}")
#     printd(f"Next 120s: {each.forecast(120)}")
#     printd()
# save_model(pcs)
# exit(0)
if os.path.exists(MODEL_FILE_PATH):
    with open(MODEL_FILE_PATH, 'rb') as file:
        model_cpupercent = pickle.load(file)
    printd(f"Loaded model from '{MODEL_FILE_PATH}'.")
else:
    if len(df) == 0:
        print("No model and data found. Exiting...")
        print("Perhaps you need to run 'stats-fetcher' module first.")
        exit(0)
    print("Creating new model.")
    model_cpupercent = PredictComponent('CPUPercent', df['CPUPercent'])
    save_model(model_cpupercent)

while True:
    currdata = read_from_file()
    if len(currdata) > 0:
        currdf = create_dataframe(currdata)
        model_cpupercent.update(currdf['CPUPercent'])
        save_model(model_cpupercent)
    else:
        printd(f"No new data found.")
    printd(f"Next 60s: {model_cpupercent.forecast(60)}")
    printd(f"Next 120s: {model_cpupercent.forecast(120)}")
    time.sleep(PREDICTOR_INTERVAL_SEC)

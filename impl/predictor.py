import json
import time
import pickle
import os
import warnings
from utils import printd, read_from_file, save_model, create_dataframe, timings
from configuration import WARNING, MODEL_FILE_PATH, PREDICTOR_INTERVAL_SEC
from predict import PredictComponent, PredictComponentFactory, PredictComponentStorage

if not WARNING:
    warnings.filterwarnings("ignore")

data = read_from_file()
printd("Loading data...")
df = create_dataframe(data)
pcf = PredictComponentFactory(df, ['WriteLoad', 'Index', 'Get', 'Query', 'Fetch', 'Scroll', 'Suggest', 'Bulk', 'Flush', 'Refresh', 'CPUPercent', 'LoadAvg1m', 'LoadAvg5m', 'LoadAvg15m', 'MemUsedPercent'], 0.75)
printd("Starting training... (this may take a while)")
buildtime = timings()
predictor = PredictComponentStorage(pcf)
printd(f"Build time: {buildtime()}ms")
printd(f"Forecasting next 60s:")
f60 = predictor.forecast(60)
printd(json.dumps(f60, indent=4))
printd(f"Forecasting next 120s:")
f120 = predictor.forecast(120)
printd(json.dumps(f120, indent=4))
printd(str(predictor))
exit(0)
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

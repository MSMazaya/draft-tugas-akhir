import warnings
import time
import os
import datetime
from configuration import WARNING, COMPONENTS, MODEL_FILE_PATH, DATA_UPDATE_TICK_SEC, PERCENT_RETRAIN
from utils import printd, read_from_file, create_dataframe, timings, load_model, save_model
from predict import PredictComponentFactory, PredictComponentStorage
from rule import RuleManager
from resourcecontroller import ResourceController

if not WARNING:
    warnings.filterwarnings("ignore")

class AdaptiveControl:

    def __init__(self):
        self.is_launched = False
        self.rulemanager = RuleManager()
        self.predictiontime = self.rulemanager.get_required_prediction_time()
        self.controller = ResourceController()
        self.nextTickData = 0
    
    def __safe_call(self):
        if (not self.is_launched):
            printd("Please call 'launch()' first.")
            exit(0)

    def __tick_new_data(self):
        if time.time() <= self.nextTickData:
            return
        printd("-"*10)
        printd(datetime.datetime.now())
        self.nextTickData = time.time() + DATA_UPDATE_TICK_SEC
        currdata = read_from_file()
        if len(currdata) > 0:
            currdf = create_dataframe(currdata)
            self.predictor.update(currdf)
            save_model(self.predictor)
            printd(currdf.head())
    
    def tick(self):
        self.__safe_call()
        self.__tick_new_data()
        forecasted = {}
        for pt in self.predictiontime:
            forecasted[pt] = self.predictor.forecast(pt)
        runningRules = self.rulemanager.test(forecasted)
        if len(runningRules) > 0:
            for rule in runningRules:
                printd(f"Applying rule: {rule}")
                if rule['Type'] == 'cpu':
                    self.controller.change_resource(rule['Amount'], None)
                elif rule['Type'] == 'mem':
                    self.controller.change_resource(None, rule['Amount'])
        self.controller.tick()
                

    def launch(self):
        printd("-"*10)
        printd("Launching adaptive control...")
        data = self.__wait_for_data()
        printd("Data found! Loading data...")
        df = create_dataframe(data)

        self.pcf = PredictComponentFactory(df, COMPONENTS[1:], PERCENT_RETRAIN)

        if os.path.exists(MODEL_FILE_PATH):
            self.__load_model()
        else:
            self.__build()
        save_model(self.predictor)
        self.is_launched = True
        
    def __build(self):
        printd("-"*10)
        printd("Building model...")
        buildtime = timings()
        self.predictor = PredictComponentStorage(self.pcf)
        printd(f"Build time: {buildtime()}ms")

    def __load_model(self):
        printd("-"*10)
        printd("Loading model...")
        self.predictor = load_model()
        if (self.predictor == None and not(type(self.predictor) is PredictComponentStorage)):
            printd("Failed to load model...")
            self.build()

    def __wait_for_data(self):
        data = read_from_file()
        failed = 0
        while len(data) == 0:
            failed += 1
            printd("Waiting for data...")
            data = read_from_file()
            time.sleep(1)
            if failed > 10:
                print("No data found. Exiting...")
                print("Perhaps you need to run 'stats-fetcher' module first.")
                exit(0)
        return data

ac = AdaptiveControl()
ac.launch()
while True:
    ac.tick()
    time.sleep(1)
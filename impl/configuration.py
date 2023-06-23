DEBUG = True
WARNING = False
TIMEZONE = 'Asia/Jakarta'
NODE_NAME = "node-1"
STREAM_FILE_PATH = './data/stream'
RULE_FILE_PATH = 'example.rule'
MODEL_FILE_PATH = './data/model.pkl'
RSRC_CTRL_DATA_PATH = 'resourcecontrol.json'
FETCHER_INTERVAL_SEC = 1
OFFSET_TRESHOLD_RETRAIN = 120
PERCENT_RETRAIN = 0.8
DATA_UPDATE_TICK_SEC = 10
SAVE_MODEL = True
ELASTICSEARCH_HOST = 'http://localhost:9200'
KUBERNETES_NAMESPACE = 'default'
KUBERNETES_DEPLOYMENT_NAME = 'elasticsearch'
RESOURCE_CHANGE_COOLDOWN = 10
CPU_LIMIT_IN_MILLI = (500,8000)
MEM_LIMIT_IN_MIB = (4096,8192)

# DO NOT CHANGE THIS
COMPONENTS = ['Time', 'WriteLoad', 'Index', 'Get', 'Query', 'Fetch', 'Scroll', 'Suggest', 'Bulk', 'Flush', 'Refresh', 'CPUPercent', 'LoadAvg1m', 'LoadAvg5m', 'LoadAvg15m', 'MemUsedPercent']
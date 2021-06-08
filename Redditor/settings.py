from pathlib import Path

# The root folder of Redditor
FILE_PATH = Path(__file__).parent.absolute()

# Path to the config.json file
CONFIG_PATH = FILE_PATH/"./config.json"

# Path to the DB folder
DB_NAME = "Redditor.sql"
DB_FOLDER =  FILE_PATH/"./db/"
DB_PATH = DB_FOLDER/DB_NAME

# Path to the cogs folder
COGS_NAME = "cogs"
COGS_FOLDER = FILE_PATH/f"./{COGS_NAME}/"

# Path to the logs folder
LOGS_FOLDER = FILE_PATH/"./logs/"
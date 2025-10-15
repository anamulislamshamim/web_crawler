# db_config.py

from settings import MONGO_URI, DB_NAME
from database.storage import MongoStorage

# Shared mongo instance
def config_mongo():
    return MongoStorage(uri=MONGO_URI, db_name=DB_NAME)

# This is the shared instance that can be imported elsewhere
mongo = config_mongo()
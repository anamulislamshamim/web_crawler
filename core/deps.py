# Common dependencies (DB, pagination)
from fastapi import Request
from database.storage import MongoStorage


async def get_mongo(request: Request) -> MongoStorage:
    return request.app.state.mongo

# while app.state.mongo makes the client globally available, using Depends(get_mongo) 
# makes the client globally accessible, testable, and maintainable. 
# It moves the "how to get it" logic outside of the "how to use it" logic.
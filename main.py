from loguru import logger
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
import datetime
from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database
import datetime
from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database

import os

# --- Database Configuration ---
# The database URL is now read from an environment variable for security and flexibility.
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+aiomysql://user:password@localhost/dbname")

database = Database(DATABASE_URL)
Base = declarative_base()
engine = create_engine(DATABASE_URL.replace("aiomysql", "pymysql"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Database Model ---
class History(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True, index=True)
    input_str = Column(String(255))
    result = Column(JSON)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

def get_char_value(char):
    """
    Calculates the value of a character. a=1, b=2, ..., z=26.
    Non-alphabetic characters have a value of 0.
    """
    if 'a' <= char.lower() <= 'z':
        return ord(char.lower()) - ord('a') + 1
    return 0

def get_z_value(input_str, index):
    """
    Calculates the value of 'z' which takes the next character's value.
    This is recursive if the next character is also 'z'.
    """
    # Base value of 'z'
    value = get_char_value('z')
    next_index = index + 1

    # If there is a next character
    if next_index < len(input_str):
        next_char = input_str[next_index]
        if next_char.lower() == 'z':
            # If next char is 'z', recurse
            recursive_value, new_index = get_z_value(input_str, next_index)
            value += recursive_value
            return value, new_index
        else:
            # Otherwise, just add the next char's value
            value += get_char_value(next_char)
            return value, next_index + 1
    
    # 'z' is the last character in the string
    return value, next_index

def convert_measurements(input_str):
    """
    Processes a string to calculate sums based on character values.

    The function reads the string in segments. The first character of a segment
    determines a count (a=1, b=2, etc.). The following characters up to that
    count are summed up based on their alphabetic value.

    A special rule applies to 'z': 
    - If 'z' is a counter, its count is 26 + value of the next character.
    - If 'z' appears as a character to be summed, it also incorporates the value 
      of the character immediately following it (recursively for chained 'z's).

    Args:
        input_str (str): The string to be processed.

    Returns:
        list: A list of integers, where each integer is the sum for a segment
              of the string.
    """
    logger.info(f"Processing input string: '{input_str}'")
    results = []
    i = 0
    while i < len(input_str):
        count_char = input_str[i]
        logger.debug(f"Current index: {i}, count_char: '{count_char}'")
        count = 0
        
        if count_char.lower() == 'z':
            z_value, next_i = get_z_value(input_str, i)
            count = z_value
            i = next_i
            logger.debug(f"Handled 'z' as counter. Count: {count}, new index: {i}")
        else:
            count = get_char_value(count_char)
            i += 1

        if count == 0:
            logger.warning(f"Count is 0 for char '{count_char}' at index {i-1}. Appending 0 to results.")
            results.append(0)
            continue

        logger.debug(f"Segment count: {count}")
        current_sum = 0
        values_to_process = count
        
        while values_to_process > 0 and i < len(input_str):
            value_char = input_str[i]
            
            if value_char.lower() == 'z':
                z_value, next_i = get_z_value(input_str, i)
                current_sum += z_value
                logger.debug(f"Handled 'z' in values. Value: {z_value}, consumed until index {next_i}")
                # Move index past all consumed characters for 'z'
                i = next_i
            else:
                char_val = get_char_value(value_char)
                current_sum += char_val
                logger.debug(f"Char '{value_char}' value: {char_val}, current_sum: {current_sum}")
                i += 1
            
            values_to_process -= 1
        
        logger.info(f"Segment sum: {current_sum}")
        results.append(current_sum)

    logger.info(f"Final result for '{input_str}': {results}")
    return results

app = FastAPI()

class ConvertRequest(BaseModel):
    input_str: str

async def save_to_history(input_str: str, result: list):
    query = History.__table__.insert().values(
        input_str=input_str,
        result={"result": result},
        timestamp=datetime.datetime.utcnow()
    )
    await database.execute(query)

@app.get("/convert-measurements", response_model=dict)
async def get_convert_measurements_api_with_db(input_str: str):
    """
    GET endpoint to process a string, save to history, and return measurement values.
    """
    logger.info(f"GET /convert-measurements for str: '{input_str}'")
    result = convert_measurements(input_str)
    await save_to_history(input_str, result)
    return {"input_str": input_str, "result": result}

@app.post("/convert-measurements", response_model=dict)
async def post_convert_measurements_api_with_db(request: ConvertRequest):
    """
    POST endpoint to process a string, save to history, and return measurement values.
    """
    logger.info(f"POST /convert-measurements with str: '{request.input_str}'")
    result = convert_measurements(request.input_str)
    await save_to_history(request.input_str, result)
    return {"input_str": request.input_str, "result": result}

@app.get("/history")
async def get_history():
    """
    GET endpoint to retrieve all historical data.
    """
    logger.info("GET request for history received")
    query = History.__table__.select()
    return await database.fetch_all(query)

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

# Configure logger to write to a file
logger.add("app.log", rotation="1 week", retention="2 weeks", level="INFO")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8090)
import pandas as pd
import json
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy import text
from dotenv import load_dotenv
import os

load_dotenv()
db_url = os.getenv("AIVEN_DB_URL")
engine = create_engine(db_url)

# '__file__' returns the name of the script,
# 'parent' returns the parent folder, does not add the /load_data.py at the end
# 'resolve()' gets the directory from the root of the hard drive
current_dir = Path(__file__).resolve().parent
# finding the Data folders directory
data_dir = current_dir / "Data"
all_listening_data = []
# json_files is a generator object
# instead of storing all the file paths as a list that uses a lot of memory at once,
# It calculates and yields just one file path at a time when called by a loop
json_files = data_dir.glob("*.json")
for json_file in json_files:
    # The 'with' statement acts as a safety mechanism
    # that guarantees the closing of a file or the termination of a connection and at last freeing memory,
    # even if the program crashes or encounters an error
    with open(json_file, 'r', encoding='utf-8') as f:
        # 'extend' is used instead of 'append' to create a single flat list, instead of nested list.
        # for example : [1,2].append([3,4]) --> [1,2,[3,4]] | [1,2].extend([3,4]) --> [1,2,3,4]
        all_listening_data.extend(json.load(f))
# converting list to pandas
df = pd.DataFrame(all_listening_data)

# getting a connection (conn) from the connection pool (engine)
with engine.begin() as conn:
    # 'SET' only applies to one exact connection, so we have to keep all the commands in a single connection.
    # removes the requirement for primary key
    conn.execute(text("SET SESSION sql_require_primary_key = 0;"))
    # converts pandas to SQL
    df.to_sql(name='listening_history', con=conn, if_exists='replace', index=False)
    # create a column and makes it a primary key, now each individual song played, has an id.
    conn.execute(text("ALTER TABLE listening_history ADD COLUMN id INT AUTO_INCREMENT PRIMARY KEY FIRST;"))
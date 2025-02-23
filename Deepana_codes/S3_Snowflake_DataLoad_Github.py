import snowflake.connector
import pandas as pd
import numpy as np

conn= snowflake.connector.connect(
    user='BOA',
    password='',
    account='PDB57018',
    warehouse='ANIMAL_TASK_WH',
    database='STREET_FAIRY',
    schema='PUBLIC'
)



table_name='Business_test'



cur=conn.cursor()

query = """
COPY INTO Business_test
    FROM @my_s3_stage_Business_test/top5_states_businesses.csv
    FILE_FORMAT = (
        TYPE = 'CSV'
        FIELD_OPTIONALLY_ENCLOSED_BY = '"',  -- Handle quoted fields
        SKIP_HEADER = 1
    );
"""

#query=f"select top 5 * from {table_name}"

cur.execute(query)

conn.commit()

cur.close()
conn.close()

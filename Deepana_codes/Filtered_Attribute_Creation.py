import snowflake.connector
import pandas as pd
import numpy as np
import json

conn= snowflake.connector.connect(
    user='BOA',
    password='Kavinkumar3006$',
    account='PDB57018',
    warehouse='ANIMAL_TASK_WH',
    database='STREET_FAIRY',
    schema='PUBLIC'
)

cur = conn.cursor()

query=r"select  * from final_attribute_model where( upper(attribute_value) not like '%FALSE%' and upper(attribute_value)<>'NONE' and upper(attribute_value)<>'NO' and attribute_value<>'{}'  AND LOWER(attribute_name) NOT LIKE '%restaurantspricerange%')"

df = pd.read_sql(query, conn)

df_aggregated = df.groupby("BUSINESS_ID").apply(
    lambda x: dict(zip(x["ATTRIBUTE_NAME"], x["ATTRIBUTE_VALUE"]))
).reset_index(name="ATTRIBUTES")

data_tuples = [(row["BUSINESS_ID"], json.dumps(row["ATTRIBUTES"])) for _, row in df_aggregated.iterrows()]

query1=r"INSERT INTO PUBLIC.Filtered_Attributes (BUSINESS_ID, ATTRIBUTES) VALUES (%s, %s)"

cur.executemany(query1, data_tuples)
conn.commit()
cur.close() 
conn.close()


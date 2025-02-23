use street_fairy
---fILE FORMAT CREATION
CREATE OR REPLACE FILE FORMAT my_csv_format
TYPE = 'CSV'
FIELD_OPTIONALLY_ENCLOSED_BY='"'
SKIP_HEADER=1;
--STAGE NAME CREATION
CREATE OR REPLACE STAGE my_s3_stage_Business_test
URL = 's3://bucket_name/'
CREDENTIALS = (AWS_KEY_ID = '' AWS_SECRET_KEY = '') --Replace ''  with AWS_KEY_ID AND AWS_SECRET_KEY
FILE_FORMAT = my_csv_format;

LIST @my_s3_stage_Business_test;


CREATE TABLE Business_test (
    ID INT PRIMARY KEY,
    business_id STRING,
    name STRING,
    address STRING,
    city STRING,
    state STRING,
    postal_code STRING,
    latitude FLOAT,
    longitude FLOAT,
    stars FLOAT,
    review_count INT,
    is_open BOOLEAN,
    attributes VARIANT,
    categories STRING,
    hours STRING
);

SELECT CURRENT_DATABASE(), CURRENT_SCHEMA();







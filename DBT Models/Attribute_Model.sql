{{ config(materialized='table') }}
WITH parsed_data AS (
    SELECT 
        business_id, 
        PARSE_JSON(Attributes) AS attributes_json
    FROM Business
    where is_open='1'
    and STATE IN ('PA','FL','TN','IN','MO')
),
Attribute_Model AS (
    SELECT 
        business_id,
        f.key AS attribute_name,         
        f.value AS attribute_value,
    FROM parsed_data,
    LATERAL FLATTEN(input => attributes_json) f
    
)
select * from Attribute_Model
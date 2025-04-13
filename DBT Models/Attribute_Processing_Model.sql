{{ config(materialized='table') }}

WITH Attribute AS (
    SELECT 
        business_id, 
        attribute_name,
        PARSE_JSON(
            REPLACE(
                REPLACE(
                    REPLACE(attribute_value, '''', '"'), 
                    'None', 'null'                        
                ), 
                'u"', '"')                        
        ) AS attributes_json
    FROM Attribute_Model  -- Reference the model correctly
    WHERE attribute_value LIKE '%,%'  -- Filter records that have commas in attribute_value
),

Attribute_Processing_Model AS (
    SELECT 
        business_id,
        CONCAT(attribute_name, '_', f.key) AS attribute_name,  -- Dynamically concatenate attribute name and key
        f.value AS attribute_value  -- Extract corresponding values
    FROM Attribute,
    LATERAL FLATTEN(input => attributes_json) f
)

SELECT * 
FROM Attribute_Processing_Model
WHERE attribute_value <>'null'

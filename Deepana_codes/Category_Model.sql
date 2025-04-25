
-- Use the `ref` function to select from other models

{{ config(materialized='table') }}

with Category_Model as (

    SELECT b.business_id, TRIM(f.VALUE) AS Categories
    FROM Business b,
    LATERAL FLATTEN(input => SPLIT(b.CATEGORIES, ',')) f
    where is_open='1'
    and STATE IN ('PA','FL','TN','IN','MO')
)

select *
from Category_Model
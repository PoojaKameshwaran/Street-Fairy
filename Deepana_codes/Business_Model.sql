
/*
    Welcome to your first dbt model!
    Did you know that you can also configure models directly within SQL files?
    This will override configurations stated in dbt_project.yml

    Try changing "table" to "view" below
*/

{{ config(materialized='table') }}

with Business_Model as (

    select 
    business_id,
    Name,
    ADDRESS,
    city,
    state,
    Postal_code,
    LATITUDE,
    LONGITUDE,
    stars,
    REVIEW_COUNT,
    hours:Monday::STRING as Monday,
    hours:Tuesday::STRING as Tuesday,
    hours:Wednesday::STRING as Wednesday,
    hours:Thursday::STRING as Thursday,
    hours:Friday::STRING as Friday,
    hours:Saturday::STRING as Saturday,
    hours:Sunday::STRING as Sunday
    from Business
    where is_open='1'
    and STATE IN ('PA','FL','TN','IN','MO')

)

select *
from Business_Model

/*
    Uncomment the line below to remove records with null `id` values
*/

-- where id is not null

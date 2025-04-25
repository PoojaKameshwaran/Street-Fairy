
WITH ATTRIBUTE as 
(
 SELECT business_id,attribute_name , 
 replace(replace(ATTRIBUTE_VALUE,'""',''),'u''none''','Invalid')as attribute_value
 FROM ATTRIBUTE_MODEL
 where attribute_value not like '%,%'
), Attribute_Preprocessed as
(
    select * from Attribute_Processing_Model
), a as
(
select * from ATTRIBUTE
where attribute_value<>'Invalid'
union all
select * from Attribute_Processing_Model
)
select business_id,attribute_name,replace(replace (attribute_value,'u''',''),'''','') as attribute_value
from a
where NOT ILIKE(CAST(attribute_value AS STRING), 'none')
    AND NOT ILIKE(CAST(attribute_value AS STRING), 'None')
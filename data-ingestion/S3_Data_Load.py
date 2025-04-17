import boto3
import pandas as pd

s3= boto3.resource(
    service_name='s3',
    region_name='us-east-2',
    aws_access_key_id='',
    aws_secret_access_key=''
)

for buckets in s3.buckets.all(): #display buckets 
   print(buckets.name)

filelocation=r'C:\Users\deepa\Documents\Northeastern_Sem_3\DAMG7374\Project\yelp_dataset\top5_states_businesses.csv'
s3_object_key = 'top5_states_businesses.csv'
s3.Bucket('damgbusinesspractice').upload_file(Filename=filelocation, Key=s3_object_key)

for obj in s3.Bucket('damgbusinesspractice').objects.all():
    print(obj)
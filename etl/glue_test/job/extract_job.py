# import boto3

# glue = boto3.client('glue', region_name='ap-southeast-1')

# if not glue.get_job(JobName='extract_job'):
#     glue.create_job(
#         Name='extract_job',
#         Role='AWSGlueServiceRoleDefault',
#         Command={
#             'Name': 'glueetl',
#             'ScriptLocation': 's3://your-script-location/extract_job.py',
#             'PythonVersion': '3'
#         },
#         DefaultArguments={
#             '--TempDir': 's3://your-temp-dir/',
#             '--job-language': 'python'
#         },
#         MaxRetries=0,
#         GlueVersion='2.0',      
#         NumberOfWorkers=2,
#         WorkerType='Standard'
#     )   

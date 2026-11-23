import boto3

glue = boto3.client("glue", region_name= "ap-southeast-1")

if not glue.get_workflow(Name="auto_extract_workflow"):
    glue.create_workflow(
        Name="auto_extract_workflow",
        Description="Workflow for daily auto extract job"
    )

response = glue.create_trigger(
    Name="daily_auto_extract_trigger",
    WorkflowName="auto_extract_workflow",
    Type="SCHEDULED",
    Schedule="cron(0 18 * * ? *)",
    Actions=[
        {
            "JobName": "extract_job"
        }
    ],
    StartOnCreation=True,
    Description="Trigger for daily auto extract job"
)



# import boto3
# from botocore.exceptions import ClientError

# glue = boto3.client(
#     "glue",
#     region_name="ap-southeast-1"
# )

# job_name = "extract_job"
# trigger_name = "daily_auto_extract_trigger"

# try:
#     # Bước 1: Kiểm tra Job tồn tại
#     glue.get_job(JobName=job_name)

#     print(f"Job '{job_name}' đã tồn tại.")

#     # Bước 2: Tạo Trigger
#     response = glue.create_trigger(
#         Name=trigger_name,
#         Type="SCHEDULED",
#         Schedule="cron(0 18 * * ? *)",
#         Actions=[
#             {
#                 "JobName": job_name
#             }
#         ],
#         StartOnCreation=True
#     )

#     print(f"Tạo Trigger '{response['Name']}' thành công.")

# except glue.exceptions.EntityNotFoundException:
#     print(f"Job '{job_name}' không tồn tại.")

# except glue.exceptions.AlreadyExistsException:
#     print(f"Trigger '{trigger_name}' đã tồn tại.")

# except ClientError as e:
#     print(f"Lỗi AWS: {e}")

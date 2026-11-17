data "aws_vpc" "default" {
    default= true
}

# resource "aws_security_group" "sg-demo-frontend" {
#     name = "sg-frontend-test-tag"
#     description = "Demo test tag frontend"
#     vpc_id=data.aws_vpc.test.id

#     tags= {
#         Name= "frontend-demo-tag"
#     }
# }
# resource "aws_security_group" "sg-demo-backend" {
#     name = "sg-backend-test-tag"
#     description = "Demo-test-tag-backend"
#     vpc_id=data.aws_vpc.test.id
#     tag = {
#         Name = "backend-demo-tag"
#     }
# }
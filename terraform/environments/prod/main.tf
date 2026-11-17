module "network" {
  source = "../../modules/network"

  project_name = local.project_name
  environment  = local.environment

  vpc_cidr = "10.20.0.0/16"

  availability_zones = [
    "${var.aws_region}a",
    "${var.aws_region}b"
  ]

  public_subnet_cidrs = [
    "10.20.1.0/24",
    "10.20.2.0/24"
  ]

  private_subnet_cidrs = [
    "10.20.11.0/24",
    "10.20.12.0/24"
  ]

  nat_gateway_mode = "per_az"

  common_tags = local.common_tags
}

module "security" {
  source = "../../modules/security"

  project_name = local.project_name
  environment  = local.environment

  vpc_id = module.network.vpc_id

  frontend_node_port = 30080
  backend_node_port  = 30081

  common_tags = local.common_tags
}

module "iam" {
  source = "../../modules/iam"

  project_name = local.project_name
  environment  = local.environment

  common_tags = local.common_tags
}


module "kubernetes" {
  source = "../../modules/kubernetes"

  project_name = local.project_name
  environment  = local.environment
  aws_region   = var.aws_region


  cluster_name = "${local.project_name}-${local.environment}-k8s"

  vpc_id = module.network.vpc_id

  private_subnet_ids = module.network.private_subnet_ids

  control_plane_sg_id = module.security.control_plane_sg_id
  worker_sg_id        = module.security.worker_sg_id

  control_plane_role_name = module.iam.control_plane_role_name
  worker_role_name        = module.iam.worker_role_name

  control_plane_instance_profile_name = module.iam.control_plane_instance_profile_name
  worker_instance_profile_name        = module.iam.worker_instance_profile_name

  control_plane_instance_type = "t3.medium"
  worker_instance_type        = "t3.medium"

  worker_min_size         = 1
  worker_desired_capacity = 2
  worker_max_size         = 4

  common_tags = local.common_tags

  depends_on = [module.iam, module.security]
}


module "alb" {
  source = "../../modules/alb"

  project_name = local.project_name
  environment  = local.environment

  vpc_id            = module.network.vpc_id
  public_subnet_ids = module.network.public_subnet_ids

  alb_sg_id       = module.security.alb_sg_id
  worker_asg_name = module.kubernetes.worker_asg_name

  frontend_node_port = 30080
  backend_node_port  = 30081

  frontend_health_path = "/"
  backend_health_path  = "/health"

  enable_https    = true
  certificate_arn = var.acm_certificate_arn

  common_tags = local.common_tags
}


module "database" {
  source = "../../modules/database"

  project_name = local.project_name
  environment  = local.environment

  private_subnet_ids = module.network.private_subnet_ids

  rds_sg_id = module.security.rds_sg_id

  db_name     = "coco_marketplace"
  db_username = "coco_admin"

  db_instance_class = "db.t4g.small"

  allocated_storage     = 20
  max_allocated_storage = 200

  multi_az = true

  backup_retention_period = 7

  deletion_protection = true
  skip_final_snapshot = false

  apply_immediately = false

  common_tags = local.common_tags
}


module "storage" {
  source = "../../modules/storage"

  project_name = local.project_name
  environment  = local.environment

  noncurrent_version_days = 90

  common_tags = local.common_tags
}


module "ecr" {
  source = "../../modules/ecr"

  project_name = local.project_name
  environment  = local.environment

  image_tag_mutability = "IMMUTABLE"
  scan_on_push         = true

  untagged_image_days = 14
  max_tagged_images   = 50

  common_tags = local.common_tags
}


module "cloudfront" {
  source = "../../modules/cloudfront"

  project_name = local.project_name
  environment  = local.environment

  images_bucket_name = module.storage.images_bucket_name

  images_bucket_arn = module.storage.images_bucket_arn

  images_bucket_domain_name = module.storage.images_bucket_regional_domain_name

  price_class = "PriceClass_100"

  common_tags = local.common_tags
}

module "monitoring" {
  source = "../../modules/monitoring"

  project_name = local.project_name
  environment  = local.environment
  aws_region   = var.aws_region

  worker_asg_name = module.kubernetes.worker_asg_name
  worker_min_size = 1

  alb_arn_suffix = module.alb.alb_arn_suffix

  backend_target_group_arn_suffix = (
    module.alb.backend_target_group_arn_suffix
  )

  db_instance_identifier = module.database.db_instance_id

  rds_cpu_threshold         = 80
  alb_5xx_threshold         = 10
  backend_latency_threshold = 2

  common_tags = local.common_tags
}

module "etl" {
  source = "../../modules/etl"

  project_name = local.project_name
  environment  = local.environment
  aws_region   = var.aws_region

  # Network
  vpc_id         = module.network.vpc_id
  glue_subnet_id = module.network.private_subnet_ids[0]

  # Security
  rds_security_group_id = module.security.rds_sg_id

  # PostgreSQL
  db_host       = module.database.db_address
  db_port       = module.database.db_port
  db_name       = module.database.db_name
  db_secret_arn = module.database.db_master_secret_arn

  # S3 Data Lake
  etl_bucket_name = module.storage.etl_bucket_name
  etl_bucket_arn  = module.storage.etl_bucket_arn

  # Glue Spark
  glue_version      = "5.0"
  worker_type       = "G.1X"
  number_of_workers = 2
  job_timeout       = 30

  common_tags = local.common_tags
}

# Image storage permissions

Baseline: IAM Policy Autopilot output supplied by the owner for
`backend/app/services/storage.py`, account `858525799322`, region `ap-southeast-1`.
The baseline was reviewed and narrowed before implementing `images.tf`.

The optional `worker_images` inline policy grants only `s3:GetObject` and
`s3:PutObject`, scoped to `uploads/*`, `product-images/*`, `shop-logos/*` within the
exact configured image bucket. It grants no delete, list-buckets, ACL, Object Lock,
Object Lambda or KMS permissions. The bucket is configured for SSE-S3 and
BucketOwnerEnforced. HEAD uses GetObject permission; presigned requests still need
the signing identity to have the corresponding S3 permissions.

This policy includes the planned logo storage prefixes but does not implement
logo upload APIs. Existing legacy objects in other prefixes or buckets are not
covered by the write statement. A separate GetObject-only statement now covers
the three known `ProductImages/{shop}/*` prefixes and exact keys `logo/1.png`,
`logo/2.png`, `logo/3.png` for the owner's manual catalog import. It grants no
legacy writes. Backend now signs validated existing logo keys; public and seller
shop responses expose only the URL, not the raw key. Logo upload APIs remain separate work.
No images or DB references are copied or rewritten by this module.

Only dev enables shared worker image access. All Pods that can obtain the node
role credentials share those permissions. Dev explicitly sets worker IMDSv2 hop
limit 2 for Pod networking; tokens remain required. Prod keeps access disabled
and hop limit 1 until a separate workload identity design is implemented.
Do not put permanent access keys in the backend image or ConfigMap.

Updating the node role policy affects current workers after IAM propagation.
Updating a launch template does not change metadata settings on existing workers.
Inspect current metadata settings before giving commands to modify instances;
do not replace workers or apply unrelated EC2/bootstrap changes just to add S3 access.

Owner-run checks, from the repository root:

```sh
terraform -chdir=terraform/environments/dev validate
terraform -chdir=terraform/environments/dev test -filter=tests/image_permissions.tftest.hcl
```

The mock tests check exact actions, bucket prefixes, target role and the disabled
default. No test or AWS command was run by the agent when preparing this change.

For the current S3 repair, inspect a plan targeting
`module.iam.aws_iam_role_policy.worker_images` and
`module.cloudfront.aws_s3_bucket_policy.images`. Targeting is for this repair only,
not the routine deployment workflow; review dependencies and stop if it would
modify the database, delete resources or replace machines. Plan and apply are
owner actions, not actions performed by the agent.

References: [HeadObject permissions](https://docs.aws.amazon.com/AmazonS3/latest/API/API_HeadObject.html),
[PutObject permissions](https://docs.aws.amazon.com/AmazonS3/latest/API/API_PutObject.html),
[IMDS options](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-instance-metadata-options.html).

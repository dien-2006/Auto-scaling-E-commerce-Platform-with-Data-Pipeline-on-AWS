# COCO — Kubernetes on AWS EC2 (self-managed kubeadm)

This folder is Kubernetes workload configuration, NOT AWS infrastructure.
Terraform owns the EC2 control plane, worker ASG, ALB, S3, ECR, RDS and IAM.
Use a separate kubeconfig/context for dev and prod clusters.

## Hướng dẫn theo thư mục

Các lệnh bên dưới chạy từ **gốc repo**. Cần `kubectl`, Helm, context `coco-dev`/`coco-prod` và đường mạng tới Kubernetes API private. Không có lệnh build ứng dụng trong repo vì chưa có source/Dockerfile ứng dụng.

| Phần | Hướng dẫn |
| --- | --- |
| Ứng dụng dev | [overlays/dev](overlays/dev/README.md) |
| Ứng dụng prod | [overlays/prod](overlays/prod/README.md) |
| Manifest dùng chung | [base](base/README.md) |
| Metrics Server cho HPA | [metrics-server](metrics-server/README.md) |
| Autoscaling worker EC2 | [autoscaling](autoscaling/README.md) |
| Prometheus/Grafana | [monitoring](monitoring/README.md) |

`kubectl kustomize` chỉ render cục bộ. `kubectl apply` và `helm upgrade --install` thay đổi cluster thật. Chuẩn bị đầy đủ các điều kiện bên dưới trước khi chạy các bước cài.

## Prerequisites
- `kubectl get nodes` shows Ready kubeadm nodes, Flannel/CoreDNS healthy; `kubectl top nodes` works.
- Kubelet can authenticate and pull private ECR images using a credential provider.
- EC2 worker ASG is correctly tagged for Cluster Autoscaler and worker role has required AWS permissions.
- ALB instance target groups connect to worker NodePorts 30080/30081 with matching SG rules and health check paths.
- Replace `ACCOUNT_ID` in both overlays with the actual AWS account ID, and push the referenced `v1.0.0` images. Repository paths match Terraform: `ecommerce/dev/frontend`, `ecommerce/dev/backend`, `ecommerce/prod/frontend`, `ecommerce/prod/backend`. Confirm the full URIs against `terraform output -raw ecr_frontend_url` and `terraform output -raw ecr_backend_url` in the corresponding environment.
- Backend Secret `coco-backend-secret` must be created in each cluster before deploying the backend. The sample environment file contains placeholders, not usable credentials.
- If Kubernetes API is private, execute commands from a machine connected securely to the VPC.

## 0. Install Metrics Server before enabling HPA

The pinned Metrics Server v0.9.1 manifest supports the Kubernetes 1.34 cluster defined in Terraform. It is a separate cluster add-on and is not included in the `coco` application overlays. Prometheus is not a replacement for the `metrics.k8s.io` API used by these HPAs.

```bash
kubectl --context coco-dev apply -k k8s/metrics-server/dev
kubectl --context coco-dev -n kube-system rollout status deployment/metrics-server
kubectl --context coco-dev wait --for=condition=Available apiservice/v1beta1.metrics.k8s.io --timeout=180s
kubectl --context coco-dev top nodes
```

Dev uses a lab-only kubelet TLS verification bypass. Prod verifies certificates and requires cluster-CA-signed kubelet serving certificates with InternalIP SANs before installing `k8s/metrics-server/prod`. The existing Terraform bootstrap does not provision those certificates. See [Metrics Server installation and TLS prerequisites](metrics-server/README.md).

## 1. Before applying workloads: create backend Secret (per cluster)
`cp k8s/backend-secret.env.example k8s/backend-secret.env`, edit only the local copy.
The real env variable names MUST match your actual backend.

```bash
kubectl --context coco-dev apply -f k8s/base/namespace.yaml
kubectl --context coco-dev -n coco create secret generic coco-backend-secret   --from-env-file=k8s/backend-secret.env --dry-run=client -o yaml   | kubectl --context coco-dev apply -f -
```

This command can expose Secret data in command output/pipelines; use a protected workstation and never commit the generated Secret. Kubernetes Secrets are not a substitute for encryption-at-rest and IAM controls. Repeat separately for prod.

## 2. Deploy application

| Application | Minimum Pods | Maximum Pods | CPU target | Scale-down stabilization |
| --- | --- | --- | --- | --- |
| Frontend | 2 | 4 | 60% of CPU request | 300 seconds |
| Backend | 2 | 10 | 60% of CPU request | 300 seconds |

HPA owns Deployment replicas; application manifests intentionally omit `spec.replicas`. On a new installation, the Deployment may briefly start with the default one replica before HPA reconciles it to its minimum of two. Install and verify Metrics Server first.

### Existing deployments: transfer replica ownership once

If you previously applied these Deployments with `replicas: 2`, first remove **only** `spec.replicas` from each Deployment's last-applied configuration using:

```bash
kubectl --context coco-dev -n coco apply edit-last-applied deployment/coco-frontend
kubectl --context coco-dev -n coco apply edit-last-applied deployment/coco-backend
```

Repeat with `--context coco-prod` for existing production Deployments. Do this before applying the updated manifests: simply dropping `replicas` from a previously applied manifest can otherwise cause a one-time reset to the Deployment default. Follow [Kubernetes' HPA migration instructions](https://kubernetes.io/docs/concepts/workloads/autoscaling/horizontal-pod-autoscale/#migrating-deployments-and-statefulsets-to-horizontal-autoscaling).

### Apply the application
```bash
kubectl kustomize k8s/overlays/dev
kubectl --context coco-dev apply -k k8s/overlays/dev
kubectl --context coco-dev -n coco rollout status deploy/coco-frontend
kubectl --context coco-dev -n coco rollout status deploy/coco-backend
kubectl --context coco-dev get pods -n coco -o wide
kubectl --context coco-dev get svc,hpa,pdb -n coco
```
Use a separate `coco-prod` context and `k8s/overlays/prod` for prod.

## 3. Install Cluster Autoscaler via Helm
The official autoscaler chart supports AWS ASG tag auto-discovery. Values now match Terraform's ASG tags: `ecommerce-dev-k8s` and `ecommerce-prod-k8s`. These cluster names are separate from local kubeconfig context names (`coco-dev` and `coco-prod`).

Before installing the chart, verify the following infrastructure prerequisites; installing this Helm chart does not supply them:

- The identity used by the Autoscaler can read ASG/EC2 metadata and change only this cluster's worker ASG. The current Terraform worker role grants SSM/ECR/bootstrap access, not the required ASG scaling actions.
- Nodes expose AWS provider IDs (`aws:///AZ/INSTANCE_ID`) so the Autoscaler can associate them with EC2 instances. The current kubeadm bootstrap does not configure these explicitly.
- If the pod uses an EC2 role, IMDS credentials must be reachable from the pod. Terraform requires IMDSv2; do not assume a normal pod can use instance credentials with the default hop limit. Use a suitable dedicated identity or deliberately configured placement/networking.
- The Autoscaler image version matches Kubernetes 1.34, and outbound AWS API connectivity works.

See the [upstream AWS Autoscaler prerequisites](https://github.com/kubernetes/autoscaler/blob/master/cluster-autoscaler/cloudprovider/aws/README.md). This change fixes Kubernetes configuration names and leaves AWS architecture/IAM unchanged.

```bash
helm repo add autoscaler https://kubernetes.github.io/autoscaler
helm repo update
helm --kube-context coco-dev upgrade --install cluster-autoscaler   autoscaler/cluster-autoscaler   --namespace kube-system -f k8s/autoscaling/values-dev.yaml   --set image.tag=v1.34.0
kubectl --context coco-dev -n kube-system get deploy -l app.kubernetes.io/instance=cluster-autoscaler
```

**Version note:** The image tag is an example for a Kubernetes v1.34 cluster; verify the exact matching supported patch and chart version. This self-managed kubeadm cluster also needs an appropriate AWS integration/provider-id and IAM; the Helm command alone will not activate AWS autoscaling.

## 4. Install Prometheus + Grafana via Helm
This sample uses ephemeral monitoring storage. Production must configure a functioning persistent StorageClass (e.g. EBS CSI) before turning on PVCs, otherwise dashboards/data are lost on rescheduling.

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
kubectl --context coco-dev create namespace monitoring --dry-run=client -o yaml | kubectl --context coco-dev apply -f -
# Create grafana-admin Secret in monitoring first using a secure method
helm --kube-context coco-dev upgrade --install monitoring   prometheus-community/kube-prometheus-stack   --namespace monitoring -f k8s/monitoring/values-dev.yaml
kubectl --context coco-dev -n monitoring port-forward svc/monitoring-grafana 3001:80
```

## 5. Test autoscaling
```bash
kubectl --context coco-dev -n coco get hpa -w
kubectl --context coco-dev get nodes -w
kubectl --context coco-dev -n kube-system logs -l app.kubernetes.io/instance=cluster-autoscaler --all-containers=true --tail=100
```
For a true autoscaling demo, use k6 to increase application CPU usage, verify HPA adds pods, then verify Pending unschedulable pods prompt Cluster Autoscaler to increase the worker ASG. HPA CPU decisions require Metrics Server and appropriate CPU requests.

## Notes
- Deployments use example frontend port 80 and backend 3000 `/health`: align with the real Docker images.
- `/api/*` ALB routing is handled by Terraform. If frontend needs browser API requests, use `/api` via same ALB domain.
- Not a fully HA control plane: single EC2 control-plane is a single point of failure.
- For real multi-AZ resilience, confirm subnet placement, node labels, storage and AZ topology requirements; `topologySpreadConstraints` here use `ScheduleAnyway` preference.
- Prometheus/Grafana are installed in Kubernetes, not Terraform. Glue ETL is separate from this folder.

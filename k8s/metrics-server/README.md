# Metrics Server

Pinned upstream manifest: [metrics-server v0.9.1](https://github.com/kubernetes-sigs/metrics-server/releases/tag/v0.9.1).
Supports Kubernetes 1.34+ as configured in Terraform. `base/components.yaml` is the unmodified upstream `components.yaml`.

Upstream SHA-256: `3c7f57cdbee0f57fb0259a150e8f6d6cb4f29d72d1aa5dce8803151dd6d4c2a1`.

Install this add-on separately from application overlays: it owns cluster-scoped RBAC/APIService and runs in `kube-system`, while the applications run in `coco`.

```sh
kubectl --context coco-dev apply -k k8s/metrics-server/dev
kubectl --context coco-dev -n kube-system rollout status deployment/metrics-server
kubectl --context coco-dev wait --for=condition=Available apiservice/v1beta1.metrics.k8s.io --timeout=180s
kubectl --context coco-dev top nodes
```

The patch runs Metrics Server on the existing control plane with `hostNetwork` and TCP 10251. This lets it scrape kubelets on TCP 10250 through the existing Terraform security group rules without adding AWS resources or opening another security group rule. `Recreate` avoids two Metrics Server replicas trying to bind the same host port during upgrades; metrics will briefly pause during an upgrade.

The dev overlay uses `--kubelet-insecure-tls` for this kubeadm lab's self-signed kubelet certificates. This disables certificate verification only on the Metrics Server -> kubelet connection; it is for testing, not the production configuration.

The prod overlay verifies kubelet certificates against the cluster CA. Before installing it, provide CA-signed kubelet serving certificates with the node InternalIP in their SANs. The existing Terraform bootstrap does not configure these automatically. With kubeadm, configure `serverTLSBootstrap: true` and establish a process to validate/approve `kubernetes.io/kubelet-serving` CSRs; do not approve unidentified requests. See [kubeadm kubelet serving certificate instructions](https://kubernetes.io/docs/tasks/administer-cluster/kubeadm/kubeadm-certs/#kubelet-serving-certs).

After that prerequisite is satisfied:

```sh
kubectl --context coco-prod apply -k k8s/metrics-server/prod
kubectl --context coco-prod -n kube-system rollout status deployment/metrics-server
kubectl --context coco-prod wait --for=condition=Available apiservice/v1beta1.metrics.k8s.io --timeout=180s
kubectl --context coco-prod top nodes
```

Both clusters still require a functioning Pod network, API aggregation and kubelet webhook authentication/authorization. These are prerequisites, not components installed by this folder. See [upstream requirements](https://github.com/kubernetes-sigs/metrics-server/blob/v0.9.1/README.md#requirements).

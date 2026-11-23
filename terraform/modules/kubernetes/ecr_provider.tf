locals {
  # Reuse the same reviewed source for first boot and repairs of existing nodes.
  ecr_provider_bootstrap = join("\n", [
    "install -d -m 0755 /usr/local/libexec/kubelet-credential-providers",
    "cat > /usr/local/libexec/kubelet-credential-providers/coco-ecr-credential-provider <<'COCO_ECR_PROVIDER'",
    file("${path.module}/../../../scripts/k8s/ecr-credential-provider.py"),
    "COCO_ECR_PROVIDER",
    "chmod 0755 /usr/local/libexec/kubelet-credential-providers/coco-ecr-credential-provider",
    "/usr/local/libexec/kubelet-credential-providers/coco-ecr-credential-provider --install"
  ])
}

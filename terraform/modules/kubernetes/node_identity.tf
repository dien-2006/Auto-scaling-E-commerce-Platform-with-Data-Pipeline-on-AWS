locals {
  # Shared first-boot source; derive identity from IMDS instead of hardcoding IDs.
  node_identity_bootstrap = join("\n", [
    "install -d -m 0755 /usr/local/sbin",
    "cat > /usr/local/sbin/coco-configure-aws-node <<'COCO_AWS_NODE'",
    file("${path.module}/../../../scripts/k8s/configure-aws-node.sh"),
    "COCO_AWS_NODE",
    "chmod 0755 /usr/local/sbin/coco-configure-aws-node",
    "/usr/local/sbin/coco-configure-aws-node"
  ])
}

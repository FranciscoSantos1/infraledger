resource "aws_eks_cluster" "main" {
    name = "infraledger-cluster"
    role_arn = aws_iam_role.eks_cluster.arn
    version = "1.31"

    vpc_config {
        subnet_ids               = [aws_subnet.public.id, aws_subnet.private_a.id]
        endpoint_public_access   = true
        endpoint_private_access  = false
    }

    depends_on = [
        aws_iam_role_policy_attachment.eks_cluster_policy
    ]

    tags = {
        Name = "infraledger-cluster"
    }
}

resource "aws_eks_node_group" "main" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "infraledger-nodes"
  node_role_arn   = aws_iam_role.eks_node.arn
  subnet_ids      = [aws_subnet.public.id]

  launch_template {
    id      = aws_launch_template.eks_nodes.id
    version = "$Latest"
  }

  scaling_config {
    desired_size = 1
    max_size     = 1
    min_size     = 1
  }

  depends_on = [
    aws_iam_role_policy_attachment.eks_node_worker_policy,
    aws_iam_role_policy_attachment.eks_node_cni_policy,
    aws_iam_role_policy_attachment.eks_node_ecr_policy,
  ]

  tags = {
    Name = "infraledger-node"
  }
}

output "eks_cluster_endpoint" {
  value = aws_eks_cluster.main.endpoint
}
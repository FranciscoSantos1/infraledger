resource "aws_security_group" "web" {
  name        = "infraledger-web-sg"
  description = "Allows SSH from my IP, HTTP/HTTPS from anywhere"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "SSH open for CI/CD"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "infraledger-web-sg"
  }
}

resource "aws_security_group" "database" {
  name        = "infraledger-db-sg"
  description = "Allows Postgres from the web SG and EKS nodes"
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Postgres from web SG and EKS nodes"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [
      aws_security_group.web.id,
      aws_eks_cluster.main.vpc_config[0].cluster_security_group_id,
    ]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "infraledger-db-sg"
  }
}

resource "aws_security_group" "eks_node_access" {
  name        = "infraledger-eks-node-access-sg"
  description = "Allows reaching NodePort services from outside the cluster"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "Kubernetes NodePort range"
    from_port   = 30000
    to_port     = 32767
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "infraledger-eks-node-access-sg"
  }
}

resource "aws_launch_template" "eks_nodes" {
  name = "infraledger-eks-node-template"
  instance_type = "t3.small"

  vpc_security_group_ids = [
    aws_security_group.eks_node_access.id, # to have access from outside
    aws_eks_cluster.main.vpc_config[0].cluster_security_group_id, # to still  get the eks manage the node's networking
  ]

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "infraledger-eks-node"
    }
  }
}

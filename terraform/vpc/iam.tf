resource "aws_iam_role" "ec2_pricing" {
  name = "infraledger-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "infraledger-ec2-role"
  }
}

resource "aws_iam_role_policy" "pricing_api_access" {
  name = "infraledger-pricing-api-access"
  role = aws_iam_role.ec2_pricing.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "pricing:GetProducts",
          "pricing:DescribeServices",
          "pricing:GetAttributeValues"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_instance_profile" "ec2_pricing" {
  name = "infraledger-ec2-instance-profile"
  role = aws_iam_role.ec2_pricing.name
}

resource "aws_iam_role" "github_actions" {
  name = "infraledger-github-actions"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        }
        Action = ["sts:AssumeRoleWithWebIdentity", "sts:TagSession"]
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:FranciscoSantos1/infraledger:*"
          }
        }
      }
    ]
  })

  tags = {
    Name = "infraledger-github-actions"
  }
}

resource "aws_iam_role_policy" "github_actions_ecr" {
  name = "infraledger-github-actions-ecr-push"
  role = aws_iam_role.github_actions.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "ecr:GetAuthorizationToken"
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload"
        ]
        Resource = aws_ecr_repository.api.arn
      }
    ]
  })
}

output "github_actions_role_arn" {
  value = aws_iam_role.github_actions.arn
  
}
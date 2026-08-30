resource "aws_cloudwatch_log_group" "app_logs" {
    name = "/eks/infraledger/application"
    retention_in_days = 7

    tags = {
        Name = "infraledger-app-logs"
    } 
}

resource "aws_iam_role" "fluent_bit" {
  name = "infraledger-fluent-bit-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = aws_iam_openid_connect_provider.eks.arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:sub" = "system:serviceaccount:kube-system:fluent-bit"
            "${replace(aws_iam_openid_connect_provider.eks.url, "https://", "")}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "fluent_bit_cloudwatch" {
  name = "infraledger-fluent-bit-cloudwatch-access"
  role = aws_iam_role.fluent_bit.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "${aws_cloudwatch_log_group.app_logs.arn}:*"
      }
    ]
  })
}

output "fluent_bit_role_arn" {
  value = aws_iam_role.fluent_bit.arn
}
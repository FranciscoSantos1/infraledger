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
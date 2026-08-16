resource "aws_key_pair" "main" {
  key_name   = "infraledger-key"
  public_key = file("~/.ssh/infraledger-key.pub")
}

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical's official AWS account

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "main" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"

  subnet_id                  = aws_subnet.public.id
  vpc_security_group_ids     = [aws_security_group.web.id]
  iam_instance_profile       = aws_iam_instance_profile.ec2_pricing.name
  key_name                   = aws_key_pair.main.key_name
  associate_public_ip_address = true

  user_data = <<-EOF
    #!/bin/bash
    apt-get update -y
    apt-get install -y docker.io docker-compose-v2
    systemctl enable docker
    systemctl start docker
    usermod -aG docker ubuntu
  EOF

  tags = {
    Name = "infraledger-api-server"
  }
}

output "instance_public_ip" {
  value = aws_instance.main.public_ip
}
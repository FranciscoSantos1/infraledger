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
    set -e 

    apt-get update -y
    apt-get install -y docker.io docker-compose-v2
    systemctl enable docker
    systemctl start docker
    usermod -aG docker ubuntu
    
    sudo -u ubuntu git clone https://github.com/FranciscoSantos1/infraledger.git /home/ubuntu/infraledger

    cat > /home/ubuntu/infraledger/docker-compose.yml <<'COMPOSE_EOF'
    services:
      api:
        image: ${aws_ecr_repository.api.repository_url}:latest
        container_name: infraledger-api
        restart: always
        ports:
          - "5000:5000"
        environment:
          DATABASE_URL: postgresql://infraledger:${random_password.db_password.result}@${aws_db_instance.main.endpoint}/infraledger
          AWS_REGION: eu-west-1
          AWS_PRICING_API_REGION: us-east-1
    COMPOSE_EOF

    chown ubuntu:ubuntu /home/ubuntu/infraledger/docker-compose.yml

    aws ecr get-login-password --region eu-west-1 | docker login --username AWS --password-stdin ${aws_ecr_repository.api.repository_url}

    cd /home/ubuntu/infraledger
    sudo -u ubuntu docker compose pull
    sudo -u ubuntu docker compose up -d
    sleep 10
    sudo -u ubuntu docker compose exec -T api python -m flask --app wsgi db upgrade
  EOF

  tags = {
    Name = "infraledger-api-server"
  }
}

output "instance_public_ip" {
  value = aws_instance.main.public_ip
}
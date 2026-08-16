resource "random_password" "db_password" {
  length           = 24
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "eu-west-1a"

  tags = {
    Name = "infraledger-private-subnet-a"
  }
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.3.0/24"
  availability_zone = "eu-west-1b"

  tags = {
    Name = "infraledger-private-subnet-b"
  }
}

resource "aws_db_subnet_group" "main" {
  name       = "infraledger-db-subnet-group"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]

  tags = {
    Name = "infraledger-db-subnet-group"
  }
}

resource "aws_db_instance" "main" {
  identifier     = "infraledger-db"
  engine         = "postgres"
  engine_version = "16"

  instance_class    = "db.t3.micro"
  allocated_storage = 20
  storage_type      = "gp3"

  db_name  = "infraledger"
  username = "infraledger"
  password = random_password.db_password.result

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.database.id]

  publicly_accessible = false
  multi_az            = false
  skip_final_snapshot = true

  backup_retention_period = 1

  tags = {
    Name = "infraledger-db"
  }
}

output "db_password" {
  value     = random_password.db_password.result
  sensitive = true
}

output "db_endpoint" {
  value = aws_db_instance.main.endpoint
}
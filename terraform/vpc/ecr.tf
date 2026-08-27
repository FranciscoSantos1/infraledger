resource "aws_ecr_repository" "api" {
    name = "infraledger-api"
    image_tag_mutability = "MUTABLE"
    force_delete = true

    image_scanning_configuration {
      scan_on_push = true
    }

    tags = {
        Name =  "infraledger-api"
    }  
}
output "ecr_repository_url" {
  value = aws_ecr_repository.api.repository_url
}
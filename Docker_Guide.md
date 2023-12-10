
# Guide to Building and Deploying Docker Containers

## Build a Docker Image
- Build your Docker image:
  ```bash
  docker build -t [your-image-name] .
  ```

## Tagging the Docker Image for a Repository
- Tag the image for your repository:
  ```bash
  docker tag [your-image-name]:latest [your-repository-url]/[your-image-name]:latest
  ```

## Pushing the Docker Image to a Repository
- Push the image to your Docker repository:
  ```bash
  docker push [your-repository-url]/[your-image-name]:latest
  ```

## Pull and Run Docker Container on an EC2 Machine
- Pull and run the Docker container on an EC2 machine:
  ```bash
  docker pull [your-repository-url]/[your-image-name]:latest
  docker run -d --restart=always -p 80:80 [your-repository-url]/[your-image-name]:latest
  ```

## Install Docker on Ubuntu
- To install Docker on Ubuntu:
  ```bash
  sudo apt update
  sudo apt install docker.io
  sudo systemctl start docker
  sudo usermod -aG docker $USER
  ```

## Install Docker on Amazon Linux
- To install Docker on Amazon Linux:
  ```bash
  sudo yum update -y
  sudo yum search docker
  sudo yum install docker.aarch64
  sudo service docker start
  sudo usermod -aG docker $USER
  ```

## Install Amazon Credential Helper and CLI
- To install Amazon Credential Helper and CLI:
  ```bash
  sudo yum search awscli
  sudo yum install awscli-2.noarch
  sudo yum search amazon-ecr-credential-helper
  sudo yum install amazon-ecr-credential-helper.aarch64
  aws configure
  ```


## Configure Docker Credentials
- Configure your Docker credentials in `~/.docker/config.json`:
  ```json
  {
    "credHelpers": {
      "[your-repository-url]": "ecr-login"
    }
  }
  ```

## Clear Docker Data
- To clear Docker data:
  ```bash
  docker container prune
  docker image prune -a
  docker network prune
  docker volume prune
  docker system prune --volumes
  ```

# Use the official Ubuntu base image
FROM ubuntu:latest

# Set the working directory in the container
WORKDIR /usr/src/app

# Copy the backend and frontend directories into the container
COPY ./backend /usr/src/app/backend
COPY ./frontend/allo-guru/ /usr/src/app/frontend
COPY ./backend/asyncio_script.py /usr/src/app/backend/asyncio_script.py 

# Copy the Nginx configuration file into the container
COPY default /etc/nginx/sites-enabled/default

# Install Nginx, Git, wget, curl, and other necessary tools
RUN apt-get update && \
    apt-get install -y nginx git wget curl ca-certificates gnupg

# Install system dependencies
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-dev libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    NODE_MAJOR=20 && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs

# Install Python dependencies for the backend
RUN pip3 install --no-cache-dir -r backend/requirements.txt

# Install Node dependencies for the frontend
RUN cd frontend && npm install

# Make the necessary ports available
EXPOSE 3000 8000

# Use a script to start both Nginx, the backend, and serve the frontend
COPY start_services.py /start_services.py
RUN chmod +x /start_services.py
CMD ["python3", "/start_services.py"]

#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Starting FloraCare AI EC2 Setup..."

# 1. Update and Install Dependencies
echo "Updating system..."
sudo apt-get update
sudo apt-get upgrade -y
sudo apt-get install -y ca-certificates curl gnupg lsb-release git

# 2. Install Docker
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
      $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
else
    echo "Docker already installed."
fi

# Add user to docker group
sudo usermod -aG docker $USER || true

# 3. Setup Project
# Assuming files are already copied here (e.g. via git clone or scp)
# If using git clone in the future, add it here. For now we assume files are present.

# 4. Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "WARNING: .env file not found! creating a placeholder."
    echo "GOOGLE_API_KEY=your_key_here" > .env
    echo "OPENWEATHER_API_KEY=your_key_here" >> .env
    echo "Please edit .env with real keys."
fi

# 5. Build and Run Container
echo "Building and starting containers..."
# Use docker compose (v2)
sudo docker compose up -d --build

echo "Setup Complete! Backend should be running on port 8000."
echo "Verify with: curl http://localhost:8000/health"

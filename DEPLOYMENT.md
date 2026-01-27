# Deployment Guide for FloraCare AI

This guide will help you deploy the FloraCare AI backend to an AWS EC2 instance.

## Prerequisites
- An AWS Account.
- An EC2 Instance (Ubuntu 22.04 LTS or 24.04 LTS recommended).
- SSH Access to the instance.
- Security Group allowing:
    - **SSH (22)** (Your IP Only)
    - **Custom TCP (8000)** (Optional, for debugging backend directly)
    - **Custom TCP (8501)** (Anywhere 0.0.0.0/0, for public access)

## Steps

### 1. Prepare your EC2 Instance
Launch a `t2.medium` or `t3.medium` instance (recommended for AI workloads, though `t2.micro` might work for testing, it may OOM on heavy libraries).
Ensure you save your `.pem` key file.

### 2. Copy Files to EC2
You want to avoid copying the heavy `.venv` folder. We recommend using `rsync` (if available) or `git`.

**Option A: Using Git (Recommended)**
Push your code to GitHub/GitLab and clone it on the server.
```bash
git clone <your-repo-url>
cd FloraCare-Ai
```

**Option B: Using Rsync (Direct Copy)**
Run this from your local machine:
```bash
rsync -avz --exclude '.venv' --exclude '.git' --exclude '__pycache__' -e "ssh -i /path/to/key.pem" ./FloraCare-Ai ubuntu@<EC2_PUBLIC_IP>:~/
```

**Option C: Using SCP**
If you must use `scp`, it will copy *everything*. To avoid sending the huge `.venv`:
1. Move/Rename your local `.venv` temporarily (e.g. `mv .venv .venv_backup`).
2. Run `scp` as before.
3. Move it back (`mv .venv_backup .venv`).

### 3. Run Setup Script
SSH into your instance:
```bash
ssh -i /path/to/key.pem ubuntu@<EC2_PUBLIC_IP>
```

Navigate to the project directory:
```bash
cd FloraCare-Ai
```

Make the script executable and run it:
```bash
chmod +x scripts/setup_ec2.sh
./scripts/setup_ec2.sh
```

This script will:
- Install Docker and Docker Compose.
- Build the backend container.
- Start the server on port 8000.

### 4. Verify Deployment
Check if the containers are running:
```bash
sudo docker compose ps
```
You should see both `floracare_backend` and `floracare_frontend` running.

### 5. Access the Application
The application is now accessible globally!

**Open your browser and visit:**
`http://<EC2_PUBLIC_IP>:8501`

*(Make sure your Security Group allows traffic on port **8501**)*

## Troubleshooting
- **Permission Denied (Docker)**: Logout and login again for group changes to take effect, or run `newgrp docker`.
- **timeout**: Check EC2 Security Groups (Firewall) to ensure port 8000 (backend) and 8501 (frontend) are open.
- **OOM Killed**: The instance ran out of memory. Upgrade instance type (t3.medium recommended).

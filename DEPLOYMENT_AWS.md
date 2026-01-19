# ☁️ Deploying FloraCare AI to AWS

This guide explains how to deploy the application completely using Docker.

## 1. Prerequisites
*   **AWS Account**
*   **Docker Installed** locally
*   **AWS CLI Installed** and configured (`aws configure`)

## 2. Local Testing (Docker Compose)
Before pushing to the cloud, ensure it runs in containers locally.

1.  **Build and Run**:
    ```bash
    docker-compose up --build
    ```
2.  **Access**:
    *   Frontend: `http://localhost:8501`
    *   Backend Docs: `http://localhost:8000/docs`

---

## 3. AWS Deployment Option A: AWS App Runner (Easiest)
AWS App Runner automatically builds and deploys from your GitHub repository or Container Registry.

### Step 1: Push Images to AWS ECR (Elastic Container Registry)
1.  **Create Repositories**:
    ```bash
    aws ecr create-repository --repository-name floracare-backend
    aws ecr create-repository --repository-name floracare-frontend
    ```
2.  **Login to ECR**:
    ```bash
    aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <YOUR_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com
    ```
3.  **Build & Push Backend**:
    ```bash
    docker build -f Dockerfile.backend -t floracare-backend .
    docker tag floracare-backend:latest <YOUR_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/floracare-backend:latest
    docker push <YOUR_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/floracare-backend:latest
    ```
4.  **Build & Push Frontend**:
    ```bash
    docker build -f Dockerfile.frontend -t floracare-frontend .
    docker tag floracare-frontend:latest <YOUR_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/floracare-frontend:latest
    docker push <YOUR_ACCOUNT_ID>.dkr.ecr.us-east-1.amazonaws.com/floracare-frontend:latest
    ```

### Step 2: Create App Runner Service (Backend)
1.  Go to **AWS App Runner Console** -> **Create Service**.
2.  Source: **Container Registry**.
3.  Image URI: Select the `floracare-backend` image you pushed.
4.  Configuration:
    *   **Port**: `8000`
    *   **Env Variables**: Add `GOOGLE_API_KEY`.
5.  Deploy. **Copy the Service URL** (e.g., `https://api.awsapprunner.com`).

### Step 3: Create App Runner Service (Frontend)
1.  Create another service.
2.  Image URI: Select `floracare-frontend`.
3.  Configuration:
    *   **Port**: `8501`
    *   **Env Variables**:
        *   `API_URL`: Paste the Backend Service URL from Step 2 (e.g., `https://api.awsapprunner.com`).
4.  Deploy.

---

## 4. AWS Deployment Option B: EC2 (Cheapest/Traditional)
1.  Launch an **Ubuntu EC2 Instance** (t3.medium recommended).
2.  Allow Inbound Traffic on ports `8501` and `8000` in Security Group.
3.  SSH into the instance.
4.  Install Docker & Docker Compose.
5.  Clone your repo.
6.  Create a `.env` file with your keys.
7.  Run:
    ```bash
    docker-compose up -d --build
    ```

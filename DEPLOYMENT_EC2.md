# SuperFarmer - AWS EC2 Docker Deployment Guide

This guide walks you through deploying **SuperFarmer** to an AWS EC2 instance using Docker and Docker Compose.

---

## Prerequisites

1. **AWS Account**: Access to AWS Management Console.
2. **EC2 Key Pair**: `.pem` file downloaded to your local machine for SSH access.
3. **Environment Secrets**: Your `.env` variables (`FLUXBASE_API_KEY`, `FLUXBASE_PROJECT_ID`, etc.).

---

## Step 1: Launch an AWS EC2 Instance

1. Go to **AWS Console ➔ EC2 ➔ Launch Instance**.
2. **Name**: `superfarmer-server`
3. **OS Image (AMI)**: **Ubuntu Server 24.04 LTS** (or 22.04 LTS) — 64-bit (x86_64).
4. **Instance Type**: 
   - `t2.micro` or `t3.micro` (Free Tier eligible) is sufficient since AI inference is offloaded to the Fluxbase Gateway.
   - `t3.small` (2 vCPU, 2 GB RAM) recommended for multi-worker production.
5. **Key Pair**: Select your existing `.pem` key or create a new one.
6. **Network Settings (Security Group)**:
   Ensure your Security Group allows the following **Inbound Rules**:

   | Type | Protocol | Port Range | Source | Description |
   |---|---|---|---|---|
   | **SSH** | TCP | `22` | `My IP` (or `0.0.0.0/0`) | Remote SSH terminal access |
   | **HTTP** | TCP | `80` | `0.0.0.0/0` (Anywhere IPv4) | Public web traffic (default port) |
   | **Custom TCP** | TCP | `5000` | `0.0.0.0/0` (Anywhere IPv4) | Direct access to FastAPI port |

7. Click **Launch Instance**.

---

## Step 2: SSH into Your EC2 Instance

Open your local terminal and connect using your `.pem` key:

```bash
chmod 400 your-key.pem
ssh -i your-key.pem ubuntu@<YOUR-EC2-PUBLIC-IP>
```

*(Replace `<YOUR-EC2-PUBLIC-IP>` with the Public IPv4 address shown in the EC2 console).*

---

## Step 3: Install Docker & Docker Compose on the EC2 Instance

Run these commands on your EC2 terminal:

```bash
# Update package lists
sudo apt-get update -y
sudo apt-get upgrade -y

# Install Docker and Docker Compose plugin
sudo apt-get install -y docker.io docker-compose-v2 git

# Enable and start Docker service
sudo systemctl enable --now docker

# Allow running docker without sudo
sudo usermod -aG docker $USER
newgrp docker
```

Verify Docker is working:
```bash
docker --version
docker compose version
```

---

## Step 4: Clone the SuperFarmer Repository

```bash
# Clone the repo
git clone https://github.com/shree-hari-23/superfarmer.git
cd superfarmer
```

---

## Step 5: Configure the Environment Variables (`.env`)

Create your `.env` file on the server:

```bash
nano .env
```

Paste your actual environment secrets into the file:

```dotenv
FLUXBASE_API_KEY=your_fluxbase_api_key_here
FLUXBASE_PROJECT_ID=your_fluxbase_project_id_here
FLUXBASE_URL=https://fluxbase.vercel.app/api/execute-sql
FLUXBASE_BASE_URL=https://fluxbasedb.me
FLUXBASE_AI_BASE_URL=https://fluxbasedb.me/api/v1
SECRET_KEY=superfarmer-production-secret-key-replace-me

# Optional Fallback API Keys
GLM_API_KEY=
GROK_API_KEY=
ANTHROPIC_API_KEY=
GEMINI_API_KEY=

# Optional Email Notification Credentials
SMTP_EMAIL=
SMTP_PASSWORD=
```

Save and exit in nano: press `Ctrl + O`, then `Enter`, then `Ctrl + X`.

---

## Step 6: Build & Run the Container

Build and start the container in the background using Docker Compose:

```bash
docker compose up -d --build
```

Docker will:
1. Pull the lightweight `python:3.11-slim` base image.
2. Install the production dependencies in ~30 seconds.
3. Start the application on **Port 80** and **Port 5000**.

---

## Step 7: Verify Container Status & Logs

Check if the container is running:
```bash
docker compose ps
```
You should see:
```text
NAME                IMAGE                    COMMAND                  SERVICE       STATUS
superfarmer-app     superfarmer-superfarmer  "uvicorn app:app --h…"   superfarmer   Up (healthy)
```

View live real-time server logs:
```bash
docker compose logs -f
```

*(Press `Ctrl + C` to exit log streaming).*

---

## Step 8: Access SuperFarmer in Your Browser

Open your browser and navigate to:

```text
http://<YOUR-EC2-PUBLIC-IP>
```
*(or `http://<YOUR-EC2-PUBLIC-IP>:5000`)*

SuperFarmer is now live on AWS EC2!

---

## Useful Maintenance Commands

```bash
# Stop the application
docker compose down

# Restart the application
docker compose restart

# Pull latest code from git and rebuild container
git pull origin master
docker compose up -d --build

# View container resource usage (CPU/RAM)
docker stats
```

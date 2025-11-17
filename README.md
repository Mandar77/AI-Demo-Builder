# AI-Demo-Builder
CS 6620 Project Group

### Step 1.1: Install AWS CLI v2
Download and Install:
```powershell
# Download MSI installer
Invoke-WebRequest -Uri "https://awscli.amazonaws.com/AWSCLIV2.msi" -OutFile "AWSCLIV2.msi"

# Install silently
msiexec.exe /i AWSCLIV2.msi /qn

# Verify installation
aws --version
# Expected: aws-cli/2.27.x Python/3.11.x Windows/10
```
Configure AWS Credentials:

```powershell
aws configure
# AWS Access Key ID: <your-key>
# AWS Secret Access Key: <your-secret>
# Default region name: us-east-1
# Default output format: json

# Verify
aws sts get-caller-identity
```
### Step 1.2: Install AWS SAM CLI
```powershell
# Download SAM CLI MSI
$url = "https://github.com/aws/aws-sam-cli/releases/latest/download/AWS_SAM_CLI_64_PY3.msi"
Invoke-WebRequest -Uri $url -OutFile "AWS_SAM_CLI.msi"

# Install
Start-Process msiexec.exe -ArgumentList "/i AWS_SAM_CLI.msi /qb" -Wait

# Verify
sam --version
```
### Step 1.3: Install Docker Desktop
Required for local Lambda testing and building cross-platform dependencies:

Download from https://www.docker.com/products/docker-desktop

Install and restart computer if prompted

Verify: ```docker --version``` 

### Step 1.4: Install Python 3.11
```powershell
# Download Python 3.11 (Lambda-compatible)
# From https://www.python.org/downloads/

# During installation, CHECK "Add Python to PATH"

# Verify
python --version  # Should show Python 3.11.x
pip --version
```
Step 1.5: Install FFmpeg on Windows (for local testing)
```powershell
# Using Chocolatey (recommended)
choco install ffmpeg

# OR download manually from https://www.gyan.dev/ffmpeg/builds/
# Extract to C:\ffmpeg and add to PATH

# Verify
ffmpeg -version
```
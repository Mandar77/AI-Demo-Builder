# AI-Powered Demo Builder

> Automatically generate professional product demo videos using AI and AWS microservices

**Cloud Computing Final Project - Fall 2025**

---

## 📖 Overview

AI Demo Builder is a cloud-native platform that automatically generates professional product demonstration videos. Users submit their GitHub repository, receive AI-powered suggestions on what to record, upload short video clips, and receive a polished demo video stitched together automatically.

### Key Features

- 🤖 **AI-Powered Analysis** - Gemini AI analyzes repositories and generates intelligent demo suggestions
- 📹 **Automated Video Processing** - FFmpeg-based video stitching and optimization
- 🔗 **Shareable Public Links** - Instantly shareable demo URLs
- ☁️ **Serverless Architecture** - 18 microservices on AWS Lambda
- 💰 **Zero Cost** - Built entirely on AWS Free Tier

---

## 🏗️ Architecture

### System Overview

```
User → Frontend (S3) → API Gateway → 18 Lambda Microservices → AWS Data Layer
                                            ↓
                            S3, DynamoDB, SQS, SNS, CloudWatch
```

### 18 Microservices

**Phase 1: Analysis & Suggestions (Services 1-6)**
1. GitHub Fetcher - Fetches repository data
2. README Parser - Extracts project information
3. Project Analyzer - Categorizes project type
4. AI Suggestion Service - Generates demo suggestions via Gemini
5. Suggestion Organizer - Formats AI output
6. Session Creator - Initializes session in DynamoDB

**Phase 2: Upload & Validation (Services 7-10)**
7. Upload URL Generator - Creates S3 presigned URLs
8. Upload Tracker - Monitors upload progress
9. Video Validator - Validates video files
10. Format Converter - Standardizes video format

**Phase 3: Demo Generation (Services 11-15)**
11. Job Queue Service - Manages processing queue
12. Slide Creator - Generates transition slides
13. Video Stitcher - Combines videos with FFmpeg
14. Video Optimizer - Compresses final output
15. Public Link Generator - Creates shareable URLs

**Phase 4: Support Services (Services 16-18)**
16. Notification Service - Alerts users when complete
17. Status Tracker - Provides real-time status
18. Cleanup Service - Removes expired content

### AWS Services Used

| Service | Purpose | Free Tier |
|---------|---------|-----------|
| **Lambda** | Run all 18 microservices | 1M requests/month |
| **S3** | Video storage + static hosting | 5 GB storage |
| **DynamoDB** | Session state management | 25 GB storage |
| **SQS** | Asynchronous job queue | 1M requests/month |
| **API Gateway** | REST API endpoints | 1M requests/month |
| **SNS** | Push notifications | 1M publishes/month |
| **CloudWatch** | Logging and monitoring | 5 GB logs/month |

**Total Cost:** $0 (within free tier for 700+ demos/month)

---

## 🚀 Quick Start

### Prerequisites

- AWS Account (student account recommended)
- AWS CLI configured
- Node.js 18+ and Python 3.11+
- Gemini API Key (free from https://ai.google.dev/)

### Setup

```bash
# Clone repository
git clone https://github.com/your-team/ai-demo-builder.git
cd ai-demo-builder

# Set up environment
cp .env.example .env
# Edit .env with your Gemini API key

# Deploy infrastructure
cd infrastructure
./deploy.sh

# Deploy Lambda functions
cd ../scripts
./deploy-all.sh

# Deploy frontend
cd ../frontend
npm install
npm run build
aws s3 sync build/ s3://cs6620-ai-demo-builder/
```

---

## 📁 Project Structure

```
ai-demo-builder/
├── lambda/                          # All Lambda microservices
│   ├── analysis-pipeline/           # Services 1-4 (Xinyu)
│   │   ├── github-fetcher/
│   │   ├── readme-parser/
│   │   ├── project-analyzer/
│   │   └── cache-service/
│   │
│   ├── ai-suggestions/              # Services 5-6 (Aarzoo)
│   │   ├── ai-analysis/
│   │   ├── suggestion-organizer/
│   │   └── session-creator/
│   │
│   ├── upload-pipeline/             # Services 7-10 (Sampada) 
│   │   ├── upload-url-generator/
│   │   ├── upload-tracker/
│   │   ├── video-validator/
│   │   └── format-converter/
│   │
│   ├── video-processing/            # Services 11-15 (Mandar)
│   │   ├── job-queue-service/
│   │   ├── slide-creator/
│   │   ├── video-stitcher/
│   │   ├── video-optimizer/
│   │   └── public-link-generator/
│   │
│   ├── infrastructure/              # Services 16-18 (Chang)
│   │   ├── notification-service/
│   │   ├── status-tracker/
│   │   └── cleanup-service/
│   │
│   └── shared/                      # Common utilities
│       ├── s3_utils.py
│       ├── dynamo_utils.py
│       └── error_handler.py
│
├── layers/                          # Lambda layers
│   └── ffmpeg/                      # FFmpeg for video processing
│       └── arn: ...layer:ffmpeg:1
│
├── frontend/                        # React web interface
│   ├── src/
│   └── public/
│
├── infrastructure/                  # CloudFormation templates
│   ├── storage.yaml                 # S3 buckets
│   ├── databases.yaml               # DynamoDB tables
│   └── api-gateway.yaml             # API endpoints
│
├── scripts/                         # Deployment scripts
│   ├── deploy-all.sh
│   └── test-flow.sh
│
├── tests/                           # Test files
│   └── events/                      # Lambda test events
│
├── docs/                            # Documentation
│   ├── architecture.md
│   └── api-reference.md
│
└── README.md                        # This file
```

---

## 🎯 How It Works

### User Flow

1. **Submit GitHub URL** 
   ```
   User pastes: https://github.com/username/awesome-project
   ```

2. **AI Analyzes Project**
   ```
   System generates suggestions:
   - Video 1: Show homepage (15 seconds)
   - Video 2: Show search feature (20 seconds)
   - Video 3: Show results page (15 seconds)
   ```

3. **User Uploads Videos**
   ```
   User records 3 short clips on their phone/screen recorder
   Uploads each video (one per suggestion)
   ```

4. **Automatic Processing**
   ```
   System stitches videos together with transition slides
   Optimizes for web playback
   Uploads to public URL
   ```

5. **Share Demo**
   ```
   User receives: https://demos.../abc123/final.mp4
   Shares with anyone - no login needed
   ```

---

## 🗄️ Database Schema

### DynamoDB Table: Sessions

```javascript
{
  id: String,              // Primary Key (UUID)
  github_url: String,      // Original GitHub URL
  project_name: String,    // Repository name
  status: String,          // analyzing|ready|uploading|processing|complete
  suggestions: Array,      // AI-generated demo suggestions
  uploaded_videos: Map,    // Video number → S3 key
  demo_url: String,        // Final shareable URL
  created_at: String,      // ISO timestamp
  expires_at: Number       // TTL (30 days)
}
```

---

## 🔑 Environment Variables

```bash
# .env file
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=288418345946
S3_BUCKET=cs6620-ai-demo-builder
DYNAMODB_TABLE=Sessions
GEMINI_API_KEY=your-gemini-key-here
```
---

## 🚀 Deployment

### One-Command Deploy

```bash
./scripts/deploy-all.sh
```

### Manual Deploy

```bash
# 1. Create infrastructure
aws cloudformation deploy \
  --template-file infrastructure/main-template.yaml \
  --stack-name demo-builder \
  --capabilities CAPABILITY_IAM

# 2. Deploy each Lambda service
cd lambda/upload-pipeline/upload-url-generator
./deploy.sh

# Repeat for all 18 services...

# 3. Deploy frontend
cd frontend
npm run build
aws s3 sync build/ s3://cs6620-ai-demo-builder/
```

---

## 📚 API Documentation

### POST /analyze
Analyze GitHub repository and generate suggestions

**Request:**
```json
{
  "github_url": "https://github.com/owner/repo"
}
```

**Response:**
```json
{
  "session_id": "abc-123-def",
  "suggestions": [...]
}
```

### POST /upload-url
Get presigned URL for video upload

**Request:**
```json
{
  "session_id": "abc-123-def",
  "suggestion_id": 1
}
```

**Response:**
```json
{
  "upload_url": "https://...",
  "expires_in": 3600
}
```

### GET /demo/{session_id}
Retrieve final demo video

**Response:**
```json
{
  "demo_url": "https://demos.../final.mp4",
  "status": "complete"
}
```

[See full API documentation](docs/api-reference.md)

---
**Built with ❤️ using AWS and AI**

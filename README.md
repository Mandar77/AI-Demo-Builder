# AI-Demo-Builder
CS 6620 Project Group

## Team Assignments:

- Person 1 (Xinyu): Analysis Pipeline - GitHub Fetcher, Content Parser, AI Analysis, Suggestion Formatter
- Person 2 (Aarzoo): Video Processing - Upload Manager, Video Validator, Thumbnail Generator, Video Preprocessor
- Person 3 (Sampada): Infrastructure - API Gateway Service, Notification Service, State Manager, Cleanup Service
- Person 4 (Mandar): Video Processing - Slide Generator, Video Stitcher, Video Optimizer, Job Queue Manager
- Person 5 (Chang): Frontend + Status Tracker, Notification Service, Clean Up service

## File System Architecture:

```bash
ai-demo-builder/

├── .github/
│   └── workflows/
│       └── deploy.yml
├── lambda/
│   ├── analysis-pipeline/
│   │   ├── github-fetcher/
│   │   ├── content-parser/
│   │   ├── ai-analysis/
│   │   └── suggestion-formatter/
│   │
│   ├── video-processing/
│   │   ├── slide-generator/
│   │   ├── video-stitcher/
│   │   ├── video-optimizer/
│   │   ├── upload-manager/
│   │   ├── video-validator/
│   │   └── thumbnail-generator/
│   │
│   ├── infrastructure/
│   │   ├── job-queue-manager/
│   │   ├── api-router/
│   │   ├── notification/
│   │   ├── state-manager/
│   │   ├── cleanup/
│   │   └── cache/
│   │
│   └── shared/
│       ├── __init__.py
│       ├── s3_utils.py
│       ├── dynamo_utils.py
│       ├── sqs_utils.py
│       └── error_handler.py
│
├── layers/
│   ├── ffmpeg/
│   │   ├── bin/
│   │   │   ├── ffmpeg
│   │   │   └── ffprobe
│   │   └── build.sh
│   ├── common-dependencies/
│   │   ├── python/
│   │   └── requirements.txt
│   └── ai-sdk/
│       └── python/
│
├── frontend/
│   ├── public/
│   ├── src/
│   └── package.json
│
├── infrastructure/
│   ├── main-template.yaml
│   ├── api-gateway.yaml
│   ├── databases.yaml
│   ├── queues.yaml
│   ├── storage.yaml
│   └── monitoring.yaml
│
├── scripts/
│   ├── deploy.ps1
│   ├── deploy.sh
│   ├── setup-windows.ps1
│   ├── build-layers.ps1
│   └── test-local.ps1
│
├── tests/
│   ├── unit/
│   │   └── video-processing/
│   ├── integration/
│   └── events/
│       ├── slide-create.json
│       ├── video-stitch.json
│       ├── video-optimize.json
│       └── job-queue.json
│
├── docs/
│   ├── architecture.md
│   ├── implementation.md
│   └── api-reference.md
│
├── .env.example
├── .gitignore
├── requirements.txt
├── package.json
├── samconfig.toml
└── README.md
 ```
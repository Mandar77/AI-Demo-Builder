#!/bin/bash
# Deploy all infrastructure services (16, 17, 18) and service 7

set -e

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Force region to us-west-1 for consistency
export AWS_REGION=us-west-1

# AWS Profile
AWS_PROFILE=${AWS_PROFILE:-iam-user}
export AWS_PROFILE=$AWS_PROFILE

echo "🚀 Deploying Infrastructure Services"
echo "===================================="
echo "📍 Region: us-west-1"
echo "📍 Profile: $AWS_PROFILE"
echo ""

# Check AWS credentials
if ! aws sts get-caller-identity &>/dev/null; then
    echo "❌ AWS credentials not configured or expired."
    exit 1
fi

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
echo "✅ AWS credentials valid (Account: $AWS_ACCOUNT)"
echo ""

# Get Lambda role
LAMBDA_ROLE=$(aws iam list-roles --query 'Roles[?contains(RoleName, `lambda`) && contains(RoleName, `dynamodb`)].Arn' --output text 2>/dev/null | head -1)
if [ -z "$LAMBDA_ROLE" ]; then
    LAMBDA_ROLE=$(aws iam list-roles --query 'Roles[?contains(RoleName, `lambda`)].Arn' --output text 2>/dev/null | head -1)
fi
echo "📍 Using Lambda role: $LAMBDA_ROLE"
echo ""

# Function to deploy a Python Lambda
deploy_python_lambda() {
    local SERVICE_NAME=$1
    local FUNCTION_NAME=$2
    local HANDLER=$3
    local ENV_VARS=$4
    
    echo "📦 Deploying $SERVICE_NAME..."
    cd "lambda/infrastructure/$SERVICE_NAME"
    
    # Clean up old package
    rm -rf package package.zip
    
    # Install dependencies
    echo "  📥 Installing dependencies..."
    mkdir -p package
    pip install -r requirements.txt -t package/ --quiet 2>&1 | grep -v "already satisfied" || true
    
    # Copy function and shared utilities
    cp lambda_function.py package/
    mkdir -p package/shared
    cp -r ../../shared/* package/shared/
    
    # Create deployment package
    echo "  📦 Creating package..."
    (cd package && zip -r ../package.zip . -q)
    
    # Deploy or update
    if aws lambda get-function --function-name "$FUNCTION_NAME" --region us-west-1 &>/dev/null; then
        echo "  🔄 Updating function..."
        # Wait for any in-progress updates
        while true; do
            STATUS=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region us-west-1 --query 'Configuration.LastUpdateStatus' --output text 2>/dev/null || echo "Successful")
            if [ "$STATUS" != "InProgress" ]; then
                break
            fi
            echo "    ⏳ Waiting for previous update to complete..."
            sleep 5
        done
        
        aws lambda update-function-code \
            --function-name "$FUNCTION_NAME" \
            --zip-file fileb://package.zip \
            --region us-west-1 \
            --output json > /dev/null
        
        # Wait for code update to complete
        sleep 3
        
        aws lambda update-function-configuration \
            --function-name "$FUNCTION_NAME" \
            --handler "$HANDLER" \
            --environment "Variables={$ENV_VARS}" \
            --region us-west-1 \
            --output json > /dev/null
    else
        echo "  🆕 Creating function..."
        aws lambda create-function \
            --function-name "$FUNCTION_NAME" \
            --runtime python3.11 \
            --role "$LAMBDA_ROLE" \
            --handler "$HANDLER" \
            --zip-file fileb://package.zip \
            --timeout 30 \
            --memory-size 256 \
            --environment "Variables={$ENV_VARS}" \
            --region us-west-1 \
            --output json > /dev/null
    fi
    
    # Clean up
    rm -rf package package.zip
    cd - > /dev/null
    echo "  ✅ $SERVICE_NAME deployed!"
    echo ""
}

# Function to deploy a Node.js Lambda
deploy_nodejs_lambda() {
    local SERVICE_NAME=$1
    local FUNCTION_NAME=$2
    local HANDLER=$3
    local ENV_VARS=$4
    
    echo "📦 Deploying $SERVICE_NAME..."
    cd "lambda/upload-pipeline/$SERVICE_NAME"
    
    # Clean up
    rm -f package.zip
    
    # Install dependencies
    if [ ! -d "node_modules" ]; then
        echo "  📥 Installing dependencies..."
        npm install --quiet
    fi
    
    # Create package
    echo "  📦 Creating package..."
    zip -r package.zip index.js node_modules package.json -q
    
    # Deploy or update
    if aws lambda get-function --function-name "$FUNCTION_NAME" --region us-west-1 &>/dev/null; then
        echo "  🔄 Updating function..."
        # Wait for any in-progress updates
        while true; do
            STATUS=$(aws lambda get-function --function-name "$FUNCTION_NAME" --region us-west-1 --query 'Configuration.LastUpdateStatus' --output text 2>/dev/null || echo "Successful")
            if [ "$STATUS" != "InProgress" ]; then
                break
            fi
            echo "    ⏳ Waiting for previous update to complete..."
            sleep 5
        done
        
        aws lambda update-function-code \
            --function-name "$FUNCTION_NAME" \
            --zip-file fileb://package.zip \
            --region us-west-1 \
            --output json > /dev/null
        
        # Wait for code update to complete
        sleep 3
        
        aws lambda update-function-configuration \
            --function-name "$FUNCTION_NAME" \
            --environment "Variables={$ENV_VARS}" \
            --region us-west-1 \
            --output json > /dev/null
    else
        echo "  🆕 Creating function..."
        aws lambda create-function \
            --function-name "$FUNCTION_NAME" \
            --runtime nodejs18.x \
            --role "$LAMBDA_ROLE" \
            --handler "$HANDLER" \
            --zip-file fileb://package.zip \
            --timeout 30 \
            --memory-size 256 \
            --environment "Variables={$ENV_VARS}" \
            --region us-west-1 \
            --output json > /dev/null
    fi
    
    # Clean up
    rm -f package.zip
    cd - > /dev/null
    echo "  ✅ $SERVICE_NAME deployed!"
    echo ""
}

# Deploy all services
deploy_nodejs_lambda "upload-url-generator" "service-7-upload-url-generator" "index.handler" "S3_BUCKET=${S3_BUCKET:-cs6620-ai-demo-builder},DYNAMODB_TABLE=${DYNAMODB_TABLE:-Sessions}"

# Build environment variables for notification service
NOTIFICATION_ENV="DYNAMODB_TABLE=${DYNAMODB_TABLE:-Sessions}"
if [ -n "$HTTP_WEBHOOK_URL" ]; then
    NOTIFICATION_ENV="$NOTIFICATION_ENV,HTTP_WEBHOOK_URL=$HTTP_WEBHOOK_URL"
fi
if [ -n "$SNS_TOPIC_ARN" ]; then
    NOTIFICATION_ENV="$NOTIFICATION_ENV,SNS_TOPIC_ARN=$SNS_TOPIC_ARN"
fi

deploy_python_lambda "notification-service" "service-16-notification-service" "lambda_function.lambda_handler" "$NOTIFICATION_ENV"

deploy_python_lambda "status-tracker" "service-17-status-tracker" "lambda_function.lambda_handler" "DYNAMODB_TABLE=${DYNAMODB_TABLE:-Sessions}"

deploy_python_lambda "cleanup-service" "service-18-cleanup-service" "lambda_function.lambda_handler" "DYNAMODB_TABLE=${DYNAMODB_TABLE:-Sessions},S3_BUCKET=${S3_BUCKET:-cs6620-ai-demo-builder}"

echo "✅ All infrastructure services deployed!"
echo ""
echo "📍 Deployed functions:"
echo "  - service-7-upload-url-generator"
echo "  - service-16-notification-service"
echo "  - service-17-status-tracker"
echo "  - service-18-cleanup-service"


#!/bin/bash

# Deploy all upload pipeline services
echo "Deploying Upload Pipeline Services..."

SERVICES=("upload-url-generator" "upload-tracker" "video-validator" "format-converter")
REGION="us-east-1"
ROLE_ARN="arn:aws:iam::288418345946:role/lambda-execution-role"

for SERVICE in "${SERVICES[@]}"; do
    echo "Deploying $SERVICE..."
    
    cd $SERVICE
    
    if [ -f "package.json" ]; then
        # Node.js service
        npm install
        zip -r function.zip index.js node_modules package.json
        
        aws lambda create-function \
            --function-name $SERVICE \
            --runtime nodejs18.x \
            --role $ROLE_ARN \
            --handler index.handler \
            --zip-file fileb://function.zip \
            --timeout 60 \
            --memory-size 512 \
            --environment Variables="{S3_BUCKET=cs6620-ai-demo-builder,DYNAMODB_TABLE=Sessions}" \
            --region $REGION \
            2>/dev/null || \
        aws lambda update-function-code \
            --function-name $SERVICE \
            --zip-file fileb://function.zip \
            --region $REGION
            
        rm function.zip
        
    elif [ -f "requirements.txt" ]; then
        # Python service
        pip install -r requirements.txt -t .
        zip -r function.zip . -x "*.git*"
        
        aws lambda create-function \
            --function-name $SERVICE \
            --runtime python3.11 \
            --role $ROLE_ARN \
            --handler handler.handler \
            --zip-file fileb://function.zip \
            --timeout 300 \
            --memory-size 1024 \
            --layers arn:aws:lambda:us-east-1:288418345946:layer:ffmpeg:1 \
            --environment Variables="{S3_BUCKET=cs6620-ai-demo-builder,DYNAMODB_TABLE=Sessions}" \
            --region $REGION \
            2>/dev/null || \
        aws lambda update-function-code \
            --function-name $SERVICE \
            --zip-file fileb://function.zip \
            --region $REGION
            
        rm function.zip
    fi
    
    echo "$SERVICE deployed successfully!"
    cd ..
done

echo "All upload pipeline services deployed!"
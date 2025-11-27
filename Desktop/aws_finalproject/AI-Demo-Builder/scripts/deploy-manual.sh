#!/bin/bash
# Person 1 手动部署脚本

set -e

# 配置
REGION=${AWS_REGION:-"us-west-1"}
ROLE_NAME="ai-demo-builder-person1-lambda-role"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Person 1 手动部署脚本 ===${NC}"
echo ""

# 检查是否使用共享资源
USE_SHARED=${1:-"false"}
if [ "$USE_SHARED" = "true" ]; then
  echo -e "${YELLOW}使用共享资源模式${NC}"
  read -p "请输入共享 Jobs Table 名称: " SHARED_JOBS_TABLE
  read -p "请输入共享 Repos Bucket 名称: " SHARED_REPOS_BUCKET
  read -p "请输入共享 Cache Table 名称: " SHARED_CACHE_TABLE
  
  JOBS_TABLE=${SHARED_JOBS_TABLE}
  REPOS_BUCKET=${SHARED_REPOS_BUCKET}
  CACHE_TABLE=${SHARED_CACHE_TABLE}
else
  echo -e "${YELLOW}使用独立资源模式${NC}"
  JOBS_TABLE="ai-demo-builder-person1-jobs-${ACCOUNT_ID}"
  REPOS_BUCKET="ai-demo-builder-person1-repos-${ACCOUNT_ID}"
  CACHE_TABLE="ai-demo-builder-person1-cache-${ACCOUNT_ID}"
fi

echo ""
echo "资源配置:"
echo "  Jobs Table: ${JOBS_TABLE}"
echo "  Repos Bucket: ${REPOS_BUCKET}"
echo "  Cache Table: ${CACHE_TABLE}"
echo ""

# 步骤 1: 创建 IAM 角色（如果不存在）
echo -e "${GREEN}[1/6] 检查 IAM 角色...${NC}"
if aws iam get-role --role-name ${ROLE_NAME} &>/dev/null; then
  echo "  角色已存在，跳过创建"
else
  echo "  创建 IAM 角色..."
  cat > /tmp/lambda-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

  aws iam create-role \
    --role-name ${ROLE_NAME} \
    --assume-role-policy-document file:///tmp/lambda-trust-policy.json \
    > /dev/null

  aws iam attach-role-policy \
    --role-name ${ROLE_NAME} \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

  echo "  等待角色生效..."
  sleep 5
fi

ROLE_ARN=$(aws iam get-role --role-name ${ROLE_NAME} --query 'Role.Arn' --output text)
echo "  角色 ARN: ${ROLE_ARN}"

# 步骤 2: 创建资源权限策略
echo -e "${GREEN}[2/6] 配置资源权限...${NC}"

# S3 策略
cat > /tmp/s3-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::${REPOS_BUCKET}",
        "arn:aws:s3:::${REPOS_BUCKET}/*"
      ]
    }
  ]
}
EOF

# DynamoDB 策略
cat > /tmp/dynamodb-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:PutItem",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": [
        "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${JOBS_TABLE}",
        "arn:aws:dynamodb:${REGION}:${ACCOUNT_ID}:table/${CACHE_TABLE}"
      ]
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name ${ROLE_NAME} \
  --policy-name S3AccessPolicy \
  --policy-document file:///tmp/s3-policy.json \
  > /dev/null

aws iam put-role-policy \
  --role-name ${ROLE_NAME} \
  --policy-name DynamoDBAccessPolicy \
  --policy-document file:///tmp/dynamodb-policy.json \
  > /dev/null

echo "  权限已配置"

# 步骤 3: 准备部署包
echo -e "${GREEN}[3/6] 准备部署包...${NC}"
cd "$(dirname "$0")/../lambda"

# GitHub Fetcher
echo "  打包 github-fetcher..."
cd analysis-pipeline/github-fetcher
rm -rf package *.zip 2>/dev/null
mkdir -p package
cp app.py package/
pip install -r requirements.txt -t package/ --quiet
cd package && zip -r ../github-fetcher.zip . -q && cd .. && rm -rf package
cd ../../..

# Content Parser
echo "  打包 content-parser..."
cd analysis-pipeline/content-parser
rm -rf package *.zip 2>/dev/null
mkdir -p package
cp app.py package/
pip install -r requirements.txt -t package/ --quiet
cd package && zip -r ../content-parser.zip . -q && cd .. && rm -rf package
cd ../../..

# Cache Service
echo "  打包 cache..."
cd infrastructure/cache
rm -rf package *.zip 2>/dev/null
mkdir -p package
cp app.py package/
pip install -r requirements.txt -t package/ --quiet
cd package && zip -r ../cache-service.zip . -q && cd .. && rm -rf package
cd ../../..

# 步骤 4: 创建或更新 Lambda 函数
echo -e "${GREEN}[4/6] 部署 Lambda 函数...${NC}"

deploy_function() {
  local FUNC_NAME=$1
  local ZIP_FILE=$2
  local HANDLER=$3
  local ENV_VARS=$4
  local TIMEOUT=${5:-300}
  local MEMORY=${6:-512}

  if aws lambda get-function --function-name ${FUNC_NAME} &>/dev/null; then
    echo "  更新函数: ${FUNC_NAME}"
    aws lambda update-function-code \
      --function-name ${FUNC_NAME} \
      --zip-file fileb://${ZIP_FILE} \
      --region ${REGION} \
      > /dev/null
    
    aws lambda update-function-configuration \
      --function-name ${FUNC_NAME} \
      --environment Variables="${ENV_VARS}" \
      --timeout ${TIMEOUT} \
      --memory-size ${MEMORY} \
      --region ${REGION} \
      > /dev/null
  else
    echo "  创建函数: ${FUNC_NAME}"
    aws lambda create-function \
      --function-name ${FUNC_NAME} \
      --runtime python3.12 \
      --role ${ROLE_ARN} \
      --handler ${HANDLER} \
      --zip-file fileb://${ZIP_FILE} \
      --timeout ${TIMEOUT} \
      --memory-size ${MEMORY} \
      --environment Variables="${ENV_VARS}" \
      --region ${REGION} \
      > /dev/null
  fi
}

# 部署 GitHub Fetcher
ENV_VARS_GITHUB="{
  \"S3_BUCKET_NAME\": \"${REPOS_BUCKET}\",
  \"JOBS_TABLE_NAME\": \"${JOBS_TABLE}\",
  \"CACHE_TABLE_NAME\": \"${CACHE_TABLE}\"
}"
deploy_function "ai-demo-builder-github-fetcher" \
  "analysis-pipeline/github-fetcher/github-fetcher.zip" \
  "app.lambda_handler" \
  "${ENV_VARS_GITHUB}"

# 部署 Content Parser
ENV_VARS_PARSER="{
  \"S3_BUCKET_NAME\": \"${REPOS_BUCKET}\",
  \"JOBS_TABLE_NAME\": \"${JOBS_TABLE}\"
}"
deploy_function "ai-demo-builder-readme-parser" \
  "analysis-pipeline/content-parser/content-parser.zip" \
  "app.lambda_handler" \
  "${ENV_VARS_PARSER}"

# 部署 Cache Service
ENV_VARS_CACHE="{
  \"CACHE_TABLE_NAME\": \"${CACHE_TABLE}\",
  \"CACHE_TTL_SECONDS\": \"86400\"
}"
deploy_function "ai-demo-builder-cache-service" \
  "infrastructure/cache/cache-service.zip" \
  "app.lambda_handler" \
  "${ENV_VARS_CACHE}" \
  60 \
  256

# 步骤 5: 清理临时文件
echo -e "${GREEN}[5/6] 清理临时文件...${NC}"
rm -f analysis-pipeline/*/*.zip infrastructure/cache/*.zip
rm -f /tmp/lambda-trust-policy.json /tmp/s3-policy.json /tmp/dynamodb-policy.json

# 步骤 6: 输出函数信息
echo -e "${GREEN}[6/6] 部署完成！${NC}"
echo ""
echo "Lambda 函数列表:"
aws lambda list-functions \
  --region ${REGION} \
  --query 'Functions[?starts_with(FunctionName, `ai-demo-builder`)].FunctionName' \
  --output table

echo ""
echo -e "${GREEN}✅ 所有函数已部署！${NC}"
echo ""
echo "函数 ARN:"
for func in "ai-demo-builder-github-fetcher" "ai-demo-builder-readme-parser" "ai-demo-builder-cache-service"; do
  ARN=$(aws lambda get-function --function-name ${func} --region ${REGION} --query 'Configuration.FunctionArn' --output text 2>/dev/null || echo "未找到")
  echo "  ${func}: ${ARN}"
done


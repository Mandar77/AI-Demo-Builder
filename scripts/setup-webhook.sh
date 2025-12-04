#!/bin/bash
# Setup webhook URL for notification service

set -e

echo "🔗 Setting up Webhook for Notification Service"
echo "=============================================="
echo ""

# Check if webhook URL is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <webhook-url>"
    echo ""
    echo "Examples:"
    echo "  # Use webhook.site (free testing service)"
    echo "  $0 https://webhook.site/your-unique-id"
    echo ""
    echo "  # Use local server with ngrok"
    echo "  # 1. Start local server: python3 scripts/test-webhook-server.py"
    echo "  # 2. Expose with ngrok: ngrok http 8000"
    echo "  # 3. Use ngrok URL: $0 https://your-ngrok-url.ngrok.io"
    echo ""
    echo "  # Use your own server"
    echo "  $0 https://your-server.com/webhook"
    echo ""
    exit 1
fi

WEBHOOK_URL=$1
AWS_PROFILE=${AWS_PROFILE:-iam-user}
export AWS_PROFILE=$AWS_PROFILE

echo "📍 Webhook URL: $WEBHOOK_URL"
echo "📍 AWS Profile: $AWS_PROFILE"
echo ""

# Check AWS credentials
if ! aws sts get-caller-identity &>/dev/null; then
    echo "❌ AWS credentials not configured or expired."
    exit 1
fi

# Update Lambda environment variable
echo "🔄 Updating Lambda function environment..."
aws lambda update-function-configuration \
    --function-name service-16-notification-service \
    --region us-west-1 \
    --environment "Variables={DYNAMODB_TABLE=${DYNAMODB_TABLE:-Sessions},HTTP_WEBHOOK_URL=$WEBHOOK_URL}" \
    --output json > /dev/null

echo "✅ Webhook URL configured!"
echo ""
echo "📋 Test the webhook:"
echo "  1. Trigger notification service (when video processing completes)"
echo "  2. Check your webhook endpoint for the notification"
echo ""
echo "💡 To test manually, you can call the notification service API"


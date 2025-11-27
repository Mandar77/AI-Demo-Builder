SESSION_ID="flow-test-$(date +%s)"
echo "Testing with session: $SESSION_ID"

# ========================================
# Step 1: Upload a REAL video to S3
# ========================================
echo ""
echo "1️⃣ Uploading real video to S3..."

aws s3 cp sample-video.mp4 s3://cs6620-ai-demo-builder/videos/${SESSION_ID}/1.mp4

echo "✅ Video uploaded"

# ========================================
# Step 2: Wait for Upload Tracker
# ========================================
echo ""
echo "2️⃣ Waiting for Upload Tracker (5 seconds)..."
sleep 5

echo "Checking Upload Tracker logs..."
aws logs tail /aws/lambda/upload-tracker --since 1m --region us-east-1 | tail -5

# ========================================
# Step 3: Validate Video
# ========================================
echo ""
echo "3️⃣ Validating video..."

aws lambda invoke \
  --function-name video-validator \
  --cli-binary-format raw-in-base64-out \
  --payload "{\"body\": \"{\\\"video_key\\\":\\\"videos/${SESSION_ID}/1.mp4\\\"}\"}" \
  validate.json \
  --region us-east-1 \
  --no-cli-pager

echo "Validation result:"
cat validate.json
echo ""

# ========================================
# Step 4: Convert Video
# ========================================
echo ""
echo "4️⃣ Converting video with FFmpeg..."

aws lambda invoke \
  --function-name format-converter \
  --cli-binary-format raw-in-base64-out \
  --payload "{\"body\": \"{\\\"video_key\\\":\\\"videos/${SESSION_ID}/1.mp4\\\"}\"}" \
  convert.json \
  --region us-east-1 \
  --no-cli-pager

echo "Conversion result:"
cat convert.json
echo ""

# Wait for conversion to finish
echo "Waiting 10 seconds for conversion..."
sleep 10

# Check converter logs
echo "Checking Format Converter logs..."
aws logs tail /aws/lambda/format-converter --since 1m --region us-east-1 | tail -10

# ========================================
# Step 5: Verify Both Files in S3
# ========================================
echo ""
echo "5️⃣ Checking S3 for files..."

aws s3 ls s3://cs6620-ai-demo-builder/videos/${SESSION_ID}/

echo ""
echo "=========================================="
echo "✅ END-TO-END TEST COMPLETE!"
echo "=========================================="
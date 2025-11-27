const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');
const { getSignedUrl } = require('@aws-sdk/s3-request-presigner');

const s3Client = new S3Client({ region: 'us-east-1' });
const BUCKET = 'cs6620-ai-demo-builder';

exports.handler = async (event) => {
  try {
    const body = JSON.parse(event.body);
    const { session_id, suggestion_id } = body;
    
    // Create S3 key
    const key = `videos/${session_id}/${suggestion_id}.mp4`;
    
    // Generate presigned URL (valid for 1 hour)
    const command = new PutObjectCommand({
      Bucket: BUCKET,
      Key: key,
      ContentType: 'video/mp4'
    });
    
    const uploadUrl = await getSignedUrl(s3Client, command, {
      expiresIn: 3600
    });
    
    return {
      statusCode: 200,
      headers: { 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({
        upload_url: uploadUrl,
        key: key,
        expires_in: 3600
      })
    };
    
  } catch (error) {
    console.error('Error:', error);
    return {
      statusCode: 500,
      headers: { 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ error: error.message })
    };
  }
};

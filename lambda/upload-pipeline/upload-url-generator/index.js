const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');
const { DynamoDBClient, GetItemCommand, UpdateItemCommand } = require('@aws-sdk/client-dynamodb');
const { getSignedUrl } = require('@aws-sdk/s3-request-presigner');

const s3Client = new S3Client({ region: process.env.AWS_REGION || 'us-east-1' });
const dynamoClient = new DynamoDBClient({ region: process.env.AWS_REGION || 'us-east-1' });

const BUCKET = process.env.S3_BUCKET || 'ai-demo-builder';
const TABLE = process.env.DYNAMODB_TABLE || 'ai-demo-sessions';

exports.handler = async (event) => {
  console.log('Event:', JSON.stringify(event));
  
  try {
    const body = JSON.parse(event.body);
    const { session_id, suggestion_id, file_name } = body;
    
    if (!session_id || !suggestion_id) {
      return {
        statusCode: 400,
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify({ error: 'Missing session_id or suggestion_id' })
      };
    }
    
    // Verify session exists
    const sessionData = await getSession(session_id);
    if (!sessionData) {
      return {
        statusCode: 404,
        headers: { 'Access-Control-Allow-Origin': '*' },
        body: JSON.stringify({ error: 'Session not found' })
      };
    }
    
    // Create unique S3 key
    const timestamp = Date.now();
    const extension = file_name ? file_name.split('.').pop() : 'mp4';
    const key = `videos/${session_id}/${suggestion_id}_${timestamp}.${extension}`;
    
    // Generate presigned URL (valid for 1 hour)
    const command = new PutObjectCommand({
      Bucket: BUCKET,
      Key: key,
      ContentType: 'video/mp4',
      Metadata: {
        session_id: session_id,
        suggestion_id: suggestion_id.toString(),
        upload_timestamp: timestamp.toString()
      }
    });
    
    const uploadUrl = await getSignedUrl(s3Client, command, {
      expiresIn: 3600
    });
    
    // Update session with upload initiated status
    await updateUploadStatus(session_id, suggestion_id, 'initiated', key);
    
    return {
      statusCode: 200,
      headers: { 
        'Access-Control-Allow-Origin': '*',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        upload_url: uploadUrl,
        key: key,
        expires_in: 3600,
        session_id: session_id,
        suggestion_id: suggestion_id
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

async function getSession(sessionId) {
  const params = {
    TableName: TABLE,
    Key: {
      id: { S: sessionId }
    }
  };
  
  try {
    const result = await dynamoClient.send(new GetItemCommand(params));
    return result.Item;
  } catch (error) {
    console.error('Error getting session:', error);
    return null;
  }
}

async function updateUploadStatus(sessionId, suggestionId, status, s3Key) {
  const params = {
    TableName: TABLE,
    Key: {
      id: { S: sessionId }
    },
    UpdateExpression: 'SET #uploads.#suggId = :uploadInfo, #status = :status',
    ExpressionAttributeNames: {
      '#uploads': 'uploaded_videos',
      '#suggId': `suggestion_${suggestionId}`,
      '#status': 'status'
    },
    ExpressionAttributeValues: {
      ':uploadInfo': {
        M: {
          status: { S: status },
          s3_key: { S: s3Key },
          timestamp: { N: Date.now().toString() }
        }
      },
      ':status': { S: 'uploading' }
    }
  };
  
  try {
    await dynamoClient.send(new UpdateItemCommand(params));
  } catch (error) {
    console.error('Error updating upload status:', error);
  }
}
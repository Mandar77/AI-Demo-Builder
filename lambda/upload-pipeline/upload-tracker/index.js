const { DynamoDBClient, UpdateItemCommand, GetItemCommand } = require('@aws-sdk/client-dynamodb');
const { S3Client, HeadObjectCommand } = require('@aws-sdk/client-s3');

const dynamoClient = new DynamoDBClient({ region: process.env.AWS_REGION || 'us-east-1' });
const s3Client = new S3Client({ region: process.env.AWS_REGION || 'us-east-1' });

const TABLE = process.env.DYNAMODB_TABLE || 'Sessions';
const BUCKET = process.env.S3_BUCKET || 'cs6620-ai-demo-builder';

exports.handler = async (event) => {
  console.log('Event:', JSON.stringify(event));
  
  try {
    // This can be triggered by S3 events or periodic checks
    if (event.Records) {
      // S3 event trigger
      return await handleS3Event(event);
    } else {
      // Direct API call for status check
      return await handleStatusCheck(event);
    }
  } catch (error) {
    console.error('Error:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: error.message })
    };
  }
};

async function handleS3Event(event) {
  const results = [];
  
  for (const record of event.Records) {
    if (record.eventName.startsWith('ObjectCreated:')) {
      const bucket = record.s3.bucket.name;
      const key = decodeURIComponent(record.s3.object.key.replace(/\+/g, ' '));
      const size = record.s3.object.size;
      
      console.log(`File uploaded: ${key}, Size: ${size}`);
      
      // Extract session_id and suggestion_id from key
      const keyParts = key.split('/');
      if (keyParts[0] === 'videos' && keyParts.length >= 3) {
        const sessionId = keyParts[1];
        const fileName = keyParts[2];
        const suggestionId = fileName.split('_')[0];
        
        // Update DynamoDB with upload complete status
        await updateUploadComplete(sessionId, suggestionId, key, size);
        
        // Trigger video validation
        await triggerVideoValidation(sessionId, suggestionId, key);
        
        results.push({
          sessionId,
          suggestionId,
          key,
          status: 'uploaded'
        });
      }
    }
  }
  
  return {
    statusCode: 200,
    body: JSON.stringify({ processed: results })
  };
}

async function handleStatusCheck(event) {
  const body = JSON.parse(event.body || '{}');
  const { session_id } = body;
  
  if (!session_id) {
    return {
      statusCode: 400,
      headers: { 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ error: 'Missing session_id' })
    };
  }
  
  // Get session data
  const sessionData = await getSession(session_id);
  if (!sessionData) {
    return {
      statusCode: 404,
      headers: { 'Access-Control-Allow-Origin': '*' },
      body: JSON.stringify({ error: 'Session not found' })
    };
  }
  
  // Check upload status for all videos
  const uploadStatus = {};
  if (sessionData.uploaded_videos && sessionData.uploaded_videos.M) {
    for (const [key, value] of Object.entries(sessionData.uploaded_videos.M)) {
      if (value.M && value.M.s3_key && value.M.s3_key.S) {
        const s3Key = value.M.s3_key.S;
        const exists = await checkS3FileExists(s3Key);
        uploadStatus[key] = {
          status: value.M.status?.S || 'unknown',
          exists: exists,
          s3_key: s3Key
        };
      }
    }
  }
  
  return {
    statusCode: 200,
    headers: { 
      'Access-Control-Allow-Origin': '*',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      session_id: session_id,
      overall_status: sessionData.status?.S || 'unknown',
      uploads: uploadStatus
    })
  };
}

async function updateUploadComplete(sessionId, suggestionId, s3Key, fileSize) {
  const params = {
    TableName: TABLE,
    Key: {
      id: { S: sessionId }
    },
    UpdateExpression: 'SET #uploads.#suggId = :uploadInfo',
    ExpressionAttributeNames: {
      '#uploads': 'uploaded_videos',
      '#suggId': `suggestion_${suggestionId}`
    },
    ExpressionAttributeValues: {
      ':uploadInfo': {
        M: {
          status: { S: 'uploaded' },
          s3_key: { S: s3Key },
          file_size: { N: fileSize.toString() },
          upload_complete_timestamp: { N: Date.now().toString() }
        }
      }
    }
  };
  
  try {
    await dynamoClient.send(new UpdateItemCommand(params));
    console.log(`Updated upload status for session ${sessionId}, suggestion ${suggestionId}`);
  } catch (error) {
    console.error('Error updating upload status:', error);
    throw error;
  }
}

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

async function checkS3FileExists(key) {
  try {
    await s3Client.send(new HeadObjectCommand({
      Bucket: BUCKET,
      Key: key
    }));
    return true;
  } catch (error) {
    if (error.name === 'NotFound') {
      return false;
    }
    console.error('Error checking S3 file:', error);
    return false;
  }
}

async function triggerVideoValidation(sessionId, suggestionId, s3Key) {
  // This would trigger the video-validator Lambda
  // For now, we'll just log it
  console.log(`Triggering video validation for ${s3Key}`);
  // In production, you would use Lambda.invoke or SQS to trigger the next service
}
const { DynamoDBClient, UpdateItemCommand, GetItemCommand } = require('@aws-sdk/client-dynamodb');
const { unmarshall } = require('@aws-sdk/util-dynamodb');

const dynamodb = new DynamoDBClient({ region: 'us-east-1' });
const TABLE = 'Sessions';

exports.handler = async (event) => {
  try {
    const record = event.Records[0];
    const key = record.s3.object.key;
    
    console.log(`New upload detected: ${key}`);
    
    // Parse key: videos/session123/1.mp4
    const parts = key.split('/');
    if (parts[0] !== 'videos' || parts.length !== 3) {
      console.log('Not a video upload, skipping');
      return { statusCode: 200, body: 'Skipped' };
    }
    
    const session_id = parts[1];
    const video_number = parts[2].replace('.mp4', '');
    
    console.log(`Session: ${session_id}, Video: ${video_number}`);
    
    // First check if session exists
    const getResult = await dynamodb.send(new GetItemCommand({
      TableName: TABLE,
      Key: { id: { S: session_id } }
    }));
    
    if (!getResult.Item) {
      console.log(`Session ${session_id} not found in database (will be created by analysis service)`);
      return { statusCode: 200, body: 'Session not found yet' };
    }
    
    // Session exists - update it
    await dynamodb.send(new UpdateItemCommand({
      TableName: TABLE,
      Key: { id: { S: session_id } },
      UpdateExpression: 'SET uploaded_videos.#num = :key, updated_at = :time',
      ExpressionAttributeNames: {
        '#num': video_number
      },
      ExpressionAttributeValues: {
        ':key': { S: key },
        ':time': { S: new Date().toISOString() }
      }
    }));
    
    console.log(`✅ Marked video ${video_number} as uploaded`);
    
    // Check progress
    const sessionData = unmarshall(getResult.Item);
    const totalSuggestions = sessionData.suggestions ? sessionData.suggestions.length : 0;
    const uploadedVideos = sessionData.uploaded_videos || {};
    const uploadedCount = Object.keys(uploadedVideos).length + 1; // +1 for the one we just added
    
    console.log(`Progress: ${uploadedCount}/${totalSuggestions} videos uploaded`);
    
    // If all uploaded, mark ready
    if (uploadedCount >= totalSuggestions && totalSuggestions > 0) {
      await dynamodb.send(new UpdateItemCommand({
        TableName: TABLE,
        Key: { id: { S: session_id } },
        UpdateExpression: 'SET #status = :status',
        ExpressionAttributeNames: { '#status': 'status' },
        ExpressionAttributeValues: { ':status': { S: 'ready_to_process' } }
      }));
      
      console.log(`🎉 All videos uploaded! Ready to process.`);
    }
    
    return { statusCode: 200, body: 'Success' };
    
  } catch (error) {
    console.error('Error:', error);
    return { statusCode: 500, body: error.message };
  }
};

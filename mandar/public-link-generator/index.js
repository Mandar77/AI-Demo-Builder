const { S3Client, HeadObjectCommand, GetObjectCommand } = require('@aws-sdk/client-s3');
const { getSignedUrl } = require('@aws-sdk/s3-request-presigner');
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, UpdateCommand, GetCommand } = require('@aws-sdk/lib-dynamodb');

// Initialize AWS clients
const s3Client = new S3Client({ region: process.env.AWS_REGION || 'us-east-1' });
const ddbClient = new DynamoDBClient({ region: process.env.AWS_REGION || 'us-east-1' });
const docClient = DynamoDBDocumentClient.from(ddbClient);

// Configuration
const CONFIG = {
    BUCKET_NAME: process.env.BUCKET_NAME || 'ai-demo-builder-bucket',
    TABLE_NAME: process.env.TABLE_NAME || 'Sessions',
    BASE_URL: process.env.BASE_URL || null, // CloudFront or custom domain
    DEFAULT_EXPIRY_DAYS: parseInt(process.env.DEFAULT_EXPIRY_DAYS || '7'),
    MAX_EXPIRY_DAYS: parseInt(process.env.MAX_EXPIRY_DAYS || '30')
};

// Link expiry presets (in seconds)
const EXPIRY_PRESETS = {
    '1hour': 3600,
    '24hours': 86400,
    '7days': 604800,
    '30days': 2592000,
    'permanent': null // Uses CloudFront or public bucket URL
};

/**
 * Generate a unique short ID for public links
 */
function generateShortId(length = 8) {
    const chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

/**
 * Check if an S3 object exists
 */
async function checkObjectExists(bucket, key) {
    try {
        const command = new HeadObjectCommand({ Bucket: bucket, Key: key });
        const response = await s3Client.send(command);
        return {
            exists: true,
            contentType: response.ContentType,
            contentLength: response.ContentLength,
            lastModified: response.LastModified
        };
    } catch (error) {
        if (error.name === 'NotFound' || error.$metadata?.httpStatusCode === 404) {
            return { exists: false };
        }
        throw error;
    }
}

/**
 * Generate a presigned URL for S3 object
 */
async function generatePresignedUrl(bucket, key, expiresInSeconds) {
    const command = new GetObjectCommand({
        Bucket: bucket,
        Key: key,
        ResponseContentDisposition: 'inline',
        ResponseContentType: 'video/mp4'
    });
    
    const url = await getSignedUrl(s3Client, command, {
        expiresIn: expiresInSeconds
    });
    
    return url;
}

/**
 * Generate a CloudFront or direct S3 URL (for permanent links)
 */
function generateDirectUrl(bucket, key) {
    if (CONFIG.BASE_URL) {
        // Use CloudFront or custom domain
        return `${CONFIG.BASE_URL}/${key}`;
    }
    // Direct S3 URL (requires bucket to have public access)
    return `https://${bucket}.s3.amazonaws.com/${key}`;
}

/**
 * Get session data from DynamoDB
 */
async function getSession(sessionId) {
    const command = new GetCommand({
        TableName: CONFIG.TABLE_NAME,
        Key: { session_id: sessionId }
    });
    
    const response = await docClient.send(command);
    return response.Item;
}

/**
 * Update session with public link info
 */
async function updateSessionWithLink(sessionId, linkData) {
    const command = new UpdateCommand({
        TableName: CONFIG.TABLE_NAME,
        Key: { session_id: sessionId },
        UpdateExpression: 'SET #links = list_append(if_not_exists(#links, :empty), :link), demo_url = :demoUrl, updated_at = :now',
        ExpressionAttributeNames: {
            '#links': 'public_links'
        },
        ExpressionAttributeValues: {
            ':link': [linkData],
            ':empty': [],
            ':demoUrl': linkData.url,
            ':now': new Date().toISOString()
        }
    });
    
    await docClient.send(command);
}

/**
 * Generate public link for a video
 */
async function generatePublicLink(params) {
    const {
        session_id,
        video_key,
        resolution = '720p',
        expiry = '7days',
        include_thumbnail = true
    } = params;
    
    if (!session_id) {
        throw new Error('session_id is required');
    }
    
    // Determine the video key
    let finalVideoKey = video_key;
    
    if (!finalVideoKey) {
        // Try to find the video from session data
        const session = await getSession(session_id);
        
        if (session && session.final_outputs) {
            // Find the requested resolution
            const output = session.final_outputs.find(o => o.resolution === resolution);
            if (output) {
                finalVideoKey = output.s3_key;
            }
        }
        
        if (!finalVideoKey) {
            // Default pattern
            finalVideoKey = `final/${session_id}/demo_${session_id}_${resolution}.mp4`;
        }
    }
    
    // Check if video exists
    const objectInfo = await checkObjectExists(CONFIG.BUCKET_NAME, finalVideoKey);
    
    if (!objectInfo.exists) {
        throw new Error(`Video not found: ${finalVideoKey}`);
    }
    
    // Calculate expiry
    let expiresInSeconds = EXPIRY_PRESETS[expiry];
    if (expiresInSeconds === undefined) {
        // Try to parse as number of days
        const days = parseInt(expiry);
        if (!isNaN(days) && days > 0 && days <= CONFIG.MAX_EXPIRY_DAYS) {
            expiresInSeconds = days * 86400;
        } else {
            expiresInSeconds = CONFIG.DEFAULT_EXPIRY_DAYS * 86400;
        }
    }
    
    // Generate the URL
    let videoUrl;
    let urlType;
    
    if (expiresInSeconds === null) {
        // Permanent link (CloudFront or direct S3)
        videoUrl = generateDirectUrl(CONFIG.BUCKET_NAME, finalVideoKey);
        urlType = 'permanent';
    } else {
        // Presigned URL with expiry
        videoUrl = await generatePresignedUrl(CONFIG.BUCKET_NAME, finalVideoKey, expiresInSeconds);
        urlType = 'presigned';
    }
    
    // Generate thumbnail URL if requested
    let thumbnailUrl = null;
    if (include_thumbnail) {
        const thumbnailKey = `final/${session_id}/thumbnail.jpg`;
        const thumbExists = await checkObjectExists(CONFIG.BUCKET_NAME, thumbnailKey);
        
        if (thumbExists.exists) {
            if (expiresInSeconds === null) {
                thumbnailUrl = generateDirectUrl(CONFIG.BUCKET_NAME, thumbnailKey);
            } else {
                thumbnailUrl = await generatePresignedUrl(CONFIG.BUCKET_NAME, thumbnailKey, expiresInSeconds);
            }
        }
    }
    
    // Calculate expiry timestamp
    const expiresAt = expiresInSeconds 
        ? new Date(Date.now() + expiresInSeconds * 1000).toISOString()
        : null;
    
    // Create link data
    const linkId = generateShortId();
    const linkData = {
        id: linkId,
        url: videoUrl,
        thumbnail_url: thumbnailUrl,
        video_key: finalVideoKey,
        resolution,
        url_type: urlType,
        file_size: objectInfo.contentLength,
        created_at: new Date().toISOString(),
        expires_at: expiresAt,
        expiry_preset: expiry
    };
    
    // Update session in DynamoDB
    try {
        await updateSessionWithLink(session_id, linkData);
    } catch (error) {
        console.warn('Could not update session (this is OK for testing):', error.message);
    }
    
    return {
        session_id,
        link_id: linkId,
        video_url: videoUrl,
        thumbnail_url: thumbnailUrl,
        resolution,
        file_size: objectInfo.contentLength,
        file_size_mb: (objectInfo.contentLength / (1024 * 1024)).toFixed(2),
        url_type: urlType,
        created_at: linkData.created_at,
        expires_at: expiresAt,
        expires_in_seconds: expiresInSeconds
    };
}

/**
 * Get all public links for a session
 */
async function getSessionLinks(sessionId) {
    const session = await getSession(sessionId);
    
    if (!session) {
        throw new Error('Session not found');
    }
    
    return {
        session_id: sessionId,
        demo_url: session.demo_url || null,
        public_links: session.public_links || [],
        status: session.status
    };
}

/**
 * Generate links for all available resolutions
 */
async function generateAllLinks(sessionId, expiry = '7days') {
    const session = await getSession(sessionId);
    const links = [];
    
    // Default resolutions to try
    const resolutions = ['1080p', '720p', '480p'];
    
    for (const resolution of resolutions) {
        const videoKey = `final/${sessionId}/demo_${sessionId}_${resolution}.mp4`;
        const exists = await checkObjectExists(CONFIG.BUCKET_NAME, videoKey);
        
        if (exists.exists) {
            try {
                const link = await generatePublicLink({
                    session_id: sessionId,
                    video_key: videoKey,
                    resolution,
                    expiry,
                    include_thumbnail: resolution === '720p' // Only include thumbnail once
                });
                links.push(link);
            } catch (error) {
                console.warn(`Could not generate link for ${resolution}:`, error.message);
            }
        }
    }
    
    if (links.length === 0) {
        throw new Error('No video files found for this session');
    }
    
    return {
        session_id: sessionId,
        links_generated: links.length,
        links
    };
}

/**
 * Process the incoming request
 */
async function processRequest(event) {
    // Parse input
    let body;
    if (typeof event.body === 'string') {
        body = JSON.parse(event.body);
    } else if (event.body) {
        body = event.body;
    } else {
        body = event;
    }
    
    const operation = body.operation || 'generate';
    
    switch (operation) {
        case 'generate':
            return await generatePublicLink(body);
            
        case 'generate_all':
            if (!body.session_id) {
                throw new Error('session_id is required');
            }
            return await generateAllLinks(body.session_id, body.expiry);
            
        case 'get_links':
            if (!body.session_id) {
                throw new Error('session_id is required');
            }
            return await getSessionLinks(body.session_id);
            
        default:
            throw new Error(`Unknown operation: ${operation}`);
    }
}

/**
 * Lambda handler
 */
exports.handler = async (event, context) => {
    console.log('Public Link Generator invoked:', JSON.stringify(event, null, 2));
    
    try {
        const result = await processRequest(event);
        
        return {
            statusCode: 200,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            body: JSON.stringify({
                success: true,
                data: result
            })
        };
    } catch (error) {
        console.error('Error:', error);
        
        const statusCode = error.message.includes('required') || error.message.includes('not found') 
            ? 400 
            : 500;
        
        return {
            statusCode,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: JSON.stringify({
                success: false,
                error: error.message
            })
        };
    }
};
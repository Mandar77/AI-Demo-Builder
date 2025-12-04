/**
 * Public Link Generator Service (Service 15)
 * Generates shareable public URLs for completed demo videos
 * 
 * Operations:
 * - generate: Create presigned URL for a video
 * - get: Retrieve existing link info
 * - list: List all links for a session
 * - revoke: Invalidate a link (mark as revoked)
 */

const { S3Client, HeadObjectCommand, GetObjectCommand } = require('@aws-sdk/client-s3');
const { getSignedUrl } = require('@aws-sdk/s3-request-presigner');
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, UpdateCommand, GetCommand } = require('@aws-sdk/lib-dynamodb');

// Initialize AWS clients
const s3Client = new S3Client({ region: process.env.AWS_REGION || 'us-west-1' });
const dynamoClient = new DynamoDBClient({ region: process.env.AWS_REGION || 'us-west-1' });
const docClient = DynamoDBDocumentClient.from(dynamoClient);

// Configuration
const CONFIG = {
    BUCKET_NAME: process.env.BUCKET_NAME || 'cs6620-ai-builder-project',
    TABLE_NAME: process.env.TABLE_NAME || 'ai-demo-sessions',
    PARTITION_KEY: process.env.PARTITION_KEY || 'project_name',
    DEFAULT_EXPIRY: 7 * 24 * 60 * 60, // 7 days in seconds
    MAX_EXPIRY: 7 * 24 * 60 * 60,     // Max 7 days (S3 presigned URL limit)
};

// Expiry presets (in seconds)
const EXPIRY_PRESETS = {
    '1hour': 60 * 60,
    '6hours': 6 * 60 * 60,
    '24hours': 24 * 60 * 60,
    '1day': 24 * 60 * 60,
    '3days': 3 * 24 * 60 * 60,
    '7days': 7 * 24 * 60 * 60,
    '1week': 7 * 24 * 60 * 60,
};

/**
 * Generate a short random ID for links
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
 * Parse expiry string to seconds
 */
function parseExpiry(expiry) {
    if (!expiry) return CONFIG.DEFAULT_EXPIRY;
    
    // Check presets
    if (EXPIRY_PRESETS[expiry.toLowerCase()]) {
        return EXPIRY_PRESETS[expiry.toLowerCase()];
    }
    
    // Parse number (assume seconds)
    const num = parseInt(expiry);
    if (!isNaN(num) && num > 0) {
        return Math.min(num, CONFIG.MAX_EXPIRY);
    }
    
    return CONFIG.DEFAULT_EXPIRY;
}

/**
 * Get file info from S3
 */
async function getFileInfo(s3Key) {
    try {
        const command = new HeadObjectCommand({
            Bucket: CONFIG.BUCKET_NAME,
            Key: s3Key
        });
        const response = await s3Client.send(command);
        
        return {
            exists: true,
            size: response.ContentLength,
            contentType: response.ContentType,
            lastModified: response.LastModified,
            metadata: response.Metadata || {}
        };
    } catch (error) {
        if (error.name === 'NotFound' || error.$metadata?.httpStatusCode === 404) {
            return { exists: false };
        }
        throw error;
    }
}

/**
 * Generate presigned URL for S3 object
 */
async function generatePresignedUrl(s3Key, expiresIn) {
    const command = new GetObjectCommand({
        Bucket: CONFIG.BUCKET_NAME,
        Key: s3Key
    });
    
    const url = await getSignedUrl(s3Client, command, { expiresIn });
    return url;
}

/**
 * Update session status in DynamoDB
 */
async function updateSessionStatus(projectName, status, additionalData = {}) {
    const now = new Date().toISOString();
    
    let updateExpr = 'SET #status = :status, updated_at = :now';
    const exprNames = { '#status': 'status' };
    const exprValues = {
        ':status': status,
        ':now': now
    };
    
    // Add additional data fields
    Object.entries(additionalData).forEach(([key, value], index) => {
        const attrName = `#attr${index}`;
        const attrValue = `:val${index}`;
        updateExpr += `, ${attrName} = ${attrValue}`;
        exprNames[attrName] = key;
        exprValues[attrValue] = value;
    });
    
    try {
        await docClient.send(new UpdateCommand({
            TableName: CONFIG.TABLE_NAME,
            Key: { [CONFIG.PARTITION_KEY]: projectName },
            UpdateExpression: updateExpr,
            ExpressionAttributeNames: exprNames,
            ExpressionAttributeValues: exprValues
        }));
        console.log(`Updated status to '${status}' for project: ${projectName}`);
    } catch (error) {
        console.error(`Warning: Could not update DynamoDB status: ${error.message}`);
        // Don't throw - allow operation to continue
    }
}

/**
 * Get session data from DynamoDB
 */
async function getSessionData(projectName) {
    try {
        const response = await docClient.send(new GetCommand({
            TableName: CONFIG.TABLE_NAME,
            Key: { [CONFIG.PARTITION_KEY]: projectName }
        }));
        return response.Item || null;
    } catch (error) {
        console.error(`Warning: Could not get session data: ${error.message}`);
        return null;
    }
}

/**
 * Add public link to session record
 */
async function addPublicLinkToSession(projectName, linkData) {
    const now = new Date().toISOString();
    
    try {
        await docClient.send(new UpdateCommand({
            TableName: CONFIG.TABLE_NAME,
            Key: { [CONFIG.PARTITION_KEY]: projectName },
            UpdateExpression: 'SET public_links = list_append(if_not_exists(public_links, :empty), :link), demo_url = :url, updated_at = :now, #status = :status',
            ExpressionAttributeNames: { '#status': 'status' },
            ExpressionAttributeValues: {
                ':link': [linkData],
                ':empty': [],
                ':url': linkData.video_url,
                ':now': now,
                ':status': 'link_generated'
            }
        }));
        console.log(`Added public link for project: ${projectName}`);
    } catch (error) {
        console.error(`Warning: Could not add public link to DynamoDB: ${error.message}`);
    }
}

/**
 * Find video file for a session
 */
async function findVideoFile(projectName, resolution = '720p') {
    // Try different possible paths in order of preference
    const possiblePaths = [
        `final/${projectName}/demo_${projectName}_${resolution}.mp4`,
        `final/${projectName}/demo_${resolution}.mp4`,
        `output/${projectName}/stitched_${projectName}.mp4`,
        // Also try with underscores replaced by hyphens
        `final/${projectName.replace(/-/g, '_')}/demo_${projectName.replace(/-/g, '_')}_${resolution}.mp4`,
    ];
    
    for (const path of possiblePaths) {
        const info = await getFileInfo(path);
        if (info.exists) {
            return { key: path, ...info };
        }
    }
    
    return null;
}

/**
 * Find thumbnail for a session
 */
async function findThumbnail(projectName) {
    const possiblePaths = [
        `final/${projectName}/thumbnail.jpg`,
        `final/${projectName}/thumbnail.png`,
        `thumbnails/${projectName}.jpg`,
    ];
    
    for (const path of possiblePaths) {
        const info = await getFileInfo(path);
        if (info.exists) {
            return { key: path, ...info };
        }
    }
    
    return null;
}

/**
 * Format file size for display
 */
function formatFileSize(bytes) {
    if (!bytes) return 'Unknown';
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
}

/**
 * OPERATION: Generate public link
 */
async function generateLink(params) {
    const { project_name, session_id, resolution = '720p', expiry = '7days', include_thumbnail = true } = params;
    
    // Support both project_name and session_id for compatibility
    const projectName = project_name || session_id;
    
    if (!projectName) {
        throw new Error('project_name is required');
    }
    
    console.log(`Generating public link for project: ${projectName}, resolution: ${resolution}`);
    
    // Update status to generating
    await updateSessionStatus(projectName, 'generating_link', {
        processing_step: 'Finding video file'
    });
    
    // Find the video file
    const videoFile = await findVideoFile(projectName, resolution);
    
    if (!videoFile) {
        await updateSessionStatus(projectName, 'link_failed', {
            error_message: `No video found for project ${projectName} at ${resolution}`
        });
        throw new Error(`No video found for project ${projectName}. Available at: final/${projectName}/demo_${projectName}_${resolution}.mp4`);
    }
    
    // Parse expiry
    const expirySeconds = parseExpiry(expiry);
    const expiresAt = new Date(Date.now() + expirySeconds * 1000);
    
    // Generate presigned URL for video
    const videoUrl = await generatePresignedUrl(videoFile.key, expirySeconds);
    
    // Generate link ID
    const linkId = generateShortId(8);
    
    // Prepare response
    const result = {
        project_name: projectName,
        link_id: linkId,
        video_url: videoUrl,
        resolution: resolution,
        file_size: formatFileSize(videoFile.size),
        file_size_bytes: videoFile.size,
        expires_at: expiresAt.toISOString(),
        expires_in_seconds: expirySeconds,
        created_at: new Date().toISOString()
    };
    
    // Include thumbnail if requested
    if (include_thumbnail) {
        const thumbnail = await findThumbnail(projectName);
        if (thumbnail) {
            result.thumbnail_url = await generatePresignedUrl(thumbnail.key, expirySeconds);
        }
    }
    
    // Save link to DynamoDB
    await addPublicLinkToSession(projectName, {
        link_id: linkId,
        video_url: videoUrl,
        thumbnail_url: result.thumbnail_url || null,
        resolution: resolution,
        expires_at: expiresAt.toISOString(),
        created_at: result.created_at
    });
    
    console.log(`Successfully generated link ${linkId} for project ${projectName}`);
    
    return result;
}

/**
 * OPERATION: Get link info
 */
async function getLink(params) {
    const { project_name, session_id, link_id } = params;
    const projectName = project_name || session_id;
    
    if (!projectName) {
        throw new Error('project_name is required');
    }
    
    const sessionData = await getSessionData(projectName);
    
    if (!sessionData || !sessionData.public_links) {
        throw new Error(`No links found for project ${projectName}`);
    }
    
    if (link_id) {
        const link = sessionData.public_links.find(l => l.link_id === link_id);
        if (!link) {
            throw new Error(`Link ${link_id} not found for project ${projectName}`);
        }
        return link;
    }
    
    // Return the most recent link
    return sessionData.public_links[sessionData.public_links.length - 1];
}

/**
 * OPERATION: List all links for a session
 */
async function listLinks(params) {
    const { project_name, session_id } = params;
    const projectName = project_name || session_id;
    
    if (!projectName) {
        throw new Error('project_name is required');
    }
    
    const sessionData = await getSessionData(projectName);
    
    return {
        project_name: projectName,
        links: sessionData?.public_links || [],
        count: sessionData?.public_links?.length || 0,
        demo_url: sessionData?.demo_url || null
    };
}

/**
 * OPERATION: Get session status (for frontend polling)
 */
async function getStatus(params) {
    const { project_name, session_id } = params;
    const projectName = project_name || session_id;
    
    if (!projectName) {
        throw new Error('project_name is required');
    }
    
    const sessionData = await getSessionData(projectName);
    
    if (!sessionData) {
        return {
            project_name: projectName,
            status: 'not_found',
            exists: false
        };
    }
    
    return {
        project_name: projectName,
        status: sessionData.status || 'unknown',
        exists: true,
        demo_url: sessionData.demo_url || null,
        thumbnail_url: sessionData.thumbnail_url || null,
        processing_step: sessionData.processing_step || null,
        error_message: sessionData.error_message || null,
        updated_at: sessionData.updated_at || null,
        public_links_count: sessionData.public_links?.length || 0
    };
}

/**
 * Main Lambda handler
 */
exports.handler = async (event, context) => {
    console.log('Public Link Generator invoked:', JSON.stringify(event, null, 2));
    
    try {
        // Parse request body
        let body;
        if (typeof event.body === 'string') {
            body = JSON.parse(event.body);
        } else if (event.body) {
            body = event.body;
        } else {
            body = event;
        }
        
        // Determine operation
        const operation = body.operation || 'generate';
        
        let result;
        
        switch (operation.toLowerCase()) {
            case 'generate':
                result = await generateLink(body);
                break;
            case 'get':
                result = await getLink(body);
                break;
            case 'list':
                result = await listLinks(body);
                break;
            case 'status':
                result = await getStatus(body);
                break;
            default:
                throw new Error(`Unknown operation: ${operation}. Valid operations: generate, get, list, status`);
        }
        
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
                operation: operation,
                data: result
            })
        };
        
    } catch (error) {
        console.error('Error:', error);
        
        return {
            statusCode: error.message.includes('required') ? 400 : 500,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            body: JSON.stringify({
                success: false,
                error: error.message
            })
        };
    }
};
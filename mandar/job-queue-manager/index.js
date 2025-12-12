const { SQSClient, SendMessageCommand, ReceiveMessageCommand, DeleteMessageCommand, GetQueueAttributesCommand } = require('@aws-sdk/client-sqs');
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, UpdateCommand, GetCommand } = require('@aws-sdk/lib-dynamodb');
const { LambdaClient, InvokeCommand } = require('@aws-sdk/client-lambda');

const sqsClient = new SQSClient({ region: process.env.AWS_REGION || 'us-west-1' });
const ddbClient = new DynamoDBClient({ region: process.env.AWS_REGION || 'us-west-1' });
const docClient = DynamoDBDocumentClient.from(ddbClient);
const lambdaClient = new LambdaClient({ region: process.env.AWS_REGION || 'us-west-1' });

const CONFIG = {
    QUEUE_URL: process.env.QUEUE_URL || 'https://sqs.us-west-1.amazonaws.com/515952579991/demo-builder-video-processing-queue',
    TABLE_NAME: process.env.TABLE_NAME || 'ai-demo-sessions',
    PARTITION_KEY: process.env.PARTITION_KEY || 'project_name',
    BUCKET_NAME: process.env.BUCKET_NAME || 'ai-demo-builder',
    SLIDE_GENERATOR_FUNCTION: process.env.SLIDE_GENERATOR_FUNCTION || 'service-12-slide-generator',
    VIDEO_STITCHER_FUNCTION: process.env.VIDEO_STITCHER_FUNCTION || 'service-13-video-stitcher',
    VIDEO_OPTIMIZER_FUNCTION: process.env.VIDEO_OPTIMIZER_FUNCTION || 'service-14-video-optimizer',
    PUBLIC_LINK_FUNCTION: process.env.PUBLIC_LINK_FUNCTION || 'service-15-public-link',
    JOB_TIMEOUT_MINUTES: parseInt(process.env.JOB_TIMEOUT_MINUTES || '15')
};

const JOB_STATUS = { QUEUED: 'queued', PROCESSING: 'processing', COMPLETED: 'completed', FAILED: 'failed' };

function generateJobId() {
    return `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

async function updateSessionStatus(sessionId, status, additionalData = {}) {
    const updateExprParts = ['#status = :status', 'updated_at = :now'];
    const exprAttrNames = { '#status': 'status' };
    const exprAttrValues = { ':status': status, ':now': new Date().toISOString() };

    Object.entries(additionalData).forEach(([key, value], index) => {
        const attrName = `#attr${index}`;
        const attrValue = `:val${index}`;
        updateExprParts.push(`${attrName} = ${attrValue}`);
        exprAttrNames[attrName] = key;
        exprAttrValues[attrValue] = typeof value === 'object' ? JSON.stringify(value) : value;
    });

    try {
        await docClient.send(new UpdateCommand({
            TableName: CONFIG.TABLE_NAME,
            Key: { [CONFIG.PARTITION_KEY]: sessionId },
            UpdateExpression: 'SET ' + updateExprParts.join(', '),
            ExpressionAttributeNames: exprAttrNames,
            ExpressionAttributeValues: exprAttrValues
        }));
        console.log(`Status updated: ${sessionId} -> ${status}`);
    } catch (error) {
        console.error('DynamoDB update error:', error.message);
    }
}

async function invokeLambda(functionName, payload) {
    console.log(`Invoking ${functionName}`);
    const command = new InvokeCommand({
        FunctionName: functionName,
        InvocationType: 'RequestResponse',
        Payload: JSON.stringify(payload)
    });
    
    const response = await lambdaClient.send(command);
    const resultStr = new TextDecoder().decode(response.Payload);
    const result = JSON.parse(resultStr);
    
    if (response.FunctionError) {
        throw new Error(`${functionName} error: ${result.errorMessage || 'failed'}`);
    }
    
    if (result.body) {
        const body = typeof result.body === 'string' ? JSON.parse(result.body) : result.body;
        if (body.success === false) throw new Error(body.error || `${functionName} failed`);
        return body.data || body;
    }
    return result.data || result;
}

async function runFullPipeline(job) {
    const sessionId = job.sessionId;
    const mediaItems = job.payload.media_items || [];
    const options = job.payload.options || {};
    
    console.log(`[${job.jobId}] Starting pipeline for: ${sessionId}`);

    // STAGE 1: Generate Slides
    await updateSessionStatus(sessionId, 'generating_slides', { processing_step: 'Creating slides', progress: 10 });
    
    const slideDefinitions = mediaItems.filter(item => item.type === 'slide' && item.content);
    let generatedSlides = {};
    
    if (slideDefinitions.length > 0) {
        try {
            const slides = slideDefinitions.map((item, i) => ({
                id: item.id || `slide_${i}`,
                type: item.slideType || 'section',
                content: item.content,
                order: item.order || i
            }));
            
            const slideResult = await invokeLambda(CONFIG.SLIDE_GENERATOR_FUNCTION, {
                project_name: sessionId,
                slides: slides
            });
            
            if (slideResult.slides) {
                slideResult.slides.forEach(s => { generatedSlides[s.id] = s.s3_key; });
            }
            console.log(`Generated ${Object.keys(generatedSlides).length} slides`);
        } catch (error) {
            console.error('Slide generation error:', error.message);
        }
    }

    await updateSessionStatus(sessionId, 'slides_ready', { processing_step: 'Slides ready', progress: 25 });

    // STAGE 2: Stitch Videos
    await updateSessionStatus(sessionId, 'stitching', { processing_step: 'Stitching videos', progress: 35 });
    
    const stitchMediaItems = mediaItems.map(item => {
        if (item.type === 'slide') {
            const s3Key = generatedSlides[item.id || `slide_${item.order}`];
            return s3Key ? { type: 'slide', key: s3Key, order: item.order, duration: item.duration || 3 } : null;
        }
        return { type: 'video', key: item.key, order: item.order };
    }).filter(Boolean);

    if (stitchMediaItems.length === 0) throw new Error('No valid media items to stitch');

    const stitchResult = await invokeLambda(CONFIG.VIDEO_STITCHER_FUNCTION, {
        project_name: sessionId,
        media_items: stitchMediaItems
    });
    
    const stitchedVideoKey = stitchResult.output_key;
    if (!stitchedVideoKey) throw new Error('Stitcher did not return output_key');
    
    console.log(`Stitched: ${stitchedVideoKey}`);
    await updateSessionStatus(sessionId, 'stitched', { processing_step: 'Videos stitched', progress: 55 });

    // STAGE 3: Optimize Video
    await updateSessionStatus(sessionId, 'optimizing', { processing_step: 'Optimizing video', progress: 70 });
    
    const optimizeResult = await invokeLambda(CONFIG.VIDEO_OPTIMIZER_FUNCTION, {
        project_name: sessionId,
        input_key: stitchedVideoKey,
        resolutions: options.resolutions || ['720p'],
        generate_thumbnail: true
    });
    
    const outputs = optimizeResult.outputs || [];
    console.log(`Optimized: ${outputs.length} outputs`);
    
    await updateSessionStatus(sessionId, 'optimized', { processing_step: 'Video optimized', progress: 85 });

    // STAGE 4: Generate Public Link
    await updateSessionStatus(sessionId, 'generating_link', { processing_step: 'Creating link', progress: 90 });
    
    let publicLinkResult;
    try {
        publicLinkResult = await invokeLambda(CONFIG.PUBLIC_LINK_FUNCTION, {
            operation: 'generate',
            project_name: sessionId,
            resolution: '720p',
            expiry: options.link_expiry || '7days',
            include_thumbnail: true
        });
    } catch (error) {
        console.error('Public link error:', error.message);
        publicLinkResult = {
            video_url: outputs[0]?.download_url,
            thumbnail_url: optimizeResult.thumbnail?.download_url
        };
    }

    // COMPLETE
    const finalDemoUrl = publicLinkResult.video_url || outputs[0]?.download_url;
    const finalThumbnailUrl = publicLinkResult.thumbnail_url || optimizeResult.thumbnail?.download_url;

    await updateSessionStatus(sessionId, 'completed', {
        processing_step: 'Your demo video is ready!',
        demo_url: finalDemoUrl,
        thumbnail_url: finalThumbnailUrl,
        outputs: outputs,
        completed_at: new Date().toISOString(),
        progress: 100
    });

    console.log(`Pipeline complete! URL: ${finalDemoUrl}`);
    return { demo_url: finalDemoUrl, thumbnail_url: finalThumbnailUrl };
}

/**
 * Submit job to SQS queue - RETURNS IMMEDIATELY
 */
async function submitJobToQueue(jobData) {
    const jobId = generateJobId();
    const sessionId = jobData.session_id || jobData.project_name;
    const timestamp = new Date().toISOString();

    const job = {
        jobId,
        sessionId,
        jobType: 'full_pipeline',
        payload: jobData.payload || {},
        createdAt: timestamp
    };

    // Send to SQS for async processing
    await sqsClient.send(new SendMessageCommand({
        QueueUrl: CONFIG.QUEUE_URL,
        MessageBody: JSON.stringify(job),
        MessageAttributes: {
            'JobType': { DataType: 'String', StringValue: 'full_pipeline' },
            'SessionId': { DataType: 'String', StringValue: sessionId }
        }
    }));

    // Update status to queued
    await updateSessionStatus(sessionId, 'queued', {
        current_job_id: jobId,
        queued_at: timestamp,
        processing_step: 'Job queued for processing',
        progress: 5
    });

    console.log(`Job ${jobId} queued for session ${sessionId}`);

    return {
        jobId,
        sessionId,
        status: 'queued',
        message: 'Job submitted successfully. Processing will begin shortly.',
        queuedAt: timestamp
    };
}

async function getJobStatus(sessionId) {
    const response = await docClient.send(new GetCommand({
        TableName: CONFIG.TABLE_NAME,
        Key: { [CONFIG.PARTITION_KEY]: sessionId }
    }));
    
    if (!response.Item) {
        return { sessionId, status: 'not_found', exists: false };
    }
    
    return {
        sessionId,
        status: response.Item.status,
        processing_step: response.Item.processing_step,
        progress: response.Item.progress || 0,
        demo_url: response.Item.demo_url,
        thumbnail_url: response.Item.thumbnail_url,
        outputs: response.Item.outputs,
        error_message: response.Item.error_message,
        updated_at: response.Item.updated_at,
        exists: true
    };
}

async function getQueueStats() {
    const response = await sqsClient.send(new GetQueueAttributesCommand({
        QueueUrl: CONFIG.QUEUE_URL,
        AttributeNames: ['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
    }));
    return {
        pendingJobs: parseInt(response.Attributes.ApproximateNumberOfMessages || '0'),
        processingJobs: parseInt(response.Attributes.ApproximateNumberOfMessagesNotVisible || '0')
    };
}

async function processRequest(event) {
    let body;
    if (typeof event.body === 'string') {
        body = JSON.parse(event.body);
    } else if (event.body) {
        body = event.body;
    } else {
        body = event;
    }
    
    const operation = body.operation || 'submit';
    
    switch (operation) {
        case 'start_pipeline':
        case 'submit':
            const sessionId = body.project_name || body.session_id;
            if (!sessionId) throw new Error('project_name is required');
            body.session_id = sessionId;
            // ALWAYS queue - never process synchronously from API Gateway
            return await submitJobToQueue(body);
            
        case 'status':
            const statusSessionId = body.project_name || body.session_id;
            if (!statusSessionId) throw new Error('project_name is required');
            return await getJobStatus(statusSessionId);
            
        case 'stats':
            return await getQueueStats();
            
        default:
            throw new Error(`Unknown operation: ${operation}`);
    }
}

/**
 * Lambda handler
 */
exports.handler = async (event, context) => {
    console.log('Job Queue Manager invoked');
    
    // SQS trigger - process the pipeline
    if (event.Records && event.Records[0]?.eventSource === 'aws:sqs') {
        console.log(`Processing ${event.Records.length} SQS messages`);
        const results = [];
        
        for (const record of event.Records) {
            const job = JSON.parse(record.body);
            console.log(`Processing job: ${job.jobId}`);
            
            try {
                await updateSessionStatus(job.sessionId, 'processing', {
                    processing_step: 'Starting pipeline',
                    progress: 8
                });
                
                const result = await runFullPipeline(job);
                results.push({ jobId: job.jobId, status: 'completed', result });
            } catch (error) {
                console.error(`Job ${job.jobId} failed:`, error);
                await updateSessionStatus(job.sessionId, 'failed', {
                    error_message: error.message,
                    failed_at: new Date().toISOString()
                });
                results.push({ jobId: job.jobId, status: 'failed', error: error.message });
            }
        }
        return { processed: results };
    }
    
    // API Gateway - queue the job and return immediately
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
            body: JSON.stringify({ success: true, data: result })
        };
    } catch (error) {
        console.error('Error:', error);
        return {
            statusCode: error.message.includes('required') ? 400 : 500,
            headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' },
            body: JSON.stringify({ success: false, error: error.message })
        };
    }
};
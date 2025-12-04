const { SQSClient, SendMessageCommand, ReceiveMessageCommand, DeleteMessageCommand, GetQueueAttributesCommand } = require('@aws-sdk/client-sqs');
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, UpdateCommand, GetCommand } = require('@aws-sdk/lib-dynamodb');
const { LambdaClient, InvokeCommand } = require('@aws-sdk/client-lambda');

// Initialize AWS clients
const sqsClient = new SQSClient({ region: process.env.AWS_REGION || 'us-west-1' });
const ddbClient = new DynamoDBClient({ region: process.env.AWS_REGION || 'us-west-1' });
const docClient = DynamoDBDocumentClient.from(ddbClient);
const lambdaClient = new LambdaClient({ region: process.env.AWS_REGION || 'us-west-1' });

// Configuration
const CONFIG = {
    QUEUE_URL: process.env.QUEUE_URL || '',
    TABLE_NAME: process.env.TABLE_NAME || 'ai-demo-sessions',
    PARTITION_KEY: process.env.PARTITION_KEY || 'project_name',
    VIDEO_STITCHER_FUNCTION: process.env.VIDEO_STITCHER_FUNCTION || 'service-13-video-stitcher',
    VIDEO_OPTIMIZER_FUNCTION: process.env.VIDEO_OPTIMIZER_FUNCTION || 'service-14-video-optimizer',
    MAX_CONCURRENT_JOBS: parseInt(process.env.MAX_CONCURRENT_JOBS || '3'),
    JOB_TIMEOUT_MINUTES: parseInt(process.env.JOB_TIMEOUT_MINUTES || '15')
};

// Job types
const JOB_TYPES = {
    STITCH_VIDEO: 'stitch_video',
    OPTIMIZE_VIDEO: 'optimize_video',
    GENERATE_SLIDES: 'generate_slides',
    FULL_PIPELINE: 'full_pipeline'
};

// Job priorities (lower = higher priority)
const PRIORITIES = {
    HIGH: 1,
    NORMAL: 5,
    LOW: 10
};

// Job statuses
const JOB_STATUS = {
    QUEUED: 'queued',
    PROCESSING: 'processing',
    COMPLETED: 'completed',
    FAILED: 'failed'
};

/**
 * Generate a unique job ID
 */
function generateJobId() {
    return `job_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Update session status in DynamoDB for frontend tracking
 */
async function updateSessionStatus(sessionId, status, additionalData = {}) {
    const updateExprParts = ['#status = :status', 'updated_at = :now'];
    const exprAttrNames = { '#status': 'status' };
    const exprAttrValues = {
        ':status': status,
        ':now': new Date().toISOString()
    };

    Object.entries(additionalData).forEach(([key, value], index) => {
        const attrName = `#attr${index}`;
        const attrValue = `:val${index}`;
        updateExprParts.push(`${attrName} = ${attrValue}`);
        exprAttrNames[attrName] = key;
        exprAttrValues[attrValue] = typeof value === 'object' ? JSON.stringify(value) : value;
    });

    const command = new UpdateCommand({
        TableName: CONFIG.TABLE_NAME,
        Key: { [CONFIG.PARTITION_KEY]: sessionId },
        UpdateExpression: 'SET ' + updateExprParts.join(', '),
        ExpressionAttributeNames: exprAttrNames,
        ExpressionAttributeValues: exprAttrValues
    });

    try {
        await docClient.send(command);
        console.log(`Status updated: ${sessionId} -> ${status}`);
    } catch (error) {
        console.error('DynamoDB update error:', error.message);
    }
}

/**
 * Submit a job to the SQS queue
 */
async function submitJob(jobData) {
    const jobId = generateJobId();
    const timestamp = new Date().toISOString();
    let priority = jobData.priority || PRIORITIES.NORMAL;
if (typeof priority === 'string') {
    priority = PRIORITIES[priority.toUpperCase()] || PRIORITIES.NORMAL;
}


    const job = {
        jobId,
        sessionId: jobData.session_id,
        jobType: jobData.job_type || JOB_TYPES.FULL_PIPELINE,
    priority: priority,
        payload: jobData.payload || {},
        status: JOB_STATUS.QUEUED,
        createdAt: timestamp,
        updatedAt: timestamp
    };
    
    const delaySeconds = job.priority === PRIORITIES.HIGH ? 0 : Math.min(job.priority * 2, 900);
    
    const command = new SendMessageCommand({
        QueueUrl: CONFIG.QUEUE_URL,
        MessageBody: JSON.stringify(job),
        DelaySeconds: delaySeconds,
        MessageAttributes: {
            'JobType': {
                DataType: 'String',
                StringValue: job.jobType
            },
            'Priority': {
                DataType: 'Number',
                StringValue: job.priority.toString()
            },
            'SessionId': {
                DataType: 'String',
                StringValue: job.sessionId
            }
        }
    });
    
    const result = await sqsClient.send(command);
    
    // STATUS UPDATE: queued
    await updateSessionStatus(job.sessionId, 'queued', {
        current_job_id: jobId,
        job_type: job.jobType,
        queued_at: timestamp,
        message_id: result.MessageId
    });
    
    return {
        jobId,
        messageId: result.MessageId,
        status: JOB_STATUS.QUEUED,
        queuedAt: timestamp
    };
}

/**
 * Invoke the Video Stitcher Lambda
 */
async function invokeVideoStitcher(job) {
    const payload = {
        session_id: job.sessionId,
        ...job.payload
    };
    
    const command = new InvokeCommand({
        FunctionName: CONFIG.VIDEO_STITCHER_FUNCTION,
        InvocationType: 'RequestResponse',
        Payload: JSON.stringify(payload)
    });
    
    const response = await lambdaClient.send(command);
    const result = JSON.parse(new TextDecoder().decode(response.Payload));
    
    if (response.FunctionError) {
        throw new Error(result.errorMessage || 'Video stitcher failed');
    }
    
    return result;
}

/**
 * Invoke the Video Optimizer Lambda
 */
async function invokeVideoOptimizer(job) {
    const payload = {
        session_id: job.sessionId,
        ...job.payload
    };
    
    const command = new InvokeCommand({
        FunctionName: CONFIG.VIDEO_OPTIMIZER_FUNCTION,
        InvocationType: 'RequestResponse',
        Payload: JSON.stringify(payload)
    });
    
    const response = await lambdaClient.send(command);
    const result = JSON.parse(new TextDecoder().decode(response.Payload));
    
    if (response.FunctionError) {
        throw new Error(result.errorMessage || 'Video optimizer failed');
    }
    
    return result;
}

/**
 * Run the full video processing pipeline
 */
async function runFullPipeline(job) {
    const results = {
        stages: []
    };
    
    // STATUS UPDATE: processing
    await updateSessionStatus(job.sessionId, 'processing', {
        processing_step: 'Starting video pipeline',
        pipeline_started_at: new Date().toISOString()
    });
    
    // Stage 1: Stitch videos
    console.log(`[${job.jobId}] Stage 1: Stitching videos...`);
    await updateSessionStatus(job.sessionId, 'processing', {
        processing_step: 'Stitching videos'
    });
    
    const stitchResult = await invokeVideoStitcher(job);
    results.stages.push({ stage: 'stitch', result: stitchResult });
    
    // Extract output key from stitch result
    let stitchedVideoKey;
    if (stitchResult.body) {
        const body = typeof stitchResult.body === 'string' ? JSON.parse(stitchResult.body) : stitchResult.body;
        stitchedVideoKey = body.data?.output_key || body.output_key;
    } else {
        stitchedVideoKey = stitchResult.data?.output_key || stitchResult.output_key;
    }
    
    if (!stitchedVideoKey) {
        throw new Error('Video stitcher did not return output_key');
    }
    
    // Stage 2: Optimize video
    console.log(`[${job.jobId}] Stage 2: Optimizing video...`);
    await updateSessionStatus(job.sessionId, 'processing', {
        processing_step: 'Optimizing video'
    });
    
    const optimizePayload = {
        ...job,
        payload: {
            ...job.payload,
            input_key: stitchedVideoKey
        }
    };
    const optimizeResult = await invokeVideoOptimizer(optimizePayload);
    results.stages.push({ stage: 'optimize', result: optimizeResult });
    
    // Extract final outputs
    let finalOutputs;
    if (optimizeResult.body) {
        const body = typeof optimizeResult.body === 'string' ? JSON.parse(optimizeResult.body) : optimizeResult.body;
        finalOutputs = body.data?.outputs || body.outputs;
    } else {
        finalOutputs = optimizeResult.data?.outputs || optimizeResult.outputs;
    }
    
    results.finalVideo = finalOutputs;
    
    return results;
}

/**
 * Process jobs from the queue
 */
async function processJobs(maxJobs = 1) {
    const processedJobs = [];
    
    for (let i = 0; i < maxJobs; i++) {
        const receiveCommand = new ReceiveMessageCommand({
            QueueUrl: CONFIG.QUEUE_URL,
            MaxNumberOfMessages: 1,
            WaitTimeSeconds: 5,
            MessageAttributeNames: ['All'],
            VisibilityTimeout: CONFIG.JOB_TIMEOUT_MINUTES * 60
        });
        
        const response = await sqsClient.send(receiveCommand);
        
        if (!response.Messages || response.Messages.length === 0) {
            console.log('No messages in queue');
            break;
        }
        
        const message = response.Messages[0];
        const job = JSON.parse(message.Body);
        
        console.log(`Processing job: ${job.jobId}`);
        
        try {
            // STATUS UPDATE: processing
            await updateSessionStatus(job.sessionId, 'processing', {
                current_job_id: job.jobId,
                started_at: new Date().toISOString()
            });
            
            let result;
            switch (job.jobType) {
                case JOB_TYPES.STITCH_VIDEO:
                    result = await invokeVideoStitcher(job);
                    break;
                case JOB_TYPES.OPTIMIZE_VIDEO:
                    result = await invokeVideoOptimizer(job);
                    break;
                case JOB_TYPES.FULL_PIPELINE:
                    result = await runFullPipeline(job);
                    break;
                default:
                    throw new Error(`Unknown job type: ${job.jobType}`);
            }
            
            // Delete message from queue
            const deleteCommand = new DeleteMessageCommand({
                QueueUrl: CONFIG.QUEUE_URL,
                ReceiptHandle: message.ReceiptHandle
            });
            await sqsClient.send(deleteCommand);
            
            // STATUS UPDATE: completed (final status set by optimizer)
            processedJobs.push({
                jobId: job.jobId,
                status: JOB_STATUS.COMPLETED,
                result
            });
            
        } catch (error) {
            console.error(`Error processing job ${job.jobId}:`, error);
            
            // STATUS UPDATE: failed
            await updateSessionStatus(job.sessionId, 'failed', {
                current_job_id: job.jobId,
                error_message: error.message,
                failed_at: new Date().toISOString()
            });
            
            processedJobs.push({
                jobId: job.jobId,
                status: JOB_STATUS.FAILED,
                error: error.message
            });
        }
    }
    
    return processedJobs;
}

/**
 * Get queue statistics
 */
async function getQueueStats() {
    const command = new GetQueueAttributesCommand({
        QueueUrl: CONFIG.QUEUE_URL,
        AttributeNames: [
            'ApproximateNumberOfMessages',
            'ApproximateNumberOfMessagesNotVisible',
            'ApproximateNumberOfMessagesDelayed'
        ]
    });
    
    const response = await sqsClient.send(command);
    
    return {
        pendingJobs: parseInt(response.Attributes.ApproximateNumberOfMessages || '0'),
        processingJobs: parseInt(response.Attributes.ApproximateNumberOfMessagesNotVisible || '0'),
        delayedJobs: parseInt(response.Attributes.ApproximateNumberOfMessagesDelayed || '0')
    };
}

/**
 * Get job status by session ID
 */
async function getJobStatus(sessionId) {
    const command = new GetCommand({
        TableName: CONFIG.TABLE_NAME,
        Key: { [CONFIG.PARTITION_KEY]: sessionId }
    });
    
    const response = await docClient.send(command);
    
    if (!response.Item) {
        return { error: 'Session not found' };
    }
    
    return {
        sessionId,
        status: response.Item.status,
        currentJobId: response.Item.current_job_id,
        processingStep: response.Item.processing_step,
        demoUrl: response.Item.demo_url,
        updatedAt: response.Item.updated_at
    };
}

/**
 * Process incoming request
 */
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
        case 'submit':
        // Support both project_name and session_id
        body.session_id = body.project_name || body.session_id;
            if (!body.session_id) {
                throw new Error('project_name is required');
            }
            return await submitJob(body);
            
        case 'process':
            const maxJobs = body.max_jobs || 1;
            return await processJobs(maxJobs);
            
        case 'status':
            // Support both project_name and session_id
            const statusSessionId = body.project_name || body.session_id;
        if (!statusSessionId) {
        throw new Error('project_name is required for status check');
    }
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
    console.log('Job Queue Manager invoked:', JSON.stringify(event, null, 2));
    
    // Check if triggered by SQS
    if (event.Records && event.Records[0]?.eventSource === 'aws:sqs') {
        const results = [];
        for (const record of event.Records) {
            const job = JSON.parse(record.body);
            try {
                await updateSessionStatus(job.sessionId, 'processing', {
                    current_job_id: job.jobId,
                    processing_step: 'Processing from SQS trigger'
                });
                
                let result;
                switch (job.jobType) {
                    case JOB_TYPES.STITCH_VIDEO:
                        result = await invokeVideoStitcher(job);
                        break;
                    case JOB_TYPES.OPTIMIZE_VIDEO:
                        result = await invokeVideoOptimizer(job);
                        break;
                    case JOB_TYPES.FULL_PIPELINE:
                        result = await runFullPipeline(job);
                        break;
                }
                results.push({ jobId: job.jobId, status: 'completed' });
            } catch (error) {
                await updateSessionStatus(job.sessionId, 'failed', {
                    error_message: error.message,
                    failed_at: new Date().toISOString()
                });
                results.push({ jobId: job.jobId, status: 'failed', error: error.message });
            }
        }
        return { processed: results };
    }
    
    // Handle API Gateway or direct invocation
    try {
        const result = await processRequest(event);
        
        return {
            statusCode: 200,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            body: JSON.stringify({
                success: true,
                data: result
            })
        };
    } catch (error) {
        console.error('Error:', error);
        
        return {
            statusCode: error.message.includes('required') ? 400 : 500,
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

// Export for testing
module.exports.JOB_TYPES = JOB_TYPES;
module.exports.PRIORITIES = PRIORITIES;
module.exports.JOB_STATUS = JOB_STATUS;
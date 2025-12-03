const { SQSClient, SendMessageCommand, ReceiveMessageCommand, DeleteMessageCommand, GetQueueAttributesCommand } = require('@aws-sdk/client-sqs');
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, UpdateCommand, GetCommand } = require('@aws-sdk/lib-dynamodb');
const { LambdaClient, InvokeCommand } = require('@aws-sdk/client-lambda');

// Initialize AWS clients
const sqsClient = new SQSClient({ region: process.env.AWS_REGION || 'us-east-1' });
const ddbClient = new DynamoDBClient({ region: process.env.AWS_REGION || 'us-east-1' });
const docClient = DynamoDBDocumentClient.from(ddbClient);
const lambdaClient = new LambdaClient({ region: process.env.AWS_REGION || 'us-east-1' });

// Configuration
const CONFIG = {
    QUEUE_URL: process.env.QUEUE_URL || '',
    TABLE_NAME: process.env.TABLE_NAME || 'Sessions',
    VIDEO_STITCHER_FUNCTION: process.env.VIDEO_STITCHER_FUNCTION || 'video-stitcher',
    VIDEO_OPTIMIZER_FUNCTION: process.env.VIDEO_OPTIMIZER_FUNCTION || 'video-optimizer',
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
 * Submit a job to the SQS queue
 */
async function submitJob(jobData) {
    const jobId = generateJobId();
    const timestamp = new Date().toISOString();
    
    const job = {
        jobId,
        sessionId: jobData.session_id,
        jobType: jobData.job_type || JOB_TYPES.FULL_PIPELINE,
        priority: jobData.priority || PRIORITIES.NORMAL,
        payload: jobData.payload || {},
        status: JOB_STATUS.QUEUED,
        createdAt: timestamp,
        updatedAt: timestamp
    };
    
    // Send to SQS with delay based on priority
    const delaySeconds = Math.min(job.priority * 2, 900); // Max 15 minutes
    
    const command = new SendMessageCommand({
        QueueUrl: CONFIG.QUEUE_URL,
        MessageBody: JSON.stringify(job),
        DelaySeconds: job.priority === PRIORITIES.HIGH ? 0 : delaySeconds,
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
    
    // Update session in DynamoDB
    await updateSessionJobStatus(job.sessionId, jobId, JOB_STATUS.QUEUED, {
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
 * Process jobs from the queue (called by Lambda trigger or manually)
 */
async function processJobs(maxJobs = 1) {
    const processedJobs = [];
    
    for (let i = 0; i < maxJobs; i++) {
        // Receive message from queue
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
            // Update status to processing
            await updateSessionJobStatus(job.sessionId, job.jobId, JOB_STATUS.PROCESSING, {
                started_at: new Date().toISOString()
            });
            
            // Process based on job type
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
            
            // Delete message from queue (job completed)
            const deleteCommand = new DeleteMessageCommand({
                QueueUrl: CONFIG.QUEUE_URL,
                ReceiptHandle: message.ReceiptHandle
            });
            await sqsClient.send(deleteCommand);
            
            // Update status to completed
            await updateSessionJobStatus(job.sessionId, job.jobId, JOB_STATUS.COMPLETED, {
                completed_at: new Date().toISOString(),
                result
            });
            
            processedJobs.push({
                jobId: job.jobId,
                status: JOB_STATUS.COMPLETED,
                result
            });
            
        } catch (error) {
            console.error(`Error processing job ${job.jobId}:`, error);
            
            // Update status to failed
            await updateSessionJobStatus(job.sessionId, job.jobId, JOB_STATUS.FAILED, {
                failed_at: new Date().toISOString(),
                error: error.message
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
    
    // Stage 1: Stitch videos
    console.log(`[${job.jobId}] Stage 1: Stitching videos...`);
    const stitchResult = await invokeVideoStitcher(job);
    results.stages.push({ stage: 'stitch', result: stitchResult });
    
    // Stage 2: Optimize video
    console.log(`[${job.jobId}] Stage 2: Optimizing video...`);
    const optimizePayload = {
        ...job,
        payload: {
            ...job.payload,
            input_key: stitchResult.body?.output_key || stitchResult.output_key
        }
    };
    const optimizeResult = await invokeVideoOptimizer(optimizePayload);
    results.stages.push({ stage: 'optimize', result: optimizeResult });
    
    results.finalVideo = optimizeResult.body?.outputs || optimizeResult.outputs;
    
    return results;
}

/**
 * Update session job status in DynamoDB
 */
async function updateSessionJobStatus(sessionId, jobId, status, additionalData = {}) {
    const command = new UpdateCommand({
        TableName: CONFIG.TABLE_NAME,
        Key: { session_id: sessionId },
        UpdateExpression: 'SET #jobs.#jobId = :jobData, #status = :sessionStatus, updated_at = :now',
        ExpressionAttributeNames: {
            '#jobs': 'jobs',
            '#jobId': jobId,
            '#status': 'status'
        },
        ExpressionAttributeValues: {
            ':jobData': {
                status,
                updated_at: new Date().toISOString(),
                ...additionalData
            },
            ':sessionStatus': status === JOB_STATUS.COMPLETED ? 'completed' : 
                             status === JOB_STATUS.FAILED ? 'failed' : 'processing',
            ':now': new Date().toISOString()
        }
    });
    
    try {
        await docClient.send(command);
    } catch (error) {
        // If jobs map doesn't exist, create it
        if (error.name === 'ValidationException') {
            const initCommand = new UpdateCommand({
                TableName: CONFIG.TABLE_NAME,
                Key: { session_id: sessionId },
                UpdateExpression: 'SET #jobs = :jobs, #status = :sessionStatus, updated_at = :now',
                ExpressionAttributeNames: {
                    '#jobs': 'jobs',
                    '#status': 'status'
                },
                ExpressionAttributeValues: {
                    ':jobs': {
                        [jobId]: {
                            status,
                            updated_at: new Date().toISOString(),
                            ...additionalData
                        }
                    },
                    ':sessionStatus': 'processing',
                    ':now': new Date().toISOString()
                }
            });
            await docClient.send(initCommand);
        } else {
            throw error;
        }
    }
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
        Key: { session_id: sessionId }
    });
    
    const response = await docClient.send(command);
    
    if (!response.Item) {
        return { error: 'Session not found' };
    }
    
    return {
        sessionId,
        status: response.Item.status,
        jobs: response.Item.jobs || {},
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
            if (!body.session_id) {
                throw new Error('session_id is required');
            }
            return await submitJob(body);
            
        case 'process':
            const maxJobs = body.max_jobs || 1;
            return await processJobs(maxJobs);
            
        case 'status':
            if (!body.session_id) {
                throw new Error('session_id is required for status check');
            }
            return await getJobStatus(body.session_id);
            
        case 'stats':
            return await getQueueStats();
            
        default:
            throw new Error(`Unknown operation: ${operation}`);
    }
}

/**
 * Lambda handler - can be triggered by API Gateway, SQS, or direct invocation
 */
exports.handler = async (event, context) => {
    console.log('Job Queue Manager invoked:', JSON.stringify(event, null, 2));
    
    // Check if triggered by SQS
    if (event.Records && event.Records[0]?.eventSource === 'aws:sqs') {
        const results = [];
        for (const record of event.Records) {
            const job = JSON.parse(record.body);
            try {
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
                await updateSessionJobStatus(job.sessionId, job.jobId, JOB_STATUS.COMPLETED, {
                    completed_at: new Date().toISOString(),
                    result
                });
                results.push({ jobId: job.jobId, status: 'completed' });
            } catch (error) {
                await updateSessionJobStatus(job.sessionId, job.jobId, JOB_STATUS.FAILED, {
                    failed_at: new Date().toISOString(),
                    error: error.message
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
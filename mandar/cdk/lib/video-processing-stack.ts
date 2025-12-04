import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as path from 'path';
import { Construct } from 'constructs';

export class VideoProcessingStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ==========================================
    // SHARED RESOURCES (may already exist from other team members)
    // ==========================================

    // Reference existing S3 bucket (created by team)
    const bucket = s3.Bucket.fromBucketName(this, 'DemoBucket', 'ai-demo-builder-bucket');

    // Reference existing DynamoDB table (created by team)
    const sessionsTable = dynamodb.Table.fromTableName(this, 'SessionsTable', 'Sessions');

    // Reference existing FFmpeg Layer (created by Sampada)
    // Replace with actual ARN from your team
    const ffmpegLayerArn = 'arn:aws:lambda:us-east-1:ACCOUNT_ID:layer:ffmpeg-layer:1';
    const ffmpegLayer = lambda.LayerVersion.fromLayerVersionArn(this, 'FFmpegLayer', ffmpegLayerArn);

    // ==========================================
    // SQS QUEUE (Service 11 dependency)
    // ==========================================

    const videoProcessingQueue = new sqs.Queue(this, 'VideoProcessingQueue', {
      queueName: 'video-processing-jobs',
      visibilityTimeout: cdk.Duration.minutes(15),
      retentionPeriod: cdk.Duration.days(1),
    });

    // ==========================================
    // SERVICE 12: SLIDE GENERATOR
    // ==========================================

    const slideGenerator = new lambda.Function(this, 'SlideGenerator', {
      functionName: 'slide-generator',
      runtime: lambda.Runtime.NODEJS_18_X,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../slide-generator')),
      timeout: cdk.Duration.minutes(1),
      memorySize: 1024,
      environment: {
        BUCKET_NAME: bucket.bucketName,
        TABLE_NAME: sessionsTable.tableName,
      },
    });

    // Grant permissions
    bucket.grantReadWrite(slideGenerator);
    sessionsTable.grantReadWriteData(slideGenerator);

    // ==========================================
    // SERVICE 13: VIDEO STITCHER
    // ==========================================

    const videoStitcher = new lambda.Function(this, 'VideoStitcher', {
      functionName: 'video-stitcher',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'lambda_function.lambda_handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../video-stitcher'), {
        bundling: {
          image: lambda.Runtime.PYTHON_3_11.bundlingImage,
          command: [
            'bash', '-c',
            'pip install -r requirements.txt -t /asset-output && cp lambda_function.py /asset-output'
          ],
        },
      }),
      timeout: cdk.Duration.minutes(15),
      memorySize: 3008,
      ephemeralStorageSize: cdk.Size.gibibytes(10),
      layers: [ffmpegLayer],
      environment: {
        BUCKET_NAME: bucket.bucketName,
        TABLE_NAME: sessionsTable.tableName,
        FFMPEG_PATH: '/opt/bin/ffmpeg',
        FFPROBE_PATH: '/opt/bin/ffprobe',
      },
    });

    bucket.grantReadWrite(videoStitcher);
    sessionsTable.grantReadWriteData(videoStitcher);

    // ==========================================
    // SERVICE 14: VIDEO OPTIMIZER
    // ==========================================

    const videoOptimizer = new lambda.Function(this, 'VideoOptimizer', {
      functionName: 'video-optimizer',
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'lambda_function.lambda_handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../video-optimizer'), {
        bundling: {
          image: lambda.Runtime.PYTHON_3_11.bundlingImage,
          command: [
            'bash', '-c',
            'pip install -r requirements.txt -t /asset-output && cp lambda_function.py /asset-output'
          ],
        },
      }),
      timeout: cdk.Duration.minutes(15),
      memorySize: 3008,
      ephemeralStorageSize: cdk.Size.gibibytes(10),
      layers: [ffmpegLayer],
      environment: {
        BUCKET_NAME: bucket.bucketName,
        TABLE_NAME: sessionsTable.tableName,
        FFMPEG_PATH: '/opt/bin/ffmpeg',
        FFPROBE_PATH: '/opt/bin/ffprobe',
      },
    });

    bucket.grantReadWrite(videoOptimizer);
    sessionsTable.grantReadWriteData(videoOptimizer);

    // ==========================================
    // SERVICE 15: PUBLIC LINK GENERATOR
    // ==========================================

    const publicLinkGenerator = new lambda.Function(this, 'PublicLinkGenerator', {
      functionName: 'public-link-generator',
      runtime: lambda.Runtime.NODEJS_18_X,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../public-link-generator')),
      timeout: cdk.Duration.seconds(30),
      memorySize: 256,
      environment: {
        BUCKET_NAME: bucket.bucketName,
        TABLE_NAME: sessionsTable.tableName,
      },
    });

    bucket.grantRead(publicLinkGenerator);
    sessionsTable.grantReadWriteData(publicLinkGenerator);

    // ==========================================
    // SERVICE 11: JOB QUEUE MANAGER
    // ==========================================

    const jobQueueManager = new lambda.Function(this, 'JobQueueManager', {
      functionName: 'job-queue-manager',
      runtime: lambda.Runtime.NODEJS_18_X,
      handler: 'index.handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../../job-queue-manager')),
      timeout: cdk.Duration.minutes(5),
      memorySize: 512,
      environment: {
        QUEUE_URL: videoProcessingQueue.queueUrl,
        TABLE_NAME: sessionsTable.tableName,
        VIDEO_STITCHER_FUNCTION: videoStitcher.functionName,
        VIDEO_OPTIMIZER_FUNCTION: videoOptimizer.functionName,
      },
    });

    // Grant permissions
    videoProcessingQueue.grantSendMessages(jobQueueManager);
    videoProcessingQueue.grantConsumeMessages(jobQueueManager);
    sessionsTable.grantReadWriteData(jobQueueManager);
    videoStitcher.grantInvoke(jobQueueManager);
    videoOptimizer.grantInvoke(jobQueueManager);

    // ==========================================
    // OUTPUTS
    // ==========================================

    new cdk.CfnOutput(this, 'SlideGeneratorArn', {
      value: slideGenerator.functionArn,
      description: 'Slide Generator Lambda ARN',
    });

    new cdk.CfnOutput(this, 'VideoStitcherArn', {
      value: videoStitcher.functionArn,
      description: 'Video Stitcher Lambda ARN',
    });

    new cdk.CfnOutput(this, 'VideoOptimizerArn', {
      value: videoOptimizer.functionArn,
      description: 'Video Optimizer Lambda ARN',
    });

    new cdk.CfnOutput(this, 'PublicLinkGeneratorArn', {
      value: publicLinkGenerator.functionArn,
      description: 'Public Link Generator Lambda ARN',
    });

    new cdk.CfnOutput(this, 'JobQueueManagerArn', {
      value: jobQueueManager.functionArn,
      description: 'Job Queue Manager Lambda ARN',
    });

    new cdk.CfnOutput(this, 'VideoProcessingQueueUrl', {
      value: videoProcessingQueue.queueUrl,
      description: 'SQS Queue URL for video processing jobs',
    });
  }
}
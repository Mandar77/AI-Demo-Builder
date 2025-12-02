// =============================================================================================
// This file contains all the constants that will be needed to create resources in CDK
// =============================================================================================
export class Constants {

    // =============================================================================================
    // AWS Configuration
    // =============================================================================================
    static readonly AWS_REGION = 'us-east-1'
    static readonly AWS_ACCOUNT = process.env.CDK_DEFAULT_ACCOUNT || ''

    // =============================================================================================
    // DynamoDB
    // =============================================================================================
    static readonly DYNAMODB_TABLE_NAME = 'demo-builder-sessions'
    static readonly DYNAMODB_STATUS_INDEX = 'StatusIndex'
    static readonly DYNAMODB_REPO_INDEX = 'RepoUrlIndex'

    // =============================================================================================
    // Lambda Function Names
    // =============================================================================================
    static readonly SERVICE_4_FUNCTION_NAME = 'demo-builder-service-4-ai-suggestions';
    static readonly SERVICE_5_FUNCTION_NAME = 'demo-builder-service-5-organizer';
    static readonly SERVICE_6_FUNCTION_NAME = 'demo-builder-service-6-session-creator';

    // =============================================================================================
    // Secrets Manager
    // =============================================================================================
    static readonly GEMINI_SECRET_NAME = 'ai-demo-builder/gemini-api-key'

    // =============================================================================================
    // S3
    // =============================================================================================
    static readonly S3_VIDEOS_BUCKET = 'demo-builder-videos'
    static readonly S3_UPLOADS_PREFIX = 'uploads/'
    static readonly S3_CONVERTED_PREFIX = 'converted/'
    static readonly S3_FINAL_PREFIX = 'final/'

    // =============================================================================================
    // API Gateway
    // =============================================================================================
    static readonly API_NAME = 'demo-builder-person2-api'
    static readonly API_STAGE = 'dev'

    // =============================================================================================
    // CDK Exports for Cross-Stack references
    // =============================================================================================
    static readonly EXPORT_TABLE_NAME = 'DemoBuilderSessionsTableName'
    static readonly EXPORT_TABLE_ARN = 'DemoBuilderSessionsTableArn'

    // =============================================================================================
    // Lambda Configurations
    // =============================================================================================
    static readonly LAMBDA_TIMEOUT_SHORT = 10 // 10 seconds
    static readonly LAMBDA_TIMEOUT_MEDIUM = 30
    static readonly LAMBDA_TIMEOUT_LARGE = 60

    static readonly LAMBDA_MEMORY_SMALL = 256
    static readonly LAMBDA_MEMORY_MEDIUM = 512
    static readonly LAMBDA_MEMORY_LARGE = 1024
}
import * as cdk from 'aws-cdk-lib'
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb'
import { Construct } from 'constructs'
import { Constants } from './constants'

export class StorageCreationStack extends cdk.Stack {
    public readonly sessionTable: dynamodb.Table

    constructor(scope: Construct, id: string, props?: cdk.StackProps) {
        super(scope, id, props)

    // =============================================================================================
    // DynamoDB Session Table
    // =============================================================================================
    this.sessionTable = new dynamodb.Table(this, 'SessionTable', {
        tableName: Constants.DYNAMODB_TABLE_NAME,

        partitionKey: {
            name: 'session_id',
            type: dynamodb.AttributeType.STRING
        },

        billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
        removalPolicy: cdk.RemovalPolicy.DESTROY,
        pointInTimeRecovery: true,
        encryption: dynamodb.TableEncryption.AWS_MANAGED
    })

    // GSI for status queries
    this.sessionTable.addGlobalSecondaryIndex({
        indexName: Constants.DYNAMODB_STATUS_INDEX,
        partitionKey: {
            name: 'status',
            type: dynamodb.AttributeType.STRING
        },
        sortKey: {
            name: 'created_at',
            type: dynamodb.AttributeType.STRING
        }
    })

    // GSI for repo URL Queries
    this.sessionTable.addGlobalSecondaryIndex({
        indexName: Constants.DYNAMODB_REPO_INDEX,
        partitionKey: {
            name: 'repo_url',
            type: dynamodb.AttributeType.STRING
        },
        sortKey: {
            name: 'created_at',
            type: dynamodb.AttributeType.STRING
        }
    })

    // =============================================================================================
    // Exports
    // =============================================================================================
    new cdk.CfnOutput(this, 'SessionTableName', {
        value: this.sessionTable.tableName,
        exportName: Constants.EXPORT_TABLE_NAME,
        description: 'DynamoDB Sessions Table Name'
    });

    new cdk.CfnOutput(this, 'SessionTableArn', {
        value: this.sessionTable.tableArn,
        exportName: Constants.EXPORT_TABLE_ARN,
        description: 'DynamoDB Sessions Table Arn'
    })
    }
}
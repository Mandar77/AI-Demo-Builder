#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { VideoProcessingStack } from '../lib/video-processing-stack';

const app = new cdk.App();

new VideoProcessingStack(app, 'VideoProcessingStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
  description: 'Person 4 Services: Video Processing Pipeline (Services 11-15)',
});
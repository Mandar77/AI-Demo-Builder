const { S3Client, PutObjectCommand } = require('@aws-sdk/client-s3');
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { DynamoDBDocumentClient, UpdateCommand } = require('@aws-sdk/lib-dynamodb');
const { createCanvas, registerFont } = require('canvas');

// Initialize AWS clients
const s3Client = new S3Client({ region: process.env.AWS_REGION || 'us-east-1' });
const ddbClient = new DynamoDBClient({ region: process.env.AWS_REGION || 'us-east-1' });
const docClient = DynamoDBDocumentClient.from(ddbClient);

// Configuration
const CONFIG = {
    BUCKET_NAME: process.env.BUCKET_NAME || 'ai-demo-builder-bucket',
    TABLE_NAME: process.env.TABLE_NAME || 'Sessions',
    SLIDE_WIDTH: 1920,
    SLIDE_HEIGHT: 1080,
    BACKGROUND_COLOR: '#1a1a2e',
    PRIMARY_COLOR: '#eaeaea',
    ACCENT_COLOR: '#00d9ff',
    SECONDARY_COLOR: '#a0a0a0'
};

/**
 * Generate a gradient background on the canvas
 */
function drawBackground(ctx, width, height, style = 'gradient') {
    if (style === 'gradient') {
        const gradient = ctx.createLinearGradient(0, 0, width, height);
        gradient.addColorStop(0, '#1a1a2e');
        gradient.addColorStop(0.5, '#16213e');
        gradient.addColorStop(1, '#0f3460');
        ctx.fillStyle = gradient;
    } else if (style === 'solid') {
        ctx.fillStyle = CONFIG.BACKGROUND_COLOR;
    } else if (style === 'dark') {
        const gradient = ctx.createRadialGradient(width/2, height/2, 0, width/2, height/2, width);
        gradient.addColorStop(0, '#2d2d44');
        gradient.addColorStop(1, '#1a1a2e');
        ctx.fillStyle = gradient;
    }
    ctx.fillRect(0, 0, width, height);
}

/**
 * Draw decorative elements on the slide
 */
function drawDecorations(ctx, width, height) {
    // Draw accent lines
    ctx.strokeStyle = CONFIG.ACCENT_COLOR;
    ctx.lineWidth = 3;
    ctx.globalAlpha = 0.6;
    
    // Top left corner accent
    ctx.beginPath();
    ctx.moveTo(50, 100);
    ctx.lineTo(50, 50);
    ctx.lineTo(150, 50);
    ctx.stroke();
    
    // Bottom right corner accent
    ctx.beginPath();
    ctx.moveTo(width - 50, height - 100);
    ctx.lineTo(width - 50, height - 50);
    ctx.lineTo(width - 150, height - 50);
    ctx.stroke();
    
    ctx.globalAlpha = 1;
    
    // Draw subtle grid pattern
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 0.5;
    ctx.globalAlpha = 0.05;
    
    for (let i = 0; i < width; i += 60) {
        ctx.beginPath();
        ctx.moveTo(i, 0);
        ctx.lineTo(i, height);
        ctx.stroke();
    }
    for (let i = 0; i < height; i += 60) {
        ctx.beginPath();
        ctx.moveTo(0, i);
        ctx.lineTo(width, i);
        ctx.stroke();
    }
    ctx.globalAlpha = 1;
}

/**
 * Draw text with word wrapping
 */
function drawWrappedText(ctx, text, x, y, maxWidth, lineHeight) {
    const words = text.split(' ');
    let line = '';
    let currentY = y;
    
    for (let i = 0; i < words.length; i++) {
        const testLine = line + words[i] + ' ';
        const metrics = ctx.measureText(testLine);
        
        if (metrics.width > maxWidth && i > 0) {
            ctx.fillText(line.trim(), x, currentY);
            line = words[i] + ' ';
            currentY += lineHeight;
        } else {
            line = testLine;
        }
    }
    ctx.fillText(line.trim(), x, currentY);
    return currentY;
}

/**
 * Generate a title slide
 */
function generateTitleSlide(ctx, width, height, content) {
    drawBackground(ctx, width, height, 'gradient');
    drawDecorations(ctx, width, height);
    
    const { title, subtitle, projectName } = content;
    
    // Draw project name badge at top
    if (projectName) {
        ctx.font = 'bold 24px Arial';
        ctx.fillStyle = CONFIG.ACCENT_COLOR;
        ctx.textAlign = 'center';
        ctx.fillText(projectName.toUpperCase(), width / 2, 120);
        
        // Underline
        const textWidth = ctx.measureText(projectName.toUpperCase()).width;
        ctx.strokeStyle = CONFIG.ACCENT_COLOR;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo((width - textWidth) / 2 - 20, 135);
        ctx.lineTo((width + textWidth) / 2 + 20, 135);
        ctx.stroke();
    }
    
    // Draw main title
    ctx.font = 'bold 72px Arial';
    ctx.fillStyle = CONFIG.PRIMARY_COLOR;
    ctx.textAlign = 'center';
    drawWrappedText(ctx, title || 'Demo Video', width / 2, height / 2 - 50, width - 200, 85);
    
    // Draw subtitle
    if (subtitle) {
        ctx.font = '36px Arial';
        ctx.fillStyle = CONFIG.SECONDARY_COLOR;
        drawWrappedText(ctx, subtitle, width / 2, height / 2 + 80, width - 300, 45);
    }
}

/**
 * Generate a section/transition slide
 */
function generateSectionSlide(ctx, width, height, content) {
    drawBackground(ctx, width, height, 'dark');
    drawDecorations(ctx, width, height);
    
    const { sectionNumber, sectionTitle, sectionDescription } = content;
    
    // Draw section number
    if (sectionNumber) {
        ctx.font = 'bold 180px Arial';
        ctx.fillStyle = CONFIG.ACCENT_COLOR;
        ctx.globalAlpha = 0.15;
        ctx.textAlign = 'left';
        ctx.fillText(sectionNumber.toString().padStart(2, '0'), 100, 250);
        ctx.globalAlpha = 1;
    }
    
    // Draw section title
    ctx.font = 'bold 64px Arial';
    ctx.fillStyle = CONFIG.PRIMARY_COLOR;
    ctx.textAlign = 'center';
    ctx.fillText(sectionTitle || 'Section', width / 2, height / 2);
    
    // Draw accent line under title
    const titleWidth = ctx.measureText(sectionTitle || 'Section').width;
    ctx.strokeStyle = CONFIG.ACCENT_COLOR;
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.moveTo((width - titleWidth) / 2, height / 2 + 20);
    ctx.lineTo((width + titleWidth) / 2, height / 2 + 20);
    ctx.stroke();
    
    // Draw section description
    if (sectionDescription) {
        ctx.font = '32px Arial';
        ctx.fillStyle = CONFIG.SECONDARY_COLOR;
        drawWrappedText(ctx, sectionDescription, width / 2, height / 2 + 100, width - 400, 42);
    }
}

/**
 * Generate an ending slide
 */
function generateEndSlide(ctx, width, height, content) {
    drawBackground(ctx, width, height, 'gradient');
    drawDecorations(ctx, width, height);
    
    const { projectName, githubUrl, message } = content;
    
    // Draw thank you message
    ctx.font = 'bold 80px Arial';
    ctx.fillStyle = CONFIG.PRIMARY_COLOR;
    ctx.textAlign = 'center';
    ctx.fillText(message || 'Thank You!', width / 2, height / 2 - 80);
    
    // Draw project name
    if (projectName) {
        ctx.font = '48px Arial';
        ctx.fillStyle = CONFIG.ACCENT_COLOR;
        ctx.fillText(projectName, width / 2, height / 2 + 20);
    }
    
    // Draw GitHub URL
    if (githubUrl) {
        ctx.font = '28px Arial';
        ctx.fillStyle = CONFIG.SECONDARY_COLOR;
        ctx.fillText(githubUrl, width / 2, height / 2 + 100);
    }
    
    // Draw decorative circle
    ctx.strokeStyle = CONFIG.ACCENT_COLOR;
    ctx.lineWidth = 3;
    ctx.globalAlpha = 0.3;
    ctx.beginPath();
    ctx.arc(width / 2, height / 2 - 80, 150, 0, Math.PI * 2);
    ctx.stroke();
    ctx.globalAlpha = 1;
}

/**
 * Main slide generation function
 */
async function generateSlide(slideType, content) {
    const canvas = createCanvas(CONFIG.SLIDE_WIDTH, CONFIG.SLIDE_HEIGHT);
    const ctx = canvas.getContext('2d');
    
    // Anti-aliasing
    ctx.antialias = 'subpixel';
    
    switch (slideType) {
        case 'title':
            generateTitleSlide(ctx, CONFIG.SLIDE_WIDTH, CONFIG.SLIDE_HEIGHT, content);
            break;
        case 'section':
            generateSectionSlide(ctx, CONFIG.SLIDE_WIDTH, CONFIG.SLIDE_HEIGHT, content);
            break;
        case 'end':
            generateEndSlide(ctx, CONFIG.SLIDE_WIDTH, CONFIG.SLIDE_HEIGHT, content);
            break;
        default:
            generateSectionSlide(ctx, CONFIG.SLIDE_WIDTH, CONFIG.SLIDE_HEIGHT, content);
    }
    
    // Convert to PNG buffer
    return canvas.toBuffer('image/png');
}

/**
 * Upload slide to S3
 */
async function uploadSlideToS3(sessionId, slideId, pngBuffer) {
    const key = `slides/${sessionId}/${slideId}.png`;
    
    const command = new PutObjectCommand({
        Bucket: CONFIG.BUCKET_NAME,
        Key: key,
        Body: pngBuffer,
        ContentType: 'image/png'
    });
    
    await s3Client.send(command);
    
    return {
        bucket: CONFIG.BUCKET_NAME,
        key: key,
        url: `s3://${CONFIG.BUCKET_NAME}/${key}`
    };
}

/**
 * Update session in DynamoDB with slide info
 */
async function updateSessionWithSlide(sessionId, slideInfo) {
    const command = new UpdateCommand({
        TableName: CONFIG.TABLE_NAME,
        Key: { session_id: sessionId },
        UpdateExpression: 'SET #slides = list_append(if_not_exists(#slides, :empty), :slide), updated_at = :now',
        ExpressionAttributeNames: {
            '#slides': 'slides'
        },
        ExpressionAttributeValues: {
            ':slide': [slideInfo],
            ':empty': [],
            ':now': new Date().toISOString()
        }
    });
    
    await docClient.send(command);
}

/**
 * Process request to generate slides
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
    
    const { session_id, slides } = body;
    
    if (!session_id) {
        throw new Error('session_id is required');
    }
    
    if (!slides || !Array.isArray(slides) || slides.length === 0) {
        throw new Error('slides array is required and must not be empty');
    }
    
    const generatedSlides = [];
    
    for (let i = 0; i < slides.length; i++) {
        const slide = slides[i];
        const slideId = slide.id || `slide_${i + 1}`;
        const slideType = slide.type || 'section';
        const content = slide.content || {};
        
        // Generate the slide image
        const pngBuffer = await generateSlide(slideType, content);
        
        // Upload to S3
        const s3Info = await uploadSlideToS3(session_id, slideId, pngBuffer);
        
        const slideInfo = {
            id: slideId,
            type: slideType,
            order: slide.order || i,
            s3_key: s3Info.key,
            s3_url: s3Info.url,
            created_at: new Date().toISOString()
        };
        
        generatedSlides.push(slideInfo);
        
        // Update DynamoDB
        await updateSessionWithSlide(session_id, slideInfo);
    }
    
    return {
        session_id,
        slides_generated: generatedSlides.length,
        slides: generatedSlides
    };
}

/**
 * Lambda handler
 */
exports.handler = async (event, context) => {
    console.log('Slide Generator invoked:', JSON.stringify(event, null, 2));
    
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
        console.error('Error generating slides:', error);
        
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
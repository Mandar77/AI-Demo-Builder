/**
 * Local test script for Slide Generator
 * Run: node test_local.js
 */

const { createCanvas } = require('canvas');
const fs = require('fs');
const path = require('path');

// Configuration (same as index.js)
const CONFIG = {
    SLIDE_WIDTH: 1920,
    SLIDE_HEIGHT: 1080,
    BACKGROUND_COLOR: '#1a1a2e',
    PRIMARY_COLOR: '#eaeaea',
    ACCENT_COLOR: '#00d9ff',
    SECONDARY_COLOR: '#a0a0a0'
};

// Copy the drawing functions from index.js
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

function drawDecorations(ctx, width, height) {
    ctx.strokeStyle = CONFIG.ACCENT_COLOR;
    ctx.lineWidth = 3;
    ctx.globalAlpha = 0.6;
    
    ctx.beginPath();
    ctx.moveTo(50, 100);
    ctx.lineTo(50, 50);
    ctx.lineTo(150, 50);
    ctx.stroke();
    
    ctx.beginPath();
    ctx.moveTo(width - 50, height - 100);
    ctx.lineTo(width - 50, height - 50);
    ctx.lineTo(width - 150, height - 50);
    ctx.stroke();
    
    ctx.globalAlpha = 1;
}

function generateTitleSlide(ctx, width, height, content) {
    drawBackground(ctx, width, height, 'gradient');
    drawDecorations(ctx, width, height);
    
    const { title, subtitle, projectName } = content;
    
    if (projectName) {
        ctx.font = 'bold 24px Arial';
        ctx.fillStyle = CONFIG.ACCENT_COLOR;
        ctx.textAlign = 'center';
        ctx.fillText(projectName.toUpperCase(), width / 2, 120);
    }
    
    ctx.font = 'bold 72px Arial';
    ctx.fillStyle = CONFIG.PRIMARY_COLOR;
    ctx.textAlign = 'center';
    ctx.fillText(title || 'Demo Video', width / 2, height / 2 - 50);
    
    if (subtitle) {
        ctx.font = '36px Arial';
        ctx.fillStyle = CONFIG.SECONDARY_COLOR;
        ctx.fillText(subtitle, width / 2, height / 2 + 80);
    }
}

function generateSectionSlide(ctx, width, height, content) {
    drawBackground(ctx, width, height, 'dark');
    drawDecorations(ctx, width, height);
    
    const { sectionNumber, sectionTitle, sectionDescription } = content;
    
    if (sectionNumber) {
        ctx.font = 'bold 180px Arial';
        ctx.fillStyle = CONFIG.ACCENT_COLOR;
        ctx.globalAlpha = 0.15;
        ctx.textAlign = 'left';
        ctx.fillText(sectionNumber.toString().padStart(2, '0'), 100, 250);
        ctx.globalAlpha = 1;
    }
    
    ctx.font = 'bold 64px Arial';
    ctx.fillStyle = CONFIG.PRIMARY_COLOR;
    ctx.textAlign = 'center';
    ctx.fillText(sectionTitle || 'Section', width / 2, height / 2);
    
    if (sectionDescription) {
        ctx.font = '32px Arial';
        ctx.fillStyle = CONFIG.SECONDARY_COLOR;
        ctx.fillText(sectionDescription, width / 2, height / 2 + 100);
    }
}

function generateEndSlide(ctx, width, height, content) {
    drawBackground(ctx, width, height, 'gradient');
    drawDecorations(ctx, width, height);
    
    const { projectName, githubUrl, message } = content;
    
    ctx.font = 'bold 80px Arial';
    ctx.fillStyle = CONFIG.PRIMARY_COLOR;
    ctx.textAlign = 'center';
    ctx.fillText(message || 'Thank You!', width / 2, height / 2 - 80);
    
    if (projectName) {
        ctx.font = '48px Arial';
        ctx.fillStyle = CONFIG.ACCENT_COLOR;
        ctx.fillText(projectName, width / 2, height / 2 + 20);
    }
    
    if (githubUrl) {
        ctx.font = '28px Arial';
        ctx.fillStyle = CONFIG.SECONDARY_COLOR;
        ctx.fillText(githubUrl, width / 2, height / 2 + 100);
    }
}

async function generateSlide(slideType, content) {
    const canvas = createCanvas(CONFIG.SLIDE_WIDTH, CONFIG.SLIDE_HEIGHT);
    const ctx = canvas.getContext('2d');
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
    
    return canvas.toBuffer('image/png');
}

// Test function
async function runTests() {
    console.log('🧪 Testing Slide Generator locally...\n');
    
    // Create output directory
    const outputDir = './test_output';
    if (!fs.existsSync(outputDir)) {
        fs.mkdirSync(outputDir);
    }
    
    // Test 1: Title slide
    console.log('Test 1: Generating title slide...');
    const titleSlide = await generateSlide('title', {
        title: 'AI Demo Builder',
        subtitle: 'Automatically generate demo videos for your projects',
        projectName: 'CS6620 Project'
    });
    fs.writeFileSync(path.join(outputDir, 'title_slide.png'), titleSlide);
    console.log('✅ Title slide saved to test_output/title_slide.png\n');
    
    // Test 2: Section slide
    console.log('Test 2: Generating section slide...');
    const sectionSlide = await generateSlide('section', {
        sectionNumber: 1,
        sectionTitle: 'Installation',
        sectionDescription: 'How to set up the project on your local machine'
    });
    fs.writeFileSync(path.join(outputDir, 'section_slide.png'), sectionSlide);
    console.log('✅ Section slide saved to test_output/section_slide.png\n');
    
    // Test 3: Another section slide
    console.log('Test 3: Generating another section slide...');
    const section2Slide = await generateSlide('section', {
        sectionNumber: 2,
        sectionTitle: 'Features',
        sectionDescription: 'Key features and capabilities'
    });
    fs.writeFileSync(path.join(outputDir, 'section2_slide.png'), section2Slide);
    console.log('✅ Section slide saved to test_output/section2_slide.png\n');
    
    // Test 4: End slide
    console.log('Test 4: Generating end slide...');
    const endSlide = await generateSlide('end', {
        projectName: 'AI Demo Builder',
        githubUrl: 'https://github.com/Mandar77/AI-Demo-Builder',
        message: 'Thank You!'
    });
    fs.writeFileSync(path.join(outputDir, 'end_slide.png'), endSlide);
    console.log('✅ End slide saved to test_output/end_slide.png\n');
    
    console.log('🎉 All tests completed! Check the test_output directory for generated slides.');
}

runTests().catch(console.error);
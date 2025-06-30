import { execSync } from 'child_process';
import { readFileSync } from 'fs';
import path from 'path';

// Read package.json to get version
const packageJson = JSON.parse(readFileSync(new URL('../package.json', import.meta.url)));
const version = packageJson.version;
const packageName = packageJson.name;
const imageName = `ericdudley/${packageName}`;

try {
    console.log('Building Docker image...');
    // Build with both tags
    execSync(`docker build . -t ${imageName}:latest -t ${imageName}:v${version}`, { stdio: 'inherit' });
    
    console.log('Logging into Docker Hub...');
    execSync('docker login', { stdio: 'inherit' });
    
    console.log('Pushing Docker image with both tags...');
    execSync(`docker push ${imageName}:latest`, { stdio: 'inherit' });
    execSync(`docker push ${imageName}:v${version}`, { stdio: 'inherit' });
    
    console.log(`Successfully published Docker image with tags:
    - ${imageName}:latest
    - ${imageName}:v${version}`);
} catch (error) {
    console.error('Error during Docker publish:', error);
    process.exit(1);
}

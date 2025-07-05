import { execSync } from 'child_process';
import { readFileSync } from 'fs';

// Read package.json for version and name
const packageJson = JSON.parse(readFileSync(new URL('../package.json', import.meta.url)));
const version = packageJson.version;
const packageName = packageJson.name;
const imageName = `ericdudley/${packageName}`;

try {
  console.log('Logging into Docker Hub...');
  execSync('docker login', { stdio: 'inherit' });

  console.log('Building Docker image for linux/amd64...');
  execSync(`docker buildx build --platform linux/amd64 -t ${imageName}:latest -t ${imageName}:v${version} --push .`, { stdio: 'inherit' });

  console.log(`Successfully published Docker image with tags:
    - ${imageName}:latest
    - ${imageName}:v${version}`);
} catch (error) {
  console.error('Error during Docker publish:', error);
  process.exit(1);
}
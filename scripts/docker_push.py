#!/usr/bin/env python3
"""
Docker Registry Push Script
Push Netflix API containers to multiple registries: Docker Hub, ECR, GCR, ACR
"""

import os
import subprocess
import sys
import argparse
import json
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class RegistryConfig:
    """Registry configuration"""
    name: str
    registry_url: str
    repository: str
    username: Optional[str] = None
    password: Optional[str] = None
    region: Optional[str] = None  # For AWS ECR, GCP GCR, Azure ACR


class DockerRegistryPusher:
    """Push Docker images to multiple registries"""
    
    def __init__(self, project_dir: str = "."):
        self.project_dir = Path(project_dir)
        self.images = {
            'backend': {
                'dockerfile': 'backend/Dockerfile',
                'context': 'backend'
            },
            'frontend': {
                'dockerfile': 'frontend_react/Dockerfile',
                'context': 'frontend_react'
            },
            'ml-pipeline': {
                'dockerfile': 'ml_pipeline/Dockerfile',
                'context': 'ml_pipeline'
            }
        }
    
    def get_version(self) -> str:
        """Get version from git tag or use latest"""
        try:
            result = subprocess.run(
                ['git', 'describe', '--tags', '--abbrev=0'],
                cwd=self.project_dir,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        
        return 'latest'
    
    def build_image(self, service: str, tag: str) -> bool:
        """Build Docker image"""
        config = self.images[service]
        
        print(f"\n📦 Building {service} image: {tag}")
        
        cmd = [
            'docker', 'build',
            '-f', config['dockerfile'],
            '-t', tag,
            config['context']
        ]
        
        result = subprocess.run(cmd, cwd=self.project_dir)
        
        if result.returncode != 0:
            print(f"❌ Failed to build {service}")
            return False
        
        print(f"✅ Built {service}")
        return True
    
    def push_to_registry(self, image_tag: str, registry: RegistryConfig) -> bool:
        """Push image to registry"""
        print(f"\n🚀 Pushing {image_tag} to {registry.name}")
        
        # Login to registry
        if not self.login_to_registry(registry):
            return False
        
        # Build full image name
        full_tag = f"{registry.registry_url}/{registry.repository}:{image_tag}"
        
        # Tag image
        cmd_tag = ['docker', 'tag', image_tag, full_tag]
        if subprocess.run(cmd_tag).returncode != 0:
            print(f"❌ Failed to tag image for {registry.name}")
            return False
        
        # Push image
        cmd_push = ['docker', 'push', full_tag]
        if subprocess.run(cmd_push).returncode != 0:
            print(f"❌ Failed to push to {registry.name}")
            return False
        
        print(f"✅ Pushed to {registry.name}: {full_tag}")
        return True
    
    def login_to_registry(self, registry: RegistryConfig) -> bool:
        """Login to Docker registry"""
        print(f"   Authenticating with {registry.name}...")
        
        if registry.name == 'docker-hub':
            return self._login_docker_hub(registry)
        elif registry.name == 'ecr':
            return self._login_ecr(registry)
        elif registry.name == 'gcr':
            return self._login_gcr(registry)
        elif registry.name == 'acr':
            return self._login_acr(registry)
        else:
            print(f"❌ Unknown registry: {registry.name}")
            return False
    
    def _login_docker_hub(self, registry: RegistryConfig) -> bool:
        """Login to Docker Hub"""
        username = registry.username or os.getenv('DOCKER_USERNAME')
        password = registry.password or os.getenv('DOCKER_PASSWORD')
        
        if not username or not password:
            print("❌ Docker Hub credentials not found")
            print("   Set DOCKER_USERNAME and DOCKER_PASSWORD environment variables")
            return False
        
        cmd = ['docker', 'login', '-u', username, '-p', password]
        return subprocess.run(cmd).returncode == 0
    
    def _login_ecr(self, registry: RegistryConfig) -> bool:
        """Login to AWS ECR"""
        region = registry.region or os.getenv('AWS_REGION', 'us-east-1')
        
        # Get ECR login token
        cmd_login = [
            'aws', 'ecr', 'get-login-password',
            '--region', region
        ]
        
        result = subprocess.run(cmd_login, capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Failed to get ECR login token")
            return False
        
        password = result.stdout.strip()
        
        # Login to ECR
        cmd = [
            'docker', 'login',
            '--username', 'AWS',
            '--password', password,
            registry.registry_url
        ]
        
        return subprocess.run(cmd).returncode == 0
    
    def _login_gcr(self, registry: RegistryConfig) -> bool:
        """Login to Google Container Registry"""
        key_file = os.getenv('GCR_KEY_FILE')
        
        if not key_file:
            print("❌ GCR_KEY_FILE environment variable not set")
            return False
        
        cmd = [
            'gcloud', 'auth', 'configure-docker',
            registry.registry_url
        ]
        
        return subprocess.run(cmd).returncode == 0
    
    def _login_acr(self, registry: RegistryConfig) -> bool:
        """Login to Azure Container Registry"""
        username = registry.username or os.getenv('AZURE_REGISTRY_USER')
        password = registry.password or os.getenv('AZURE_REGISTRY_PASSWORD')
        
        if not username or not password:
            print("❌ Azure registry credentials not found")
            print("   Set AZURE_REGISTRY_USER and AZURE_REGISTRY_PASSWORD")
            return False
        
        cmd = [
            'docker', 'login',
            '-u', username,
            '-p', password,
            registry.registry_url
        ]
        
        return subprocess.run(cmd).returncode == 0
    
    def push_all_services(self, registries: List[RegistryConfig], version: str) -> bool:
        """Push all services to all registries"""
        all_success = True
        
        for service in self.images.keys():
            image_tag = f"{service}:{version}"
            
            # Build image
            if not self.build_image(service, image_tag):
                all_success = False
                continue
            
            # Push to each registry
            for registry in registries:
                if not self.push_to_registry(image_tag, registry):
                    all_success = False
        
        return all_success


def get_docker_hub_config() -> RegistryConfig:
    """Get Docker Hub configuration"""
    return RegistryConfig(
        name='docker-hub',
        registry_url='docker.io',
        repository=os.getenv('DOCKER_HUB_REPO', 'yourusername/netflix-api'),
        username=os.getenv('DOCKER_USERNAME'),
        password=os.getenv('DOCKER_PASSWORD')
    )


def get_ecr_config() -> RegistryConfig:
    """Get AWS ECR configuration"""
    account = os.getenv('AWS_ACCOUNT_ID', '')
    region = os.getenv('AWS_REGION', 'us-east-1')
    registry_url = f"{account}.dkr.ecr.{region}.amazonaws.com"
    
    return RegistryConfig(
        name='ecr',
        registry_url=registry_url,
        repository='netflix-api',
        region=region
    )


def get_gcr_config() -> RegistryConfig:
    """Get Google Container Registry configuration"""
    project = os.getenv('GCP_PROJECT_ID', '')
    registry = os.getenv('GCR_REGION', 'gcr.io')
    
    return RegistryConfig(
        name='gcr',
        registry_url=registry,
        repository=f"{project}/netflix-api"
    )


def get_acr_config() -> RegistryConfig:
    """Get Azure Container Registry configuration"""
    registry_name = os.getenv('AZURE_REGISTRY_NAME', '')
    registry_url = f"{registry_name}.azurecr.io"
    
    return RegistryConfig(
        name='acr',
        registry_url=registry_url,
        repository='netflix-api',
        username=os.getenv('AZURE_REGISTRY_USER'),
        password=os.getenv('AZURE_REGISTRY_PASSWORD')
    )


def main():
    parser = argparse.ArgumentParser(
        description='Push Netflix API Docker images to registries',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python docker_push.py --registry docker-hub --version v1.0.0
  python docker_push.py --registry ecr,gcr --version latest
  python docker_push.py --all-registries --auto-version
  
Environment Variables:
  DOCKER_USERNAME    - Docker Hub username
  DOCKER_PASSWORD    - Docker Hub password
  DOCKER_HUB_REPO    - Docker Hub repository (default: yourusername/netflix-api)
  AWS_ACCOUNT_ID     - AWS account ID
  AWS_REGION         - AWS region (default: us-east-1)
  GCP_PROJECT_ID     - Google Cloud project ID
  GCR_REGION         - GCR region (default: gcr.io)
  AZURE_REGISTRY_NAME - Azure registry name
  AZURE_REGISTRY_USER - Azure registry user
  AZURE_REGISTRY_PASSWORD - Azure registry password
        """
    )
    
    parser.add_argument(
        '--registry',
        help='Registry to push to (docker-hub, ecr, gcr, acr)',
        default='docker-hub'
    )
    
    parser.add_argument(
        '--all-registries',
        action='store_true',
        help='Push to all configured registries'
    )
    
    parser.add_argument(
        '--version',
        help='Image version tag',
        default=None
    )
    
    parser.add_argument(
        '--auto-version',
        action='store_true',
        help='Use git tag as version'
    )
    
    parser.add_argument(
        '--project-dir',
        default='.',
        help='Project directory'
    )
    
    args = parser.parse_args()
    
    pusher = DockerRegistryPusher(args.project_dir)
    
    # Determine version
    version = args.version
    if args.auto_version:
        version = pusher.get_version()
    if not version:
        version = 'latest'
    
    print("=" * 70)
    print("🐳 NETFLIX API DOCKER REGISTRY PUSHER")
    print("=" * 70)
    print(f"Version: {version}")
    
    # Determine registries
    registries = []
    
    if args.all_registries:
        print("\n🎯 Pushing to all registries...")
        registries = [
            get_docker_hub_config(),
            get_ecr_config(),
            get_gcr_config(),
            get_acr_config()
        ]
    else:
        registry_names = [r.strip() for r in args.registry.split(',')]
        
        for reg_name in registry_names:
            reg_name = reg_name.strip().lower()
            if reg_name == 'docker-hub':
                registries.append(get_docker_hub_config())
            elif reg_name == 'ecr':
                registries.append(get_ecr_config())
            elif reg_name == 'gcr':
                registries.append(get_gcr_config())
            elif reg_name == 'acr':
                registries.append(get_acr_config())
            else:
                print(f"⚠️  Unknown registry: {reg_name}")
    
    if not registries:
        print("❌ No valid registries specified")
        sys.exit(1)
    
    # Push all services
    success = pusher.push_all_services(registries, version)
    
    print("\n" + "=" * 70)
    if success:
        print("✅ ALL IMAGES PUSHED SUCCESSFULLY")
    else:
        print("❌ SOME IMAGES FAILED TO PUSH")
    print("=" * 70)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

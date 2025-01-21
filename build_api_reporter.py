#!/usr/bin/env python3
import os
import glob
import json
import requests
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Union
from dataclasses import dataclass
import xml.etree.ElementTree as ET
import yaml
from dotenv import load_dotenv
import argparse



@dataclass
class KetryxConfig:
    ketryx_url: str
    project: str
    api_key: str
    commit_sha: Optional[str]
    version: Optional[str]


class KetryxReporter:
    def __init__(self, config: KetryxConfig):
        self.config = config
        self.base_url = config.ketryx_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {config.api_key}',
            'Content-Type': 'application/json'
        }

    def upload_artifact(self, file_path: str, content_type: str = 'application/octet-stream') -> str:
        """Upload a single artifact file to Ketryx."""
        url = f"{self.base_url}/api/v1/build-artifacts"
        params = {'project': self.config.project}
        
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, content_type)}
            response = requests.post(url, params=params, headers={'Authorization': self.headers['Authorization']}, files=files)
        
        if response.status_code != 200:
            raise Exception(f"Failed to upload artifact: {response.text}")
        
        return response.json()['id']

    def upload_test_results(self, junit_paths: List[str], cucumber_paths: List[str]) -> List[Dict]:
        """Upload all test results and return artifact data."""
        artifacts = []
        
        # Upload JUnit XML results
        for pattern in junit_paths:
            for file_path in glob.glob(pattern):
                artifact_id = self.upload_artifact(file_path, 'application/xml')
                artifacts.append({
                    'id': artifact_id,
                    'type': 'junit-xml'
                })

        # Upload Cucumber JSON results
        for pattern in cucumber_paths:
            for file_path in glob.glob(pattern):
                artifact_id = self.upload_artifact(file_path, 'application/json')
                artifacts.append({
                    'id': artifact_id,
                    'type': 'cucumber-json'
                })

        return artifacts

    def upload_sbom(self, sbom_paths: List[str], sbom_type: str) -> List[Dict]:
        """Upload SBOM files.
        
        Args:
            sbom_paths: List of file paths to SBOM files
            sbom_type: Type of SBOM (e.g., 'cyclonedx', 'spdx')
        """
        artifacts = []
        
        for pattern in sbom_paths:
            for file_path in glob.glob(pattern):
                artifact_id = self.upload_artifact(file_path, 'application/json')
                artifacts.append({
                    'id': artifact_id,
                    'type': f'{sbom_type}-json'
                })

        return artifacts

    def report_build(self, build_name: str, artifacts: List[Dict]) -> Dict:
        """Report build data to Ketryx."""
        url = f"{self.base_url}/api/v1/builds"
        
        data = {
            'project': self.config.project,
            'buildName': build_name,
            'artifacts': artifacts,
            'sourceUrl': os.getenv('GITHUB_SERVER_URL', ''),
            'repositoryUrls': [f"{os.getenv('GITHUB_SERVER_URL', '')}/{os.getenv('GITHUB_REPOSITORY', '')}"],
        }
        
        # If version is specified, it takes precedence over commitSha
        if self.config.version:
            data['version'] = self.config.version
        elif self.config.commit_sha:
            data['commitSha'] = self.config.commit_sha

        response = requests.post(url, headers=self.headers, json=data)
        if response.status_code != 200:
            raise Exception(f"Failed to report build: {response.text}")
        
        return response.json()

def process_build_config(config_file: str) -> List[Dict]:
    """Process the YAML config file and return build artifacts."""
    with open(config_file, 'r') as f:
        build_config = yaml.safe_load(f)
    
    if not build_config or 'builds' not in build_config:
        raise ValueError("Invalid config file: missing 'builds' section")
    
    # Collect all missing files
    missing_files = []
    
    for build in build_config['builds']:
        if build['type'] == 'test-results':
            for junit_path in build['artifacts'].get('junit', []):
                if not glob.glob(junit_path):
                    missing_files.append(f"JUnit file not found: {junit_path}")
            for cucumber_path in build['artifacts'].get('cucumber', []):
                if not glob.glob(cucumber_path):
                    missing_files.append(f"Cucumber file not found: {cucumber_path}")
        elif build['type'] == 'sbom':
            for artifact in build['artifacts']:
                if not glob.glob(artifact['file']):
                    missing_files.append(f"SBOM file not found: {artifact['file']}")
    
    if missing_files:
        print("\nMissing files:")
        for file in missing_files:
            print(f"  - {file}")
        import sys; sys.exit(1)
    
    return build_config['builds']

def main():
    # Add argument parser
    parser = argparse.ArgumentParser(description='Process build configuration and report to Ketryx')
    parser.add_argument('config_file', help='Path to the YAML configuration file')
    args = parser.parse_args()

    # Load environment variables from .env file
    load_dotenv()
    
    # Configuration from environment variables
    config = KetryxConfig(
        ketryx_url=os.getenv('KETRYX_URL'),
        project=os.getenv('KETRYX_PROJECT'),
        api_key=os.getenv('KETRYX_API_KEY'),
        version=os.getenv('KETRYX_VERSION'),
        commit_sha=os.getenv('GITHUB_SHA')
    )

    if not all([config.project, config.api_key, config.version]):
        raise ValueError("Missing required environment variables")

    reporter = KetryxReporter(config)
    
    # Run tests and collect results
    try:
        builds = process_build_config(args.config_file)
        
        for build in builds:
            if build['type'] == 'test-results':
                artifacts = reporter.upload_test_results(
                    junit_paths=build['artifacts'].get('junit', []),
                    cucumber_paths=build['artifacts'].get('cucumber', [])
                )
            elif build['type'] == 'sbom':
                for artifact in build['artifacts']:
                    artifacts = reporter.upload_sbom(
                        sbom_paths=[artifact['file']], 
                        sbom_type=artifact['type']
                    )
            else:
                print(f"Warning: Unknown build type '{build['type']}'")
                continue
                
            build_result = reporter.report_build(build['name'], artifacts)
            print(f"Reported {build['name']} to Ketryx: {build_result.get('buildId')}")

    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == '__main__':
    main()
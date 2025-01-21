# Ketryx Build API Utility

A Python utility for uploading and reporting test results and Software Bill of Materials (SBOM) to the Ketryx platform.

## Features

- Upload JUnit XML test results
- Upload Cucumber JSON test results
- Upload SBOM files (supports CycloneDX and SPDX formats)
- Configurable build reporting via YAML configuration
- Environment variable configuration support

## Prerequisites

- Python 3.6 or higher
- pip (Python package installer)
- Access to Ketryx platform (API key required)

## Installation

1. Clone this repository:
   ```bash
   git clone git@github.com:Ketryx/build-api-reporter.git
   cd build-api-reporter
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   
   # On Windows
   .\venv\Scripts\activate
   
   # On Unix or MacOS
   source venv/bin/activate
   ```

3. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### Environment Variables

Create a `.env` file in the project root directory with the following variables:

```ini
KETRYX_URL=https://your-ketryx-instance.com
KETRYX_PROJECT=your-project-name
KETRYX_API_KEY=your-api-key
KETRYX_VERSION=your-version
GITHUB_SHA=your-commit-sha  # Optional, used if KETRYX_VERSION is not set
```

### Build Configuration

Create a YAML configuration file (e.g., `build-config.yaml`) to specify your builds:

```yaml
builds:
  - name: "Unit Tests"
    type: "test-results"
    artifacts:
      junit:
        - "test-results/*.xml"
      cucumber:
        - "cucumber-results/*.json"
  
  - name: "SBOM Analysis"
    type: "sbom"
    artifacts:
      - file: "sbom/cyclonedx.json"
        type: "cyclonedx"
      - file: "sbom/spdx.json"
        type: "spdx"
```

## Usage

Run the script with your configuration file:

```bash
python build_api_reporter.py build-config.yaml
```

## Build Types

The tool supports two types of builds:

### Test Results
- Supports JUnit XML and Cucumber JSON formats
- Can specify multiple file patterns using glob syntax
- Both formats can be used in the same build

### SBOM
- Supports CycloneDX and SPDX formats
- Each SBOM file needs to specify its type
- Multiple SBOM files can be uploaded in a single build

## Error Handling

The script will:
- Validate the presence of all required environment variables
- Check for the existence of all specified files before uploading
- Exit with a non-zero status code if any required files are missing
- Display detailed error messages for troubleshooting

## Example Output

Successful execution:
```
Reported Unit Tests to Ketryx: build-123
Reported SBOM Analysis to Ketryx: build-124
```

Missing files error:
```
Missing files:
  - JUnit file not found: test-results/*.xml
  - SBOM file not found: sbom/cyclonedx.json
```

## Notes

- All file paths in the configuration YAML are relative to the working directory
- The script supports glob patterns for file paths
- If KETRYX_VERSION is not specified, GITHUB_SHA will be used as the commit reference
- API responses include build IDs which can be used to track builds in the Ketryx platform
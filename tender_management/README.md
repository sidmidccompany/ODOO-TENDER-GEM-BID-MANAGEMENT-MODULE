# Tender & GEM Bid Management

A comprehensive Odoo module for managing tenders and Government e-Marketplace (GeM) portal bids.

## Features

- **Complete Tender Lifecycle Management**: Track tenders from opportunity identification to bid submission and award
- **GeM Portal Integration**: Integrate with Government e-Marketplace for seamless bid management
- **Automated Bid Preparation**: Streamline bid creation with templates and wizards
- **Document Management**: Organize and track all tender-related documents
- **OCR Processing**: Extract key information from tender documents using OCR
- **AI-powered Assistant**: Get help with tender analysis and bid preparation
- **Analytics and Reporting**: Gain insights into tender performance and success rates
- **Team Collaboration**: Coordinate bid preparation efforts with team management and assignment

## Technical Details

### Module Organization

The module is organized into several components:

1. **Tender Management**: Core tender tracking and lifecycle
2. **GeM Portal Integration**: Integration with Government e-Marketplace
3. **Document Management**: Document storage, OCR, and analysis
4. **Team Collaboration**: Team setup, skill management, and assignment
5. **Analytics**: Performance tracking and reporting
6. **Portal Access**: External access to tender information

### Requirements

- Odoo 17.0
- Python 3.10+
- Additional Python libraries:
  - PyPDF2
  - pytesseract
  - openai
  - requests
  - beautifulsoup4
- External dependencies:
  - tesseract-ocr

## Installation

1. Install the required dependencies:
   ```
   pip install PyPDF2 pytesseract openai requests beautifulsoup4
   ```

2. Ensure tesseract-ocr is installed on your system:
   - For Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
   - For CentOS/RHEL: `sudo yum install tesseract`
   - For Windows: Download and install from [https://github.com/UB-Mannheim/tesseract/wiki](https://github.com/UB-Mannheim/tesseract/wiki)

3. Copy the module to your Odoo addons directory

4. Update the modules list in Odoo

5. Install the "Tender & GEM Bid Management" module

## Configuration

After installation, navigate to Tenders > Configuration to set up:

- Company profile for tenders
- Department access rights
- GeM portal API credentials
- OCR settings
- Email templates

## Usage

The main menu provides access to:

- Tenders Dashboard
- Tender Opportunities
- Bid Management
- GeM Portal Integration
- Analytics & Reports
- Team Collaboration

### Tender Management

1. Create a new tender
2. Upload tender documents
3. Process documents with OCR to extract key information
4. Analyze tender requirements using the AI assistant
5. Create and submit bids
6. Track bid status and results

### GeM Portal Integration

1. Configure GeM portal credentials
2. Import tenders from GeM
3. Create and submit bids through the GeM portal
4. Monitor bid status updates

### Team Collaboration

1. Create teams with specialized skills
2. Assign team members to tender preparation
3. Track workload and performance
4. Coordinate through integrated messaging

## API Integration

The module provides a RESTful API for integration with external systems:

- Authentication: `/api/tender/authenticate`
- Tender listing: `/api/tender/tenders`
- Tender details: `/api/tender/tender/{id}`
- Document upload: `/api/tender/document/upload`

## Support

For questions and support, please contact support@yourcompany.com

## License

This module is distributed under the terms of the GNU Lesser General Public License (LGPL-3).

## Contributors

- Your Name <your.email@example.com>

=============
Configuration
=============

After installing the Tender & GeM Bid Management module, you need to configure it to suit your organization's needs. This document guides you through the configuration process.

General Settings
==============

1. Navigate to Tenders → Configuration → Settings.

2. Configure the following options:

   - **Default Tender Sequence:** Set the numbering sequence for new tenders
   - **Default Bid Sequence:** Set the numbering sequence for new bids
   - **Approval Workflow:** Choose whether to enable the approval workflow
   - **Archive Period:** Define when to automatically archive closed tenders
   - **Document Management:** Enable document versioning and OCR processing
   - **Analytics:** Configure analytics and dashboard settings

3. Click "Save" to apply the changes.

GeM Integration
=============

To enable GeM (Government e-Marketplace) integration:

1. Navigate to Tenders → Configuration → GeM Settings.

2. Configure the following:

   - **Enable GeM Integration:** Check this box to enable GeM features
   - **API Endpoint:** Enter the GeM API endpoint URL
   - **API Key:** Enter your GeM API key
   - **API Secret:** Enter your GeM API secret
   - **Sandbox Mode:** Enable for testing without affecting real GeM data

3. Click "Test Connection" to verify your API credentials.

4. Click "Save" to apply the settings.

.. note::
   To obtain GeM API credentials, contact the GeM support team or visit the GeM portal.

OCR Document Processing
=====================

To configure OCR document processing:

1. Navigate to Tenders → Configuration → OCR Settings.

2. Configure the following:

   - **Enable OCR:** Check to enable document OCR processing
   - **OCR Service:** Select the OCR service to use (Built-in, Tesseract, or External)
   - **OCR API Endpoint:** If using an external service, enter the API endpoint
   - **API Key:** Enter your OCR service API key
   - **Default Language:** Set the default language for OCR processing
   - **Auto-process Documents:** Enable to automatically process uploaded documents

3. Click "Test OCR" to verify your configuration.

4. Click "Save" to apply the settings.

AI Analytics Configuration
=======================

To configure AI analytics and prediction features:

1. Navigate to Tenders → Configuration → AI Analytics.

2. Configure the following:

   - **Enable AI Analytics:** Check to enable AI-powered analytics
   - **AI Service:** Select the AI service to use (Built-in or External)
   - **API Endpoint:** If using an external service, enter the API endpoint
   - **API Key:** Enter your AI service API key
   - **Prediction Model:** Select the success prediction model to use
   - **Prediction Threshold:** Set the threshold for success predictions
   - **Auto-update Model:** Enable to automatically update the model with new data

3. Click "Test AI Service" to verify your configuration.

4. Click "Save" to apply the settings.

Email Notifications
================

To configure email notifications:

1. Navigate to Tenders → Configuration → Notification Settings.

2. Configure the following for each notification type:

   - **Tender Published:** Notify when a tender is published
   - **Tender Deadline Approaching:** Notify before tender deadline
   - **Bid Received:** Notify when a new bid is received
   - **Tender Awarded:** Notify when a tender is awarded
   - **Document Uploaded:** Notify when a document is uploaded
   - **Status Change:** Notify on tender status changes

3. For each notification, you can configure:

   - **Enabled:** Check to enable the notification
   - **Recipients:** Select user groups to notify
   - **Email Template:** Select the email template to use
   - **Send SMS:** Enable to send SMS notifications (requires SMS gateway)

4. Click "Save" to apply the settings.

User Permissions
==============

To configure user permissions:

1. Navigate to Settings → Users & Companies → Groups.

2. Configure the following groups:

   - **Tender User:** Can view tenders and submit bids
   - **Tender Manager:** Can create and manage tenders
   - **Tender Administrator:** Full access to all tender features
   - **GeM Integration User:** Can access GeM integration features
   - **Analytics User:** Can access analytics and dashboards

3. Assign users to the appropriate groups based on their roles.

Additional Configuration
=====================

Import/Export Templates
---------------------

To configure import/export templates:

1. Navigate to Tenders → Configuration → Import/Export Templates.

2. Create templates for importing and exporting:
   
   - Tender data
   - Bid data
   - Document metadata
   - Analytics data

Custom Fields
-----------

To add custom fields to tender or bid forms:

1. Navigate to Settings → Technical → Database Structure → Fields.

2. Click "Create" to add a new custom field.

3. Configure the field properties:

   - **Model:** Select tender.tender, tender.bid, or other models
   - **Field Name:** Enter a technical name for the field
   - **Field Label:** Enter the display label
   - **Field Type:** Select the data type (char, integer, selection, etc.)
   - **Required:** Check if the field is required
   - **Visible:** Check if the field should be visible in forms and reports

4. Click "Save" to add the field.

Workflow Customization
-------------------

To customize the tender workflow:

1. Navigate to Settings → Technical → Workflows → Workflows.

2. Select the "Tender" workflow.

3. Modify the workflow states and transitions as needed.

4. Click "Save" to apply your changes.


# File: tender_management/doc/user_manual.rst
===========
User Manual
===========

This user manual provides detailed instructions for using the Tender & GeM Bid Management module. It covers all aspects of the system from creating tenders to analyzing bid data.

Dashboard
========

The dashboard is the main entry point to the system, providing an overview of tender activities and key metrics.

Accessing the Dashboard
---------------------

1. Log in to Odoo.
2. Navigate to Tenders → Dashboard.

Dashboard Components
------------------

The dashboard includes several components:

- **Tender Summary:** Overview of tender counts by status
- **Value Distribution:** Graphical representation of tender values
- **Recent Tenders:** List of recently created or modified tenders
- **Upcoming Deadlines:** Tenders with approaching submission deadlines
- **Tender Success Rate:** Analytics on tender award success rates
- **GeM Status:** Overview of GeM bid statuses

Customizing the Dashboard
----------------------

To customize your dashboard:

1. Click the "Customize" button in the top-right corner.
2. Select the widgets you want to display.
3. Drag and drop widgets to rearrange them.
4. Click "Save" to apply your changes.

Creating a New Tender
===================

Creating a Standard Tender
------------------------

1. Navigate to Tenders → Tenders → Create.
2. Fill in the required fields:
   - **Name:** Enter a descriptive name for the tender
   - **Reference:** A unique reference code (auto-generated or manual)
   - **Tender Type:** Select the type of tender
   - **Submission Deadline:** Set the deadline for bid submissions
   - **Estimated Value:** Enter the estimated contract value
   - **Currency:** Select the currency
   - **Description:** Enter a detailed description of the tender requirements
3. Add tender documents by clicking the "Add a document" button.
4. Define line items by navigating to the "Items" tab.
5. Set evaluation criteria in the "Evaluation" tab.
6. Click "Save" to create the tender as a draft.
7. Click "Publish" when ready to make the tender visible to bidders.

Creating a GeM Tender
-------------------

1. Navigate to Tenders → GeM Tenders → Create.
2. Check the "Is GeM Tender" checkbox.
3. Fill in the standard tender fields.
4. Enter the GeM-specific fields:
   - **GeM Bid Number:** The official GeM bid number
   - **GeM Category:** Select the relevant GeM category
   - **GeM Department:** Select the department
   - **GeM Contract Type:** Select the contract type
5. Click "Fetch from GeM" to import details from the GeM portal (requires valid GeM bid number).
6. Review and edit the imported information if needed.
7. Click "Save" to create the GeM tender.
8. Click "Publish" when ready.

Managing Tender Documents
======================

Uploading Documents
-----------------

1. Open the tender form.
2. Navigate to the "Documents" tab.
3. Click "Add" to upload a new document.
4. Select the document type from the dropdown.
5. Click "Upload" and select the file from your computer.
6. Enter a description for the document.
7. Set visibility and access rights for the document.
8. Click "Save" to add the document.

Using OCR Processing
-----------------

For PDF documents containing text that needs extraction:

1. Upload the document as described above.
2. Click on the document in the list.
3. Click the "Process with OCR" button.
4. Wait for the OCR processing to complete.
5. Review the extracted text and data.
6. Click "Apply to Tender" to update tender fields with extracted data.
7. Click "Save" to confirm the changes.

Document Versioning
-----------------

When updating an existing document:

1. Find the document in the Documents tab.
2. Click the document to open it.
3. Click "Upload New Version."
4. Select the updated file from your computer.
5. Enter a comment describing the changes.
6. Click "Upload" to add the new version.

The system maintains a history of all document versions, which you can access by clicking the "History" button on the document form.

Managing Bids
===========

Receiving Bids
------------

1. Bidders submit bids through the portal or you can manually enter them.
2. To manually enter a bid:
   - Open the tender.
   - Navigate to the "Bids" tab.
   - Click "Create" to add a new bid.
   - Enter the bidder details and bid information.
   - Upload any bid documents.
   - Click "Save" to record the bid.

Evaluating Bids
-------------

1. Open the tender form.
2. Navigate to the "Bids" tab.
3. Click "Start Evaluation" to begin the evaluation process.
4. For each bid:
   - Review the bid details and documents.
   - Navigate to the "Evaluation" tab of the bid.
   - Score each criterion based on the bid content.
   - Add comments to justify your scores.
   - Click "Save" to record your evaluation.
5. Once all bids are evaluated, click "Calculate Ranking" to see the bid rankings.
6. Review the rankings and make any adjustments if needed.

Awarding a Tender
--------------

1. Open the tender form.
2. Navigate to the "Bids" tab.
3. Review the bid rankings.
4. Select the winning bid by clicking the checkbox next to it.
5. Click "Award Tender" to award the tender to the selected bidder.
6. Enter any additional award information in the popup form.
7. Click "Confirm Award" to finalize the award.

GeM Integration Features
=====================

Importing GeM Tenders
-------------------

To import tenders from the GeM portal:

1. Navigate to Tenders → GeM Integration → Import Tenders.
2. Enter your search criteria:
   - Date range
   - Categories
   - Departments
   - Keywords
3. Click "Search on GeM" to find matching tenders.
4. Select the tenders you want to import.
5. Click "Import Selected" to create tender records in the system.

Syncing Bid Status with GeM
-------------------------

To synchronize bid statuses with the GeM portal:

1. Open a GeM tender.
2. Click the "Sync with GeM" button.
3. The system will connect to the GeM portal and update the tender and bid statuses.
4. Review the changes and click "Save" to confirm the updates.

Submitting Bids to GeM
--------------------

To submit a bid to the GeM portal:

1. Create a bid for a GeM tender as described in the "Receiving Bids" section.
2. Ensure all required fields are filled.
3. Click "Submit to GeM" to send the bid to the GeM portal.
4. The system will display a confirmation message with the GeM bid reference number.
5. Click "OK" to close the confirmation dialog.

Analytics and Reporting
====================

Standard Reports
-------------

The system includes several standard reports:

1. **Tender Summary Report:**
   - Navigate to Tenders → Reports → Tender Summary
   - Select the date range and other filters
   - Click "Generate Report"

2. **Bid Analysis Report:**
   - Navigate to Tenders → Reports → Bid Analysis
   - Select the filters and grouping options
   - Click "Generate Report"

3. **Success Rate Report:**
   - Navigate to Tenders → Reports → Success Rate
   - Select the analysis parameters
   - Click "Generate Report"

4. **Vendor Performance Report:**
   - Navigate to Tenders → Reports → Vendor Performance
   - Select the vendor and analysis period
   - Click "Generate Report"

Custom Reports
-----------

To create a custom report:

1. Navigate to Tenders → Reports → Custom Reports.
2. Click "Create" to start a new report.
3. Select the report type and data sources.
4. Define the report parameters and filters.
5. Design the report layout using the available fields.
6. Save the report design.
7. Run the report by clicking "Generate."

AI Analytics
----------

For AI-powered analytics and predictions:

1. Navigate to Tenders → Analytics → AI Insights.
2. Select the analysis type:
   - Bid Success Prediction
   - Vendor Performance Analysis
   - Price Trend Analysis
   - Risk Assessment
3. Set the analysis parameters.
4. Click "Run Analysis" to generate insights.
5. Review the results and predictions.
6. Click "Export" to save the analysis as a PDF or Excel file.

Dashboards
--------

To create custom dashboards:

1. Navigate to Tenders → Analytics → Dashboards.
2. Click "Create" to start a new dashboard.
3. Enter a name for the dashboard.
4. Click "Add Widget" to add visualizations to the dashboard.
5. For each widget:
   - Select the widget type (chart, table, metric, etc.)
   - Configure the data source and parameters
   - Set the widget size and position
   - Click "Add" to place the widget on the dashboard
6. Click "Save" to save the dashboard configuration.

Mobile App Features
================

The Tender Management mobile app allows you to access key features on the go:

1. **Tender Notifications:**
   - Receive push notifications for new tenders, approaching deadlines, and bid updates

2. **Document Access:**
   - View and download tender documents
   - Upload documents from your mobile device

3. **Bid Submission:**
   - Submit bids from your mobile device
   - Upload bid documents using your camera

4. **Approval Workflows:**
   - Review and approve tenders and bids
   - Receive notifications for pending approvals

To install the mobile app:

1. Download the Odoo mobile app from the App Store or Google Play.
2. Log in with your Odoo credentials.
3. Navigate to the Tenders module.

Troubleshooting
=============

Common Issues
-----------

**Issue: Cannot publish a tender**

Possible causes:
- Missing required fields
- Insufficient permissions
- Approval workflow requirements not met

Solution:
1. Check for error messages indicating missing fields
2. Verify that you have tender manager permissions
3. Ensure all approval steps are completed

**Issue: OCR processing fails**

Possible causes:
- Document format not supported
- Poor document quality
- OCR service configuration issue

Solution:
1. Ensure the document is in a supported format (PDF, TIFF, JPG)
2. Upload a clearer copy of the document
3. Check the OCR service configuration in the settings

**Issue: GeM integration not working**

Possible causes:
- Invalid API credentials
- Network connectivity issues
- GeM portal maintenance

Solution:
1. Verify your GeM API credentials in the settings
2. Check your network connection
3. Verify if the GeM portal is operational

Getting Help
----------

If you encounter issues not covered in this manual:

1. Click the "Help" button in the top-right corner of any screen.
2. Search the knowledge base for answers.
3. Click "Contact Support" to submit a support ticket.
4. For urgent issues, call the support hotline at +1-234-567-8900.


# File: tender_management/doc/api_reference.rst
=============
API Reference
=============

The Tender & GeM Bid Management module provides a comprehensive API for integrating with external systems. This document describes the available API endpoints and how to use them.

Authentication
============

All API requests require authentication using API keys or OAuth2 tokens.

API Key Authentication
--------------------

1. Generate an API key in the Odoo interface:
   - Navigate to Settings → Technical → API Keys
   - Click "Generate New Key"
   - Copy the generated key

2. Include the API key in your requests:

.. code-block:: bash

    curl -X GET https://your-odoo-server/api/v1/tenders \
      -H "Content-Type: application/json" \
      -H "X-API-Key: your-api-key"

OAuth2 Authentication
-------------------

1. Register your application:
   - Navigate to Settings → Technical → OAuth2 Apps
   - Register your application to get client credentials

2. Request an access token:

.. code-block:: bash

    curl -X POST https://your-odoo-server/oauth2/token \
      -d "grant_type=client_credentials" \
      -d "client_id=your-client-id" \
      -d "client_secret=your-client-secret"

3. Use the access token in your requests:

.. code-block:: bash

    curl -X GET https://your-odoo-server/api/v1/tenders \
      -H "Authorization: Bearer your-access-token"

Tender API
=========

List Tenders
----------

Retrieves a list of tenders with optional filtering.

**Endpoint:** ``GET /api/v1/tenders``

**Parameters:**

- ``limit`` (optional): Maximum number of records to return (default: 80)
- ``offset`` (optional): Number of records to skip (default: 0)
- ``order`` (optional): Field to sort by (default: "id desc")
- ``domain`` (optional): Search domain in JSON format
- ``fields`` (optional): Comma-separated list of fields to include

**Example Request:**

.. code-block:: bash

    curl -X GET "https://your-odoo-server/api/v1/tenders?limit=10&fields=id,name,state" \
      -H "Authorization: Bearer your-access-token"

**Example Response:**

.. code-block:: json

    {
      "count": 45,
      "results": [
        {
          "id": 1,
          "name": "Office Supplies Tender",
          "state": "published"
        },
        {
          "id": 2,
          "name": "IT Equipment Tender",
          "state": "draft"
        }
      ]
    }

Get Tender Details
---------------

Retrieves detailed information about a specific tender.

**Endpoint:** ``GET /api/v1/tenders/{id}``

**Parameters:**

- ``id`` (required): The ID of the tender
- ``fields`` (optional): Comma-separated list of fields to include

**Example Request:**

.. code-block:: bash

    curl -X GET "https://your-odoo-server/api/v1/tenders/1" \
      -H "Authorization: Bearer your-access-token"

**Example Response:**

.. code-block:: json

    {
      "id": 1,
      "name": "Office Supplies Tender",
      "reference": "TEND-2024-001",
      "tender_type_id": {
        "id": 3,
        "name": "Goods"
      },
      "submission_deadline": "2024-12-31 23:59:59",
      "estimated_value": 5000.00,
      "currency_id": {
        "id": 1,
        "name": "USD"
      },
      "state": "published",
      "description": "Procurement of office supplies for the main office.",
      "is_gem": false,
      "created_date": "2024-01-15 10:30:45",
      "items": [
        {
          "id": 1,
          "name": "Paper A4",
          "quantity": 100,
          "unit_price": 5.00
        },
        {
          "id": 2,
          "name": "Pens",
          "quantity": 200,
          "unit_price": 1.50
        }
      ]
    }

Create Tender
-----------

Creates a new tender record.

**Endpoint:** ``POST /api/v1/tenders``

**Request Body:**

.. code-block:: json

    {
      "name": "IT Services Tender",
      "reference": "TEND-2024-002",
      "tender_type_id": 4,
      "submission_deadline": "2024-12-15 23:59:59",
      "estimated_value": 50000.00,
      "currency_id": 1,
      "description": "Procurement of IT support services.",
      "is_gem": false
    }

**Example Request:**

.. code-block:: bash

    curl -X POST "https://your-odoo-server/api/v1/tenders" \
      -H "Authorization: Bearer your-access-token" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "IT Services Tender",
        "reference": "TEND-2024-002",
        "tender_type_id": 4,
        "submission_deadline": "2024-12-15 23:59:59",
        "estimated_value": 50000.00,
        "currency_id": 1,
        "description": "Procurement of IT support services.",
        "is_gem": false
      }'

**Example Response:**

.. code-block:: json

    {
      "id": 3,
      "name": "IT Services Tender",
      "reference": "TEND-2024-002",
      "state": "draft"
    }

Update Tender
-----------

Updates an existing tender record.

**Endpoint:** ``PUT /api/v1/tenders/{id}``

**Parameters:**

- ``id`` (required): The ID of the tender to update

**Request Body:** JSON object with fields to update

**Example Request:**

.. code-block:: bash

    curl -X PUT "https://your-odoo-server/api/v1/tenders/3" \
      -H "Authorization: Bearer your-access-token" \
      -H "Content-Type: application/json" \
      -d '{
        "description": "Updated description for IT services tender.",
        "submission_deadline": "2024-12-20 23:59:59"
      }'

**Example Response:**

.. code-block:: json

    {
      "id": 3,
      "name": "IT Services Tender",
      "state": "draft"
    }

Delete Tender
-----------

Deletes a tender record.

**Endpoint:** ``DELETE /api/v1/tenders/{id}``

**Parameters:**

- ``id`` (required): The ID of the tender to delete

**Example Request:**

.. code-block:: bash

    curl -X DELETE "https://your-odoo-server/api/v1/tenders/3" \
      -H "Authorization: Bearer your-access-token"

**Example Response:**

.. code-block:: json

    {
      "result": true
    }

Change Tender State
----------------

Updates the state of a tender.

**Endpoint:** ``POST /api/v1/tenders/{id}/change_state``

**Parameters:**

- ``id`` (required): The ID of the tender
- ``state`` (required): The new state (draft, published, closed, awarded, cancelled)

**Example Request:**

.. code-block:: bash

    curl -X POST "https://your-odoo-server/api/v1/tenders/1/change_state" \
      -H "Authorization: Bearer your-access-token" \
      -H "Content-Type: application/json" \
      -d '{
        "state": "published"
      }'

**Example Response:**

.. code-block:: json

    {
      "id": 1,
      "name": "Office Supplies Tender",
      "state": "published"
    }

Bid API
======

List Bids
--------

Retrieves a list of bids for a tender.

**Endpoint:** ``GET /api/v1/tenders/{tender_id}/bids``

**Parameters:**

- ``tender_id`` (required): The ID of the tender
- ``limit`` (optional): Maximum number of records to return
- ``offset`` (optional): Number of records to skip
- ``fields`` (optional): Comma-separated list of fields to include

**Example Request:**

.. code-block:: bash

    curl -X GET "https://your-odoo-server/api/v1/tenders/1/bids" \
      -H "Authorization: Bearer your-access-token"

**Example Response:**

.. code-block:: json

    {
      "count": 3,
      "results": [
        {
          "id": 1,
          "partner_id": {
            "id": 10,
            "name": "ABC Supplies"
          },
          "amount": 4800.00,
          "currency_id": {
            "id": 1,
            "name": "USD"
          },
          "state": "submitted",
          "submission_date": "2024-02-10 14:25:30"
        },
        {
          "id": 2,
          "partner_id": {
            "id": 11,
            "name": "XYZ Corporation"
          },
          "amount": 5200.00,
          "currency_id": {
            "id": 1,
            "name": "USD"
          },
          "state": "submitted",
          "submission_date": "2024-02-11 09:15:45"
        }
      ]
    }

Create Bid
--------

Creates a new bid for a tender.

**Endpoint:** ``POST /api/v1/tenders/{tender_id}/bids``

**Parameters:**

- ``tender_id`` (required): The ID of the tender

**Request Body:**

.. code-block:: json

    {
      "partner_id": 12,
      "amount": 4950.00,
      "currency_id": 1,
      "technical_score": 85,
      "description": "Competitive bid with high-quality products."
    }

**Example Request:**

.. code-block:: bash

    curl -X POST "https://your-odoo-server/api/v1/tenders/1/bids" \
      -H "Authorization: Bearer your-access-token" \
      -H "Content-Type: application/json" \
      -d '{
        "partner_id": 12,
        "amount": 4950.00,
        "currency_id": 1,
        "technical_score": 85,
        "description": "Competitive bid with high-quality products."
      }'

**Example Response:**

.. code-block:: json

    {
      "id": 3,
      "partner_id": {
        "id": 12,
        "name": "Best Supplies Ltd"
      },
      "amount": 4950.00,
      "state": "draft"
    }

GeM Integration API
=================

Import GeM Tender
--------------

Imports a tender from the GeM portal.

**Endpoint:** ``POST /api/v1/gem/import_tender``

**Request Body:**

.. code-block:: json

    {
      "gem_bid_no": "GEM/2024/B/12345"
    }

**Example Request:**

.. code-block:: bash

    curl -X POST "https://your-odoo-server/api/v1/gem/import_tender" \
      -H "Authorization: Bearer your-access-token" \
      -H "Content-Type: application/json" \
      -d '{
        "gem_bid_no": "GEM/2024/B/12345"
      }'

**Example Response:**

.. code-block:: json

    {
      "id": 4,
      "name": "Supply of IT Equipment",
      "reference": "GEM-2024-B-12345",
      "is_gem": true,
      "gem_bid_no": "GEM/2024/B/12345",
      "state": "draft"
    }

Sync GeM Status
------------

Synchronizes the status of a GeM tender.

**Endpoint:** ``POST /api/v1/gem/sync_status``

**Request Body:**

.. code-block:: json

    {
      "tender_id": 4
    }

**Example Request:**

.. code-block:: bash

    curl -X POST "https://your-odoo-server/api/v1/gem/sync_status" \
      -H "Authorization: Bearer your-access-token" \
      -H "Content-Type: application/json" \
      -d '{
        "tender_id": 4
      }'

**Example Response:**

.. code-block:: json

    {
      "id": 4,
      "name": "Supply of IT Equipment",
      "gem_bid_no": "GEM/2024/B/12345",
      "gem_status": "PUBLISHED",
      "state": "published",
      "last_synced": "2024-03-15 10:30:45"
    }

Document API
==========

Upload Document
------------

Uploads a document for a tender or bid.

**Endpoint:** ``POST /api/v1/documents``

**Request Body (multipart/form-data):**

- ``model`` (required): The model name (tender.tender or tender.bid)
- ``res_id`` (required): The record ID
- ``document_type`` (required): The document type code
- ``name`` (required): The document name
- ``description`` (optional): The document description
- ``file`` (required): The file to upload

**Example Request:**

.. code-block:: bash

    curl -X POST "https://your-odoo-server/api/v1/documents" \
      -H "Authorization: Bearer your-access-token" \
      -F "model=tender.tender" \
      -F "res_id=1" \
      -F "document_type=tech_spec" \
      -F "name=Technical Specifications" \
      -F "description=Detailed technical specifications for the tender" \
      -F "file=@/path/to/file.pdf"

**Example Response:**

.. code-block:: json

    {
      "id": 5,
      "name": "Technical Specifications",
      "model": "tender.tender",
      "res_id": 1,
      "document_type": "tech_spec",
      "file_size": 256000,
      "mimetype": "application/pdf"
    }

OCR Process Document
-----------------

Processes a document with OCR to extract text and data.

**Endpoint:** ``POST /api/v1/documents/{id}/ocr_process``

**Parameters:**

- ``id`` (required): The ID of the document

**Example Request:**

.. code-block:: bash

    curl -X POST "https://your-odoo-server/api/v1/documents/5/ocr_process" \
      -H "Authorization: Bearer your-access-token"

**Example Response:**

.. code-block:: json

    {
      "id": 5,
      "name": "Technical Specifications",
      "ocr_status": "completed",
      "extracted_text": "Technical specifications for office supplies...",
      "extracted_fields": {
        "quantity": "100",
        "price": "5000",
        "delivery_date": "2024-12-31"
      }
    }

Analytics API
===========

Generate Dashboard Data
-------------------

Generates data for a dashboard.

**Endpoint:** ``POST /api/v1/analytics/generate_dashboard``

**Request Body:**

.. code-block:: json

    {
      "dashboard_id": 1,
      "date_from": "2024-01-01",
      "date_to": "2024-12-31",
      "tender_types": [1, 2, 3],
      "states": ["draft", "published", "closed", "awarded"]
    }

**Example Request:**

.. code-block:: bash

    curl -X POST "https://your-odoo-server/api/v1/analytics/generate_dashboard" \
      -H "Authorization: Bearer your-access-token" \
      -H "Content-Type: application/json" \
      -d '{
        "dashboard_id": 1,
        "date_from": "2024-01-01",
        "date_to": "2024-12-31",
        "tender_types": [1, 2, 3],
        "states": ["draft", "published", "closed", "awarded"]
      }'

**Example Response:**

.. code-block:: json

    {
      "dashboard_id": 1,
      "data": {
        "tender_count": 45,
        "total_value": 1250000,
        "by_type": {
          "Goods": 15,
          "Services": 20,
          "Construction": 10
        },
        "by_state": {
          "draft": 10,
          "published": 15,
          "closed": 12,
          "awarded": 8
        },
        "monthly_trend": [
          {"month": "Jan", "count": 3, "value": 75000},
          {"month": "Feb", "count": 4, "value": 120000},
          {"month": "Mar", "count": 5, "value": 150000}
        ]
      }
    }

Predict Bid Success
----------------

Predicts the success rate of a bid using AI analytics.

**Endpoint:** ``POST /api/v1/analytics/predict_bid_success``

**Request Body:**

.. code-block:: json

    {
      "bid_id": 3
    }

**Example Request:**

.. code-block:: bash

    curl -X POST "https://your-odoo-server/api/v1/analytics/predict_bid_success" \
      -H "Authorization: Bearer your-access-token" \
      -H "Content-Type: application/json" \
      -d '{
        "bid_id": 3
      }'

**Example Response:**

.. code-block:: json

    {
      "bid_id": 3,
      "predicted_success_rate": 0.75,
      "confidence": 0.85,
      "factors": {
        "bid_competitiveness": 0.8,
        "technical_alignment": 0.7,
        "past_performance": 0.9
      }
    }

Error Handling
============

The API uses standard HTTP status codes to indicate the success or failure of requests:

- **200 OK:** The request was successful
- **201 Created:** The resource was successfully created
- **400 Bad Request:** The request was invalid or missing required parameters
- **401 Unauthorized:** Authentication is required or failed
- **403 Forbidden:** The authenticated user does not have permission to access the resource
- **404 Not Found:** The requested resource was not found
- **500 Internal Server Error:** An error occurred on the server

Error responses include a JSON object with details about the error:

.. code-block:: json

    {
      "error": "Bad Request",
      "code": 400,
      "message": "Missing required field: name",
      "details": {
        "field": "name",
        "reason": "required"
      }
    }

Rate Limiting
===========

API requests are subject to rate limiting to prevent abuse. The current limits are:

- 100 requests per minute per API key
- 5,000 requests per day per API key

Rate limit information is included in the response headers:

- ``X-RateLimit-Limit``: The rate limit ceiling for the given type of request
- ``X-RateLimit-Remaining``: The number of requests left for the time window
- ``X-RateLimit-Reset``: The time at which the current rate limit window resets

When a rate limit is exceeded, the API returns a 429 Too Many Requests status code with a JSON error object.

Versioning
=========

The API is versioned to ensure backward compatibility. The current version is v1.

To use a specific API version, include the version number in the URL path:

.. code-block:: bash

    https://your-odoo-server/api/v1/tenders

API changes are documented in the changelog, and deprecated features are supported for at least 6 months before being removed.

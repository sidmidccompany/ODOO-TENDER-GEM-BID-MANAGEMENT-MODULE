===================================
Tender & GeM Bid Management Module
===================================

A comprehensive solution for managing tenders and Government e-Marketplace (GeM) bids in Odoo.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   configuration
   user_manual
   api_reference

Overview
========

The Tender & GeM Bid Management module provides organizations with a complete solution for managing the tender and bidding process, with special integration for the Government e-Marketplace (GeM) in India. This module helps organizations manage the entire tender lifecycle from publication to award, with powerful features for document management, OCR processing, and analytics.

Key Features
===========

- Complete tender lifecycle management
- GeM bid integration and synchronization
- OCR document processing
- Automated bid evaluation
- AI-powered analytics and success prediction
- Comprehensive reporting and dashboards
- Bidder management and evaluation
- Document management with versioning
- Multi-language support
- Role-based access control
- Email notifications and alerts

Support
=======

For questions or support, please contact support@yourcompany.com or visit our support portal at https://support.yourcompany.com.


# File: tender_management/doc/installation.rst
============
Installation
============

Prerequisites
============

Before installing the Tender & GeM Bid Management module, ensure you have:

- Odoo 17.0 or later
- PostgreSQL 12 or later
- Python 3.10 or later
- Additional Python dependencies as listed in the requirements file

Standard Installation
====================

1. Download the module
----------------------

Download the module from the Odoo App Store or your provider's website and place it in your Odoo addons directory.

.. code-block:: bash

    cd /path/to/odoo/addons
    git clone https://github.com/yourcompany/tender_management.git

2. Install dependencies
----------------------

Install the required Python dependencies:

.. code-block:: bash

    pip install -r tender_management/requirements.txt

3. Update Odoo addons list
-------------------------

Restart your Odoo server and update the addons list from the Odoo Apps menu.

4. Install the module
--------------------

Navigate to Apps menu and search for "Tender Management". Click "Install" to install the module.

Alternatively, you can use the Odoo command line:

.. code-block:: bash

    python odoo-bin -c /path/to/odoo.conf -d your_database --install=tender_management

5. Post-installation steps
-------------------------

After installation, you will need to:

- Configure your GeM API credentials
- Set up OCR service connection (if using)
- Configure AI analytics (if using)
- Set up user permissions

Docker Installation
==================

If you are using Docker, you can use the following commands to add the module to your Odoo instance:

1. Add to your Dockerfile:

.. code-block:: dockerfile

    FROM odoo:17

    USER root
    
    # Install system dependencies
    RUN apt-get update && apt-get install -y \
        python3-dev \
        libssl-dev \
        libffi-dev \
        && rm -rf /var/lib/apt/lists/*
    
    # Clone the module
    RUN git clone https://github.com/yourcompany/tender_management.git /mnt/extra-addons/tender_management
    
    # Install Python dependencies
    RUN pip3 install -r /mnt/extra-addons/tender_management/requirements.txt
    
    USER odoo

2. Rebuild your Docker image:

.. code-block:: bash

    docker-compose build
    docker-compose up -d

3. Install the module through the Odoo web interface.

Upgrading
=========

To upgrade the module from a previous version:

1. Backup your database
----------------------

Always backup your database before upgrading:

.. code-block:: bash

    pg_dump your_database > your_database_backup.sql

2. Update the module files
-------------------------

Replace the old module files with the new version:

.. code-block:: bash

    cd /path/to/odoo/addons
    rm -rf tender_management
    git clone https://github.com/yourcompany/tender_management.git

3. Update dependencies
--------------------

Install any new dependencies:

.. code-block:: bash

    pip install -r tender_management/requirements.txt

4. Upgrade the module
-------------------

Go to the Apps menu, find the "Tender Management" module, and click "Upgrade".

Alternatively, use the command line:

.. code-block:: bash

    python odoo-bin -c /path/to/odoo.conf -d your_database -u tender_management

Troubleshooting
==============

Common issues and solutions:

Database migration errors
------------------------

If you encounter errors during database migration:

1. Check the Odoo server logs for specific error messages
2. Ensure your database backup is intact
3. Try running the update in maintenance mode:

.. code-block:: bash

    python odoo-bin -c /path/to/odoo.conf -d your_database -u tender_management --stop-after-init

Missing dependencies
------------------

If you encounter missing dependency errors:

1. Ensure all requirements are installed:

.. code-block:: bash

    pip install -r tender_management/requirements.txt

2. Check system dependencies with:

.. code-block:: bash

    ldd /usr/local/lib/python3.10/site-packages/some_package.so

Permission issues
---------------

If you encounter permission errors:

1. Check file ownership:

.. code-block:: bash

    chown -R odoo:odoo /path/to/odoo/addons/tender_management

2. Check directory permissions:

.. code-block:: bash

    chmod -R 755 /path/to/odoo/addons/tender_management


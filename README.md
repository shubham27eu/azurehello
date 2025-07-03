# Consent Management System (CMS)

## Project Overview

The Consent Management System (CMS) is a Flask-based application designed to manage user consent for document access and data processing. It aims to provide a robust framework for:

*   Securely ingesting and storing documents.
*   Identifying and classifying data within documents, particularly sensitive or personally identifiable information (PII).
*   Allowing users to define granular consent preferences for their documents and the data within them.
*   Enforcing these consent preferences when data access is requested.
*   Maintaining comprehensive audit logs of all relevant activities.

This system is being developed to address the growing need for transparent and user-controlled data privacy.

## Current Functionality (Phase 1 - Setup)

As of the initial setup phase, the project has the following basic structure and capabilities:

*   **Flask Application Core:**
    *   A minimal Flask application (`app.py`) is set up.
    *   Basic project structure with placeholders for models (`models.py`) and API routes (`routes.py`).
*   **API:**
    *   A health check endpoint (`/api/health`) is available to confirm the application is running.
*   **Development Environment:**
    *   `requirements.txt` for managing Python dependencies (currently just Flask).
    *   `.gitignore` for standard Python and Flask project exclusions.
    *   Git repository initialized for version control.
*   **Documentation (Initial Drafts):**
    *   `SYSTEM_REQUIREMENTS.md`: Outlines basic system prerequisites.
    *   `DATA_FLOW_AND_COMPONENTS.md`: High-level overview of intended system architecture and data flows.
    *   `DATABASE_SCHEMA.md`: Initial proposal for the database structure.
    *   This `README.md`: Provides a general project overview.

## Core Modules (Planned for Development)

The system will be built around the following core modules:

1.  **Document Management:** Handling document uploads, storage, typing, and metadata extraction.
2.  **Data Classification:** Identifying and tagging fields within documents based on sensitivity (e.g., PII).
3.  **Consent Engine:** Managing user consent definitions, linking them to documents/data, and providing logic for consent checks.
4.  **Access Control:** Enforcing consent rules when data is requested, including potential data masking or redaction.
5.  **API Layer:** Providing RESTful endpoints for all system interactions.
6.  **Auditing:** Logging all significant system events and user actions.
7.  **User Management (TBD):** Handling user identities and authentication, potentially integrating with external providers.

## Next Steps

The immediate next steps involve:

1.  Detailed architecture and design of the system components.
2.  Setting up the database and ORM (e.g., SQLAlchemy).
3.  Developing the core functionalities for document ingestion and basic consent definition.

## Running the Project Locally (Current State)

1.  Ensure Python 3.8+ and pip are installed.
2.  Clone the repository: `git clone <repository_url>`
3.  Navigate to the project directory: `cd <project_directory>`
4.  Install dependencies: `pip install -r requirements.txt`
5.  Run the Flask development server: `python app.py`
6.  The application will be accessible at `http://127.0.0.1:5000/`.
    *   The health check is at `http://127.0.0.1:5000/api/health`.

This `README.md` will be updated as the project progresses and new features are added.

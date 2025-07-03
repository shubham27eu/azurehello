# Data Flow and Components (Initial Outline)

This document provides a high-level overview of the anticipated data flow and key components for the Consent Management System. This will be refined as the project progresses.

## Core Components

1.  **API Layer (Flask):**
    *   Handles all incoming HTTP requests.
    *   Routes requests to appropriate services.
    *   Manages request validation and response formatting.
    *   Endpoints for:
        *   Document upload and management.
        *   User authentication and management (to be detailed).
        *   Consent definition and management.
        *   Data access requests (subject to consent).
        *   Audit log viewing (privileged access).

2.  **Document Processing Service:**
    *   Responsible for handling uploaded documents.
    *   Tasks:
        *   Receiving files from the API layer.
        *   Storing raw documents (e.g., in a file system or object store).
        *   Extracting text and metadata (OCR if necessary, TBD).
        *   Identifying document type.
        *   Classifying fields within documents (e.g., PII, sensitive data).
        *   Storing processed document information and metadata in the database.

3.  **Consent Management Service:**
    *   Manages user consent preferences.
    *   Tasks:
        *   Storing and retrieving consent settings per user, per document (or document type).
        *   Allowing users to grant or revoke consent for specific data fields or actions.
        *   Enforcing consent rules when data is accessed.

4.  **Data Access Control Service:**
    *   Mediates access to data based on consent.
    *   Tasks:
        *   Receiving data access requests.
        *   Checking with the Consent Management Service to verify if access is permitted.
        *   Returning data (potentially masked or redacted) or denying access.

5.  **Database (Relational - e.g., PostgreSQL, SQLite for dev):**
    *   Stores:
        *   User information (details TBD).
        *   Document metadata (type, source, processed fields, classifications).
        *   Consent records (user ID, document ID/type, field ID, consent status, timestamp).
        *   Audit logs.

6.  **Audit Logging Service:**
    *   Records significant events in the system.
    *   Events to log:
        *   User login/logout.
        *   Document upload, processing, deletion.
        *   Consent changes (grant, revoke).
        *   Data access attempts (successful, denied).
        *   Policy changes.

7.  **User Interface (UI) (Future - TBD):**
    *   A web-based interface for users to:
        *   Upload documents.
        *   Manage their consent preferences.
        *   View their data (as permitted).
    *   An administrative interface for system management.

## Basic Data Flow Examples

### 1. Document Ingestion and Consent Setup

1.  **User/System uploads a document** via the API Layer.
2.  **API Layer** sends the document to the **Document Processing Service**.
3.  **Document Processing Service**:
    *   Stores the raw document.
    *   Extracts text and metadata.
    *   Identifies document type and classifies fields.
    *   Saves document metadata and field classifications to the **Database**.
4.  **User defines consent preferences** for the document (or its type/fields) via the API Layer.
5.  **API Layer** interacts with the **Consent Management Service**.
6.  **Consent Management Service** stores these preferences in the **Database**.
7.  All significant actions are logged by the **Audit Logging Service** into the **Database**.

### 2. Data Access Request

1.  **User/System requests access to specific data** (e.g., a field in a document) via the API Layer.
2.  **API Layer** forwards the request to the **Data Access Control Service**.
3.  **Data Access Control Service** queries the **Consent Management Service** to check if consent is granted for the requested data and user.
4.  **Consent Management Service** checks the **Database** for relevant consent records.
5.  If consent is granted, **Data Access Control Service** retrieves the data (potentially from the **Document Processing Service** or directly from the **Database** if it's just metadata).
    *   Data might be masked or redacted here based on fine-grained consent.
6.  Data is returned to the user via the **API Layer**.
7.  The access attempt (and its outcome) is logged by the **Audit Logging Service** into the **Database**.

This initial outline will serve as a basis for more detailed architectural design in Phase 2.

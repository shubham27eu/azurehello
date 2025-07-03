# Database Schema (Initial Outline)

This document outlines the initial proposed database schema for the Consent Management System. This schema will evolve as requirements are refined. We'll likely use an ORM like SQLAlchemy with Flask.

## Core Tables

### 1. `users` (If managing users directly, otherwise may link to external auth)

*   `id`: INTEGER, PRIMARY KEY, AUTOINCREMENT
*   `username`: VARCHAR(80), UNIQUE, NOT NULL (or `external_user_id` if using external auth)
*   `email`: VARCHAR(120), UNIQUE, NOT NULL (optional, if applicable)
*   `password_hash`: VARCHAR(255) (if storing passwords, ensure proper hashing)
*   `created_at`: TIMESTAMP, DEFAULT CURRENT_TIMESTAMP
*   `updated_at`: TIMESTAMP, DEFAULT CURRENT_TIMESTAMP

**Notes:** User authentication and management details need further definition. We might integrate with an existing identity provider.

### 2. `documents`

*   `id`: INTEGER, PRIMARY KEY, AUTOINCREMENT
*   `uuid`: VARCHAR(36), UNIQUE, NOT NULL (for external referencing)
*   `filename`: VARCHAR(255), NOT NULL
*   `document_type_id`: INTEGER, FOREIGN KEY (references `document_types.id`) (nullable if type is unknown initially)
*   `uploader_user_id`: INTEGER, FOREIGN KEY (references `users.id`) (nullable if system uploaded)
*   `storage_path`: VARCHAR(1024) (path to raw document, e.g., S3 URL or local path)
*   `mime_type`: VARCHAR(100)
*   `size_bytes`: INTEGER
*   `status`: VARCHAR(50) (e.g., 'uploaded', 'processing', 'processed', 'error')
*   `uploaded_at`: TIMESTAMP, DEFAULT CURRENT_TIMESTAMP
*   `processed_at`: TIMESTAMP (nullable)

### 3. `document_types`

*   `id`: INTEGER, PRIMARY KEY, AUTOINCREMENT
*   `name`: VARCHAR(100), UNIQUE, NOT NULL (e.g., "Payslip", "Utility Bill", "Invoice")
*   `description`: TEXT (optional)
*   `default_policy_id`: INTEGER, FOREIGN KEY (references `policies.id`) (optional, for default handling of fields)

### 4. `document_fields` (Stores information about fields identified within documents)

*   `id`: INTEGER, PRIMARY KEY, AUTOINCREMENT
*   `document_id`: INTEGER, FOREIGN KEY (references `documents.id`), NOT NULL
*   `field_name`: VARCHAR(255), NOT NULL (e.g., "employee_name", "total_amount", "account_number")
*   `field_value_preview`: TEXT (optional, a snippet of the value for quick reference, can be sensitive)
*   `data_classification_id`: INTEGER, FOREIGN KEY (references `data_classifications.id`) (e.g., PII, Sensitive, Public)
*   `coordinates`: JSON (optional, location of the field in the document, e.g., bounding box)
*   `identified_at`: TIMESTAMP, DEFAULT CURRENT_TIMESTAMP

**Note:** The actual extracted values might be stored elsewhere or accessed on-demand from the raw document to avoid duplicating large amounts of data, especially sensitive data. This table focuses on the metadata about the fields.

### 5. `data_classifications` (Predefined list of data sensitivity levels)

*   `id`: INTEGER, PRIMARY KEY, AUTOINCREMENT
*   `name`: VARCHAR(100), UNIQUE, NOT NULL (e.g., "Personally Identifiable Information (PII)", "Financial Data", "Medical Information", "Public")
*   `description`: TEXT (optional)
*   `sensitivity_level`: INTEGER (e.g., 1=Low, 5=High)

### 6. `consents`

*   `id`: INTEGER, PRIMARY KEY, AUTOINCREMENT
*   `user_id`: INTEGER, FOREIGN KEY (references `users.id`), NOT NULL
*   `document_id`: INTEGER, FOREIGN KEY (references `documents.id`) (nullable, if consent is for a document type or all documents)
*   `document_type_id`: INTEGER, FOREIGN KEY (references `document_types.id`) (nullable, if consent is for a specific document instance)
*   `field_name`: VARCHAR(255) (nullable, if consent is for the whole document/type, e.g., "customer_address". Could also be `document_field_id` if granularity is always per-field instance)
*   `consent_purpose_id`: INTEGER, FOREIGN KEY (references `consent_purposes.id`), NOT NULL (e.g., "View", "Download", "Share with X")
*   `is_granted`: BOOLEAN, NOT NULL
*   `expires_at`: TIMESTAMP (nullable, if consent does not expire)
*   `granted_at`: TIMESTAMP, DEFAULT CURRENT_TIMESTAMP
*   `updated_at`: TIMESTAMP, DEFAULT CURRENT_TIMESTAMP

### 7. `consent_purposes` (Defines the reasons/actions for which consent can be given)

*   `id`: INTEGER, PRIMARY KEY, AUTOINCREMENT
*   `name`: VARCHAR(100), UNIQUE, NOT NULL (e.g., "VIEW_DATA", "PROCESS_FOR_ANALYTICS", "SHARE_WITH_PARTNER_X")
*   `description`: TEXT (optional)

### 8. `policies` (Rules for data handling, can be linked to document types or fields)

*   `id`: INTEGER, PRIMARY KEY, AUTOINCREMENT
*   `name`: VARCHAR(100), UNIQUE, NOT NULL
*   `description`: TEXT
*   `rules`: JSON (e.g., default masking rules, access conditions for "unknown" fields)
*   `created_at`: TIMESTAMP, DEFAULT CURRENT_TIMESTAMP

### 9. `audit_logs`

*   `id`: INTEGER, PRIMARY KEY, AUTOINCREMENT
*   `user_id`: INTEGER, FOREIGN KEY (references `users.id`) (nullable for system actions)
*   `action`: VARCHAR(255), NOT NULL (e.g., "USER_LOGIN", "DOCUMENT_UPLOAD", "CONSENT_GRANTED", "DATA_ACCESS_ATTEMPT")
*   `target_resource_type`: VARCHAR(100) (e.g., "Document", "User", "Consent")
*   `target_resource_id`: INTEGER (ID of the affected resource)
*   `status`: VARCHAR(50) (e.g., "SUCCESS", "FAILURE", "PENDING")
*   `details`: TEXT (JSON or plain text with more information)
*   `ip_address`: VARCHAR(45) (optional)
*   `timestamp`: TIMESTAMP, DEFAULT CURRENT_TIMESTAMP

## Relationships (Summary)

*   `users` (1) -- (*) `documents` (uploader)
*   `users` (1) -- (*) `consents`
*   `users` (1) -- (*) `audit_logs` (actor)
*   `document_types` (1) -- (*) `documents`
*   `document_types` (1) -- (*) `consents`
*   `document_types` (1) -- (1) `policies` (default policy)
*   `documents` (1) -- (*) `document_fields`
*   `documents` (1) -- (*) `consents`
*   `data_classifications` (1) -- (*) `document_fields`
*   `consent_purposes` (1) -- (*) `consents`

## Considerations for Future Development

*   **Normalization vs. Denormalization:** This is a fairly normalized schema. Depending on query patterns, some denormalization might be considered for performance.
*   **Indexing:** Proper indexing will be crucial for query performance, especially on foreign keys and frequently queried columns (e.g., `uuid` in `documents`, `user_id` and `document_id` in `consents`).
*   **Scalability:** For very large volumes of documents or logs, partitioning or NoSQL solutions for certain parts (like `audit_logs` or document content) might be explored.
*   **Data Retention and Archival:** Policies for data retention and archival will need to be defined.
*   **Flexibility for Field Definitions:** The `document_fields` table might need to be more flexible if dealing with highly unstructured or variable document types. JSON fields for `field_metadata` could be an option.

This initial schema provides a foundation. It will be implemented and iterated upon using an ORM like SQLAlchemy in the Flask application. The `models.py` file will reflect these table structures.

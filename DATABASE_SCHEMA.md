# Database Schema (Refined for Demo)

This document outlines the database schema for the Consent Management System, refined for the specific demo scenarios. ORM: SQLAlchemy with Flask.

## Core Tables

### 1. `users`
*   `id`: INTEGER, PRIMARY KEY, AUTOINCREMENT
*   `username`: VARCHAR(80), UNIQUE, NOT NULL
*   `email`: VARCHAR(120), UNIQUE, NOT NULL (optional)
*   `password_hash`: VARCHAR(255) (ensure proper hashing)
*   `role`: VARCHAR(50), NOT NULL (e.g., 'professor', 'student', 'employer', 'admin')
*   `created_at`: TIMESTAMP, DEFAULT CURRENT_TIMESTAMP
*   `updated_at`: TIMESTAMP, DEFAULT CURRENT_TIMESTAMP

### 2. `document_types`
*   `id`: INTEGER, PRIMARY KEY, AUTOINCREMENT
*   `name`: VARCHAR(100), UNIQUE, NOT NULL (e.g., "Grade Sheet")
*   `description`: TEXT (optional)
*   `fields_definition`: JSON, NOT NULL
    *   *Example `fields_definition` for "Grade Sheet":*
        ```json
        [
          {"name": "StudentName", "type": "string", "label": "Student Name", "access": "open"},
          {"name": "StudentID", "type": "string", "label": "Student ID", "access": "open"},
          {"name": "CourseName", "type": "string", "label": "Course Name", "access": "open"},
          {"name": "FinalGrade", "type": "string", "label": "Final Grade", "access": "controlled"},
          {"name": "InstructorComments", "type": "text", "label": "Instructor Comments", "access": "controlled"}
        ]
        ```
    *   *`access` can be: 'open' (publicly viewable if document is accessible), 'controlled' (requires explicit consent), 'closed' (never accessible via consent request, only by owner/uploader).*
*   `owner_user_id`: INTEGER, FOREIGN KEY (references `users.id`), NOT NULL // User who defined/owns this type

### 3. `documents`
*   `id`: INTEGER, PRIMARY KEY, AUTOINCREMENT
*   `uuid`: VARCHAR(36), UNIQUE, NOT NULL (for external referencing)
*   `name`: VARCHAR(255), NOT NULL (e.g., "Alice Wonderland - CS101 Grade Sheet")
*   `document_type_id`: INTEGER, FOREIGN KEY (references `document_types.id`), NOT NULL
*   `uploader_user_id`: INTEGER, FOREIGN KEY (references `users.id`), NOT NULL (e.g., Professor Smith who uploaded it)
*   `data_subject_user_id`: INTEGER, FOREIGN KEY (references `users.id`), (nullable, e.g., Student Alice, if the document pertains to a specific user)
*   `content`: JSON, NOT NULL
    *   *Example `content` for a "Grade Sheet" instance:*
        ```json
        {
          "StudentName": "Alice Wonderland",
          "StudentID": "S12345",
          "CourseName": "CS101 Intro to Computing",
          "FinalGrade": "A",
          "InstructorComments": "Excellent work on the final project!"
        }
        ```
*   `status`: VARCHAR(50), DEFAULT 'active' (e.g., 'active', 'archived', 'deleted')
*   `uploaded_at`: TIMESTAMP, DEFAULT CURRENT_TIMESTAMP
*   `updated_at`: TIMESTAMP, DEFAULT CURRENT_TIMESTAMP

### 4. `consent_requests`
*   `id`: INTEGER, PRIMARY KEY, AUTOINCREMENT
*   `document_id`: INTEGER, FOREIGN KEY (references `documents.id`), NOT NULL
*   `requester_user_id`: INTEGER, FOREIGN KEY (references `users.id`), NOT NULL (e.g., Potential Employer, Student B)
*   `owner_user_id`: INTEGER, FOREIGN KEY (references `users.id`), NOT NULL (User responsible for granting consent, e.g., Student A or Professor Smith for Student A's document)
*   `requested_fields`: JSON, NOT NULL // List of field names from `document_types.fields_definition`, e.g., `["FinalGrade", "InstructorComments"]`
*   `purpose`: TEXT, NOT NULL (Reason for request, provided by requester)
*   `status`: VARCHAR(50), NOT NULL, DEFAULT 'pending' (e.g., 'pending', 'approved', 'denied', 'expired_time', 'expired_count', 'revoked')
*   `request_timestamp`: TIMESTAMP, DEFAULT CURRENT_TIMESTAMP
*   `decision_timestamp`: TIMESTAMP (nullable, when owner approved/denied)
*   `decider_user_id`: INTEGER, FOREIGN KEY (references `users.id`) (nullable, user who made the decision, could be `owner_user_id` or a delegate)
*   `grant_expires_at`: TIMESTAMP (nullable, set on approval if consent is time-bound)
*   `grant_access_count_total`: INTEGER (nullable, e.g., allow 5 views, set on approval)
*   `grant_access_count_remaining`: INTEGER (nullable, decremented on each access if `grant_access_count_total` is set)

### 5. `audit_logs`
*   `id`: INTEGER, PRIMARY KEY, AUTOINCREMENT
*   `acting_user_id`: INTEGER, FOREIGN KEY (references `users.id`) (User performing the action. Can be null for pure system actions, though a system user_id is better.)
*   `action`: VARCHAR(255), NOT NULL (e.g., "USER_LOGIN_SUCCESS", "USER_LOGIN_FAILURE", "DOC_TYPE_CREATE", "DOC_UPLOAD", "CONSENT_REQUEST_CREATE", "CONSENT_APPROVE", "CONSENT_DENY", "CONSENT_REVOKE", "DATA_ACCESS_SUCCESS", "DATA_ACCESS_DENIED_NO_CONSENT", "DATA_ACCESS_DENIED_EXPIRED", "DATA_ACCESS_DENIED_NO_ACCESS_TO_FIELD")
*   `target_document_id`: INTEGER, FOREIGN KEY (references `documents.id`) (nullable)
*   `target_field_name`: VARCHAR(255) (nullable, specific field within the document)
*   `target_user_id`: INTEGER, FOREIGN KEY (references `users.id`) (nullable, e.g., data subject of a document, or user whose consent request is being modified)
*   `consent_request_id`: INTEGER, FOREIGN KEY (references `consent_requests.id`) (nullable)
*   `status_outcome`: VARCHAR(50) (e.g., "SUCCESS", "FAILURE", "ATTEMPT")
*   `details`: TEXT (JSON or plain text with more information, e.g., requester IP, error messages, old/new values)
*   `timestamp`: TIMESTAMP, DEFAULT CURRENT_TIMESTAMP

## Relationships Summary:

*   `users` (1) -- (*) `document_types` (owner)
*   `users` (1) -- (*) `documents` (uploader)
*   `users` (1) -- (*) `documents` (data_subject)
*   `users` (1) -- (*) `consent_requests` (requester)
*   `users` (1) -- (*) `consent_requests` (owner/decider)
*   `users` (1) -- (*) `audit_logs` (acting_user, target_user)
*   `document_types` (1) -- (*) `documents`
*   `documents` (1) -- (*) `consent_requests`
*   `documents` (1) -- (*) `audit_logs` (target_document_id)
*   `consent_requests` (1) -- (*) `audit_logs` (consent_request_id)

## Removed Tables (for Demo Simplicity):
*   `document_fields` (field values now in `documents.content`, definitions in `document_types.fields_definition`)
*   `data_classifications` (handled by `access` property in `document_types.fields_definition`)
*   `consents` (active grants are `consent_requests` with `status='approved'` and valid `grant_expires_at`/`grant_access_count_remaining`)
*   `consent_purposes` (`purpose` is free text in `consent_requests`)
*   `policies` (core logic relies on `fields_definition.access` and explicit consent)

This refined schema is tailored for the demo scenarios, prioritizing clarity and minimizing tables while supporting the key consent workflows.Tool output for `overwrite_file_with_block`:

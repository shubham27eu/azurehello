from app import db
from app.models import User, Document, DocumentType, ConsentRequest
from datetime import datetime, timezone
from app.services.audit_logging_service import AuditLoggingService

class DataAccessControlService:
    @staticmethod
    def get_field_value(requester_user_id, document_uuid, field_name):
        # Validate requester
        requester = User.query.get(requester_user_id)
        if not requester:
            # This should ideally not happen if JWT identity is always a valid user ID
            raise ValueError(f"Requester user with id '{requester_user_id}' not found.")

        # Get Document and its DocumentType
        document = Document.query.filter_by(uuid=document_uuid).first()
        if not document:
            raise FileNotFoundError(f"Document with uuid '{document_uuid}' not found.")

        doc_type = document.document_type
        if not doc_type:
            # Should not happen with proper data integrity
            raise RuntimeError(f"DocumentType not found for document '{document_uuid}'.")

        # Find the field definition
        field_def = None
        for f_def in doc_type.fields_definition:
            if f_def.get('name') == field_name:
                field_def = f_def
                break

        if not field_def:
            raise ValueError(f"Field '{field_name}' is not defined in document type '{doc_type.name}'.")

        access_type = field_def.get('access')

        # Check access classification
        if access_type == 'closed':
            AuditLoggingService.log_event(action="DATA_ACCESS_DENIED_CLOSED", acting_user_id=requester_user_id, target_document_id=document.id, target_field_name=field_name, status_outcome="FAILURE", details={"reason": "Field is closed"})
            raise PermissionError(f"Field '{field_name}' is closed and not accessible.")

        if access_type == 'open':
            AuditLoggingService.log_event(action="DATA_ACCESS_SUCCESS_OPEN", acting_user_id=requester_user_id, target_document_id=document.id, target_field_name=field_name, status_outcome="SUCCESS", details={"reason": "Field is open"})
            if field_name not in document.content:
                 # This means data is inconsistent with its type definition
                AuditLoggingService.log_event(action="DATA_ACCESS_FAILURE_INCONSISTENT_DATA", acting_user_id=requester_user_id, target_document_id=document.id, target_field_name=field_name, status_outcome="FAILURE", details={"reason": "Field defined as open but not in content"})
                raise ValueError(f"Field '{field_name}' not found in document content, though defined as open.")
            return document.content.get(field_name)

        if access_type == 'controlled':
            # Check for active, valid consent
            # A field is 'controlled', so we need to check consent requests.
            # The owner of consent is document.data_subject_user_id or document.uploader_user_id
            # For this check, we need to find a ConsentRequest where:
            # - document_id matches
            # - requester_user_id matches
            # - status is 'approved'
            # - requested_fields (JSON list) contains field_name
            # - grant_expires_at is null or in the future
            # - grant_access_count_remaining is null or > 0

            now = datetime.now(timezone.utc)

            # Query for relevant approved consent requests
            # This query could be complex if checking requested_fields as JSON array elements.
            # For SQLite, JSON operations are limited. For PostgreSQL, more advanced JSON queries are possible.
            # Simplification: Iterate through approved consents for this doc & requester.
            print(f"DEBUG: DACService: Checking controlled field '{field_name}' for doc_id={document.id}, requester_id={requester_user_id}") # DEBUG

            approved_consents = ConsentRequest.query.filter_by(
                document_id=document.id,
                requester_user_id=requester_user_id,
                status='approved'
            ).all()

            valid_consent_found = False
            active_consent_request = None
            print(f"DEBUG: DACService: Found {len(approved_consents)} approved consents to check.") # DEBUG

            for consent in approved_consents:
                print(f"DEBUG: DACService: Checking consent ID {consent.id}, fields: {consent.requested_fields}, type: {type(consent.requested_fields)}") # DEBUG
                if field_name not in consent.requested_fields:
                    print(f"DEBUG: DACService: Field '{field_name}' not in consent {consent.id} requested_fields.") # DEBUG
                    continue # This consent doesn't cover the requested field

                print(f"DEBUG: DACService: Field '{field_name}' IS IN consent {consent.id} requested_fields.") # DEBUG

                # Check expiry
                if consent.grant_expires_at and consent.grant_expires_at < now:
                    AuditLoggingService.log_event(action="DATA_ACCESS_DENIED_EXPIRED_TIME", acting_user_id=requester_user_id, target_document_id=document.id, target_field_name=field_name, consent_request_id=consent.id, status_outcome="FAILURE", details={"reason": "Consent expired (time)"})
                    # TODO: Optionally change status to 'expired_time' here or by a batch job
                    # For now, just deny access based on this check
                    continue # Expired

                # Check access count
                if consent.grant_access_count_total is not None: # If count-based
                    if consent.grant_access_count_remaining is None or consent.grant_access_count_remaining <= 0:
                        AuditLoggingService.log_event(action="DATA_ACCESS_DENIED_EXPIRED_COUNT", acting_user_id=requester_user_id, target_document_id=document.id, target_field_name=field_name, consent_request_id=consent.id, status_outcome="FAILURE", details={"reason": "Consent expired (count)"})
                        # TODO: Optionally change status to 'expired_count'
                        continue # Used up

                # If all checks pass, this is a valid consent
                valid_consent_found = True
                active_consent_request = consent
                break

            if valid_consent_found and active_consent_request:
                # Decrement access count if applicable
                if active_consent_request.grant_access_count_total is not None and \
                   active_consent_request.grant_access_count_remaining is not None and \
                   active_consent_request.grant_access_count_remaining > 0:
                    active_consent_request.grant_access_count_remaining -= 1
                    # Consider what happens if it becomes 0 - should status change to 'expired_count'?
                    # if active_consent_request.grant_access_count_remaining == 0:
                    #    active_consent_request.status = 'expired_count' # Or similar
                    db.session.commit() # Save the decremented count

                AuditLoggingService.log_event(action="DATA_ACCESS_SUCCESS_CONSENTED", acting_user_id=requester_user_id, target_document_id=document.id, target_field_name=field_name, consent_request_id=active_consent_request.id, status_outcome="SUCCESS")
                if field_name not in document.content: # Should be caught by DocumentService validation ideally
                    AuditLoggingService.log_event(action="DATA_ACCESS_FAILURE_INCONSISTENT_DATA", acting_user_id=requester_user_id, target_document_id=document.id, target_field_name=field_name, consent_request_id=active_consent_request.id, status_outcome="FAILURE", details={"reason": "Field consented but not in content"})
                    raise ValueError(f"Field '{field_name}' not found in document content, though consent was granted.")
                return document.content.get(field_name)
            else:
                AuditLoggingService.log_event(action="DATA_ACCESS_DENIED_NO_VALID_CONSENT", acting_user_id=requester_user_id, target_document_id=document.id, target_field_name=field_name, status_outcome="FAILURE", details={"reason": "No active/valid consent found"})
                raise PermissionError(f"Access denied: No valid consent found for field '{field_name}'.")

        # Should not be reached if access_type is one of 'open', 'closed', 'controlled'
        AuditLoggingService.log_event(action="DATA_ACCESS_FAILURE_UNKNOWN_ACCESS_TYPE", acting_user_id=requester_user_id, target_document_id=document.id, target_field_name=field_name, status_outcome="FAILURE", details={"access_type": access_type})
        raise PermissionError(f"Unknown access type '{access_type}' for field '{field_name}'.")

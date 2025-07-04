from app import db
from app.models import User, Document, DocumentType, ConsentRequest
from sqlalchemy.exc import IntegrityError
# from datetime import datetime, timedelta # If needed for expiry calculations

class ConsentService:
    @staticmethod
    def create_request(requester_user_id, document_uuid, requested_fields, purpose):
        # Validate requester
        requester = User.query.get(requester_user_id)
        if not requester:
            raise ValueError(f"Requester user with id '{requester_user_id}' not found.")

        # Validate document
        document = Document.query.filter_by(uuid=document_uuid).first()
        if not document:
            raise ValueError(f"Document with uuid '{document_uuid}' not found.")

        # Validate document type and fields
        doc_type = document.document_type # Relies on relationship being loaded or auto-loaded
        if not doc_type:
            # This should ideally not happen if data integrity is maintained
            raise ValueError(f"DocumentType not found for document '{document_uuid}'.")

        if not isinstance(requested_fields, list) or not all(isinstance(rf, str) for rf in requested_fields):
            raise ValueError("requested_fields must be a list of strings.")

        if not requested_fields:
            raise ValueError("requested_fields cannot be empty.")

        valid_field_definitions = {field_def['name']: field_def for field_def in doc_type.fields_definition}

        for req_field in requested_fields:
            if req_field not in valid_field_definitions:
                raise ValueError(f"Requested field '{req_field}' is not defined in the document type '{doc_type.name}'.")
            if valid_field_definitions[req_field]['access'] == 'closed':
                raise PermissionError(f"Field '{req_field}' is marked as 'closed' and cannot be requested for consent.")
            # Note: 'open' fields could also be requested, or client-side could just allow access directly.
            # For now, allow requesting 'open' or 'controlled'. Enforcement is separate.

        if not purpose or not isinstance(purpose, str) or len(purpose.strip()) == 0:
            raise ValueError("A valid purpose string is required.")

        # Determine owner_user_id for the consent
        # Prioritize data_subject_user_id if present, else uploader_user_id
        owner_user_id_for_consent = document.data_subject_user_id if document.data_subject_user_id else document.uploader_user_id

        if not owner_user_id_for_consent:
            # This case should be rare if documents always have an uploader
            raise ValueError("Could not determine an owner for consent for this document.")

        # Check if an identical pending or approved (and not expired/revoked) request already exists
        # This is to prevent duplicate requests. More complex logic might be needed for "overlapping" requests.
        existing_request = ConsentRequest.query.filter_by(
            document_id=document.id,
            requester_user_id=requester_user_id,
            owner_user_id=owner_user_id_for_consent,
            # requested_fields=requested_fields, # Comparing JSON list directly can be tricky depending on DB and order
            purpose=purpose # Maybe also consider purpose in uniqueness
        ).filter(
            ConsentRequest.status.in_(['pending', 'approved']) # Check relevant statuses
        ).first()

        if existing_request:
            # Check if requested_fields are the same. This is a bit naive for JSON lists.
            # A more robust check would normalize the lists (e.g. sort) before comparison or store fields hashed.
            # For now, simple check:
            if sorted(existing_request.requested_fields) == sorted(requested_fields):
                 raise ValueError(f"An identical active or pending consent request (ID: {existing_request.id}) already exists.")


        consent_request = ConsentRequest(
            document_id=document.id,
            requester_user_id=requester_user_id,
            owner_user_id=owner_user_id_for_consent,
            requested_fields=requested_fields, # Stored as JSON
            purpose=purpose.strip(),
            status='pending'
        )

        try:
            db.session.add(consent_request)
            db.session.commit()
            return consent_request
        except IntegrityError as e:
            db.session.rollback()
            # Log e
            raise ValueError("Database integrity error while creating consent request. This might be due to concurrent requests or data issues.")
        except Exception as e:
            db.session.rollback()
            # Log e
            raise RuntimeError(f"An unexpected error occurred while creating the consent request: {str(e)}")

    @staticmethod
    def get_requests_for_owner(owner_user_id, status=None, page=1, per_page=10):
        query = ConsentRequest.query.filter_by(owner_user_id=owner_user_id)
        if status:
            query = query.filter_by(status=status)

        return query.order_by(ConsentRequest.request_timestamp.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)

    @staticmethod
    def get_request_by_id(request_id):
        return ConsentRequest.query.get(request_id)

    @staticmethod
    def decide_request(request_id, decider_user_id, decision, conditions=None):
        consent_request = ConsentService.get_request_by_id(request_id)
        if not consent_request:
            raise ValueError(f"ConsentRequest with id '{request_id}' not found.")

        # Validate decider
        decider = User.query.get(decider_user_id)
        if not decider:
            raise ValueError(f"Decider user with id '{decider_user_id}' not found.")

        if consent_request.owner_user_id != decider.id:
            # Future: could allow admin override or delegation logic here
            raise PermissionError("Only the designated owner can decide on this consent request.")

        if consent_request.status != 'pending':
            raise ValueError(f"Consent request is not pending (current status: {consent_request.status}). Cannot change decision.")

        if decision not in ['approved', 'denied']:
            raise ValueError("Decision must be 'approved' or 'denied'.")

        consent_request.status = decision
        consent_request.decider_user_id = decider_user_id
        from datetime import datetime, timezone # Ensure datetime is available
        consent_request.decision_timestamp = datetime.now(timezone.utc)

        if decision == 'approved':
            if conditions:
                expires_at_str = conditions.get('grant_expires_at')
                if expires_at_str:
                    try:
                        # Assuming ISO format string from client e.g. "YYYY-MM-DDTHH:MM:SSZ"
                        # For simplicity, direct conversion. Robust parsing might be needed.
                        consent_request.grant_expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
                    except ValueError:
                        raise ValueError("Invalid format for grant_expires_at. Use ISO format (e.g., YYYY-MM-DDTHH:MM:SSZ).")

                count_total = conditions.get('grant_access_count_total')
                if count_total is not None:
                    try:
                        count_total = int(count_total)
                        if count_total <= 0:
                            raise ValueError("grant_access_count_total must be a positive integer if provided.")
                        consent_request.grant_access_count_total = count_total
                        consent_request.grant_access_count_remaining = count_total # Initialize remaining
                    except ValueError:
                         raise ValueError("grant_access_count_total must be a positive integer.")
        else: # Denied
            consent_request.grant_expires_at = None
            consent_request.grant_access_count_total = None
            consent_request.grant_access_count_remaining = None
            # Could add a denial_reason field if needed

        try:
            db.session.commit()
            # Here, potentially trigger a notification to the requester
            return consent_request
        except Exception as e:
            db.session.rollback()
            # Log e
            raise RuntimeError(f"An unexpected error occurred while updating the consent request: {str(e)}")

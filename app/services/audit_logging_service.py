from app import db
from app.models import AuditLog # Assuming AuditLog model is defined
from datetime import datetime, timezone
import json # For serializing details if they are complex

class AuditLoggingService:
    @staticmethod
    def log_event(action: str, acting_user_id: int = None,
                  target_document_id: int = None, target_field_name: str = None,
                  target_user_id: int = None, consent_request_id: int = None,
                  status_outcome: str = None, details: dict = None):
        """
        Logs an audit event.
        - action: A string describing the action (e.g., "USER_LOGIN", "DOC_UPLOAD").
        - acting_user_id: ID of the user performing the action.
        - target_document_id: ID of the document being affected.
        - target_field_name: Name of the specific field being affected.
        - target_user_id: ID of a user being targeted by the action (e.g., data subject).
        - consent_request_id: ID of the consent request involved.
        - status_outcome: 'SUCCESS', 'FAILURE', 'ATTEMPT', etc.
        - details: A dictionary of additional information, stored as JSON string.
        """

        details_str = None
        if details is not None:
            try:
                details_str = json.dumps(details)
            except TypeError:
                details_str = json.dumps(str(details)) # Fallback if details not directly serializable

        audit_entry = AuditLog(
            acting_user_id=acting_user_id,
            action=action,
            target_document_id=target_document_id,
            target_field_name=target_field_name,
            target_user_id=target_user_id,
            consent_request_id=consent_request_id,
            status_outcome=status_outcome,
            details=details_str,
            timestamp=datetime.now(timezone.utc) # Ensure timestamp is set
        )

        try:
            db.session.add(audit_entry)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # What to do if logging fails? Critical issue.
            # For now, print to server log. In production, might go to a separate logging system.
            print(f"CRITICAL: Failed to log audit event: {e}")
            print(f"Failed event details: action={action}, user={acting_user_id}, details={details_str}")
            # Optionally re-raise or handle based on policy

    # Example of specific logging methods if preferred over generic log_event
    # @staticmethod
    # def log_user_login_success(user_id, ip_address=None):
    #     details = {}
    #     if ip_address: details['ip_address'] = ip_address
    #     AuditLoggingService.log_event(
    #         action="USER_LOGIN_SUCCESS",
    #         acting_user_id=user_id,
    #         status_outcome="SUCCESS",
    #         details=details
    #     )

    # @staticmethod
    # def log_user_login_failure(username_attempted, ip_address=None, reason="Invalid credentials"):
    #     details = {"username_attempted": username_attempted, "reason": reason}
    #     if ip_address: details['ip_address'] = ip_address
    #     AuditLoggingService.log_event(
    #         action="USER_LOGIN_FAILURE",
    #         status_outcome="FAILURE",
    #         details=details
    #     )

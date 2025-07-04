from app import db
from app.models import DocumentType, User
from app.services.audit_logging_service import AuditLoggingService

class DocumentTypeService:
    @staticmethod
    def create(data, owner_user_id):
        name = data.get('name')
        description = data.get('description')
        fields_definition = data.get('fields_definition')

        if not name or not fields_definition:
            raise ValueError("Name and fields_definition are required.")

        # Basic validation for fields_definition structure
        if not isinstance(fields_definition, list):
            raise ValueError("fields_definition must be a list.")
        for field_def in fields_definition:
            if not isinstance(field_def, dict) or \
               not all(key in field_def for key in ['name', 'label', 'type', 'access']):
                raise ValueError("Each field definition must be a dictionary with 'name', 'label', 'type', and 'access' keys.")
            if field_def['access'] not in ['open', 'controlled', 'closed']:
                raise ValueError(f"Invalid access type '{field_def['access']}' for field '{field_def['name']}'. Must be 'open', 'controlled', or 'closed'.")

        if DocumentType.query.filter_by(name=name).first():
            raise ValueError(f"DocumentType with name '{name}' already exists.")

        owner = User.query.get(owner_user_id)
        if not owner:
            raise ValueError("Owner user not found.")

        doc_type = DocumentType(
            name=name,
            description=description,
            fields_definition=fields_definition,
            owner_user_id=owner_user_id
        )
        db.session.add(doc_type)
        db.session.commit()
        AuditLoggingService.log_event(
            action="DOC_TYPE_CREATE_SUCCESS",
            acting_user_id=owner_user_id,
            status_outcome="SUCCESS",
            details={"document_type_id": doc_type.id, "name": doc_type.name}
        )
        return doc_type

    # Consider adding logging for failures in create method if specific exceptions are caught.
    # For example, if name uniqueness is violated:
    # except IntegrityError: # or specific check before commit
    #     db.session.rollback()
    #     AuditLoggingService.log_event(action="DOC_TYPE_CREATE_FAILURE", acting_user_id=owner_user_id, status_outcome="FAILURE", details={"name": name, "reason": "Name already exists"})
    #     raise ValueError("DocumentType name already exists")


    @staticmethod
    def get_by_id(dt_id):
        return DocumentType.query.get(dt_id)

    @staticmethod
    def get_all():
        return DocumentType.query.all()

    @staticmethod
    def get_by_name(name):
        return DocumentType.query.filter_by(name=name).first()

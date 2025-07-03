import uuid as uuid_generator
from app import db
from app.models import Document, DocumentType, User

class DocumentService:
    @staticmethod
    def create(data, uploader_user_id):
        name = data.get('name')
        document_type_id = data.get('document_type_id')
        data_subject_user_id = data.get('data_subject_user_id') # Optional
        content = data.get('content') # This is expected to be JSON

        if not name or not document_type_id or content is None: # content can be empty dict/list
            raise ValueError("Name, document_type_id, and content are required.")

        # Validate uploader
        uploader = User.query.get(uploader_user_id)
        if not uploader:
            raise ValueError("Uploader user not found.")

        # Validate document type
        doc_type = DocumentType.query.get(document_type_id)
        if not doc_type:
            raise ValueError(f"DocumentType with id '{document_type_id}' not found.")

        # Validate data_subject_user_id if provided
        if data_subject_user_id:
            data_subject = User.query.get(data_subject_user_id)
            if not data_subject:
                raise ValueError(f"Data subject user with id '{data_subject_user_id}' not found.")

        # Validate content against DocumentType.fields_definition
        if not isinstance(content, dict):
            raise ValueError("Content must be a JSON object (dictionary).")

        defined_fields = {field['name'] for field in doc_type.fields_definition}
        content_fields = set(content.keys())

        # Check for missing fields (all defined fields should ideally be present, or handled gracefully)
        # For now, let's be strict: all fields defined in type must be in content.
        # This could be relaxed later (e.g. allow optional fields).
        missing_fields = defined_fields - content_fields
        if missing_fields:
            raise ValueError(f"Missing fields in content: {', '.join(missing_fields)}. All fields defined in DocumentType must be provided.")

        # Check for extra fields (fields in content not defined in type)
        extra_fields = content_fields - defined_fields
        if extra_fields:
            raise ValueError(f"Extra fields in content not defined in DocumentType: {', '.join(extra_fields)}.")

        # Potential further validation: field types, specific value formats (not implemented for brevity)
        # For example, if fields_definition includes 'type': 'integer', check content[field_name] is int.

        new_doc = Document(
            uuid=str(uuid_generator.uuid4()),
            name=name,
            document_type_id=document_type_id,
            uploader_user_id=uploader_user_id,
            data_subject_user_id=data_subject_user_id,
            content=content,
            status='active' # Default status
        )
        db.session.add(new_doc)
        db.session.commit()
        return new_doc

    @staticmethod
    def get_by_uuid(doc_uuid):
        return Document.query.filter_by(uuid=doc_uuid).first()

    @staticmethod
    def get_by_id(doc_id): # Internal use potentially
        return Document.query.get(doc_id)

    @staticmethod
    def get_all_for_uploader(uploader_user_id, page=1, per_page=10):
        return Document.query.filter_by(uploader_user_id=uploader_user_id)\
            .order_by(Document.uploaded_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False) # error_out=False to return empty if page out of range

    @staticmethod
    def get_all_for_data_subject(data_subject_user_id, page=1, per_page=10):
         return Document.query.filter_by(data_subject_user_id=data_subject_user_id)\
            .order_by(Document.uploaded_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)

    # Add more query methods as needed, e.g., list all documents (admin) with pagination
    @staticmethod
    def get_all(page=1, per_page=10):
        return Document.query.order_by(Document.uploaded_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

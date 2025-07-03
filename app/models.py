from app import db # Import db instance from app package
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

# Flask-SQLAlchemy's db.JSON is generally preferred as it's dialect-aware.

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='student')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_email and self.email: # Check if email exists
            data['email'] = self.email
        return data


class DocumentType(db.Model):
    __tablename__ = 'document_types'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    fields_definition = db.Column(db.JSON, nullable=False) # Use db.JSON
    owner_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    owner = db.relationship('User', backref=db.backref('owned_document_types', lazy=True))

    def __repr__(self):
        return f'<DocumentType {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'fields_definition': self.fields_definition,
            'owner_user_id': self.owner_user_id
        }


class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    document_type_id = db.Column(db.Integer, db.ForeignKey('document_types.id'), nullable=False)
    uploader_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    data_subject_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    content = db.Column(db.JSON, nullable=False) # Use db.JSON
    status = db.Column(db.String(50), default='active', nullable=False)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    document_type = db.relationship('DocumentType', backref=db.backref('documents', lazy=True))
    uploader = db.relationship('User', foreign_keys=[uploader_user_id], backref=db.backref('uploaded_documents', lazy=True))
    data_subject = db.relationship('User', foreign_keys=[data_subject_user_id], backref=db.backref('subject_of_documents', lazy=True))

    def __repr__(self):
        return f'<Document {self.name} ({self.uuid})>'

    def to_dict(self, include_content=False):
        data = {
            'id': self.id,
            'uuid': self.uuid,
            'name': self.name,
            'document_type_id': self.document_type_id,
            'document_type_name': self.document_type.name if self.document_type else None,
            'uploader_user_id': self.uploader_user_id,
            'data_subject_user_id': self.data_subject_user_id,
            'status': self.status,
            'uploaded_at': self.uploaded_at.isoformat() if self.uploaded_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_content:
            data['content'] = self.content
        return data

    def to_dict_preview(self):
        return self.to_dict(include_content=False)


class ConsentRequest(db.Model):
    __tablename__ = 'consent_requests'
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    requester_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    owner_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    requested_fields = db.Column(db.JSON, nullable=False) # Use db.JSON
    purpose = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='pending')
    request_timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    decision_timestamp = db.Column(db.DateTime, nullable=True)
    decider_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    grant_expires_at = db.Column(db.DateTime, nullable=True)
    grant_access_count_total = db.Column(db.Integer, nullable=True)
    grant_access_count_remaining = db.Column(db.Integer, nullable=True)

    document = db.relationship('Document', backref=db.backref('consent_requests', lazy=True))
    requester = db.relationship('User', foreign_keys=[requester_user_id], backref=db.backref('consent_requests_made', lazy=True))
    owner = db.relationship('User', foreign_keys=[owner_user_id], backref=db.backref('consent_requests_to_decide', lazy=True))
    decider = db.relationship('User', foreign_keys=[decider_user_id], backref=db.backref('consent_requests_decided', lazy=True))

    def __repr__(self):
        return f'<ConsentRequest {self.id} for Doc {self.document_id} by User {self.requester_user_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'document_name': self.document.name if self.document else None,
            'requester_user_id': self.requester_user_id,
            'requester_username': self.requester.username if self.requester else None,
            'owner_user_id': self.owner_user_id,
            'owner_username': self.owner.username if self.owner else None,
            'requested_fields': self.requested_fields,
            'purpose': self.purpose,
            'status': self.status,
            'request_timestamp': self.request_timestamp.isoformat() if self.request_timestamp else None,
            'decision_timestamp': self.decision_timestamp.isoformat() if self.decision_timestamp else None,
            'decider_user_id': self.decider_user_id,
            'decider_username': self.decider.username if self.decider else None,
            'grant_expires_at': self.grant_expires_at.isoformat() if self.grant_expires_at else None,
            'grant_access_count_total': self.grant_access_count_total,
            'grant_access_count_remaining': self.grant_access_count_remaining,
        }


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id = db.Column(db.Integer, primary_key=True)
    acting_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    target_document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=True)
    target_field_name = db.Column(db.String(255), nullable=True)
    target_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    consent_request_id = db.Column(db.Integer, db.ForeignKey('consent_requests.id'), nullable=True)
    status_outcome = db.Column(db.String(50), nullable=True)
    details = db.Column(db.Text, nullable=True) # Can store JSON as string
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    acting_user = db.relationship('User', foreign_keys=[acting_user_id], backref=db.backref('audit_logs_performed', lazy=True))
    target_document = db.relationship('Document', foreign_keys=[target_document_id], backref=db.backref('audit_logs_related_to_doc', lazy=True))
    target_user_acted_on = db.relationship('User', foreign_keys=[target_user_id], backref=db.backref('audit_logs_targeting_user', lazy=True))
    consent_request_related = db.relationship('ConsentRequest', foreign_keys=[consent_request_id], backref=db.backref('audit_logs_related_to_req', lazy=True))

    def __repr__(self):
        return f'<AuditLog {self.id} - Action: {self.action} by User {self.acting_user_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'acting_user_id': self.acting_user_id,
            'acting_username': self.acting_user.username if self.acting_user and self.acting_user.username else 'System', # Added check for self.acting_user.username
            'action': self.action,
            'target_document_id': self.target_document_id,
            'target_field_name': self.target_field_name,
            'target_user_id': self.target_user_id,
            'consent_request_id': self.consent_request_id,
            'status_outcome': self.status_outcome,
            'details': self.details,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }

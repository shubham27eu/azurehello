from flask import Blueprint, request, jsonify
from app.services.document_type_service import DocumentTypeService
from app.utils.decorators import role_required # Import the decorator
from flask_jwt_extended import jwt_required, get_jwt_identity

dt_bp = Blueprint('document_type', __name__)

@dt_bp.route('', methods=['POST'])
@jwt_required()
@role_required('professor', 'admin') # Apply role check
def create_document_type_route(): # Renamed to avoid conflict with service method
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body must be JSON"}), 400

    current_user_id = get_jwt_identity() # This is a string, convert if necessary for service
                                         # Our AuthService.get_user_by_id expects int.
                                         # User.id is int. JWT sub is str(user.id).
                                         # owner_user_id in DocumentType is int.

    try:
        # Ensure current_user_id is an integer for the service layer
        owner_id = int(current_user_id)
        doc_type = DocumentTypeService.create(data, owner_user_id=owner_id)
        # Assuming a to_dict() method in the DocumentType model
        return jsonify(doc_type.to_dict()), 201
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        # Log the exception e for debugging
        return jsonify({"message": "Failed to create document type due to an unexpected error."}), 500

@dt_bp.route('', methods=['GET'])
@jwt_required() # All users can list document types for now
def list_document_types_route(): # Renamed
    try:
        doc_types = DocumentTypeService.get_all()
        return jsonify([dt.to_dict() for dt in doc_types]), 200
    except Exception as e:
        # Log the exception e
        return jsonify({"message": "Failed to retrieve document types."}), 500

@dt_bp.route('/<int:dt_id>', methods=['GET'])
@jwt_required()
def get_document_type_route(dt_id): # Renamed
    try:
        doc_type = DocumentTypeService.get_by_id(dt_id)
        if doc_type:
            return jsonify(doc_type.to_dict()), 200
        return jsonify({"message": "Document type not found"}), 404
    except Exception as e:
        # Log the exception e
        return jsonify({"message": "Failed to retrieve document type."}), 500

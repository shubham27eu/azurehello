from flask import Blueprint, request, jsonify
# from app.services.document_type_service import DocumentTypeService (to be created)
# from flask_jwt_extended import jwt_required, get_jwt_identity

dt_bp = Blueprint('document_type', __name__)

@dt_bp.route('', methods=['POST'])
# @jwt_required()
# @role_required('professor', 'admin') # Placeholder for role check
def create_document_type():
    # data = request.get_json()
    # current_user_id = get_jwt_identity()
    # doc_type = DocumentTypeService.create(data, owner_user_id=current_user_id)
    # if doc_type:
    #     return jsonify(doc_type.to_dict()), 201 # Assuming a to_dict() method in model
    # return jsonify({"message": "Failed to create document type"}), 400
    return jsonify({"message": "Document Type creation placeholder"}), 201

@dt_bp.route('', methods=['GET'])
# @jwt_required()
def list_document_types():
    # doc_types = DocumentTypeService.get_all()
    # return jsonify([dt.to_dict() for dt in doc_types]), 200
    return jsonify([{"id": 1, "name": "Sample Document Type"}]), 200

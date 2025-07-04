from flask import Blueprint, request, jsonify
from app.services.document_service import DocumentService
# from app.services.data_access_control_service import DataAccessControlService # Will be used later
from app.utils.decorators import role_required
from flask_jwt_extended import jwt_required, get_jwt_identity

doc_bp = Blueprint('document', __name__)

@doc_bp.route('', methods=['POST'])
@jwt_required()
@role_required('professor', 'admin') # Or any role that can upload documents
def ingest_document_route(): # Renamed
    data = request.get_json()
    if not data:
        return jsonify({"message": "Request body must be JSON"}), 400

    uploader_user_id_str = get_jwt_identity()

    try:
        uploader_user_id = int(uploader_user_id_str)
        document = DocumentService.create(data, uploader_user_id=uploader_user_id)
        # Document model should have a to_dict() method
        return jsonify(document.to_dict(include_content=False)), 201 # Do not include full content in response by default
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except Exception as e:
        # Log e
        return jsonify({"message": "Failed to ingest document due to an unexpected error."}), 500

@doc_bp.route('/<string:document_uuid>', methods=['GET'])
@jwt_required() # Access control for who can see details will be trickier
                # Might depend on ownership, consent, or role. For now, any auth user.
def get_document_details_route(document_uuid): # Renamed
    # current_user_id = get_jwt_identity() # For future access control logic
    try:
        document = DocumentService.get_by_uuid(document_uuid)
        if document:
            # Here, we might need to filter what is returned based on user's access rights
            # For now, using the preview method from the model
            return jsonify(document.to_dict_preview()), 200
        return jsonify({"message": "Document not found"}), 404
    except Exception as e:
        # Log e
        return jsonify({"message": "Failed to retrieve document details."}), 500

# Endpoint for listing documents - useful for dashboards
@doc_bp.route('', methods=['GET'])
@jwt_required()
def list_documents_route():
    current_user_id_str = get_jwt_identity()
    user_id = int(current_user_id_str)
    # For simplicity, let's return documents uploaded by the user.
    # Could be extended with query params for other views (e.g., documents subject to user)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    try:
        # Example: Get documents uploaded by the current user
        # paginated_docs = DocumentService.get_all_for_uploader(user_id, page, per_page)

        # Or, for a general list (admin view, or if all docs are somewhat public)
        # For now, let's make it general for testing, but this needs role/permission checks
        paginated_docs = DocumentService.get_all(page, per_page)

        return jsonify({
            "documents": [doc.to_dict_preview() for doc in paginated_docs.items],
            "total": paginated_docs.total,
            "pages": paginated_docs.pages,
            "current_page": paginated_docs.page
        }), 200
    except Exception as e:
        # Log e
        return jsonify({"message": f"Failed to retrieve documents: {str(e)}"}), 500


@doc_bp.route('/<string:document_uuid>/fields/<string:field_name>', methods=['GET'])
@jwt_required()
def get_document_field_value_route(document_uuid, field_name): # Renamed
    current_user_id_str = get_jwt_identity()
    # from app.services.data_access_control_service import DataAccessControlService # Import when ready
    try:
        # value = DataAccessControlService.get_field_value(
        #     document_uuid=document_uuid,
        #     field_name=field_name,
        #     requester_user_id=int(current_user_id_str)
        # )
        # return jsonify({"document_uuid": document_uuid, "field_name": field_name, "value": value}), 200
        return jsonify({"message": f"Data Access Control Service not yet implemented for field {field_name}"}), 501 # 501 Not Implemented
    except PermissionError as e: # Custom PermissionError from DataAccessControlService
        return jsonify({"error": "Access Denied", "reason": str(e)}), 403
    except FileNotFoundError as e: # Custom DocumentNotFound error
        return jsonify({"error": "Not Found", "reason": str(e)}), 404
    except Exception as e:
        # Log e
        return jsonify({"error": "Server Error", "reason": str(e)}), 500


@doc_bp.route('/<string:document_uuid>/access-requests', methods=['POST'])
@jwt_required()
def create_access_request_route(document_uuid): # Renamed
    current_user_id_str = get_jwt_identity() # This is the requester
    data = request.get_json()
    if not data or not data.get('requested_fields') or not data.get('purpose'):
        return jsonify({"message": "requested_fields and purpose are required."}), 400

    requested_fields = data.get('requested_fields')
    purpose = data.get('purpose')

    from app.services.consent_service import ConsentService # Import the service
    try:
        consent_req = ConsentService.create_request(
           requester_user_id=int(current_user_id_str),
           document_uuid=document_uuid,
           requested_fields=requested_fields,
           purpose=purpose
        )
        # Assuming ConsentRequest model has a to_dict() method
        return jsonify(consent_req.to_dict()), 202 # 202 Accepted
    except ValueError as e: # Raised by ConsentService for validation errors
        return jsonify({"message": str(e)}), 400
    except PermissionError as e: # Raised if trying to request 'closed' fields
        return jsonify({"message": str(e)}), 403
    except Exception as e: # Catch other unexpected errors
        # Log e for server-side review
        return jsonify({"message": f"Failed to create access request due to an unexpected server error."}), 500

from flask import Blueprint, request, jsonify
# from app.services.document_service import DocumentService (to be created)
# from app.services.data_access_control_service import DataAccessControlService (to be created)
# from flask_jwt_extended import jwt_required, get_jwt_identity

doc_bp = Blueprint('document', __name__)

@doc_bp.route('', methods=['POST'])
# @jwt_required()
# @role_required('professor', 'admin') # Placeholder for role check
def ingest_document():
    # data = request.get_json()
    # uploader_user_id = get_jwt_identity()
    # document = DocumentService.create(data, uploader_user_id=uploader_user_id)
    # if document:
    #     return jsonify(document.to_dict()), 201
    # return jsonify({"message": "Failed to ingest document"}), 400
    return jsonify({"message": "Document ingestion placeholder"}), 201

@doc_bp.route('/<string:document_uuid>', methods=['GET'])
# @jwt_required()
def get_document_details(document_uuid):
    # document = DocumentService.get_by_uuid(document_uuid)
    # if document:
    #     # Further checks might be needed here based on who can see what
    #     return jsonify(document.to_dict_preview()), 200 # A preview version
    # return jsonify({"message": "Document not found"}), 404
    return jsonify({"message": f"Document details placeholder for {document_uuid}"}), 200

@doc_bp.route('/<string:document_uuid>/fields/<string:field_name>', methods=['GET'])
# @jwt_required()
def get_document_field_value(document_uuid, field_name):
    # current_user_id = get_jwt_identity()
    # try:
    #     value = DataAccessControlService.get_field_value(
    #         document_uuid=document_uuid,
    #         field_name=field_name,
    #         requester_user_id=current_user_id
    #     )
    #     return jsonify({"document_uuid": document_uuid, "field_name": field_name, "value": value}), 200
    # except PermissionError as e:
    #     return jsonify({"error": "Access Denied", "reason": str(e)}), 403
    # except FileNotFoundError as e: # Or a custom DocumentNotFound error
    #     return jsonify({"error": "Not Found", "reason": str(e)}), 404
    # except Exception as e: # Catch all for other errors during processing
    #     return jsonify({"error": "Server Error", "reason": str(e)}), 500
    return jsonify({"message": f"Field value placeholder for {document_uuid}, field {field_name}"}), 200

@doc_bp.route('/<string:document_uuid>/access-requests', methods=['POST'])
# @jwt_required()
def create_access_request(document_uuid):
    # current_user_id = get_jwt_identity() # This is the requester
    # data = request.get_json()
    # requested_fields = data.get('requested_fields')
    # purpose = data.get('purpose')
    # from app.services.consent_service import ConsentService # Import here or at top
    # consent_req = ConsentService.create_request(
    #    requester_user_id=current_user_id,
    #    document_uuid=document_uuid,
    #    requested_fields=requested_fields,
    #    purpose=purpose
    # )
    # if consent_req:
    #    return jsonify(consent_req.to_dict()), 202 # 202 Accepted
    # return jsonify({"message": "Failed to create access request"}), 400
    return jsonify({"message": f"Access request creation placeholder for doc {document_uuid}"}), 202

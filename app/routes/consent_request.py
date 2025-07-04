from flask import Blueprint, request, jsonify
from app.services.consent_service import ConsentService
from flask_jwt_extended import jwt_required, get_jwt_identity

cr_bp = Blueprint('consent_request_bp', __name__) # Renamed blueprint to avoid conflict if service is named ConsentRequest

@cr_bp.route('/<int:request_id>/decide', methods=['POST'])
@jwt_required()
def decide_consent_request_route(request_id): # Renamed
    data = request.get_json()
    if not data or not data.get('decision'):
        return jsonify({"message": "Decision ('approved' or 'denied') is required."}), 400

    decider_user_id_str = get_jwt_identity()
    decision = data.get('decision')
    conditions = {
        "grant_expires_at": data.get("grant_expires_at"), # Expects ISO string e.g. "YYYY-MM-DDTHH:MM:SSZ"
        "grant_access_count_total": data.get("grant_access_count_total")
    }

    try:
        consent_request = ConsentService.decide_request(
            request_id=request_id,
            decider_user_id=int(decider_user_id_str),
            decision=decision,
            conditions=conditions
        )
        return jsonify(consent_request.to_dict()), 200
    except ValueError as e: # Covers issues from service validation (e.g. not found, not pending)
        return jsonify({"message": str(e)}), 400 # Or 404 if appropriate
    except PermissionError as e: # If decider is not the owner
        return jsonify({"message": str(e)}), 403
    except Exception as e:
        # Log e for server-side review
        return jsonify({"message": "Failed to process consent decision due to an unexpected server error."}), 500

@cr_bp.route('', methods=['GET'])
@jwt_required()
def list_consent_requests_route(): # Renamed
    owner_user_id_str = get_jwt_identity() # Assuming the logged-in user is the owner listing their requests
    status = request.args.get('status') # Optional filter by status e.g. 'pending'
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    try:
        paginated_requests = ConsentService.get_requests_for_owner(
            owner_user_id=int(owner_user_id_str),
            status=status,
            page=page,
            per_page=per_page
        )
        return jsonify({
            "consent_requests": [req.to_dict() for req in paginated_requests.items],
            "total": paginated_requests.total,
            "pages": paginated_requests.pages,
            "current_page": paginated_requests.page
        }), 200
    except Exception as e:
        # Log e
        return jsonify({"message": "Failed to retrieve consent requests."}), 500

# Note: The route for *creating* a consent request (POST /api/documents/{document_uuid}/access-requests)
# is already implemented in app/routes/document.py and uses ConsentService.create_request.
# This blueprint (cr_bp) handles operations on existing consent requests, like listing for an owner or deciding.

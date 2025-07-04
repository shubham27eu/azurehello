#!/bin/bash

# Script to set up data and test data access
# Assumes Flask server (python run.py) is running on http://127.0.0.1:5000
# Assumes database has been freshly migrated (flask db upgrade) and users seeded (python seed_db.py)

echo "--- Logging in users ---"
PROF_TOKEN=$(curl -s -X POST -H "Content-Type: application/json" -d '{"username":"prof_smith", "password":"password123"}' http://127.0.0.1:5000/api/auth/login | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', 'ERROR_PROF_TOKEN'))")
ALICE_TOKEN=$(curl -s -X POST -H "Content-Type: application/json" -d '{"username":"alice_wonder", "password":"password123"}' http://127.0.0.1:5000/api/auth/login | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', 'ERROR_ALICE_TOKEN'))")
BOB_TOKEN=$(curl -s -X POST -H "Content-Type: application/json" -d '{"username":"bob_builder", "password":"password123"}' http://127.0.0.1:5000/api/auth/login | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', 'ERROR_BOB_TOKEN'))")

if [[ "$PROF_TOKEN" == ERROR* || "$ALICE_TOKEN" == ERROR* || "$BOB_TOKEN" == ERROR* ]]; then
    echo "Error: Failed to get one or more tokens. Exiting."
    echo "PROF_TOKEN: $PROF_TOKEN"
    echo "ALICE_TOKEN: $ALICE_TOKEN"
    echo "BOB_TOKEN: $BOB_TOKEN"
    exit 1
fi

echo "Prof Smith token (start): ${PROF_TOKEN:0:15}..."
echo "Alice Wonder token (start): ${ALICE_TOKEN:0:15}..."
echo "Bob Builder token (start): ${BOB_TOKEN:0:15}..."
echo ""

echo "--- Professor Smith creating Document Type 'GradeSheet' ---"
DOC_TYPE_RESPONSE=$(curl -s -w "\\nHTTP_STATUS_CODE:%{http_code}\\n" -X POST \
    -H "Authorization: Bearer $PROF_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
          "name": "GradeSheet",
          "description": "Official student grade report.",
          "fields_definition": [
            {"name": "StudentName", "type": "string", "label": "Student Name", "access": "open"},
            {"name": "StudentID", "type": "string", "label": "Student ID", "access": "open"},
            {"name": "CourseName", "type": "string", "label": "Course Name", "access": "open"},
            {"name": "FinalGrade", "type": "string", "label": "Final Grade", "access": "controlled"},
            {"name": "InstructorComments", "type": "text", "label": "Instructor Comments", "access": "controlled"}
          ]
        }' \
    http://127.0.0.1:5000/api/document-types)

echo "$DOC_TYPE_RESPONSE"
# Extract DocType ID (assuming it's 1 for a fresh DB)
DOC_TYPE_ID=1
echo "Assuming Document Type ID for 'GradeSheet' is $DOC_TYPE_ID"
echo ""

echo "--- Professor Smith ingesting Alice_s CS101 Grades ---"
# Assumes Alice user_id is 2
ALICE_USER_ID=2
DOC_INGEST_RESPONSE=$(curl -s -w "\\nHTTP_STATUS_CODE:%{http_code}\\n" -X POST \
    -H "Authorization: Bearer $PROF_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
          \"name\": \"Alice CS101 Grades\",
          \"document_type_id\": $DOC_TYPE_ID,
          \"data_subject_user_id\": $ALICE_USER_ID,
          \"content\": {
            \"StudentName\": \"Alice Wonderland\",
            \"StudentID\": \"S002\",
            \"CourseName\": \"CS101 Programming\",
            \"FinalGrade\": \"A\",
            \"InstructorComments\": \"Excellent work, Alice!\"
          }
        }" \
    http://127.0.0.1:5000/api/documents)

echo "$DOC_INGEST_RESPONSE"
ALICE_DOC_UUID=$(echo "$DOC_INGEST_RESPONSE" | grep -oP '(?<=\"uuid\": \")[^\"]*' | head -n 1)

if [ -z "$ALICE_DOC_UUID" ]; then
    echo "Error: Failed to get document UUID for Alice_s document. Exiting."
    exit 1
fi
echo "Alice_s Document UUID: $ALICE_DOC_UUID"
echo ""

echo "--- Bob Builder requesting access to FinalGrade ---"
ACCESS_REQUEST_RESPONSE=$(curl -s -w "\\nHTTP_STATUS_CODE:%{http_code}\\n" -X POST \
    -H "Authorization: Bearer $BOB_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
          "requested_fields": ["FinalGrade"],
          "purpose": "Bob is curious about Alice_s CS101 grade."
        }' \
    http://127.0.0.1:5000/api/documents/$ALICE_DOC_UUID/access-requests)

echo "$ACCESS_REQUEST_RESPONSE"
CONSENT_REQUEST_ID=$(echo "$ACCESS_REQUEST_RESPONSE" | grep -oP '(?<=\"id\": )[0-9]+' | head -n 1)

if [ -z "$CONSENT_REQUEST_ID" ]; then
    echo "Error: Failed to get Consent Request ID. Exiting."
    exit 1
fi
echo "Consent Request ID: $CONSENT_REQUEST_ID"
echo ""

echo "--- Alice Wonder approving Bob_s request ---"
# EXPIRY_TIME needs to be a valid future ISO 8601 timestamp
# For simplicity in a script, using a fixed far future date.
# In a real test, generate this dynamically or ensure it's valid.
EXPIRY_TIME="2025-12-31T23:59:59Z"
APPROVAL_RESPONSE=$(curl -s -w "\\nHTTP_STATUS_CODE:%{http_code}\\n" -X POST \
    -H "Authorization: Bearer $ALICE_TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
          \"decision\": \"approved\",
          \"grant_expires_at\": \"$EXPIRY_TIME\",
          \"grant_access_count_total\": 1
        }" \
    http://127.0.0.1:5000/api/consent-requests/$CONSENT_REQUEST_ID/decide)

echo "$APPROVAL_RESPONSE"
echo ""

echo "--- CRITICAL TEST: Bob Builder attempting to access FinalGrade ---"
echo "Please observe the Flask server logs (where python run.py is running) for this request."
echo "The server logs for this next command are what Jules needs."
# Using -v to see curl_s own verbose output for this critical request
curl -v -X GET \
    -H "Authorization: Bearer $BOB_TOKEN" \
    http://127.0.0.1:5000/api/documents/$ALICE_DOC_UUID/fields/FinalGrade

echo ""
echo "--- Test script finished. Please provide server logs for the 'CRITICAL TEST' step. ---"

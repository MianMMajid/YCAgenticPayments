"""
Mock x402 Payment Services for Demo

These services simulate real third-party APIs that require payment before providing services.
They return 402 Payment Required initially, then accept payment signatures and return results.
"""
from flask import Flask, request, jsonify
import hashlib
import time
from datetime import datetime, timedelta

app = Flask(__name__)

# In-memory storage for payment tracking
payments = {}

# Service configurations
SERVICES = {
    "/landamerica/title-search": {
        "name": "LandAmerica Title Search",
        "amount": 1200.00,
        "description": "Title search and verification service"
    },
    "/amerispec/inspection": {
        "name": "AmeriSpec Inspection",
        "amount": 500.00,
        "description": "Property inspection service"
    },
    "/corelogic/valuation": {
        "name": "CoreLogic Valuation",
        "amount": 400.00,
        "description": "Property appraisal and valuation service"
    },
    "/fanniemae/verify": {
        "name": "Fannie Mae Verification",
        "amount": 0.00,  # No payment required for verification
        "description": "Loan verification service"
    }
}


@app.route("/landamerica/title-search", methods=["GET", "POST"])
def title_search():
    """Title search service - returns 402, accepts payment."""
    # Handle GET request - return 402 Payment Required
    if request.method == "GET":
        challenge = f"landamerica_title_{int(time.time())}"
        return jsonify({
            "error": "Payment Required",
            "message": "This service requires payment before execution",
            "amount": 1200.00,
            "currency": "USD",
            "challenge": challenge,
            "service": "LandAmerica",
            "payment_endpoint": "/landamerica/title-search"
        }), 402
    
    # Handle POST request - check for payment
    data = request.get_json() or {}
    property_id = data.get("property_id", "unknown")
    
    # Check for X-PAYMENT header (x402 protocol)
    payment_signature = request.headers.get("X-PAYMENT") or data.get("payment_signature")
    payment_tx_hash = payment_signature or data.get("payment_tx_hash")
    
    if not payment_signature:
        # Return 402 Payment Required
        challenge = f"landamerica_title_{int(time.time())}"
        return jsonify({
            "error": "Payment Required",
            "message": "This service requires payment before execution",
            "amount": 1200.00,
            "currency": "USD",
            "challenge": challenge,
            "service": "LandAmerica",
            "payment_endpoint": "/landamerica/title-search"
        }), 402
    
    # Verify payment (in real system, this would verify blockchain transaction)
    payment_id = f"title-{property_id}-{int(time.time())}"
    payments[payment_id] = {
        "service": "title-search",
        "property_id": property_id,
        "amount": 1200.00,
        "signature": payment_signature,
        "tx_hash": payment_tx_hash,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Return successful title search result
    return jsonify({
        "success": True,
        "service": "LandAmerica Title Search",
        "property_id": property_id,
        "payment_id": payment_id,
        "payment_tx": payment_tx_hash,
        "result": {
            "title_status": "CLEAR",
            "current_owner": "John Smith",
            "chain_of_title": [
                {"owner": "John Smith", "date": "2020-01-15", "deed_type": "Warranty Deed"},
                {"owner": "Jane Doe", "date": "2015-03-20", "deed_type": "Warranty Deed"}
            ],
            "liens_and_encumbrances": [],
            "has_issues": False,
            "report_date": datetime.utcnow().isoformat()
        },
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@app.route("/amerispec/inspection", methods=["GET", "POST"])
def inspection():
    """Inspection service - returns 402, accepts payment."""
    # Handle GET request - return 402 Payment Required
    if request.method == "GET":
        challenge = f"amerispec_inspection_{int(time.time())}"
        return jsonify({
            "error": "Payment Required",
            "message": "This service requires payment before execution",
            "amount": 500.00,
            "currency": "USD",
            "challenge": challenge,
            "service": "AmeriSpec",
            "payment_endpoint": "/amerispec/inspection"
        }), 402
    
    # Handle POST request - check for payment
    data = request.get_json() or {}
    property_id = data.get("property_id", "unknown")
    
    # Check for X-PAYMENT header (x402 protocol)
    payment_signature = request.headers.get("X-PAYMENT") or data.get("payment_signature")
    payment_tx_hash = payment_signature or data.get("payment_tx_hash")
    
    if not payment_signature:
        # Return 402 Payment Required
        challenge = f"amerispec_inspection_{int(time.time())}"
        return jsonify({
            "error": "Payment Required",
            "message": "This service requires payment before execution",
            "amount": 500.00,
            "currency": "USD",
            "challenge": challenge,
            "service": "AmeriSpec",
            "payment_endpoint": "/amerispec/inspection"
        }), 402
    
    # Verify payment
    payment_id = f"inspection-{property_id}-{int(time.time())}"
    payments[payment_id] = {
        "service": "inspection",
        "property_id": property_id,
        "amount": 500.00,
        "signature": payment_signature,
        "tx_hash": payment_tx_hash,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Schedule inspection for tomorrow
    inspection_date = (datetime.utcnow() + timedelta(days=1)).isoformat()
    
    # Return successful inspection scheduling
    return jsonify({
        "success": True,
        "service": "AmeriSpec Inspection",
        "property_id": property_id,
        "payment_id": payment_id,
        "payment_tx": payment_tx_hash,
        "result": {
            "scheduled_date": inspection_date,
            "inspector_name": "Michael Johnson",
            "inspector_license": "CA-LIC-12345",
            "status": "SCHEDULED",
            "estimated_completion": (datetime.utcnow() + timedelta(days=2)).isoformat()
        },
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@app.route("/corelogic/valuation", methods=["GET", "POST"])
def valuation():
    """Appraisal service - returns 402, accepts payment."""
    # Handle GET request - return 402 Payment Required
    if request.method == "GET":
        challenge = f"corelogic_valuation_{int(time.time())}"
        return jsonify({
            "error": "Payment Required",
            "message": "This service requires payment before execution",
            "amount": 400.00,
            "currency": "USD",
            "challenge": challenge,
            "service": "CoreLogic",
            "payment_endpoint": "/corelogic/valuation"
        }), 402
    
    # Handle POST request - check for payment
    data = request.get_json() or {}
    property_id = data.get("property_id", "unknown")
    purchase_price = data.get("purchase_price", 850000)
    
    # Check for X-PAYMENT header (x402 protocol)
    payment_signature = request.headers.get("X-PAYMENT") or data.get("payment_signature")
    payment_tx_hash = payment_signature or data.get("payment_tx_hash")
    
    if not payment_signature:
        # Return 402 Payment Required
        challenge = f"corelogic_valuation_{int(time.time())}"
        return jsonify({
            "error": "Payment Required",
            "message": "This service requires payment before execution",
            "amount": 400.00,
            "currency": "USD",
            "challenge": challenge,
            "service": "CoreLogic",
            "payment_endpoint": "/corelogic/valuation"
        }), 402
    
    # Verify payment
    payment_id = f"valuation-{property_id}-{int(time.time())}"
    payments[payment_id] = {
        "service": "valuation",
        "property_id": property_id,
        "amount": 400.00,
        "signature": payment_signature,
        "tx_hash": payment_tx_hash,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Calculate appraised value (slightly above purchase price for demo)
    appraised_value = float(purchase_price) * 1.02
    
    # Return successful appraisal
    return jsonify({
        "success": True,
        "service": "CoreLogic Valuation",
        "property_id": property_id,
        "payment_id": payment_id,
        "payment_tx": payment_tx_hash,
        "result": {
            "appraised_value": appraised_value,
            "purchase_price": purchase_price,
            "appraisal_date": datetime.utcnow().isoformat(),
            "appraiser_name": "Sarah Williams",
            "appraiser_license": "CA-APP-67890",
            "appraisal_method": "sales_comparison",
            "status": "APPROVED"
        },
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@app.route("/fanniemae/verify", methods=["GET", "POST"])
def verify():
    """Loan verification service - returns 402 (but no payment needed)."""
    # Handle GET request - return 402 Payment Required
    if request.method == "GET":
        challenge = f"fanniemae_verify_{int(time.time())}"
        return jsonify({
            "error": "Payment Required",
            "message": "This service requires payment signature before execution",
            "amount": 0.00,
            "currency": "USD",
            "challenge": challenge,
            "service": "Fannie Mae",
            "payment_endpoint": "/fanniemae/verify",
            "note": "No payment amount required, but signature verification needed"
        }), 402
    
    # Handle POST request - check for payment
    data = request.get_json() or {}
    property_id = data.get("property_id", "unknown")
    loan_amount = data.get("loan_amount", 0)
    
    # Check for X-PAYMENT header (x402 protocol)
    payment_signature = request.headers.get("X-PAYMENT") or data.get("payment_signature")
    payment_tx_hash = payment_signature or data.get("payment_tx_hash")
    
    if not payment_signature:
        # Return 402 Payment Required (even though it's free, signature is required)
        challenge = f"fanniemae_verify_{int(time.time())}"
        return jsonify({
            "error": "Payment Required",
            "message": "This service requires payment signature before execution",
            "amount": 0.00,
            "currency": "USD",
            "challenge": challenge,
            "service": "Fannie Mae",
            "payment_endpoint": "/fanniemae/verify",
            "note": "No payment amount required, but signature verification needed"
        }), 402
    
    # Verify payment (even though amount is 0)
    payment_id = f"verify-{property_id}-{int(time.time())}"
    payments[payment_id] = {
        "service": "verify",
        "property_id": property_id,
        "amount": 0.00,
        "signature": payment_signature,
        "tx_hash": payment_tx_hash,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Return successful loan verification
    return jsonify({
        "success": True,
        "service": "Fannie Mae Verification",
        "property_id": property_id,
        "payment_id": payment_id,
        "payment_tx": payment_tx_hash,
        "result": {
            "loan_approved": True,
            "loan_amount": loan_amount,
            "lender_name": "Fannie Mae",
            "loan_officer_name": "Robert Chen",
            "loan_officer_contact": "r.chen@fanniemae.com",
            "loan_type": "conventional",
            "interest_rate": 6.5,
            "loan_term_years": 30,
            "underwriting_complete": True,
            "status": "PRE-APPROVED"
        },
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "services": list(SERVICES.keys()),
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@app.route("/payments", methods=["GET"])
def list_payments():
    """List all payments (for debugging)."""
    return jsonify({
        "payments": payments,
        "count": len(payments)
    }), 200


if __name__ == "__main__":
    print("=" * 60)
    print("Mock x402 Payment Services")
    print("=" * 60)
    print("\nAvailable Services:")
    for endpoint, config in SERVICES.items():
        print(f"  {endpoint:30} ${config['amount']:>8.2f} - {config['name']}")
    print("\nStarting server on http://localhost:5001")
    print("=" * 60)
    app.run(host="0.0.0.0", port=5001, debug=True)


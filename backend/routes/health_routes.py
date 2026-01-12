from flask import Blueprint, jsonify
from backend.utils.decorators import add_timing, handle_exceptions

# Create blueprint
health_bp = Blueprint('health', __name__)

#Route 1: Home page
@health_bp.route("/")
@add_timing
@handle_exceptions
def hello():
    return "Hello from Slovenia Air Quality, šaša"


#Route 2: Health check
@health_bp.route("/api/health")
@add_timing
@handle_exceptions
def health():
    return jsonify({
        "status": "OK",
        "message": "Slovenia Air Quality Monitoring",
        "version": "1.0",
        "utf-8 test": "Čevapčiči, šampinjoni, žličnik"
    })
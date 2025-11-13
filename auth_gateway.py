from flask import request, jsonify, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

def init_auth_gateway(app):
	"""
	Register a before_request handler that:
	- Allows unauthenticated access to /api/auth/* and /health
	- For all other requests attempts to verify JWT using Flask-JWT-Extended
	- On success sets g.current_user to the identity; on failure returns 401
	"""
	@app.before_request
	def _auth_gateway():
		# Allow auth endpoints and health check to pass through
		path = request.path or ""
		if path.startswith("/api/auth") or path == "/health":
			return None

		# Optionally allow OPTIONS (CORS preflight)
		if request.method == "OPTIONS":
			return None
		if path.startswith("/openapi.yaml") or path.startswith("/api/docs"):
			return None
		# Try to verify JWT; verify_jwt_in_request will raise on failure
		try:
			verify_jwt_in_request()
			g.current_user = get_jwt_identity()
			return None
		except Exception as exc:
			# Keep response minimal and consistent
			return jsonify({"error": "Unauthorized", "message": str(exc)}), 401

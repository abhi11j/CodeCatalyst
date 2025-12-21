"""
Flask REST API for GitHub Scanner

This module provides a REST API interface for the GitHub Scanner,
allowing UI applications to request repository analysis and receive
improvement suggestions via HTTP endpoints.

Endpoints:
    POST /api/scan - Analyze a repository and get suggestions
    GET  /api/health - Health check
"""

import os
from flask import Flask, request, jsonify
from flask_cors import CORS

from Scanner.Utility.env import load_env_file
from Scanner.Utility.auth import get_github_token
from Scanner.Exception.GitHubError import GitHubError
from Scanner.Business.ScanBusiness import ScanBusiness
from Scanner.Routes.validators import validate_scan_payload, map_suggestions

import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

"""Create and configure the Flask application.    
    Args:
        config: Optional configuration dictionary        
    Returns:
        Flask application instance
"""
def CreateApp(config=None):
    
    app = Flask(__name__)    
    # Load environment variables from .env
    load_env_file()
    # Enable CORS for all routes
    CORS(app)
    # Register blueprints and routes
    RegisterRoutes(app)    
    return app

"""Register all API routes.    
    Args:
        app: Flask application instance
"""
def RegisterRoutes(app: Flask) -> None:    
    
    @app.route("/")
    def index():
        return "App is running!"

    """Health check endpoint.        
        Returns:
            JSON response with status
    """
    @app.route('/api/health-check', methods=['GET'])
    def HealthCheck():        
        return jsonify({
            "status": "healthy",
            "message": "GitHub Scanner API is running"
        }), 200
    
    """Scan a repository and get improvement suggestions.        
        Request JSON body:
        {
            "target": "owner/repo",           # Required
            "max_results": 6,                 # Optional, default 6
            "search_type": 1,                 # Optional, default 1
            "openai_key": "sk_...",           # Optional, default None, Set from env if not provided
            "github_token": "ghp_...",        # Optional, default None, Set from env if not provided
        }        
        Returns:
            JSON response with suggestions or error
    """
    @app.route('/api/scan-repos', methods=['POST'])
    def ScanRepositoryEndpoint():        
        try:
            # Parse request data
            data = request.get_json() or {}
            try:
                target, max_results, search_type, ai_key, github_token = validate_scan_payload(data)
            except ValueError as e:
                return jsonify({"error": "invalid_parameter", "message": str(e)}), 400

            # Run the scan
            logger.info(f"Scanning repository: {target}")
            result = ScanBusiness(github_token).ScanRepository(
                target,
                max_results=max_results,
                search_type=search_type,
                ai_key=ai_key
            )
            logger.info(f"Scan completed for repository: {target}")
            suggestions = result.get("suggestions", [])

            return jsonify({
                "success": True,
                "target": target,
                "suggestions": map_suggestions(suggestions),
            }), 200
        
        except GitHubError as e:
            logger.error(f"GitHub API error: {e.message}")
            error_code = e.status_code
            if e.status_code == 401:
                return jsonify({
                    "error": "unauthorized",
                    "message": "Invalid GitHub token"
                }), 401
            elif e.status_code == 429:
                return jsonify({
                    "error": "rate_limit",
                    "message": "GitHub API rate limit exceeded"
                }), 429
            elif e.status_code == 404:
                return jsonify({
                    "error": "not_found",
                    "message": f"Repository not found: {target}"
                }), 404
            else:
                return jsonify({
                    "error": "github_error",
                    "message": e.message
                }), error_code
        
        except ValueError as e:
            logger.error(f"Validation error: {str(e)}")
            return jsonify({
                "error": "invalid_parameter",
                "message": str(e)
            }), 400
        
        except Exception as e:
            logger.exception(f"Error scanning repository: {str(e)}")
            return jsonify({
                "error": "internal_error",
                "message": f"Internal server error: {str(e)}"
            }), 500

    """Apply provided suggestions in a new branch and open a PR.
        Expected JSON body:
        {
            "target": "owner/repo",
            # "search_type": 3,              # required to indicate apply mode
            "suggestions": [{"title":"Add CI","detail":"..."}, ...],
            "branch": "optional-branch-name",
            "github_token": "optional-token"  # optional fallback token
        }
    """
    @app.route('/api/apply-suggestions', methods=['POST'])
    def ApplySuggestionsEndpoint():
       
        try:
            data = request.get_json() or {}
            target = data.get("target")
            suggestions = data.get("suggestions")
            branch = data.get("branch")
            token = data.get("github_token") or None
            ai_key = data.get("ai_key") or None

            if not target:
                return jsonify({"error": "invalid_parameter", "message": "Field 'target' is required"}), 400
           
            if not isinstance(suggestions, list) or not suggestions:
                return jsonify({"error": "invalid_parameter", "message": "Field 'suggestions' must be a non-empty list"}), 400

            # Perform apply -> uses local git and may push and create PR
            from Scanner.Utility.apply_suggestions import apply_suggestions_to_branch

            result = apply_suggestions_to_branch(suggestions, branch_name=branch, github_token=token, ai_key=ai_key, repo_dir=os.getcwd())

            # If validation error occurred while applying AI instructions, return 400 with details
            if isinstance(result, dict) and result.get("message") == "validation_error":
                return jsonify({"success": False, "target": target, "result": result}), 400

            return jsonify({"success": True, "target": target, "result": result}), 200

        except Exception as e:
            logger.exception("Error applying suggestions: %s", e)
            return jsonify({"error": "internal_error", "message": str(e)}), 500
    
    """Handle 404 errors.
        
        Args:
            error: The error object
            
        Returns:
            JSON response with error
    """
    @app.errorhandler(404)
    def NotFound(error):        
        return jsonify({
            "error": "not_found",
            "message": "Endpoint not found. Try GET /api/health or POST /api/scan"
        }), 404
    
    """Handle 405 errors.        
        Args:
            error: The error object            
        Returns:
            JSON response with error
    """
    @app.errorhandler(405)
    def MethodNotAllowed(error):        
        return jsonify({
            "error": "method_not_allowed",
            "message": "Method not allowed for this endpoint"
        }), 405

"""
Main Routes Blueprint - Frontend serving and static files

This blueprint handles serving the React frontend.
"""

import logging
from pathlib import Path
from flask import Blueprint, send_from_directory

logger = logging.getLogger(__name__)

main_bp = Blueprint("main", __name__)

# Project root directory
APP_DIR = Path(__file__).parent.parent.parent


@main_bp.route("/")
def dashboard():
    """
    Serve the React frontend dashboard.

    Returns the built React application from the dist/ folder.
    """
    dist_index = APP_DIR / "dist" / "index.html"
    if dist_index.exists():
        return dist_index.read_text()
    else:
        return "Frontend not built! Run 'npm run build' first.", 500


@main_bp.route("/<path:path>")
def serve_static(path):
    """
    Serve static files or fallback to index.html for SPA routing.
    """
    dist_path = APP_DIR / "dist"
    file_path = dist_path / path
    if file_path.exists():
        return send_from_directory(dist_path, path)
    return send_from_directory(dist_path, "index.html")

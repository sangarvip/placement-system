"""
Campus Placement Management System - Configuration
"""

import os

class Config:

    # Secret key for sessions and security
    SECRET_KEY = os.environ.get("SECRET_KEY", "placement-system-secret-key-change-in-production")

    # MySQL Database Configuration
    MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
    MYSQL_USER = os.environ.get("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "")
    MYSQL_DB = os.environ.get("MYSQL_DB", "placement_system")

    # File Upload Configuration
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "resumes")

    MAX_CONTENT_LENGTH = 5 * 1024 * 1024

    ALLOWED_EXTENSIONS = {"pdf"}

    # Session Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # Session lifetime (24 hours)
    PERMANENT_SESSION_LIFETIME = 86400

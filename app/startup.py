"""
Startup validation and health checks for Hammy the Hire Tracker.

Validates environment, configuration, and service dependencies
before the application starts.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from app.logging_config import get_logger, setup_logging

logger = get_logger(__name__)


class StartupError(Exception):
    """Raised when startup validation fails."""

    pass


class ValidationResult:
    """Result of a validation check."""

    def __init__(
        self,
        name: str,
        passed: bool,
        message: str,
        severity: str = "error",  # error, warning, info
        fix_hint: Optional[str] = None,
    ):
        self.name = name
        self.passed = passed
        self.message = message
        self.severity = severity
        self.fix_hint = fix_hint

    def __str__(self) -> str:
        status = "PASS" if self.passed else self.severity.upper()
        return f"[{status}] {self.name}: {self.message}"


def validate_environment() -> List[ValidationResult]:
    """
    Validate environment variables and configuration.

    Returns:
        List of validation results
    """
    results = []

    # Check for at least one AI provider API key
    ai_providers = [
        ("ANTHROPIC_API_KEY", "Claude/Anthropic"),
        ("OPENAI_API_KEY", "OpenAI"),
        ("GOOGLE_API_KEY", "Google Gemini"),
    ]

    has_ai_provider = False
    for env_var, provider_name in ai_providers:
        value = os.environ.get(env_var)
        if value and len(value) > 10:  # Basic sanity check
            has_ai_provider = True
            results.append(
                ValidationResult(
                    name=f"AI Provider: {provider_name}",
                    passed=True,
                    message=f"{provider_name} API key configured",
                    severity="info",
                )
            )
        else:
            results.append(
                ValidationResult(
                    name=f"AI Provider: {provider_name}",
                    passed=False,
                    message=f"{provider_name} API key not set",
                    severity="info",  # Info because only one is required
                    fix_hint=f"Set {env_var} in your .env file",
                )
            )

    if not has_ai_provider:
        results.append(
            ValidationResult(
                name="AI Provider Required",
                passed=False,
                message="No AI provider API key found. At least one is required.",
                severity="error",
                fix_hint="Set ANTHROPIC_API_KEY, OPENAI_API_KEY, or GOOGLE_API_KEY in .env",
            )
        )

    # Check Flask environment
    flask_env = os.environ.get("FLASK_ENV", "development")
    results.append(
        ValidationResult(
            name="Flask Environment",
            passed=True,
            message=f"Running in {flask_env} mode",
            severity="info",
        )
    )

    return results


def validate_file_system() -> List[ValidationResult]:
    """
    Validate file system paths and permissions.

    Returns:
        List of validation results
    """
    results = []
    app_dir = Path(__file__).parent.parent

    # Check database directory
    db_path = app_dir / "jobs.db"
    db_dir = db_path.parent

    if not db_dir.exists():
        results.append(
            ValidationResult(
                name="Database Directory",
                passed=False,
                message=f"Database directory does not exist: {db_dir}",
                severity="error",
                fix_hint="Create the directory or check app installation",
            )
        )
    elif not os.access(db_dir, os.W_OK):
        results.append(
            ValidationResult(
                name="Database Directory",
                passed=False,
                message=f"No write permission for database directory: {db_dir}",
                severity="error",
                fix_hint="Fix directory permissions: chmod 755",
            )
        )
    else:
        results.append(
            ValidationResult(
                name="Database Directory",
                passed=True,
                message="Database directory accessible",
                severity="info",
            )
        )

    # Check logs directory
    logs_dir = app_dir / "logs"
    if not logs_dir.exists():
        try:
            logs_dir.mkdir(parents=True, exist_ok=True)
            results.append(
                ValidationResult(
                    name="Logs Directory",
                    passed=True,
                    message=f"Created logs directory: {logs_dir}",
                    severity="info",
                )
            )
        except Exception as e:
            results.append(
                ValidationResult(
                    name="Logs Directory",
                    passed=False,
                    message=f"Cannot create logs directory: {e}",
                    severity="warning",
                    fix_hint="Create directory manually or check permissions",
                )
            )
    else:
        results.append(
            ValidationResult(
                name="Logs Directory", passed=True, message="Logs directory exists", severity="info"
            )
        )

    # Check backups directory
    backups_dir = app_dir / "backups"
    if not backups_dir.exists():
        try:
            backups_dir.mkdir(parents=True, exist_ok=True)
            results.append(
                ValidationResult(
                    name="Backups Directory",
                    passed=True,
                    message=f"Created backups directory: {backups_dir}",
                    severity="info",
                )
            )
        except Exception as e:
            results.append(
                ValidationResult(
                    name="Backups Directory",
                    passed=False,
                    message=f"Cannot create backups directory: {e}",
                    severity="warning",
                    fix_hint="Create directory manually or check permissions",
                )
            )
    else:
        results.append(
            ValidationResult(
                name="Backups Directory",
                passed=True,
                message="Backups directory exists",
                severity="info",
            )
        )

    # Check Gmail credentials
    credentials_file = app_dir / "credentials.json"
    token_file = app_dir / "token.json"

    if credentials_file.exists():
        results.append(
            ValidationResult(
                name="Gmail Credentials",
                passed=True,
                message="Gmail credentials.json found",
                severity="info",
            )
        )
    else:
        results.append(
            ValidationResult(
                name="Gmail Credentials",
                passed=False,
                message="Gmail credentials.json not found",
                severity="warning",
                fix_hint="Download credentials from Google Cloud Console",
            )
        )

    if token_file.exists():
        results.append(
            ValidationResult(
                name="Gmail Token",
                passed=True,
                message="Gmail token.json found (authenticated)",
                severity="info",
            )
        )
    else:
        results.append(
            ValidationResult(
                name="Gmail Token",
                passed=False,
                message="Gmail token.json not found (not authenticated)",
                severity="warning",
                fix_hint="Run the app and complete Gmail OAuth flow",
            )
        )

    # Check frontend build
    dist_dir = app_dir / "dist"
    index_file = dist_dir / "index.html"

    if index_file.exists():
        results.append(
            ValidationResult(
                name="Frontend Build",
                passed=True,
                message="Frontend build found (dist/index.html)",
                severity="info",
            )
        )
    else:
        results.append(
            ValidationResult(
                name="Frontend Build",
                passed=False,
                message="Frontend build not found",
                severity="error",
                fix_hint="Run 'npm run build' to build the frontend",
            )
        )

    return results


def validate_database() -> List[ValidationResult]:
    """
    Validate database connection and schema.

    Returns:
        List of validation results
    """
    results = []

    try:
        from app.database import init_db, get_db

        # Initialize database (creates tables if needed)
        init_db()

        results.append(
            ValidationResult(
                name="Database Connection",
                passed=True,
                message="Database initialized successfully",
                severity="info",
            )
        )

        # Check critical tables exist
        conn = get_db()
        cursor = conn.cursor()

        critical_tables = ["jobs", "resume_variants", "followups", "custom_email_sources"]
        for table in critical_tables:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if cursor.fetchone():
                results.append(
                    ValidationResult(
                        name=f"Table: {table}",
                        passed=True,
                        message=f"Table '{table}' exists",
                        severity="info",
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        name=f"Table: {table}",
                        passed=False,
                        message=f"Critical table '{table}' missing",
                        severity="error",
                    )
                )

    except Exception as e:
        results.append(
            ValidationResult(
                name="Database Connection",
                passed=False,
                message=f"Database error: {e}",
                severity="error",
                fix_hint="Check database file permissions and integrity",
            )
        )

    return results


def validate_dependencies() -> List[ValidationResult]:
    """
    Validate Python package dependencies.

    Returns:
        List of validation results
    """
    results = []

    critical_packages = [
        ("flask", "Flask web framework"),
        ("anthropic", "Claude AI SDK"),
        ("google.oauth2", "Google OAuth"),
        ("googleapiclient", "Gmail API"),
    ]

    optional_packages = [
        ("openai", "OpenAI SDK"),
        ("google.generativeai", "Google Gemini SDK"),
    ]

    for package, description in critical_packages:
        try:
            __import__(package)
            results.append(
                ValidationResult(
                    name=f"Package: {package}",
                    passed=True,
                    message=f"{description} available",
                    severity="info",
                )
            )
        except ImportError:
            results.append(
                ValidationResult(
                    name=f"Package: {package}",
                    passed=False,
                    message=f"{description} not installed",
                    severity="error",
                    fix_hint=f"Run: pip install {package}",
                )
            )

    for package, description in optional_packages:
        try:
            __import__(package)
            results.append(
                ValidationResult(
                    name=f"Package: {package}",
                    passed=True,
                    message=f"{description} available",
                    severity="info",
                )
            )
        except ImportError:
            results.append(
                ValidationResult(
                    name=f"Package: {package}",
                    passed=False,
                    message=f"{description} not installed (optional)",
                    severity="info",
                )
            )

    return results


def run_startup_validation(
    strict: bool = False, log_results: bool = True
) -> Tuple[bool, List[ValidationResult]]:
    """
    Run all startup validations.

    Args:
        strict: If True, treat warnings as errors
        log_results: If True, log validation results

    Returns:
        Tuple of (all_passed, results)
    """
    all_results = []

    # Run all validators
    validators = [
        ("Environment", validate_environment),
        ("File System", validate_file_system),
        ("Database", validate_database),
        ("Dependencies", validate_dependencies),
    ]

    for category, validator in validators:
        try:
            results = validator()
            all_results.extend(results)
        except Exception as e:
            all_results.append(
                ValidationResult(
                    name=f"{category} Validation",
                    passed=False,
                    message=f"Validation failed with error: {e}",
                    severity="error",
                )
            )

    # Log results
    if log_results:
        logger.info("=" * 60)
        logger.info("STARTUP VALIDATION RESULTS")
        logger.info("=" * 60)

        for result in all_results:
            if result.passed:
                logger.info(str(result))
            elif result.severity == "error":
                logger.error(str(result))
                if result.fix_hint:
                    logger.error(f"  Hint: {result.fix_hint}")
            elif result.severity == "warning":
                logger.warning(str(result))
                if result.fix_hint:
                    logger.warning(f"  Hint: {result.fix_hint}")
            else:
                logger.info(str(result))

        logger.info("=" * 60)

    # Check for failures
    errors = [r for r in all_results if not r.passed and r.severity == "error"]
    warnings = [r for r in all_results if not r.passed and r.severity == "warning"]

    if errors:
        logger.error(f"Startup validation failed with {len(errors)} error(s)")
        return False, all_results

    if strict and warnings:
        logger.error(f"Startup validation failed with {len(warnings)} warning(s) (strict mode)")
        return False, all_results

    logger.info("Startup validation passed")
    return True, all_results


def get_health_status() -> Dict:
    """
    Get current health status for health check endpoint.

    Returns:
        Health status dictionary
    """
    status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": {},
    }

    # Quick database check
    try:
        from app.database import get_db

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM jobs")
        job_count = cursor.fetchone()[0]
        status["checks"]["database"] = {
            "status": "healthy",
            "job_count": job_count,
        }
    except Exception as e:
        status["status"] = "unhealthy"
        status["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }

    # Check AI provider
    try:
        from app.ai.factory import get_provider_info

        provider_info = get_provider_info()
        available = [p for p, info in provider_info.items() if info.get("available")]
        status["checks"]["ai_provider"] = {
            "status": "healthy" if available else "unhealthy",
            "available_providers": available,
        }
        if not available:
            status["status"] = "unhealthy"
    except Exception as e:
        status["checks"]["ai_provider"] = {
            "status": "unknown",
            "error": str(e),
        }

    # Check disk space (basic)
    try:
        import shutil

        app_dir = Path(__file__).parent.parent
        total, used, free = shutil.disk_usage(app_dir)
        free_gb = free / (1024**3)
        status["checks"]["disk"] = {
            "status": "healthy" if free_gb > 1 else "warning",
            "free_gb": round(free_gb, 2),
        }
        if free_gb < 0.5:
            status["status"] = "unhealthy"
    except Exception as e:
        status["checks"]["disk"] = {
            "status": "unknown",
            "error": str(e),
        }

    return status

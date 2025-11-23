import uvicorn
import argparse
import sys
from pathlib import Path
from app.settings import Settings
from app.web_server.web_server import GraphWebServer
from app.auth.service import AuthService
from app.logger import ConsoleLogger
import logging

logger = ConsoleLogger(name="main", level=logging.INFO)

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="gplot Web Server - Graph rendering REST API")
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Host address to bind to (default: from env or 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port number to listen on (default: from env or 8000)",
    )
    parser.add_argument(
        "--jwt-secret",
        type=str,
        default=None,
        help="JWT secret key (default: from GPLOT_JWT_SECRET env var)",
    )
    parser.add_argument(
        "--token-store",
        type=str,
        default=None,
        help="Path to token store file (default: {data_dir}/auth/tokens.json)",
    )
    parser.add_argument(
        "--no-auth",
        action="store_true",
        help="Disable authentication (WARNING: insecure, for development only)",
    )
    args = parser.parse_args()

    try:
        # Build settings from environment and CLI args
        require_auth = not args.no_auth
        settings = Settings.from_env(require_auth=require_auth)

        # Override with CLI arguments if provided
        if args.host:
            settings.server.host = args.host
        if args.port:
            settings.server.web_port = args.port
        if args.jwt_secret:
            settings.auth.jwt_secret = args.jwt_secret
        if args.token_store:
            settings.auth.token_store_path = Path(args.token_store)

        # Resolve defaults and validate
        settings.resolve_defaults()
        settings.validate()

    except ValueError as e:
        logger.error(
            "FATAL: Configuration error",
            error=str(e),
            help="Set GPLOT_JWT_SECRET environment variable or use --jwt-secret flag, or use --no-auth to disable authentication",
        )
        sys.exit(1)

    # Create AuthService instance if authentication is enabled (dependency injection)
    auth_service_instance = None
    if require_auth:
        auth_service_instance = AuthService(
            secret_key=settings.auth.jwt_secret,
            token_store_path=str(settings.auth.token_store_path),
        )
        logger.info(
            "Authentication service created",
            token_store=str(auth_service_instance.token_store_path),
            secret_fingerprint=auth_service_instance.get_secret_fingerprint(),
        )

    # Initialize server with dependency injection
    server = GraphWebServer(
        jwt_secret=settings.auth.jwt_secret,  # Legacy parameter (ignored if auth_service provided)
        token_store_path=str(
            settings.auth.token_store_path
        ),  # Legacy parameter (ignored if auth_service provided)
        require_auth=require_auth,
        auth_service=auth_service_instance,  # Dependency injection
    )

    try:
        logger.info(
            "Starting web server",
            host=settings.server.host,
            port=settings.server.web_port,
            transport="HTTP REST API",
            jwt_enabled=require_auth,
        )
        uvicorn.run(server.app, host=settings.server.host, port=settings.server.web_port)
        logger.info("Web server shutdown complete")
    except KeyboardInterrupt:
        logger.info("Web server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error("Failed to start web server", error=str(e), error_type=type(e).__name__)
        sys.exit(1)

import argparse
import sys
import asyncio
from pathlib import Path
from app.settings import Settings
from app.auth import AuthService
from app.logger import ConsoleLogger
import logging

logger = ConsoleLogger(name="main_mcp", level=logging.INFO)

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="gplot MCP Server - Graph rendering via Model Context Protocol"
    )
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
        help="Port number to listen on (default: from env or 8001)",
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

    # Create logger for startup messages
    startup_logger = ConsoleLogger(name="startup", level=logging.INFO)

    try:
        # Build settings from environment and CLI args
        require_auth = not args.no_auth
        settings = Settings.from_env(require_auth=require_auth)

        # Override with CLI arguments if provided
        if args.host:
            settings.server.host = args.host
        if args.port:
            settings.server.mcp_port = args.port
        if args.jwt_secret:
            settings.auth.jwt_secret = args.jwt_secret
        if args.token_store:
            settings.auth.token_store_path = Path(args.token_store)

        # Resolve defaults and validate
        settings.resolve_defaults()
        settings.validate()

    except ValueError as e:
        startup_logger.error(
            "FATAL: Configuration error",
            error=str(e),
            help="Set GPLOT_JWT_SECRET environment variable or use --jwt-secret flag, or use --no-auth to disable authentication",
        )
        sys.exit(1)

    # Initialize auth service only if auth is required
    auth_service = None
    if require_auth:
        auth_service = AuthService(
            secret_key=settings.auth.jwt_secret,
            token_store_path=str(settings.auth.token_store_path),
        )
        startup_logger.info(
            "Authentication service initialized",
            jwt_enabled=True,
            token_store=str(auth_service.token_store_path),
            secret_fingerprint=auth_service.get_secret_fingerprint(),
        )
    else:
        startup_logger.info("Authentication disabled", jwt_enabled=False)

    # Import and configure mcp_server with auth service (dependency injection)
    from app.mcp_server.mcp_server import set_auth_service, main

    set_auth_service(auth_service)

    try:
        startup_logger.info(
            "Starting MCP server",
            host=settings.server.host,
            port=settings.server.mcp_port,
            transport="Streamable HTTP",
            jwt_enabled=require_auth,
        )
        asyncio.run(main(host=settings.server.host, port=settings.server.mcp_port))
        startup_logger.info("MCP server shutdown complete")
    except KeyboardInterrupt:
        startup_logger.info("Shutdown complete")
        sys.exit(0)
    except Exception as e:
        startup_logger.error("Failed to start server", error=str(e), error_type=type(e).__name__)
        sys.exit(1)

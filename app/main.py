import uvicorn
import argparse
from app.web_server import GraphWebServer
from app.logger import ConsoleLogger
import logging
import sys

server = GraphWebServer()
logger = ConsoleLogger(name="main", level=logging.INFO)

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="gplot Web Server - Graph rendering REST API")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Host address to bind to (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port number to listen on (default: 8000)",
    )
    args = parser.parse_args()

    try:
        logger.info(
            "Starting web server", host=args.host, port=args.port, transport="HTTP REST API"
        )
        uvicorn.run(server.app, host=args.host, port=args.port)
        logger.info("Web server shutdown complete")
    except KeyboardInterrupt:
        logger.info("Web server stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error("Failed to start web server", error=str(e), error_type=type(e).__name__)
        sys.exit(1)

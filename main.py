"""
GitHub Scanner API Server
Run the Flask REST API server for GitHub Scanner.
Usage:
    python main.py
    python main.py --port 8000
    python main.py --debug
"""

import argparse
import sys
from Scanner.Routes.ScanRoute import CreateApp

# ✅ Create the Flask app globally so Gunicorn can find it
app = CreateApp()

def main():
    """Parse arguments and start the API server."""
    parser = argparse.ArgumentParser(
        description="GitHub Scanner REST API Server",
        epilog="""
            Examples:
            python main.py                    # Start on port 5000
            python main.py --port 8000        # Start on port 8000
            python main.py --host 127.0.0.1   # Start on localhost only
            python main.py --debug            # Start in debug mode
        """
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Port to run the server on (default: 5000)'
    )
    parser.add_argument(
        '--host',
        default='0.0.0.0',
        help='Host to bind to (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Run in debug mode'
    )

    args = parser.parse_args()

    print(f"\n{'='*60}")
    print("GitHub Scanner API Server")
    print(f"{'='*60}")
    print(f"Server starting on http://{args.host}:{args.port}")
    print(f"Debug mode: {args.debug}")
    print(f"\nEndpoints:")
    print(f"  GET  http://{args.host}:{args.port}/api/health")
    print(f"  POST http://{args.host}:{args.port}/api/scan")
    print(f"{'='*60}\n")

    try:
        app.run(
            host=args.host,
            port=args.port,
            debug=args.debug,
            use_reloader=args.debug
        )
    except KeyboardInterrupt:
        print("\n\nServer stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nError starting server: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
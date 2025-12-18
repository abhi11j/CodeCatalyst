# Run with Docker

Build the image:

    docker build -t codecatalyst:latest .

Run the container (default port 5000):

    docker run --rm -p 5000:5000 --env-file .env codecatalyst:latest

Notes:
- Use `--env-file .env` to pass environment variables (e.g., GitHub API keys).
- For production, consider running with a process manager (Gunicorn) and mounting a volume for logs.
- The image uses Python 3.11-slim; add additional OS packages to the Dockerfile if your project requires them.


"""
Static templates for Docker workflows.
"""

DOCKER_TEMPLATES = {
    "node_app": {
        "name": "Node.js Web App",
        "description": "Create a Node.js environment container",
        "steps": [
            {"desc": "Pull node:18-alpine", "cmd": "docker pull node:18-alpine"},
            {"desc": "Run node container", "cmd": "docker run -d --name node-web-app -p 3000:3000 node:18-alpine node -e 'const http = require(\"http\"); http.createServer((req, res) => { res.writeHead(200); res.end(\"Hello from FixShell Node App\"); }).listen(3000);'"}
        ],
        "summary": "Node.js app running on port 3000 (container: node-web-app)"
    },
    "python_app": {
        "name": "Python Web App",
        "description": "Create a Python environment container",
        "steps": [
            {"desc": "Pull python:3.11-slim", "cmd": "docker pull python:3.11-slim"},
            {"desc": "Run python container", "cmd": "docker run -d --name python-web-app -p 8000:8000 python:3.11-slim python -m http.server 8000"}
        ],
        "summary": "Python HTTP server on port 8000 (container: python-web-app)"
    },
    "mysql": {
        "name": "MySQL Database",
        "description": "Run a standard MySQL 8.0 instance",
        "steps": [
            {"desc": "Pull mysql:8.0", "cmd": "docker pull mysql:8.0"},
            {"desc": "Start MySQL container", "cmd": "docker run -d --name mysql-db -e MYSQL_ROOT_PASSWORD=password -p 3306:3306 mysql:8.0"}
        ],
        "summary": "MySQL running on port 3306 (user: root, pass: password)"
    },
    "postgres": {
        "name": "PostgreSQL Database",
        "description": "Run a standard PostgreSQL 15 instance",
        "steps": [
            {"desc": "Pull postgres:15", "cmd": "docker pull postgres:15"},
            {"desc": "Start Postgres container", "cmd": "docker run -d --name postgres-db -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:15"}
        ],
        "summary": "PostgreSQL running on port 5432 (user: postgres, pass: password)"
    }
}

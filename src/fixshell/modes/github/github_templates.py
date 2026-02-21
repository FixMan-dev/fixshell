"""
Static templates for GitHub workflows.
"""

GITHUB_TEMPLATES = {
    "init_repo": {
        "name": "Initialize Git Repository",
        "description": "Create a new local git repo with standard .gitignore",
        "steps": [
            {"desc": "Check Git", "action": "validate_git"},
            {"desc": "Git Init", "cmd": "git init"},
            {"desc": "Create standard gitignore", "cmd": "touch .gitignore"}
        ],
        "summary": "Repository initialized locally."
    },
    "ci_node": {
        "name": "Add Node.js CI",
        "description": "Add GitHub Actions workflow for Node.js",
        "steps": [
            {"desc": "Creating .github/workflows", "cmd": "mkdir -p .github/workflows"},
            {"desc": "Creating node-ci.yml", "cmd": "printf 'name: Node CI\non: [push]\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - name: Use Node.js\n        uses: actions/setup-node@v3\n        with:\n          node-version: 18\n      - run: npm ci\n      - run: npm test' > .github/workflows/node-ci.yml"}
        ],
        "summary": "Node.js CI added to .github/workflows/node-ci.yml"
    },
     "ci_python": {
        "name": "Add Python CI",
        "description": "Add GitHub Actions workflow for Python",
        "steps": [
            {"desc": "Creating .github/workflows", "cmd": "mkdir -p .github/workflows"},
            {"desc": "Creating python-ci.yml", "cmd": "printf 'name: Python CI\non: [push]\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v3\n      - name: Set up Python\n        uses: actions/setup-python@v4\n        with:\n          python-version: 3.10\n      - run: pip install -r requirements.txt\n      - run: pytest' > .github/workflows/python-ci.yml"}
        ],
        "summary": "Python CI added to .github/workflows/python-ci.yml"
    }
}

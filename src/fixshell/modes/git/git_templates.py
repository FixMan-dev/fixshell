
GIT_MENU = {
    "1": "Start New Project",
    "2": "Clone Repository",
    "3": "Daily Work (Pull → Commit → Push)",
    "4": "Create Feature Branch",
    "5": "Sync Feature Branch with Main",
    "6": "Resolve Merge Conflict",
    "7": "Delete Branch Safely",
    "8": "Add CI Workflow",
    "9": "Show Repository Status",
    "10": "Login / Authenticate (gh)",
    "11": "Exit"
}

GITIGNORE_CONTENT = {
    "python": "__pycache__/\n*.pyc\nvenv/\n.env\n.pytest_cache/\n",
    "node": "node_modules/\n.env\nnpm-debug.log*\n",
    "go": "bin/\n*.exe\n*.exe~\n*.dll\n*.so\n*.dylib\n"
}

CI_TEMPLATES = {
    "python": """name: Python CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run tests
      run: pytest
""",
    "node": """name: Node.js CI
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Use Node.js
      uses: actions/setup-node@v2
      with:
        node-version: '14'
    - run: npm install
    - run: npm test
"""
}

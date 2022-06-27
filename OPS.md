# Pushing a new version
1. Make code changes
1. Update version in `pyproject.toml`
1. Commit & push changes
1. Clean: `rm -r distr`
1. Build: `python3 -m build`
1. Upload to pypi: `python3 -m twine upload dist/*`
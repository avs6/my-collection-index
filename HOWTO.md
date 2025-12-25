# Using the auto-updater

## 1) Create a GitHub token
Create a fine-grained personal access token with:
- **Read access** to: `Starring` (and optionally `Metadata`)

Export it locally:
```bash
export GITHUB_TOKEN="..."
```

## 2) Run updater
```bash
python scripts/update_from_stars.py --user <your_github_username> --write
```

## 3) Commit changes
```bash
git add README.md
git commit -m "Update curated tables from stars"
git push
```

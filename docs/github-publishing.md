# GitHub Publishing

This repository is safe to publish as open source when `.local/` and `.env` remain ignored.

## Create a GitHub Repository

Create an empty public repository, for example:

```text
https://github.com/<account>/hermes-line-wordpress-agent
```

Then connect this local repo:

```bash
git remote add origin https://github.com/<account>/hermes-line-wordpress-agent.git
git push -u origin main
```

## Pre-Push Checklist

```bash
git status --short
git check-ignore -v .local/my-site/site.profile.yaml
python -m compileall src
```

Confirm the staged or committed files do not include:

- `.local/`
- `.env`
- WordPress credentials
- LINE user IDs or group IDs
- Site-specific SEO strategy

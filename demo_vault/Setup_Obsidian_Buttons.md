---
type: setup_guide
---

# Obsidian Buttons Setup Guide

## Step 1: Install Plugins

1. Open Obsidian Settings (gear icon bottom-left)
2. Go to **Community Plugins** → **Turn on community plugins**
3. Click **Browse** and install:
   - **Buttons** (by shabegom)
   - **Shell commands** (by Jarkko Linnanvirta)
4. Enable both plugins

## Step 2: Configure Shell Commands

1. Go to **Settings** → **Shell commands** (in left sidebar under Community Plugins)
2. Click **New shell command** for each:

### Command 1: generate-linkedin
```
cd "E:\hackathon 0 qwen\Personal-AI-Employee" && venv-win\Scripts\python.exe post_social.py --generate linkedin
```
**Alias**: `generate-linkedin`

### Command 2: generate-twitter
```
cd "E:\hackathon 0 qwen\Personal-AI-Employee" && venv-win\Scripts\python.exe post_social.py --generate twitter
```
**Alias**: `generate-twitter`

### Command 3: generate-all
```
cd "E:\hackathon 0 qwen\Personal-AI-Employee" && venv-win\Scripts\python.exe post_social.py --generate all
```
**Alias**: `generate-all`

### Command 4: post-linkedin
```
cd "E:\hackathon 0 qwen\Personal-AI-Employee" && for %f in (demo_vault\Pending_Approval\SOCIAL_linkedin_*.md) do venv-win\Scripts\python.exe post_social.py --platform linkedin --file "%f"
```
**Alias**: `post-linkedin`

### Command 5: post-twitter
```
cd "E:\hackathon 0 qwen\Personal-AI-Employee" && for %f in (demo_vault\Pending_Approval\SOCIAL_twitter_*.md) do venv-win\Scripts\python.exe post_social.py --platform twitter --file "%f"
```
**Alias**: `post-twitter`

### Command 6: post-all
```
cd "E:\hackathon 0 qwen\Personal-AI-Employee" && for %f in (demo_vault\Pending_Approval\SOCIAL_*.md) do venv-win\Scripts\python.exe post_social.py --platform all --file "%f"
```
**Alias**: `post-all`

### Command 7: quick-post-linkedin
```
cd "E:\hackathon 0 qwen\Personal-AI-Employee" && venv-win\Scripts\python.exe post_social.py --platform linkedin --text "{{clipboard}}"
```
**Alias**: `quick-post-linkedin`

## Step 3: Test

1. Open `Social_Media_Control.md` in Obsidian
2. Click **"Generate LinkedIn Post"** button
3. Check `Pending_Approval/` folder - a new draft should appear
4. Open draft, edit if needed
5. Click **"Post to LinkedIn"** button
6. Check `Done/` folder - posted file moves there

## Alternative: Without Plugins (PowerShell)

If plugins don't work, use PowerShell directly:

```powershell
# Generate AI post
python post_social.py --generate linkedin
python post_social.py --generate twitter --topic "AI automation"

# Post draft
python post_social.py --platform linkedin --file "demo_vault\Pending_Approval\SOCIAL_linkedin_draft_xxx.md"

# Quick post
python post_social.py --platform twitter --text "Excited about AI automation! #AI #Tech"

# Post to all platforms
python post_social.py --platform all --text "Big news coming soon! #Innovation"
```


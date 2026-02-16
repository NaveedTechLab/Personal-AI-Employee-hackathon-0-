#!/usr/bin/env python3
"""
Social Media Poster - Called from Obsidian buttons
Posts to LinkedIn, Twitter, or all platforms.

Usage:
    python post_social.py --platform linkedin --file "path/to/post.md"
    python post_social.py --platform twitter --file "path/to/post.md"
    python post_social.py --platform all --file "path/to/post.md"
    python post_social.py --platform linkedin --text "Post content here"
    python post_social.py --generate linkedin  # AI generates + saves draft
"""

import argparse
import os
import sys
import json
import requests
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

VAULT_DIR = Path(os.getenv("VAULT_DIR", "./demo_vault"))
LOGS_DIR = VAULT_DIR / "Logs"
DONE_DIR = VAULT_DIR / "Done"
PENDING_DIR = VAULT_DIR / "Pending_Approval"

# API Credentials
LINKEDIN_ACCESS_TOKEN = os.getenv("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_PAGE_IDS = os.getenv("LINKEDIN_PAGE_IDS", "")

TWITTER_API_KEY = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")

META_PAGE_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
META_PAGE_ID = os.getenv("META_PAGE_ID", "")


def log_activity(platform, action, details=""):
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOGS_DIR / f"social_posting_{datetime.now().strftime('%Y%m%d')}.log"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{platform}] {action}: {details}\n")


def read_post_from_file(filepath):
    """Read post content from a markdown file."""
    path = Path(filepath)
    if not path.exists():
        print(f"ERROR: File not found: {filepath}")
        return None, None

    content = path.read_text(encoding="utf-8")

    # Extract post text (between ## Post Content markers or after ---)
    post_text = ""
    in_post = False
    for line in content.split("\n"):
        if "## Post Content" in line or "## Content" in line:
            in_post = True
            continue
        if in_post and line.startswith("## "):
            break
        if in_post:
            post_text += line + "\n"

    if not post_text.strip():
        # Fallback: use everything after frontmatter
        parts = content.split("---")
        if len(parts) >= 3:
            post_text = parts[2].strip()
        else:
            post_text = content.strip()

    return post_text.strip(), path


# ============================================================
# LINKEDIN POSTING
# ============================================================

def get_linkedin_profile_id():
    """Get LinkedIn profile URN."""
    headers = {"Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}"}
    r = requests.get("https://api.linkedin.com/v2/me", headers=headers)
    if r.status_code == 200:
        data = r.json()
        return data.get("id")
    else:
        print(f"LinkedIn auth error: {r.status_code} - {r.text}")
        return None


def post_to_linkedin(text):
    """Post text to LinkedIn."""
    if not LINKEDIN_ACCESS_TOKEN or LINKEDIN_ACCESS_TOKEN.startswith("your_"):
        print("ERROR: LinkedIn access token not configured in .env")
        return False

    profile_id = get_linkedin_profile_id()
    if not profile_id:
        return False

    headers = {
        "Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    payload = {
        "author": f"urn:li:person:{profile_id}",
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {"text": text},
                "shareMediaCategory": "NONE",
            }
        },
        "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
    }

    r = requests.post(
        "https://api.linkedin.com/v2/ugcPosts",
        headers=headers,
        json=payload,
    )

    if r.status_code in [200, 201]:
        post_id = r.json().get("id", "unknown")
        print(f"LINKEDIN POST SUCCESS! Post ID: {post_id}")
        log_activity("linkedin", "POSTED", f"ID={post_id}, text={text[:50]}...")
        return True
    else:
        print(f"LINKEDIN ERROR: {r.status_code} - {r.text}")
        log_activity("linkedin", "ERROR", f"{r.status_code}: {r.text[:100]}")
        return False


# ============================================================
# TWITTER/X POSTING
# ============================================================

def post_to_twitter(text):
    """Post tweet using OAuth 1.0a."""
    if not TWITTER_API_KEY or TWITTER_API_KEY.startswith("your_"):
        print("ERROR: Twitter API key not configured in .env")
        return False

    try:
        import tweepy
        auth = tweepy.OAuth1UserHandler(
            TWITTER_API_KEY, TWITTER_API_SECRET,
            TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET
        )
        api = tweepy.API(auth)

        # Twitter v2 client for posting
        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
        )

        # Truncate to 280 chars
        if len(text) > 280:
            text = text[:277] + "..."

        response = client.create_tweet(text=text)
        tweet_id = response.data["id"]
        print(f"TWITTER POST SUCCESS! Tweet ID: {tweet_id}")
        log_activity("twitter", "POSTED", f"ID={tweet_id}, text={text[:50]}...")
        return True

    except ImportError:
        print("ERROR: tweepy not installed. Run: pip install tweepy")
        return False
    except Exception as e:
        print(f"TWITTER ERROR: {e}")
        log_activity("twitter", "ERROR", str(e)[:100])
        return False


# ============================================================
# META (FACEBOOK) POSTING
# ============================================================

def post_to_facebook(text):
    """Post to Facebook page."""
    if not META_PAGE_ACCESS_TOKEN or META_PAGE_ACCESS_TOKEN.startswith("your_"):
        print("ERROR: Meta access token not configured in .env")
        return False

    url = f"https://graph.facebook.com/v21.0/{META_PAGE_ID}/feed"
    payload = {"message": text, "access_token": META_PAGE_ACCESS_TOKEN}

    r = requests.post(url, data=payload)
    if r.status_code == 200:
        post_id = r.json().get("id", "unknown")
        print(f"FACEBOOK POST SUCCESS! Post ID: {post_id}")
        log_activity("facebook", "POSTED", f"ID={post_id}")
        return True
    else:
        print(f"FACEBOOK ERROR: {r.status_code} - {r.text}")
        log_activity("facebook", "ERROR", f"{r.status_code}: {r.text[:100]}")
        return False


# ============================================================
# AI CONTENT GENERATOR
# ============================================================

def generate_post_content(platform, topic=None):
    """Generate social media post using AI (OpenRouter/Qwen)."""
    api_key = os.getenv("OPENAI_API_KEY", "")
    base_url = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    model = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

    if not api_key:
        print("ERROR: No AI API key configured")
        return None

    if platform == "twitter":
        max_chars = "280 characters"
        style = "concise, engaging, with relevant hashtags"
    elif platform == "linkedin":
        max_chars = "1000 characters"
        style = "professional, insightful, thought-leadership tone"
    else:
        max_chars = "500 characters"
        style = "engaging, casual but professional"

    prompt = f"""Generate a {platform} post for a business/tech professional.
Topic: {topic if topic else 'AI and automation in business, productivity tips, or tech industry insights'}
Style: {style}
Max length: {max_chars}
Include relevant hashtags.
Output ONLY the post text, nothing else."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
    }

    try:
        r = requests.post(f"{base_url}/chat/completions", headers=headers, json=payload)
        if r.status_code == 200:
            content = r.json()["choices"][0]["message"]["content"].strip()
            print(f"\n--- AI Generated {platform.upper()} Post ---")
            print(content)
            print("--- End ---\n")
            return content
        else:
            print(f"AI ERROR: {r.status_code} - {r.text[:200]}")
            return None
    except Exception as e:
        print(f"AI ERROR: {e}")
        return None


def save_draft(platform, content):
    """Save AI-generated draft to Pending_Approval for review."""
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    filename = f"SOCIAL_{platform}_draft_{now.strftime('%Y%m%d_%H%M%S')}.md"

    draft = f"""---
type: social_post
platform: {platform}
status: pending_approval
generated: {now.isoformat()}
---

# {platform.title()} Post Draft

## Post Content
{content}

## Actions
- Edit the content above if needed
- Move this file to `Approved/` to post
- Move to `Rejected/` to discard

> AI-generated draft at {now.strftime('%Y-%m-%d %H:%M:%S')}
"""

    filepath = PENDING_DIR / filename
    filepath.write_text(draft, encoding="utf-8")
    print(f"Draft saved: {filepath}")
    return filepath


def move_to_done(filepath, platform, success):
    """Move posted file to Done."""
    if filepath and Path(filepath).exists():
        DONE_DIR.mkdir(parents=True, exist_ok=True)
        status = "POSTED" if success else "FAILED"
        done_name = f"{status}_{Path(filepath).name}"
        done_path = DONE_DIR / done_name
        import shutil
        shutil.move(str(filepath), str(done_path))
        print(f"Moved to Done: {done_name}")


# ============================================================
# MAIN
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="Social Media Poster")
    parser.add_argument("--platform", choices=["linkedin", "twitter", "facebook", "all"],
                        help="Platform to post to")
    parser.add_argument("--file", help="Path to markdown file with post content")
    parser.add_argument("--text", help="Direct text to post")
    parser.add_argument("--generate", metavar="PLATFORM",
                        choices=["linkedin", "twitter", "facebook", "all"],
                        help="AI-generate post content and save as draft")
    parser.add_argument("--topic", help="Topic for AI generation", default=None)
    parser.add_argument("--post-draft", metavar="FILE",
                        help="Post a draft file directly (skip approval)")

    args = parser.parse_args()

    # Mode 1: Generate AI content
    if args.generate:
        platforms = ["linkedin", "twitter", "facebook"] if args.generate == "all" else [args.generate]
        for p in platforms:
            print(f"\nGenerating {p} content...")
            content = generate_post_content(p, args.topic)
            if content:
                save_draft(p, content)
        return

    # Mode 2: Post from file
    if args.file:
        text, filepath = read_post_from_file(args.file)
        if not text:
            return
    elif args.text:
        text = args.text
        filepath = None
    elif args.post_draft:
        text, filepath = read_post_from_file(args.post_draft)
        if not text:
            return
    else:
        parser.print_help()
        return

    if not args.platform and not args.post_draft:
        print("ERROR: --platform required when posting")
        return

    platform = args.platform or "linkedin"

    # Post
    print(f"\nPosting to {platform}...")
    print(f"Content: {text[:100]}...")
    print()

    results = {}
    if platform in ["linkedin", "all"]:
        results["linkedin"] = post_to_linkedin(text)
    if platform in ["twitter", "all"]:
        results["twitter"] = post_to_twitter(text)
    if platform in ["facebook", "all"]:
        results["facebook"] = post_to_facebook(text)

    # Summary
    print("\n" + "=" * 40)
    print("  POSTING RESULTS")
    print("=" * 40)
    for p, success in results.items():
        icon = "OK" if success else "FAIL"
        print(f"  {p:12s}: {icon}")

    if filepath:
        all_success = all(results.values())
        move_to_done(filepath, platform, all_success)


if __name__ == "__main__":
    main()

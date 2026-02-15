---
type: control_panel
updated: 2026-02-08
---

# Social Media Control Panel

> Use the buttons below to generate and post content. AI will write the post, you review and click to publish.

---

## Step 1: Generate Post (AI Writes It)

```button
name Generate LinkedIn Post
type command
action Shell commands: Execute: generate-linkedin
color blue
```

```button
name Generate Twitter Post
type command
action Shell commands: Execute: generate-twitter
color blue
```

```button
name Generate All Platforms
type command
action Shell commands: Execute: generate-all
color purple
```

---

## Step 2: Review Draft
After clicking "Generate", check the `Pending_Approval/` folder.
A new `SOCIAL_linkedin_draft_*.md` or `SOCIAL_twitter_draft_*.md` will appear.

**Open the draft file and edit the content if needed.**

---

## Step 3: Post It (One Click)

```button
name Post to LinkedIn
type command
action Shell commands: Execute: post-linkedin
color green
```

```button
name Post to Twitter
type command
action Shell commands: Execute: post-twitter
color green
```

```button
name Post to All Platforms
type command
action Shell commands: Execute: post-all
color green
```

---

## Quick Post (Type & Post)

Write your post below and click the button:

### My Post:
> Write your content here...



```button
name Post Above Text to LinkedIn
type command
action Shell commands: Execute: quick-post-linkedin
color orange
```

---

## Recent Posts

| Date | Platform | Status | Content |
|------|----------|--------|---------|
| Check `Done/POSTED_*` files for history | | | |

---

## How It Works

```
1. Click "Generate" → AI writes a professional post
2. Draft appears in Pending_Approval/ folder
3. Open draft, edit if needed
4. Click "Post" → Published to your account!
5. File moves to Done/ automatically
```

> **Note**: Install Obsidian plugins: **Buttons** + **Shell commands** for buttons to work.


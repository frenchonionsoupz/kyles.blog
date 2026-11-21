# kyles.blog

A Jekyll blog hosted on GitHub Pages.

## One-time publishing setting

Open https://github.com/frenchonionsoupz/kyles.blog/settings/pages and select
**Build and deployment → Source → GitHub Actions**. This is needed for the automatic
short-URL generator, which runs before Jekyll builds the site. The workflow file is
`.github/workflows/deploy.yml`. Keep the custom domain `kyles.blog` configured.

## New posts

Create `_posts/YYYY-MM-DD-post-title.md` with front matter:

```yaml
---
layout: post
title: "The title of my post"
date: 2026-11-20
---
```

Every push to main automatically rebuilds and deploys the website. The build
chooses a short URL from a distinctive title word, without duplicating earlier
slugs. When you want a more creative URL, specify either `slug: evolution`
or `permalink: /evolution/` in that post's front matter. Manual permalinks
always take precedence. Preserve old `permalink` values when updating a post
so existing URLs stay stable. Existing original-title URLs redirect to the
current short URLs.

## Automatic pages

- `/` shows an automatically updated word count and published posts.
- `/hyperlinks/` lists every published article by category with a link to the post. Add `category: "Work & Life"` (or another category) to a post's YAML front matter for grouping; posts without a category appear under Other. The directory updates on every build.
- `/feed.xml` is the RSS feed.

## Email subscriptions

The copied Kit embed still points to the original Learning Freelance Kit form.
This site does not run an automated newsletter campaign. Replace the Kit embed
in `index.html` and `_layouts/default.html` when you want a separate signup.

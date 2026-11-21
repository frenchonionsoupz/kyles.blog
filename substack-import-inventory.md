# Substack published-post inventory

Source: user-supplied Substack `posts(3).csv` export metadata (2026-11-20).

**22 published posts** are flagged `is_published=true`. The CSV additionally lists **24 unpublished/draft records**, deliberately excluded. This file contains only post IDs, dates, titles, subtitles, and flags — **no article bodies or embedded image files**. Do not generate placeholder website posts from this inventory.

This list is for reconciling the complete Substack export with the existing Jekyll and Medium articles. Some entries may overlap with already imported posts (e.g., Kobe or Cubicle; What Marketers Get Wrong About Psychology). The CSV’s `post_date` values are UTC; preserve them when eventually importing.

| Original date (UTC) | Title | Public URL candidate (verify) |
|---|---|---|
| 2026-10-21 | The Acoustic Algorithm | https://kylejennings.substack.com/p/the-acoustic-algorithm |
| 2026-09-26 | The Antidote to Alienation Is Embeddedness | https://kylejennings.substack.com/p/the-antidote-to-alienation-is-embeddedness |
| 2026-08-23 | Always almost there... | https://kylejennings.substack.com/p/always-almost-there |
| 2026-03-04 | Life Is Weird | https://kylejennings.substack.com/p/life-is-weird |
| 2026-02-12 | When Everyone's a Marketer | https://kylejennings.substack.com/p/when-everyones-a-marketer |
| 2026-02-09 | How Algorithms Reshape Our Reality | https://kylejennings.substack.com/p/how-algorithms-reshape-our-reality |
| 2026-01-27 | Impacts Of A Me-ritocracy | https://kylejennings.substack.com/p/the-impacts-of-a-me-ritocracy |
| 2026-01-19 | The Age of Enter-Train-Ment | https://kylejennings.substack.com/p/the-age-of-enter-train-ment |
| 2026-01-16 | Lose Yourself In the Algo | https://kylejennings.substack.com/p/lose-yourself-in-the-algo |
| 2025-12-31 | The McDicks of Information | https://kylejennings.substack.com/p/the-mcdicks-of-information |
| 2025-12-09 | #2: Kobe Or Cubicle | https://kylejennings.substack.com/p/2-kobe-or-cubicle |
| 2025-12-02 | This Week In Kyle #1: Hi | https://kylejennings.substack.com/p/this-week-in-kyle-1-hi |
| 2025-09-02 | The Invasive Species Inside Of Us | https://kylejennings.substack.com/p/the-invasive-species-inside-of-us |
| 2025-07-08 | 10 things Goose taught us | https://kylejennings.substack.com/p/10-things-goose-taught-us |
| 2025-06-30 | Molehills Are The Mountains | https://kylejennings.substack.com/p/molehills-are-the-mountains |
| 2025-06-24 | Ugly Photos Are More Beautiful | https://kylejennings.substack.com/p/ugly-photos-are-more-beautiful |
| 2025-06-12 | 13 things I take for granted | https://kylejennings.substack.com/p/13-things-i-take-for-granted |
| 2025-06-10 | Laugh like a crazy person | https://kylejennings.substack.com/p/laugh-like-a-crazy-person |
| 2025-06-02 | A forgotten family history | https://kylejennings.substack.com/p/a-forgotten-family-history |
| 2025-01-29 | You vs. The Algorithm | https://kylejennings.substack.com/p/you-vs-the-algorithm |
| 2023-11-16 | What Marketers Get Wrong About Psychology | https://kylejennings.substack.com/p/what-marketers-get-wrong-about-psychology |
| 2023-09-25 | Humor as a Tool | https://kylejennings.substack.com/p/humor-as-a-tool |

## To complete the import

Export the full Substack publication data as a ZIP containing the **post body HTML/Markdown files** and any available images, not only `posts.csv`. Upload the complete ZIP for import. Preserve the original posts and avoid publishing unpublished drafts.

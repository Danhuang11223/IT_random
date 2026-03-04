# Sustainability Report Template

This project brief requires before/after evidence. The current local environment does not include Chrome or Lighthouse, so the measurements must be run manually on your machine and then pasted into this file.

## Tool

- Recommended tool: Google Lighthouse (Chrome DevTools or PageSpeed Insights for public URLs)

## Pages to Test

Test at least two pages:

1. Login page
2. One core feature page (recommended: Generator dashboard)

If using the local app:

- Front end: `http://127.0.0.1:5173/login`
- Dashboard: `http://127.0.0.1:5173/dashboard`

## Baseline (Before)

Fill this in before you make any performance-focused changes.

| Page | Performance | Accessibility | Best Practices | SEO | Notes |
| --- | --- | --- | --- | --- | --- |
| Login |  |  |  |  |  |
| Dashboard |  |  |  |  |  |

Add screenshots or exported Lighthouse reports below this table in the final PDF.

## Changes Implemented to Improve Sustainability / Performance

Use only changes you actually made and can justify. Suitable examples for this project include:

- Built the front end with Vite production build for minified assets
- Kept API responses paginated for history data
- Avoided large image assets on the main interactive screens
- Used reusable components instead of duplicated markup
- Removed unnecessary decorative media from the primary user flow
- Kept front-end API calls scoped to the current view instead of loading everything at once

If you make further changes, list them here.

## After Measurement

Run Lighthouse again after the changes and fill this table.

| Page | Performance | Accessibility | Best Practices | SEO | What improved |
| --- | --- | --- | --- | --- | --- |
| Login |  |  |  |  |  |
| Dashboard |  |  |  |  |  |

## Reflection

Write 3–5 sentences:

- What changed most
- Which change had the biggest effect
- Which trade-offs were involved
- What you would optimise next if given more time

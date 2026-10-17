# bojianhou.com

Personal homepage of Bojian Hou, built with Jekyll and served by GitHub Pages from `master`.
Originally based on the [AcademicPages](https://github.com/academicpages/academicpages.github.io) template
(itself derived from Minimal Mistakes, MIT License; see `LICENSE`).

## Where things live

| What | File |
|---|---|
| Publications (one entry per paper; drives the homepage and `/publications/`) | `_data/publications.yml` |
| Topic filters | `_data/topics.yml` |
| News | `_data/news.yml` |
| Honors and awards | `_data/awards.yml` |
| Academic service summary | `_data/service.yml` (full list in `_pages/services.md`) |
| Research interest areas | `_data/research.yml` |
| Navigation, selected papers, venue list | `_data/site.yml` |
| Page templates | `_layouts/rd.html`, `_includes/rd-*.html`, `_includes/pub-*.html`, `_includes/news-list.html` |
| Styles and script | `assets/css/site.scss`, `assets/js/site.js` |
| Paper thumbnails | `images/pubs/<id>.webp` |
| Resume PDF | `files/Bojian_Hou_Resume.pdf` |

## Adding a paper

Add an entry at the right place (newest first) in `_data/publications.yml` with `id`, `title`, `authors`
(exactly as published, `*` equal contribution, `†` corresponding), `venue`, `venue_group`, `year`, `tags`,
`selected`, `lead`, `links`, and `tldr`. For a thumbnail, add `_sources` (an arXiv id, a PDF URL, a PMC id or an
image URL) and run the site tools, or drop a 640×400 WebP into `images/pubs/<id>.webp` and set `teaser`.

## Site tools

`scripts/site_tools/` holds scripts that collect paper metadata, download PDFs, crop Figure 1 thumbnails,
check every publication link, and take screenshots. They run in GitHub Actions
(`.github/workflows/site-tools.yml`) from the Actions tab, or when a commit message on a non-`master` branch
contains `[tools]` or `[preview]`. Results are pushed to the `site-tools-output` and `site-preview-output` branches.

## Local preview

```
bundle install
bundle exec jekyll serve --config _config.yml,_config.dev.yml
```

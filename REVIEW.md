# Homepage redesign: review notes

Branch `redesign-2026`. Nothing here is live until this branch is merged into `master`.

## What changed

- **New look, same URLs.** `/`, `/publications/`, `/resume/`, `/services/`, `/awards/` keep their addresses; `/news/` is new. Old `/about/`, `/cv/` and `/publication/2017-SFL-IJCAI` redirect.
- **Homepage keeps the academic structure:** profile card and three-paragraph bio (based on the old About text), venues and recognition, five research areas with representative papers, nine selected publications, news (10 shown, "Show all" for the full history back to 2020), experience and education, honors, academic service.
- **Publications page:** 61 papers grouped by year, filterable by topic (All, Selected, Lead-authored, 8 topics). Filters are linkable, for example `/publications/#topic=llm`. Each paper has a Figure 1 thumbnail (or a figure chosen from the paper), a one-sentence summary, the venue, awards, and links.
- **Data files are the single source:** `_data/publications.yml`, `news.yml`, `awards.yml`, `service.yml`, `research.yml`, `topics.yml`, `site.yml`. To add a paper, add one entry to `publications.yml`; the homepage counts, filters and lists update themselves.
- **Removed AcademicPages leftovers:** sample posts, talks, teaching, portfolio, demo pages and images, `files/paper1-3.pdf`, the sample `_data/authors.yml`, the talkmap and markdown generator.
- **SEO:** real site description, Open Graph image, JSON-LD `Person`, page titles like "Publications | Bojian Hou". The dead `google-universal` analytics block is switched off.
- **Files:** `files/CCFAI'19.pdf` renamed to `files/CCFAI19.pdf` (apostrophes break links).

## Publications: decisions applied

- The list matches Google Scholar (one entry per paper; preprint and published versions merged), plus the CCFAI 2019 paper.
- Removed MentalGPT (AMIA 2024 abstract).
- Added 10 papers that are on Scholar but were not on the old site, with full author lists copied from the papers: npj Digital Medicine 2026 (CT VLM), arXiv 2026 (TAP-GPT multimodal), AMIA 2025 (Fair multi-modal CCA), IEEE TAI 2025 (ICAFS), Innovation in Aging 2025 (SDoH + EHR + KG), two ICCV 2025 workshop papers, two AIMedHealth 2025 papers, arXiv 2025 (RNA survey).
- Title corrections to the published versions: "Determining the Importance of Clinical Modalities ..." (AMIA Summit 2025), "... Alzheimer's Disease Subtype Discovery" (Medical Image Analysis 2024), "Learning Interpretability from RNN with Feature Changing" (CCFAI 2019).
- Author corrections from the papers: ISBI 2023 has "Hao Zheng" (not Hao Zhang); the DETR arXiv paper includes "Bohan Chen".
- Code and dataset links added where the paper's abstract states them (MentalChat16K dataset and code, FREEFORM, SDoHenPKG, DALK, GlaucomaNet, Manifoldron, TAP-GPT, FR-CCA-ADNI).
- Links fixed: legacy PMC PDF paths, an ACM link with a personal `casa_token`, `[PDF]` labels that pointed to arXiv pages, absolute `bojianhou.github.io` links.

## Please check

1. **Author lists you know better than the papers' metadata.** In particular the ICML 2025 paper: arXiv lists Qi Long before Weijie J. Su; the site keeps your old order (Weijie Su, Qi Long, Li Shen). Tell me which is right.
2. **Manifoldron (TNNLS 2024) and the quadratic-neuron autoencoder (TAI 2024):** the arXiv versions list extra authors (Zhen Jia, Boce Zhou; Xiaoge Zhang). The site keeps the author lists from your old page, which may match the published versions. Please confirm.
3. **Thumbnails.** All figures are cropped from the papers. A few use a figure other than Figure 1 because Figure 1 was a results table or a cohort flowchart; see `scripts/site_tools/teaser_overrides.yml`.
4. **One-sentence summaries** are paraphrased from each abstract (no numbers or claims beyond the abstract). Skim them on `/publications/`.
5. **Still without a public version:** MLMI 2026 (in press; shows "In press"). Fair multi-modal CCA (AMIA 2025) links to PubMed only.
6. **Chinese name.** The homepage shows "also published as Bo-Jian Hou · 侯博建" (the old sidebar already showed 侯博建). Remove it if you prefer.
7. **Links that block automated checkers** (ACM, OUP, medRxiv DOIs return 403 to bots). They open normally in a browser; the link report marks them "blocked", not broken.

## On Google Scholar itself (optional)

- Three AAIC abstracts are still listed (FR-CCA, Neural Additive DCSM, Interpretable DCSM risk groups).
- Duplicates to merge: the old-title ICLR 2025 preprint (2 entries, one with a garbled author field), an entry titled only "Uncertainty in Artificial Intelligence", and preprints of the BCB 2025, TAI 2024, TNNLS 2020, npj 2026 and ESN papers.
- Typo: "Prexdiction" in the TAP-GPT multimodal title.
- CCFAI 2019 is not on Scholar; add it to make the two lists identical.

## Maintenance tools

`scripts/site_tools/` (run by `.github/workflows/site-tools.yml`, never on `master`):

- `collect_metadata.py`: titles, authors and abstracts from arXiv, Europe PMC and Crossref.
- `fetch_pdfs.py` + `extract_teasers.py`: download each paper and crop its figure into `images/pubs/<id>.webp`.
- `check_links.py`: checks every publication link.
- `screens.mjs`: screenshots at desktop and phone widths in light and dark mode, plus filter and news checks.

Trigger from the Actions tab, or push a commit whose message contains `[tools]` or `[preview]` to any branch other than `master`. Results are pushed to the `site-tools-output` and `site-preview-output` branches.

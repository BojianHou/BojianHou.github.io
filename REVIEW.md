# Homepage redesign: review notes

First redesign merged in PR #1. Visual refresh (cards layout) on branch `visual-2026`.

## What changed

- **New look, same URLs.** `/`, `/publications/`, `/resume/`, `/services/`, `/awards/` keep their addresses; `/news/` is new. Old `/about/`, `/cv/` and `/publication/2017-SFL-IJCAI` redirect.
- **Homepage keeps the academic structure, laid out as cards:** intro with contact buttons, recent-paper figures, background, Published at (conferences and journals, no counts), news (latest 6, full list on /news/), honors, five research areas with representative papers, nine selected publications as figure cards, experience and education, academic service.
- **Publications page:** 61 papers grouped by year, filterable by topic (All, Selected, Lead-authored, 10 method topics; healthcare is an application domain, not a topic). Filters are linkable, for example `/publications/#topic=llm`. Each paper has an overview thumbnail (a method or framework figure from the paper, or a drawn overview when the paper has none), a one-sentence summary, the venue, awards, and links.
- **Data files are the single source:** `_data/publications.yml`, `news.yml`, `awards.yml`, `service.yml`, `research.yml`, `topics.yml`, `site.yml`. To add a paper, add one entry to `publications.yml`; the homepage counts, filters and lists update themselves.
- **Removed AcademicPages leftovers:** sample posts, talks, teaching, portfolio, demo pages and images, `files/paper1-3.pdf`, the sample `_data/authors.yml`, the talkmap and markdown generator.
- **Light/dark switch** in the header (saved per visitor); without a saved choice the site follows the system setting.
- **Favicon:** the bee B in `assets/favicon/`, also at `/favicon.ico`.
- **Fonts:** Geist (body) and Bricolage Grotesque (headings), both SIL Open Font License, self-hosted in `assets/fonts/`.
- **SEO:** real site description, Open Graph image, JSON-LD `Person`, page titles like "Publications | Bojian Hou". The dead `google-universal` analytics block is switched off.
- **Experience and education:** Meta (Monetization and MRS), Penn (Postdoctoral Fellow), Cornell (Postdoctoral Associate), 4Paradigm (Research Scientist), Nanjing University Ph.D. 2014 to 2020 and B.Sc. 2010 to 2014. The Background card mentions only Penn and Nanjing University.
- **Quality checks (latest preview build):** Jekyll builds cleanly with the GitHub Pages gem set; 125 publication links checked, 0 broken (10 publisher pages refuse bots and are marked "blocked"); no horizontal scrolling at 390 px; Lighthouse mobile: home 99 / 100 / 100 / 100, publications 97 / 100 / 100 / 100 (performance / accessibility / best practices / SEO). Fonts (Geist, SIL Open Font License) are self-hosted in `assets/fonts/`.
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

1. **Author lists changed to match the published versions** (your old page differed):
    - ICML 2025: PMLR lists "... Ruochen Jin, Qi Long, Weijie J. Su, Li Shen" (old page had Weijie Su before Qi Long).
    - IEEE TAI 2024: the published paper includes Xiaoge Zhang (5th author).
    - IEEE TNNLS 2024 (Manifoldron): the published paper includes Zhen Jia and Boce Zhang (Crossref spells "Boce Zhang"; arXiv spells "Boce Zhou").
    - Kunlun keeps "et al." after six authors (the paper has 28).
2. **Kunlun now links to the ACM DL page** (doi.org/10.1145/3770855.3818438) as well as arXiv.
3. **Thumbnails.** Each thumbnail should show what the paper does, not a result plot. Most are the paper's own method or framework figure (some are not Figure 1; see `scripts/site_tools/teaser_overrides.yml`). For 14 papers whose figures are all results, cohort or data plots, the thumbnail is an overview figure generated with PaperBanana (Gemini image model) from a method summary that paraphrases the abstract (`scripts/site_tools/paperbanana/papers.yml`); each was checked against its paper. Please check those 14 read correctly.
4. **One-sentence summaries** are paraphrased from each abstract (no numbers or claims beyond the abstract). Skim them on `/publications/`.
5. **Posters, slides and talk videos.** Linked where a copy exists: conference-hosted posters and slides (NeurIPS 2023/2024/2025, ICML 2025, ICLR 2025, AISTATS 2024) are copied into `files/posters/` and `files/slides/` (list in `scripts/site_tools/media.yml`), the AAAI 2021 poster comes from your computer, and two SlidesLive talk recordings are linked. Slides, Poster and Video links open in a new tab.
6. **MLMI 2026** links to the author PDF hosted at `/files/MLMI26-3D-VLM-report.pdf`. Fair multi-modal CCA (AMIA 2025) links to its PMC full text, with Figure 1 as the thumbnail.
7. **Chinese name.** The homepage shows "also published as Bo-Jian Hou · 侯博建" (the old sidebar already showed 侯博建). Remove it if you prefer.
8. **Links that block automated checkers** (ACM, OUP, medRxiv DOIs return 403 to bots). They open normally in a browser; the link report marks them "blocked", not broken.

## On Google Scholar itself (optional)

- Three AAIC abstracts are still listed (FR-CCA, Neural Additive DCSM, Interpretable DCSM risk groups).
- Duplicates to merge: the old-title ICLR 2025 preprint (2 entries, one with a garbled author field), an entry titled only "Uncertainty in Artificial Intelligence", and preprints of the BCB 2025, TAI 2024, TNNLS 2020, npj 2026 and ESN papers.
- Typo: "Prexdiction" in the TAP-GPT multimodal title.
- CCFAI 2019 is not on Scholar; add it to make the two lists identical.

## Maintenance tools

`scripts/site_tools/` (run by `.github/workflows/site-tools.yml`, never on `master`):

- `collect_metadata.py`: titles, authors and abstracts from arXiv, Europe PMC and Crossref.
- `fetch_pdfs.py` + `extract_teasers.py`: download each paper and crop its figure into `images/pubs/<id>.webp`.
- `paperbanana/`: method summaries, captions and palettes for PaperBanana; push with `[figs]` in the commit message (needs the `GEMINI_API_KEY` secret with billing enabled) and review the candidates on the branch `site-figs-output`.
- `check_links.py`: checks every publication link.
- `screens.mjs`: screenshots at desktop and phone widths in light and dark mode, plus filter and news checks.

Trigger from the Actions tab, or push a commit whose message contains `[tools]` or `[preview]` to any branch other than `master`. Results are pushed to the `site-tools-output` and `site-preview-output` branches.

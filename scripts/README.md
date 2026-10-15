Run from any directory:

```sh
python3 /path/to/thesis/scripts/prepare_arxiv.py
```

From the repository root, use `python3 scripts/prepare_arxiv.py`. Requires Python 3,
`pdflatex`, and `bibtex` (already available in the devcontainer; Python 3.9 or newer).

The script uses your saved working files, including uncommitted edits, and creates:

- `submission/arxiv/`: upload sources, with `main.tex` at the root.
- `submission/arxiv.zip`: the same files, ready to upload.
- `submission/arxiv-preview.pdf`: the PDF to review; excluded from the upload.

`submission/` uses the normal workspace storage, so these files are visible locally
as well as inside the devcontainer. The `build/` Docker volume stays available for
temporary compilation files.

Each successful run replaces these generated outputs. Original sources stay untouched.
Comments are stripped from TeX sources, preserving escaped `%`, URLs, and verbatim text.
Project `\newif` switches are resolved using `tex/config.sty` (false by default),
then declarations, setters, and the config package are removed. Commands in
`commands.sty` whose entire body is conditional are removed along with their calls
and arguments, regardless of their switch setting. Currently these are
`\editorial` and `\directorscut`. Unconditional commands such as `\tomyself` remain.

This deliberately handles this paper's boolean switches and `\newcommand` syntax,
rather than implementing a general TeX interpreter. Unsupported conditionals stop
the export. After cleaning, compilation records identify the required local files;
unused sections and figures are excluded. A freshly generated `main.bbl` is included,
so bibliography databases and standard TeX Live packages need not be uploaded.
The final bundle is compiled separately without BibTeX or shell escape.
For the paper's `alpha` bibliography style, the exported natbib package explicitly
uses numeric mode (which also supports alphabetic labels). This lets the supplied
`.bbl` compile on the first run without depending on a previous `.aux` file.

arXiv's [current pipeline](https://info.arxiv.org/help/submit_tex.html) accepts this
prebuilt bibliography; it also supports processing `.bib` files. No legacy
`\pdfoutput` workaround or manually generated `00README.json` is needed. Select
`main.tex` and PDFLaTeX in the submission interface.

Validation uses the installed TeX Live version, printed when the script starts.
The devcontainer currently uses TeX Live 2026; arXiv currently defaults to 2025 and
also offers 2023. Its [TeX Live notes](https://info.arxiv.org/help/faq/texlive.html)
describe a `cleveref` issue under 2025 relevant to this paper's theorem names.
Review the PDF produced by arXiv too; choose 2023 if affected. The script keeps the
paper's existing typography and date settings.

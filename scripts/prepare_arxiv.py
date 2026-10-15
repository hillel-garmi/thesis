#!/usr/bin/env python3
"""Export this paper with Python 3, pdflatex and BibTeX; see scripts/README.md."""

from pathlib import Path
import re
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tex"
OUTPUT = ROOT / "submission"
DEFINITIONS = {r"\newcommand", r"\renewcommand", r"\providecommand"}
CONTROL_WORD = re.compile(r"\\[A-Za-z@]+\Z")
# Keep verbatim spans and escaped characters intact; comments consume the newline.
TOKEN = re.compile(
    r"\\begin\{(verbatim\*?|lstlisting|minted)\}.*?\\end\{\1\}"
    r"|\\(?:url|path|href)\{(?:\\.|[^}])*\}"
    r"|\\verb(?![A-Za-z@])\*?([^\n]).*?\2|\\[A-Za-z@]+|\\[^\n]"
    r"|%[^\n]*(?:\n[ \t]*|$)|.", re.DOTALL
)


def tokenize(text):
    return [match[0] for match in TOKEN.finditer(text) if not match[0].startswith("%")]


def render(tokens):
    # Deleting a comment or command must not turn '\\alpha' + 'x' into '\\alphax'.
    return "".join(
        token + (" " if CONTROL_WORD.fullmatch(token)
                 and (following.isalpha() or following == "@") else "")
        for token, following in zip(tokens, tokens[1:] + [""])
    )


def skip_space(tokens, index):
    while index < len(tokens) and tokens[index].isspace():
        index += 1
    return index


def argument(tokens, index, opening="{", closing="}"):
    """Read one balanced argument; escaped braces are already separate tokens."""
    index = skip_space(tokens, index)
    if index == len(tokens):
        raise ValueError("Missing TeX argument")
    if tokens[index] != opening:
        return [tokens[index]], index + 1
    start, depth = index + 1, 1
    for end in range(start, len(tokens)):
        depth += (tokens[end] == opening) - (tokens[end] == closing)
        if depth == 0:
            return tokens[start:end], end + 1
    raise ValueError("Unclosed TeX argument")


def definition(tokens, index):
    index = skip_space(tokens, index + 1)
    if tokens[index] == "*":
        index += 1
    name, index = argument(tokens, index)
    index = skip_space(tokens, index)
    count = 0
    if tokens[index] == "[":
        count, index = argument(tokens, index, "[", "]")
        count = int("".join(count))
    index = skip_space(tokens, index)
    optional = tokens[index] == "["
    if optional:
        _, index = argument(tokens, index, "[", "]")
    body, end = argument(tokens, index)
    return "".join(name), count, optional, body, end


def conditional(tokens, index, switches):
    """Split a switch into its true/false branches, respecting nested switches."""
    yes, no = [], []
    branch, depth = yes, 1
    for end in range(index + 1, len(tokens)):
        token = tokens[end]
        if token in switches:
            depth += 1
        elif token == r"\fi":
            depth -= 1
            if depth == 0:
                return yes, no, end + 1
        elif token == r"\else" and depth == 1:
            branch = no
            continue
        branch.append(token)
    raise ValueError(f"Unclosed conditional: {tokens[index]}")


def guarded_commands(tokens, switches):
    """Find commands whose whole body is one conditional block."""
    removed = {}
    for index, token in enumerate(tokens):
        if token not in DEFINITIONS:
            continue
        name, count, optional, body, _ = definition(tokens, index)
        body = tokenize(render(body).strip())
        if body and body[0] in switches:
            _, _, end = conditional(body, 0, switches)
            if end == len(body):
                if optional:
                    raise ValueError(f"Guarded command with optional arguments: {name}")
                removed[name] = count
    return removed


def clean(tokens, switches, removed):
    result, index = [], 0
    setters = {
        name[3:] + suffix: (name, value)
        for name in switches if name not in (r"\iftrue", r"\iffalse")
        for suffix, value in (("true", True), ("false", False))
    }
    setters = {"\\" + name: setting for name, setting in setters.items()}
    while index < len(tokens):
        token = tokens[index]
        if token == r"\newif":
            _, index = argument(tokens, index + 1)
        elif token in DEFINITIONS and definition(tokens, index)[0] in removed:
            index = definition(tokens, index)[4]
        elif token in removed:
            index += 1
            for _ in range(removed[token]):
                _, index = argument(tokens, index)
        elif token == r"\usepackage":
            packages, end = argument(tokens, index + 1)
            if render(packages) == "config":
                index = end
            else:
                result.append(token)
                index += 1
        elif token in setters:
            name, value = setters[token]
            switches[name] = value
            index += 1
        elif token in switches:
            yes, no, end = conditional(tokens, index, switches)
            result.extend(clean(yes if switches[token] else no, switches, removed))
            index = end
        elif re.fullmatch(r"\\if[A-Za-z@]*|\\(?:else|fi|or)", token):
            raise ValueError(f"Unsupported conditional syntax: {token}")
        else:
            result.append(token)
            index += 1
    return result


def run(command, directory):
    completed = subprocess.run(command, cwd=directory, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if completed.returncode:
        raise RuntimeError(f"{' '.join(command)} failed:\n{completed.stdout[-6000:]}")


def build(directory, bibliography=False):
    latex = ["pdflatex", "-no-shell-escape", "-interaction=nonstopmode",
             "-halt-on-error", "-recorder", "main.tex"]
    run(latex, directory)
    if bibliography and r"\bibdata{" in (directory / "main.aux").read_text():
        run(["bibtex", "main"], directory)
    run(latex, directory)
    run(latex, directory)
    log = (directory / "main.log").read_text(errors="replace")
    if re.search(r"(?:Citation|Reference) .* undefined|There were undefined|multiply-defined", log):
        raise ValueError("The exported paper has unresolved citations/references; inspect the source.")
    for line in (directory / "main.fls").read_text().splitlines():
        if line.startswith("INPUT ") and (directory / line[6:]).resolve().is_relative_to(ROOT):
            raise ValueError(f"Build reached outside its temporary folder: {line[6:]}")


def main():
    compiler = subprocess.check_output(["pdflatex", "--version"], text=True).splitlines()[0]
    print(f"Local compiler: {compiler}", flush=True)
    with tempfile.TemporaryDirectory(prefix="arxiv-") as temporary:
        temporary = Path(temporary)
        stage, package = temporary / "source", temporary / "arxiv"
        shutil.copytree(SOURCE, stage, ignore=shutil.ignore_patterns(
            "config.sty", "main.pdf", "*.aux", "*.log", "*.bbl", "*.blg", "*.fls",
            "*.fdb_latexmk", "*.synctex.gz", "*.toc", "*.out", "*.bcf", "*.run.xml"
        ))
        sources = {path: tokenize(path.read_text()) for path in stage.rglob("*")
                   if path.suffix in {".tex", ".sty", ".cls"}}
        switches = {r"\iftrue": True, r"\iffalse": False}
        for tokens in sources.values():
            for index, token in enumerate(tokens):
                if token == r"\newif":
                    switches[tokens[skip_space(tokens, index + 1)]] = False
        config = SOURCE / "config.sty"
        if config.exists():
            clean(tokenize(config.read_text()), switches, {})
        removed = guarded_commands(sources[stage / "commands.sty"], switches)
        alpha_style = r"\bibliographystyle{alpha}" in render(sources[stage / "main.tex"])
        for path, tokens in sources.items():
            text = render(clean(tokens, switches.copy(), removed))
            if alpha_style:
                # Without an old .aux, natbib otherwise assumes author-year labels.
                text = text.replace(r"\usepackage{natbib}", r"\usepackage[numbers]{natbib}")
            path.write_text(re.sub(r"\n[ \t]*\n(?:[ \t]*\n)+", "\n\n", text).strip() + "\n")
        original_files = {path.resolve() for path in stage.rglob("*") if path.is_file()}
        print("Building cleaned sources and bibliography…", flush=True)
        build(stage, bibliography=True)
        used = {stage / "main.bbl"} if (stage / "main.bbl").exists() else set()
        for line in (stage / "main.fls").read_text().splitlines():
            if line.startswith("INPUT "):
                path = (stage / line[6:]).resolve()
                if path in original_files:
                    used.add(path)
        for path in sorted(used):
            relative = path.relative_to(stage)
            if not re.fullmatch(r"[A-Za-z0-9_+.,=/\-]+", relative.as_posix()):
                raise ValueError(f"Filename unsupported by arXiv: {relative}")
            destination = package / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix == ".bbl":
                destination.write_text(render(tokenize(path.read_text())))
            else:
                shutil.copy2(path, destination)
        print("Checking the exported folder independently…", flush=True)
        check = temporary / "check"
        shutil.copytree(package, check)
        build(check)
        OUTPUT.mkdir(exist_ok=True)
        destination = OUTPUT / "arxiv"
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(package, destination)
        shutil.make_archive(str(destination), "zip", package)
        shutil.copy2(check / "main.pdf", OUTPUT / "arxiv-preview.pdf")
        print(f"Created {destination} ({len(used)} files), {destination}.zip, and arxiv-preview.pdf")
        print(f"Removed guarded commands: {', '.join(sorted(removed))}")


if __name__ == "__main__":
    main()

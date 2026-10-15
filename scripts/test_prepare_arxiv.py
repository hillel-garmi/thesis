"""Focused regression tests for the submission source transformations."""

import unittest

from prepare_arxiv import clean, guarded_commands, render, tokenize


class SourceCleaningTests(unittest.TestCase):
    def setUp(self):
        self.switches = {
            r"\iftrue": True,
            r"\iffalse": False,
            r"\ifeditorial": False,
            r"\ifdirectorscut": True,
        }

    def cleaned(self, text, removed=None):
        return render(clean(tokenize(text), self.switches, removed or {}))

    def test_nested_conditionals_select_content(self):
        source = (r"A\ifeditorial hidden\else visible"
                  r"\ifdirectorscut extended\else short\fi\fi Z")
        self.assertEqual(self.cleaned(source), "A visible extended Z")

    def test_declarations_and_config_setters_disappear(self):
        clean(tokenize(r"\editorialtrue\directorscutfalse"), self.switches, {})
        source = (r"\newif\ifeditorial\newif\ifdirectorscut"
                  r"\usepackage{config}"
                  r"\ifeditorial included\fi"
                  r"\ifdirectorscut hidden\else concise\fi")
        self.assertEqual(self.cleaned(source), " included concise")

    def test_guarded_definitions_and_nested_arguments_disappear(self):
        source = (r"\newcommand{\editorial}[1]{\ifeditorial #1\fi}"
                  r"\newcommand*\draftpair[2]{\ifdirectorscut #1 #2\else\fi}"
                  r"\newcommand{\keep}[1]{Visible #1}"
                  r"A\editorial{hidden {nested} \{braces\}}"
                  r"\draftpair{first}{second {nested}}B")
        tokens = tokenize(source)
        removed = guarded_commands(tokens, self.switches)
        self.assertEqual(removed, {r"\editorial": 1, r"\draftpair": 2})
        self.assertEqual(render(clean(tokens, self.switches, removed)),
                         r"\newcommand{\keep}[1]{Visible #1}AB")

    def test_partially_guarded_command_is_preserved(self):
        source = r"\newcommand{\keep}[1]{Visible\ifeditorial #1\fi}"
        self.assertEqual(guarded_commands(tokenize(source), self.switches), {})
        self.assertEqual(self.cleaned(source), r"\newcommand{\keep}[1]{Visible}")

    def test_comments_escaped_percent_and_control_word_boundaries(self):
        source = "before% comment\n  after \\% kept \\alpha% comment\nx\n"
        self.assertEqual(self.cleaned(source), "beforeafter \\% kept \\alpha x\n")
        self.assertEqual(self.cleaned("\\\\% comment\nend"), r"\\end")

    def test_removed_macro_cannot_merge_control_word_with_text(self):
        self.assertEqual(self.cleaned(r"\alpha\editorial{hidden}x", {r"\editorial": 1}),
                         r"\alpha x")

    def test_verbatim_is_preserved(self):
        for source in (r"\verb|% \ifeditorial secret\fi|",
                       r"\verb*+% text+",
                       "\\begin{verbatim}\n% literal\\ifeditorial X\\fi\n\\end{verbatim}",
                       "\\begin{lstlisting}\n% literal\n\\end{lstlisting}",
                       "\\begin{minted}{python}\n% literal\n\\end{minted}"):
            with self.subTest(source=source):
                self.assertEqual(self.cleaned(source), source)

    def test_percent_encoded_url_is_not_a_comment(self):
        url = r"\url{https://example.org/?x=%7B1%7D}"
        self.assertEqual(self.cleaned(url + "% actual comment\n  after"), url + "after")

    def test_verb_prefix_does_not_capture_longer_commands(self):
        self.assertEqual(tokenize(r"\verbatiminput{data}")[0], r"\verbatiminput")

    def test_unsupported_or_unbalanced_conditionals_fail(self):
        for source in (r"\ifnum1=1 text\fi", r"\ifeditorial text", r"\else", r"\fi"):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    self.cleaned(source)

    def test_optional_guarded_arguments_fail_clearly(self):
        source = r"\newcommand{\editorial}[1][default]{\ifeditorial #1\fi}"
        with self.assertRaisesRegex(ValueError, "optional arguments"):
            guarded_commands(tokenize(source), self.switches)


if __name__ == "__main__":
    unittest.main()

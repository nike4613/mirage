"""HTML and Markdown processing tools."""

import re

import html_sanitizer.sanitizer as sanitizer
import mistune
from html_sanitizer.sanitizer import Sanitizer
from lxml.html import HtmlElement  # nosec


class MarkdownInlineGrammar(mistune.InlineGrammar):
    """Markdown inline elements syntax modifications for the Mistune parser.

    Modifications:

    - Disable underscores for bold/italics (e.g. `__bold__`)
    """

    emphasis        = re.compile(r"^\*((?:\*\*|[^\*])+?)\*(?!\*)")
    double_emphasis = re.compile(r"^\*{2}([\s\S]+?)\*{2}(?!\*)")


class MarkdownInlineLexer(mistune.InlineLexer):
    """Apply the changes from `MarkdownInlineGrammar` for Mistune."""

    grammar_class = MarkdownInlineGrammar


    def output_double_emphasis(self, m):
        return self.renderer.double_emphasis(self.output(m.group(1)))


    def output_emphasis(self, m):
        return self.renderer.emphasis(self.output(m.group(1)))


class HTMLProcessor:
    """Provide HTML filtering and conversion from Markdown.

    Filtering sanitizes HTML and ensures it complies with the supported Qt
    subset for usage in QML: https://doc.qt.io/qt-5/richtext-html-subset.html

    Some methods take an `outgoing` argument, specifying if the HTML is
    intended to be sent to matrix servers or used locally in our application.

    For local usage, extra transformations are applied:

    - Wrap text lines starting with a `>` in `<span>` with a `quote` class.
      This allows them to be styled appropriately from QML.

    Some methods have `inline` counterparts, which return text appropriate
    for UI elements restricted to display a single line, e.g. the room
    last message subtitles in QML or notifications.
    In inline filtered HTML, block tags are stripped or substituted and
    newlines are turned into ⏎ symbols (U+23CE).
    """

    inline_tags = {"font", "a", "sup", "sub", "b", "i", "s", "u", "code"}

    block_tags = {
        "h1", "h2", "h3", "h4", "h5", "h6","blockquote",
        "p", "ul", "ol", "li", "hr", "br",
        "table", "thead", "tbody", "tr", "th", "td", "pre",
    }

    link_regexes = [re.compile(r, re.IGNORECASE) for r in [
        (r"(?P<body>[a-zA-Z\d]+://(?P<host>[a-z\d._-]+(?:\:\d+)?)"
         r"(?:/[/\-_.,a-z\d#%&?;=~]*)?(?:\([/\-_.,a-z\d#%&?;=~]*\))?)"),
        r"mailto:(?P<body>[a-z0-9._-]+@(?P<host>[a-z0-9_.-]+[a-z](?:\:\d+)?))",
        r"tel:(?P<body>[0-9+-]+)(?P<host>)",
        r"(?P<body>magnet:\?xt=urn:[a-z0-9]+:.+)(?P<host>)",
    ]]

    inline_quote_regex = re.compile(r"(^|⏎)(\s*&gt;[^⏎\n]*)", re.MULTILINE)

    quote_regex = re.compile(
        r"(^|<p/?>|<br/?>|<h\d/?>)(\s*&gt;.*?)(</?p>|<br/?>|</?h\d>|$)",
        re.MULTILINE,
    )

    extra_newlines_regex = re.compile(r"\n(\n*)")


    def __init__(self) -> None:
        self._sanitizer        = Sanitizer(self.sanitize_settings())
        self._inline_sanitizer = Sanitizer(self.sanitize_settings(inline=True))

        # The whitespace remover doesn't take <pre> into account
        sanitizer.normalize_overall_whitespace = lambda html, *args, **kw: html
        sanitizer.normalize_whitespace_in_text_or_tail = \
            lambda el, *args, **kw: el

        # hard_wrap: convert all \n to <br> without required two spaces
        # escape: escape HTML characters in the input string, e.g. tags
        self._markdown_to_html = mistune.Markdown(
            hard_wrap=True, escape=True, inline=MarkdownInlineLexer,
        )

        self._markdown_to_html.block.default_rules = [
            rule for rule in self._markdown_to_html.block.default_rules
            if rule != "block_quote"
        ]


    def from_markdown(self, text: str, outgoing: bool = False) -> str:
        """Return filtered HTML from Markdown text."""

        return self.filter(self._markdown_to_html(text), outgoing)


    def from_markdown_inline(self, text: str, outgoing: bool = False) -> str:
        """Return single-line filtered HTML from Markdown text."""

        return self.filter_inline(self._markdown_to_html(text), outgoing)


    def filter_inline(self, html: str, outgoing: bool = False) -> str:
        """Filter and return HTML with block tags stripped or substituted."""

        html = self._inline_sanitizer.sanitize(html)

        if outgoing:
            return html

        # Client-side modifications
        return self.inline_quote_regex.sub(
            r'\1<span class="quote">\2</span>', html,
        )


    def filter(self, html: str, outgoing: bool = False) -> str:
        """Filter and return HTML."""

        html = self._sanitizer.sanitize(html).rstrip("\n")

        if outgoing:
            return html

        return self.quote_regex.sub(r'\1<span class="quote">\2</span>\3', html)


    def sanitize_settings(self, inline: bool = False) -> dict:
        """Return an html_sanitizer configuration."""

        # https://matrix.org/docs/spec/client_server/latest#m-room-message-msgtypes
        # TODO: mx-reply and the new hidden thing

        inline_tags = self.inline_tags
        all_tags    = inline_tags | self.block_tags

        inlines_attributes = {
            "font": {"color"},
            "a":    {"href"},
            "code": {"class"},
        }
        attributes = {**inlines_attributes, **{
            "ol":   {"start"},
            "hr":   {"width"},
        }}

        return {
            "tags": inline_tags if inline else all_tags,
            "attributes": inlines_attributes if inline else attributes,
            "empty": {} if inline else {"hr", "br"},
            "separate": {"a"} if inline else {
                "a", "p", "li", "table", "tr", "th", "td", "br", "hr",
            },
            "whitespace": {},
            "keep_typographic_whitespace": True,
            "add_nofollow": False,
            "autolink": {
                "link_regexes": self.link_regexes,
                "avoid_hosts": [],
            },
            "sanitize_href": lambda href: href,
            "element_preprocessors": [
                sanitizer.bold_span_to_strong,
                sanitizer.italic_span_to_em,
                sanitizer.tag_replacer("strong", "b"),
                sanitizer.tag_replacer("em", "i"),
                sanitizer.tag_replacer("strike", "s"),
                sanitizer.tag_replacer("del", "s"),
                sanitizer.tag_replacer("form", "p"),
                sanitizer.tag_replacer("div", "p"),
                sanitizer.tag_replacer("caption", "p"),
                sanitizer.target_blank_noopener,
                self._process_span_font,
                self._img_to_a,
                self._remove_extra_newlines,
                self._newlines_to_return_symbol if inline else lambda el: el,
            ],
            "element_postprocessors": [],
            "is_mergeable": lambda e1, e2: e1.attrib == e2.attrib,
        }


    @staticmethod
    def _process_span_font(el: HtmlElement) -> HtmlElement:
        """Convert HTML `<span data-mx-color=...` to `<font color=...>`."""

        if el.tag not in ("span", "font"):
            return el

        color = el.attrib.pop("data-mx-color", None)
        if color:
            el.tag = "font"
            el.attrib["color"] = color

        return el


    @staticmethod
    def _img_to_a(el: HtmlElement) -> HtmlElement:
        """Linkify images by wrapping `<img>` tags in `<a>`."""

        if el.tag == "img":
            el.tag            = "a"
            el.attrib["href"] = el.attrib.pop("src", "")
            el.text           = el.attrib.pop("alt", None) or el.attrib["href"]

        return el


    def _remove_extra_newlines(self, el: HtmlElement) -> HtmlElement:
        """Remove excess `\\n` characters from non-`<pre>` HTML elements.

        This is done to avoid additional blank lines when the CSS directive
        `white-space: pre` is used.
        """

        pre_parent = any(parent.tag == "pre" for parent in el.iterancestors())

        if el.tag != "pre" and not pre_parent:
            if el.text:
                el.text = self.extra_newlines_regex.sub(r"\1", el.text)
            if el.tail:
                el.tail = self.extra_newlines_regex.sub(r"\1", el.tail)

        return el


    def _newlines_to_return_symbol(self, el: HtmlElement) -> HtmlElement:
        """Turn newlines into unicode return symbols (⏎, U+23CE).

        The symbol is added to blocks with siblings (e.g. a `<p>` followed by
        another `<p>`) and `<br>` tags.
        The `<br>` themselves will be removed by the inline sanitizer.
        """

        is_block_with_siblings = (el.tag in self.block_tags and
                                  next(el.itersiblings(), None) is not None)

        if el.tag == "br" or is_block_with_siblings:
            el.tail = f" ⏎ {el.tail or ''}"


        # Replace left \n in text/tail of <pre> content by the return symbol.
        if el.text:
            el.text = re.sub(r"\n", r" ⏎ ", el.text)

        if el.tail:
            el.tail = re.sub(r"\n", r" ⏎ ", el.tail)

        return el


HTML_PROCESSOR = HTMLProcessor()
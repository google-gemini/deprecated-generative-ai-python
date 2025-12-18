import re

project = 'Google Generative AI - Python'
copyright = '2024, Google LLC'
author = 'Google LLC'

extensions = [
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.coverage',
    'myst_parser',
    'sphinx.ext.viewcode',
    'sphinx.ext.githubpages',
    ]

# autosectionlabel_prefix_document = True

myst_url_schemes = ["http", "https", "mailto"]
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "fieldlist",
    "html_image",
    "replacements",
    "smartquotes",
    "strikethrough",
    "tasklist",
    "substitution",
    "linkify",
]
# https://myst-parser.readthedocs.io/en/latest/syntax/optional.html#syntax-header-anchors
# Controls allowable header anchors in markdown files. Value allows header anchors for h1 - h6
myst_heading_anchors = 6
suppress_warnings = ["myst.xref_missing", "myst.iref_ambiguous"]

source_suffix = {'.md': 'markdown',}
master_doc = 'index' #'api/google/generativeai'

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'alabaster'
# html_static_path = ['_static']


def set_relative_links(app, docname, source):
    source[0] = source[0].replace(
        '../google/generativeai/',
        '/api/google/generativeai/'
    )

def replace_md_links(app, pagename, templatename, context, doctree):
    """Replaces all .md links with .html in the final HTML output."""
    if 'body' in context:
        # Pattern to identify and replace <a href="*.md#anchor"> links
        pattern = re.compile(r'<a href="([^"]+)\.md(#[^"]*)?">')
        
        # Function to replace matched .md links with .html links
        def md_to_html(match):
            # Get the base link and optional fragment
            base_link = match.group(1)
            fragment = match.group(2) or ""
            # Replace .md with .html and retain the fragment if present
            return f'<a href="/generative-ai-python{base_link}.html{fragment}" class="reference internal">'

        # Apply the replacement to all <a> links in the HTML body
        context['body'] = pattern.sub(md_to_html, context['body'])

def setup(app):
    app.connect('html-page-context', replace_md_links)
    app.connect('source-read', set_relative_links)

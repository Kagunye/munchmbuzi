from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def rich_text(value):
    """Tiny, safe formatter for news posts.

    Blank line = new paragraph, '## ' = heading, '- ' lines = bullet list.
    All text is HTML-escaped first, so admins can't inject markup by accident.
    """
    html = []
    for block in str(value).replace("\r\n", "\n").split("\n\n"):
        lines = [ln.rstrip() for ln in block.strip().split("\n") if ln.strip()]
        if not lines:
            continue
        buf, items = [], []

        def flush_para():
            if buf:
                html.append("<p>" + "<br>".join(escape(x) for x in buf) + "</p>")
                buf.clear()

        def flush_list():
            if items:
                html.append("<ul>" + "".join(f"<li>{escape(x)}</li>" for x in items) + "</ul>")
                items.clear()

        for ln in lines:
            if ln.startswith("## "):
                flush_para(); flush_list()
                html.append(f"<h2>{escape(ln[3:])}</h2>")
            elif ln.lstrip().startswith(("- ", "• ")):
                flush_para()
                items.append(ln.lstrip()[2:])
            else:
                flush_list()
                buf.append(ln)
        flush_para(); flush_list()
    return mark_safe("\n".join(html))

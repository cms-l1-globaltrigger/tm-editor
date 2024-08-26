"""This module provides functions to construct valid HTML tags.

>>> from html import p, a
>>> doc = p(["Hello ", a("World", href="https://cern.ch/")], id="root")
>>> print(doc)
'<p>Hello <a href="https://cern.ch/">World</a></p>'

"""

from collections.abc import Iterable

__all__ = ["a", "code", "h1", "h2", "h3", "h4", "h5", "li", "ol", "p", "pre", "span", "strong", "ul"]


def tag_factory(tag):
    def tag_func(children=None, **attrs):
        if isinstance(children, (str, bytes, bytearray)):
            f_children = format(children)
        elif isinstance(children, Iterable):
            f_children = " ".join([format(child) for child in children or []])
        else:
            f_children = format(children)
        f_attrs = " ".join([f"{key}=\"{value}\"" for key, value in attrs.items()])
        f_attrs = f" {f_attrs}" if f_attrs else ""
        if f_children:
            return f"<{tag}{f_attrs}>{f_children}</{tag}>"
        else:
            return f"<{tag}{f_attrs}/>"
    return tag_func


a = tag_factory("a")
code = tag_factory("code")
h1 = tag_factory("h1")
h2 = tag_factory("h2")
h3 = tag_factory("h3")
h4 = tag_factory("h4")
h5 = tag_factory("h5")
li = tag_factory("li")
ol = tag_factory("ol")
p = tag_factory("p")
pre = tag_factory("pre")
span = tag_factory("span")
strong = tag_factory("strong")
ul = tag_factory("ul")

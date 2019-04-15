"""Common information so that all traceback generating scripts
   create files in the same format.

"""
import sys
from contextlib import redirect_stderr

import friendly_traceback


def write(text):
    sys.stderr.write(text + "\n")


def make_title(text):
    write("\n" + text)
    write("-" * len(text) + "\n")
    write(".. code-block:: none\n")


all_imports = {
    "IndentationError - 1: expected an indented block": "syntax.raise_indentation_error1",
    "IndentationError - 2: unexpected indent": "syntax.raise_indentation_error2",
    "IndentationError - 3: unindent does not match ...": "syntax.raise_indentation_error3",
    "NameError": ("test_name_error", "test_name_error"),
    "SyntaxError": "syntax.raise_syntax_error1",
    "TabError - 1": ("syntax.raise_tab_error1", "raise_tab_error1"),
    "TabError - 2": "syntax.raise_tab_error2",
    "UnboundLocalError": ("test_unbound_local_error", "test_unbound_local_error"),
    "Unknown exception": ("test_unknown_error", "test_unknown_error"),
    "ZeroDivisionError - 1": ("test_zero_division_error", "test_zero_division_error"),
    "ZeroDivisionError - 2": ("test_zero_division_error", "test_zero_division_error2"),
}


def create_tracebacks(target, intro_text):
    with open(target, "w", encoding="utf8") as out:
        with redirect_stderr(out):
            write(intro_text)

            for title in all_imports:
                function = None
                if isinstance(all_imports[title], tuple):
                    name, function = all_imports[title]
                else:
                    name = all_imports[title]
                make_title(title)
                try:
                    mod = __import__(name)
                    if function is not None:
                        result = getattr(mod, function)()
                        write(result)
                except Exception:
                    friendly_traceback.explain(*sys.exc_info(), redirect=None)
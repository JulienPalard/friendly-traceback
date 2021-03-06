"""This module contains functions that are used to
   analyze a single line of code which has been identified
   as containing a syntax error with the message "invalid syntax".
"""
from keyword import kwlist
import sys
import tokenize


from .my_gettext import current_lang
from . import utils
from .friendly_exception import FriendlyException


def count_char(tokens, char):
    """Counts how many times a given character appears in a list of tokens"""
    return sum(1 for token in tokens if token.string == char)


def is_potential_statement(tokens):
    """This helper function tests the list of tokens
       (usually corresponding to a single line of code)
       and returns True if the corresponding line of code could possibly be a
       complete Python statement as described below.

       A complete Python statement would have brackets,
       including (), [], and {}, matched in pairs,
       and would not end with the continuation character \\
    """
    line = tokens[0].line

    # All tokens passed should come from the same line of code
    if tokens[-1].line != line:
        raise FriendlyException("line_analyzer.is_potential_statement")

    if line.endswith("\\"):
        return False

    return (
        (count_char(tokens, "(") == count_char(tokens, ")"))
        and (count_char(tokens, "[") == count_char(tokens, "]"))
        and (count_char(tokens, "{") == count_char(tokens, "}"))
    )


LINE_ANALYZERS = []


def add_line_analyzer(func):
    """A simple decorator that adds a function to the list
       of all functions that analyze a single line of code."""
    LINE_ANALYZERS.append(func)

    def wrapper(tokens):
        return func(tokens)

    return wrapper


# ========================================================
# Main calling function
# ========================================================


def analyze_last_line(line):
    """Analyzes the last line of code as identified by Python as that
       on which the error occurred."""
    tokens = utils.tokenize_source(line)  # tokens do not include spaces nor comments

    if not tokens:
        return

    for analyzer in LINE_ANALYZERS:
        cause = analyzer(tokens)
        if cause:
            return cause
    return


# ==================
# IMPORTANT: causes are looked at in the same order as they appear below.
# Changing the order can yield incorrect results
# ==================


@add_line_analyzer
def detect_walrus(tokens):
    """Detecting if code uses named assignment operator := with an
       older version of Python.
    """
    _ = current_lang.translate
    if sys.version_info >= (3, 8):
        return False

    found_colon = False
    for token in tokens:
        if found_colon and token.string == "=":
            return _(
                "You appear to be using the operator :=, sometimes called\n"
                "the walrus operator. This operator requires the use of\n"
                "Python 3.8 or newer. You are using version {version}.\n"
            ).format(version=f"{sys.version_info.major}.{sys.version_info.minor}")

        found_colon = token.string == ":"


@add_line_analyzer
def detect_backquote(tokens):
    """Detecting if the error is due to using `x` which was allowed
       in Python 2.
    """
    _ = current_lang.translate
    for token in tokens:
        if token.string == "`":
            return _(
                "You are using the backquote character `.\n"
                "This was allowed in Python 2 but is no longer allowed.\n"
                "Use the function repr(x) instead of `x`."
            )


@add_line_analyzer
def assign_to_a_keyword(tokens):
    """Checks to see if line is of the form 'keyword = ...'
    """
    _ = current_lang.translate
    if len(tokens) < 2 or (tokens[0].string not in kwlist) or tokens[1].string != "=":
        return False

    return _(
        "You were trying to assign a value to the Python keyword '{keyword}'.\n"
        "This is not allowed.\n"
        "\n"
    ).format(keyword=tokens[0].string)


@add_line_analyzer
def confused_elif(tokens):
    _ = current_lang.translate
    name = None
    if tokens[0].string == "elseif":
        name = "elseif"
    elif tokens[0].string == "else" and len(tokens) > 1 and tokens[1].string == "if":
        name = "else if"
    if name:
        return _(
            "You meant to use Python's 'elif' keyword\n"
            "but wrote '{name}' instead\n"
            "\n"
        ).format(name=name)


@add_line_analyzer
def import_from(tokens):
    _ = current_lang.translate
    if len(tokens) < 4:
        return
    if tokens[0].string != "import":
        return
    third = tokens[2].string
    if third == "from":
        function = tokens[1].string
        module = tokens[3].string

        return _(
            "You wrote something like\n"
            "    import {function} from {module}\n"
            "instead of\n"
            "    from {module} import {function}\n"
            "\n"
        ).format(module=module, function=function)


@add_line_analyzer
def keyword_as_attribute(tokens):
    """Will identify something like  obj.True ..."""
    _ = current_lang.translate
    prev_word = None
    for token in tokens:
        word = token.string
        if prev_word == ".":
            if word in kwlist:
                return _(
                    "You cannot use the Python keyword {word} as an attribute.\n\n"
                ).format(word=word)
            elif word == "__debug__":
                return _("You cannot use the constant __debug__ as an attribute.\n\n")
        else:
            prev_word = word


@add_line_analyzer
def misplaced_quote(tokens):
    """This looks for a misplaced quote, something like
       info = 'don't' ...

    The clue we are looking for is a STRING token ('don')
    followed by a NAME token (t).
    """
    _ = current_lang.translate
    if len(tokens) < 2:
        return
    prev = tokens[0]
    for token in tokens:
        if prev.type == tokenize.STRING and token.type == tokenize.NAME:
            return _(
                "There appears to be a Python identifier (variable name)\n"
                "immediately following a string.\n"
                "I suspect that you were trying to use a quote inside a string\n"
                "that was enclosed in quotes of the same kind.\n"
            )
        prev = token


@add_line_analyzer
def missing_colon(tokens):
    """look for missing colon at the end of statement"""
    _ = current_lang.translate

    if tokens[-1].string == ":":
        return

    if not is_potential_statement(tokens):
        return

    name = tokens[0].string

    if name == "class":
        name = _("a class")
        return _(
            "You wanted to define {class_}\n"
            "but forgot to add a colon ':' at the end\n"
            "\n"
        ).format(class_=name)
    elif name in ["for", "while"]:
        return _(
            "You wrote a '{for_while}' loop but\n"
            "forgot to add a colon ':' at the end\n"
            "\n"
        ).format(for_while=name)
    elif name in ["def", "elif", "else", "except", "finally", "if", "try"]:
        return _(
            "You wrote a statement beginning with\n"
            "'{name}' but forgot to add a colon ':' at the end\n"
            "\n"
        ).format(name=name)


@add_line_analyzer
def malformed_def(tokens):
    """Looks for problems with defining a function, assuming that
       the information passed looks like a complete statement"""
    _ = current_lang.translate
    if tokens[0].string != "def":
        return False

    if not is_potential_statement(tokens):
        return

    # need at least five tokens: def name ( ) :
    if (
        len(tokens) < 5
        or tokens[1].type != tokenize.NAME
        or tokens[2].string != "("
        or tokens[-2].string != ")"
        or tokens[-1].string != ":"
    ):
        name = _("a function or method")
        return _(
            "You tried to define {class_or_function} "
            "and did not use the correct syntax.\n"
            "The correct syntax is:\n"
            "    def name ( optional_arguments ):"
            "\n"
        ).format(class_or_function=name)
    fn_name = tokens[1].string
    if fn_name in kwlist:
        return _(
            "You tried to use the Python keyword '{kwd}' as a function name.\n"
        ).format(kwd=fn_name)

    # Lets look at the possibility that a keyword might have been used
    # as an argument or keyword argument. The following test is admiteddly
    # crude and imperfect, but it is the last one we do.

    prev_token_str = None
    parens = 0
    brackets = 0
    curly = 0
    for index, tok in enumerate(tokens):
        # Note, we know that a SyntaxError: invalid syntax occurred.
        # So, while some cases of the following might be ok, we assume here that
        # they might have caused the error. They might include things like:
        # def test(None ...)  or
        # def test(*None ...) or
        # def test(**None ...) or
        # def test(a, None ...)
        #       but not
        # def test(a=None ...) nor
        # def test(a=(None,...)) nor
        # def test(a = [1, None])
        char = tok.string
        if char == "(":
            parens += 1
        elif char == ")":
            parens -= 1
        elif char == "[":
            brackets += 1
        elif char == "]":
            brackets -= 1
        elif char == "{":
            curly += 1
        elif char == "}":
            curly -= 1

        elif char in kwlist and (
            (prev_token_str == "(" and index == 3)  # first argument
            or (
                parens % 2 == 1
                and brackets % 2 == 0
                and curly % 2 == 0
                and prev_token_str in [",", "*", "**"]
            )
        ):
            return _(
                "I am guessing that you tried to use the Python keyword\n"
                "{kwd} as an argument in the definition of a function.\n"
            ).format(kwd=char)
        prev_token_str = char

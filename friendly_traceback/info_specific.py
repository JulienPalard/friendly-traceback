"""info_specific.py

Attempts to provide some specific information about the likely cause
of a given exception.
"""
import os


from . import utils
from .my_gettext import current_lang
from . import analyze_syntax
from . import analyze_type_error


def import_error(etype, value):
    _ = current_lang.lang
    # str(value) is expected to be something like
    #
    #  ImportError: cannot import name 'X' from 'Y'  | Python 3.7
    #  ImportError: cannot import name 'X'           | Python 3.6
    #
    # By splitting value using ', we can extract the name and object
    parts = str(value).split("'")
    name = parts[1]
    if len(parts) > 3:
        module = parts[3]
        return _(
            "        The object that could not be imported is '{name}'.\n"
            "        The module or package where it was \n"
            "        expected to be found is '{module}'.\n"
        ).format(name=name, module=module)
    else:
        return _("        The object that could not be imported is '{name}'.\n").format(
            name=name
        )


def indentation_error(etype, value):
    _ = current_lang.lang

    value = str(value)
    if "unexpected indent" in value:
        this_case = _(
            "        In this case, the line identified above\n"
            "        is more indented than expected and \n"
            "        does not match the indentation of the previous line.\n"
        )
    elif "expected an indented block" in value:
        this_case = _(
            "        In this case, the line identified above\n"
            "        was expected to begin a new indented block.\n"
        )
    else:
        this_case = _(
            "        In this case, the line identified above is\n"
            "        less indented than the preceding one,\n"
            "        and is not aligned vertically with another block of code.\n"
        )
    return _("    Likely cause:\n{cause}").format(cause=this_case)


def index_error(etype, value):
    _ = current_lang.lang
    value = str(value)
    if "list" in value:
        this_case = _("        In this case, the sequence is a list.\n")
    elif "tuple" in value:
        this_case = _("        In this case, the sequence is a tuple.\n")
    else:
        this_case = None
    return this_case


def key_error(etype, value):
    _ = current_lang.lang
    # str(value) is expected to be something like
    #
    # KeyError: 'c'
    #
    # By splitting value using ', we can extract the missing key name.
    return _(
        "        In your program, the name of the key\n"
        "        that cannot be found is '{key_name}'.\n"
    ).format(key_name=str(value).split("'")[1])


def module_not_found_error(etype, value):
    _ = current_lang.lang
    # str(value) is expected to be something like
    #
    # ModuleNotFoundError: No module named 'does_not_exist'
    #
    # By splitting value using ', we can extract the module name.
    return _(
        "        In your program, the name of the\n"
        "        module that cannot be found is '{mod_name}'.\n"
    ).format(mod_name=str(value).split("'")[1])


def name_error(etype, value):
    _ = current_lang.lang
    # str(value) is expected to be something like
    #
    # NameError: name 'c' is not defined
    #
    # By splitting value using ', we can extract the variable name.
    return _("        In your program, the unknown name is '{var_name}'.\n").format(
        var_name=str(value).split("'")[1]
    )


def syntax_error(etype, value):
    _ = current_lang.lang
    filepath = value.filename
    linenumber = value.lineno
    offset = value.offset
    message = value.msg
    partial_source, _ignore = utils.get_partial_source(filepath, linenumber, offset)
    filename = os.path.basename(filepath)
    info = _(
        "    Python could not parse the file '{filename}'\n"
        "    beyond the location indicated below by --> and ^.\n"
        "\n"
        "{source}\n"
    ).format(filename=filename, source=partial_source)

    source = utils.get_source(filepath)
    cause = analyze_syntax.find_likely_cause(source, linenumber, message, offset)
    this_case = analyze_syntax.expand_cause(cause)

    return info + this_case


def tab_error(etype, value):
    _ = current_lang.lang
    filename = value.filename
    linenumber = value.lineno
    offset = value.offset
    source, _ignore = utils.get_partial_source(filename, linenumber, offset)
    filename = os.path.basename(filename)
    return _(
        "    Python could not parse the file '{filename}'\n"
        "    beyond the location indicated below by --> and ^.\n"
        "\n"
        "{source}\n"
    ).format(filename=filename, source=source)


def type_error(etype, value):
    return analyze_type_error.convert_message(str(value))


def unbound_local_error(etype, value):
    _ = current_lang.lang
    # str(value) is expected to be something like
    #
    # UnboundLocalError: local variable 'a' referenced before assignment
    #
    # By splitting value using ', we can extract the variable name.
    return _(
        "        The variable that appears to cause the problem is '{var_name}'.\n"
        "        Perhaps the statement\n"
        "            global {var_name}\n"
        "        should have been included as the first line inside your function.\n"
    ).format(var_name=str(value).split("'")[1])


def zero_division_error(*args):
    return None


get_cause = {
    "ImportError": import_error,
    "IndentationError": indentation_error,
    "IndexError": index_error,
    "KeyError": key_error,
    "ModuleNotFoundError": module_not_found_error,
    "NameError": name_error,
    "SyntaxError": syntax_error,
    "TabError": tab_error,
    "TypeError": type_error,
    "UnboundLocalError": unbound_local_error,
    "ZeroDivisionError": zero_division_error,
}
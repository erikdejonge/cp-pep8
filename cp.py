#!/usr/bin/python3
# coding=utf-8
"""
cp.py
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from builtins import int
from builtins import open
from future import standard_library
standard_library.install_aliases()
import io

from builtins import range
from builtins import str
from io import StringIO
from past.utils import old_div
modpylev = False
import os
import time
try:
    import Levenshtein
except ImportError:
    import pylev
    modpylev = True

from argparse import ArgumentParser

ADDCOMMENT_WITH_FOUND_TYPE = False
datastructure_define = False
g_last_assignment_on_global_prefix = ""
g_is_python = True
g_almost_alike = 0

def lev_dist(a, b):
    if modpylev:
        return pylev.levenshtein(a, b)
    else:
        return Levenshtein.distance(a, b)


def help_line(s):
    if "--" in s:
        return True
    elif s.strip().startswith("-"):
        return True
    else:
        return False


def almost_alike(s1, s2, scoped):
    alikeval = 10
    maxlength = 10
    s1 = s1.strip()[:20]
    s2 = s2.strip()[:20]
    global g_almost_alike
    if (len(s1) < maxlength) or (len(s2) < maxlength):
        d = alikeval * 2
    else:
        d = lev_dist(s1, s2)

    if s1.strip().startswith("<") and s2.strip().startswith("<"):
        d = 10000
    elif help_line(s1) or help_line(s2):
        d = 10000
    elif (":" in s2 and ":" in s1):
        d = 1000
    elif s1.strip().startswith("import ") and s2.strip().startswith("import "):
        d = 10000
    elif s1.strip().startswith("from ") and s2.strip().startswith("from "):
        d = 10000
    elif s1.strip().startswith("self.g_") and s2.strip().startswith("self.g_"):
        d = 1
    elif s1.strip().startswith("self.m_") and s2.strip().startswith("self.m_"):
        d = 1
    elif s1.strip().startswith("self._") and s2.strip().startswith("self._"):
        d = 1
    elif s1.strip().startswith("g_") and s2.strip().startswith("g_"):
        d = 1
    elif s1.strip().startswith("m_") and s2.strip().startswith("m_"):
        d = 1
    elif int(scoped) != 0:
        d = alikeval * 2

    if d < alikeval:
        if g_almost_alike < 0:
            g_almost_alike = 0
        g_almost_alike += 1
    else:
        if g_almost_alike > 0:
            g_almost_alike = -1
        else:
            g_almost_alike = 0
    return g_almost_alike


def replace_variables(orgfname):
    """
    @return: @rtype:
    """

    # variables = ["print", "event_emit"]
    variables = ["utils.print_once", "broadcast_and_emit_event", "urls.http_error", "utils.digest_scope", "warning_server_error", "utils.digest_scope_debounce", "utils.assert_equal", "utils.assert_not_equal", "serverevents.subscribe", "emit_event_angular", "urls.slug_comand_timestamp", "urls.postcommand", "async_call_retries", "utils.set_time_out", "utils.set_interval"]
    undo_variables = ["print"]
    watch_variables = []
    #color_vals_to_keep = ['91m', '32m', '34m', '95m', '41m', '97m']
    color_vals_to_keep = ['30m', '31m', '32m', '33m', '34m', '35m', '36m', '37m', '38m', '39m', '90m', '91m', '92m', '93m', '94m', '95m', '96m', '97m', '98m', '99m']

    if orgfname.endswith(".py"):
        undo_variables.remove("print")
    return color_vals_to_keep, undo_variables, variables, watch_variables


def func_test(funcs, line):
    """

    @param funcs:
    @param line:
    @return: @rtype:
    """
    for func in funcs:
        res = func(line)
        if res:
            return True
    return False


def global_class_declare(line):
    """

    @param line:
    @return: @rtype:
    """
    if line.strip().find("=") == len(line.strip()) - 1:
        if line.find(" ") != 0:
            return True
    return False


def on_scope(line):
    """

    @param line:
    @return: @rtype:
    """
    return line.strip().find("$scope.") == 0


def anon_func(line):
    """

    @param line:
    @return: @rtype:
    """
    line = str(line)
    if in_test(["print"], line):
        return False
    if "->" in line:
        return True
    if "=>" in line:
        return True
    return False


def parenthesis(line):
    """

    @param line:
    @return: @rtype:
    """
    return ("(" in line) and (")" in line)


def anon_func_param(line):
    """

    @param line:
    @return: @rtype:
    """
    if functional(line):
        return False

    line = str(line)
    return parenthesis(line) and anon_func(line)


def functional(line):
    """

    @param line:
    @return: @rtype:
    """
    if "_." in line:
        return True
    return False


def func_def(line):
    """

    @param line:
    @return: @rtype:
    """

    if in_test(["+=", "-=", "++", "--", "*="], line):
        return False

    if ", ->" in line.strip():
        return True
    elif ", ->" in line.strip():
        return True
    elif "...) ->" in line.strip():
        return True
    elif line.strip().startswith("def "):
        return True
    elif functional(line):
        return False
    line = str(line)

    if in_test(["print "], line):
        return False

    global g_is_python
    if not g_is_python:
        is_func = ("->" in line or "=>" in line) and "= " in line
    else:
        is_func = False

    if not is_func:
        if "def " in line and ":" in line:
            is_func = True
        if line.startswith("function") and line.strip().endswith("{"):
            is_func = True
    return is_func


def method_call(line):
    """

    @param line:
    @return: @rtype:
    """
    if line.strip().startswith("return"):
        return False

    if line.strip().startswith("except"):
        return False

    if in_test(["+=", "-=", "++", "--", "*="], line):
        return False

    if line.strip().endswith(","):
        return False
    if line.count("(") == 1:
        if line.count("str(") == 1:
            return False

    if (line.count("(") > 0 and line.count(")") > 0) or ("$(this)." in line and line.count("(") > 0 and line.count(")") > 0):
        if line.replace(" ", "").find("[(") > 0:
            return False
        if line.replace(" ", "").find("=(") > 0:
            return False
        return True
    return False


def class_method(line):
    """

    @param line:
    @return: @rtype:
    """
    if "raise" in line:
        return False
    line = str(line)
    if in_test(["+=", "-=", "++", "--", "*="], line):
        return False
    if in_test(["print"], line):
        if not in_test([":", "->", "=>"], line):
            return False

    return ("->" in line or "=>" in line) and ":" in line


def scope_declaration(line):
    """

    @param line:
    @return: @rtype:
    """
    if line.strip().find("$scope") == 0:
        return True
    return False


def scoped_method_call(line):
    """

    @param line:
    @return: @rtype:
    """
    if functional(line):
        return False

    if in_test([ "print"], line):
        return False

    line = str(line)
    return ("= " in line and ("->" in line or "=>" in line)) or (scope_declaration(line) and "()" in line and line.find("     ") is not 0)


def some_func(line):
    """

    @param line:
    @return: @rtype:
    """
    return func_test([func_def, class_method, scoped_method_call], line)


def assignment(line):
    """

    @param line:
    @return: @rtype:
    """
    line = line.strip()
    if "memory.set" in line:
        return True

    if "<=" not in line and ">=" not in line and "==" not in line and line.count("= ") is 1 and not is_member_var(line):
        if not some_func(line):
            return True
    return False


def elif_switch(line):
    """

    @param line:
    @return: @rtype:
    """
    if line.strip() == "":
        return True
    if in_test(["else if", "elif", "else"], line):
        return True
    return False


def keyword(line, returnkw=False):
    """

    @param line:
    @return: @rtype:
    """
    if line.strip() == "":
        return True
    kws = ["class", "print", "with", "require", "#noinspection", "except", "pass", "del", "return", "with", "super", "catch", " pass", "switch", "raise", "for", "when", "if", "elif", "else", "while", "finally", "try", "unless", "catch"]
    kws = [x + " " for x in kws]
    kws.extend(["$on", "$(", '"""'])
    if in_test(kws, line):
        if returnkw:
            return in_test(kws, line, return_val=True)
        return True
    elif some_func(line):
        if returnkw:
            return "some_func"
        return True
    return False


def indentation(line):
    """

    @param line:
    @return: @rtype:
    """
    cnt = 0
    for c in line:
        if c != " ":
            break
        cnt += 1
    return old_div(float(cnt), 4)


def data_assignment(line, prev_line):
    """

    @param line:
    @param prev_line:
    @return: @rtype:
    """
    lvalue = "-"
    if '["' in line and '"]' in line:
        line = line.replace('["', ".")
        prev_line = prev_line.replace('["', ".")
    if "." in line:
        lvalue = line.split(".")[0].strip()
    if "." in prev_line:
        rvalue = prev_line.split(".")[0].strip()
        return lvalue in rvalue
    else:
        return False


def comment(line):
    """
    @param line:
    @return: @rtype:
    """
    if not line:
        return False

    line = line.strip().replace("# ##^", "")
    if line.startswith("#") and "noinspection" not in line:
        return True
    else:
        return False


def whitespace(line):
    """

    @param line:
    @return: @rtype:
    """
    cnt = 0
    for i in line:
        if i != " ":
            return cnt
        cnt += 1
    return cnt


def list_comprehension(line):
    return (("]" in line or "}" in line or ")" in line) and ("[" in line or "{" in line or "(" in line) and "for" in line) and (line.strip().endswith("]") or line.strip().endswith("}"))


def scope_diff(line, prev_line):
    """

    @param line:
    @param prev_line:
    @return: @rtype:
    """
    if not prev_line:
        return 0

    lws = whitespace(line)
    pws = whitespace(prev_line)
    dif = old_div((pws - lws), 4)

    return dif


def in_test(items, line, return_val=False, words=False):
    """

    @param words:
    @param items:
    @type items:
    @param line:
    @type line:
    @param return_val:
    @type return_val:
    @return: @rtype:
    """
    for item in items:
        if item.strip() == "if":
            item = "if "
        if item == line:
            if return_val:
                return item
            return True
        if not words:
            if item in line:
                if return_val:
                    return item
                return True
    if return_val:
        return ""
    return False


def start_in_test(items, line):
    """

    @param items:
    @param line:
    @return: @rtype:
    """
    line = line.strip()
    for item in items:
        if line.startswith(item):
            return True
    return False


def in_test_kw(items, line):
    """

    @param items:
    @param line:
    @return: @rtype:
    """
    items = [x + " " for x in items]
    return in_test(items, line)


def in_test_result(items, line):
    """

    @param items:
    @param line:
    @return: @rtype:
    """
    for item in items:
        if item in line:
            return item.replace('"""', '')
    return None


def is_test(items, line):
    """

    @param items:
    @param line:
    @return: @rtype:
    """
    for item in items:
        if item is line.strip():
            return True
    return False


def is_member_var(line):
    """

    @param line:
    @return: @rtype:
    """
    line = str(line)
    if "http" in line.lower():
        return False
    if not "[" in line and not "]" in line and not "= {" in line and not "@param" in line and (":" in line and not ".cf" in line) and (line.count(":") is 1 and not '":"' in line and not "':'" in line) and not anon_func(line) and not keyword(line):
        return True
    return False


def global_line(line):
    """

    @param line:
    @return: @rtype:
    """
    return line.find(" ") != 0


def global_object_method_call(line):
    """

    @param line:
    @return: @rtype:
    """
    if global_line(line):
        if "." in line and parenthesis(line):
            return True
    return False


def class_method_call(line):
    """

    @param line:
    @return: @rtype:
    """
    if line.strip().find("@") == 0:
        if "(" in line and ")" in line:
            return True
    return False


def function_call(line):
    """

    @param line:
    @return: @rtype:
    """
    if line.strip().startswith("except"):
        return False

    if parenthesis(line) and not "." in line:
        if line.replace(" ", "").find("[(") > 0:
            return False
        if line.replace(" ", "").find("=(") > 0:
            return False

        return True
    return False


def double_meth_call(line):
    """

    @param line:
    @return: @rtype:
    """
    if "serverconfig" in line:
        return False
    return "self" in line and line.count("()") > 1


def coffee_script_pretty_printer(add_double_enter, add_enter, first_method_class, first_method_factory, line, next_line, prev_line, resolve_func, scoped, if_cnt, in_python_comment, fname, in_method_param_list, mylines, line_cnt, in_python_comment_cnt):
    """
    @param fname:
    @param add_double_enter:
    @param add_enter:
    @param first_method_class:
    @param first_method_factory:
    @param line:
    @param next_line:
    @param prev_line:
    @param resolve_func:
    @param scoped:
    @param if_cnt:
    @param in_python_comment:
    @return: @rtype:
    """
    global g_last_assignment_on_global_prefix
    global g_is_python
    g_is_python = fname.endswith(".py")
    add_docstring = False
    line_redone = org_line = line
    if "demo.governet.nl" in line:
        x = 4

    if scoped > 0:
        if if_cnt > 0:
            if_cnt -= scoped

    if line.strip().startswith("if"):
        if_cnt += 1

    debuginfo = ""
    if ".save(" in prev_line:
        add_enter = True
        debuginfo = "object save"

    if ".factory" in line:
        add_double_enter = True
        debuginfo += ".factory"
    elif line.startswith("class ") and "=" not in line:
        if "noinspection" in prev_line:
            debuginfo += "class def after inspection"
        else:
            add_double_enter = True
            debuginfo = "class def"
        add_double_enter, add_enter, debuginfo = in_python_comment_test(add_double_enter, add_enter, debuginfo, in_python_comment)
    elif line.strip().startswith("self.assert") and scoped == 0:
        debuginfo = "testcase"
        if not prev_line.strip().startswith("self.assert"):
            debuginfo += " start"
            add_enter = False
            if prev_line.strip() == '"""':
                debuginfo += " after comment2"
                add_enter = False

        if not next_line.strip().startswith("self.assert"):
            debuginfo += " single"
            add_enter = False
    elif line.strip().lower().startswith("options:"):
        add_enter = True
        debuginfo = "docopt options"
    elif line.strip().lower().startswith("description:"):
        add_enter = True
        debuginfo = "docopt options"

    elif line.strip().lower().startswith("usage:") :
        add_enter = True
        debuginfo = "docopt usage"
    elif line.strip().lower().startswith("commands:"):
        add_enter = True
        debuginfo = "docopt commands"
    elif "for " in line.strip() and in_python_comment:
        add_enter = False
        debuginfo = "for in python comment"
    elif line.strip().startswith("Usage:"):
        add_enter = False
        debuginfo = "doc opt option"
    elif line.strip().startswith("Commands:"):
        add_enter = True
        debuginfo = "doc opt option"
    elif line.strip().startswith("@") and in_python_comment:
        add_enter = False
        debuginfo = "return"
    elif not in_python_comment and not line.strip().startswith("@type") and not line.strip().startswith("@return") and line.strip().startswith("@") and not (line.strip().startswith("@m_") and ".setter" not in line) and not '"""' in prev_line and not "param" in line and fname.endswith(".py"):
        debuginfo = "propertyx "
        if func_def(prev_line):
            debuginfo += " after func"
        else:
            if line.find(" ") > 0 or line.find(" ") == -1:
                debuginfo += " global - "
                add_double_enter = True
            else:
                add_enter = True
    elif "it " in line and ("->" in line or "=>" in line):
        debuginfo = "karma test"
        add_enter = True

    elif "noinspection" in line:
        debuginfo = ""
        if not keyword(prev_line) or "return" in prev_line or "raise" in prev_line:
            add_enter = True
        else:
            add_enter = False
            debuginfo += " after keyword"
        if next_line:
            if keyword(next_line) and not keyword(prev_line):
                if "class" not in next_line:
                    debuginfo += " keyword (not class) in nextline"
                    add_enter = True
                    add_double_enter = False
        if next_line.rstrip().startswith("def "):
            add_double_enter = True
            debuginfo += " next line def"
        if next_line.rstrip().startswith("class "):
            add_double_enter = True
            debuginfo += " next line class"
        debuginfo = ""
    elif prev_line.strip().startswith("raise"):
        debuginfo = "raise"
        if "except" not in line and "else" not in line and not elif_switch(line):
            debuginfo = " after raise"
            add_enter = True
            if func_def(line) and not "(self" in line:
                add_double_enter = True
    elif line.strip().startswith("print"):
        debuginfo = "debug(pr1t) statement"
        if "= ->" in line:
            debuginfo = "func with print"
            add_enter = True
            if not line.strip().startswith("print"):
                debuginfo = " (doesn't start with print)"
                add_enter = False

            if class_method(prev_line):
                debuginfo = " func with print after classmethod"
                add_enter = False
        if scoped > 0:
            add_enter = True
            debuginfo += " scope change " + str(scoped)
    elif line.strip().startswith("return"):
        debuginfo = "retrn"
        if not comment(line) and not comment(prev_line):
            add_enter = False
            if scoped < 1:
                debuginfo += " scoped is <1"
                add_enter = False
            elif whitespace(prev_line) - whitespace(line) > 0:
                add_enter = True
                debuginfo += " whitespace"
            elif '"""' in prev_line:
                add_enter = False
                debuginfo += " after doc comment"

            elif keyword(prev_line):
                add_enter = False
                debuginfo += " after keyword1 "
                if scoped == 0:
                    debuginfo += " same scope  "
                    add_enter = True
            elif func_def(prev_line):
                add_enter = False
                debuginfo += " after funcdef"
            elif prev_line:
                if next_line:
                    if (prev_line.strip() == "") or ("else" in prev_line) or ("else" in next_line) and not in_test(["setInterval", "setTimeout"], prev_line):
                        debuginfo += " after empty line time func or 3lse"
                elif is_test([")"], prev_line.strip()) or in_test(["_.filter", "_.map"], prev_line):
                    debuginfo += " after close or underscore func"
                    # add_enter = True
                elif "return" in prev_line:
                    debuginfo += " after rturn" + str(scoped)

                    # add_enter = True
                elif keyword(prev_line):
                    debuginfo += "after keyword2"
                    add_enter = False
                else:
                    if next_line and not in_test(["setInterval", "setTimeout"], prev_line):
                        if "class" not in next_line or len(str(next_line)) > 0:
                            debuginfo += " after js time func"
                    elif scoped > 1:
                        debuginfo += " after scope d!ff " + str(scoped)
                        # add_enter = True

    elif "__main__" in line and "__name__" in line:
        add_double_enter = True
        debuginfo = "main"
    elif line.strip().startswith("class ") and "=" not in line:
        add_enter = True
        debuginfo = "class def"
        add_double_enter, add_enter, debuginfo = in_python_comment_test(add_double_enter, add_enter, debuginfo, in_python_comment)
    elif line.strip().startswith("<div") and prev_line.strip().startswith("</div"):
        add_enter = True
        debuginfo = "close div"
    elif "unless" in line:
        add_enter = True
        debuginfo = "unless"
    elif double_meth_call(line):
        debuginfo = "double method call"
        if not keyword(prev_line):
            if not double_meth_call(prev_line):
                add_enter = True
    elif line.strip().startswith("import "):
        debuginfo = "import"
    elif line.strip().startswith("from ") and fname.endswith(".py") and '"""' not in prev_line:
        debuginfo += "from import"
        if prev_line.strip().startswith("import "):
            debuginfo += " after import"
            add_enter = True
        elif prev_line.strip().startswith("#noinspection"):
            debuginfo += " after pycharm directive"
            add_enter = False
        else:
            debuginfo += " after from"
    elif line.strip().startswith("import") and fname.endswith(".py") and '"""' not in prev_line:
        debuginfo += "import"
        if prev_line.strip().startswith("import"):
            debuginfo += " after import"
        elif prev_line.strip().startswith("#noinspection"):
            debuginfo += " after pycharm directive"
            add_enter = False
        elif scoped != 0:
            debuginfo += " scope change"
        else:
            add_enter = True
    elif global_class_declare(line):
        debuginfo = "global_class_declare"
        add_enter = True
    elif line.strip().startswith("try"):
        debuginfo = "try statement"
    elif line.strip().startswith("app.controller"):
        debuginfo = "angular controller"
        add_enter = True
    elif line.strip().startswith("app.directive"):
        debuginfo = "angular directive"
        add_enter = True
    elif assignment(line):

        debuginfo = "assignment"
        global datastructure_define
        if "[" in line and not "]" in line and not "\\033[" in line and not anon_func(line) and not func_def(line):
            debuginfo += " datastructure"
            datastructure_define = True
            if global_line(line):
                add_enter = True
                debuginfo += " (global)"

        if scoped > 0:
            debuginfo += " prev scope"
            add_enter = True
        if prev_line.strip().startswith("_.") and not prev_line.strip().endswith(">"):
            debuginfo += " after some functional js"
            add_enter = True
        if assignment(prev_line) and method_call(prev_line) and scoped == 0:
            debuginfo += " again"
            add_enter = False

        if global_line(line):
            debuginfo += " on global"
            assignment_on_global_prefix = line.strip()[:2]
            if g_last_assignment_on_global_prefix != assignment_on_global_prefix:
                add_enter = True
                debuginfo += " has different prefix "
                if comment(prev_line):
                    debuginfo += " after comment(3)"
                    add_enter = False
                if line.strip().startswith("app = angular.module"):
                    add_enter = True
                    debuginfo += "angular app object"

            else:
                if datastructure_define:
                    debuginfo += " same prefix"
                    add_enter = False
                    if "angular.module" in prev_line:
                        debuginfo += " after angular module"
                        add_enter = True
                        datastructure_define = False
            g_last_assignment_on_global_prefix = assignment_on_global_prefix
            if not global_line(prev_line):
                debuginfo += " (prev!=global)"
                if scoped == 0:
                    add_double_enter = True
                else:
                    add_enter = True

            if prev_line.strip().startswith(")"):
                debuginfo += " prev ends data"
                add_double_enter = True
        if scoped > 1:
            debuginfo += " on prev scope"
            add_enter = True
        elif on_scope(line):
            debuginfo += " on $scope"
            if scoped == 1:
                add_enter = False
                debuginfo += " func?"
        if scoped >= 2:
            add_enter = True
            debuginfo += " new scope"
    elif global_object_method_call(line):
        if not ("noinspection" in prev_line and "no1nspect1on" not in prev_line) and "import " not in prev_line:
            debuginfo = "global method call"
            add_enter = True
        if "angular.module" in line:
            debuginfo = " angular.module"
            add_double_enter = False
            add_enter = True
    elif ": [" in line and not fname.endswith(".py"):
        debuginfo = "struct coffeescript"
        add_enter = True
        if line.find(" ") is 0:
            debuginfo = " nested"
            add_enter = False
    elif class_method(line):
        debuginfo = str('print' in line) + " class_method"
        if first_method_class:
            debuginfo += " " + str(first_method_class)
            if "class" in prev_line:
                add_enter = False
                debuginfo += " class in prevline"
            else:
                add_enter = True
        elif first_method_factory:
            debuginfo = "factorymethod " + str(first_method_factory)

            add_enter = True
        else:
            if is_member_var(prev_line):
                debuginfo += " after member var"
                add_enter = True
            else:
                if not fname.endswith(".py"):
                    if line.strip().startswith("link:"):
                        debuginfo += " directive link"
                        add_enter = False
                        if prev_line.lower().strip().startswith("return"):
                            debuginfo += " after return"
                            add_enter = True
                    elif scoped < 0:
                        if "unless" not in prev_line:
                            add_enter = True
                            debuginfo += " in a nested scope " + str(global_class_declare(prev_line))
                        else:
                            debuginfo += " in a nested scope after unless"

                        if global_class_declare(prev_line):
                            debuginfo += " after class declare"
                            add_enter = False
                    else:
                        if indentation(line) == 1:
                            debuginfo += " indented 1"
                            if scoped >= 1:
                                debuginfo += " scoped >=1"
                                add_double_enter = True
                            else:
                                add_enter = True
                        else:
                            add_enter = True
    elif line.strip().startswith("_.each"):
        if scoped > 0:
            add_enter = False
            debuginfo = "start for each"
        else:
            add_enter = False
            debuginfo = "for each, one liner"
    elif prev_line.strip().startswith("_.each") and not prev_line.strip().endswith(">"):
        add_enter = True
        debuginfo = "after for each loop"
    elif "@unittest" in line:
        add_enter = True
        debuginfo = "unittest decorator"
    elif ".$on" in line:
        debuginfo = "0n event"
        if scoped <= 1:
            debuginfo += " on same scope "
            add_enter = False
        if scoped > 1:
            debuginfo += " on different scope "
            add_enter = True
    elif "set_time_out" in line:
        debuginfo = "set_time_out"
        if not func_def(prev_line) and not start_in_test(["if", "else"], prev_line):
            add_enter = True
    elif line.strip().find("it ") == 0:
        debuginfo = "test statement"
        if not some_func(prev_line) and not anon_func(prev_line):
            add_enter = True
    elif line.strip().find("describe ") == 0:
        debuginfo = "describe statement"
        if not some_func(prev_line) and not anon_func(prev_line):
            add_enter = True
    elif "$observe" in line and "$observe" not in prev_line:
        debuginfo = "observe method"
        add_enter = True
    elif ".then" in line:
        debuginfo = "resolve method body"
        resolve_func += 1
        if prev_line:
            if prev_line.strip().startswith("return"):
                debuginfo = " after return"
                add_enter = True
            if not in_test(["if", "else", "->", "=>"], prev_line):
                add_enter = True
    elif "if" in line and (line.strip().find("if") is 0 or line.strip().find("else") is 0 or line.strip().find("elif") is 0):
        debuginfo = " if statement"

        if scoped > 0:
            debuginfo += " scope change"
            add_enter = True

        if scoped == 0:
            debuginfo += " on same scope "
            if "_.defer" in prev_line:
                debuginfo += " after defer call"
                add_enter = True

            if assignment(prev_line):
                debuginfo += " after assignement"
                add_enter = True
            if "if" in prev_line:
                debuginfo += " after if"
                add_enter = True
            if method_call(prev_line):
                debuginfo += " after method call"
                add_enter = True
            if line.find(" ") != 0:
                add_enter = True
                debuginfo += "global scope"
        if "else" in line:
            debuginfo += " else"
            add_enter = False
        if "elif" in line:
            debuginfo += " elif"
            add_enter = False
            if scoped > 1:
                add_enter = True
                debuginfo += " scope change more then 1 "

    elif func_def(line):
        if '"""' not in next_line:
            add_docstring = True
        debuginfo = "function def "
        if line.find(" ") is not 0:
            if prev_line.strip().startswith("@"):
                debuginfo += "after property - "
                add_double_enter = False
                add_enter = False
            elif prev_line.strip().startswith("#"):
                debuginfo += " after comment(4)"
                if "PyUnresolvedReferences" in prev_line.strip():
                    debuginfo += " pyinspection line"
                    add_double_enter = False
                    add_enter = False
            else:
                add_double_enter = True
                debuginfo += " commentblock"
        else:
            if not func_def(prev_line) and not comment(prev_line):
                debuginfo = "function def nested"
                if func_def(prev_line):
                    debuginfo += " after function def"
                    add_enter = False
                elif assignment(prev_line):
                    debuginfo = "function def nested after assignement"
                    add_enter = True
                elif class_method(prev_line):
                    debuginfo += " after method"
                elif "@unittest" in prev_line:
                    debuginfo += " after unittest decorator"
                    add_enter = False
                elif in_test(["if", "else"], prev_line):
                    debuginfo += " after if or else"
                elif keyword(prev_line):
                    debuginfo += " after keyword"
                    add_enter = True
                elif anon_func(prev_line) and not fname.endswith(".py"):
                    debuginfo += " after anon func"
                    add_enter = False
                elif not class_method(prev_line) and not keyword(prev_line) and not assignment(prev_line):
                    debuginfo += " somewhere"
                    add_enter = True
                    if "return" in prev_line:
                        add_enter = True
                        debuginfo += " in a class"
                    if scoped > 1:
                        add_enter = True
                        debuginfo = "scope change"
                    if "@" in prev_line or keyword(prev_line):
                        add_enter = False
                        debuginfo += " after property or kw " + str(keyword(prev_line, True))
                elif first_method_factory:
                    debuginfo += "first method factory"
                    add_enter = True
                elif on_scope(line):
                    debuginfo += " on $scope "
                    if scoped != 1:
                        add_enter = True
                    else:
                        debuginfo += " func?"
                elif scoped > 0:
                    debuginfo += " on previous scope"
                    add_enter = True
                if "(self" in line and not "class" in prev_line and not '"""' in prev_line and not prev_line.strip().startswith("@"):
                    debuginfo += " a python class "
                    add_double_enter = False
                    if "#@" in prev_line or "# @" in prev_line:
                        debuginfo += " after commented out property"
                        add_enter = False
                    else:
                        add_enter = True
                    if "noinspection" in prev_line:
                        debuginfo += " after no inspection"
                        add_enter = False
                if "(self" in line and ("class" in prev_line or '"""' in prev_line) and not prev_line.strip().startswith("@") and not "__class__" in prev_line:
                    debuginfo += " first method"
                    add_double_enter = False
                    add_enter = True
                    if fname.endswith(".py"):
                        debuginfo += " python"
                        if '"""' in prev_line:
                            debuginfo += " after comment(5)"
                        else:
                            debuginfo += " no enter"
                            add_enter = False


            else:
                debuginfo = "functiondef after functiondef"
                line = line + "\n" + " c" * whitespace(line) + 'print "' + line.replace('"', "'") + "'\n"
            add_double_enter, add_enter, debuginfo = in_python_comment_test(add_double_enter, add_enter, debuginfo, in_python_comment)
        if line.strip().startswith("def "):
            if not "(self" in line and not "(cls" in line and not "@" in prev_line and not prev_line.strip().startswith("def ") and not line.startswith(" ") and not "#noinspection" in prev_line:
                add_enter = True
                add_double_enter = True
                debuginfo += " python"
            elif "noinspection" in prev_line:
                add_enter = False
                add_double_enter = False
                debuginfo += " after noinspection"

    elif class_method_call(line) and not fname.endswith(".py"):
        debuginfo = "class method call"
        if scoped > 0:
            add_enter = True
            debuginfo += " scoped"
    elif scoped_method_call(line):
        debuginfo = "scoped_method_call"
        if prev_line:
            if not func_test([method_call, class_method], prev_line.strip()) and not in_test([".then", "if", "->", "=>", "else"], prev_line):
                debuginfo += " method define or scoped method call"
                if line.find(" ") is not 0:
                    if len(prev_line) > 0:
                        add_double_enter = True
                    else:
                        debuginfo += "after non empty line"
                        add_enter = True
                else:
                    debuginfo += " not on globalscope"
    elif anon_func(line) and not in_test([".directive", "$watch", ".bind"], prev_line) and not in_test(["_.delay", "_.defer", ".directive", "$watch", ".bind"], line) and not fname.endswith(".py"):
        debuginfo = "anonymousfunction"
        if not resolve_func:
            debuginfo += "resolve result 3"
            add_enter = True
            if line.count("    ") is 1 and not assignment(prev_line) and not func_def(prev_line):
                debuginfo = "anonymousfunction2"
                datastructure_define = False
                add_enter = True
            if line.find(" ") is not 0:
                add_double_enter = True
        else:
            debuginfo = "resolve result 2"
    elif line.strip().startswith("super("):
        debuginfo = "super"
        if scoped > 0:
            debuginfo = " with scope chage"
            add_enter = True
        add_double_enter, add_enter, debuginfo = in_python_comment_test(add_double_enter, add_enter, debuginfo, in_python_comment)
    elif in_test_kw(["when"], line):
        debuginfo = in_test_result(["when"], line) + " statement"
    elif "pass" == prev_line.strip() and not in_test_result(["if", "elif", "else"], line):
        debuginfo = " pass"
        add_enter = True
    elif list_comprehension(line) and fname.endswith(".py"):
        debuginfo = "list comprehension"
    elif in_test_kw(["switch", "for", "while"], line) and not in_test_kw(["switch", "for", "while", "["], prev_line) and not comment(prev_line) and not ("]" in line and "[" in line):
        debuginfo = in_test_result(["switch", "try", "when", "while", "for"], line) + " statement tested"
        if prev_line:
            if not in_test(["when", "if", "->", "=>", '"""', "def ", "else", "with", "switch", "try", "#noinspection"], prev_line):
                if in_test(["return"], prev_line) and in_test(["when"], line) and scoped > 1:
                    debuginfo += " prevented when statement"
                else:
                    add_enter = True
            else:
                debuginfo += " prevented by " + str(in_test_result(["when", "if", "->", "=>", "else", "switch"], prev_line))
    elif line.strip().startswith(".directive") or line.strip().startswith("app.directive"):
        add_enter = True
        debuginfo = ".directive "
    elif is_member_var(line) and not fname.endswith(".py"):
        debuginfo = "is_member_var "
        ls = line.strip().split(" ")
        first_word = ""
        if len(ls) > 0:
            first_word = ls[0]
        if not keyword(first_word):
            debuginfo += " member initialization"
            if scoped > 0:
                if not is_member_var(prev_line):
                    add_enter = True
                    debuginfo += " new scope"
    elif line.strip().startswith("with") and fname.endswith(".py"):
        debuginfo = "with statement"

        if comment(prev_line) or '"""' in prev_line:
            debuginfo += " after comment(1)"
        else:
            if not keyword(prev_line):
                add_enter = True
            else:
                debuginfo += "after keyword -> " + keyword(prev_line, returnkw=True)
    elif method_call(line) and not "raise" in line:
        assigned = False
        debuginfo = "methodcall"
        if assignment(line):
            debuginfo += " and assigned "
            assigned = True
            if fname.endswith(".py"):
                if scoped > 0:
                    debuginfo += "in python scope change "
                    add_enter = True
        if line.find(" ") is not 0:
            debuginfo += "method call global scope"
            if assigned:
                add_double_enter = False
                assignment_on_global_prefix = line.strip()[:2]

                if g_last_assignment_on_global_prefix != assignment_on_global_prefix:
                    add_enter = True
                    debuginfo += " different prefix"
                else:
                    debuginfo += " same prefix"
                g_last_assignment_on_global_prefix = assignment_on_global_prefix
            else:
                if "# noins" not in prev_line and "import " not in prev_line and "#noins" not in prev_line:
                    lastlinemethodcall = (method_call(prev_line) and scoped!=0)
                    add_enter = not lastlinemethodcall
                    add_double_enter = lastlinemethodcall
                    debuginfo += "noins in pre, lastlinemethodcall:" + str(lastlinemethodcall)
                if ")()" in line.strip():
                    debuginfo += " end mod"
                    add_enter = False
                    add_double_enter = False
        elif prev_line:
            if method_call(prev_line) and not elif_switch(line):
                if whitespace(line) < whitespace(prev_line):
                    if not elif_switch(prev_line) and not line.strip().startswith("except"):
                        debuginfo += " method call higher scope " + str(whitespace(prev_line) - whitespace(line))
                        if whitespace(prev_line) - whitespace(line) > 0:
                            add_enter = True
                            debuginfo += " scope>2 "
            elif not func_test([func_def, scoped_method_call, method_call, class_method], prev_line.strip()) :
                debuginfo += " mcall not after functest "
                if data_assignment(line, prev_line):
                    debuginfo += "method call data assignment " + str(if_cnt)
                    add_enter = False
                else:
                    if assignment(prev_line):
                        debuginfo += " after assignment"
                        if elif_switch(line):
                            debuginfo += " if or elif in line"
                            add_enter = False
                        else:
                            if scoped == 0:
                                add_enter = False
                                debuginfo += " same scope"
                            else:
                                add_enter = True
                                debuginfo += " mcall scope change"

                    else:
                        test_items = ["@staticmethod", "catch", "print", "with", "when", "_.keys", "finally", "except", '"""', "->", "=>"]
                        if in_test(test_items, prev_line) and scoped == 0:
                            debuginfo += " after " + str(in_test_result(test_items, prev_line)).replace("print", "pr1nt")
                        else:
                            if comment(prev_line):
                                debuginfo += " after comment(2)"
                            else:
                                debuginfo += " not after comment "
                                if assignment(line) and not "_." in line:
                                    if not fname.endswith(".py"):
                                        debuginfo += " and assigned in coffee "
                                        add_enter = False
                                if scoped > 0:
                                    add_enter = True
                                    debuginfo += " scope change "

                if in_test(["$watch", "if", "else", "for", "while", "try:", "#noinspection", "= {"], prev_line.strip()):
                    debuginfo += "method call after 1f 3lse or wtch or dct"
                    add_enter = False
                    add_double_enter = False
            else:
                debuginfo += "method call nested "
                add_enter = False
    elif line.strip().startswith("raise"):
        debuginfo = " raise"
        if not in_test(["if", "else", "except"], prev_line):

            if scoped > 1:
                debuginfo += " after big if"
                add_enter = False
            else:
                add_enter = True
        elif not method_call(prev_line):
            debuginfo += " after methodcall"
            add_enter = False
        elif prev_line.strip().startswith("console"):
            debuginfo += " after console statement"
            add_enter = False
            add_double_enter = False
    elif function_call(line):
        debuginfo = "function call"
        if not function_call(prev_line):
            if "return" in prev_line and not "_return" in prev_line:
                debuginfo = " after return"
                add_enter = True
        if prev_line.strip() == ")":
            debuginfo = " new line"
            add_enter = True
    elif start_in_test(["class"], line) and not start_in_test(["classifier"], line):
        debuginfo = "class"
        add_double_enter = True
    elif "except" in line:
        debuginfo = "except"
        # add_enter = True
    elif line.lstrip().startswith("$scope") and in_test(["->", "=>"], line):
        debuginfo = "scoped method define"
        if prev_line:
            if not ")" is prev_line.strip():
                add_enter = True
    elif "$(e" in line:
        debuginfo = "jquery"
        if not keyword(prev_line):
            add_enter = True
    elif "$watch" in line:
        debuginfo = "watch def"
        if not keyword(prev_line):
            if scoped == 0:
                add_enter = True
    elif "raise" in line:
        if not keyword(prev_line):
            debuginfo = "raise"
            add_enter = True
    elif "angular.module" in line:
        debuginfo = "angular module"
        add_double_enter = True
    elif not line.startswith("import ") and not line.startswith("from ") and (prev_line.startswith("from ") or prev_line.startswith("import ")):
        debuginfo = "imports over"
        add_enter = True

    elif "$." in line:
        if prev_line:
            if not ("_." in prev_line or "$." in prev_line or "if" in prev_line):
                if not resolve_func:
                    add_enter = True
                    debuginfo = ".each"
    elif line.lstrip().startswith("f_") and (line.endswith("->") or line.endswith("=>")):
        add_double_enter = True
    elif "setInterval" in line or "setTimeout" in line:
        debuginfo = "setInterval timeout"

    if prev_line.strip().startswith("self.assert") and not line.strip().startswith("self.assert"):
        if not add_enter and not add_double_enter:
            debuginfo = "testcase ended on previous line"
            add_enter = True

    if "{" in line and "}" in line and ":" in line and "," in line and line.strip().endswith("}"):
        nesting = line.find("{")
        if fname.endswith(".py"):
            line_redone = line.replace(",", ",\n" + nesting * " ")


    if line.count('(') % 2 != 0  and not (line[0] == '(') and in_method_param_list is False:
        in_method_param_list = True





    if line.count(')') % 2 != 0 and in_method_param_list:
        in_method_param_list = False
        debuginfo += " end method_param_list "

    if in_method_param_list is True:
        debuginfo += " method_param_list "

    if line.count('"""') % 2 != 0 and not "strip" in line and not (line[0] == '"' and not line.strip() == '"""'):

        if in_python_comment:

            in_python_comment = False
            in_python_comment_cnt -= 1
        else:
            if in_python_comment_cnt % 2 == 0:
                in_python_comment = True
                in_python_comment_cnt += 1
            else:
                in_python_comment_cnt -= 1
            try:
                line_cnt2 = line_cnt
                while True:
                    line2 = mylines[line_cnt2]

                    if line2.startswith('"""'):
                        break

                    if "Usage:" in line2:
                        in_python_comment = False

                    line_cnt2 += 1
            except IndexError:
                pass

            if in_python_comment is True and next_line.count('"""') > 0 or "rtype" in next_line:
                if "rtype" in next_line:
                    next_line = ""
                if "(" in prev_line:
                    emptydocstring = prev_line.replace("def ", "").replace("class ", "").strip()
                    if "(" in emptydocstring:
                        emptydocstring = emptydocstring.split("(")[0]
                    docstring = ""

                    if ")" in prev_line:
                        pls = prev_line.split("(")[1].split(")")[0].split(",")
                        pls = [x.strip() for x in pls if len(x) > 0]
                        empty = True
                        for typeitem in pls:
                            if typeitem != "self" and typeitem != "Exception" and typeitem != "object" and "admin." not in typeitem.lower() and "model." not in typeitem.lower():
                                empty = False
                                mytype = "str"
                                typeval = None
                                if "=" in typeitem:
                                    tis = typeitem.split("=")
                                    typeitem = tis[0]
                                    typeval = tis[1].strip()
                                if typeitem.startswith("arguments"):
                                    mytype = "IArguments"
                                elif typeitem.startswith("i_"):
                                    mytype = "int"
                                elif "verbose" in typeitem:
                                    mytype = "bool"
                                elif "size" in typeitem:
                                    mytype = "int"
                                elif "index" in typeitem:
                                    mytype = "int"
                                elif "cnt" in typeitem:
                                    mytype = "int"
                                elif "dict" in typeitem:
                                    mytype = "dict"
                                elif "list" in typeitem:
                                    mytype = "list"
                                elif "ids" in typeitem:
                                    mytype = "list"
                                elif typeitem.endswith("s"):
                                    mytype = "list"
                                elif "commandline" in typeitem:
                                    mytype = "Arguments"
                                elif "argument" in typeitem.lower():
                                    mytype = "Arguments"
                                elif typeitem.startswith("d_"):
                                    mytype = "dict"
                                elif typeitem.startswith("l_"):
                                    mytype = "list"
                                elif typeitem.startswith("f_"):
                                    mytype = "float"
                                elif typeitem.startswith("u_"):
                                    mytype = "unicode"
                                elif typeitem.startswith("s_"):
                                    mytype = "str"
                                elif typeitem.startswith("b_"):
                                    mytype = "bool"
                                elif typeitem.startswith("events"):
                                    mytype = "Events"
                                elif typeitem.startswith("request"):
                                    mytype = "HttpRequest, django.core.handlers.wsgi.WSGIRequest"
                                elif typeitem.startswith("serverconfig"):
                                    mytype = "ServerConfig"
                                elif typeitem.startswith("dbase"):
                                    mytype = "CouchDBServer"
                                elif typeitem.startswith("crypto_user"):
                                    mytype = "CryptoUser"
                                elif typeitem == "cryptobox":
                                    mytype = "CryptoboxMetaData"
                                elif typeitem == "cryptobox_db":
                                    mytype = "CryptoboxMetaData"
                                elif typeitem == "login_token":
                                    mytype = "LoginToken"

                                if typeval:
                                    if typeval == "True" or typeval == "False":
                                        mytype = "bool"
                                    elif typeval == "None" or typeval == "None":
                                        mytype += ", None"
                                    elif '"' in typeval or "'" in typeval:
                                        mytype = "str"
                                    else:
                                        try:
                                            if "." in str(typeval):
                                                float(typeval)
                                            mytype = "float"
                                        except:
                                            pass
                                        try:
                                            int(typeval)
                                            mytype = "int"
                                        except:
                                            pass
                                if "kwargs" in typeitem or "args" in typeitem:
                                    if "kwargs" in typeitem:
                                        typeitem = "@type kwargs: dict"
                                    elif "args" in typeitem:
                                        typeitem = "@type args: tuple"
                                else:
                                    typeitem = "@type " + typeitem + ": " + mytype
                                docstring += next_line.count(" ") * " " + typeitem + "\n"

                        if empty:
                            line_redone += "\n" + line.replace('"""', "") + emptydocstring.strip()
                        else:
                            docstring += next_line.count(" ") * " " + "@return: None"

                            line_redone += "\n" + line.replace('"""', "") + docstring.lstrip()

    if "]" in line and not "[]" in line:
        if line.rfind("]") > line.rfind('"'):
            if datastructure_define:
                debuginfo += " end datastructure_define"
            datastructure_define = False
    if prev_line.strip() == "]":
        debuginfo += " prevline is ]"
        add_enter = True

    if datastructure_define and ("=" not in line):
        debuginfo += " in datastructure_define"
        add_double_enter = False
        add_enter = False
    if in_python_comment:

        debuginfo += " in in_python_comment"
        add_double_enter = False
        #add_enter = False

        if line.strip().startswith("@param") and "args" not in line:
            if not next_line.strip().startswith("@type"):
                line_redone += "\n" + org_line.split("@param")[0] + "@type " + line.strip().split("@param")[1].split(":")[0].strip() + ": "

    if add_docstring and fname.endswith(".py") and not in_python_comment:

        line_redone += "\n"
        line_redone += " " * (whitespace(line) + 4)
        line_redone += '"""\n'
        line_redone += " " * (whitespace(line) + 4)

        line_redone += '"""\n'

    if not in_method_param_list and not in_python_comment and line.strip() != '"""' and prev_line.strip() != '"""' and not assignment(line) and not func_def(line) and not "alias" in line:
        alike = almost_alike(line, prev_line, scoped)

        if alike > 0:
            if datastructure_define is False:
                add_enter = False
                add_double_enter = False
                debuginfo = "almost alike"
        elif alike < 0 and scoped == 0:
            if datastructure_define is False:
                add_enter = True
                add_double_enter = False
                debuginfo = "almost alike is over"
        debuginfo += " alike:" + str(alike)
    if "alias " in line:
        add_enter = False
        add_double_enter = False
    if line.startswith("__"):
        debuginfo += " module declaration"
        if prev_line.startswith("__"):
            debuginfo += " after module declaration"
            add_enter = False
            add_double_enter = False
        else:
            debuginfo += " first"
            add_enter = True
            add_double_enter = False

    debuginfo = debuginfo.replace("  ", " ")

    return in_python_comment, add_double_enter, add_enter, debuginfo, resolve_func, if_cnt, line_redone, in_method_param_list, in_python_comment_cnt


def coffeescript_pretty_printer_emitter(add_double_enter, add_enter, cnt, line, mylines, prev_line):
    # print debuginfo, add_enter, add_double_enter
    """

    @param add_double_enter:
    @param add_enter:
    @param cnt:
    @param line:
    @param mylines:
    @param prev_line:
    @return: @rtype:
    """
    global datastructure_define

    if add_double_enter:
        cont = True
        # if cnt - 1 > 0:
        # if ".module" in prev_line:
        # cont = False

        if cont:
            if cnt - 1 > 0:
                if not len(prev_line.strip()) is 0:
                    line = "\n" + line
            if cnt - 2 > 0:
                if not len(mylines[cnt - 2].strip()) is 0:
                    line = "\n" + line
    if add_enter:
        if cnt - 1 > 0:
            if not len(prev_line.strip()) is 0:
                line = "\n" + line
    return line


def add_debuginfo(debuginfo, line):
    """

    @param debuginfo:
    @param line:
    @return: @rtype:
    """
    if line.strip().startswith("#"):

        return debuginfo, line
    if debuginfo:
        ef = line.find("\n")
        if ef > 0 and ef is not 0:
            line = line.rstrip("\n")
        if debuginfo.strip()=="0":
            print(debuginfo)
            print(line)
            raise RuntimeError()
        line = line + " # ##^ " + debuginfo.replace("i", "1").replace("return", "retrn")
        if ef > 0 and ef is not 0:
            line += "\n"
        debuginfo = ""

    return debuginfo, line


def sanatize_line(line, next_line):
    """

    @param line:
    @param next_line:
    @return: @rtype:
    """
    if not line.strip().startswith("<") and not (line.strip().endswith(",") or ")" in next_line) and not in_test([")", "|=", "=>", "!=", "hotkeys", "==", "$(", "?", "ng-", "trim", "ansible", "strip", "match", "split", "input", "type=", "/=", "\=", ":", "replace", "element", "if ", "b64", "padding", "vagrant", "--", "]"], line):
        line = line.replace("=>", "@>").replace("( ", "(").replace("@>", "=>").replace("< =", "<=").replace("> =", ">=").replace("+ =", "+=").replace("- =", "-=").replace("* =", "*=").replace("! =", "!=").replace('(" = ")', '("=")').replace('+ " = "', '+ "="')
        if not "+=" in line and not "++" in line:
            line = line.replace("+", " + ")
            line = line.replace("  +  ", " + ")
    for i in range(0, 10):
        line = line.replace("( ", "(")
        line = line.replace("  is  ", " is ")
        line = line.replace("  is not  ", " is ")
    line = line.replace("coding = utf-8", "coding=utf-8")
    line = line.replace("(by.", "(`by`.")
    line = line.replace("print ()", "print()")
    if line.strip().startswith("#") and not line.strip().startswith("# "):
        line = line.replace("#", "# ")
    line = line.replace("# !", "#!")
    line += "\n"
    return line


def coffeescript_pretty_print_resolve_function(add_enter, debuginfo, line, prev_line, resolve_func):
    """

    @param add_enter:
    @param debuginfo:
    @param line:
    @param prev_line:
    @param resolve_func:
    @return: @rtype:
    """
    if resolve_func:
        if anon_func(line) and in_test(["(", ")"], line) and not "= " in line:
            if resolve_func:
                if prev_line:
                    if not (".then" in prev_line or "->" in prev_line or "=>" in prev_line):
                        add_enter = True
                        debuginfo = "resolve func " + str(resolve_func)

        if line.strip() is ")":
            resolve_func = 0
            debuginfo = "resolve func stopped " + str(resolve_func)

    return add_enter, debuginfo, resolve_func


# noinspection PyUnusedLocal
def add_file_and_linenumbers_for_replace_vars(args, fname, line, location_id, orgfname, undo_variables, variables):
    """

    @param args:
    @param fname:
    @param line:
    @param location_id:
    @param orgfname:
    @param undo_variables:
    @param variables:
    @return: @rtype:
    """
    for replace_variable in variables:
        # if "print_once" in line:
        # line = line.replace("print_once(", "print_once (")
        check_split = line.split(" ")
        check_split2 = []
        for i in check_split:
            check_split2.extend(i.split("("))

        check_split = [x.strip() for x in check_split2]

        found_color = False
        fname = fname.replace("/__init__.py", "")
        if replace_variable in check_split and len(line.strip()) > 0:
            if replace_variable + " = " not in line:
                if fname.endswith(".py"):
                    if "33m" in line:
                        found_color = True
                        line = line.replace('"\\033[33m" + log_date_time_string(),', "")
                        line = line.replace('"\\033[33m"', "")
                        line = line.replace('33m', "")
                        line = line.replace('log_date_time_string(),', "")
                        line = line.replace(", '\\033[m'", "")
                    else:
                        line = line.replace('log_date_time_string(),', "")
                if fname in line:
                    line2 = line.replace(fname, "")
                    lines = line2.split(",")

                    def lnr(code_line):
                        """ lnr
                        @param code_line:
                        """

                        for i in range(0, 10):
                            for var in variables:
                                code_line = code_line.replace(var + "  ", var + " ")
                        var_not_in_codeline = False

                        true_list = set()
                        for var in variables:
                            ts1 = var + ' ":'
                            ts2 = var + '(":'
                            true_list.add(ts1 in code_line or ts2 in code_line)

                        if len(true_list) == 1:
                            var_not_in_codeline = True

                        if var_not_in_codeline:
                            return code_line

                    lines = [i.strip() for i in lines if lnr(i)]

                    line = line2.split(replace_variable)[0]

                    line += replace_variable + " "
                    for linet in lines:
                        line += linet
                        line += ", "

                if replace_variable + "(msg" not in line and "do " not in line:
                    line = line.replace(replace_variable + "(", replace_variable)

                    location = fname + ":" + "@@@@"
                    location_id += 1

                    if replace_variable not in undo_variables:
                        line = line.replace(replace_variable, replace_variable + "(\"" + str(location) + "\",")
                    else:
                        line = line.replace(replace_variable, replace_variable + "(").replace("( \"", "(\"")

                for i in range(0, 20):
                    line = line.rstrip(",")
                    line = line.rstrip()
                question = False
                if "?" in line:
                    question = True
                    line = line.replace("?", "")
                if ".then" not in line:
                    line = line.rstrip(")")
                    if line.count("(") != line.count(")"):
                        for i in range(0, line.count("(") - line.count(")")):
                            line += ")"
                if question:
                    line += "?"

                if orgfname.endswith(".py"):
                    if found_color:
                        line = line.replace("print(", "print \"\\033[33m\" + log_date_time_string(), ")
                    else:
                        line = line.replace("print(", "print ")
                    if line.strip().startswith("print"):
                        line = line.replace("print(", "print ")
                        line = line[:len(line) - 1]
                else:
                    if "print(" in line:
                        line = line.replace("print(", "print ")
                        line = line[:len(line) - 1]
                    for i in range(0, 5):
                        line = line.replace("print  ", "print ")

                    if "print_once(" in line:
                        line = line.replace("print_once(", "print_once ")
                        line = line[:len(line) - 1]
                    if "print" in line:
                        line = line.replace("print", "console.log")

                if found_color:
                    line += ", '\\033[m'"

                line += "\n"
                line = line.replace('",', '", ')
                line = line.replace('",  ', '", ')

                if replace_variable == "throw":
                    line = line.replace(",", " +")

    return line


def arg_parse():
    """
    @return: @rtype:
    """
    parser = ArgumentParser()
    parser.add_argument("-f", dest="myfile")
    parser.add_argument("-t", dest="test")
    args = parser.parse_args()
    return args


def init_file(args):
    """

    @param args:
    @return: @rtype:
    """
    if args.myfile == "./":
        print("Focus is on debug panel pycharm")
        exit(1)
    myfile = None
    if args.myfile:
        if not os.path.exists(args.myfile):
            print("file does not exist:", args.myfile)
            exit(1)
        if os.path.isdir(args.myfile):
            print("is folder:", args.myfile)
            exit(1)

        myfile = open(args.myfile, encoding="utf-8")

        if args.myfile.strip().endswith(".go"):
            print("/usr/local/bin/gofmt -s=True -w " + args.myfile)
            os.system("/usr/local/bin/gofmt -s=True -w " + args.myfile)
            exit(0)

        content = ""
        for i in myfile:
            if str(i).strip() != "":
                content += i
        if "# # #" in content:
            print("\033[31mPatterns of '# # #' occurs in file, cannot handle this with the type commenting\033[0m")
            raise RuntimeError()
        if args.test is None:
            if args.myfile.endswith(".conf"):
                exit(0)
            #if args.myfile.endswith(".sh"):
            #    exit(0)

            open(args.myfile, "wt", encoding="utf-8").write(content)

        myfile = open(args.myfile, encoding="utf-8")
    else:
        print("no -f (file) given as argument")
        exit(1)
    buffer_string = ""
    num = 1
    orgfname = fname = os.path.basename(args.myfile)
    if "__init__" in fname:
        fname = "/".join(str(args.myfile).split("/")[-2:])
        if "__init__" in fname:
            fname = os.path.basename(os.getcwd())
            fname = fname + "/" + (str(orgfname))
            # fname = fname.replace("__init__.py", "")
            # fname = fname.replace("/:", ":")


    return buffer_string, fname, myfile, num, orgfname


# noinspection PyPep8Naming
def init_cp(args, fname, myfile):
    """

    @param args:
    @param fname:
    @param myfile:
    @return: @rtype:
    """
    fname = fname.replace("coffee", "cf")

    color_vals_to_keep, undo_variables, variables, watch_vars = replace_variables(fname)
    mylines = []

    # if fname.endswith(".py"):
    # variables.remove("event_emit")
    import io
    data = myfile.read()
    if "ADDTYPES" in data or "addtypes" in data:
        global ADDCOMMENT_WITH_FOUND_TYPE
        ADDCOMMENT_WITH_FOUND_TYPE = True
    for i in range(0, 10):
        data = data.replace("\n\n", "\n")
    data = data.replace(")->", ") ->")
    data = data.replace(")=>", ") =>")
    data = data.replace("\t", "    ")
    for line in data.split("\n"):
        mylines.append(line + "\n")
    cnt = 0
    location_id = 0

    if ".cf" not in fname and ".py" not in fname and ".html" not in fname and ".sh" not in fname:

        if str(args.myfile).endswith(".less"):
            myfile.seek(0)
            buffer_string = myfile.read()
            buffer_string = buffer_string.replace("}\n.", "}\n\n.").replace("}\n@media", "}\n\n@media").replace("}\n#", "}\n\n#").replace("  }\n  .", "  }\n\n  .").replace("}\n@", "}\n\n@").replace("}\nbody", "}\n\nbody")
            myfile.close()
            open(str(args.myfile), "wt", encoding="utf-8").write(buffer_string)
        if ".yml" in fname or ".yaml" in fname:
            buffer_string = ""
            myfile.seek(0)

            for line in myfile:

                if line.startswith("-"):
                    line = "\n" + line

                if "--" not in line:
                    line = line.replace("-\n", "-")

                if not line.startswith(" "):
                    buffer_string += "\n"
                if line.strip().endswith(":"):
                    buffer_string += "\n"
                if line.strip().endswith("drop-ins:"):
                    buffer_string += "\n\n\n\n"
                if line.strip().endswith("groups:"):
                    buffer_string += "\n\n\n\n"

                buffer_string += line
            buffer_string = buffer_string.replace(":\n\n-", ":\n-").strip().replace("\n\n---\n\n", "\n---\n").replace("---\n\n", "---\n").replace("\n  - ", "\n\n  - ").replace(":\n\n    - ", ":\n    - ").replace("\n    - ", "\n\n    - ").replace(":\n\n    - ", ":\n    - ").replace(":\n\n", ":\n").replace("\n\n\n\n\n", "").replace("\n\n#", "\n#")
            cnt = 50
            for i in range(1, 50):

                cnt = 50 - i
                spaces = " " * cnt
                print(cnt, "[" + "-" + spaces + "]")
                buffer_string = buffer_string.replace("- "+spaces, "- ")
            open(str(args.myfile), "wt", encoding="utf-8").write(buffer_string)
        myfile.close()
        exit(0)
        # mylines = open(args.myfile)
        # mylines = cStringIO.StringIO(data)


    resolve_func = 0
    debuginfo = ""
    in_if = False
    first_method_factory = first_method_class = False
    return StringIO, cnt, color_vals_to_keep, debuginfo, first_method_class, first_method_factory, fname, in_if, location_id, mylines, resolve_func, undo_variables, variables, watch_vars


def prepare_line(cnt, line, mylines):
    """

    @param cnt:
    @param line:
    @param mylines:
    @return: @rtype:
    """
    prev_line = ""
    next_line = ""
    if cnt > 1:
        prev_line = mylines[cnt - 1]
    line = line.replace("# # ^", "## ^")

    if len(mylines) > cnt + 1:
        next_line = mylines[cnt + 1]
    scoped = scope_diff(line, prev_line)
    ls = line.split("# ##^ ")
    ltemp = ls[0].rstrip()
    if ADDCOMMENT_WITH_FOUND_TYPE:
        if ltemp.strip() == "" and len(ls) > 0:
            ltemp = line
    line = ltemp
    line = line.replace("\n", "")
    add_enter = add_double_enter = False

    # line = line.replace("console.log ", "console?.log? ")
    # line = line.replace("console?.log", "console?.log")
    # line = line.replace("console?.log?", "print")
    line = line.replace("# noinspection", "#noinspection")
    next_line = next_line.replace("# noinspection", "#noinspection")
    prev_line = prev_line.replace("# noinspection", "#noinspection")

    # line = line.replace("console.log", "print")

    return add_double_enter, add_enter, line, next_line, prev_line, scoped


def exceptions_coffeescript_pretty_printer(add_double_enter, add_enter, cnt, debuginfo, line, next_line, prev_line, scoped, if_cnt, in_python_comment):
    """


    @param prev_line:
    @param add_double_enter:
    @param add_enter:
    @param cnt:
    @param debuginfo:
    @param line:
    @param next_line:
    @param scoped:
    @param if_cnt:
    @return: @rtype:
    """
    global g_is_python
    if comment(line):
        if line.find(" ") > 0:
            add_double_enter = True

        if debuginfo:
            if comment(prev_line):
                add_double_enter = False
                debuginfo += " another comment "
            else:
                debuginfo += "comment -> " + debuginfo
        else:
            debuginfo += "comment line"
            if g_is_python:
                if line.find(" ") > 0:
                    debuginfo += " module level"
                    add_enter = False
                    add_double_enter = False

        if not comment(prev_line) and not "else" in prev_line and not func_def(prev_line) and not anon_func(prev_line) and not prev_line.strip().startswith("if "):
            debuginfo += " comment after something"
            add_double_enter = False
            add_enter = True
            assignment_on_global_prefix = line.strip().strip("#")[:2]
            if g_last_assignment_on_global_prefix != assignment_on_global_prefix:
                if line.find(" ") > 0:
                    debuginfo += " different prefix "
                    add_enter = True
                    add_double_enter = False
            else:
                if line.find(" ") > 0:
                    add_enter = True
                    debuginfo += " module level" + g_last_assignment_on_global_prefix + "|" + line.strip()[:2]
                add_double_enter = False

    if add_double_enter:
        debuginfo += " double disables add_enter"
        add_enter = False


    elif cnt > 1:
        if line.strip() != "":
            if scoped >= 3:
                if not class_method(line):
                    if not add_double_enter:
                        debuginfo += " triple scope change in_pythoncomment:" + str(in_python_comment)
                        add_enter = True


                    if elif_switch(line):
                        debuginfo += " in elif switch"
                        add_enter = False

                    if next_line:
                        if "else" not in line:
                            debuginfo += " scope level " + str(line.find(" "))
                            add_enter = True
                            if line.find(" ") != 0:
                                debuginfo += " root "
                                add_enter = False
                                add_double_enter = True
                    if len(line.strip()) <= 2:
                        add_enter = False
                        debuginfo += " some closing tag"
                        if line.strip() == "]" and not g_is_python:
                            debuginfo = "coffeescript data or module block end"
                            add_enter = False
                            add_double_enter = False

    # debuginfo += " ifcnt:" + str(if_cnt) + " double_enter:" + str(add_double_enter)+ " add_enter:" + str(add_enter)
    add_double_enter, add_enter, debuginfo = in_python_comment_test(add_double_enter, add_enter, debuginfo, in_python_comment, line, next_line, prev_line)
    return add_double_enter, add_enter, debuginfo, line


def in_python_comment_test(add_double_enter, add_enter, debuginfo, in_python_comment, line=None, nextline=None, prevline=None):
    if line is not None:
        if line.strip().startswith('"""'):
            in_python_comment = True

    if in_python_comment is True:
        if line is not None:
            debuginfo += " com"+str(line.strip().startswith('"""'))
        debuginfo += " (in p comment) "
        if line and '"""' not in line:
            add_double_enter = False
            add_enter = False
        else:
            debuginfo += " python comment"
        #if nextline.strip().startswith("#"):
        add_enter = False
        if prevline and not prevline.strip().startswith("#") and line.strip().startswith("#"):
            add_enter = True
        if prevline and prevline.strip().startswith("["):
            add_enter = False
        if line and line.strip().startswith("["):
            add_double_enter = True
        if prevline and prevline.strip().startswith("["):
            add_enter = False
    return add_double_enter, add_enter, debuginfo


# noinspection PyPep8Naming
def main(args):
    """
        main function
    @param args:
    """
    if "cp.py" in args.myfile.strip().lower():
        print("can't cp myself")
        return

    # print "cp.py -f", os.path.basename(os.path.dirname(args.myfile)) + "/" + os.path.basename(args.myfile)

    buffer_string, fname, myfile, num, orgfname = init_file(args)

    StringIO, cnt, color_vals_to_keep, debuginfo, first_method_class, first_method_factory, fname, in_if, location_id, mylines, resolve_func, undo_variables, variables, watch_vars = init_cp(args, fname, myfile)

    line_cnt = 0
    if_cnt = 0
    in_python_comment_cnt = 0
    in_python_comment = False
    in_method_param_list = False
    for line in mylines:

        line_cnt += 1

        for v in watch_vars:
            if v.lower() in line.lower():
                print(line)

        process_line = True

        if "console" in line:
            for i in range(0, line.count("if running_local()")):
                line = line.replace("if running_local()", "")
            line = line.replace("log?  ", "log? ")

        add_double_enter, add_enter, line, next_line, prev_line, scoped = prepare_line(cnt, line, mylines)

        in_python_comment, add_double_enter, add_enter, debuginfo, resolve_func, if_cnt, line, in_method_param_list, in_python_comment_cnt = coffee_script_pretty_printer(add_double_enter, add_enter, first_method_class, first_method_factory, line, next_line, prev_line, resolve_func, scoped, if_cnt, in_python_comment, fname, in_method_param_list, mylines, line_cnt, in_python_comment_cnt)

        add_double_enter, add_enter, debuginfo, line = exceptions_coffeescript_pretty_printer(add_double_enter, add_enter, cnt, debuginfo, line, next_line, prev_line, scoped, if_cnt, in_python_comment)

        add_enter, debuginfo, resolve_func = coffeescript_pretty_print_resolve_function(add_enter, debuginfo, line, prev_line, resolve_func)

        # if ".cf" in fname:
        line = coffeescript_pretty_printer_emitter(add_double_enter, add_enter, cnt, line, mylines, prev_line)

        if not ADDCOMMENT_WITH_FOUND_TYPE:
            debuginfo = ""

        debuginfo, line = add_debuginfo(debuginfo, line)

        if args.myfile.endswith(".sh"):


            bashreplacements1 = [(" + ", "+"), (" - ", "-"), (" = ", "=")]
            bashreplacements2 = [(x[0], x[1]) for x in bashreplacements1 if "==" not in x]

            bashreplacements = bashreplacements1
            bashreplacements.extend(bashreplacements2)

            for br in bashreplacements:
                line = line.replace(br[0], br[1])
            line += "\n"
        elif args.myfile.strip().endswith(".py") and not in_python_comment:
            line = sanatize_line(line, str(next_line))
        else:
            line += "\n"

        if process_line:
            line = add_file_and_linenumbers_for_replace_vars(args, fname, line, location_id, orgfname, undo_variables, variables)


        buffer_string += line
        num += 1
        cnt += 1

    myfile.close()

    buffer_string = buffer_string.rstrip()

    if not buffer_string.startswith("#"):
        buffer_string = "\n" + buffer_string
    sio_file2 = io.StringIO(buffer_string)
    # open(args.myfile, "w").write()

    num = 0
    buffer_string = ""
    for line in sio_file2:

        line = line.replace("@@@@", str(num))
        line = line.replace("#noinspection", "# noinspection")
        num += 1
        if line.strip() != "#" and line.strip() != "debugger;" and line.strip() != "debugger":
            buffer_string += line

    if not args.test:
        if str(args.myfile).endswith(".coffee"):
            finalbuf = buffer_string.rstrip() + "\n"
            open(args.myfile, "wt", encoding="utf-8").write(finalbuf)

        else:
            open(args.myfile, "wt", encoding="utf-8").write(buffer_string.rstrip() + "\n")
    else:
        print("file not written (test run)")

    if args.myfile.endswith(".py"):
        if "addtypes" not in buffer_string:
            os.system("autopep8 --in-place --max-line-length=440 --aggressive "+args.myfile)
            buf = open(args.myfile, encoding="utf-8").read()
            buf = buf.replace("class Meta(object):\n\n", "class Meta(object):\n")
            buf = buf.replace("class Meta:\n\n", "class Meta(object):\n")
            buf = buf.replace('):\n\n    """', '):\n    """')
            buf = buf.replace('"""\n\n    def', '"""\n    def')
            if "# coding=utf-8" not in buf:
                buf = "# coding=utf-8\n"+buf
            open(args.myfile, "wt", encoding="utf-8").write(buf)
    elif args.myfile.endswith(".sh") or 'bash' in args.myfile:
        buf = open(args.myfile, encoding="utf-8").read()
        buf = buf.replace(" = (", "=(")
        buf = buf.replace("=(", "=(\t")
        buf = buf.replace("\nfunction", "function")
        open(args.myfile, "wt", encoding="utf-8").write(buf)

def lock_acquire(key):
    """

    @param key:
    """
    lfile = key + ".lock"
    cnt = 0

    while os.path.exists(lfile):
        time.sleep(0.1)
        cnt += 1
        if cnt > 200:
            os.remove(lfile)
    open(lfile, "w").write("x")


def lock_release(key):
    """

    @param key:
    @return: @rtype:
    """
    lfile = key + ".lock"
    if os.path.exists(lfile):
        # noinspection PyBroadException
        try:
            os.remove(lfile)
        except:
            pass
        return True
    return True


if __name__ == "__main__":
    args = arg_parse()

    if args.myfile is not None:
        lock = os.path.dirname(os.path.join(os.getcwd(), args.myfile)) + "/cp"
        try:
            lock_acquire(lock)

            main(args)
            main(args)
        finally:
            lock_release(lock)

""" add linenumbers to coffee """

import os
from argparse import ArgumentParser

ADDCOMMENT_WITH_FOUND_TYPE = True

def func_test(funcs, line):
    for func in funcs:
        res = func(line)
        if res:
            return True
    return False


def anon_func(line):
    line = str(line)
    return "->" in line or "=>" in line


def anon_func_param(line):
    line = str(line)
    return "(" in line and ")" in line and anon_func(line)


def func_def(line):
    line = str(line)
    return ("->" in line or "=>" in line) and "=" in line


def method_call(line):
    line = str(line)
    return (("(" in line and ")" in line)) or ("$(this)." in line and line.find("(") > 1 and line.find(")") > 1)


def class_method(line):
    line = str(line)
    return ("->" in line or "=>" in line) and ":" in line


def scoped_method_call(line):
    line = str(line)
    return ("=" in line and ("->" in line or "=>" in line)) or ("$scope." in line and "()" in line and line.find("     ") is not 0)


def some_func(line):
    return func_test([func_def, class_method, scoped_method_call], line)


def assignment(line):
    line = line.strip()
    if line.count("=") is 1 and not some_func(line):
        return True
    return False


def data_assignment(line, prev_line):
    lvalue = "-"
    if '["' in line and '"]' in line:
        line = line.replace('["', ".")
        prev_line = prev_line.replace('["', ".")
    if "." in line:
        lvalue = line.split(".")[0].strip()
    if "." in prev_line:
        rvalue = "|"
        rvalue = prev_line.split(".")[0].strip()
        return lvalue in rvalue
    else:
        return False


def ws(line):
    cnt = 0
    for i in line:
        if i != " ":
            return cnt
        cnt += 1
    return cnt


def scope_diff(line, prev_line):
    if not prev_line:
        return 0

    lws = ws(line)
    pws = ws(prev_line)
    dif = (pws - lws) / 4

    return dif


def in_test(items, line):
    for item in items:
        if item in line:
            return True
    return False


def in_test_result(items, line):
    for item in items:
        if item in line:
            return item
    return None


def is_test(items, line):
    for item in items:
        if item is line.strip():
            return True
    return False


def main():
    """
        main function
    """

    parser = ArgumentParser()
    parser.add_argument("-f", dest="myfile")
    parser.add_argument("-r", dest="reverse")
    args = parser.parse_args()

    if args.myfile:
        myfile = open(args.myfile, "r")
    else:
        print "no -f (file) given as argument"
        return

    buffer_string = ""
    num = 1

    orgfname = fname = os.path.basename(args.myfile)

    if "__init__" in fname:
        fname = "/".join(str(args.myfile).split("/")[-2:])
        fname = fname.replace("__init__.py", "")
        fname = fname.replace("/:", ":")

    variables = ["print", "cvar.set", "throw", "cvar.commit_set", "clientcookies.del", "memory.get_promise", "cvar.mem_get", "cvar.get", "cvar.del", "urls.command", "urls.http_error", "clientcookies.set_no_warning", "clientcookies.set", "urls.make_route", "set_document_location", "urls.change_route", "clientcookies.get", "memory.set_no_warning", "memory.set", "memory.get", "memory.del"]
    ignore_variables = ['91m', '92m', '94m', '95m', '41m']

    mylines = []
    fname = fname.replace("coffee", "cf")

    data = myfile.read()
    for i in range(0, 10):
        data = data.replace("\n\n", "\n")
    data = data.replace(")->", ") ->")
    data = data.replace(")=>", ") =>")
    for line in data.split("\n"):
        mylines.append(line + "\n")

    cnt = 0
    location_id = 0

    if ".cf" not in fname:
        myfile.close()
        mylines = open(args.myfile, "r")

    resolve_func = False
    debuginfo = ""
    in_if = False
    first_method_factory = first_method_class = False

    for line in mylines:
        process_line = True
        if ".cf" in fname:
            prev_line = None
            next_line = None

            if cnt > 1:
                prev_line = mylines[cnt - 1]
            if next_line:
                next_line = mylines[cnt + 1]

            scoped = scope_diff(line, prev_line)

            ls = line.split("#@")

            ltemp = ls[0].rstrip()
            if ADDCOMMENT_WITH_FOUND_TYPE:
                if ltemp.strip() == "" and len(ls) > 0:
                    ltemp = line
            line = ltemp

            line = line.replace("\n", "")
            if "=>" not in line:
                line = line.replace("==", " is ")
            add_enter = add_double_enter = False

            if "if " in line and not in_if:
                in_if = True

            if ".factory" in line:
                add_double_enter = True
                first_method_factory = True
                debuginfo = ".factory"
            elif "_.map" in line:
                debuginfo = ".map"
                add_enter = True
            elif class_method(line):
                if first_method_class:
                    debuginfo = "classmethod " + str(first_method_class)
                    first_method_class = False
                    if "class" in prev_line:
                        add_enter = False
                    else:
                        add_enter = True
                elif first_method_factory:
                    debuginfo = "factorymethod " + str(first_method_factory)
                    first_method_factory = False
                    add_enter = True
                else:
                    add_double_enter = True
            elif ".then" in line:
                debuginfo = "resolve method body"
                resolve_func = True
                if prev_line:
                    if not in_test(["if", "else", "->", "=>"], prev_line):
                        add_enter = True
            elif func_def(line) and not resolve_func:
                debuginfo = "function def"
                if line.find(" ") is not 0:
                    add_double_enter = True
                else:
                    if not func_def(prev_line):
                        debuginfo = "function def nested first"
                        add_enter = True
            elif scoped_method_call(line):
                if prev_line:
                    if not func_test([method_call, class_method], prev_line.strip()) and not in_test([".then", "if", "->", "=>", "else"], prev_line):
                        debuginfo = ".method define or scoped method call"
                        if line.find(" ") is not 0:
                            if len(prev_line) > 0:
                                add_double_enter = True
                            else:
                                add_enter = True
                        else:
                            add_enter = True
                if resolve_func:
                    debuginfo = "resolveresult"
            elif anon_func(line) and not in_test([".directive", "$watch"], line):
                if not resolve_func:
                    debuginfo = "anonymousfunction"
                    if line.find(" ") is not 0:
                        add_double_enter = True
                else:
                    debuginfo = "resolveresult"
            elif  ("if" in line and line.strip().find("if") is 0) or in_test(["switch", "when", "while"], line):
                debuginfo = in_test_result(["switch", "when", "while", "if"], line) + " statement"
                if prev_line:
                    if not in_test(["when", "if", "->", "=>", "else"], prev_line):
                        add_enter = True
                    else:
                        debuginfo += " denied by " + in_test_result(["when", "if", "->", "=>", "else"], prev_line)
            elif method_call(line):
                debuginfo = ""
                if assignment(line):
                    debuginfo += "assigned "

                if line.find(" ") is not 0:
                    debuginfo += "method call global scope"
                    add_enter = False
                    add_double_enter = True

                elif prev_line:
                    if method_call(prev_line):
                        if ws(line) < ws(prev_line):
                            debuginfo += "method call higher scope"
                            add_enter = True
                        else:
                            debuginfo += "nested method call"
                    elif not func_test([func_def, scoped_method_call, method_call, class_method], prev_line.strip()):
                        debuginfo += "method call"
                        if data_assignment(line, prev_line):
                            debuginfo += "method call data assignment"
                        else:
                            if assignment(prev_line):
                                debuginfo += "method call after assignment"
                            else:
                                debuginfo += "method call"
                                add_enter = True
                        if in_test(["$watch", "if", "else"], prev_line.strip()):
                            debuginfo += "method call after 1f 3lse or w@tch"
                            add_enter = False
                            add_double_enter = False
                    else:
                        debuginfo += "method call nested "
                        add_enter = False

            elif assignment(line):
                debuginfo = "assignment"
            elif in_test(["class"], line):
                first_method_class = True
                debuginfo = "class"
                add_double_enter = True
            elif "except" in line:
                debuginfo = "except"
                add_enter = True
            elif line.lstrip().startswith("$scope") and in_test(["->", "=>"], line):
                debuginfo = "scoped method define"
                if prev_line:
                    if not ")" is prev_line.strip():
                        add_enter = True
            elif "#noinspection" in line:
                debuginfo = "no-inspection"
                add_enter = True
            elif "raise" in line:
                debuginfo = "raise"
                add_enter = True
            elif "try" in line:
                debuginfo = "try"
                add_enter = True
            elif "angular.module" in line:
                debuginfo = "angular module"
                add_double_enter = True
            elif "_.filter" in line:
                add_enter = True
                debuginfo = ".filter"
            elif "_." in line or "$." in line:
                if prev_line:
                    if not ("_." in prev_line or "$." in prev_line or "if" in prev_line):
                        if not resolve_func:
                            add_enter = True
                            debuginfo = ".each"
            elif ".directive" in line:
                add_enter = True
                debuginfo = ".directive"
            elif line.lstrip().startswith("f_") and (line.endswith("->") or line.endswith("=>")):
                add_double_enter = True
            elif "setInterval" in line or "setTimeout" in line:
                debuginfo = "setInterval timeout"
                add_enter = True
            elif "return" in line:
                debuginfo = "return"
                if prev_line and next_line:
                    if (prev_line.strip() == "") or ("else" in prev_line) or ("else" in next_line) and not in_test(["setInterval", "setTimeout"], prev_line):
                        pass
                    if is_test([")"], prev_line.strip()) or in_test(["_.filter", "_.map"], prev_line):
                        add_enter = True
                    else:
                        if next_line and not in_test(["setInterval", "setTimeout"], prev_line):
                            if "class" not in next_line or len(next_line) > 0:
                                pass
            elif cnt > 1:
                if line.strip() != "":
                    if scoped >= 2:
                        debuginfo = "double scope change"
                        if next_line:
                            if "else" not in line:
                                add_enter = True
            elif in_if:
                if cnt > 1:
                    if "else" not in line and scoped >= 1:
                        debuginfo = "double scope change in if statement"
                        in_if = False
                        add_enter = True
            if "throw" in line:
                print "WARNING THROW", line
                line = line.replace("(", " ").replace(")", " ").replace("throw", "warning")

            if resolve_func:
                if anon_func(line):
                    if resolve_func:
                        if prev_line:
                            if not (".then" in prev_line or "->" in prev_line or "=>" in prev_line):
                                add_enter = True
                                debuginfo = "resolve func"

                if line.strip() is ")":
                    debuginfo = "resolve func stopped"
                    resolve_func = False
            elif "print" in line:
                debuginfo = "debug statement"

            if ".cf" in fname:
                #print debuginfo, add_enter, add_double_enter
                if add_double_enter:
                    cont = True
                    if cnt - 1 > 0:
                        #if "class" in prev_line:
                        #    cont = False
                        #if ".factory" in prev_line:
                        #    cont = False
                        if ".module" in prev_line:
                            cont = False

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

            if not ADDCOMMENT_WITH_FOUND_TYPE:
                debuginfo = None

            if debuginfo:
                ef = line.find("\n")
                if ef > 0 and ef is not 0:
                    line = line.rstrip("\n")
                line = line + " #@ " + debuginfo
                if ef > 0 and ef is not 0:
                    line += "\n"
                debuginfo = None

            line = line.replace(" != ", " is not ")
            if "=>" not in line and "!=" not in line:
                line = line.replace("=>", "@>").replace("=", " = ").replace("  =", " =").replace("=  ", "= ").replace("@>", "=>").replace("< =", "<=").replace("> =", ">=").replace("+ =", "+=").replace("- =", "-=").replace("! =", "!=").replace('(" = ")', '("=")').replace('+ " = "', '+ "="')

            for i in range(0, 10):
                line = line.replace("  =", " =")
                line = line.replace("  is  ", " is ")
                line = line.replace("  is not  ", " is ")

            line = line + "\n"

        if orgfname.strip().endswith(".py"):
            for ignore_var in ignore_variables:
                if ignore_var in line:
                    process_line = False

        if process_line:
            for replace_variable in variables:
                check_split = line.split(" ")
                check_split2 = []
                for i in check_split:
                    check_split2.extend(i.split("("))

                check_split = [x.strip() for x in check_split2]

                if replace_variable in check_split and len(line.strip()) > 0:
                    if replace_variable + " = " not in line:
                        if fname.endswith(".py"):
                            line = line.replace('"\\033[93m" + log_date_time_string(),', "")

                        if fname in line:
                            line2 = line.replace(fname, "")
                            lines = line2.split(",")

                            def lnr(i):
                                """ lnr """
                                if ":" not in i:
                                    return i

                            lines = [i.strip() for i in lines if lnr(i)]
                            line = line2.split(replace_variable)[0]
                            line += replace_variable + " "
                            for linet in lines:
                                line += linet
                                line += ", "

                        if replace_variable + "(msg" not in line:
                            line = line.replace(replace_variable + "(", replace_variable)
                            if not args.reverse:
                                location = fname + ":" + "@@@@"
                                location_id += 1

                                line = line.replace(replace_variable, replace_variable + "(\"" + str(location) + "\",")
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
                            line = line + "?"

                        if orgfname.endswith(".py"):
                            line = line.replace("print(", "print \"\\033[93m\" + log_date_time_string(), ")
                            #line = line.replace("print(", "print ")
                            line = line[:len(line) - 1]
                        else:
                            if "print(" in line:
                                line = line.replace("print(", "print ")
                                line = line[:len(line) - 1]

                        line += "\n"
                        line = line.replace('",', '", ')
                        line = line.replace('",  ', '", ')

                        if replace_variable == "throw":
                            line = line.replace(",", " +")

                            #print line.strip()

        buffer_string += line
        num += 1
        cnt += 1

    myfile.close()
    open(args.myfile, "w").write("\n" + buffer_string.lstrip())

    num = 1
    buffer_string = ""
    for line in open(args.myfile, "r"):
        line = line.replace("@@@@", str(num))
        num += 1
        buffer_string += line

    open(args.myfile, "w").write("\n\n" + buffer_string.lstrip())

if __name__ == "__main__":
    main()

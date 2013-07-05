coffeescript-pretty-print
=========================

pretty printer for coffeescript and python

reformats coffeescript in a consistant way, usage

python cp.py -f yourfile.coffee

Also ads debugging info to printstatements (linenumber and sourcefile)

<pre>
print "hello world"
</pre>

becomes

<pre>
print "yourfile.cf:1", "helloworld"
</pre>

You can use this print method

<pre>

print = (msg, others...) ->
    if exist(window.globals["g_browser"])
        if window.globals["g_browser"].browser == 'Chrome'
            switch _.size(others)
                when 0
                    console?.log "%c" + msg, 'color: crimson', others
                when 1
                    console?.log "%c" + msg, 'color: crimson', others[0]
                when 2
                    if others[0].indexOf?(".cf") > 0
                        console?.log "%c" + msg + " " + others[0], 'color: crimson', others[1]
                    else
                        console?.log "%c" + msg, 'color: crimson', others[0], others[1]
                when 3
                    if others[0].indexOf?(".cf") > 0
                        console?.log "%c" + msg + " " + others[0], 'color: crimson', others[1], others[2]
                    else
                        console?.log "%c" + msg, 'color: crimson', others[0], others[1], others[2]
                when 4
                    console?.log "%c" + msg, 'color: crimson', others[0], others[1], others[2], others[3]
                else
                    console?.log others, msg

        else
            switch _.size(others)
                when 0
                    console?.log msg
                when 1
                    console?.log msg + " " + others[0]
                when 2
                    console?.log msg + " " + others[0] + " " + others[1]
                when 3
                    console?.log msg + " " + others[0] + " " + others[1] + " " + others[2]
                when 4
                    console?.log msg + " " + others[0] + " " + others[1] + " " + others[2] + " " + others[3]
                else
                    console?.log others, msg

    else
        console?.log msg, others
    if not exist_truth(window.cvar_show_debug_info)
        return
    if msg.replace?
        shortdate = "" + (get_local_time() - start_time) / 1000

        while shortdate.length < 6
            shortdate += " "

        shortdate += " "

        while msg.length < 22
            msg += " "

        msg = shortdate + msg
        others2 = []

        coffee2cf = (obj) ->
            if obj?
                if obj.replace?
                    return obj.replace(".cf", ".cf")
            return obj

        others = (coffee2cf(obj) for obj in others)
        others_length = others.length

        if others?
            cnt = 0

            loop_others = (i) ->
                if exist(i)
                    l = i.length
                else
                    l = "undefined".length
                if other_with[cnt]?
                    if other_with[cnt] < l
                        other_with[cnt] = l + 2
                else
                    other_with[cnt] = l + 2

                cnt += 1
            _.each(others, loop_others)
            print_str = ""
            cnt = 0

            spaces = (n) ->
                c = 0
                s = " "

                while c < n
                    s += " "
                    c += 1
                return s

            found_object = -1
            num_objects = 0
            create_print_string = (s) ->
                if _.isObject(s)
                    found_object = cnt
                    num_objects += 1
                else
                    if exist(s)
                        print_str += s + spaces(other_with[cnt] - s.length)
                    else
                        print_str += s + " "

                cnt += 1
            _.each(others, create_print_string)
            if found_object != -1
                if num_objects > 1
                    window.g_logfile.push(msg)
                else
                    window.g_logfile.push(msg + " " + print_str + " " + others[found_object])
            else
                window.g_logfile.push(msg + " " + print_str)
        else
            window.g_logfile.push(msg + " " + String(others))

        window.g_logfile = window.g_logfile[_.size(window.g_logfile) - 150..]
        return 1

</pre>

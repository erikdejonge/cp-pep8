coffeescript-pretty-print
=========================

pretty printer for coffeescript

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
    if msg.replace?
        msg = msg.replace(".cf", ".cf")
        others2 = []

        coffee2cf = (obj) ->
            if obj?
                if obj.replace?
                    return obj.replace(".cf", ".cf")
            return obj

        others = (coffee2cf(obj) for obj in others)
        others_length = others.length

        if others_length > 1
            if others[0]?
                if others[0].indexOf?
                    if others[0].indexOf(".cf") is not -1
                        msg = others[0]

                        if others_length > 1
                            others[0] = others[1]

                        if others_length > 2
                            others[1] = others[2]

                        if others_length > 3
                            others[2] = others[3]
                        others_length -= 1

        while msg.length < 20
            msg += " "

        if others?
            if others_length > 0
                switch others_length
                    when 1
                        console?.log? msg, others[0]

                    when 2
                        msg2 = others[0]

                        if msg2?
                            while msg2.length < 20
                                msg2 += " "
                            console?.log? msg, msg2, others[1]
                        else
                            console?.log? msg, others

                    when 3
                        msg2 = others[0]

                        while msg2.length < 20
                            msg2 += " "
                        console?.log? msg, msg2, others[1], others[2]

                    when 4
                        msg2 = others[0]
                        msg3 = others[1]

                        while msg2.length < 20
                            msg2 += " "

                        while msg3.length < 20
                            msg3 += " "
                        console?.log? msg, msg2, msg3, others[2], others[3]
                    else
                        console?.log? msg, others
            else
                console?.log? msg
        else
            console?.log? msg, others
        return 1
</pre>

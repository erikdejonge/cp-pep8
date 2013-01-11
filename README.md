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
    if msg.replace? #@if switch when while
        msg = msg.replace(".cf", ".cf") #@method call
        others2 = []

        coffee2cf = (obj) -> #@function def
            if obj? #@if switch when while
                if obj.replace? #@if switch when while
                    return obj.replace(".cf", ".cf") #@method call
            return obj #@return

        others = (coffee2cf(obj) for obj in others) #@method call
        others_length = others.length

        if others_length > 1 #@if switch when while
            if others[0]? #@if switch when while
                if others[0].indexOf? #@if switch when while
                    if others[0].indexOf(".cf") is not -1 #@if switch when while
                        msg = others[0]

                        if others_length > 1 #@if switch when while
                            others[0] = others[1]

                        if others_length > 2 #@if switch when while
                            others[1] = others[2]

                        if others_length > 3 #@if switch when while
                            others[2] = others[3]
                        others_length -= 1

        while msg.length < 20 #@if switch when while
            msg += " "

        if others? #@if switch when while
            if others_length > 0 #@if switch when while
                switch others_length #@if switch when while
                    when 1 #@if switch when while
                        console?.log? msg, others[0]

                    when 2 #@if switch when while
                        msg2 = others[0]

                        if msg2? #@if switch when while
                            while msg2.length < 20 #@if switch when while
                                msg2 += " "
                            console?.log? msg, msg2, others[1]
                        else
                            console?.log? msg, others

                    when 3 #@if switch when while
                        msg2 = others[0]

                        while msg2.length < 20 #@if switch when while
                            msg2 += " "
                        console?.log? msg, msg2, others[1], others[2]

                    when 4 #@if switch when while
                        msg2 = others[0]
                        msg3 = others[1]

                        while msg2.length < 20 #@if switch when while
                            msg2 += " "

                        while msg3.length < 20 #@if switch when while
                            msg3 += " "
                        console?.log? msg, msg2, msg3, others[2], others[3]
                    else
                        console?.log? msg, others
            else #@large pull back
                console?.log? msg
        else
            console?.log? msg, others
        return 1 #@return

</pre>


"use strict"
g_running_local = null
directive_check_timeout = 1000
directive_check_slow_timeout = 1000
window.base64 = {}
window.base64.PADCHAR = " = "
window.base64.ALPHA = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 + /"


ignore = (v) ->
    return v


translate = (k) ->
    return k


o2j = (obj) ->
    JSON.stringify(obj)


j2o = (json) ->
    JSON.parse(json)


pluck_exception = (error) ->
    loc = error.sourceURL || error.fileName
    line = error.lineNumber || error.line
    message = String(error)
    return [loc, line, message]


_splitlast = (str, splitter) ->
    s = String(str)
    sp = s.split(splitter)
    return sp[_.size(sp) - 1]


g_replace_all = (str, v1, v2) ->
    newstr = str
    while newstr.indexOf(v1) != -1
        newstr = newstr.replace(v1, v2)

    return newstr


exist_string = (value) ->
    if not value?
        return false
    else
        switch value
            when undefined, null, "null", "undefined"
                return false
            else
                return true


exist = (value) ->
    if _.isArray(value)
        if _.size(value) == 0
            return false

    if exist_string(value)
        if value == ""
            return false

        if String(value) == "NaN"
            return false

        if String(value) == "undefined"
            return false

        if value.trim?
            if value.trim() == ""
                return false
        return true
    else
        return false


pg = (v) ->
    if exist(v)
        if exist(window.globals[v])
            console?.log v, window.globals[v]
        else
            print_key = (k) ->
                if String(k).toLowerCase().indexOf(v.toLowerCase()) >= 0
                    console?.log v, "->", k, " -> ", window.globals[k]
                if String(window.globals[k]).toLowerCase().indexOf(v.toLowerCase()) >= 0
                    console?.log v, "->", k, " -> ", window.globals[k]

            _.each(_.keys(window.globals), print_key)
    else
        print_key = (k) ->
            console?.log k, window.globals[k]

        _.each(_.keys(window.globals), print_key)

    return ""


param_unused = (param) ->
    param


string_contains = (astring, val) ->
    String(astring).indexOf(val) != -1


startswith = (astring, val) ->
    String(astring).indexOf(val) == 0


endswith = (astring, val) ->
    astring.indexOf(val, astring.length - val.length) != -1


async_call = (func) ->
    _.delay(func, directive_check_timeout)


r_retrieve_kvs = (o, l_kvs) ->
    for item in o
        if _.isArray(item)
            r_retrieve_kvs(item, l_kvs)
        else
            for k in _.keys(item)
                if _.isObject(item[k])
                    r_retrieve_kvs([item[k]], l_kvs)
                else
                    if not exist(l_kvs[k])
                        l_kvs[k] = []

                    l_kvs[k].push(item[k])


list_contains_slow = (alist, val) ->
    contains = false
    item = null
    if not _.isArray(alist)
        contains = false
    else
        for i in alist
            if _.isString(i)
                contains = strcmp(i, val)

            else if _.isNumber(i)
                contains = (i==val)
            else
                if _.isArray(val)
                    for i2 in val
                        contains = (strcmp(o2j(i), o2j(i2)))
                else
                    contains = (strcmp(o2j(i), o2j(val)))

            if contains == true
                return [true, i]

        if contains == false
            for i in alist
                item = i
                if _.isObject(i)
                    kvs = {}
                    kvsv = {}
                    r_retrieve_kvs([i], kvs)

                    if _.isObject(val)
                        r_retrieve_kvs([val], kvsv)
                    else
                        kvsv['scalar'] = val

                    for k in _.keys(kvs)
                        for k2 in _.keys(kvsv)
                            for v in kvs[k]
                                contains = (strcmp(o2j(v), o2j(val)))

                                if not contains
                                    for v2 in kvsv[k2]
                                        contains = (strcmp(o2j(v2), o2j(val)))

                                if contains
                                    return [true, item]

        return [false, null]


list_contains = (alist, val) ->
    contains = false
    item = null
    if not _.isArray(alist)
        contains = false
    else
        check_vals = (i) ->
            if contains
                return

            if _.isString(i)
                contains = (i== val)

            else if _.isNumber(i)
                contains = (i==val)

            else if _.isArray(val)
                for i2 in val
                    contains = (i==i2)
            else
                contains = (i == val)

            if contains == true
                item = i

        _.each(alist, check_vals)

        if contains
            return [contains, item]
        else
            check_vals = (i) ->
                if _.isObject(i)
                    kvs = {}
                    kvsv = {}
                    r_retrieve_kvs([i], kvs)

                    if _.isObject(val)
                        r_retrieve_kvs([val], kvsv)
                    else
                        kvsv['scalar'] = val

                    check_keys = (k) ->
                        check_keys2 = (k2) ->
                            check_v = (v) ->
                                if contains
                                    return
                                else
                                    contains = (v==val)

                                    if contains
                                        if not exist(item)
                                            item = i

                                        return

                                    for v2 in kvsv[k2]
                                        contains = (v2== val)

                                        if contains
                                            if not exist(item)
                                                item = i

                                            return

                            _.each(kvs[k], check_v)

                        _.each(_.keys(kvsv), check_keys2)

                    _.each(_.keys(kvs), check_keys)

            _.each(alist, check_vals)

        return [contains, item]


padding = '='
chrTable = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
binTable = [
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1,
    -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, 62, -1, -1, -1, 63,
    52, 53, 54, 55, 56, 57, 58, 59, 60, 61, -1, -1, -1, 0, -1, -1,
    -1, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14,
    15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, -1, -1, -1, -1, -1,
    -1, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40,
    41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, -1, -1, -1, -1, -1
]


utf8Encode = (str) ->
    mybytes = []
    offset = 0
    mychar = undefined
    str = encodeURI(str)
    length = str.length

    while offset < length
        mychar = str[offset]
        offset += 1

        if "%" is mychar
            mychar = str[offset] + str[offset + 1]
            mybytes.push parseInt(mychar, 16)
            offset += 2
        else
            mybytes.push mychar.charCodeAt(0)

    return mybytes


utf8Decode = (mybytes) ->
    chars = []
    offset = 0
    length = mybytes.length
    c = undefined
    c2 = undefined
    c3 = undefined

    while offset < length
        c = mybytes[offset]
        c2 = mybytes[offset + 1]
        c3 = mybytes[offset + 2]

        if 128 > c
            chars.push String.fromCharCode(c)
            offset += 1
        else if 191 < c and c < 224
            chars.push String.fromCharCode(((c & 31) << 6) | (c2 & 63))
            offset += 2
        else
            chars.push String.fromCharCode(((c & 15) << 12) | ((c2 & 63) << 6) | (c3 & 63))
            offset += 3
    chars.join ""


encode_utf8_b64 = (str) ->
    result = ""
    mybytes = utf8Encode(str)
    length = mybytes.length
    # Convert every three mybytes to 4 ascii characters.
    i = 0
    while i < (length - 2)
        result += chrTable[mybytes[i] >> 2]
        result += chrTable[((mybytes[i] & 0x03) << 4) + (mybytes[i + 1] >> 4)]
        result += chrTable[((mybytes[i + 1] & 0x0f) << 2) + (mybytes[i + 2] >> 6)]
        result += chrTable[mybytes[i + 2] & 0x3f]
        i += 3
    # Convert the remaining 1 or 2 mybytes, pad out to 4 characters.
    if length % 3
        i = length - (length % 3)
        result += chrTable[mybytes[i] >> 2]
        if (length % 3) is 2
            result += chrTable[((mybytes[i] & 0x03) << 4) + (mybytes[i + 1] >> 4)]
            result += chrTable[(mybytes[i + 1] & 0x0f) << 2]
            result += padding
        else
            result += chrTable[(mybytes[i] & 0x03) << 4]
            result += padding + padding
    result


decode_utf8_b64 = (data) ->
    value = undefined
    code = undefined
    mybytes = []
    leftbits = 0 # number of bits decoded, but yet to be appended
    leftdata = 0 # bits decoded, but yet to be appended
    # Convert one by one.
    idx = 0

    while idx < data.length
        code = data.charCodeAt(idx)
        value = binTable[code & 0x7F]

        if -1 is value
            # Skip illegal characters and whitespace
            log "WARN: Illegal characters (code=" + code + ") in position " + idx
        else
            # Collect data into leftdata, update bitcount
            leftdata = (leftdata << 6) | value
            leftbits += 6
            # If we have 8 or more bits, append 8 bits to the result
            if leftbits >= 8
                leftbits -= 8
                # Append if not padding.
                mybytes.push (leftdata >> leftbits) & 0xFF  if padding isnt data.charAt(idx)
                leftdata &= (1 << leftbits) - 1
        idx++
    # If there are any bits left, the base64 string was corrupted
    if leftbits
        log "ERROR: Corrupted base64 string"
        return null
    return utf8Decode mybytes

if not window.btoa?
    base64_encode = window.base64.encode
else
    base64_encode = window.btoa

if not window.atob?
    base64_decode = window.base64.decode
else
    base64_decode = window.atob

unless String::trim
    String::trim = ->
        @replace /^\s+|\s+$/g, ""

String::startsWith = (suffix) ->
    @indexOf(suffix) is 0

String::endsWith = (suffix) ->
    @indexOf(suffix, @length - suffix.length) != -1

String::contains = (substr) ->
    @indexOf(substr) != -1


# Array Remove - By John Resig (MIT Licensed)

Array::remove = (from, to) ->
    rest = @slice((to or from) + 1 or @length)
    @length = (if from < 0 then @length + from else from)
    @push.apply this, rest


uri_b64 = (s) ->
    s = encodeURI(s)
    return base64_encode(s)


safe_b64 = (s) ->
    s = encodeURI(s)
    s = base64_encode(s)
    return s


strcmp = (s1, s2) ->
    if not exist_string(s1)
        return false

    if not exist_string(s2)
        return false

    if exist(s1.trim)
        s1 = s1.trim()

    if exist(s2.trim)
        s2 = s2.trim()

    return s1 == s2


exist_truth = (value) ->
    if exist(value)
        switch value
            when "0", 0
                return false
            when "1", 1
                return true
            when "false", false
                return false
            when "true", true
                return true
            else
                warning "app_basic.cf:453", "exist_truth neither true or false", value
                return false

    else
        #if document?.location?.pathname?.indexOf?("/context.html") < 0
        #    warning "app_basic.cf:458", "exist_truth value does not exist", value
        return false


b64safe = "data:b64:safe,"


b64_encode_safe = (s) ->
    if not exist(s)
        return s

    if not exist(s.indexOf)
        return s

    if s.indexOf(b64safe) == 0
        return s
    s = encodeURIComponent(s)
    s = base64_encode(s)
    s = s.replace /\=/g, "-"
    return b64safe + s


b64_decode_safe = (s) ->
    if not exist(s)
        return s

    if not exist(s.indexOf)
        return s
    if s.indexOf(b64safe) != 0
        return s
    s = s.replace(b64safe, "")
    s = s.replace /-/g, "="
    s = base64_decode(s)
    try
        s = decodeURIComponent(s)
    catch error
        s = "error decoding"

    return s


object_b64_safe = (v) ->
    set_var = (k) ->
        v[k] = object_b64_safe(v[k])

    if _.isObject(v)
        _.each(_.keys(v), set_var)
        return v
    else
        v = b64_encode_safe(v)
        return v


b64_object_safe = (v) ->
    set_var = (k) ->
        v[k] = b64_object_safe(v[k])

    if _.isObject(v)
        _.each(_.keys(v), set_var)
        return v
    else
        v = b64_decode_safe(v)
        return v


b64_uri = (s) ->
    s = base64_decode(s)
    return decodeURI(s)


pass = ->
    true


asciistring = (s) ->
    ns = ""
    testchar = (c) ->
        code = c.charCodeAt(0)

        switch true
            when code >= 48 and code <= 57
                ns += c
            when code >= 65 and code <= 90
                ns += c
            when code >= 97 and code <= 122
                ns += c
            when code == 32
                ns += c
            when code == 45
                ns += c
            when code == 38
                ns += c
            when code == 47
                ns += c
            when code == 46
                ns += c
            when code == 43
                ns += c
            when code == 8364
                ns += "€"
            else
                pass

    _.each(s, testchar)
    return ns


asciistring_no_specials = (s) ->
    ns = ""
    testchar = (c) ->
        code = c.charCodeAt(0)

        switch true
            when code >= 48 and code <= 57
                ns += c
            when code >= 65 and code <= 90
                ns += c
            when code >= 97 and code <= 122
                ns += c
            when code == 32
                ns += c
            when code == 45
                ns += c
            when code == 38
                ns += c
            when code == 43
                ns += c
            when code == 214
                ns += "O"
            when code == 246
                ns += "o"
            when code == 47
                ns += c
            when code == 8364
                ns += "EUR "
            else
                ns += ""

    #print code, c
    _.each(s, testchar)

    if not ns?
        return ""
    else
        return ns


asciistring_lowercase = (s) ->
    s = s.toLowerCase()
    return asciistring(s)


asciistring_lowercase_nospace = (s) ->
    s = asciistring_no_specials(s)
    ns = ""
    stripspace = (i) ->
        if i != ' '
            ns += i

    _.each(s, stripspace)
    return ns


g_format_file_size = (mybytes) ->
    if mybytes == 0
        return "-"

    if typeof mybytes != "number"
        mybytes = parseFloat(mybytes)

    if mybytes >= Math.pow(2, 40)
        return (mybytes / Math.pow(2, 40)).toFixed(2) + " tb"

    if mybytes >= Math.pow(2, 30)
        return (mybytes / Math.pow(2, 30)).toFixed(2) + " gb"

    if mybytes >= Math.pow(2, 20)
        return (mybytes / Math.pow(2, 20)).toFixed(2) + " mb"

    if mybytes >= Math.pow(2, 10)
        return (mybytes / Math.pow(2, 10)).toFixed(2) + " kb"

    (mybytes).toFixed(0) + " b."


get_s4_num = ->
    num = Math.floor(Math.random() * 0x10000).toString 16
    return num


get_guid = ->
    get_s4_num() + get_s4_num() + "-" + get_s4_num() + "-" + get_s4_num() + "-" + get_s4_num() + "-" + get_s4_num() + get_s4_num() + get_s4_num()


get_local_time = ->
    t = new Date().getTime() / 1000

    if exist(window.globals)
        if exist(window.globals["g_corrected_servertime"])
            t = window.globals["g_corrected_servertime"]

    return t


get_version = ->
    return "$$unique_id$$"


unique_number = ->
    if running_local()
        new Date().getTime()
    else
        get_version()


window.cvar_show_debug_info = false
other_with = {}
window.g_logfile = []


start_time = get_local_time()


print = (msg, others...) ->
    if exist(window.globals) and ("g_browser" in _.keys(window.globals)) and (window.globals["g_browser"].browser == 'Chrome')
        switch _.size(others)
            when 0
                console?.log "%c" + msg, 'color: crimson', others
            when 1
                console?.log "%c" + msg, 'color: crimson', others[0]
            when 2
                if String(others[0]).indexOf?(".cf") > 0
                    console?.log "%c" + msg + " " + others[0], 'color: crimson', others[1]
                else
                    console?.log "%c" + msg, 'color: crimson', others[0], others[1]
            when 3
                if String(others[0]).indexOf?(".cf") > 0
                    console?.log "%c" + msg + " " + others[0], 'color: crimson', others[1], others[2]
                else
                    console?.log "%c" + msg, 'color: crimson', others[0], others[1], others[2]
            when 4
                if String(others[0]).indexOf?(".cf") > 0
                    console?.log "%c" + msg + " " + others[0], 'color: crimson', others[1], others[2], others[3]
                else
                    console?.log "%c" + msg, 'color: crimson', others[0], others[1], others[2], others[3]
            when 5
                if String(others[0]).indexOf?(".cf") > 0
                    console?.log "%c" + msg + " " + others[0], 'color: crimson', others[1], others[2], others[3], others[4]
                else
                    console?.log "%c" + msg, 'color: crimson', others[0], others[1], others[2], others[3], others[4]
            else
                console?.log others, msg

    else
        switch _.size(others)
            when 0
                console?.log msg
            when 1
                console?.log msg, others[0]
            when 2
                console?.log msg, others[0], others[1]
            when 3
                console?.log msg, others[0], others[1], others[2]
            when 4
                console?.log msg, others[0], others[1], others[2], others[3]
            when 5
                console?.log msg, others[0], others[1], others[2], others[3], others[4]
            else
                console?.log others, msg

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
        coffee2cf = (obj) ->
            if obj?
                if obj.replace?
                    return obj.replace(".cf", ".cf")
            return obj
        others = (coffee2cf(obj) for obj in others)

        if not others?
            window.g_logfile.push(msg + " " + String(others))
        else
            cnt = 0
            loop_others = (i) ->
                if exist(i)
                    l = i.length
                else
                    l = "undefined".length

                if not other_with[cnt]?
                    other_with[cnt] = l + 2
                else
                    if other_with[cnt] < l
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

            if found_object == -1
                window.g_logfile.push(msg + " " + print_str)
            else
                if num_objects > 1
                    window.g_logfile.push(msg)
                else
                    window.g_logfile.push(msg + " " + print_str + " " + others[found_object])

        window.g_logfile = window.g_logfile[_.size(window.g_logfile) - 150..]
        return 1


warning = (msg, others...) ->
    console?.log '%c------ important ' + msg + ' ---------', 'color: red'

    switch _.size(others)
        when 0
            console?.log others
        when 1
            console?.log others[0], "\t\t"
        when 2
            console?.log others[0], others[1], "\t\t"
        when 3
            console?.log others[0], others[1], others[2], "\t\t"
        when 4
            console?.log others[0], others[1], others[2], others[3], "\t\t"
        else
            console?.log others

    if exist(console.trace)
        console?.trace()

    console?.log '%c------------------------------------------------', 'color: red'


async_call_retries = (msg, func, retries, max_retries) ->
    if not exist(max_retries)
        max_retries = 200

    if retries > max_retries
        if retries % 20 == 0
            print "app_basic.cf:835", "giving up", msg, "async_call_retries", retries
        return

    if retries > 150
        print "app_basic.cf:839", msg, "async_call_retries", retries

    if retries > 150
        _.delay(func, directive_check_slow_timeout)
    else
        _.delay(func, directive_check_timeout)


running_local = ->
    if not window.g_running_local?
        path_split = document.location.hostname

        if path_split == "127.0.0.1" || path_split == "192.168.14.107"
            print "app_basic.cf:852", "running local"
            window.g_running_local = true
        else
            window.g_running_local = false
    else
        return window.g_running_local


g_http_error = (data) ->
    if not data.indexOf?
        if data.data?
            if data.data.indexOf?
                data = data.data

    if not data.indexOf?
        traceback = data
        window.g_logfile.push(traceback)
        print "app_basic.cf:869", data
    else
        tracebacks = String(data[data.indexOf('<div id="pastebinTraceback" class="pastebin">') ...  _.size(data)])
        tracebacks = String(tracebacks[tracebacks.indexOf('Traceback:') ...  _.size(tracebacks)])
        tracebacks = String(tracebacks[0 ... tracebacks.indexOf('</textarea>')])
        tracebacks = "\n" + tracebacks.trim()
        tracebacks = g_replace_all(tracebacks, "&#39;", " * ")

        if exist(tracebacks)
            warning "app_basic.cf:878", " **  django error  ** ", tracebacks
            window.g_logfile.push(tracebacks)

    return traceback


ismobile = ->
    if navigator.userAgent.match(/Android/i)
        return true

    if navigator.userAgent.match(/webOS/i)
        return true

    if navigator.userAgent.match(/iPhone/i)
        return true

    if navigator.userAgent.match(/iPad/i)
        return true

    if navigator.userAgent.match(/iPod/i)
        return true

    if navigator.userAgent.match(/BlackBerry/i)
        return true

    return navigator.userAgent.match(/Windows Phone/i)

BrowserDetect = 
    init: ->
        @browser = @searchString(@dataBrowser) or "An unknown browser"
        @version = @searchVersion(navigator.userAgent) or @searchVersion(navigator.appVersion) or "an unknown version"
        @OS = @searchString(@dataOS) or "an unknown OS"


#print "browser: " + @browser, "version: " + @version, "os: " + @OS

    searchString: (data) ->
        i = 0

        while i < data.length
            dataString = data[i].string
            dataProp = data[i].prop
            @versionSearchString = data[i].versionSearch or data[i].identity

            if dataString
                return data[i].identity  unless dataString.indexOf(data[i].subString) == -1
            else
                return data[i].identity  if dataProp
            i += 1


    searchVersion: (dataString) ->
        index = dataString.indexOf(@versionSearchString)
        return  if index == -1
        parseFloat dataString.substring(index + @versionSearchString.length + 1)

    dataBrowser: [
        string: navigator.userAgent
        subString: "Chrome"
        identity: "Chrome"
    ,
        string: navigator.userAgent
        subString: "OmniWeb"
        versionSearch: "OmniWeb/"
        identity: "OmniWeb"
    ,
        string: navigator.vendor
        subString: "Apple"
        identity: "Safari"
        versionSearch: "Version"
    ,
        prop: window.opera
        identity: "Opera"
        versionSearch: "Version"
    ,
        string: navigator.vendor
        subString: "iCab"
        identity: "iCab"
    ,
        string: navigator.vendor
        subString: "KDE"
        identity: "Konqueror"
    ,
        string: navigator.userAgent
        subString: "Firefox"
        identity: "Firefox"
    ,
        string: navigator.vendor
        subString: "Camino"
        identity: "Camino"
    ,
        # for newer Netscapes (6 + )
        string: navigator.userAgent
        subString: "Netscape"
        identity: "Netscape"
    ,
        string: navigator.userAgent
        subString: "MSIE"
        identity: "Explorer"
        versionSearch: "MSIE"
    ,
        string: navigator.userAgent
        subString: "Gecko"
        identity: "Mozilla"
        versionSearch: "rv"
    ,
        # for older Netscapes (4-)
        string: navigator.userAgent
        subString: "Mozilla"
        identity: "Netscape"
        versionSearch: "Mozilla"
    ]

    dataOS: [
        string: navigator.platform
        subString: "Win"
        identity: "Windows"
    ,
        string: navigator.platform
        subString: "Mac"
        identity: "Mac"
    ,
        string: navigator.userAgent
        subString: "iPhone"
        identity: "iPhone/iPod"
    ,
        string: navigator.platform
        subString: "Linux"
        identity: "Linux"
    ]


bool_parse = (bs) ->
    if bs == "true"
        return true
    else if bs == "false"
        return false
    else
        return bs


emit_event = (msg, scope, event) ->
    scope.$emit(event)
    scope.$broadcast(event)


init_cryptobox = (cryptobox, utils, serverclock, memory, clientcookies) =>
    print "app_basic.cf:1025", "init cryptobox"
    memory.set("g_first_tree_render", true)
    cryptobox.init()
    utils.uinit()
    serverclock.init()
    clientcookies.get("c_persist_html5mode")


once_cb_init = _.once(init_cryptobox)


angular.module("cryptoboxApp.base", [])


.factory "memory", ["$q", ($q) ->
        window.globals = {}
        _set = (key, value) ->
            if key.indexOf("cvar_") == 0
                key = key.replace("cvar_", "g_cvar_")

            if key.indexOf("c_") == 0
                key = key.replace("c_", "g_c_")

            if key.indexOf("g_") == 0
                window.globals[key] = value
                return
            error = "memory._set you have to supply a key starting with g_, c_, or cvar_, key was: " + key
            warning "app_basic.cf:1052", error

        get_debug_mode: ->
            g_debugmode = @get("g_debugmode")

            if not exist(g_debugmode)
                return false
            return g_debugmode

        debug_mode: ->
            @get_debug_mode()

        debug: ->
            @get_debug_mode()

        set_debug_mode: (b) ->
            @set("g_debugmode", b)

        debug_on: ->
            @set("g_debugmode", true)

        debug_off: ->
            @set("g_debugmode", false)

        set: (key, value) ->
            if not exist(key)
                warning "app_basic.cf:1078", "no key given"

            if key.indexOf("g_ls_") == 0
                if exist(localStorage)
                    if not @has("g_print_once_" + key, true)
                        print "app_basic.cf:1083", "set localstorage", key
                        @set("g_print_once_" + key, true)
                    localStorage[key] = value

            if key.indexOf("g_f_") == 0
                if  _.size(_.filter(_.keys(window.globals), (k) -> strcmp(k, key))) > 0
                    if not string_contains(document.location.pathname, "context.html")
                        warning "app_basic.cf:1090", key, "already exist as functional value"

                    if string_contains(document.location.pathname, "context.html")
                        throw "already exist"

            if not exist(value)
                value = ""

            _set(key, value)
            return value

        set_if_higher: (key, value) ->
            cv = @get(key)
            value = parseFloat(value)

            if isNaN(value)
                throw "not a number"

            if exist(cv)
                if cv < value
                    @set(key, value)
            else
                @set(key, value)

        critical_set: (key, value) ->
            if not exist(key)
                warning "app_basic.cf:1116", "no key given"

            if not exist(value)
                throw new Error("critical set undefined value for key " + key)

            _set(key, value)

        set_no_warning: (key, value) ->
            _set(key, value)

        all_keys_prefix: (key_prefix) ->
            keys = _.keys(window.globals)

            check = (val) ->
                if val.indexOf("g_cvar_") == 0
                    v = val.replace("g_cvar_", "cvar_")

                    if v.indexOf(key_prefix) == 0
                        return v

                if val.indexOf(key_prefix) == 0
                    return val
            result = _.filter(_.map(keys, check), (val) ->
                val?)

            return result

        all_vals_prefix: (key_prefix) ->
            result = []
            for key in @all_keys_prefix(key_prefix)
                result.push(@get(key))

            return result

        prefix: (kp) ->
            @all_keys_prefix(kp)

        del_prefix: (kp) ->
            del_cache = (key) =>
                @del(key)

            _.each(@all_keys_prefix(kp), del_cache)

        exist: (key) ->
            if not exist(key)
                return false

            return exist(@get(key))

        has: (key) ->
            if not exist(key)
                warning "app_basic.cf:1167", "no key given"

            if key.indexOf("cvar_") == 0
                key = key.replace("cvar_", "g_cvar_")

            if key.indexOf("c_") == 0
                key = key.replace("c_", "g_c_")

            return @exist(key)

        get: (key) ->
            val = null
            if not exist(key)
                warning "app_basic.cf:1180", "no key given"

            if key.indexOf("cvar_") == 0
                key = key.replace("cvar_", "g_cvar_")

            if key.indexOf("c_") == 0
                key = key.replace("c_", "g_c_")

            if key.indexOf("g_") == 0
                value = window.globals[key]
                val = bool_parse(value)

            if not exist(val)
                if key.indexOf("g_ls_") == 0
                    if exist(localStorage)
                        print "app_basic.cf:1195", "get localstorage", key
                        if exist(localStorage[key])
                            val = localStorage[key]
                            window.globals[key] = val

            if exist(key)
                return val

            error = "globals g_ ->" + key
            print "app_basic.cf:1204", error
            throw error

        event: (name, done) ->
            if not exist(done)
                done = false
            ek = "g_event_" + name
            lek = "g_last_event_" + name
            ec = "g_event_count_"+name
            if @has(lek)
                last_event =@get(lek)

                if last_event != -1
                    duration = get_local_time() - last_event
                    runtime = @get(ek)
                    runtime += duration
                    @set(ek, runtime)
            else
                @set(ek, 0)

            if @has(ec)
                @increment_counter(ec)
            else
                @counter(ec)
                @increment_counter(ec)

            if done
                @set(lek, -1)
                @decrement_counter(ec)
            else
                @set(lek, get_local_time())

            if @get_debug_mode()
                if @has(ec)
                    cnt = @get(ec)
                else
                    cnt = 0
                print "app_basic.cf:1241", "event", cnt, name

        get_event_duration: (name) ->
            @event(name, true)
            ec = "g_event_count_" + name
            ek = "g_event_"+name
            if @has(ek)
                return @get(ek)
            return 0

        get_event_counter: (name) ->
            ec = "g_event_count_"+name
            if @has(ec)
                return @get(ec)
            return 0

        get_events: ->
            events = []
            add_event = (e) =>
                key = _splitlast(e, "g_event_count_")
                event = {}
                event["name"] = key
                event["count"] = @get("g_event_count_"+key)
                event["duration"] = @get("g_event_"+key)
                events.push(event)

            _.each(@all_keys_prefix("g_event_count_"), add_event)
            return events

        get_int: (key) ->
            val = @get(key)
            return parseInt(val, 10)

        get_float: (key) ->
            val = @get(key)
            return parseFloat(val)

        set_one_read_value: (key) ->
            _set(key, true)
            return true

        get_one_read_value: (key) ->
            val = @get(key)
            @del(key)
            return exist(val)

        get_promise: (key) ->
            p = $q.defer()
            val = @get(key)

            if not val?
                p.reject("memory:get_promise no value for key [" + String(key) + "]")
            else
                p.resolve(val)

            return p.promise

        del: (key) ->
            if key.indexOf("cvar_") == 0
                key = key.replace("cvar_", "g_cvar_")

            if key.indexOf("c_") == 0
                key = key.replace("c_", "g_c_")

            if key.indexOf("g_") == 0
                delete window.globals[key]
                return
            error = "globals should start with g_ (global) - " + key
            print "app_basic.cf:1309", key, "no g_ prefix"
            warning "app_basic.cf:1310", error

        reset: ->
            for key in _.keys window.globals
                keep = false
                if key.indexOf("g_service") == 0
                    print "app_basic.cf:1316", "stopping", key
                    clearInterval(window.globals[key])
                cookie_key = key
                if cookie_key.indexOf("g_c_") == 0
                    cookie_key = cookie_key.replace("g_c_", "c_")

                if cookie_key.indexOf("c_") == 0
                    if cookie_key.indexOf("c_persist_") == 0
                        keep = true

                    if cookie_key.indexOf("c_const_persist_") == 0
                        keep = true

                if key.indexOf("g_persist_") == 0
                    keep = true

                if not keep
                    @del(key)

            return

        bool_test: (key) ->
            val = @get(key)

            if not exist(val)
                @set(key, false)
                val = false

            if String(val) != "true" and String(val) != "false"
                throw new Error("not a boolean")

            return exist_truth(val)

        get_bool: (key) ->
            @bool_test(key)

        counter: (key) ->
            if not exist(@get(key))
                @set(key, 0)

        counter_create: (key, val) ->
            if not exist(@get(key))
                @set(key, 0)

            if exist(val)
                @set(key, val)

        reset_counter: (key) ->
            if not exist(@get(key))
                @set(key, 0)

            @set(key, 0)

        get_counter: (key) ->
            return @get(key)

        counter_get: (key) ->
            return @get(key)

        mod_counter: (key, modulus) ->
            val = @get(key)
            ival = parseInt(val, 10)
            imod = parseInt(modulus, 10)
            return (ival % imod) == 0

        increment_counter: (key) ->
            val = @get(key)

            if not exist(val)
                val = 0

            val = parseInt(val, 10)
            val = val + 1
            @set(key, val)
            return val

        cnt_up: (key) ->
            @increment_counter(key)

        decrement_counter: (key) ->
            val = @get(key)
            val = parseInt(val, 10)
            val = val - 1
            @set(key, val)
            return val

        cnt_down: (key) ->
            @decrement_counter(key)

        dict_set: (key, name, val) ->
            if @has(key)
                dict = @get(key)
                dict[name] = val
                @set(key, dict)
                return _.size(_.keys(dict))
            else
                dict = {}
                dict[name] = val
                @set(key, dict)
                return 1

        dict_get_size: (key) ->
            if @has(key)
                dict = @get(key)
                return _.size(_.keys(dict))
            else
                return 0

        dict_keys: (key) ->
            if @has(key)
                dict = @get(key)
                return _.keys(dict)
            else
                return []

        dict_clear: (key) ->
            dict = {}
            @set(key, dict)
            return 0

        dict_has: (key, name) ->
            if @has(key)
                dict = @get(key)
                return name in _.keys(dict)
            else
                return false

        dict_del: (key, name) ->
            if @dict_has(key, name)
                dict = @get(key)
                delete dict[name]
                @set(key, dict)
                return _.size(_.keys(dict))
            else
                return 0

        dict_get_val: (key, name) ->
            if @dict_has(key, name)
                dict = @get(key)
                return dict[name]
            else
                return null

        set_del: (key, val) ->
            if @has(key)
                list = @get(key)

                exclude_val = (ival) ->
                    return !(ival == val)

                list = _.filter(list, exclude_val)
                @set(key, list)
                return _.size(list)
            else
                @set(key, [val])
                return 1

        set_set: (key, val) ->
            if @has(key)
                list = @get(key)

                if val not in list
                    list.push(val)
                    @set(key, list)

                return _.size(list)
            else
                @set(key, [val])
                return 1

        set_clear: (key) ->
            @set(key, [])
            return 0

        set_has: (key, val) ->
            if @has(key)
                list = @get(key)
                return  val in list
            else
                return false

        set_get_size: (key) ->
            if @has(key)
                return _.size(@get(key))
            else
                return 0

        list_del: (key, val) ->
            if @has(key)
                list = @get(key)

                exclude_val = (ival) ->
                    return !(ival == val)

                list = _.filter(list, exclude_val)
                @set(key, list)
                return _.size(list)
            else
                @set(key, [val])
                return 1

        list_set: (key, val) ->
            if @has(key)
                list = @get(key)
                list.push(val)
                @set(key, list)
                return _.size(list)
            else
                @set(key, [val])
                return 1

        list_get_size: (key) ->
            if @has(key)
                return _.size(@get(key))
            else
                return 0

        list_has: (key, val) ->
            if @has(key)
                list = @get(key)
                return val in list
            else
                return false

        list_clear: (key) ->
            @set(key, [])
            return 0

        keys: ->
            _.keys(window.globals)
    ]


.factory "clientcookies", ["memory", "utils", (memory, utils) ->
        loaded = false
        _set = (key, value) ->
            if key == "c_token"
                warning "app_basic.cf:1553", "c_token not allowed"

            if key == "c_username"
                warning "app_basic.cf:1556", "c_username not allowed"

            if key.indexOf("c_") == 0
                Store.set key, value
                return
            error = "cookies should start with c_"
            print "app_basic.cf:1562", error
            warning "app_basic.cf:1563", error

        set_memory = (cookie) ->
            if cookie.key.indexOf("c_") == 0
                memory.set(cookie.key, cookie.val)

        ensure_memory: ->
            if not loaded
                cookie_data = Store.all()
                _.each(cookie_data, set_memory)
            loaded = true

        reset: ->
            check_delete = (key) =>
                keep = false
                cookie_key = key
                if cookie_key.indexOf("g_c_") == 0
                    cookie_key = cookie_key.replace("g_c_", "c_")

                if cookie_key.indexOf("c_") == 0
                    if cookie_key.indexOf("c_persist_") == 0
                        keep = true

                    else if cookie_key.indexOf("c_const_persist_") == 0
                        keep = true

                if not keep
                    @del(cookie_key)

            _.each(_.keys(window.globals), check_delete)

        del: (key) ->
            memory.del(key)
            Store.del(key)

        set: (key, value) ->
            if key.indexOf("c_const_") == 0
                if utils.exist(memory.get(key))
                    print "app_basic.cf:1601", key + "is const", value, "ignored"
                    return
            memory.set(key, value)
            _set(key, value)

        set_no_warning: (key, value) ->
            memory.set(key, value)
            _set(key, value)

        get: (key) ->
            if key == "c_token"
                warning "app_basic.cf:1612", "c_token not allowed"

            if key == "c_username"
                warning "app_basic.cf:1615", "c_username not allowed"
            if key.indexOf("c_") != 0
                error = "cookies should start with c_"
                warning "app_basic.cf:1618", error
            value = memory.get(key)
            value = bool_parse(value)

            if value?
                return value
            value = Store.get(key)

            if utils.exist(value)
                value = bool_parse(value)
                memory.set(key, value)
                return value
            return null

        has: (key) ->
            v = @get(key)
            return utils.exist(v)
]


.factory "utils", ["memory", "dateFilter", "$templateCache", "$q", "$http", "$timeout", (memory, dateFilter, $templateCache, $q, $http, $timeout) ->
        m_browser = null
        m_os = null
        m_version = null

        init = =>
            BrowserDetect.init()
            m_browser = BrowserDetect.browser
            m_version = BrowserDetect.version
            m_os = BrowserDetect.OS
            browser = {}
            browser["browser"] = m_browser
            browser["version"] = m_version
            browser["os"] = m_os
            memory.set("g_browser", browser)
            memory.set("g_browser_name", browser.browser)
            memory.set("g_browser_version", m_version)
            memory.set("g_location_origin", window.location.origin)

            if m_browser == "Chrome"
                directive_check_timeout = 250

        _rtrim = (str, charlist, cnt) ->
            r = str
            charlist = (if not charlist then " \\s " else (charlist + "").replace(/([\[\]\(\)\.\?\/\*\{\}\+\$\^\:])/g, "\\$1"))
            if not exist(cnt)
                re = new RegExp("[" + charlist + "]+$", "g")
                r = (str + "").replace re, ""
            else
                re = new RegExp("[" + charlist + "]$")

                for n in [0...cnt]
                    r = (r + "").replace re, ""

            return r

        _ltrim = (str, charlist, cnt) ->
            r = str
            charlist = (if not charlist then " \\s " else (charlist + "").replace(/([\[\]\(\)\.\?\/\*\{\}\+\$\^\:])/g, "$1"))
            if not exist(cnt)
                re = new RegExp("^[" + charlist + "]+", "g")
                r = (str + "").replace re, ""
            else
                re = new RegExp("^[" + charlist + "]")

                for n in [0...cnt]
                    r = (r + "").replace re, ""

            return r

        _slugify = (text) ->
            safe_chars = ['_', '-', '.', '~', 'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '-', '__']
            text = text.toLowerCase()
            text = text.replace(/\s/g, "-")

            while text.indexOf("__") > 0
                text = text.replace("__", "_")
            slug = ""
            checksafechar = (c) ->
                if c not in safe_chars
                    c = encode_utf8_b64(c)
                    c = _rtrim(c, "=").toLowerCase()
                slug += c

            _.each(text, checksafechar)
            return slug

        _sha3 = (data...) ->
            hashdata = ""
            append_data = (d) ->
                hashdata += String(d)
                hashdata += "+"

            _.each(data, append_data)
            hashdata = _rtrim(hashdata, "+")
            return  CryptoJS.SHA3(hashdata).toString()

        _count = (string, subString, allowOverlapping) ->
            string += ""
            subString += ""
            return string.length + 1  if subString.length <= 0
            n = 0
            pos = 0
            step = (if (allowOverlapping) then (1) else (subString.length))
            loop
                pos = string.indexOf(subString, pos)

                if pos >= 0
                    n++
                    pos += step
                else
                    break

            return n

        _print_once = (msg, themsg) ->
            if not memory.has("g_print_once_" + themsg)
                memory.set("g_print_once_" + themsg, true)
                print "app_basic.cf:1736", msg, themsg

        _get_cryptobox_slug = ->
            cryptobox_slug = memory.get("g_cryptobox_slug")

            if cryptobox_slug
                return cryptobox_slug
            else
                path_split = document.location.pathname.split("/")
                cryptobox_slug = path_split[1]
                memory.set("g_cryptobox_slug", cryptobox_slug)
                return cryptobox_slug

        _file_extension = (fname) ->
            if not exist(fname)
                return ""
            if fname.indexOf(".") != -1
                cnt_points = _count(fname, ".")

                while cnt_points > 1
                    fname = fname.replace(".", "±")
                    cnt_points -= 1

                split_name = fname.split(".")
                extension = split_name[split_name.length - 1]
                if extension.indexOf(" ") != -1
                    return fname

                if _.size(extension) > 0
                    return String(extension).trim()

            return String(fname).trim()

        get_version: ->
            get_version()

        init_utils: ->
            init()

        path_basename: (path) ->
            b = path
            lastChar = b.charAt(b.length - 1)
            b = b.slice(0, -1)  if lastChar is "/" or lastChar is "\\"
            b = b.replace(/^.*[\/\\]/g, "")
            return b

        path_dirname: (path) ->
            path = _ltrim(path, "/")
            path = _rtrim(path, "/")
            path = "/" + path
            path = path.replace(/\/[^\/]*\/?$/, "")

            if _.size(path) is 0
                path = "/"

            return path

        path_info: (path, options) ->
            OPTS = undefined
            cnt = undefined
            dirName = undefined
            have_basename = undefined
            have_extension = undefined
            have_filename = undefined
            i = undefined
            opt = undefined
            optName = undefined
            optTemp = undefined
            options = undefined
            tmp_arr = undefined
            __getExt = undefined
            options = 0  unless exist(options)
            opt = ""
            optName = ""
            optTemp = 0
            tmp_arr = {}
            cnt = 0
            i = 0
            have_basename = false
            have_extension = false
            have_filename = false
            return false  unless path

            options = "PATHINFO_ALL"  unless options
            OPTS = 
                PATHINFO_DIRNAME: 1
                PATHINFO_BASENAME: 2
                PATHINFO_EXTENSION: 4
                PATHINFO_FILENAME: 8
                PATHINFO_ALL: 0

            for optName of OPTS
                OPTS.PATHINFO_ALL = OPTS.PATHINFO_ALL | OPTS[optName]

            options = [].concat(options)  if typeof options isnt "number"
            i = 0

            while i < options.length
                optTemp = optTemp | OPTS[options[i]]  if OPTS[options[i]]
                i++
            options = optTemp
            __getExt = (path) ->
                dotP = undefined
                str = undefined
                str = path + ""
                dotP = str.lastIndexOf(".") + 1

                unless dotP
                    false
                else
                    if dotP isnt str.length
                        str.substr dotP
                    else
                        ""

            if options & OPTS.PATHINFO_DIRNAME
                dirName = path.replace(/\\/g, "/").replace(/\/[^\/]*\/?$/, "")
                tmp_arr.dirname = (if dirName is path then "." else dirName)

            if options & OPTS.PATHINFO_BASENAME
                have_basename = @path_basename(path)  if false is have_basename
                tmp_arr.basename = have_basename

            if options & OPTS.PATHINFO_EXTENSION
                have_basename = @path_basename(path)  if false is have_basename
                have_extension = __getExt(have_basename)  if false is have_extension
                tmp_arr.extension = have_extension  if false isnt have_extension

            if options & OPTS.PATHINFO_FILENAME
                have_basename = @path_basename(path)  if false is have_basename
                have_extension = __getExt(have_basename)  if false is have_extension
                have_filename = have_basename.slice(0, have_basename.length - (if have_extension then have_extension.length + 1 else (if have_extension is false then 0 else 1)))  if false is have_filename
                tmp_arr.filename = have_filename
            tmp_arr.extension = ""  unless exist(tmp_arr.extension)
            cnt = 0

            for opt of tmp_arr
                cnt++

            return tmp_arr[opt]  if cnt is 1
            return tmp_arr

        string_contains: (astring, val) ->
            return string_contains(astring, val)

        encode_utf8_b64: (str) ->
            return encode_utf8_b64(str)

        decode_utf8_b64: (str) ->
            return decode_utf8_b64(str)

        print_once: (msg, themsg) ->
            _print_once(msg, themsg)

        unique_number: ->
            unique_number()

        minimime_on_extension: (name) ->
            extension = _file_extension(name)

            switch extension
                when "as"
                    return "actionscript"
                when "csv"
                    return "excel"
                when "numbers"
                    return "excel"
                when "xls"
                    return "excel"
                when "docx"
                    return "word"
                when "doc"
                    return "word"
                when "pptx"
                    return "powerpoint"
                when "ppt"
                    return "powerpoint"
                when "css"
                    return "code"
                when "cs"
                    return "cplusplus"
                when "rb"
                    return "ruby"
                when "cryptobox"
                    return "cryptobox"
                when "vsd"
                    return "visio"
                when "vdx"
                    return "visio"
                when "mkv"
                    return "film"
                when "php"
                    return "code"
                when "mp3"
                    return "sound"
                when "pkg"
                    return "compressed"
                when "dat"
                    return "compressed"
                when "md"
                    return "text"
                when "pages"
                    return "word"
                when "dmg"
                    return "compressed"
                when "pdf"
                    return "acrobat"
                when "rtfd"
                    return "text"
                when "rtf"
                    return "text"
                when "c"
                    return "c"
                when "cpp"
                    return "cplusplus"
                when "java"
                    return "code"
                when "js"
                    return "js"
                when "txt"
                    return "text"
                when "html"
                    return "code"
                when "json"
                    return "code"
                when "htm"
                    return "code"
                when "ico"
                    return "image"
                when "eml"
                    return "default"
                when "ttf"
                    return "gear"
                when "epub"
                    return "pages"
                when "mobi"
                    return "pages"
                when "chtml"
                    return "application"
                else
                    print "app_basic.cf:1976", "unknown mimetype", name
                    return "default"

        get_mini_mime: (mime, name) ->
            switch mime
                when "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"
                    return "word"
                when "application/pdf"
                    return "acrobat"
                when "application/postscript"
                    return "vector"
                when "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel", "application/vnd.oasis.opendocument.spreadsheet"
                    return "excel"
                when "application/vnd.openxmlformats-officedocument.presentationml.presentation", "application/vnd.ms-powerpoint"
                    return "powerpoint"
                when "image/png", "image/gif", "image/bmp", "image/jpg", "image/jpeg", "image/vnd.adobe.photoshop", "image/x-ms-bmp", "image/x-photoshop",  "image/x-icon"
                    return "picture"
                when "application/visio", "application/x-visio", "application/vnd.visio", "application/visio.drawing", "application/vsd", "application/x-vsd", "image/x-vsd", "zz-application/zz-winassoc-vsd"
                    return "visio"
                when "audio/mpeg"
                    return "sound"
                when "application/bin", "application/binary", "application/com", "application/dos-exe", "application/exe", "application/macbinary", "application/msdos-windows", "application/octet-stream", "application/x-com", "application/x-exe", "application/x-macbinary", "application/x-msdos-program", "application/x-stuffit", "application/x-tencore", "application/x-winexe", "application/x-zip-compressed", "vms/exe", "application/x-msdownload"
                    return "application"
                when "application/zip", "application/x-tar"
                    return "compressed"
                when "folder"
                    return "folder"
                when "text/x-python"
                    return "code"
                when "application/javascript"
                    return "js"
                when "text/x-java-source", "text/x-java"
                    return "code"
                when "text/x-c", "text/x-csrc", "text/x-c++src"
                    if name.indexOf(".cpp") > 0
                        return "cplusplus"
                    else
                        return "c"
                when "application/rtf"
                    return "word"
                when "text/plain"
                    if name.indexOf(".note") > 0
                        return "note"
                    else
                        return "text"
                else
                    if exist(mime)
                        if mime.indexOf("video/") > -1
                            return "film"

            return @minimime_on_extension(name)

        match_mime_small_icon: (mini_mime) ->
            return "/st/img/icon-" + mini_mime + ".png"

        match_mime_large_icon: (mini_mime) ->
            switch mini_mime
                when "acrobat", "actionscript", "c", "cplusplus", "code", "ruby", "java", "vector", "compressed", "powerpoint", "text", "word", "excel", "picture", "note", "film"
                    return "/st/img/icon-" + mini_mime + "@4x.png"
                else
                    return "/st/img/icon-default@4x.png"

        get_local_time: ->
            get_local_time()

        uinit: ->
            init()

        reg_test: (data, expr) ->
            patt = new RegExp(expr)
            return patt.test(data)

        chrome: ->
            return m_browser == "Chrome"

        replace_all: (str, v1, v2) ->
            g_replace_all(str, v1, v2)

        ie8: ->
            if m_browser == "Explorer"
                if parseInt(m_version, 10) == 8
                    return true
            return false

        html5: ->
            v = memory.get("g_c_persist_html5mode")
            return bool_parse(v)

        split: (str, splitter) ->
            s = String(str)
            sp = s.split(splitter)
            return sp

        splitlast: (str, splitter) ->
            _splitlast(str, splitter)

        bool_parse: (v) ->
            return bool_parse(v)

        text_html: (str) ->
            str = str.trim()
            return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/\n/g, "<br/>").replace(/\ /g, "&nbsp;").replace(/\t/g, "&nbsp;&nbsp;&nbsp;&nbsp;")

        percentage: (current, range) ->
            current = parseFloat(current)
            range = parseFloat(range)
            perc = current / (range / 100)

            if range == 0
                return 0

            if perc > 100
                perc = 100

            if isNaN(perc)
                return 0

            return parseInt(perc, 10)

        full: (arr) ->
            return _.size(arr) > 0

        empty: (arr) ->
            return _.size(arr) == 0

        exclude: (source, excludes, keys) ->
            # loops source and excludes and removes items based on keys
            # [1,2,3], [2,3] = [1]
            # arie = {"naam": "arie", "leeftijd": 20}
            # piet = {"naam": "piet", "leeftijd": 40}
            # jan = {"naam": "jan", "leeftijd": 40}
            # exclude([arie, jan, piet], [piet, arie]) -> [jan]
            # exclude([arie, jan, piet], [piet, arie]) -> [jan]
            # exclude([arie, jan, piet], [piet, arie], ["leeftijd]) -> [jan]

            if not _.isArray(source)
                print "app_basic.cf:2112", source
                throw "exclude source must be an array"

            if not exist(excludes)
                if not excludes?
                    excludes = source

            if not _.isArray(excludes)
                throw "exclude exclude must be an array"
            else
                if _.size(excludes) == 0
                    return source

            check_keys = []
            only_check_on = []
            new_array = []
            list_of_forbidden_keyvalues = {}
            if exist(keys)
                if _.isArray(keys)
                    for citem in keys
                        if _.isObject(citem)
                            for ck in _.keys(citem)
                                check_keys.push({'k':ck, 'v':citem[ck]})
                        else
                            check_keys.push({'k':citem, 'v':null})
                            if not exist(list_of_forbidden_keyvalues[citem])
                                excludes2 = []

                                for item in excludes
                                    if not _.isObject(item)
                                        item2 = {}

                                        for ck in check_keys
                                            item2[ck.k] = item
                                        item = item2

                                    excludes2.push(item)

                                r_retrieve_kvs(excludes2, list_of_forbidden_keyvalues)

            citem = null
            if exist(check_keys)
                list_of_seen_keys = {}
                recurse_objects = (obj, found) ->
                    if not _.isObject(obj)
                        obj2 = {}

                        for ck in check_keys
                            obj2[ck.k] = obj
                        obj = obj2

                    if _.isObject(obj)
                        for k in _.keys(obj)
                            if _.isObject(obj[k])
                                recurse_objects(obj[k], found)
                            else
                                for citem in check_keys
                                    if strcmp(citem.k, k)
                                        if not exist(citem.v)
                                            for seenvalue in list_of_forbidden_keyvalues[k]
                                                if strcmp(obj[k], seenvalue)
                                                    found[0] = true

                                        else
                                            if strcmp(citem.v, obj[k])
                                                found[0] = true

                for obj in source
                    found = [false]
                    recurse_objects(obj, found)

                    if not found[0]
                        new_array.push(obj)

            else
                for item in source
                    item1obj = _.isObject(item)
                    found = false

                    for item2 in excludes
                        item2obj = _.isObject(item2)

                        if item1obj and item2obj
                                for k1 in _.keys(item)
                                    for k2 in _.keys(item2)
                                        found = (strcmp(item[k1], item2[k1]) and strcmp(item[k2], item2[k2]) )

                                        if found
                                            break

                        else if item1obj and not item2obj
                            for k1 in _.keys(item)
                                found = strcmp(item[k1], item2)

                                if found
                                    break

                        else if not item1obj and item2obj
                            for k2 in _.keys(item2)
                                found = strcmp(item, item2[k2])

                                if found
                                    break

                        else if not item1obj and not item2obj
                            found = strcmp(item, item2)

                            if found
                                break

                        if found
                            break

                    if not found
                        new_array.push(item)

            return new_array

        filter_key_value: (source, key, value) ->
            new_array = []
            check = (item) =>
                found = false
                if _.isObject(item)
                    tmp = @filter_key_value(item, key, value)

                    if _.size(tmp) > 0
                        found = true

                if item?
                    if String(item[key]) == String(value)
                        found = true

                if found
                    new_array.push(item)

            _.each(source, check)
            return new_array

        map_to_values: (source, key) ->
            new_array = []
            check = (item) =>
                if _.isObject(item[key])
                    print "app_basic.cf:2254", @map_to_values(item, key)
                else
                    if exist(item[[key]])
                        new_array.push(item[key])

            _.each(source, check)
            return new_array

        unique_object_list: (source, key) ->
            new_array = []
            make_unique = (item) ->
                found = false
                check = (item2) ->
                    if item2[key] == item[key]
                        found = true

                _.each(new_array, check)

                if not found
                    new_array.push(item)

            _.each(source, make_unique)
            return new_array

        list_contains: (alist, val) ->
            list_contains(alist, val)[0]

        list_retrieve: (alist, val) ->
            list_contains(alist, val)[1]

        unique_list: (source) ->
            new_array = []
            make_unique = (item) ->
                found = false
                check = (item2) ->
                    if item2 == item
                        found = true

                _.each(new_array, check)

                if not found
                    new_array.push(item)

            _.each(source, make_unique)
            return new_array

        slugify: (text) ->
            return _slugify(text)

        slugify_path: (path) ->
            pathsplit = path.split("/")
            pathsplit = _.map(pathsplit, _slugify)
            slugpath = ""
            makepath = (item) ->
                slugpath += "/" + item

            _.each(pathsplit, makepath)
            slugpath = _ltrim(slugpath, "/", 1)
            return slugpath

        obj2json: (obj) ->
            JSON.stringify(obj)

        json2obj: (json) ->
            JSON.parse(json)

        obj2b64: (obj) ->
            return @b64_encode_safe(@obj2json(obj))

        b642obj: (b64) ->
            if not String(b64).contains("b64:safe")
                warning "app_basic.cf:2325", "b642obj"
                return b64

            return @json2obj(@b64_decode_safe(b64))

        same_object: (obj1, obj2) ->
            j1 = @obj2json(obj1)
            j2 = @obj2json(obj2)
            return j1 == j2

        strcmp: (s1, s2) ->
            return strcmp(s1, s2)

        b64_encode_safe: (s) ->
            b64_encode_safe(s)

        b64_decode_safe: (s) ->
            b64_decode_safe(s)

        object_b64_safe: (v) ->
            object_b64_safe(v)

        b64_object_safe: (v) ->
            b64_object_safe(v)

        b64_uri: (s) ->
            b64_uri(s)

        asciistring: (s) ->
            asciistring(s)

        asciistring_no_specials: (s) ->
            asciistring_no_specials(s)

        asciistring_lowercase: (s) ->
            asciistring_lowercase(s)

        format_file_size: (mybytes) ->
            g_format_file_size(mybytes)

        browser: ->
            if not @exist(m_browser)
                init()

            return m_browser

        is_phone: ->
            if memory.has("g_device_type")
                if memory.get("g_device_type") == "phone"
                    return true
            return false

        is_tablet: ->
            if memory.has("g_device_type")
                if memory.get("g_device_type") == "tablet"
                    return true
            return false

        is_desktop: ->
            if memory.has("g_device_type")
                if memory.get("g_device_type") == "desktop"
                    return true
            return false

        version: ->
            if not @exist(m_version)
                init()

            return m_version

        os: ->
            if not @exist(m_os)
                init()

            return m_os

        mail_admins: (subject, message) ->
            p = $q.defer()
            data = {}
            data["subject"] = subject
            data["message"] = message
            command = "mailadmins"
            #print "commmand-url", command, "/" + @get_cryptobox_slug() + "/" + command
            url = "/" + @get_cryptobox_slug() + "/" + command + "/" + get_local_time()
            data = object_b64_safe(data)

            $http.post(url, data).then(
                ->
                    p.resolve()

                (e) ->
                    print "app_basic.cf:2416", "error mailing admins"
                    print "app_basic.cf:2417", e
                    p.resolve()
            )
            p.promise

        warning: (msg, others...) ->
            warnings = []
            warnings.push(msg)

            add_error = (i) ->
                warnings.push(String(i))

            _.each(others, add_error)
            warning "app_basic.cf:2430", msg, others
            warning_str = ""
            spaces = ""
            add_errors = (i) ->
                warning_str += spaces + i + "\n"
                spaces += "  "

            _.each(warnings, add_errors)
            @mail_admins(@get_cryptobox_slug() + " - javascript error", warning_str)

        digest: ->
            memory.critical_set("g_digest_requested", true)

        force_digest: (scope) ->
            if not exist(scope)
                warning "app_basic.cf:2445", "force_digest needs a scope parameter"

            digest = ->
                if not scope.$$phase
                    scope.$apply()

            _.defer(digest)

        sanitize_url: (url) ->
            url = "/" + url
            while url.indexOf("//") != -1
                url = url.replace("//", "/")

            return url

        ltrim: (str, charlist, max) ->
            _ltrim(str, charlist, max)

        rtrim: (str, charlist, max) ->
            _rtrim(str, charlist, max)

        trim: (str, tv) ->
            if not exist(tv)
                tv = " "

            str = _ltrim(str, tv)
            str = _rtrim(str, tv)
            return str

        capfirst: (s) ->
            return s.charAt(0).toUpperCase() + s.toLowerCase().substring(1)

        numbers_only_string: (v) ->
            if not exist(v)
                v = ""

            v = v.trim()

            if v == ""
                return v
            s = ""

            for i in v
                if parseInt(i, 10) in [0...10]
                    s += i

            return s

        count: (string, subString, allowOverlapping) ->
            _count(string, subString, allowOverlapping)

        cnt_char: (data, c) ->
            _.size(String(data).split(c)) - 1

        strip_file_extension: (fname) ->
            if fname.indexOf(".") != -1
                cnt_points = _count(fname, ".")

                while cnt_points > 1
                    fname = fname.replace(".", "±")
                    cnt_points -= 1

                split_name = fname.split(".")
                extension = split_name[split_name.length - 1]
                if extension.indexOf(" ") != -1
                    return String(fname).trim()
                split_name = split_name[0...split_name.length - 1]
                new_name = ""
                join_name = (i) ->
                    new_name += i

                _.each(split_name, join_name)
                new_name = new_name.replace(/±/g, ".")
                ret = _rtrim(new_name, ".")

                if ret?
                    return ret
                return ""

            _rtrim(fname, " ")

        file_extension: (fname) ->
            _file_extension(fname)

        is_mobile: ->
            return /Android|webOS|iPhone|iPad|iPod|BlackBerry/i.test navigator.userAgent

        title: (title) ->
            document.title = @get_cryptobox_slug() + " | " + title.toLowerCase()

        exist_string: (value) ->
            return exist_string(value)

        exist: (value) ->
            return exist(value)

        assert: (key, value) ->
            if not @exist(value)
                warning "app_basic.cf:2543", "value named " + key + " does not exist"

        exist_truth: (value) ->
            return exist_truth(value)

        stripTrailingSlash: (str) ->
            while str.substr(-1) == "/"
                str = str.substr(0, str.length - 1)

            return str

        strEndsWith: (str, suffix) ->
            str.indexOf(suffix, str.length - suffix.length) != -1

        get_cryptobox_slug: ->
            return _get_cryptobox_slug()

        format_date: (date) ->
            return dateFilter(date, 'EEEE d MMMM y')

        format_time: (date) ->
            return dateFilter(date, 'H:mm:ss')

        timestamp: ->
            return @format_time(@get_local_time())

        format_datetime_medium: (date) ->
            return dateFilter(date, 'd MMM y H:mm')

        format_datetime_long: (datestr) ->
            str = String(dateFilter(datestr, 'EEEE d MMMM y H:mm:ss'))
            print "app_basic.cf:2574", datestr, str
            if str.contains("undefined")
                return datestr

            if str.contains("1970")
                return datestr

            if str.contains("NaN")
                return datestr
            else
                return str

        remove_cache: ->
            if memory.debug_mode()
                $templateCache.removeAll()

        sha3: (data...) ->
            hashdata = ""
            append_data = (d) ->
                hashdata += String(d)
                hashdata += "+"

            _.each(data, append_data)
            hashdata = @rtrim(hashdata, "+")
            return  CryptoJS.SHA3(hashdata).toString()

        http_post: (postslug, data) ->
            postslug = _ltrim(postslug, "/")
            p = $q.defer()
            data = object_b64_safe(data)
            url = "/" + _get_cryptobox_slug() + "/" + postslug + "/" + get_local_time()

            $http.post(url, data).then(
                (databack) ->
                    databack = b64_object_safe(databack)
                    p.resolve(databack.data)

                (errordata) ->
                    p.reject(g_http_error(errordata.data))
            )
            data = b64_object_safe(data)
            p.promise

        http_get: (url) ->
            p = $q.defer()

            $http.get(url).then(
                (result) ->
                    p.resolve(result.data)

                (e) ->
                    p.reject(g_http_error(e.data))
            )
            p.promise

        http_get_cached: (url, cache) ->
            if not cache?
                cache = true

            url_key = asciistring_lowercase_nospace(url)
            p = $q.defer()
            content = memory.get("g_http_get_cached_" + url_key)

            if exist(content)
                p.resolve(content)
            else
                $http.get(url).then(
                    (result) ->
                        if cache
                            memory.set("g_http_get_cached_" + url_key, result.data)

                        p.resolve(result.data)

                    (e) ->
                        p.reject(g_http_error(e.data))
                )
            p.promise

        set_time_out: (msg, func, delay, notify) ->
            if not exist(notify)
                notify = true

            if notify
                func_sha3 = @sha3(String(func))

                if not memory.has("g_method_set_time_out" + func_sha3)
                    memory.counter_create("g_method_set_time_out" + func_sha3)
                    memory.set("g_time_out_func_" + func_sha3, msg)

                memory.increment_counter("g_method_set_time_out" + func_sha3)

                if memory.mod_counter("g_method_set_time_out" + func_sha3, 100)
                    print "app_basic.cf:2666", memory.get("g_time_out_func_" + func_sha3), "has a set_time_out which is called", memory.get("g_method_set_time_out" + func_sha3), "times"
            _.delay(func, delay)

        call_until_sentinal_hits_repeats: (func, param, delay, sentinels, repeats, terminating_sentinel, max_repeats, success_callback, error_callback) =>
            # a sentinal is a value which the function returns at max a number of repeats (max_repeats)
            # a terminating sentinal is hit only once
            # at max_repeats bail out anyway
            start = get_local_time()

            if memory.get_debug_mode()
                print "app_basic.cf:2676", "-------------------"
                print "app_basic.cf:2677", "call_until_sentinal_hits_repeats"
                print "app_basic.cf:2678", "delay", delay
                print "app_basic.cf:2679", "repeats", repeats
                print "app_basic.cf:2680", "max_repeats", max_repeats
                print "app_basic.cf:2681", "terminating_sentinel", terminating_sentinel
                print "app_basic.cf:2682", "sentinels", sentinels
                print "app_basic.cf:2683", "error_callback", exist(error_callback)
                print "app_basic.cf:2684", "error_callback", exist(error_callback)
                print "app_basic.cf:2685", "-------------------"

            if not exist(max_repeats)
                throw "call_until_sentinal_hits_repeats, max_repeats not set"
            key_counter = "g_call_until_sentinal_hits_repeats" + _sha3(String(func))
            key_counter_total = "g_call_until_sentinal_hits_total_repeats" + _sha3(String(func))
            key_counter_sentinel = "g_call_until_sentinal_hits_sentinel" + _sha3(String(func))
            memory.set(key_counter_sentinel, null)
            memory.counter(key_counter)
            sentinels = _.uniq(sentinels)
            last_sentinel_matched = null
            error_called = false
            call_loop = (param) =>
                check_result = (result, def) ->
                    check_sentinel = (sentinel) ->
                        if result == sentinel
                            memory.set(key_counter_sentinel, result)

                            if not exist(last_sentinel_matched)
                                last_sentinel_matched = sentinel

                            if strcmp(last_sentinel_matched, sentinel)
                                memory.increment_counter(key_counter)
                            else
                                memory.reset_counter(key_counter)
                            last_sentinel_matched = sentinel

                    _.each(sentinels, check_sentinel)
                    memory.increment_counter(key_counter_total)

                    if repeats > memory.get_int(key_counter)
                        if result != terminating_sentinel
                            if max_repeats > memory.get_int(key_counter_total)
                                if not error_called
                                    _.delay(call_loop, delay, param)
                            else
                                if memory.get_debug_mode()
                                    print "app_basic.cf:2722", "error max repeats (" + max_repeats + ") hit for " + result
                                if exist(error_callback)
                                    error_callback("error: max repeats (" + max_repeats + ") hit for " + result)

                        else
                            stop = get_local_time()

                            if memory.get_debug_mode()
                                print "app_basic.cf:2730", "success, terminating sentinal "+terminating_sentinel+" reached in " + (stop - start) + " ms."

                            if exist(success_callback)
                                success_callback("success: terminating sentinal "+terminating_sentinel+" reached in " + (stop - start) + " ms.")

                            return
                    else
                        if memory.get_debug_mode()
                            print "app_basic.cf:2738", "error sentinal "+memory.get(key_counter_sentinel)+" reached "+repeats

                        if exist(success_callback)
                            error_callback("error: sentinal "+memory.get(key_counter_sentinel)+" reached "+repeats)
                        memory.del(key_counter)
                        memory.del(key_counter_total)
                        memory.del(key_counter_sentinel)

                w_error_callback = null
                if exist(error_callback)
                    w_error_callback = (ex) ->
                        error_called = true
                        if memory.get_debug_mode()
                            print "app_basic.cf:2751", "exception encountered " + String(ex)

                        error_callback(ex)

                if exist(param)
                    if exist(w_error_callback)
                        result = func(param, w_error_callback)
                    else
                        result = func(param)
                else
                    if exist(w_error_callback)
                        result = func(w_error_callback)
                    else
                        result = func()

                if result.then?
                    result.then(
                        (deferred_result) ->
                            check_result(deferred_result, true)

                        (deferred_result_err) ->
                            check_result(deferred_result_err)
                    )
                else
                    check_result(result)

            call_loop(param)

        set_interval: (msg, func, delay, descr) ->
            if not exist(descr)
                warning "app_basic.cf:2781", "set_interval needs a descr parameter"
            _print_once msg, "set_interval_" + descr + "_" + delay
            setInterval(func, delay)
]



.factory "urls", ["utils", "memory", "clientcookies", (utils, memory, clientcookies) ->
        _safe = (parameter) ->
            return safe_b64(parameter)

        http_error: (data) ->
            return g_http_error(data)

        make_route: (path) ->
            cryptobox_slug = utils.get_cryptobox_slug()

            if memory.get("g_c_persist_html5mode")
                new_path = "/" + cryptobox_slug + "/" + path
            else
                new_path = "/" + path

            new_path = new_path.replace(new RegExp("//", "g"), "/")
            return new_path

        make_absolute_route: (path) ->
            cryptobox_slug = utils.get_cryptobox_slug()

            if memory.has("g_c_persist_html5mode")
                html5_mode = memory.get("g_c_persist_html5mode")
            else
                html5_mode = clientcookies.get("c_html5mode")

            if html5_mode
                new_path = "/" + cryptobox_slug + "/" + path
            else
                new_path = "/" + cryptobox_slug + "#/" + path

            new_path = new_path.replace(new RegExp("//", "g"), "/")
            return new_path

        make_relative_route: (path) ->
            if clientcookies.get("c_persist_html5mode")
                new_path = "/" + path
            else
                new_path = "#/" + path

            new_path = new_path.replace(new RegExp("//", "g"), "/")
            return new_path

        force_change_route: ($location, path) ->
            path = utils.stripTrailingSlash(path)
            safe_path = @make_route(path)

            if $location.path() == safe_path
                document.location = safe_path

            $location.path(safe_path)

        change_route: ($location, path) ->
            path = utils.stripTrailingSlash(path)
            safe_path = @make_route(path)

            if $location.path() != safe_path
                $location.path(safe_path)

        change_document_location: (path) ->
            path = utils.stripTrailingSlash(path)
            safe_path = @make_route(path)
            cryptobox_slug_path = "/" + utils.get_cryptobox_slug()

            if clientcookies.get("c_html5mode")
                if String(document.location).indexOf(safe_path) < 0
                    document.location = safe_path
            else
                if String(document.location).indexOf(cryptobox_slug_path + "#" + safe_path) < 0
                    document.location = cryptobox_slug_path + "#" + safe_path

        safe: (parameter) ->
            _safe(parameter)

        command: (msg, command) ->
            url = "/" + utils.get_cryptobox_slug() + "/" + command + "/" + get_local_time()
            #print msg, "commmand-url", "/" + utils.get_cryptobox_slug() + "/" + command
            return url

        slugcommand: (slug, command) ->
            url = "/" + slug + "/" + command + "/" + get_local_time()
            return url

        postcommand: (msg, command) ->
            url = "/" + utils.get_cryptobox_slug() + "/" + command + "/" + get_local_time()
            #print msg, "commmand-url", "/" + utils.get_cryptobox_slug() + "/" + command, operation
            return url

        key_value: (command, key, value) ->
            get_local_time();
            cryptobox_slug = utils.get_cryptobox_slug()

            if not cryptobox_slug? or cryptobox_slug == "undefined"
                print "app_basic.cf:2881", "cryptobox slug == undefined"
            url = "/" + cryptobox_slug + "/" + command + "/" + _safe(key) + "/" + _safe(value) + "/" + get_local_time()
            print "app_basic.cf:2883", "urls.key_value", url
            return url
]

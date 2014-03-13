
"use strict"
angular.module("cryptoboxApp.services", ["ngResource", "ng"])

.factory "tree", ["$http", "$q", "memory", "urls", "utils", "$upload", ($http, $q, memory, urls, utils, $upload) ->
        m_loading = false
        m_tree_loaded = false
        m_getting_version = false
        m_tree_nodes = null
        _parse_tree = (tree_nodes) ->
            add_parent = (k) ->
                tree_nodes[k].slugpath = k
                tree_nodes[k].slugpath_parent = utils.path_dirname(k)

                if strcmp(tree_nodes[k].slugpath_parent, "/") and strcmp(tree_nodes[k].slugpath, "/")
                    tree_nodes[k].slugpath_parent = ""
            _.each(_.keys(tree_nodes), add_parent)
            root_nodes = _.filter(tree_nodes, (n) -> strcmp(n.slugpath, "/"))

            if _.size(root_nodes) > 1
                warning "services.cf:21", "multiple rootnodes"

            make_node = (node) ->
                obj = {}
                obj["parent"] = node.slugpath_parent

                if !obj["parent"]?
                    obj["parent"] = ""
                obj["text"] = node.m_name_p64s

                if obj["text"] == "/"
                    obj["text"] = "Home"
                obj["type"] = node.m_nodetype
                obj["slugpath"] = node.m_slugpath_p64s
                obj["content_hash"] = node.content_hash
                if memory.get("g_c_device_pixel_ratio") > 1
                    obj["imageUrl"] = "/st/img/tree-" + node.m_nodetype + "@2x.png"
                else
                    obj["imageUrl"] = "/st/img/tree-" + node.m_nodetype + ".png"

                return obj
            all_knodes = _.map(tree_nodes, make_node)
            root_node = make_node(root_nodes[0])
            items = []
            find_knode = (slugpath, searchnodes) ->
                found_node = null

                for kn in searchnodes
                    if strcmp(kn.slugpath, slugpath)
                        found_node = kn

                if !found_node
                    for kn in searchnodes
                        if kn["items"]?
                            found_node = find_knode(slugpath, kn["items"])

                            if found_node
                                break

                return found_node
            knodes = [root_node]
            path_len_sort = (item) ->
                plen = (1000 * _.size(item.slugpath.split("/"))) + _.size(item.slugpath)
                return plen
            all_knodes = _.sortBy(all_knodes, path_len_sort)

            build_tree = (nodes) ->
                for node in all_knodes
                    if node.type == "folder"
                        parent_knode = find_knode(node.parent, knodes)

                        if parent_knode?
                            if utils.exist(parent_knode["items"])
                                parent_knode["items"].push(node)
                            else
                                parent_knode["items"] = []
                                parent_knode["items"].push(node)
                        else
                            parent_knode = find_knode(node.parent, knodes)

            #    knodes.push(node)
            build_tree(knodes)
            memory.set("g_kendo_tree_folders", knodes)
            return tree_nodes

        _get_node = (node_id_or_slugpath, tree) ->
            if not utils.exist(node_id_or_slugpath)
                node_id_or_slugpath = ""

            find_node = (item) ->
                if item.m_short_id == node_id_or_slugpath
                    return true
                else
                    return strcmp(item.m_slugpath_p64s, node_id_or_slugpath)

            node = _.filter(tree, find_node)

            if utils.exist(node)
                if node[0]
                    return node[0]
            return null

        _get_children_tree = (parent, tree) ->
            if parent == ""
                parent = tree["/"]
            parent = parent.slugpath
            get_children = (item) ->
                strcmp(item.slugpath_parent, parent) and not strcmp(item.slugpath, parent)

            children = _.filter(tree, get_children)

            format_file_size = (item) ->
                item.m_size_human = g_format_file_size(Math.round(parseFloat(item.m_size_p64s)));
                return item
            doclist = _.filter(children, format_file_size)
            return doclist

        _get_icons = (item) ->
            mini_mime = utils.get_mini_mime(item.m_mime, item.m_name_p64s)
            item.mini_mime = mini_mime
            if not utils.exist(item.m_mime)
                item.m_mime = mini_mime
            item.icon = utils.match_mime_small_icon(mini_mime)
            item.icon_2x = item.icon.replace(".png", "@2x.png")
            item.icon_4x = item.icon.replace(".png", "@4x.png")
            item.icon_large = utils.match_mime_large_icon(mini_mime)
            return item

        _get = ->
            tree_promise = $q.defer()
            treenodes = memory.get("g_tree")

            if utils.exist(treenodes)
                tree_promise.resolve(treenodes)
            else
                if not memory.has("g_mimetypes_lut")
                    utils.http_get_cached("/st/data/mimetypes.json").then(
                        (content) ->
                            memory.set("g_mimetypes_lut", content)

                        (e) ->
                            warning "services.cf:142", "could not get the mime types", e
                    )
                url2 = urls.command("services.cf:144", "treedict")
                m_loading = true
                $http.post(url2).then(
                    (databack) ->
                        m_loading = false
                        memory.critical_set("g_tree_seq", databack.data[0])
                        tree_nodes = _parse_tree(databack.data[1])
                        m_tree_loaded = true
                        tree_promise.resolve(tree_nodes)
                        memory.critical_set("g_tree", tree_nodes)

                    (error) ->
                        m_loading = false
                        m_tree_loaded = false
                        tree_promise.reject()
                        urls.http_error(error)
                )

            return tree_promise.promise

        _invalidate = ->
            memory.set("g_first_tree_render", true)
            m_tree_loaded = false
            m_loading = false
            memory.del("g_tree")
            memory.del_prefix("g_doc_list")
            memory.del_prefix("g_filter_tree")
            memory.del_prefix("g_http_get_cached")

        get_children_tree: (parent, tree) ->
            return _get_children_tree(parent, tree)

        get_info_document: (object_id) ->
            p = $q.defer()
            versions = null

            if m_getting_version
                p.resolve([])
            else
                versions = memory.get("g_info_doc_" + object_id)

            if utils.exist(versions)
                p.resolve(versions)
            else
                m_getting_version = true
                data = {}
                data["object_id"] = object_id
                data = object_b64_safe(data)
                url = urls.postcommand("services.cf:192", "docinfo", "get")
                $http.post(url, data).then(
                    (databack) ->
                        databack = b64_object_safe(databack)
                        memory.set("g_info_doc_" + object_id, databack.data[1])
                        p.resolve(databack.data[1])
                        m_getting_version = false

                    (errordata) ->
                        m_getting_version = false
                        p.reject(urls.http_error(errordata.data))
                )
            p.promise

        get_node: (node_id_or_slugpath, tree) ->
            _get_node(node_id_or_slugpath, tree)

        get_node_by_id: (node_id) ->
            g_tree = memory.get("g_tree")
            _get_node(node_id, g_tree)

        get_node_slugpath: (slugpath, tree) ->
            slugpath = utils.slugify(slugpath)

            find_node = (item) ->
                if utils.exist(item.doc)
                    return utils.strcmp(item.doc.m_slugpath_p64s, slugpath)
                return false
            node = _.filter(tree, find_node)

            if utils.exist(node)
                if node[0]
                    if utils.exist(node[0].doc)
                        return node[0].doc

            return null

        calculate_size: (tree_nodes) ->
            add_folder_sizes = (folder) ->
                if folder.m_nodetype == "folder"
                    parent = utils.filter_key_value(tree_nodes, "_id", folder.parent)

                    if _.size(parent) > 0
                        parent = parent[0]

                    if utils.exist(parent)
                        parent.m_size_p64s += folder.m_size_p64s
                        np = utils.filter_key_value(tree_nodes, "_id", parent.parent)

                        if _.size(np) > 0
                            np = np[0]
                        else
                            np = null
                        cnt = 0
                        while utils.exist(np)
                            if utils.exist(np.doc)
                                np.doc.m_size_p64s += folder.doc.m_size_p64s
                                print "services.cf:249", np.doc.m_size_p64s

                            if exitst(np.parent)
                                np = utils.filter_key_value(tree_nodes, "_id", np.parent)

                                if _.size(np) > 0
                                    np = np[0]
                                else
                                    np = null
                            else
                                np = null
                            cnt += 1

                            if cnt > 1000
                                np = null

                    _.each(folder.children, add_folder_sizes)

            add_sizes = (tree_nodes) ->
                folder_size = (node) ->
                    if node.m_nodetype == "folder"
                        total = 0
                        get_size = (node) ->
                            total += node.m_size_p64s

                        _.each(node.children, get_size)
                        node.m_size_p64s = total

                _.each(tree_nodes, folder_size)
                _.each(tree_nodes, add_folder_sizes)
                return tree_nodes

            return add_sizes(tree_nodes)

        get_extension: (mimetype) ->
            mimetypes = memory.get("g_mimetypes_lut")

            if not utils.exist(mimetypes)
                warning "services.cf:287", "get extension mime types not loaded"
                return ""
            exts = mimetypes[mimetype]
            ext = ""
            check_mimetype = (i) ->
                if ext == ""
                    ext = i

            _.each(exts, check_mimetype)
            return ext

        get_icons: (item) ->
            _get_icons(item)

        filter_tree: (parent, tree, sort_string, cvar_sort_folders_top, cvar_hide_file_extensions) ->
            if utils.exist(parent)
                hash_for_call = utils.sha3(parent.m_slugpath_p64s, tree, sort_string, cvar_sort_folders_top, cvar_hide_file_extensions)
                filtered_tree_from_memory = memory.get("g_filter_tree_" + hash_for_call)

            if utils.exist(filtered_tree_from_memory)
                return filtered_tree_from_memory
            else
                if not utils.exist(parent)
                    parent = ""

                if utils.exist(parent)
                    treedocs = _get_children_tree(parent, tree)
                else
                    get_doc = (item) ->
                        item.doc
                    doclist = _.map(tree, get_doc)

                    format_file_size = (item) ->
                        item.m_size_human = g_format_file_size(Math.round(parseFloat(item.m_size_p64s)));
                        return item
                    treedocs = _.filter(doclist, format_file_size)
                doclist = []
                folders_first = (item) ->
                    return item.m_nodetype

                name_sort = (item) ->
                    return item.m_name_p64s.toLowerCase()

                size_sort = (item) ->
                    return item.m_size_p64s

                date_sort = (item) ->
                    return item.m_date

                sortitems = (method, reverse) ->
                    groups = null
                    if utils.exist_truth(cvar_sort_folders_top)
                        groups = _.groupBy(treedocs, folders_first)

                    if utils.exist(groups)
                        if utils.exist(method)
                            folders = _.sortBy(groups.folder, method)
                            file = _.sortBy(groups.file, method)
                        else
                            folders = groups.folder
                            file = groups.file

                        if reverse
                            folders = folders.reverse()

                        if reverse
                            file = file.reverse()

                        if utils.exist(folders)
                            if utils.exist(file)
                                doclist = folders.concat(file)
                            else
                                doclist = folders
                        else
                            doclist = file
                    else
                        if utils.exist(method)
                            doclist = _.sortBy(treedocs, method)
                        else
                            doclist = treedocs

                        if reverse
                            doclist = doclist.reverse()

                    return doclist

                if utils.exist(parent)
                    switch sort_string
                        when "down_name"
                            doclist = sortitems(name_sort, false)
                        when "up_name"
                            doclist = sortitems(name_sort, true)
                        when "down_size"
                            doclist = sortitems(size_sort, false)
                        when "up_size"
                            doclist = sortitems(size_sort, true)
                        when "down_date"
                            doclist = sortitems(date_sort, false)
                        when "up_date"
                            doclist = sortitems(date_sort, true)
                        else
                            warning "services.cf:388", "sortstring unknown - " + sortstring

                else
                    doclist = sortitems(null, false)

                backupname_get_icons = (item) ->
                    if utils.exist_truth(cvar_hide_file_extensions)
                        if utils.exist(item.backupname)
                            item.m_name_p64s = item.backupname
                        else
                            item.backupname = item.m_name_p64s

                    _get_icons(item)

                doclist = _.map(doclist, backupname_get_icons)
                root_short_id = null
                find_root = (node) ->
                    not utils.exist(node.slugpath_parent)

                if _.size(tree) > 0
                    root_short_id = _.find(tree, find_root)

                    if utils.exist(root_short_id)
                        root_short_id = root_short_id.m_short_id

                get_types = (item) ->
                    if utils.strcmp(item.slugpath_parent, root_short_id)
                        if memory.has("g_read_rights")
                            find_read_right_node = (rr) ->
                                return rr.m_node_short_id == item.m_short_id
                            read_right = _.filter(memory.get("g_read_rights"), find_read_right_node)

                            if _.size(read_right) > 0
                                item.icon = item.icon.replace("icon-folder", "icon-folder-root")
                                item.icon_2x = item.icon_2x.replace("icon-folder", "icon-folder-root")
                                item.icon_4x = item.icon_4x.replace("icon-folder", "icon-folder-root")
                                item.icon_large = item.icon_large.replace("icon-folder", "icon-folder-root")

                    item.m_human_type = "folder"

                    if item.m_nodetype != "folder"
                        item.m_human_type = utils.get_mini_mime(item.m_mime, item.m_name_p64s)

                    if item.m_name_p64s.length > 30
                        #max_without_spaces = item.m_name_p64s[0...30]
                        new_name = ""
                        charcnt = 0
                        break_point = 80
                        if memory.get("g_device_type") == "phone"
                            break_point = 30

                        for i in item.m_name_p64s
                            new_name += i
                            charcnt += 1

                            if charcnt > break_point
                                charcnt = 0
                                new_name += " "

                        item.m_name_p64s = new_name

                    if not utils.exist(item.m_mime)
                        item.m_mime = item.mini_mime

                    if not utils.exist(item.m_mime)
                        item.m_mime = utils.file_extension(item.m_name_p64s)

                    if utils.exist_truth(cvar_hide_file_extensions)
                        item.m_name_p64s = utils.strip_file_extension(item.m_name_p64s)

                    return item
                doclist = _.map(doclist, get_types)
                memory.set("g_filter_tree_" + hash_for_call, doclist)

            return doclist

        is_folder: (node) ->
            if utils.exist(node)
                return node.m_nodetype == "folder"
            else
                return false

        make_routing: (node, tree) ->
            nodes = []
            make_r_node = (sourcenode) ->
                r_node =
                    route: urls.make_route("/docs/" + sourcenode.m_short_id)
                    m_name_p64s: sourcenode.m_name_p64s
                    m_slug_p64s: sourcenode.m_slug_p64s
                    m_name_p64s_escaped: utils.asciistring_lowercase(sourcenode.m_name_p64s)
                    m_nodetype: sourcenode.m_nodetype
                    m_short_id: sourcenode.m_short_id
                    m_node_type: sourcenode.m_node_type
                    is_folder: sourcenode.m_nodetype == "folder"
                r_node.m_name_p64s_escaped = utils.asciistring_lowercase(sourcenode.m_name_p64s)
                return r_node

            if node
                nodes.push(make_r_node(node))

                while not strcmp(node.slugpath, "/")
                    node = _get_node(node.slugpath_parent, tree)
                    nodes.push(make_r_node(node))

            addlast = (node) ->
                node.last = false
                node.secondlast = false
                node.thirdlast = false
                node.fourthlast = false
                node.fifthlast = false
                node.sixthlast = false
                node.seventhlast = false
                return node
            nodes = _.map(nodes, addlast)
            nodes = nodes.reverse()
            node_size = _.size(nodes)

            if node_size > 0
                nodes[node_size - 1].last = true

            if node_size > 1
                nodes[node_size - 2].secondlast = true

            if node_size > 2
                nodes[node_size - 3].thirdlast = true

            if node_size > 3
                nodes[node_size - 4].fourthlast = true

            if node_size > 4
                nodes[node_size - 5].fifthlast = true

            if node_size > 5
                nodes[node_size - 6].sixthlast = true

            if node_size > 6
                nodes[node_size - 7].seventhlast = true

            if utils.is_phone() || utils.is_tablet()
                truncate_title = (item) ->
                    if _.size(item.m_name_p64s) > 20
                        item.m_name_p64s = item.m_name_p64s[0...20] + "..."
                        item.m_name_p64s_escaped = item.m_name_p64s_escaped[0...20] + "..."

                _.each(nodes, truncate_title)

            if node_size > 0
                if strcmp(nodes[0].m_name_p64s_escaped, "/")
                    nodes[0].m_name_p64s_escaped = "home"

            return nodes

        inmem: ->
            tree = memory.get("g_tree")
            return utils.exist(tree)

        add_folder: (parent, folder_name) ->
            p = $q.defer()
            data = {}
            data["parent"] = parent
            data["foldername"] = folder_name
            data = object_b64_safe(data)
            url = urls.command("services.cf:550", "docs/makefolder")
            $http.post(url, data).then(
                (success) ->
                    p.resolve(success)

                (e) ->
                    g_http_error(e.data)
                    p.reject("server error")
            )
            return p.promise

        read_right: (node_short_id, user_id, operation) ->
            p = $q.defer()
            data = {}
            data["node_short_id"] = node_short_id
            data["user_object_id"] = user_id
            data["operation"] = operation
            data = object_b64_safe(data)
            url = urls.command("services.cf:568", "assignreadright")
            $http.post(url, data).then(
                (success) ->
                    p.resolve(success)
                    _invalidate()
                    _get()

                (e) ->
                    p.reject(urls.http_error(e.data))
            )
            #data = b64_object_safe(data)
            return p.promise

        delete_tree_items: (item_list) ->
            p = $q.defer()
            url = urls.command("services.cf:583", "docs/delete")
            data = {}
            data["json_data"] = true
            data["tree_item_list"] = item_list
            $http.post(url, data).then(
                () ->
                    memory.del("g_tree")
                    p.resolve()

                (e) ->
                    p.reject(urls.http_error(e.data))
            )
            p.promise

        get_tree_loaded: ->
            m_tree_loaded

        mem_get: ->
            return memory.get("g_tree")

        invalidate: ->
            _invalidate()

        get: ->
            _get()

        get_parent: ->
            tree_promise = $q.defer()
            url = urls.command("services.cf:611", "tree")
            $http.post(url).then(
                (databack) ->
                    tree_nodes = databack.data[1]
                    memory.critical_set("g_tree_seq", databack.data[0])
                    memory.critical_set("g_tree", tree_nodes)
                    m_tree_loaded = true
                    tree_promise.resolve(tree_nodes)

                (data) ->
                    tree_promise.reject()
                    urls.http_error(data)
            )
            return tree_promise.promise

        dosearch: (terms) ->
            nodes = memory.get("g_tree")

            if not utils.exist(nodes)
                warning "services.cf:630", "cannot search not tree loaded"
                return []
            results = []
            check_name = (node) ->
                selected = true
                check_nodes = (term) ->
                    if node.doc.m_name_p64s.toLowerCase().indexOf(term.toLowerCase()) < 0
                        selected = false

                _.each(terms.split(" "), check_nodes)

                if selected
                    if node.doc.m_nodetype == 'file'
                        results.push(node)

            _.each(nodes, check_name)
            return results

        all_nodes_recursive: (tree_nodes, short_id_parent) ->
            get_all_children_recursive = (allnodes, parent) ->
                children = []
                parents = []
                get_all_children = (item) ->
                    if item.parent == parent
                        children.push(item)

                        if item.doc.m_nodetype == 'folder'
                            parents.push(item.doc.m_short_id)

                _.each(allnodes, get_all_children)

                while _.size(parents) > 0
                    parent = parents.pop()
                    _.each(allnodes, get_all_children)
                children
            nodes = get_all_children_recursive(tree_nodes, short_id_parent)
            return nodes

        change_name: (node_short_id, nodename) ->
            p = $q.defer()
            data = {}
            data["node_short_id"] = node_short_id
            data["nodename"] = nodename.trim()
            data = object_b64_safe(data)
            url = urls.command("services.cf:674", "docs/changename")
            $http.post(url, data).then(
                (success) ->
                    p.resolve(success)

                (e) ->
                    p.reject(urls.http_error(e.data))
            )
            #data = b64_object_safe(data)
            p.promise

        move: (nodes, parent) ->
            p = $q.defer()
            data = {}
            data["nodes"] = nodes
            data["parent"] = parent
            data = object_b64_safe(data)
            url = urls.command("services.cf:691", "docs/move")
            $http.post(url, data).then(vhRXiUm9KY2g39rjoz
                (success) ->
                    _invalidate()

                    _get().then(
                        () ->
                            p.resolve(success)

                        (err) ->
                            p.reject(err)
                    )

                (e) ->
                    p.reject(urls.http_error(e.data))
            )
            #data = b64_object_safe(data)
            p.promise

        load_tree: (m_tree_nodes_tmp) ->
            for path in _.keys(m_tree_nodes_tmp)
                if utils.slugify_path(m_tree_nodes_tmp[path].m_path_p64s) != path
                    throw "parse json: difference in slug algorithm"
                m_tree_nodes[path] = m_tree_nodes_tmp[path]
            m_tree_nodes

        get_root: ->
            if utils.exist(m_tree_nodes)
                return m_tree_nodes["/"]

        parse_json: (jsondata) ->
            m_tree_nodes = {}
            m_tree_nodes_tmp = utils.json2obj(jsondata)
            @load_tree(m_tree_nodes_tmp)

        ls: (path, recursive, include_parent) ->
            if not utils.exist(m_tree_nodes)
                print "services.cf:728", "m_tree_nodes not loaded (tree.parse_json)"
                return []

            if not utils.exist(recursive)
                recursive = false
            result = []
            path = utils.slugify_path(path)
            for npath in _.keys(m_tree_nodes)
                if strcmp(npath, path)
                    if strcmp(m_tree_nodes[npath].m_nodetype, "file")
                        return [m_tree_nodes[npath]]
                    else
                        if utils.exist(include_parent)
                            if include_parent
                                result.push(m_tree_nodes[npath])

                if recursive
                    if string_contains(utils.path_dirname(npath), path)
                        if strcmp(npath, path)
                            if include_parent
                                result.push(m_tree_nodes[npath])
                        else
                            result.push(m_tree_nodes[npath])

                else
                    if strcmp(utils.path_dirname(npath), path)
                        if strcmp(npath, "/")
                            if include_parent
                                result.push(m_tree_nodes[npath])
                        else
                            result.push(m_tree_nodes[npath])

            result = _.uniq(result)

            order_sort = (item) ->
                return item.m_order
            result = _.sortBy(result, order_sort)

            path_len_sort = (item) ->
                plen = (1000 * _.size(item.m_slugpath_p64s.split("/"))) + _.size(item.m_slugpath_p64s)
                return plen
            result = _.sortBy(result, path_len_sort)
            return result

        parse_tree: (nodes) ->
            _parse_tree(nodes)
]


.factory "serverclock", ["$http", "$q", "urls", "memory", "utils", "$rootScope", "tree", "authorization", ($http, $q, urls, memory, utils, $rootScope, tree, authorization) ->
        last_check = new Date().getTime()

        _get_time = ->
            local_time = new Date().getTime()
            t = memory.get("g_corrected_servertime")

            if not utils.exist(t)
                if not memory.has("g_last_received_servertime")
                    memory.set("g_last_received_servertime", local_time)
                    last_check = new Date().getTime()

                if not memory.has("g_corrected_servertime")
                    memory.set("g_corrected_servertime", local_time)
                    last_check = new Date().getTime()

            return t

        _get_time_interval = ->
            local_time = new Date().getTime()

            if not memory.has("g_last_received_servertime")
                memory.set("g_last_received_servertime", local_time)
                last_check = new Date().getTime()

            if not memory.has("g_corrected_servertime")
                memory.set("g_corrected_servertime", local_time)
                last_check = new Date().getTime()

            mfloat = (s) ->
                return parseFloat(s)

            time_since_check = mfloat((mfloat(local_time) - mfloat(last_check)))

            if memory.has("g_last_received_servertime")
                new_corrected_servertime = mfloat(memory.get("g_last_received_servertime")) + time_since_check
                memory.set("g_corrected_servertime", new_corrected_servertime)
            #print "services.cf:786", time_since_check, local_time, memory.get("g_corrected_servertime"), local_time-memory.get("g_corrected_servertime")
            if time_since_check > 30000
                url = urls.command("services.cf:816", "clock")
                $http.post(url).then(
                    (databack) ->
                        last_check = new Date().getTime()
                        servertime = parseFloat(databack.data[0])
                        #print "services.cf:794", "difference server with local", last_check-servertime
                        memory.set("g_last_received_servertime", servertime)
                        memory.set("g_corrected_servertime", parseFloat(databack.data[0]))
                        #if memory.exist("g_tree_seq")
                        #    if not utils.exist_truth(memory.get("g_upload_started"))
                        #        if memory.get("g_tree_seq") != databack.data[1]
                        #            tree.invalidate()

                        #            tree.get().then(
                        #                () ->
                        #                    emit_event("services.cf:831", $rootScope, "tree_out_of_sync")

                        #                (err) ->
                        #                    print "services.cf:834", "error getting tree", err
                        #            )

                    (errordata) ->
                        print "services.cf:838", "get_time_interval", errordata
                        if errordata.status == 403
                            authorization.logout()
                )

        init: ->
            print "services.cf:844", "init serverclock"
            service_get_time_interval = utils.set_interval("services.cf:845", _get_time_interval, 1000, "_get_time_interval")
            memory.set("g_service_get_time_interval", service_get_time_interval)

        get_time: ->
            return _get_time()
]



.factory "cryptobox", ["$http", "$q", "$location", "memory", "clientcookies", "utils", "urls", "cvar", ($http, $q, $location, memory, clientcookies, utils, urls, cvar) ->
        loading = false
        lastfetch = null
        last_result = null


        f_fetch = ->
            cryptobox_promise = $q.defer();
            url = urls.command("services.cf:862", "config")
            loading = true
            $http.post(url).then(
                (result) ->
                    if result.data[0]
                        last_result = result.data[1]
                        cryptobox_promise.resolve(result.data[1])
                        lastfetch = get_local_time()
                    else
                        cryptobox_promise.reject()
                    loading = false

                (data) ->
                    urls.http_error(data)
                    cryptobox_promise.reject()
                    loading = false
            )
            return cryptobox_promise.promise

        init: ->
            p = $q.defer()
            memory.critical_set("g_persist_browser", BrowserDetect.browser)
            memory.critical_set("g_persist_browser_version", BrowserDetect.version)

            init_cvar = (key, value) ->
                cvar.get(key).then(
                    (resolve_result) ->
                        if not utils.exist(resolve_result)
                            print "services.cf:890", "init-cvar", key
                            if utils.exist(value)
                                cvar.set(key, value)

                    (reject_result) ->
                        warning "services.cf:895", "init cvar rejected", reject_result
                )

            init_cvar("cvar_docs_sort_string", "")
            init_cvar("cvar_show_drop_area", true)
            init_cvar("cvar_docs_sort_string", "down_name")
            init_cvar("cvar_sort_folders_top", true)
            init_cvar("cvar_hide_file_extensions", false)
            init_cvar("cvar_disable_caching", false)
            init_cvar("cvar_use_menu_routing", false)
            init_cvar("cvar_show_debug_info", false)
            init_cvar("cvar_user_should_change_password", false)

            cvar.commit_retrieve_all().then(
                (cvars) ->
                    print "services.cf:910", _.size(cvars) + " cvars"
                    p.resolve()

                (error) ->
                    print "services.cf:914", "error", "init cryptobox", error
                    p.reject()
            )
            return p.promise

        get_app_var: (g_var) ->
            p = $q.defer()

            get_var = ->
                app_var = memory.get(g_var)

                if utils.exist(app_var)
                    p.resolve(app_var)
                else
                    if g_var != "g_doc_count" and g_var != "g_diskspace"
                        p.reject("unknown appvar " + g_var)

                    f_fetch().then(
                        (cryptobox) ->
                            if utils.exist(cryptobox.m_info.doc_count)
                                memory.critical_set("g_doc_count", cryptobox.m_info.doc_count)
                                memory.critical_set("g_diskspace", cryptobox.diskspace)
                                app_var = memory.get(g_var)
                                p.resolve(app_var)

                        (err) ->
                            pp.reject("could not fetch cryptobox appvar " + g_var + "(" + err + ")")
                    )

            get_var()
            return p.promise

        get: ->
            f_fetch()

        slug: ->
            utils.get_cryptobox_slug()
]



.factory "authorization", ["$http", "$q", "$location", "memory", "utils", "clientcookies", "urls", ($http, $q, $location, memory, utils, clientcookies, urls) ->
        _logincheck = (username, password, trust_computer, private_key) ->
            login_promise = $q.defer();

            if not utils.exist(username)
                warning "services.cf:960", "username doesn not exist"

            if not utils.exist(password)
                warning "services.cf:963", "password does not exist"
            url = urls.command("services.cf:964", "authorize")
            data = {}
            data.username = username
            data.password = password
            data.trust_computer = trust_computer
            data.private_key = private_key
            base64_data = object_b64_safe(data)

            $http.post(url, base64_data).then(
                (success_result) ->
                    if utils.exist_truth(success_result.data[0])
                        login_promise.resolve(success_result.data[1])
                    else
                        login_promise.reject("we konden u niet inloggen")

                (error_data) ->
                    urls.http_error(error_data)
                    login_promise.reject()
            )
            return login_promise.promise


        f_server_logout = ->
            p = $q.defer()
            url = urls.command("services.cf:988", "logoutserver")
            $http.post(url).then(
                (success_result) ->
                    print "services.cf:991", "server", "loggedout"
                    memory.reset()
                    urls.change_route($location, "/logout")
                    p.resolve(success_result)

                (error) ->
                    print "services.cf:997", "could not logout"
                    memory.reset()
                    urls.change_route($location, "/logout")
                    urls.http_error(error.data)
                    p.reject(error)
            )
            p.promise

        get_current_user: ->
            login_promise = $q.defer();
            url = urls.command("services.cf:1007", "currentuser")
            $http.post(url).then(
                (success_result) ->
                    if utils.exist_truth(success_result.data[0])
                        login_promise.resolve(b64_object_safe(success_result.data[1]))
                    else
                        login_promise.reject("currentuser not found")

                (error_data) ->
                    urls.http_error(error_data)
                    login_promise.reject()
            )
            return login_promise.promise

        logincheck: (username, password, trust_computer, private_key) ->
            _logincheck(username, password, trust_computer, private_key)

        login: (username, password, trust_computer, private_key) ->
            p = $q.defer()

            if not utils.exist(username)
                warning "services.cf:1028", "username does not exist"

            if not utils.exist(password)
                warning "services.cf:1031", "password does not exist"

            if running_local()
                clientcookies.set("c_persist_password_debug", password)

            clientcookies.set("c_persist_username_" + utils.get_cryptobox_slug(), utils.b64_encode_safe(username))

            _logincheck(username, password, trust_computer, private_key).then(
                (success) ->
                    p.resolve(success)

                (error) ->
                    print "services.cf:1043", "logincheck failed", error
                    p.reject(error)
            )
            return p.promise

        change_password: (username, old_password, new_password) ->
            p = $q.defer()
            utils.assert("username", username)
            utils.assert("old_password", old_password)
            utils.assert("new_password", new_password)
            url = urls.command("services.cf:1053", "changepassword")
            data = {}
            data.json_data = true
            data.username = username
            data.old_password = old_password
            data.new_password = new_password
            data = object_b64_safe(data)

            $http.post(url, data).then(
                (success_result) ->
                    if utils.exist_truth(success_result.data[0])
                        print "services.cf:1064", "password changed"
                        p.resolve()
                    else
                        if success_result.data[1] == "password_mismatch"
                            p.reject("het oude wachtwoord is niet correct")
                        else
                            p.reject(success_result.data[1])

                (error) ->
                    p.reject(urls.http_error(error.data))
            )
            #data = b64_object_safe(data)
            return p.promise

        reset_password: (object_id, new_password) ->
            p = $q.defer()
            utils.assert("object_id", object_id)
            utils.assert("new_password", new_password)
            url = urls.command("services.cf:1082", "resetpassword")
            data = {}
            data.object_id = object_id
            data.new_password = new_password
            data = object_b64_safe(data)

            $http.post(url, data).then(
                (success_result) ->
                    if utils.exist_truth(success_result.data[0])
                        p.resolve(success_result.data[1])
                    else
                        p.reject(success_result.data[1])

                (error) ->
                    p.reject(urls.http_error(error.data))
            )
            #data = b64_object_safe(data)
            return p.promise

        check_otp: (otp, trust_computer, trused_location_name) ->
            p = $q.defer()
            url = urls.command("services.cf:1103", "checkotp")
            data = {}
            data.otp = otp
            data.trust_computer = trust_computer
            data.trused_location_name = trused_location_name
            data = object_b64_safe(data)

            $http.post(url, data).then(
                (success_result) ->
                    p.resolve(success_result.data)

                (error) ->
                    p.reject(urls.http_error(error.data))
            )
            #data = b64_object_safe(data)
            return p.promise

        logout: ->
            clientcookies.set("c_persist_user_logged_in_status", false)
            f_server_logout()
            memory.reset()
            clientcookies.reset()
            urls.change_route($location, "logout")

        to_login: ->
            clientcookies.set("c_persist_user_logged_in_status", false)
            f_server_logout()
            memory.reset()
            clientcookies.reset()
            urls.change_route($location, "login")
]



.factory "saveobject", ["$http", "$q", "memory", "urls", "serverclock", "utils", "$rootScope", "authorization", "cvar", ($http, $q, memory, urls, serverclock, utils, $rootScope, authorization, cvar) ->
        loading = false
        loaded = false
        window.saveobject_cache = {}
        http_operation = (operation, saveobject_type, object_id, member, value) ->
            p = $q.defer()

            do_operation = ->
                if operation == "dirty_get"
                    operation = "get"
                data = {}
                data["operation"] = operation
                data["saveobject_type"] = saveobject_type
                data["object_id"] = object_id
                data["member"] = member
                data["value"] = value
                data = object_b64_safe(data)
                loading = true

                if operation == "set"
                    window.saveobject_cache = 
                    {}

                if operation == "get" or operation == "get_members"
                    if utils.exist(window.saveobject_cache[object_id])
                        p.resolve(window.saveobject_cache[object_id])
                        loading = false
                        utils.digest()

                if operation == "collection"
                    if utils.exist(window.saveobject_cache[saveobject_type + "_collection"])
                        p.resolve(window.saveobject_cache[saveobject_type + "_collection"])
                        loading = false
                        utils.digest()

                if operation == "collection_maxed"
                    if utils.exist(window.saveobject_cache[saveobject_type + "_collection_maxed"])
                        p.resolve(window.saveobject_cache[saveobject_type + "_collection_maxed"])
                        loading = false
                        utils.digest()

                if operation == "fields"
                    if utils.exist(window.saveobject_cache[saveobject_type + "_fields"])
                        p.resolve(window.saveobject_cache[saveobject_type + "_fields"])
                        loading = false
                        utils.digest()

                if operation == "get_object_id"
                    if utils.exist(window.saveobject_cache[saveobject_type + member + value])
                        p.resolve(window.saveobject_cache[saveobject_type + member + value])
                        loading = false
                        utils.digest()

                if loading
                    url = urls.postcommand("services.cf:1191", "saveobject", operation)
                    $http.post(url, data).then(
                        (databack) ->
                            databack = b64_object_safe(databack)

                            if utils.exist_truth(databack.data[0])
                                if operation == "set"
                                    window.saveobject_cache = {}

                                if operation == "delete"
                                    window.saveobject_cache = {}

                                if operation == "get"
                                    window.saveobject_cache[object_id] = databack.data[1].returnval

                                if operation == "collection"
                                    window.saveobject_cache[saveobject_type + "_collection"] = databack.data[1].returnval

                                if operation == "collection_maxed"
                                    window.saveobject_cache[saveobject_type + "_collection_maxed"] = databack.data[1].returnval

                                if operation == "fields"
                                    window.saveobject_cache[saveobject_type + "_fields"] = databack.data[1].returnval

                                if operation == "get_object_id"
                                    window.saveobject_cache[saveobject_type + member + value] = databack.data[1].returnval

                                p.resolve(databack.data[1].returnval)
                                loading = false
                                loaded = true
                            else
                                p.reject(databack.data[1].returnval)
                                loading = false
                                loaded = true
                                window.saveobject_cache = {}
                        ->
                            loaded = false
                            loading = false
                    )
            #data = b64_object_safe(data)

            if not loading or operation == "dirty_get"
                do_operation()
            else
                check_loaded = ->
                    if utils.exist_truth(loading)
                        async_call(check_loaded)
                    else
                        do_operation()

                check_loaded()

            return p.promise

        _invalidate = ->
            window.saveobject_cache = {}

        get_loaded: ->
            loaded

        invalidate: ->
            _invalidate()

        load_cache: (saveobject_type) ->
            http_operation("collection", saveobject_type, "", "", "").then(
                (collection) ->
                    window.saveobject_cache[saveobject_type + "_collection"] = collection
                    cache_item = (item) ->
                        window.saveobject_cache[item.object_id] = item
                        cache_fields = (f) ->
                            if utils.strcmp(f, "fields")
                                cache_form_fields = (kf) ->
                                    param_unused(kf)
                                    window.saveobject_cache[saveobject_type + "_fields"] = item[f]

                                _.each(_.keys(item[f]), cache_form_fields)
                            window.saveobject_cache[saveobject_type + f + item[f]] = item.object_id

                        _.each(_.keys(item), cache_fields)

                    _.each(collection, cache_item)

                (err) ->
                    warning "services.cf:1274", err
            )

        set: (saveobject_type, object_id, member, value) ->
            _invalidate()
            p = $q.defer()
            memory.del("g_save_object_" + object_id)

            http_operation("set", saveobject_type, object_id, member, value).then(
                (v) ->
                    p.resolve(v)

                (e) ->
                    warning "services.cf:1287"
                    p.reject(e)
            )
            p.promise

        set_cvar: (object_id, member, value) ->
            _invalidate()
            p = $q.defer()

            http_operation("set_cvar", "CryptoUser", object_id, member, value).then(
                (v) ->
                    memory.del(member)
                    cvar.set(member, value)
                    p.resolve(v)

                (e) ->
                    warning "services.cf:1303"
                    p.reject(e)
            )
            p.promise

        get: (saveobject_type, object_id) ->
            p = $q.defer()

            http_operation("get", saveobject_type, object_id, "", "").then(
                (v) ->
                    p.resolve(v)

                (e) ->
                    warning "services.cf:1316"
                    p.reject(e)
            )
            p.promise

        dirty_get: (saveobject_type, object_id) ->
            p = $q.defer()

            http_operation("dirty_get", saveobject_type, object_id, "", "").then(
                (v) ->
                    p.resolve(v)

                (e) ->
                    warning "services.cf:1329"
                    p.reject(e)
            )
            p.promise

        get_members: (saveobject_type, object_id, members) ->
            p = $q.defer()

            http_operation("get_members", saveobject_type, object_id, members, "").then(
                (v) ->
                    p.resolve(v)

                (e) ->
                    warning "services.cf:1342"
                    p.reject(e)
            )
            p.promise

        delete: (saveobject_type, object_id) ->
            _invalidate()
            p = $q.defer()

            http_operation("delete", saveobject_type, object_id, "", "").then(
                (v) ->
                    p.resolve(v)

                (e) ->
                    warning "services.cf:1356"
                    p.reject(e)
            )
            p.promise

        get_fields: (saveobject_type) ->
            p = $q.defer()

            http_operation("fields", saveobject_type, "", "", "").then(
                (v) ->
                    p.resolve(v)

                (e) ->
                    warning "services.cf:1369"
                    p.reject(e)
            )
            p.promise

        field_unique: (saveobject_type, member, value) ->
            p = $q.defer()

            http_operation("field_unique", saveobject_type, "", member, value).then(
                (v) ->
                    p.resolve(v)

                (e) ->
                    warning "services.cf:1382"
                    p.reject(e)
            )
            p.promise

        new_object: (saveobject_type, value) ->
            _invalidate()
            p = $q.defer()
            keys = _.keys(value)

            http_operation("new_object", saveobject_type, "", keys, value).then(
                (v) ->
                    print "services.cf:1394", "new object", saveobject_type, "stored"
                    p.resolve(v)

                (e) ->
                    warning "services.cf:1398"
                    p.reject(e)
            )
            p.promise

        collection: (save_object_type) ->
            p = $q.defer()

            http_operation("collection", save_object_type, "", "", "").then(
                (v) ->
                    p.resolve(v)

                (e) ->
                    warning "services.cf:1411"
                    p.reject(e)
            )
            p.promise

        collection_maxed: (save_object_type, max_items) ->
            p = $q.defer()

            http_operation("collection_maxed", save_object_type, "", "", max_items).then(
                (v) ->
                    p.resolve(v)

                (e) ->
                    warning "services.cf:1424"
                    p.reject(e)
            )
            p.promise

        collection_ids: (save_object_type) ->
            p = $q.defer()

            http_operation("collection_ids", save_object_type, "", "", "").then(
                (v) ->
                    print "services.cf:1434", v
                    p.resolve(v)

                (e) ->
                    warning "services.cf:1438"
                    p.reject(e)
            )
            p.promise

        collection_on_member_value: (save_object_type, member, value) ->
            p = $q.defer()

            http_operation("collection_on_member_value", save_object_type, "", member, value).then(
                (v) ->
                    p.resolve(v)

                (e) ->
                    warning "services.cf:1451"
                    p.reject(e)
            )
            p.promise

        collection_on_members_value: (save_object_type, member, value) ->
            p = $q.defer()

            http_operation("collection_on_members_value", save_object_type, "", member, value).then(
                (v) ->
                    p.resolve(v)

                (e) ->
                    warning "services.cf:1464"
                    p.reject(e)
            )
            p.promise

        get_object_id: (save_object_type, member, value) ->
            p = $q.defer()

            http_operation("get_object_id", save_object_type, "", member, value).then(
                (v) ->
                    p.resolve(v)

                (e) ->
                    warning "services.cf:1477", e
                    p.reject(e)
            )
            p.promise

        get_loggedin_user: ->
            p = $q.defer()

            http_operation("get_loggedin_user", "", "", "", "").then(
                (v) ->
                    p.resolve(v)

                (e) ->
                    warning "services.cf:1490"
                    p.reject(e)
            )
            p.promise

        get_tree_password: ->
            p = $q.defer()

            http_operation("get_tree_password", "", "", "", "").then(
                (v) ->
                    p.resolve(v)

                (e) ->
                    warning "services.cf:1503"
                    p.reject(e)
            )
            p.promise
]



.factory "cvar", ["$http", "$q", "memory", "urls", "utils", "$rootScope", "serverclock", ($http, $q, memory, urls, utils, $rootScope, serverclock) ->
        loaded = false
        loading = false
        previous_cvars = null
        m_add_commit_items = {}
        m_del_commit_items = {}
        first = true
        operation_in_progress = false
        current_operation = ""

        _get_cvar_loaded = ->
            return !loading

        do_cvar_operation = (operation, key, value) ->
            operation_in_progress = true
            current_operation = operation
            cvar_opp_promise = $q.defer()
            data = {}
            data["operation"] = operation
            data["key"] = key
            data["value"] = value
            url = urls.command("services.cf:1532", "cvar")

            if first and operation != "get_encrypt"
                loading = true
                first = false

            data = object_b64_safe(data)

            $http.post(url, data).then(
                (databack) ->
                    if utils.exist_truth(databack.data[0])
                        if utils.exist(databack.data[1].cvar_value)
                            data = databack.data[1] = b64_object_safe(databack.data[1])
                            cvar_opp_promise.resolve(data.cvar_value)
                            operation_in_progress = false
                        else
                            cvar_opp_promise.resolve()
                            operation_in_progress = false
                    else
                        cvar_opp_promise.reject()
                    loading = false

                    if operation != "get_encrypt"
                        loaded = true

                (data) ->
                    loading = false
                    operation_in_progress = false
                    cvar_opp_promise.reject(data)
            )
            return cvar_opp_promise.promise
        counter = 0
        f_cvar_operation = (operation, key, value) ->
            p = $q.defer()

            check_operation_in_progress = ->
                if operation_in_progress
                    counter += 1
                    async_call_retries("services.cf:1570", check_operation_in_progress, counter)
                    return
                else
                    do_cvar_operation(operation, key, value).then(
                        (res) ->
                            p.resolve(res)

                        (rej) ->
                            p.reject(rej)
                    )

            check_operation_in_progress()
            return p.promise

        _all = ->
            cvar_promise = $q.defer()

            if loaded
                cvar_promise.resolve()
            else
                if loading


                    f_cvar_loaded = ->
                        if _get_cvar_loaded()
                            print "services.cf:1595", "cvars", "loaded"
                            cvar_promise.resolve()

                    $rootScope.$watch(_get_cvar_loaded, f_cvar_loaded)
                else
                    f_cvar_operation("all", "", "").then(
                        (resolve_result) ->
                            resolve_result = b64_object_safe(resolve_result)

                            if utils.exist(resolve_result)
                                for key in _.keys resolve_result
                                    memory.critical_set(key, resolve_result[key])

                            cvar_promise.resolve()
                            loading = false

                        (reject_result) ->
                            cvar_promise.reject(reject_result)

                            if reject_result.status != 403
                                print "services.cf:1615", "cvar-all rejected", reject_result
                    )

            return cvar_promise.promise

        _get = (key) ->
            p = $q.defer()
            val = memory.get(key)

            if utils.exist(val)
                val = b64_object_safe(val)
                p.resolve(val)
            else
                if not loading
                    _all()


                f_cvar_loaded = ->
                    if _get_cvar_loaded()
                        val = memory.get(key)
                        val = b64_object_safe(val)

                        if utils.exist(val)
                            p.resolve(val)
                        else
                            print "services.cf:1640", "no cvar", key
                            p.resolve(null)

                $rootScope.$watch(_get_cvar_loaded, f_cvar_loaded)

            return p.promise

        _del = (key) ->
            m_del_commit_items[key] = "not-relevant"
            memory.del(key)

        _commit_retrieve_all = ->
            cvar_promise = $q.defer()

            for k in memory.all_keys_prefix("cvar_add_")
                key = String(k).replace("cvar_add_", "cvar_")
                m_add_commit_items[key] = b64_object_safe(memory.get(k))
                memory.del(k)

            for k in memory.all_keys_prefix("cvar_del_")
                key = String(k).replace("cvar_del_", "cvar_")
                m_del_commit_items[key] = memory.get(k)
                memory.del(k)
            dirty_add_keys = _.keys m_add_commit_items
            dirty_del_keys = _.keys m_del_commit_items
            commit_data = {}
            commit_data["add"] = m_add_commit_items
            commit_data["del"] = m_del_commit_items
            commit_data["ignore"] = []
            f_cvar_operation("commit", "data", commit_data).then(
                (resolve_result) ->
                    for key in dirty_add_keys
                        delete m_add_commit_items[key]

                    for key in dirty_del_keys
                        delete m_del_commit_items[key]

                    if resolve_result
                        for key in _.keys resolve_result
                            resolve_result[key] = b64_object_safe(resolve_result[key])

                            if not String(key).startsWith("cvar_")
                                print "services.cf:1682", "invalid cvar received", key, "deleting it"
                                _del(key)

                            memory.critical_set(key, resolve_result[key])
                        previous_cvars = resolve_result

                    resolve_result = b64_object_safe(resolve_result)
                    cvar_promise.resolve(resolve_result)

                (reject_result) ->
                    if reject_result.status != 403
                        print "services.cf:1693", reject_result

                    cvar_promise.reject(reject_result.data)
            )
            return cvar_promise.promise

        reset: ->
            loaded = false
            loading = false
            first = true

        logontime: ->
            p = $q.defer()

            _get("cvar_logon_time").then(
                (lt) ->
                    now = serverclock.get_time()
                    tm = now - lt
                    if not utils.exist(tm)
                        tm = 0

                    p.resolve(tm)

                (reject) ->
                    print "services.cf:1717", "could not get cvar_logon_time", reject
                    p.reject("logontime error")
            )
            return p.promise

        get_cvar_loaded: ->
            return !loading

        invalidate_reload: ->
            cvar_promise = $q.defer()

            f_cvar_operation("all", "", "").then(
                (resolve_result) ->
                    resolve_result = b64_object_safe(resolve_result)

                    if utils.exist(resolve_result)
                        for key in _.keys resolve_result
                            memory.critical_set(key, resolve_result[key])

                    cvar_promise.resolve()
                    loading = false

                (reject_result) ->
                    cvar_promise.reject()
                    print "services.cf:1741", "cvar-all rejected", reject_result
            )
            return cvar_promise.promise

        all: ->
            _all()

        all_if_loaded: ->
            p = $q.defer()

            if not loading
                _all()


            f_cvar_loaded = ->
                if _get_cvar_loaded()
                    p.resolve()

            $rootScope.$watch(_get_cvar_loaded, f_cvar_loaded)
            return p.promise

        set: (key, value) ->
            if not startswith(key, "cvar_")
                warning "services.cf:1764", "cvar", key, "does not start with cvar_"
            m_add_commit_items[key] = value
            memory.critical_set(key, b64_object_safe(value))
            memory.set("g_cvar_dirty", true)

        commit_set: (key, value) ->
            if not startswith(key, "cvar_")
                warning "services.cf:1771", "cvar", key, "does not start with cvar_"

            memory.critical_set(key, b64_object_safe(value))
            f_cvar_operation("set", key, value)
            _commit_retrieve_all()

        commit_retrieve_all: ->
            _commit_retrieve_all()

        del: (key) ->
            _del(key)

        __commit_del: (key) ->
            memory.del(key)
            return f_cvar_operation("del", key, "")

        memget: (key) ->
            memory.get(key)

        memhas: (key) ->
            memory.has(key)

        get: (key) ->
            _get(key)

        get_encrypt: (key) ->
            p = $q.defer()
            val = memory.get(key)

            if utils.exist(val)
                val = b64_object_safe(val)
                return val
            else
                _all().then(
                    () ->
                        do_cvar_operation("get_encrypt", key, "").then(
                            (res) ->
                                if utils.exist(res)
                                    memory.critical_set(key, b64_object_safe(res))

                                p.resolve(res)

                            (rej) ->
                                p.reject(rej)
                        )

                    (err) ->
                        warning "services.cf:1818", err
                )

            return p.promise
]



.factory "uploader", ["$http", "$q", "urls", "memory", "utils", "$rootScope", "tree", "authorization", "$upload", ($http, $q, urls, memory, utils, $rootScope, tree, authorization, $upload) ->
        m_original_files = []
        m_upload_files_selected = []
        m_upload_progress = {}
        m_upload_encryption_progress = {}
        m_file_not_good_for_upload = []
        m_upload_in_progress_now = 0
        m_upload_posters = []
        m_upload_server_responses = []
        m_uploads_started = []
        m_uploads_done = []
        m_uploads_error = []
        m_uploads_max_active = 1
        m_flush_requested = false
        m_retries_fhash = {}
        m_restarted_uploads = []
        m_good_items_for_display = []
        m_error_items_for_display = []
        m_loop_speed = 2000
        m_upload_succes = null
        m_upload_failed = null
        m_initial_uploads_to_start = 0
        _file_hash = (af) ->
            hashvalue = ""
            if utils.exist(af.name)
                hashvalue += af.name

            if utils.exist(af.relPath)
                hashvalue += af.relPath

            if utils.exist(af.webkitRelativePath)
                hashvalue += af.webkitRelativePath

            if utils.exist(af.size)
                hashvalue += af.size

            if utils.exist(af.type)
                hashvalue += af.type

            if utils.exist(af.lastModifiedDate)
                hashvalue += af.lastModifiedDate
            return utils.sha3(hashvalue)

        _add_to_upload_queue =  (f, uuid) ->
            fhash = _file_hash(f)

            if utils.list_contains(m_original_files, fhash)
                return
            filedata = {}
            if not utils.exist(uuid)
                filedata.uuid = _get_guid()
            else
                filedata.uuid = uuid
            filedata.fhash = fhash
            addfile = !utils.reg_test(f.name, /(^\.)/) and !utils.reg_test(f.webkitRelativePath, /(^\.)/)
            filedata.human_size = utils.format_file_size(f.size)
            filedata.size = f.size
            if not exist(f.test_size)
                f.test_size = f.size
            filedata.error = ""

            if f.test_size >= 1048576000
                addfile = false
                filedata.error = "file_too_large_for_upload"
                m_file_not_good_for_upload.push({"file": f, "filedata": filedata})
            addfile = 
            if addfile
                if not utils.list_contains(m_upload_files_selected, fhash)
                    m_upload_files_selected.push({"file": f, "filedata": filedata})

            size_sort = (item) ->
                return item.filedata.test_size
            m_upload_files_selected = _.sortBy(m_upload_files_selected, size_sort)
            m_file_not_good_for_upload = _.sortBy(m_file_not_good_for_upload, size_sort)

            if not utils.exist(uuid)
                if addfile
                    m_original_files.push({"uuid": filedata.uuid, "thefile": f})

        _update_items_for_display_core = ->
            _get_items_for_display = (displayfiles) ->
                displayitems = []
                make_report_item = (displayfile) ->
                    report_item = {}
                    report_item["uuid"] = displayfile.filedata.uuid
                    report_item["size"] = displayfile.filedata.size
                    report_item["human_size"] = displayfile.filedata.human_size
                    report_item["name"] = displayfile.file.name
                    report_item["path"] = displayfile.file.webkitRelativePath
                    if exist(displayfile.file.name)
                        mini_mime = utils.get_mini_mime(displayfile.file.type, displayfile.file.name)

                    report_item["icon"] = utils.match_mime_small_icon(mini_mime)
                    report_item["icon_2x"] = report_item["icon"].replace(".png", "@2x.png")

                    if exist(report_item["path"])
                        report_item["name"] = ""
                    report_item["progress"] = m_upload_progress[displayfile.filedata.uuid]
                    if not exist(report_item["progress"])
                        report_item["progress"] = 0
                    report_item["encryption"] = m_upload_encryption_progress[displayfile.filedata.uuid]
                    if not exist(report_item["encryption"])
                        report_item["encryption"] = 0
                    report_item["progress_half_bar"] = report_item["progress"] / 2
                    report_item["encryption_half_bar"] = report_item["encryption"] / 2
                    report_item["error"] = displayfile.filedata.error
                    displayitems.push(report_item)

                _.each(displayfiles, make_report_item)

                size_sort = (item) ->
                    return item.size
                displayitems = _.sortBy(displayitems, size_sort)
                cnt = 0
                add_cnt = (item) ->
                    cnt += 1
                    item["cnt"] = cnt

                _.each(displayitems, add_cnt)
                return displayitems
            m_error_items_for_display = _get_items_for_display(m_file_not_good_for_upload)
            m_good_items_for_display = _get_items_for_display(m_upload_files_selected)

        _update_items_for_display = _.throttle(_update_items_for_display_core, 100)

        _start_upload = (currentfile, file_data, exception_handler) ->
            if m_upload_in_progress_now >= m_uploads_max_active
                return null
            m_upload_in_progress_now += 1
            m_upload_progress[file_data.uuid] = 0
            m_upload_encryption_progress[file_data.uuid] = 0
            purl = "/" + utils.get_cryptobox_slug() + "/docs/upload"
            relpath = currentfile.webkitRelativePath
            if utils.exist(relpath)
                relpath = utils.replace_all(relpath, currentfile.name, "")

            if not utils.exist(file_data.relPath)
                file_data.relPath = relpath

            if _.size(relpath) == 0
                if utils.exist(file_data.relPath)
                    relpath = file_data.relPath

            relpath = utils.rtrim(relpath, '/')

            if not utils.exist(relpath)
                relpath = ""
            fheaders = 
                'Content-Type': file_data.type
            fdata =
                'basepath': safe_b64(parent.m_path_p64s)
                'relpath': safe_b64(relpath)
                'size': currentfile.size.toString()
                'uuid': file_data.uuid
                'name': safe_b64(currentfile.name)
            m_upload_encryption_progress[file_data.uuid] = 0
            m_upload_posters[file_data.uuid] = $upload.upload(
                url: purl
                headers: fheaders
                data: fdata
                file: currentfile

            ).then(
                (response) =>
                    try
                        response.data = b64_object_safe(response.data)

                        switch response.status
                            when 200
                                if utils.exist(response.data)
                                    if not utils.exist(response.data) or _.isObject(response.data)
                                        throw "uploader._start_upload: response.data unreadable"
                                    m_upload_in_progress_now -= 1
                                    m_upload_server_responses.push(response.data)
                                    m_upload_server_responses = _.uniq(m_upload_server_responses)
                                    m_upload_encryption_progress[response.data] = 100
                                    m_upload_progress[response.data] = 100
                                    m_uploads_done.push(response.data)
                            else
                                pass "ignored for testing"
                                m_upload_progress[response.data] = 100

                        _update_items_for_display()
                    catch error
                        exception_handler([error.fileName, error.lineNumber, error.columnNumber, String(error)])

                (err) =>
                    try
                        if exist(file_data)
                            m_upload_in_progress_now -= 1
                            m_upload_encryption_progress[err.data] = 0
                            m_upload_progress[err.data] = 0
                            org_file = utils.list_retrieve(m_original_files, file_data.uuid)

                            if not utils.list_contains(m_restarted_uploads, file_data.uuid)
                                if utils.exist(org_file)
                                    a1 = _.size(m_upload_files_selected)
                                    m_upload_files_selected= utils.exclude(m_upload_files_selected, [file_data.uuid], ["uuid"])
                                    _add_to_upload_queue(org_file.thefile, file_data.uuid)

                                m_uploads_started = utils.exclude(m_uploads_started, [file_data.uuid], ["uuid"])
                                m_restarted_uploads.push(file_data.uuid)
                            else
                                m_upload_progress[err.data] = 100
                                m_upload_encryption_progress[err.data] = 100
                                m_uploads_done.push(err.data)
                                m_uploads_error.push(err.data)

                    catch error
                        exception_handler([error.fileName, error.lineNumber, error.columnNumber, String(error)])

            , (evt) ->
                m_upload_progress[file_data.uuid] = parseInt(100.0 * evt.loaded / evt.total)
                _update_items_for_display()
            )
            m_flush_requested = true
            return file_data.uuid

        _get_guid = ->
            get_guid()

        _get_upload_progress = ->
            if _.size(m_upload_files_selected) == 0
                return 0
            total_enc_progress = 0
            total_upload_proc = 0
            if utils.exist(m_upload_encryption_progress)
                sum_enc_progress = (uuid) ->
                    total_enc_progress += m_upload_encryption_progress[uuid]

                _.each(_.keys(m_upload_encryption_progress), sum_enc_progress)

            if utils.exist(m_upload_progress)
                sum_upload_progress = (uuid) ->
                    total_upload_proc += m_upload_progress[uuid]

                _.each(_.keys(m_upload_progress), sum_upload_progress)
            total_upload_proc = total_upload_proc / m_initial_uploads_to_start
            total_enc_progress = total_enc_progress / m_initial_uploads_to_start
            proc = total_enc_progress + total_upload_proc
            proc = proc / 2
            if not exist(proc)
                return 0
            return proc

        reset: ->
            m_original_files = []
            m_upload_files_selected = []
            m_upload_progress = {}
            m_upload_encryption_progress = {}
            m_upload_in_progress_now = 0
            m_upload_posters = []
            m_upload_server_responses = []
            m_uploads_started = []
            m_uploads_done = []
            m_uploads_error = []
            m_uploads_max_active = 2
            m_flush_requested = false
            m_retries_fhash = {}
            m_restarted_uploads = []
            m_good_items_for_display = []
            m_error_items_for_display = []

        get_upload_progress: ->
            _get_upload_progress()

        add_to_upload_queue: (f) ->
           _add_to_upload_queue(f, null)

        force_update_items_for_display: ->
            _update_items_for_display_core()

        update_items_for_display: ->
            _update_items_for_display()

        get_upload_files_selected: ->
            return m_upload_files_selected

        get_file_not_good_for_upload: ->
            return m_file_not_good_for_upload

        get_upload_server_responses: ->
            return m_upload_server_responses

        reset_upload_queue: ->
            m_upload_files_selected = []
            utils.digest()

        files_selected_for_upload: ->
            _.size(m_upload_files_selected)

        done_uploading: ->
            # test number of succesfull encryptions here
            if _.size(m_upload_server_responses) == _.size(m_upload_files_selected)
                m_upload_server_responses = []
                m_upload_files_selected = []
                m_upload_encryption_progress = []
                m_upload_progress = []
                m_upload_in_progress_now = 0
                _invalidate()
                emit_event("services.cf:2126", $rootScope, "tree_out_of_sync")

        get_flush_requested: ->
            return m_flush_requested

        set_flush_requested: (b) ->
            m_flush_requested = b

        upload_start: (upload_succes, upload_failed) ->
            dummy = ->
                pass

            if exist(upload_succes)
                m_upload_succes = _.once(upload_succes)
            else
                m_upload_succes = _.once(dummy)

            if exist(upload_failed)
                m_upload_failed = _.once(upload_failed)
            else
                m_upload_failed = _.once(dummy)

            m_initial_uploads_to_start = _.size(m_upload_files_selected)
            ucnt = 0
            upload_starter_thread = (p, error_callback) ->
                ucnt += 1
                uploads_to_start = utils.exclude(m_upload_files_selected, m_uploads_started, ["uuid"])

                size_sort = (item) ->
                    return item.file.size
                uploads_to_start = _.sortBy(uploads_to_start, size_sort)

                exception_handler_uploader = (ex) ->
                    error_callback(ex)

                start_upload = (ufile) ->
                    uuid_started = _start_upload(ufile.file, ufile.filedata, exception_handler_uploader)

                    if utils.exist(uuid_started)
                        m_uploads_started.push({uuid: uuid_started})
                _.each(uploads_to_start, start_upload)

                check_progress = (uuid) ->
                    do_check_progress = utils.list_contains(m_uploads_done, uuid.uuid)

                    if utils.list_contains(m_uploads_done, uuid)
                        m_upload_encryption_progress[uuid] = 100

                    if not do_check_progress
                        utils.http_post("/docs/uploadencprogress", uuid).then(
                            (progress) ->
                                if not utils.exist(m_upload_encryption_progress[progress.uuid])
                                    m_upload_encryption_progress[progress.uuid] = 0

                                if progress.proc > m_upload_encryption_progress[progress.uuid]
                                    m_upload_encryption_progress[progress.uuid] = parseInt(progress.proc, 10)

                                if m_upload_encryption_progress[progress.uuid] >= 100
                                    m_upload_encryption_progress[progress.uuid] = 100
                                    if not utils.list_contains(m_uploads_done, progress.uuid)
                                        m_uploads_done.push(progress.uuid)
                                        m_upload_in_progress_now -= 1

                                        if m_upload_in_progress_now <= 0
                                            m_upload_in_progress_now = 0

                            (e) ->
                                print "services.cf:2193", e
                        )
                        m_flush_requested = true

                _.each(m_uploads_started, check_progress)
                m_uploads_done = _.uniq(m_uploads_done)
                m_uploads_error = _.uniq(m_uploads_error)
                progress = _get_upload_progress()
                _update_items_for_display()
                return progress

            success_cb = (r) ->
                if memory.debug_mode()
                     print "services.cf:2206", "upload_start, success_cb " + r

                m_upload_succes(r)

            error_cb = (r) ->
                if memory.debug_mode()
                    print "services.cf:2212", "upload_start, error_cb " + r

                m_upload_failed(r)

            utils.call_until_sentinal_hits_repeats(upload_starter_thread, 2000, m_loop_speed, [0..100], m_initial_uploads_to_start + 10, 100, 200, success_cb, error_cb)
            return true

        get_uploads_done: ->
            m_uploads_done

        get_uploads_error: ->
            m_uploads_error

        get_num_uploads_done: ->
            num_uploads_done = _.size(m_uploads_done)
            #if num_uploads_done == m_initial_uploads_to_start
            #    m_upload_succes("uploads done")
            return num_uploads_done

        get_num_uploads_error: ->
            num_uploads_error = _.size(m_uploads_error)
            num_uploads_done = _.size(m_uploads_done)
            #if num_uploads_done == m_initial_uploads_to_start
            #    m_upload_error("uploads done with errors")
            return num_uploads_error

        get_upload_encryption_progress: ->
            m_upload_encryption_progress

        load_file: (file) ->
            reader = new FileReader()

            _handleOnLoadEnd = ->
                pass

            reader.onloadend = _handleOnLoadEnd
            reader.readAsArrayBuffer(file)
            return true

        get_good_items_for_display: ->
            m_good_items_for_display

        get_error_items_for_display: ->
            m_error_items_for_display

        is_busy: ->
            m_upload_in_progress_now > 0
]


default_settings = (scope) ->
    scope.docs = false
    scope.settings = false
    scope.disclaimer = false
    return scope


handle_ex = (method_name, exc, mail = true) ->
    ret = "------- error -------\n"
    ret += "method:"+method_name
    ret += "type:"+exc.type
    ret += "stack:"+exc.stack
    ret += "message:"+exc.message
    ret += "------- end error -------\n\n"

    if mail
        warning "controller_base.cf:18", "mailing exception not implemented"
    warning "controller_base.cf:19", ret
    return ret


class SecuredController
    m_updating_cvars = false
    m_width = -1
    m_height = -1

    init: ->
        return


    base_init: ($rootScope, $scope, cvar, authorization, $location, cryptobox, tree, $routeParams, memory, clientcookies, utils, urls, $q, serverclock) ->

        init = ->
            once_cb_init(cryptobox, utils, serverclock, memory, clientcookies)

        _.defer(init)
        $rootScope.html5 = clientcookies.get("c_html5mode")
        $rootScope.html4 = !$rootScope.html5
        if not running_local()
            clientcookies.del("c_persist_password_debug")


    set_logged_minutes: ($scope, cvar, $q) ->
        p = $q.defer()

        cvar.logontime().then(
            (seconds) ->
                if seconds == 0
                    p.resolve("zojuist ingelogd")

                if seconds > 60 * 60
                    minutes = Math.floor(seconds / 60)
                    hour = Math.floor(minutes / 60)
                    mins = minutes - (hour * 60)

                    if mins == 1
                        seconds_string = "minuut"
                    else
                        seconds_string = "minuten"

                    $scope.long_time_login = true
                    p.resolve(hour + " uur en " + mins + " " + seconds_string)
                else
                    minutes = Math.floor(seconds / 60)
                    seconds = Math.round(seconds - (minutes * 60))
                    minstring = "minuut"

                    if minutes != 1
                        minstring = "minuten"

                    p.resolve(minutes + " " + minstring + ", " + seconds + " seconden")

            (error) ->
                print "controller_base.cf:75", error
                p.reject(error)
        )
        return p.promise


    render_auth: ->
        return


    prerender: ->
        return


    interval_minute: ->
        return


    interval_second: ->
        return


    interval_fast: ->
        return


    base_interval_second: ($rootScope, $scope, cvar, authorization, $location, cryptobox, tree, $routeParams, memory, clientcookies, utils, urls, $q) ->
        @set_logged_minutes($scope, cvar, $q).then(
            (result) ->
                $scope.logged_minutes = result
            ->
                print "controller_base.cf:106"
        )


    base_interval_minute: ->
        return


    baseprerender: ($rootScope, $scope, cvar, authorization, $location, cryptobox, tree, $routeParams, memory, clientcookies, utils, urls, $q, serverclock) ->

        $scope.loading_indicator = ->
            return memory.bool_test("g_loading")

        $scope.ctrl_change_route = (url) ->
            print "controller_base.cf:120", "scope change route", url
            urls.change_route($location, url)

        cvar.get("cvar_username").then(
            (cvar_username) ->
                $scope.username = cvar_username

                if cvar_username == "rabshakeh"
                    $scope.is_rabshakeh = true
                else
                    $scope.is_rabshakeh = false
            ->
                warning "controller_base.cf:132", "could not fetch cvar_username"
        )
        cryptobox_name = clientcookies.get("c_persist_cryptobox_name_" + utils.get_cryptobox_slug())
        utils.print_once "controller_base.cf:135", cryptobox_name
        cryptobox_slug = utils.get_cryptobox_slug()

        if exist(cryptobox_name) and exist(cryptobox_slug)
            $scope.cryptobox_name = cryptobox_name
            $scope.cryptobox_slug = cryptobox_slug

        $scope.get_cryptobox_slug = ->
            return utils.get_cryptobox_slug()

        $scope.get_cryptobox_slug_config = ->
            return "cryptobox_" + utils.get_cryptobox_slug()
        #$scope.
        $scope.docs_add = "/docs/add"
        $scope.docs_home = "/docs"
        $scope.settings_home = "/settings/security"
        $scope.settings_security = "/settings/security"
        $scope.settings_password = "/settings/personal"
        $scope.settings_users = "/settings/users"
        $scope.settings_disk = "/settings/disk"
        $scope.logout_url = "/logout"
        $scope.disclaimer_url = "/disclaimer"
        $scope.privacy_url = "/privacy"
        $scope.veiligheid_url = "/veiligheid"
        $scope.long_time_login = false

        $scope.get_span_10_12_superuser = ->
            obj = {}
            obj["span12"] = true
            return obj

        $scope.get_cvar = (cvar_name) ->
            cvar.memget(cvar_name)

        cvar.get("cvar_is_super_user").then(
            (cvar_is_super_user) ->
                $scope.is_superuser = utils.exist_truth(cvar_is_super_user)

                $scope.get_span_10_12_superuser = ->
                    obj = {}

                    if cvar_is_super_user
                        obj["span10"] = true
                    else
                        obj["span12"] = true

                    return obj

            (e) ->
                warning "controller_base.cf:184", e
        )
        $rootScope.show_debug_info = false
        cvar.get("cvar_show_debug_info").then(
            (cvar_show_debug_info) ->
                $rootScope.show_debug_info = cvar_show_debug_info
                window.cvar_show_debug_info = cvar_show_debug_info

            (e) ->
                warning "controller_base.cf:193", e
        )

        $scope.get_logfile = ->
            res = _.map(window.g_logfile, (i) ->
                i)

            return res.reverse()

        $scope.get_current_server_time = ->
            serverclock.get_time()

        $scope.docs_url = ->
            memory.set("g_first_tree_render", true)
            g_last_parent_short_id = memory.get("g_last_parent_short_id")
            g_last_parent_node = memory.get("g_last_parent_node")

            if g_last_parent_short_id
                if g_last_parent_node.m_nodetype == "file"
                    urls.change_route($location, "/doc/" + g_last_parent_short_id)
                else
                    urls.change_route($location, "/docs/" + g_last_parent_short_id)
            else
                urls.change_route($location, "/docs")

            if memory.get("g_reload_browser")
                document.location = document.location

        $scope.on_docs = ->
            return utils.exist_truth($scope.docs)

        $scope.document_pill_enabled = ->
            obj = {}
            obj.active = $scope.docs

            if not $scope.docs
                obj.disabled = !cvar.get_cvar_loaded()
            obj

        $scope.instelling_pill_enabled = ->
            obj = {}
            obj.active = $scope.settings

            if not $scope.settings
                obj.disabled = !cvar.get_cvar_loaded()
            obj

        $scope.settings_url = ->
            if utils.ie8()
                urls.change_route($location, "/settings")
            else
                g_settings_tab_selected = memory.get("g_settings_tab_selected")

                if utils.exist(g_settings_tab_selected)
                    $scope.tab_security = false
                    $scope.tab_password = false
                    $scope.tab_users = false
                    $scope.tab_config = false

                    switch g_settings_tab_selected
                        when "personal"
                            $scope.tab_security = true
                            urls.change_route($location, "/settings/security")
                        when"password"
                            $scope.tab_password = true
                            urls.change_route($location, "/settings/personal")
                        when "users"
                            $scope.tab_users = true
                            urls.change_route($location, "/settings/users")
                        when "disk"
                            $scope.tab_config = true
                            urls.change_route($location, "/settings/disk")
                        else
                            $scope.tab_security = true
                            urls.change_route($location, "/settings/security")

                else
                    urls.change_route($location, "/settings/security")


    content_loaded: ->
        return


    authrender: ($rootScope, $scope, cvar, authorization, $location, cryptobox, tree, $routeParams, memory, clientcookies, utils, urls, $q, serverclock, saveobject, uploader) =>
        @base_init($rootScope, $scope, cvar, authorization, $location, cryptobox, tree, $routeParams, memory, clientcookies, utils, urls, $q, serverclock, saveobject, uploader)

        if not utils.exist_truth(clientcookies.get("c_persist_user_logged_in_status"))
            if utils.exist($routeParams.doc_id)
                clientcookies.set("c_unauth_link", String($location.$$path).replace("/"+cryptobox.slug(), ""))

        $scope.absolute_logout_url = urls.make_absolute_route("/logout")
        memory.critical_set("g_last_click", get_local_time())
        $scope.location_origin = window.location.origin

        set_device_type = ->
            w = $(window).innerWidth()
            h = $(window).innerHeight()

            if not utils.exist(w)
                return

            if not utils.exist(h)
                return
            #print("controller_base.cf:292", "resize", w, h)
            $rootScope.is_phone = false
            $rootScope.is_desktop = false
            $rootScope.is_tablet = false

            if m_width != w
                m_width = w

            if m_width == w
                if m_height == h
                    return

            if w < 768
                new_type = "phone"
                $rootScope.is_phone = true
            else if w >= 768 and w < 980
                new_type = "tablet"
                $rootScope.is_tablet = true
            else
                new_type = "desktop"
                $rootScope.is_desktop = true

            $scope.device_type = new_type
            if memory.has("g_device_type")
                if memory.get("g_device_type") != new_type
                    print "controller_base.cf:322", "running on"
                    print "controller_base.cf:323", "phone", utils.is_phone()
                    print "controller_base.cf:324", "tablet", utils.is_tablet()
                    print "controller_base.cf:325", "desktop", utils.is_desktop()
            else
                print "controller_base.cf:327", "running on", new_type

            if memory.has("g_window_width")
                if w != memory.get("g_window_width")
                    emit_event("controller_base.cf:333", $scope, "resize_window")

                    utils.force_digest($scope)

            memory.set("g_device_type", new_type)
            memory.set("g_window_width", w)
            memory.set("g_window_height", h)

            if window.devicePixelRatio?
                clientcookies.set("c_device_pixel_ratio", window.devicePixelRatio)

        set_device_type_once = _.once(set_device_type);
        set_device_type_once()
        last_resize = get_local_time()

        on_resize = (args) ->
            now = get_local_time()

            if (now - last_resize) > 500
                last_resize = get_local_time()
                set_device_type(args.target.innerWidth, args.target.innerHeight)

        $(window).resize(on_resize)

        on_orientation_change = ->
            _.defer(on_resize)

        $(window).on('orientationchange', on_orientation_change)

        onscroll = () ->
            memory.set("g_scrollTop_" + $location.$$path, $(window).scrollTop())

        $(window).scroll(onscroll)

        set_top = ->
            if not utils.is_desktop()
                if String(document.location).indexOf("docs") > 0
                    scrolltop = memory.get("g_scrollTop_" + $location.$$path)

                    if utils.exist(scrolltop)
                        $(window).scrollTop(scrolltop)

        async_call(set_top)

        $scope.get_footer_style = ->
            obj = {}

            if not $rootScope.chrome_browser
                obj["font-family"] = "monospace"

            return obj

        content_is_loaded = =>
            @content_loaded($rootScope, $scope, cvar, authorization, $location, cryptobox, tree, $routeParams, memory, clientcookies, utils, urls, $q, serverclock, saveobject, uploader)

        $scope.$on('$viewContentLoaded', content_is_loaded);
        $rootScope.browser = utils.browser()
        $rootScope.chrome_browser = false
        $rootScope.ie8_browser = false
        if utils.browser() == "Chrome"
            $rootScope.chrome_browser = true

        if utils.ie8()
            $rootScope.ie8_browser = true

        digest_requested =  ->
            if not $scope.$$phase
                $scope.$apply()

        $scope.$on("digest_request", digest_requested)

        $q.all([cvar.all(), cvar.get("cvar_username")]).then(
            (cvar_username) =>

                $scope.get_upload_progress_bar = ->
                    perc = uploader.get_upload_progress()

                    if $scope.progress > 99
                        return {width: "100%", height: "10px;"}
                    return {width: perc + "%", height: "10px;"}

                $scope.show_upload_progress = ->
                    if $scope.drop_detected
                        return true
                    upload_progress = uploader.get_upload_progress()

                    if not utils.exist(upload_progress)
                        return false

                    upload_progress or ($rootScope.upload_in_progress>0)

                $scope.get_upload_progress = ->
                    parseInt(uploader.get_upload_progress(), 10)

                $scope.droperror_rootlevel = false
                $scope.drop_detected = false

                $scope.get_droperror_rootlevel = ->
                    return $scope.droperror_rootlevel

                $scope.reset_droperror_rootlevel = ->
                    $scope.droperror_rootlevel = false

                $scope.reset_dropsuggestion = ->
                    $scope.dropsuggestion = false

                $scope.get_dropsuggestion = ->
                    return $scope.dropsuggestion

                $scope.file_drop_root_warning = false

                $scope.get_file_drop_root_warning = ->
                    return $scope.file_drop_root_warning

                $scope.drop_error_occurred = false

                $scope.get_drop_error_occurred = ->
                    return $scope.drop_error_occurred

                $scope.reset_drop_error = ->
                    $scope.drop_error_occurred = false
                    utils.force_digest($scope)

                $scope.drop_error_other_file_occurred = false

                $scope.get_drop_error_other_file_occurred = ->
                    return $scope.drop_error_other_file_occurred

                $scope.reset_drop_error_other_file = ->
                    $scope.drop_error_other_file_occurred = false
                    utils.force_digest($scope)

                $scope.num_selectedFiles = ->
                    return _.size($scope.files_selected_for_upload)

                $scope.remove_file_upload_error = (uuid) ->
                    tree.remove_file_upload_error(uuid)

                memory.counter("g_drop_file_index")

                traverseFileTree = (item, path) ->
                    path = path or ""

                    if item.isFile
                        error_read = (e) ->
                            $scope.drop_error = e
                            warning "controller_base.cf:477", "Read file error code", e
                            $scope.drop_error_occurred = true
                            utils.force_digest($scope)

                        getfile = (file) ->
                            if _.size(path) > 0
                                file.relPath = utils.ltrim(path, "/")

                            uploader.add_to_upload_queue(file)

                        item.file(getfile, error_read)
                    else if item.isDirectory
                        dirReader = item.createReader()

                        error_read = (e) ->
                            $scope.drop_error = e
                            warning "controller_base.cf:493", "Directory FileError code", e
                            $scope.drop_error_occurred = true
                            utils.force_digest($scope)

                        read_entries = (entries) ->
                            i = 0

                            while i < entries.length
                                traverseFileTree entries[i], item.fullPath
                                i++

                        dirReader.readEntries(read_entries, error_read)

                $scope.no_drops = false

                $scope.get_no_drops = ->
                    return $scope.no_drops

                $scope.reset_no_drops = ->
                    $scope.no_drops = false

                drop_f = (evt) ->
                    $rootScope.dragover = false
                    utils.force_digest($scope)
                    evt.stopPropagation()
                    evt.preventDefault()

                    if not utils.chrome() or not utils.exist_truth($scope.current_user.m_is_superuser)
                        $scope.no_drops = true
                        utils.force_digest($scope)
                        return

                    $scope.drop_detected = true
                    items = evt.dataTransfer.items
                    files = evt.dataTransfer.files
                    if _.size(files) == 0
                        return

                    i = 0
                    num_items = items.length

                    while i < num_items
                        item = items[i].webkitGetAsEntry()

                        if item
                            traverseFileTree item, ""
                        i++

                    last_check = 0
                    last_check_cnt = 0

                    check_queue_start_download = ->
                        if uploader.files_selected_for_upload() > 0
                            print "controller_base.cf:544", "last_check_cnt", last_check_cnt
                            if uploader.files_selected_for_upload() == last_check
                                last_check_cnt += 1
                            else
                                last_check = uploader.files_selected_for_upload()
                                last_check_cnt = 0
                                return false

                            if last_check_cnt > 4
                                tree.get().then(
                                    (treenodes) ->
                                        $scope.parent = tree.get_node($routeParams.doc_id, treenodes)

                                        upload_succes = (r) ->
                                            print "controller_base.cf:558", "upload_succes", r
                                            uploader.reset()
                                            tree.invalidate()
                                            emit_event("controller_base.cf:562", $rootScope, "tree_out_of_sync")

                                        upload_error = (r) ->
                                            print "controller_base.cf:564", "upload_error", r
                                        uploader.upload_start(upload_succes, upload_error)
                                        $scope.drop_detected = false

                                    (err) ->
                                        print "controller_base.cf:569", err
                                )
                                return true
                        return false

                    utils.call_until_sentinal_hits_repeats(check_queue_start_download, null, 500, [false], 20, true, 40)
                    return false
                dropzone = document.getElementById("ng-app")
                memory.set("g_show_upload_area", true)

                dragEnterLeave = (evt) ->
                    $rootScope.dragover = false
                    utils.force_digest($scope)
                    evt.stopPropagation()
                    evt.preventDefault()

                dropzone.addEventListener? "dragover", (evt) ->
                    $rootScope.dragover = true
                    evt.stopPropagation()
                    evt.preventDefault()

                dropzone.addEventListener?("drop", drop_f)
                dropzone.addEventListener? "dragenter", dragEnterLeave, false
                dropzone.addEventListener? "dragleave", dragEnterLeave, false



                g_check_droplist_interval = memory.get("g_check_droplist_interval")

                if g_check_droplist_interval
                    clearInterval(g_check_droplist_interval)

                $scope.username = cvar_username[1]
                @init($rootScope, $scope, cvar, authorization, $location, cryptobox, tree, $routeParams, memory, clientcookies, utils, urls, $q, serverclock, saveobject, uploader)

                if not utils.exist($rootScope.current_user)
                    authorization.get_current_user().then(
                        (user) ->
                            $rootScope.current_user = user

                        (error) ->
                            warning "controller_base.cf:622", error
                            return
                    )

                $scope.get_debug_mode = ->
                    return memory.debug_mode()

                cvar.get("cvar_disable_caching").then(
                    (resolve_result) =>
                        if utils.exist_truth(resolve_result)
                            utils.remove_cache()

                    (error_result) ->
                        warning "controller_base.cf:635", "could not fetch cvar_disable_caching", error_result
                )

                clientcookies.ensure_memory()
                @baseprerender($rootScope, $scope, cvar, authorization, $location, cryptobox, tree, $routeParams, memory, clientcookies, utils, urls, $q, serverclock, saveobject, uploader)
                @prerender($rootScope, $scope, cvar, authorization, $location, cryptobox, tree, $routeParams, memory, clientcookies, utils, urls, $q, serverclock, saveobject, uploader)
                @base_interval_second($rootScope, $scope, cvar, authorization, $location, cryptobox, tree, $routeParams, memory, clientcookies, utils, urls, $q, serverclock, saveobject, uploader)
                @interval_second($rootScope, $scope, cvar, authorization, $location, cryptobox, tree, $routeParams, memory, clientcookies, utils, urls, $q, serverclock, saveobject, uploader)
                service_id = "g_service_second_interval_" + get_guid()
                now = get_local_time()
                secondstart = now
                minutestart = now
                tensecondstart = now


                f_interval = =>
                    now = get_local_time()
                    @interval_fast($rootScope, $scope, cvar, authorization, $location, cryptobox, tree, $routeParams, memory, clientcookies, utils, urls, $q, serverclock, saveobject, uploader)

                    if memory.bool_test("g_digest_requested")
                        memory.critical_set("g_digest_requested", false)

                        if not $scope.$$phase
                            $scope.$apply()

                    if parseFloat(now - secondstart) > 1000
                        secondstart = now
                        @base_interval_second($rootScope, $scope, cvar, authorization, $location, cryptobox, tree, $routeParams, memory, clientcookies, utils, urls, $q, serverclock, saveobject, uploader)
                        @interval_second($rootScope, $scope, cvar, authorization, $location, cryptobox, tree, $routeParams, memory, clientcookies, utils, urls, $q, serverclock, saveobject, uploader)
                        memory.increment_counter("g_second_interval")

                    if parseFloat(now - tensecondstart) > (1000 * 10)
                        tensecondstart = now
                        memory.increment_counter("g_ten_second_interval")

                        if not $scope.$$phase
                            $scope.$apply()

                    if parseFloat(now - minutestart) > (1000 * 60)
                        minutestart = now
                        @base_interval_minute($rootScope, $scope, cvar, authorization, $location, cryptobox, tree, $routeParams, memory, clientcookies, utils, urls, $q, serverclock, saveobject, uploader)
                        @interval_minute($rootScope, $scope, cvar, authorization, $location, cryptobox, tree, $routeParams, memory, clientcookies, utils, urls, $q, serverclock, saveobject, uploader)

                        if memory.bool_test("g_cvar_dirty")
                            cvar.commit_retrieve_all()
                            memory.set("g_cvar_dirty", false)

                if utils.ie8()
                    second_interval = utils.set_interval("controller_base.cf:666", f_interval, 1000, "f_interval")
                else
                    second_interval = utils.set_interval("controller_base.cf:668", f_interval, 250, "f_interval")
                memory.set(service_id, second_interval)

                delete_service_interval_memory =  (service) =>
                    if (service != service_id) and not service.endsWith("_start")
                        clearInterval(memory.get(service))
                        memory.del(service)

                _.each(memory.all_keys_prefix("g_service_second_interval"), delete_service_interval_memory)
                @render_auth($rootScope, $scope, cvar, authorization, $location, cryptobox, tree, $routeParams, memory, clientcookies, utils, urls, $q, serverclock, saveobject, uploader)
                m_updating_cvars = false

                @set_logged_minutes($scope, cvar, $q).then(
                    (result) =>
                        $scope.logged_minutes = result
                        memory.set("g_prev_logged_minutes", result)

                    (e) ->
                        warning "controller_base.cf:702", e
                )

            (reject_result) ->
                if reject_result.status == 403
                    print "controller_base.cf:707", "not authorized, route to login"
                    authorization.to_login()
                else
                    print "controller_base.cf:710", "could not load cvars, or not authorized", reject_result
        )


init_ctrl = (CtrlClass) ->
    ctrl = new CtrlClass().authrender
    ctrl.$inject = ['$rootScope', '$scope', 'cvar', 'authorization', '$location', 'cryptobox', 'tree', '$routeParams', 'memory', 'clientcookies', 'utils', 'urls', '$q', 'serverclock', 'saveobject', 'uploader'];
    return ctrl

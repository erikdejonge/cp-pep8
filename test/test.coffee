
utils.print_once "test.cf:2", 1
print "test.cf:3", 2

warning "test.cf:5", 3


emit_event("test.cf:8", 2)


urls.command("test.cf:11", 3)


urls.postcommand("test.cf:14", 3)


async_call_retries("test.cf:17", 4)


utils.set_time_out("test.cf:20", 4)


utils.set_interval("test.cf:23", 2)

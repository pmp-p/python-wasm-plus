def calls(frame, event, arg):
    if event != "call":
        return
    co = frame.f_code
    func_name = co.co_name
    if func_name in ("write"):
        return
    func_line_no = frame.f_lineno
    func_filename = co.co_filename

    if func_filename.startswith("/usr/lib/python3."):
        return

    if func_filename.find("/aio/") > 0:
        return

    caller = frame.f_back
    if caller:
        caller_line_no = caller.f_lineno
        caller_filename = caller.f_code.co_filename
        if caller_filename != func_filename:
            print(
                "%s() on line %s of %s from line %s of %s"
                % (
                    func_name,
                    func_line_no,
                    func_filename,
                    caller_line_no,
                    caller_filename,
                )
            )
        else:
            print(f"{func_name} {func_filename}:{caller_line_no}->{func_line_no}")
    return

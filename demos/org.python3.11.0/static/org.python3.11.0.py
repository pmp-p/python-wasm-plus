import sys, os
import asyncio
six = '/data/data/org.python/assets/cpython.six'
if os.path.isfile(six):
    print(open(six).read())

print('CPython',sys.version,'\n', file=sys.stderr)

def stdlib():
    embed.js('mount_at("org.python3.11.0.apk", "/usr/lib", "/assets")')
    __import__('importlib').invalidate_caches()


stdlib()

async def run_tests(tlist):
    global RT, BAD, ALL, FAILS
    BAD = []
    print("Starting now ...")
    for t in tlist:
        RT._main([t], {})
        for bad in RT.bad:
            if not bad in BAD:
                BAD.append(bad)
        RT.bad.clear()
        #print("BAD",len(BAD),":", *BAD)
        await asyncio.sleep(0)

    print("========== run_tests done ============")
    print("Tests total:", len(ALL) )
    print("Failed total:", len(FAILS)+len(BAD) )
    print("Recent failures:", *BAD)
    print("skipped known fails:", *FAILS )


def sys_exit(*ec):
    pass

sys.exit = sys_exit

def skip_list():
    HARMLESS= """
test.test_strftime.StrftimeTest.test_strftime

test.test_decimal.CWhitebox.test_from_tuple

test.test_sys.SysModuleTest.test_exit

test.test_exceptions.ExceptionTests.testRaising

test.test_sysconfig.TestSysConfig.test_get_config_h_filename

test.test_uu.UUFileTest.test_decode_mode

test.test_float.HexFloatTestCase.test_from_hex

test.test_capi.SubinterpreterTest.test_module_state_shared_in_global

test.test_cmath.CMathTests.test_specific_values

test.test_zipfile.TestsWithMultipleOpens.test_many_opens
test.test_zipfile.EncodedMetadataTests.test_cli_with_metadata_encoding
test.test_zipfile.OtherTests.test_comments
test.test_zipfile.StoredTestsWithSourceFile.test_add_file_before_1980

"""
    SKIP = HARMLESS + """
test.test_bytes.BytesTest.test_from_format
test.test_decimal.CWhitebox.test_maxcontext_exact_arith

ctypes.test.test_as_parameter.AsParamPropertyWrapperTestCase.test_byval
ctypes.test.test_as_parameter.AsParamPropertyWrapperTestCase.test_callbacks
ctypes.test.test_as_parameter.AsParamPropertyWrapperTestCase.test_callbacks_2
ctypes.test.test_as_parameter.AsParamPropertyWrapperTestCase.test_longlong_callbacks
ctypes.test.test_as_parameter.AsParamPropertyWrapperTestCase.test_shorts
ctypes.test.test_as_parameter.AsParamWrapperTestCase.test_callbacks
ctypes.test.test_as_parameter.AsParamWrapperTestCase.test_callbacks_2
ctypes.test.test_as_parameter.AsParamWrapperTestCase.test_longlong_callbacks
ctypes.test.test_as_parameter.AsParamWrapperTestCase.test_shorts
ctypes.test.test_as_parameter.BasicWrapTestCase.test_callbacks
ctypes.test.test_as_parameter.BasicWrapTestCase.test_callbacks_2
ctypes.test.test_as_parameter.BasicWrapTestCase.test_longlong_callbacks
ctypes.test.test_as_parameter.BasicWrapTestCase.test_shorts
ctypes.test.test_callbacks.Callbacks.test_byte
ctypes.test.test_callbacks.Callbacks.test_char
ctypes.test.test_callbacks.Callbacks.test_double
ctypes.test.test_callbacks.Callbacks.test_float
ctypes.test.test_callbacks.Callbacks.test_int
ctypes.test.test_callbacks.Callbacks.test_issue12483
ctypes.test.test_callbacks.Callbacks.test_issue_7959
ctypes.test.test_callbacks.Callbacks.test_long
ctypes.test.test_callbacks.Callbacks.test_longdouble
ctypes.test.test_callbacks.Callbacks.test_longlong
ctypes.test.test_callbacks.Callbacks.test_pyobject
ctypes.test.test_callbacks.Callbacks.test_short
ctypes.test.test_callbacks.Callbacks.test_ubyte
ctypes.test.test_callbacks.Callbacks.test_uint
ctypes.test.test_callbacks.Callbacks.test_ulong
ctypes.test.test_callbacks.Callbacks.test_ulonglong
ctypes.test.test_callbacks.Callbacks.test_unsupported_restype_1
ctypes.test.test_callbacks.Callbacks.test_unsupported_restype_2
ctypes.test.test_callbacks.Callbacks.test_ushort
ctypes.test.test_callbacks.SampleCallbacksTestCase.test_callback_large_struct
ctypes.test.test_callbacks.SampleCallbacksTestCase.test_callback_register_double
ctypes.test.test_callbacks.SampleCallbacksTestCase.test_callback_register_int
ctypes.test.test_callbacks.SampleCallbacksTestCase.test_callback_too_many_args
ctypes.test.test_callbacks.SampleCallbacksTestCase.test_convert_result_error
ctypes.test.test_callbacks.SampleCallbacksTestCase.test_integrate
ctypes.test.test_callbacks.SampleCallbacksTestCase.test_issue_8959_a
ctypes.test.test_frombuffer.Test.test_fortran_contiguous
ctypes.test.test_funcptr.CFuncPtrTestCase.test_basic
ctypes.test.test_funcptr.CFuncPtrTestCase.test_first
ctypes.test.test_funcptr.CFuncPtrTestCase.test_structures
ctypes.test.test_functions.FunctionTestCase.test_callbacks
ctypes.test.test_functions.FunctionTestCase.test_callbacks_2
ctypes.test.test_functions.FunctionTestCase.test_longlong_callbacks
ctypes.test.test_functions.FunctionTestCase.test_sf1651235
ctypes.test.test_functions.FunctionTestCase.test_shorts
ctypes.test.test_libc.LibTest.test_qsort
ctypes.test.test_pickling.PickleTest_0.test_unpickable
ctypes.test.test_pickling.PickleTest_1.test_unpickable
ctypes.test.test_pickling.PickleTest_2.test_unpickable
ctypes.test.test_pickling.PickleTest_3.test_unpickable
ctypes.test.test_pickling.PickleTest_4.test_unpickable
ctypes.test.test_pickling.PickleTest_5.test_unpickable
ctypes.test.test_pointers.PointersTestCase.test_callbacks_with_pointers
ctypes.test.test_prototypes.ArrayTest.test
ctypes.test.test_python_api.PythonAPITestCase.test_PyOS_snprintf
ctypes.test.test_random_things.CallbackTracbackTestCase.test_FloatDivisionError
ctypes.test.test_random_things.CallbackTracbackTestCase.test_IntegerDivisionError
ctypes.test.test_random_things.CallbackTracbackTestCase.test_TypeErrorDivisionError
ctypes.test.test_random_things.CallbackTracbackTestCase.test_ValueError
ctypes.test.test_refcounts.AnotherLeak.test_callback
ctypes.test.test_refcounts.RefcountTestCase.test_1
ctypes.test.test_refcounts.RefcountTestCase.test_refcount
ctypes.test.test_simplesubclasses.Test.test_ignore_retval
ctypes.test.test_simplesubclasses.Test.test_int_callback
"""
    for skip in SKIP.replace('\n',' ').split(' '):
        if skip:
            sys.argv.append("-i")
            sys.argv.append(skip)


def testv(argv):
    from test.libregrtest.main import Regrtest
    RT = Regrtest()
    sys.argv.append("-v")
    skip_list()
    RT.parse_args({})
    RT._main([argv], {})




def test(*argv):
    global RT, tlist, FAILS, ALL

    from test.libregrtest.main import Regrtest
    RT = Regrtest()
    if len(argv):
        sys.argv.extend(*argv)

    skip_list()

    RT.parse_args({})

    TESTS = """
    test_grammar test_opcodes test_dict
    test___all__ test___future__ test__locale test__opcode
    test__osx_support test__xxsubinterpreters test_abc
    test_abstract_numbers test_aifc test_argparse test_array
    test_asdl_parser test_ast test_asyncgen test_asynchat test_asyncio
    test_asyncore test_atexit test_audioop test_audit test_augassign
    test_base64 test_baseexception test_bdb test_bigaddrspace
    test_bigmem test_binascii test_binop test_bisect test_bool
    test_buffer test_bufio test_builtin test_bytes test_bz2
    test_c_locale_coercion test_calendar test_call test_capi test_cgi
    test_cgitb test_charmapcodec test_check_c_globals test_class
    test_clinic test_cmath test_cmd test_cmd_line test_cmd_line_script
    test_code test_code_module test_codeccallbacks
    test_codecencodings_cn test_codecencodings_hk
    test_codecencodings_iso2022 test_codecencodings_jp
    test_codecencodings_kr test_codecencodings_tw test_codecmaps_cn
    test_codecmaps_hk test_codecmaps_jp test_codecmaps_kr
    test_codecmaps_tw test_codecs test_codeop test_collections
    test_colorsys test_compare test_compile test_compileall
    test_complex test_concurrent_futures test_configparser
    test_contains test_context test_contextlib test_contextlib_async
    test_copy test_copyreg test_coroutines test_cprofile test_crashers
    test_crypt test_csv test_ctypes test_curses test_dataclasses
    test_datetime test_dbm test_dbm_dumb test_dbm_gnu test_dbm_ndbm
    test_decimal test_decorators test_defaultdict test_deque
    test_descr test_descrtut test_devpoll test_dict test_dict_version
    test_dictcomps test_dictviews test_difflib test_dis test_distutils
    test_doctest test_doctest2 test_docxmlrpc test_dtrace test_dynamic
    test_dynamicclassattribute test_eintr test_email test_embed
    test_ensurepip test_enum test_enumerate test_eof test_epoll
    test_errno test_except_star test_exception_group
    test_exception_hierarchy test_exception_variations test_exceptions
    test_extcall test_faulthandler test_fcntl test_file
    test_file_eintr test_filecmp test_fileinput test_fileio
    test_fileutils test_finalization test_float test_flufl
    test_fnmatch test_fork1 test_format test_fractions test_frame
    test_frozen test_fstring test_ftplib test_funcattrs test_functools
    test_future test_future3 test_future4 test_future5 test_gc
    test_gdb test_generator_stop test_generators test_genericalias
    test_genericclass test_genericpath test_genexps test_getargs2
    test_getopt test_getpass test_getpath test_gettext test_glob
    test_global test_graphlib test_grp test_gzip test_hash
    test_hashlib test_heapq test_hmac test_html test_htmlparser
    test_http_cookiejar test_http_cookies test_httplib
    test_httpservers test_idle test_imaplib test_imghdr test_imp
    test_import test_importlib test_index test_inspect test_int
    test_int_literal test_interpreters test_io test_ioctl
    test_ipaddress test_isinstance test_iter test_iterlen
    test_itertools test_json test_keyword test_keywordonlyarg
    test_kqueue test_largefile test_launcher test_lib2to3
    test_linecache test_list test_listcomps test_lltrace test_locale
    test_logging test_long test_longexp test_lzma test_mailbox
    test_mailcap test_marshal test_math test_memoryio test_memoryview
    test_metaclass test_mimetypes test_minidom test_mmap test_module
    test_modulefinder test_msilib test_multibytecodec
    test_multiprocessing_fork test_multiprocessing_forkserver
    test_multiprocessing_main_handling test_multiprocessing_spawn
    test_named_expressions test_netrc test_nis test_nntplib
    test_ntpath test_numeric_tower test_opcache test_openpty
    test_operator test_optparse test_ordered_dict test_os
    test_ossaudiodev test_osx_env test_pathlib test_patma test_pdb
    test_peepholer test_peg_generator test_pep646_syntax test_pickle
    test_picklebuffer test_pickletools test_pipes test_pkg
    test_pkgutil test_platform test_plistlib test_poll test_popen
    test_poplib test_positional_only_arg test_posix test_posixpath
    test_pow test_pprint test_print test_profile test_property
    test_pstats test_pty test_pulldom test_pwd test_py_compile
    test_pyclbr test_pydoc test_pyexpat test_queue test_quopri
    test_raise test_random test_range test_re test_readline
    test_regrtest test_repl test_reprlib test_resource test_richcmp
    test_rlcompleter test_robotparser test_runpy test_sax test_sched
    test_scope test_script_helper test_secrets test_select
    test_selectors test_set test_setcomps test_shelve test_shlex
    test_shutil test_signal test_site test_slice test_smtpd
    test_smtplib test_smtpnet test_sndhdr test_socket
    test_socketserver test_sort test_source_encoding test_spwd
    test_ssl test_stable_abi_ctypes test_startfile test_stat
    test_statistics test_strftime test_string test_string_literals
    test_stringprep test_strptime test_strtod test_struct
    test_structmembers test_structseq test_subclassinit
    test_subprocess test_sunau test_sundry test_super test_support
    test_symtable test_syntax test_sys test_sys_setprofile
    test_sys_settrace test_sysconfig test_syslog test_tabnanny
    test_tarfile test_tcl test_telnetlib test_tempfile test_textwrap
    test_thread test_threadedtempfile test_threading
    test_threading_local test_threadsignals test_time test_timeit
    test_timeout test_tix test_tk test_tokenize test_tools test_trace
    test_traceback test_tracemalloc test_ttk_guionly test_ttk_textonly
    test_tuple test_turtle test_type_annotations test_type_cache
    test_type_comments test_typechecks test_types test_typing test_ucn
    test_unary test_unicode test_unicode_file
    test_unicode_file_functions test_unicode_identifiers
    test_unicodedata test_unittest test_univnewlines test_unpack
    test_unpack_ex test_unparse test_urllib test_urllib2
    test_urllib2_localnet test_urllib2net test_urllib_response
    test_urllibnet test_urlparse test_userdict test_userlist
    test_userstring test_utf8_mode test_utf8source test_uu test_uuid
    test_venv test_wait3 test_wait4 test_warnings test_wave
    test_weakref test_weakset test_webbrowser test_winconsoleio
    test_winreg test_winsound test_with test_wsgiref test_xdrlib
    test_xml_dom_minicompat test_xml_etree test_xml_etree_c
    test_xmlrpc test_xmlrpc_net test_xxlimited test_xxtestfuzz
    test_yield_from test_zipapp test_zipfile test_zipfile64
    test_zipimport test_zipimport_support test_zlib test_zoneinfo
"""


    FAILS = []

    # those are fatal
    FAILS += ["test_code"]

    # those are extremely slow and fail
    FAILS += ["test_zipfile"]


    # known to fail

    for t in """
test_builtin test_argparse test_cgi test_code_module
test_dbm_dumb test_distutils test_ensurepip test_fileio
test_genericpath test_getpath test_importlib test_inspect
test_io test_mailbox test_mailcap test_math test_mimetypes test_multibytecodec
test_netrc test_ntpath test_numeric_tower test_os test_pathlib test_pickle
test_plistlib test_posix test_posixpath test_profile test_pydoc test_random
test_rlcompleter test_sax test_shelve test_shutil test_signal test_stat
test_strftime test_strtod test_sunau test_support test_sys test_tarfile
test_tempfile test_trace test_traceback test_tracemalloc test_unicode
test_unicode_file_functions test_unittest test_univnewlines test_urllib
test_wave test_zipapp
""".replace('\n',' ').split(' '):
        if t and not t in FAILS:
            FAILS.append(t)

    tlist = []
    start_list = True
    ALL = []
    for t in TESTS.replace('\n',' ').split(' '):
        if t:
            ALL.append(t)
            if not start_list:
                if t==FAILS[-1]:
                    start_list = True
                continue

            if t not in FAILS:
                tlist.append(t)
    asyncio.run( run_tests( tlist ) )

print( sys._emscripten_info )


if len(sys.argv[-1]):
    if sys.argv[-1]!='all':
        print("starting one verbose test : ",sys.argv[-1])
        aio.defer( testv, (sys.argv[-1],),{}, 2000)
    else:
        print(" - starting full testsuite in a few seconds -")
        aio.defer( test, (),{}, 10000)

else:
    print("""

    test() => run whole testsuite
    testv("test_xxxx") => run the test_xxxxx verboe


""")













#




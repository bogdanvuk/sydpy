cdef extern from "string.h" nogil:
     char   *strcpy  (char *pto, const char *pfrom)

cdef extern from "xsimintf.c":
    int decode_command()
    const char* xsimintf_export(const char * vals)
    const char* xsimintf_import()
    int xsimintf_delay()
    void xsimintf_init()
    void cmd_handler()
    char* msg_buf
    int msg_buf_cnt
    ctypedef struct T_Command:
        int cmd
        char params[128][1024]
        int param_cnt

    T_Command recv_cmd

callbacks = {}

def say_hello_to(name):
    print("Hello %s!" % name)

def pass_msg(bytes msg):
    global msg_buf
    global msg_buf_cnt
    cdef char* c_msg = msg
    strcpy(msg_buf, c_msg)
    msg_buf_cnt = len(msg)

def read_msg():
    global msg_buf
    return msg_buf

def decode():
    return decode_command()

def get_recv_cmd():
    global recv_cmd
    return recv_cmd

def command_handler():
    cmd_handler()

def sv_export(bytes data):
    return <bytes> xsimintf_export(<char*> data)

def sv_import():
    return <bytes> xsimintf_import()

def sv_delay():
    return xsimintf_delay()

def sv_init():
    return xsimintf_init()

cdef public void cython_get_new_message():
     callbacks['get_new_message']()

cdef public void cython_post_new_message():
     callbacks['post_new_message']()

cdef public void cython_print(const char* str):
     print(<bytes> str)

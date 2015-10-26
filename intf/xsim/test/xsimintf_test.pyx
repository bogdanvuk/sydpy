cdef extern from "string.h" nogil:
     char   *strcpy  (char *pto, const char *pfrom)

cdef extern from "xsimintf.c":
    int decode_command()
    char* msg_buf
    int msg_buf_cnt
    ctypedef struct T_Command:
        int cmd
        char params[128][32]
        int param_cnt

    T_Command cur_cmd

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

def get_cur_cmd():
    global cur_cmd
    return cur_cmd

import xsimintf_test
import random
import string

commands = ['GET', 'SET', 'IMPORT', 'EXPORT', 'ERROR']

def test_command_decode():
    for _ in range(100):
        params = []
        for _ in range(random.randint(0,128)):
            params.append(''.join(random.choice(string.ascii_letters + string.digits) for _ in range(random.randint(1, 31))))

        cmd_id = random.randint(0,len(commands)-1)
        command = '$' + commands[cmd_id]
        msg = ','.join([command] + params)
        xsimintf_test.pass_msg(msg.encode())
        xsimintf_test.decode()
        decoded_cmd = xsimintf_test.get_recv_cmd()
        assert decoded_cmd['param_cnt'] == len(params), "Error in decoding: \n\n{0}\n\n{1}".format(msg, decoded_cmd)
        assert decoded_cmd['cmd'] == cmd_id, "Error in decoding: \n\n{0}\n\n{1}".format(msg, decoded_cmd)

        for param, dec_param in zip(params, decoded_cmd['params']):
            assert param == dec_param.decode(), "Error in decoding: \n\n{0}\n\n{1}".format(msg, decoded_cmd)

def test_get_set():

    class MsgDispatch:
        def __init__(self, cnt):
            self.state_vals = [random.randint(0,256) for _ in range(cnt)]
            self.state_val_cnt = 0
            self.state = "SET"
            self.max_vals = cnt

        def get_new_message(self):
            if self.state == "SET":
                xsimintf_test.pass_msg("$SET,state,{0}".format(self.state_vals[self.state_val_cnt]).encode())
            elif self.state == "GET":
                xsimintf_test.pass_msg("$GET,state".encode())
            else:
                xsimintf_test.pass_msg("$CONTINUE".encode())

        def post_new_message(self):
            msg = xsimintf_test.read_msg().decode()

            if self.state == "SET":
                assert msg == "$RESP"
                self.state = "GET"
            elif self.state == "GET":
                assert msg == "$RESP,{0}".format(self.state_vals[self.state_val_cnt])
                self.state = "SET"
                self.state_val_cnt += 1
                if self.state_val_cnt >= self.max_vals:
                    self.state = "CONTINUE"
            else:
                assert msg == "$RESP"

    dispatch = MsgDispatch(100)

    xsimintf_test.callbacks = {'get_new_message': dispatch.get_new_message,
                               'post_new_message' : dispatch.post_new_message}
    xsimintf_test.command_handler();

def test_command_handler():
    state_type = {0: "S_STARTED", 1: "S_CONNECTED", 2: "S_INITIALIZED", 3:"S_IMPORT", 4:"S_EXPORT", 5:"S_DELAY"};
    class MsgDispatch:
        def __init__(self, ):
            self.state = "GET_STATE"
            self.xsimintf_state = 0
            self.delay = 0

        def loop(self, cycles, delta_cycles):
            xsimintf_test.sv_init()
            for i in range(cycles):
                delay = xsimintf_test.sv_delay()
                assert delay == self.delay
                sv_import = xsimintf_test.sv_import().decode()
                assert sv_import == ','.join(self.sv_import)
                for j in range(delta_cycles):
                    self.sv_export = []
                    for _ in range(random.randint(0,128)):
                        self.sv_export.append(''.join(random.choice(string.ascii_letters + string.digits) for _ in range(random.randint(1, 31))))

                    sv_import = xsimintf_test.sv_export(','.join(self.sv_export).encode()).decode()
                    assert sv_import == ','.join(self.sv_import)

        def get_new_message(self):
            if self.state == "GET_STATE":
                xsimintf_test.pass_msg("$GET,state".encode())
            elif self.state == "CONTINUE":
                xsimintf_test.pass_msg("$CONTINUE".encode())
            elif self.state == "SET_DELAY":
                xsimintf_test.pass_msg("$SET,delay,{0}".format(self.delay).encode())
            elif self.state == "IMPORT":
                xsimintf_test.pass_msg("$IMPORT,{0}".format(','.join(self.sv_import)).encode())
            elif self.state == "EXPORT":
                xsimintf_test.pass_msg("$EXPORT".encode())

        def post_new_message(self):
            msg = xsimintf_test.read_msg().decode().split(',')
            if self.state == "GET_STATE":
                assert msg[0] == "$RESP"
                self.xsimintf_state = state_type[int(msg[1])]
                if self.xsimintf_state == "S_CONNECTED":
                    self.state = "CONTINUE"
                elif self.xsimintf_state == "S_DELAY":
                    self.delay = random.randint(1,256)
                    self.state = "SET_DELAY"
                elif self.xsimintf_state == "S_IMPORT":
                    self.sv_import = []
                    for _ in range(random.randint(0,128)):
                        self.sv_import.append(''.join(random.choice(string.ascii_letters + string.digits) for _ in range(random.randint(1, 31))))

                    self.state = "IMPORT"
                elif self.xsimintf_state == "S_EXPORT":
                    self.state = "EXPORT"
            elif self.state == "SET_DELAY":
                self.state = "CONTINUE"
            elif self.state == "IMPORT":
                self.state = "CONTINUE"
            elif self.state == "EXPORT":
                self.state = "IMPORT"
                for a,b in zip(self.sv_export, msg[1:]):
                    assert a == b
            elif self.state == "CONTINUE":
                assert msg[0] == "$RESP"
                self.state = "GET_STATE"

    dispatch = MsgDispatch()

    xsimintf_test.callbacks = {'get_new_message': dispatch.get_new_message,
                               'post_new_message' : dispatch.post_new_message}

    dispatch.loop(100,10)

test_command_decode()
test_get_set()
test_command_handler()

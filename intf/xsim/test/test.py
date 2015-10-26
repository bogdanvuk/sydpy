import xsimintf_test
import random
import string

commands = ['GET', 'SET', 'IMPORT', 'EXPORT', 'ERROR']

def test_command_decode():
    for _ in range(1000):
        params = []
        for _ in range(random.randint(0,128)):
            params.append(''.join(random.choice(string.ascii_letters + string.digits) for _ in range(random.randint(1, 31))))

        cmd_id = random.randint(0,len(commands)-1)
        command = '$' + commands[cmd_id]
        msg = ','.join([command] + params)
        xsimintf_test.pass_msg(msg.encode())
        xsimintf_test.decode()
        decoded_cmd = xsimintf_test.get_cur_cmd()
        assert decoded_cmd['param_cnt'] == len(params), "Error in decoding: \n\n{0}\n\n{1}".format(msg, decoded_cmd)
        assert decoded_cmd['cmd'] == cmd_id, "Error in decoding: \n\n{0}\n\n{1}".format(msg, decoded_cmd)

        for param, dec_param in zip(params, decoded_cmd['params']):
            assert param == dec_param.decode(), "Error in decoding: \n\n{0}\n\n{1}".format(msg, decoded_cmd)

test_command_decode()

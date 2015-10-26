#include <svdpi.h>
#include <stdio.h>
#include "xsimintf_socket.h"

#define IMPORT_BUF_LEN 8192
#define MAX_PARAMS 128
#define MAX_PARAM_LEN 32

FILE *fp = NULL;
int cur_time = 0;
char msg_buf[IMPORT_BUF_LEN] = "";
int msg_buf_cnt = 0;

enum state_type {STARTED, CONNECTED, INITIALIZED};
enum state_type state;
enum command_type { GET, SET, IMPORT, EXPORT, ERROR, NUMBER_OF_COMMAND_TYPES };

const char *command_names[NUMBER_OF_COMMAND_TYPES] = {
    "$GET", "$SET", "$IMPORT", "$EXPORT", "$ERROR"
};

typedef struct {
    enum command_type cmd;
    char params[MAX_PARAMS][MAX_PARAM_LEN];
    int param_cnt;
} T_Command;

T_Command cur_cmd;

static int get_new_message(void) {
    msg_buf_cnt = socket_recv(msg_buf, IMPORT_BUF_LEN);
    return msg_buf_cnt;
}

static int decode_command(void) {
    char *token;
    int token_cnt = 0;
    int i;

    if (msg_buf_cnt > 0) {
        cur_cmd.cmd = ERROR;
        cur_cmd.param_cnt = 0;

        token = strtok (msg_buf,",");

        while (token != NULL)
        {
            if (token_cnt == 0) {
                for(i = 0; i < NUMBER_OF_COMMAND_TYPES; ++i)
                {
                    if(!strcmp(command_names[i], token))
                    {
                        cur_cmd.cmd = i;
                        break;
                    }
                }
            } else {
                strncpy(cur_cmd.params[token_cnt-1], token, MAX_PARAM_LEN);

            }
            token_cnt++;
            token = strtok (NULL, ",");
        }

        cur_cmd.param_cnt = token_cnt - 1;
    }

    return msg_buf_cnt;
}


DPI_DLLESPEC void xsimintf_init(void)
{
    state = STARTED;
    fp = fopen("xsimintf.log", "w");
    if (fp != NULL) {
        fprintf(fp, "XSIMINTF INITIALIZED\n");
    }
    cur_time = 0;
    if (socket_open() == 0) {
        fprintf(fp, "SOCKET OPENED\n");
    } else {
        fprintf(fp, "SOCKET OPEN FAILED\n");
    }
    state = CONNECTED;

    /* do { */
    /*     socket_recv(msg_buf, IMPORT_BUF_LEN) */

}

DPI_DLLESPEC int xsimintf_wait(void)
{
    cur_time += 5;
    return 5;
}

DPI_DLLESPEC const char* xsimintf_import(void)
{
    int clk;

    if ((cur_time / 5) % 2) {
        clk = 1;
    } else {
        clk = 0;
    }

    sprintf(msg_buf, "%d", clk);
    if (fp != NULL) {
        fprintf(fp, "XSIMINTF IMPORT: %s\n", msg_buf);
    }

    return msg_buf;
}

DPI_DLLESPEC void xsimintf_export(const char * vals)
{
    if (fp != NULL) {
        fprintf(fp, "XSIMINTF EXPORT: %s\n", vals);
    }
}

void main(void)
{
	strcpy(msg_buf, "$GET,1");
	msg_buf_cnt = strlen(msg_buf);
	decode_command();
}

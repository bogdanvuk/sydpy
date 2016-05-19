#include <svdpi.h>
#include <stdio.h>
#include "xsimintf_socket.h"

#define XSIM_DPI_DBG 0

#define IMPORT_BUF_LEN 65536
#define EXPORT_BUF_LEN 65536
#define MSG_BUF_LEN 65536
#define MAX_PARAMS 128
#define MAX_PARAM_LEN 1024

#ifdef CYTHON_XSIMINTF_DBG
void cython_get_new_message(void);
void cython_post_new_message(void);
void cython_print(const char* str);
char cython_print_buf[1024];
#endif

FILE *fp = NULL;
int cur_time = 0;
char msg_buf[MSG_BUF_LEN] = "";
char import_buf[IMPORT_BUF_LEN] = "";
char export_buf[EXPORT_BUF_LEN] = "";
int msg_buf_cnt = 0;

enum state_type {S_STARTED, S_CONNECTED, S_INITIALIZED, S_IMPORT, S_EXPORT, S_DELAY, S_ERROR};
enum state_type state;
enum command_type { CMD_GET, CMD_SET, CMD_IMPORT, CMD_EXPORT, CMD_ERROR, CMD_CONTINUE, CMD_RESP, CMD_CLOSE, NUMBER_OF_COMMAND_TYPES };

int delay;
int finish;

const char *command_names[NUMBER_OF_COMMAND_TYPES] = {
    "$GET", "$SET", "$IMPORT", "$EXPORT", "$ERROR", "$CONTINUE", "$RESP", "$CLOSE"
};

typedef struct {
    enum command_type cmd;
    char params[MAX_PARAMS][MAX_PARAM_LEN];
    int param_cnt;
} T_Command;

T_Command recv_cmd;
T_Command send_cmd;

static int get_new_message(void) {
#ifdef CYTHON_XSIMINTF_DBG
    cython_get_new_message();
#else
    //    msg_buf_cnt = 0;
    //while (msg_buf_cnt == 0) {
     msg_buf_cnt = socket_recv(msg_buf, IMPORT_BUF_LEN);
        // }

    msg_buf[msg_buf_cnt] = 0;
#endif
    return msg_buf_cnt;
}

static int decode_command(void) {
    char *token;
    int token_cnt = 0;
    int i;

    if (msg_buf_cnt > 0) {
        recv_cmd.cmd = CMD_ERROR;
        recv_cmd.param_cnt = 0;

        token = strtok (msg_buf,",");

        while (token != NULL)
        {
            if (token_cnt == 0) {
                for(i = 0; i < NUMBER_OF_COMMAND_TYPES; ++i)
                {
                    if(!strcmp(command_names[i], token))
                    {
                        recv_cmd.cmd = i;
                        break;
                    }
                }
            } else {
                /* cython_print(token); */
                /* sprintf(cython_print_buf, "Token ID: %d", token_cnt); */
                /* cython_print(cython_print_buf); */
                strncpy(recv_cmd.params[token_cnt-1], token, MAX_PARAM_LEN);

            }
            token_cnt++;
            token = strtok (NULL, ",");
        }

        recv_cmd.param_cnt = token_cnt - 1;

        msg_buf[0] = 0;
        msg_buf_cnt = 0;
        return recv_cmd.cmd;
    }

    return -1;
}

static int recv_command(void) {
    get_new_message();
#if XSIM_DPI_DBG == 1
    puts("*** RECV ***");
    puts(msg_buf);
#endif
    return decode_command();
}

static int send_msg() {
#ifdef CYTHON_XSIMINTF_DBG
    cython_post_new_message();
#else
#if XSIM_DPI_DBG == 1
    puts("*** SEND ***");
    puts(msg_buf);
#endif
    socket_send(msg_buf);
#endif
}

static int send_command(void) {
    int length = 0;
    int i;

    length += sprintf(msg_buf+length, "%s", command_names[send_cmd.cmd]);
    for (i = 0; i < send_cmd.param_cnt; i ++) {
        length += sprintf(msg_buf+length, "%s", ",");
        length += sprintf(msg_buf+length, "%s", send_cmd.params[i]);
    }
    send_msg();
}

void cmd_handler(void) {
    int length = 0;
    int i;

    recv_cmd.cmd = CMD_ERROR;
#if XSIM_DPI_DBG == 1
    puts("entered cmd handler");
#endif
    while ((recv_cmd.cmd != CMD_CONTINUE) && (finish == 0)) {
        //        puts("cmd handler entered loop...");
        if (recv_command() < 0) {
            finish = 1;
        } else {

            switch(recv_cmd.cmd) {

            case CMD_GET:
                send_cmd.cmd = CMD_RESP;
                send_cmd.param_cnt = recv_cmd.param_cnt;

                for (i = 0; i < recv_cmd.param_cnt; i++) {
                    if(!strcmp("state", recv_cmd.params[i])) {
                        sprintf(send_cmd.params[i], "%d", state);
                    } else if(!strcmp("delay", recv_cmd.params[i])) {
                        sprintf(send_cmd.params[i], "%d", delay);
                    } else {
                        send_cmd.cmd = CMD_ERROR;
                        send_cmd.param_cnt = 0;
                        break;
                    }
                }
                send_command();
                break;
            case CMD_SET:
                send_cmd.cmd = CMD_RESP;
                send_cmd.param_cnt = 0;

                for (i = 0; i < recv_cmd.param_cnt; i+=2) {
                    if(!strcmp("state", recv_cmd.params[i])) {
                        sscanf(recv_cmd.params[i+1], "%d", &state);
                    } else if(!strcmp("delay", recv_cmd.params[i])) {
                        sscanf(recv_cmd.params[i+1], "%d", &delay);
                    } else {
                        send_cmd.cmd = CMD_ERROR;
                        send_cmd.param_cnt = 0;
                        break;
                    }
                }
                send_command();
                break;
            case CMD_EXPORT:
                sprintf(msg_buf, "$EXPORT,%s", export_buf);
                send_msg();
                break;
            case CMD_IMPORT:
                import_buf[0] = 0;
                for (length=0,i = 0; i < recv_cmd.param_cnt; i ++) {
                    if (length > 0)
                        length += sprintf(import_buf+length, "%s", ",");

                    length += sprintf(import_buf+length, "%s", recv_cmd.params[i]);
                }
                send_cmd.cmd = CMD_RESP;
                send_cmd.param_cnt = 0;
                send_command();
                break;
            case CMD_CONTINUE:
                send_cmd.cmd = CMD_RESP;
                send_cmd.param_cnt = 0;
                send_command();
#if XSIM_DPI_DBG == 1
                puts("continuing...");
#endif
                break;
            case CMD_CLOSE:
                finish = 1;
                break;
            default:
                break;
            }
        }

    }

#ifndef CYTHON_XSIMINTF_DBG
    if (finish) {
        socket_close();
        fclose(fp);
    }
#endif
#if XSIM_DPI_DBG == 1
    puts("exiting cmd handler");
#endif
}

DPI_DLLESPEC int xsimintf_init(void)
{
    finish = 0;
    state = S_STARTED;
#ifndef CYTHON_XSIMINTF_DBG
    fp = fopen("xsimintf.log", "w");
    if (fp != NULL) {
        fprintf(fp, "XSIMINTF INITIALIZED\n");
    }
    if (socket_open() == 0) {
        fprintf(fp, "SOCKET OPENED\n");
    } else {
        fprintf(fp, "SOCKET OPEN FAILED\n");
        return 1;
    }
#endif
    state = S_CONNECTED;
#if XSIM_DPI_DBG == 1
    puts("To cmd handler from xsimintf_init");
#endif
    cmd_handler();
    return 0;
}

DPI_DLLESPEC int xsimintf_delay(void)
{
    state = S_DELAY;
#if XSIM_DPI_DBG == 1
    puts("To cmd handler from xsimintf_delay");
#endif
    cmd_handler();

    if (finish) {
        return -1;
    } else {
        return delay;
    }
}

DPI_DLLESPEC const char* xsimintf_export(const char * vals)
{
    strcpy(export_buf, vals);
    state = S_EXPORT;
    //    puts(export_buf);
#if XSIM_DPI_DBG == 1
    puts("To cmd handler from xsimintf_export");
#endif
    import_buf[0] = 0;
    cmd_handler();
    return import_buf;
}

DPI_DLLESPEC const char* xsimintf_import()
{
    state = S_IMPORT;
#if XSIM_DPI_DBG == 1
    puts("To cmd handler from xsimintf_import");
#endif
    import_buf[0] = 0;
    cmd_handler();
    return import_buf;
}

void main(void)
{
	strcpy(msg_buf, "$GET,1");
	msg_buf_cnt = strlen(msg_buf);
	decode_command();
}

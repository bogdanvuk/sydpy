#include <svdpi.h>
#include <stdio.h>
#include "xsimintf_socket.h"

FILE *fp = NULL;
int cur_time = 0;
char import_buf[1024] = "";

DPI_DLLESPEC void xsimintf_init()
{
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
}

DPI_DLLESPEC int xsimintf_wait()
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

    sprintf(import_buf, "%d", clk);
    if (fp != NULL) {
        fprintf(fp, "XSIMINTF IMPORT: %s\n", import_buf);
    }

    return import_buf;
}

DPI_DLLESPEC void xsimintf_export(const char * vals)
{
    if (fp != NULL) {
        fprintf(fp, "XSIMINTF EXPORT: %s\n", vals);
    }
}

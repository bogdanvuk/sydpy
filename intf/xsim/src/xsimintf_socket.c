#include<stdio.h> //printf
#include<string.h>    //strlen
#include<sys/socket.h>    //socket
#include<arpa/inet.h> //inet_addr

int sock;

int socket_open()
{
    struct sockaddr_in server;
    char message[1000] , server_reply[2000];
    int so_reuseaddr = 1;
    struct timeval tv;

    //Create socket
    sock = socket(AF_INET , SOCK_STREAM , 0);
    if (sock == -1)
    {
        printf("Could not create socket");
    }
    puts("Socket created");

    setsockopt(sock,SOL_SOCKET,SO_REUSEADDR, &so_reuseaddr, sizeof so_reuseaddr);


    /* tv.tv_sec = 10;  /\* 10 Secs Timeout *\/ */
    /* tv.tv_usec = 0;  // Not init'ing this can cause strange errors */

    /* setsockopt(sock, SOL_SOCKET, SO_RCVTIMEO, (char *)&tv,sizeof(struct timeval)); */

    server.sin_addr.s_addr = inet_addr("127.0.0.1");
    server.sin_family = AF_INET;
    server.sin_port = htons( 60000 );

    //Connect to remote server
    if (connect(sock , (struct sockaddr *)&server , sizeof(server)) < 0)
    {
        perror("connect failed. Error");
        return 1;
    }

    return 0;
}

int socket_send(const char* msg)
{
    //Send some data
    if( send(sock , msg , strlen(msg) , 0) < 0)
    {
        return 1;
    }

    return 0;
}

int socket_recv(char* msg, int max_len)
{
    return recv(sock , msg , max_len, 0);
}

int socket_close()
{
    close(sock);
}

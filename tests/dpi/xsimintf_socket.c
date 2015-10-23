#include<stdio.h> //printf
#include<string.h>    //strlen
#include<sys/socket.h>    //socket
#include<arpa/inet.h> //inet_addr

int sock;

int socket_open()
{
    struct sockaddr_in server;
    char message[1000] , server_reply[2000];

    //Create socket
    sock = socket(AF_INET , SOCK_STREAM , 0);
    if (sock == -1)
    {
        printf("Could not create socket");
    }
    puts("Socket created");

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
    //Receive a reply from the server
    if( recv(sock , msg , max_len, 0) < 0)
    {
        return 1;
    }

    return 0;
}

int socket_close()
{
    close(sock);
}

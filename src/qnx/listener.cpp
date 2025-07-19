#include <iostream>
#include <cstring>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>

int main() {
    std::cout << "Starting listener..." << std::endl;
    const int PORT = 23456;
    int server_fd, client_fd;
    struct sockaddr_in address;
    int addrlen = sizeof(address);

    // Create socket
    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        perror("socket failed");
        return 1;
    }

    // Bind
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);

    if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
        perror("bind failed");
        return 1;
    }

    // Listen
    if (listen(server_fd, 1) < 0) {
        perror("listen failed");
        return 1;
    }

    std::cout << "Listening on port " << PORT << "...\n";
    fflush(stdout);

    // Accept
    if ((client_fd = accept(server_fd, (struct sockaddr *)&address, (socklen_t*)&addrlen)) < 0) {
        perror("accept failed");
        return 1;
    }

    std::cout << "Client connected!\n";
    fflush(stdout);

    // Read loop
    while (true) {
        float values[4];
        ssize_t bytes_read = recv(client_fd, values, sizeof(values), MSG_WAITALL);
        if (bytes_read <= 0) break;

        std::cout << "Time: " << values[0]
                  << "  Pack Voltage: " << values[1]
                  << "  Pack Current: " << values[2]
                  << "  Cell Temp: " << values[3] << std::endl;
    }

    close(client_fd);
    close(server_fd);
    return 0;
}
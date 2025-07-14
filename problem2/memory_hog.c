#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h> // For sleep

#define MB (1024 * 1024)

int main(int argc, char *argv[]) {
    int limit_mb = (argc > 1) ? atoi(argv[1]) : 15; 
    char *data_ptr;
    int current_mb = 0;

    printf("Attempting to allocate up to %d MB...\n", limit_mb);

    while (current_mb < limit_mb) {
        data_ptr = (char *)malloc(MB);
        if (data_ptr == NULL) {
            perror("malloc failed");
            printf("Memory limit likely reached or allocation failed.\n");
            return 1;
        }

        memset(data_ptr, 'A', MB);

        current_mb++;
        printf("Allocated %d MB\n", current_mb);
        sleep(1); 
    }

    printf("Finished allocation attempt.\n");
    sleep(300);

    return 0;
}
// SPDX-License-Identifier: MIT
// Small, dependency-free executable exercised by test_v102_watcher_ownership.py.
#include "watcher_process_identity.h"
#include <stdio.h>

int main(int argc, char **argv)
{
    if (argc < 3) return 2;
    if (strcmp(argv[1], "read") == 0 && argc == 3) {
        pid_t pid = 0;
        if (!ascii_saver_read_pid(argv[2], &pid)) return 1;
        printf("%ld\n", (long)pid);
        return 0;
    }
    if (strcmp(argv[1], "renderer") == 0 && argc == 4)
        return ascii_saver_pid_is_renderer((pid_t)atol(argv[2]), argv[3]) ? 0 : 1;
    if (strcmp(argv[1], "watcher") == 0 && argc == 3)
        return ascii_saver_pid_is_watcher((pid_t)atol(argv[2])) ? 0 : 1;
    if (strcmp(argv[1], "hold") == 0 && argc == 3) {
        // Runs as the same compiled executable, for /proc/PID/exe identity.
        sleep(30);
        return 0;
    }
    return 2;
}

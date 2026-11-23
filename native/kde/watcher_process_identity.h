// SPDX-License-Identifier: MIT
// Linux-native, GTK/Qt-free process identity checks shared by the idle watchers.
// PID files are hints, never proof that an arbitrary process is ASCII Saver.
#ifndef ASCII_SAVER_WATCHER_PROCESS_IDENTITY_H
#define ASCII_SAVER_WATCHER_PROCESS_IDENTITY_H

#include <errno.h>
#include <fcntl.h>
#include <limits.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

#ifndef O_CLOEXEC
#define O_CLOEXEC 0
#endif
#ifndef O_NOFOLLOW
#define O_NOFOLLOW 0
#endif

// Read a short, decimal PID from a regular, non-symlinked runtime file.
static inline bool ascii_saver_read_pid(const char *path, pid_t *out)
{
    if (!path || !out) return false;
    int fd = open(path, O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
    if (fd < 0) return false;
    struct stat info;
    char data[64];
    const bool regular = fstat(fd, &info) == 0 && S_ISREG(info.st_mode);
    const ssize_t count = regular ? read(fd, data, sizeof(data)) : -1;
    close(fd);
    if (count < 1 || count >= (ssize_t)sizeof(data) || data[0] < '0' || data[0] > '9')
        return false;
    data[count] = '\0';
    char *end = NULL;
    errno = 0;
    const long value = strtol(data, &end, 10);
    if (errno || value <= 0 || value > INT_MAX || !end || (*end && strcmp(end, "\n")))
        return false;
    *out = (pid_t)value;
    return true;
}

static inline bool ascii_saver_same_user_process(pid_t pid)
{
    if (pid <= 0) return false;
    char path[64];
    if (snprintf(path, sizeof(path), "/proc/%ld", (long)pid) >= (int)sizeof(path))
        return false;
    struct stat info;
    return stat(path, &info) == 0 && info.st_uid == getuid();
}

// Supported launchers invoke Python with the absolute app.py path in argv[1].
// Exact argument boundaries prevent substring false positives from other apps.
static inline bool ascii_saver_pid_is_renderer(pid_t pid, const char *script)
{
    if (!script || script[0] != '/' || !ascii_saver_same_user_process(pid)) return false;
    char proc[80];
    if (snprintf(proc, sizeof(proc), "/proc/%ld/cmdline", (long)pid) >= (int)sizeof(proc))
        return false;
    int fd = open(proc, O_RDONLY | O_CLOEXEC);
    if (fd < 0) return false;
    char args[65536];
    const ssize_t count = read(fd, args, sizeof(args));
    close(fd);
    if (count < 3 || count >= (ssize_t)sizeof(args)) return false;
    const char *end0 = (const char *)memchr(args, '\0', (size_t)count);
    if (!end0) return false;
    const char *arg1 = end0 + 1;
    if (arg1 >= args + count) return false;
    const char *end1 = (const char *)memchr(arg1, '\0', (size_t)(args + count - arg1));
    return end1 && (size_t)(end1 - arg1) == strlen(script)
        && memcmp(arg1, script, strlen(script)) == 0;
}

// Detect a live native watcher from /proc/PID/exe, including an executable
// replaced on disk while an old watcher instance was still running.
static inline bool ascii_saver_pid_is_watcher(pid_t pid)
{
    if (!ascii_saver_same_user_process(pid)) return false;
    char path[80], self[4096], other[4096 + 16];
    if (snprintf(path, sizeof(path), "/proc/%ld/exe", (long)pid) >= (int)sizeof(path))
        return false;
    const ssize_t slen = readlink("/proc/self/exe", self, sizeof(self) - 1);
    const ssize_t plen = readlink(path, other, sizeof(other) - 1);
    if (slen <= 0 || plen <= 0) return false;
    self[slen] = '\0';
    other[plen] = '\0';
    const char deleted[] = " (deleted)";
    return strcmp(self, other) == 0
        || ((size_t)plen == (size_t)slen + sizeof(deleted) - 1
            && memcmp(self, other, (size_t)slen) == 0
            && strcmp(other + slen, deleted) == 0);
}

#endif // ASCII_SAVER_WATCHER_PROCESS_IDENTITY_H

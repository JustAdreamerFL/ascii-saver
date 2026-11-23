// SPDX-License-Identifier: MIT
// GNOME/Mutter native idle watcher; KDE uses the existing Qt/KIdleTime watcher.
// Event-driven idle handling, with a low-frequency configuration/inhibitor check.
#include <gio/gio.h>
#include "watcher_process_identity.h"
#include <glib-unix.h>
#include <glib/gstdio.h>
#include <json-glib/json-glib.h>
#include <signal.h>
#include <sys/file.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
#include <string.h>
#include <sys/types.h>

#ifndef ASCII_SAVER_VERSION
#define ASCII_SAVER_VERSION "unknown"
#endif

#define IDLE_BUS "org.gnome.Mutter.IdleMonitor"
#define IDLE_PATH "/org/gnome/Mutter/IdleMonitor/Core"
#define IDLE_IFACE "org.gnome.Mutter.IdleMonitor"

// IDLE inhibitor bit from GNOME SessionManager's InhibitFlags.
#define GNOME_IDLE_INHIBITOR 8u

typedef struct {
    GMainLoop *loop;
    GDBusProxy *idle;
    gulong idle_signal;
    gchar *app_dir;
    gchar *config_path;
    gchar *pid_path;
    gchar *renderer_pid_path;
    int pid_fd;  // Advisory lock remains held for the whole service lifetime.
    GSubprocess *renderer;
    guint stop_timeout;
    guint idle_watch;
    guint active_watch;
    guint poll_id;
    gboolean enabled;
    gboolean respect_inhibitors;
    gboolean deferred;
    gboolean waiting_initial_resume;
    guint idle_delay;
} Watcher;

static GVariant *idle_call(Watcher *w, const gchar *name, GVariant *params) {
    GError *error = NULL;
    GVariant *result = g_dbus_proxy_call_sync(w->idle, name, params,
                              G_DBUS_CALL_FLAGS_NONE, 1500, NULL, &error);
    if (!result) {
        g_warning("Mutter %s failed: %s", name, error->message);
        g_clear_error(&error);
    }
    return result;
}

static void remove_watch(Watcher *w, guint *watch) {
    if (!*watch) return;
    GVariant *res = idle_call(w, "RemoveWatch", g_variant_new("(u)", *watch));
    if (res) g_variant_unref(res);
    *watch = 0;
}

static guint add_watch(Watcher *w, const gchar *method, GVariant *args) {
    GVariant *result = idle_call(w, method, args);
    guint id = 0;
    if (result) {
        g_variant_get(result, "(u)", &id);
        g_variant_unref(result);
    }
    return id;
}

static gboolean bus_boolean(const gchar *destination, const gchar *path,
                             const gchar *interface, const gchar *method, GVariant *params) {
    GError *error = NULL;
    GDBusConnection *conn = g_bus_get_sync(G_BUS_TYPE_SESSION, NULL, &error);
    if (!conn) {
        g_clear_error(&error);
        return FALSE;
    }
    GVariant *out = g_dbus_connection_call_sync(conn, destination, path,
                        interface, method, params, G_VARIANT_TYPE("(b)"),
                        G_DBUS_CALL_FLAGS_NO_AUTO_START, 500, NULL, &error);
    g_object_unref(conn);
    if (!out) {
        g_clear_error(&error);
        return FALSE;
    }
    gboolean value = FALSE;
    g_variant_get(out, "(b)", &value);
    g_variant_unref(out);
    return value;
}

static gboolean session_locked(void) {
    return bus_boolean("org.gnome.ScreenSaver", "/org/gnome/ScreenSaver",
                       "org.gnome.ScreenSaver", "GetActive", NULL);
}

static gboolean session_inhibited(const Watcher *w) {
    return w->respect_inhibitors &&
        bus_boolean("org.gnome.SessionManager", "/org/gnome/SessionManager",
                    "org.gnome.SessionManager", "IsInhibited",
                    g_variant_new("(u)", GNOME_IDLE_INHIBITOR));
}

static void arm_active(Watcher *w) {
    if (!w->active_watch)
        w->active_watch = add_watch(w, "AddUserActiveWatch", g_variant_new("()"));
}

static void arm_idle(Watcher *w) {
    remove_watch(w, &w->idle_watch);
    if (w->enabled && !w->waiting_initial_resume)
        w->idle_watch = add_watch(w, "AddIdleWatch",
                          g_variant_new("(t)", (guint64) w->idle_delay * 1000));
}

static gboolean is_renderer_running(const Watcher *w) {
    pid_t pid = 0;
    if (!ascii_saver_read_pid(w->renderer_pid_path, &pid)) return FALSE;
    g_autofree gchar *script = g_build_filename(w->app_dir, "app.py", NULL);
    return ascii_saver_pid_is_renderer(pid, script);
}

static gboolean force_stop_cb(gpointer data) {
    Watcher *w = data;
    w->stop_timeout = 0;
    // A pending async wait owns the child status; don't query get_if_exited()
    // until wait_finish(), as doing so is invalid in GIO.
    if (w->renderer) g_subprocess_force_exit(w->renderer);
    return G_SOURCE_REMOVE;
}

static void stop_child(Watcher *w) {
    if (!w->renderer) return;
    g_subprocess_send_signal(w->renderer, SIGTERM);
    if (!w->stop_timeout)
        w->stop_timeout = g_timeout_add_seconds(2, force_stop_cb, w);
}

static void child_exited(GObject *obj, GAsyncResult *result, gpointer data) {
    Watcher *w = data;
    GError *error = NULL;
    g_subprocess_wait_finish(G_SUBPROCESS(obj), result, &error);
    if (error) {
        g_warning("Renderer wait failed: %s", error->message);
        g_clear_error(&error);
    }
    if (w->stop_timeout) {
        g_source_remove(w->stop_timeout);
        w->stop_timeout = 0;
    }
    if (w->renderer == G_SUBPROCESS(obj)) g_clear_object(&w->renderer);
}

static void start_child(Watcher *w) {
    if (w->renderer || is_renderer_running(w) || !w->enabled || session_locked()) return;
    if (session_inhibited(w)) {
        w->deferred = TRUE;
        return;
    }
    w->deferred = FALSE;
    gchar *venv_python = g_build_filename(w->app_dir, "venv", "bin", "python", NULL);
    gchar *python = g_file_test(venv_python, G_FILE_TEST_IS_EXECUTABLE)
                       ? g_strdup(venv_python)
                       : g_find_program_in_path("python3");
    g_free(venv_python);
    if (!python) python = g_strdup("python3");
    gchar *script = g_build_filename(w->app_dir, "app.py", NULL);
    GSubprocessLauncher *launcher = g_subprocess_launcher_new(G_SUBPROCESS_FLAGS_STDOUT_SILENCE);
    /* A systemd user manager may not propagate XDG_CURRENT_DESKTOP. */
    g_subprocess_launcher_setenv(launcher, "ASCII_SAVER_BACKEND", "gnome", TRUE);
    GError *error = NULL;
    w->renderer = g_subprocess_launcher_spawn(launcher, &error, python, script, NULL);
    if (!w->renderer) {
        g_warning("Unable to start screensaver: %s", error->message);
        g_clear_error(&error);
    } else {
        g_subprocess_wait_async(w->renderer, NULL, child_exited, w);
    }
    g_object_unref(launcher);
    g_free(script);
    g_free(python);
}

static void fired(GDBusProxy *proxy, const gchar *sender, const gchar *signal,
                  GVariant *arguments, gpointer data) {
    (void)proxy; (void)sender;
    Watcher *w = data;
    if (g_strcmp0(signal, "WatchFired")) return;
    guint id = 0;
    g_variant_get(arguments, "(u)", &id);
    if (id && id == w->idle_watch) {
        remove_watch(w, &w->idle_watch);
        arm_active(w);
        start_child(w);
    } else if (id && id == w->active_watch) {
        // Mutter's active watch is one-shot. Keep the local ID in sync.
        w->active_watch = 0;
        stop_child(w);
        w->deferred = FALSE;
        w->waiting_initial_resume = FALSE;
        arm_idle(w);
    }
}

static void read_config(Watcher *w) {
    gchar *contents = NULL;
    if (!g_file_get_contents(w->config_path, &contents, NULL, NULL)) return;
    JsonParser *parser = json_parser_new();
    GError *error = NULL;
    if (!json_parser_load_from_data(parser, contents, -1, &error)) {
        g_clear_error(&error);
        g_object_unref(parser);
        g_free(contents);
        return;
    }
    g_free(contents);
    JsonNode *root = json_parser_get_root(parser);
    if (!JSON_NODE_HOLDS_OBJECT(root)) { g_object_unref(parser); return; }
    JsonObject *cfg = json_node_get_object(root);
    gboolean enabled = !json_object_has_member(cfg, "enabled") ||
                          json_object_get_boolean_member_with_default(cfg, "enabled", TRUE);
    gboolean respect = !json_object_has_member(cfg, "respect_inhibitors") ||
                          json_object_get_boolean_member_with_default(cfg, "respect_inhibitors", TRUE);
    gint64 delay = json_object_get_int_member_with_default(cfg, "idle_delay", 120);
    delay = CLAMP(delay, 10, 86400);
    gboolean changed = w->enabled != enabled || w->respect_inhibitors != respect || w->idle_delay != (guint)delay;
    w->enabled = enabled;
    w->respect_inhibitors = respect;
    w->idle_delay = (guint) delay;
    g_object_unref(parser);
    if (!enabled) {
        w->deferred = FALSE;
        stop_child(w);
    }
    // Don't re-arm an idle watch while waiting for an active event: Mutter
    // could immediately fire it again if the user is still idle.
    if (changed && !w->active_watch) arm_idle(w);
}

static gboolean poll_state(gpointer data) {
    Watcher *w = data;
    g_autofree gchar *owner = g_dbus_proxy_get_name_owner(w->idle);
    if (!owner) {
        g_warning("Mutter IdleMonitor disappeared; restarting service");
        g_main_loop_quit(w->loop);
        return G_SOURCE_REMOVE;
    }
    read_config(w);
    if (!w->enabled || session_locked() || (w->renderer && session_inhibited(w))) {
        stop_child(w);
    } else if (w->deferred && !session_inhibited(w)) {
        start_child(w);
    }
    return G_SOURCE_CONTINUE;
}

static gboolean quit_watcher(gpointer data) {
    Watcher *w = data;
    g_main_loop_quit(w->loop);
    return G_SOURCE_REMOVE;
}

// Lock the PID file's inode before replacing its contents. This avoids a
// stale PID (possibly reused by an unrelated process) blocking startup,
// while preventing two new instances from claiming the same runtime file.
static gboolean write_pid(Watcher *w) {
    int fd = g_open(w->pid_path, O_CREAT | O_RDWR | O_CLOEXEC | O_NOFOLLOW, 0600);
    if (fd < 0) return FALSE;
    struct stat info;
    if (fstat(fd, &info) != 0 || !S_ISREG(info.st_mode)
        || info.st_uid != getuid() || flock(fd, LOCK_EX | LOCK_NB) != 0) {
        close(fd);
        return FALSE;
    }
    // Older installations used O_EXCL but did not hold a lock; refuse to
    // overwrite a genuinely live older watcher. A reused unrelated PID is
    // not evidence of a watcher and may be safely replaced.
    pid_t old_pid = 0;
    if (ascii_saver_read_pid(w->pid_path, &old_pid)
        && old_pid != getpid() && ascii_saver_pid_is_watcher(old_pid)) {
        close(fd);
        return FALSE;
    }
    gchar text[64];
    int length = g_snprintf(text, sizeof(text), "%ld\n", (long)getpid());
    if (length <= 0 || length >= (int)sizeof(text)
        || ftruncate(fd, 0) != 0 || lseek(fd, 0, SEEK_SET) == (off_t)-1
        || write(fd, text, (size_t)length) != length) {
        close(fd);
        return FALSE;
    }
    w->pid_fd = fd;
    return TRUE;
}

static void release_pid(Watcher *w) {
    if (w->pid_fd < 0) return;
    // Only unlink the inode we locked and only when it still names us.
    struct stat held, path_info;
    pid_t written_pid = 0;
    if (fstat(w->pid_fd, &held) == 0 && stat(w->pid_path, &path_info) == 0
        && held.st_dev == path_info.st_dev && held.st_ino == path_info.st_ino
        && ascii_saver_read_pid(w->pid_path, &written_pid)
        && written_pid == getpid()) {
        g_unlink(w->pid_path);
    }
    close(w->pid_fd);
    w->pid_fd = -1;
}

int main(int argc, char **argv) {
    if (argc == 2 && g_strcmp0(argv[1], "--version") == 0) {
        g_print("ASCII Saver GNOME watcher %s\n", ASCII_SAVER_VERSION);
        return 0;
    }
    Watcher w = {0};
    w.pid_fd = -1;
    const gchar *runtime = g_getenv("XDG_RUNTIME_DIR");
    if (!runtime || !*runtime) {
        g_printerr("GNOME watcher requires XDG_RUNTIME_DIR\n");
        return 1;
    }
    const gchar *configured_app_dir = g_getenv("ASCII_SAVER_APP_DIR");
    if (configured_app_dir && *configured_app_dir) {
        w.app_dir = g_strdup(configured_app_dir);
    } else {
        // The dev installer places this binary inside the application data directory.
        gchar *self = g_file_read_link("/proc/self/exe", NULL);
        if (!self) return 1;
        w.app_dir = g_path_get_dirname(self);
        g_free(self);
    }
    w.config_path = g_build_filename(g_get_user_config_dir(), "ascii-saver", "config.json", NULL);
    w.pid_path = g_strdup_printf("%s/ascii-saver-watcher-%u.pid", runtime, (guint)getuid());
    w.renderer_pid_path = g_strdup_printf("%s/ascii-saver-%u.pid", runtime, (guint)getuid());
    w.loop = g_main_loop_new(NULL, FALSE);
    w.enabled = TRUE;
    w.respect_inhibitors = TRUE;
    w.idle_delay = 120;
    w.waiting_initial_resume = TRUE;

    GError *error = NULL;
    w.idle = g_dbus_proxy_new_for_bus_sync(G_BUS_TYPE_SESSION,
                  G_DBUS_PROXY_FLAGS_DO_NOT_AUTO_START,
                  NULL, IDLE_BUS, IDLE_PATH, IDLE_IFACE, NULL, &error);
    g_autofree gchar *initial_owner = w.idle ? g_dbus_proxy_get_name_owner(w.idle) : NULL;
    if (!w.idle || !initial_owner) {
        g_printerr("GNOME Mutter IdleMonitor unavailable: %s\n",
                    error ? error->message : "service has no owner");
        g_clear_error(&error);
        return 1;
    }
    if (!write_pid(&w)) {
        g_printerr("GNOME watcher already running or PID file not writable: %s\n", w.pid_path);
        return 1;
    }
    w.idle_signal = g_signal_connect(w.idle, "g-signal", G_CALLBACK(fired), &w);
    read_config(&w);
    // GNOME's idle watch can fire immediately for an already-idle session.
    // Only arm after a fresh input event in that case.
    GVariant *elapsed = idle_call(&w, "GetIdletime", NULL);
    guint64 idle_ms = 0;
    if (elapsed) {
        g_variant_get(elapsed, "(t)", &idle_ms);
        g_variant_unref(elapsed);
    }
    if (idle_ms < (guint64)w.idle_delay * 1000) {
        w.waiting_initial_resume = FALSE;
        arm_idle(&w);
    } else {
        arm_active(&w);
    }
    w.poll_id = g_timeout_add_seconds(1, poll_state, &w);
    g_unix_signal_add(SIGTERM, quit_watcher, &w);
    g_unix_signal_add(SIGINT, quit_watcher, &w);
    g_main_loop_run(w.loop);

    if (w.poll_id) g_source_remove(w.poll_id);
    remove_watch(&w, &w.idle_watch);
    remove_watch(&w, &w.active_watch);
    stop_child(&w);
    // Give the child an opportunity to finish and be reaped before exiting.
    if (w.renderer) {
        // A closing service cannot block forever on an unresponsive renderer.
        g_subprocess_force_exit(w.renderer);
        g_subprocess_wait(w.renderer, NULL, NULL);
        g_clear_object(&w.renderer);
    }
    if (w.stop_timeout) g_source_remove(w.stop_timeout);
    release_pid(&w);
    g_main_loop_unref(w.loop);
    g_clear_object(&w.idle);
    g_free(w.app_dir);
    g_free(w.config_path);
    g_free(w.pid_path);
    g_free(w.renderer_pid_path);
    return 0;
}

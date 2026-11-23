// KDE Plasma 6 KWin script. Sends only a boolean, never titles or app names.
function report() {
    const win = workspace.activeWindow;
    const fullscreen = !!(win && win.fullScreen && !win.minimized);
    callDBus("org.kde.AsciiSaver.Activity", "/Activity",
             "org.kde.AsciiSaver.Activity", "SetFullscreenActive", fullscreen);
}
function watch(win) {
    if (!win) return;
    if (win.fullScreenChanged) win.fullScreenChanged.connect(report);
    if (win.minimizedChanged) win.minimizedChanged.connect(report);
}
workspace.windowList().forEach(watch);
workspace.windowAdded.connect(function(win) { watch(win); report(); });
workspace.windowActivated.connect(report);
workspace.windowRemoved.connect(report);
report();

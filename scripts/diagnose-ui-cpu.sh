#!/usr/bin/env bash
# Investigate high idle CPU without guessing which process is responsible.
# Run while the GUI is open but no preview/screensaver is playing.
set -euo pipefail
printf '\n=== ASCII Saver, Rust ttfx and image loader processes ===\n'
ps -eo pid,ppid,pcpu,rss,comm,args --sort=-pcpu | awk 'NR==1 || /[k]de-ascii-saver|[t]tfx|[g]lycin|[s]ettings\.py|[p]laylist_editor\.py/'
printf '\n=== Thread-level CPU for settings UI (when present) ===\n'
mapfile -t pids < <(pgrep -f '/ascii-saver/(settings|settings.py)|ascii-saver-settings' || true)
for pid in "${pids[@]}"; do
  [[ -d "/proc/$pid" ]] || continue
  ps -L -p "$pid" -o pid,tid,pcpu,rss,comm --sort=-pcpu || true
done

printf '\n=== Watcher memory (RSS vs PSS vs private) ===\n'
while read -r pid; do
  [[ -r "/proc/$pid/smaps_rollup" ]] || continue
  printf 'Watcher PID %s: ' "$pid"
  awk '/^(Rss|Pss|Private_Clean|Private_Dirty):/ {printf "%s %s KiB; ", $1, $2} END {print ""}' "/proc/$pid/smaps_rollup"
done < <(pgrep -f '[/]ascii-saver-watcher($| )' || true)

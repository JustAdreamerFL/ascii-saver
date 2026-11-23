//! Opt-in frame-output telemetry; counts writes, not KWin presentation.
use std::sync::{Mutex, OnceLock};
use std::time::Instant;

#[derive(Default)]
struct State {
    count: u64,
    first: Option<Instant>,
    last: Option<Instant>,
}
static STATE: OnceLock<Mutex<State>> = OnceLock::new();
fn state() -> &'static Mutex<State> { STATE.get_or_init(|| Mutex::new(State::default())) }

pub fn reset() { *state().lock().unwrap_or_else(|e| e.into_inner()) = State::default(); }
pub fn frame_written() {
    let mut stats = state().lock().unwrap_or_else(|e| e.into_inner());
    let now = Instant::now();
    if stats.first.is_none() { stats.first = Some(now); }
    stats.last = Some(now);
    stats.count += 1;
}
pub fn frames() -> u64 { state().lock().unwrap_or_else(|e| e.into_inner()).count }

fn json_escape(s: &str) -> String {
    let mut out = String::new();
    for c in s.chars() {
        match c {
            '\\' => out.push_str("\\\\"),
            '"' => out.push_str("\\\""),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if c.is_control() => out.push(' '),
            c => out.push(c),
        }
    }
    out
}

/// Schema 2: `active_output_fps` measures frame intervals, excluding launch
/// and teardown. A single frame has no measurable interval so the value is null.
/// Neither FPS figure represents compositor-presented frames.
pub fn record(path: &std::path::Path, elapsed: f64, status: &str, effect: &str) -> std::io::Result<()> {
    let stats = state().lock().unwrap_or_else(|e| e.into_inner());
    let count = stats.count;
    let avg = if elapsed > 0.0 { count as f64 / elapsed } else { 0.0 };
    let active = match (stats.first, stats.last) {
        (Some(first), Some(last)) if count > 1 => {
            let seconds = last.duration_since(first).as_secs_f64();
            if seconds > 0.0 { format!("{:.6}", (count - 1) as f64 / seconds) } else { "null".into() }
        }
        _ => "null".into(),
    };
    let report = format!(
        "{{\"schema\":2,\"frames_written\":{count},\"elapsed_seconds\":{elapsed:.6},\"average_output_fps\":{avg:.6},\"active_output_fps\":{active},\"status\":\"{}\",\"effect\":\"{}\"}}\n",
        json_escape(status), json_escape(effect)
    );
    drop(stats);
    // Write into a sibling temporary file and rename to avoid partially parsed reports.
    let mut tmp = path.as_os_str().to_os_string();
    tmp.push(format!(".{}.tmp", std::process::id()));
    let tmp = std::path::PathBuf::from(tmp);
    std::fs::write(&tmp, report)?;
    if let Err(err) = std::fs::rename(&tmp, path) {
        let _ = std::fs::remove_file(&tmp);
        return Err(err);
    }
    Ok(())
}
#[cfg(test)] mod tests {
    use super::*;
    #[test] fn counters_and_reset() {
        reset(); frame_written(); frame_written(); assert_eq!(frames(), 2);
        reset(); assert_eq!(frames(), 0);
    }
    #[test] fn quote_escaping() {
        assert_eq!(json_escape("a\"b\\c"), "a\\\"b\\\\c");
    }
    #[test] fn one_frame_has_no_active_interval() {
        reset(); frame_written();
        let path = std::env::temp_dir().join(format!("ttfx-telemetry-test-{}", std::process::id()));
        record(&path, 1.0, "completed", "beams").unwrap();
        let json = std::fs::read_to_string(&path).unwrap();
        assert!(json.contains("\"active_output_fps\":null"));
        assert!(json.contains("\"schema\":2"));
        std::fs::remove_file(path).unwrap();
    }
}

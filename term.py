#!/usr/bin/env python3
"""
vt_server_improved.py

Minimal virtual terminal server (single-file) with:
- Improved ANSI parsing (strip SGR, skip OSC)
- Support for Delete key (ESC[3~)
- Simple Ctrl+Arrow (ESC[1;5D / ESC[1;5C) -> word moves
- Better backspace behavior
- Rendering avoids producing an extra scroll line
"""
import os
import pty
import tty
import sys
import fcntl
import termios
import select
import json
import queue
import threading
import signal
from collections import deque

# ---------------- utilities ----------------


def get_winsize(fd):
    import struct
    s = fcntl.ioctl(fd, termios.TIOCGWINSZ, b'\0'*8)
    rows, cols = struct.unpack('hhhh', s)[:2]
    return (rows or 24, cols or 80)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))

# ---------------- screen model ----------------


class VirtualScreen:
    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.buffer = deque([""] * rows, maxlen=rows)   # top..bottom
        self.cursor_row = 0
        self.cursor_col = 0
        # set so abs_top starts at 0 initially
        self.abs_next_line = rows
        self._saved = (0, 0)

    @property
    def abs_top(self):
        return self.abs_next_line - len(self.buffer)

    # put a printable character at the cursor (with wrapping)
    def put_char(self, ch):
        r, c = self.cursor_row, self.cursor_col
        line = self.buffer[r]
        if len(line) < c:
            line = line + (" " * (c - len(line)))
        # if cursor past cols: wrap
        if c >= self.cols:
            self._newline(scroll_if_needed=True)
            self.put_char(ch)
            return
        # insert/overwrite
        if c == len(line):
            line = line + ch
        else:
            line = line[:c] + ch + line[c+1:]
        # clip to width
        self.buffer[r] = line[:self.cols]
        # advance
        self.cursor_col += 1
        if self.cursor_col >= self.cols:
            self.cursor_col = 0
            self._newline(scroll_if_needed=True)

    # newline: if at bottom, scroll and increment absolute counter
    def _newline(self, scroll_if_needed=True):
        if self.cursor_row == self.rows - 1:
            self.buffer.append("")   # pushes out top
            self.abs_next_line += 1
            self.cursor_col = 0
        else:
            self.cursor_row += 1
            self.cursor_col = 0

    def carriage_return(self):
        self.cursor_col = 0

    # backspace: move left and delete previous char if present
    def backspace(self):
        if self.cursor_col > 0:
            self.cursor_col -= 1
            r = self.cursor_row
            line = self.buffer[r]
            if self.cursor_col < len(line):
                line = line[:self.cursor_col] + line[self.cursor_col+1:]
                self.buffer[r] = line

    # delete at cursor: remove char at cursor position (do not move)
    def delete_at_cursor(self):
        r = self.cursor_row
        line = self.buffer[r]
        if self.cursor_col < len(line):
            line = line[:self.cursor_col] + line[self.cursor_col+1:]
            self.buffer[r] = line

    def cursor_position(self, r=None, c=None):
        if r is None:
            r = 1
        if c is None:
            c = 1
        self.cursor_row = clamp(r-1, 0, self.rows-1)
        self.cursor_col = clamp(c-1, 0, self.cols-1)

    def save_cursor(self):
        self._saved = (self.cursor_row, self.cursor_col)

    def restore_cursor(self):
        self.cursor_row, self.cursor_col = self._saved

    def cursor_up(self, n=1):
        self.cursor_row = clamp(self.cursor_row - n, 0, self.rows - 1)

    def cursor_down(self, n=1):
        self.cursor_row = clamp(self.cursor_row + n, 0, self.rows - 1)

    def cursor_right(self, n=1):
        self.cursor_col = clamp(self.cursor_col + n, 0, self.cols - 1)

    def cursor_left(self, n=1):
        self.cursor_col = clamp(self.cursor_col - n, 0, self.cols - 1)

    # erase line variants
    def erase_line(self, mode=0):
        r = self.cursor_row
        line = self.buffer[r]
        if mode == 0:   # from cursor to end
            if self.cursor_col < len(line):
                line = line[:self.cursor_col]
        elif mode == 1:  # from start to cursor
            if self.cursor_col < len(line):
                line = (" " * (self.cursor_col)) + line[self.cursor_col:]
            else:
                line = " " * len(line)
        else:           # 2: whole line
            line = ""
        self.buffer[r] = line[:self.cols]

    # erase display
    def erase_screen(self, mode=0):
        if mode == 0:
            self.erase_line(0)
            for i in range(self.cursor_row+1, self.rows):
                self.buffer[i] = ""
        elif mode == 1:
            for i in range(0, self.cursor_row):
                self.buffer[i] = ""
            self.erase_line(1)
        else:
            for i in range(self.rows):
                self.buffer[i] = ""
            self.cursor_row = 0
            self.cursor_col = 0

    def set_line(self, row_idx, newtext):
        if 0 <= row_idx < self.rows:
            self.buffer[row_idx] = newtext[:self.cols]

    def current_snapshot(self):
        return list(self.buffer)

    # simple word movement for ctrl+arrow
    # direction = -1 (left) or +1 (right)
    def move_word(self, direction):
        r = self.cursor_row
        line = self.buffer[r]
        if direction < 0:
            # move left to previous whitespace boundary
            pos = self.cursor_col
            if pos == 0:
                # if at start, go to previous line end if possible
                if r > 0:
                    self.cursor_row -= 1
                    self.cursor_col = len(self.buffer[self.cursor_row])
                return
            # skip any whitespace left of cursor
            while pos > 0 and line[pos-1].isspace():
                pos -= 1
            # skip non-whitespace
            while pos > 0 and not line[pos-1].isspace():
                pos -= 1
            self.cursor_col = pos
        else:
            # move right to next whitespace boundary
            pos = self.cursor_col
            L = len(line)
            # skip non-space
            while pos < L and not line[pos].isspace():
                pos += 1
            # skip spaces
            while pos < L and line[pos].isspace():
                pos += 1
            # if at end and there's a next line, move to next line start
            if pos >= L and r < self.rows - 1:
                self.cursor_row += 1
                self.cursor_col = 0
            else:
                self.cursor_col = min(pos, self.cols-1)

# ---------------- small CSI parser ----------------


def parse_csi_params(paramstr):
    if not paramstr:
        return []
    parts = paramstr.split(';')
    out = []
    for p in parts:
        try:
            out.append(int(p))
        except:
            out.append(0)
    return out

# ---------------- server ----------------


class VirtualTerminalServer:
    def __init__(self, rows, cols, out_q):
        self.rows = rows
        self.cols = cols
        self.screen = VirtualScreen(rows, cols)
        self.out_q = out_q
        self.seq = 0
        self._stop = False
        self._esc_state = None
        self._last_snapshot = None
        self._last_abs_top = None

    def spawn_shell(self):
        pid, master_fd = pty.fork()
        if pid == 0:
            shell = os.environ.get("SHELL", "/bin/bash")
            os.execvp(shell, [shell])
        else:
            self.master_fd = master_fd
            import struct
            s = struct.pack('HHHH', self.rows, self.cols, 0, 0)
            fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, s)
            return pid

    def stop(self):
        self._stop = True

    # Read loop: decode to unicode and pass to char-level feeder
    def read_loop(self):
        try:
            while not self._stop:
                r, _, _ = select.select([self.master_fd], [], [], 0.12)
                if self.master_fd in r:
                    try:
                        raw = os.read(self.master_fd, 65536)
                        if not raw:
                            self._stop = True
                            break
                    except OSError:
                        self._stop = True
                        break
                    s = raw.decode('utf-8', errors='replace')
                    self._feed_chars(s)
                    self.emit_diff()
        except Exception as e:
            print("read_loop exception:", repr(e), file=sys.stderr)
            raise

    # feed characters; handle ESC sequences, OSC, CSI, printable characters
    def _feed_chars(self, s):
        i = 0
        while i < len(s):
            ch = s[i]
            if self._esc_state is None:
                if ch == '\x1b':          # ESC - begin sequence
                    # lookahead for OSC (']') or CSI '[' quickly if available in input
                    # begin ESC state capturing
                    self._esc_state = {'buf': ''}
                    i += 1
                elif ch == '\r':
                    self.screen.carriage_return()
                    i += 1
                elif ch == '\n':
                    self.screen._newline(scroll_if_needed=True)
                    i += 1
                elif ch == '\x08' or ch == '\x7f':
                    # backspace bytes from pty output (some programs emit \x7f)
                    self.screen.backspace()
                    i += 1
                elif ch >= ' ':
                    self.screen.put_char(ch)
                    i += 1
                else:
                    # ignore other controls
                    i += 1
            else:
                # in ESC parsing: accumulate until we can handle the sequence
                # we will attempt to parse common sequences:
                #  - CSI  ESC [ ... final
                #  - OSC  ESC ] ... BEL or ESC \
                #  - other 2-byte sequences (ESC 7, ESC 8)
                buf = self._esc_state['buf']
                # append current char
                buf += ch
                i += 1
                # decide type by first char in buf
                if len(buf) == 1:
                    # first following char after ESC
                    if buf == '[':
                        # CSI: need to collect until final byte in range @..~
                        # keep collecting until we see a final
                        # check immediate availability in remaining input:
                        # scan remaining s from i for final
                        j = i
                        final_idx = None
                        while j < len(s):
                            ch2 = s[j]
                            if '@' <= ch2 <= '~':
                                final_idx = j
                                break
                            j += 1
                        if final_idx is None:
                            # we don't yet have final; store and continue
                            self._esc_state['buf'] = buf
                            continue
                        # we have final at position final_idx
                        params = s[i:final_idx]   # characters between '[' and final
                        final = s[final_idx]
                        # consume up to final
                        # note: we have already advanced i to just after buf char; we need to process params+final, so move i
                        i = final_idx + 1
                        self._handle_csi(params, final)
                        self._esc_state = None
                        continue
                    elif buf == ']':
                        # OSC: consume until BEL (\x07) or ESC '\' (ESC backslash)
                        # scan for BEL or ESC '\'
                        j = i
                        found = False
                        while j < len(s):
                            if s[j] == '\x07':
                                # found BEL
                                i = j + 1
                                found = True
                                break
                            if s[j] == '\x1b' and j + 1 < len(s) and s[j+1] == '\\':
                                i = j + 2
                                found = True
                                break
                            j += 1
                        if not found:
                            # we don't yet have termination; keep state and continue
                            self._esc_state['buf'] = buf
                            continue
                        # ignore OSC contents
                        self._esc_state = None
                        continue
                    else:
                        # simple ESC X sequences (one-char final) e.g. ESC 7 / ESC 8 / ESC c
                        # we can handle them immediately now
                        final_char = buf
                        if final_char in ('7', '8', 'c'):
                            self._handle_esc_final(final_char)
                            self._esc_state = None
                            continue
                        else:
                            # other ESC <char> - if printable, ignore; if starts with '(' etc, keep safe
                            # consume one char and treat as consumed
                            self._esc_state = None
                            continue
                else:
                    # This branch handles if we previously had an ESC and buf longer than 1 (rare).
                    # Fallback: reset state to avoid locking
                    self._esc_state = None
                    continue

    def _handle_esc_final(self, final):
        if final == '7':
            self.screen.save_cursor()
        elif final == '8':
            self.screen.restore_cursor()
        elif final == 'c':
            self.screen.erase_screen(2)
            self.screen.cursor_row = 0
            self.screen.cursor_col = 0

    # handle CSI: params is string between '[' and final (may be ''), final is final byte
    def _handle_csi(self, params, final):
        args = parse_csi_params(params)
        # many sequences are `n` or `n;mod final`
        if final == 'A':            # CUU
            n = args[0] if args else 1
            self.screen.cursor_up(n)
        elif final == 'B':          # CUD
            n = args[0] if args else 1
            self.screen.cursor_down(n)
        elif final == 'C':          # CUF
            # support modifier: args like [n, mod]; if mod==5 treat as word move
            if len(args) >= 2 and args[1] == 5:
                self.screen.move_word(+1)
            else:
                n = args[0] if args else 1
                self.screen.cursor_right(n)
        elif final == 'D':          # CUB
            if len(args) >= 2 and args[1] == 5:
                self.screen.move_word(-1)
            else:
                n = args[0] if args else 1
                self.screen.cursor_left(n)
        elif final in ('H', 'f'):   # CUP
            if len(args) >= 2:
                r, c = args[0], args[1]
            elif len(args) == 1:
                r, c = args[0], 1
            else:
                r, c = 1, 1
            self.screen.cursor_position(r, c)
        elif final == 'J':          # ED
            mode = args[0] if args else 0
            self.screen.erase_screen(mode)
        elif final == 'K':          # EL
            mode = args[0] if args else 0
            self.screen.erase_line(mode)
        elif final == 'm':
            # SGR: color/style - strip/ignore (do not alter buffer)
            pass
        elif final == '~':
            # tilde sequences: args[0] indicates key
            code = args[0] if args else 0
            if code == 3:
                # Delete key
                self.screen.delete_at_cursor()
            elif code in (1, 7):
                # Home - move to start of line
                self.screen.cursor_col = 0
            elif code in (4, 8):
                # End - move to end of line content
                r = self.screen.cursor_row
                self.screen.cursor_col = len(self.screen.buffer[r])
            else:
                # other tilde sequences ignored
                pass
        else:
            # unhandled CSI - ignore
            pass

    # compute and emit diff JSON (overlap_runs + new_lines)
    def emit_diff(self, final=False):
        cur = self.screen.current_snapshot()
        cur_top = self.screen.abs_top
        rows = self.rows
        cols = self.cols

        if self._last_snapshot is None:
            self.seq += 1
            msg = {"seq": self.seq, "rows": rows, "cols": cols, "abs_top": cur_top, "full": True, "lines": cur}
            self._last_snapshot = list(cur)
            self._last_abs_top = cur_top
            self.out_q.put(json.dumps(msg, ensure_ascii=False))
            return

        prev_top = self._last_abs_top
        prev_end = prev_top + rows - 1
        cur_end = cur_top + rows - 1

        overlap_runs = []
        overlap_start = max(prev_top, cur_top)
        overlap_end = min(prev_end, cur_end)
        if overlap_start <= overlap_end:
            for absnum in range(overlap_start, overlap_end+1):
                prev_idx = absnum - prev_top
                cur_idx = absnum - cur_top
                if not (0 <= prev_idx < rows and 0 <= cur_idx < rows):
                    continue
                old = self._last_snapshot[prev_idx]
                new = cur[cur_idx]
                if old != new:
                    # find first differing column
                    maxcmp = max(len(old), len(new), cols)
                    p = 0
                    while p < maxcmp:
                        o = old[p] if p < len(old) else ''
                        n = new[p] if p < len(new) else ''
                        if o != n:
                            break
                        p += 1
                    run_text = new[p:] if p < len(new) else ""
                    overlap_runs.append([cur_idx, p, run_text])

        new_lines = []
        if cur_top > prev_top:
            scrolled = cur_top - prev_top
            if scrolled < rows:
                start = rows - scrolled
                new_lines = cur[start:]
            else:
                new_lines = list(cur)
        else:
            new_lines = []

        if not overlap_runs and not new_lines and not final:
            return

        self.seq += 1
        msg = {"seq": self.seq, "rows": rows, "cols": cols, "abs_top": cur_top,
               "full": False, "overlap_runs": overlap_runs, "new_lines": new_lines}
        self._last_snapshot = list(cur)
        self._last_abs_top = cur_top
        self.out_q.put(json.dumps(msg, ensure_ascii=False))

# ---------------- simple local display ----------------


class SimpleDisplay:
    def __init__(self, rows, cols, in_q):
        self.rows = rows
        self.cols = cols
        self.in_q = in_q
        self.view = [""] * rows
        self.abs_top = None

    def apply_diff(self, msg):
        if msg.get("full"):
            self.view = [ln[:self.cols] for ln in msg["lines"]]
            self.abs_top = msg["abs_top"]
            self.render()
            return

        rows = msg["rows"]
        cols = msg["cols"]
        assert rows == self.rows and cols == self.cols
        new_abs_top = msg["abs_top"]
        if self.abs_top is None:
            # fallback: accept as full
            self.view = [""] * self.rows
            self.abs_top = new_abs_top

        delta = new_abs_top - self.abs_top
        if delta > 0:
            # scrolled down
            new_lines = msg.get("new_lines", [])
            if delta < self.rows:
                tail = self.view[delta:]
                merged = tail + new_lines
                if len(merged) < self.rows:
                    pad = [""] * (self.rows - len(merged))
                    self.view = pad + merged
                else:
                    self.view = merged[-self.rows:]
            else:
                if len(new_lines) >= self.rows:
                    self.view = new_lines[-self.rows:]
                else:
                    pad = [""] * (self.rows - len(new_lines))
                    self.view = pad + new_lines
            self.abs_top = new_abs_top
        elif delta < 0:
            self.abs_top = new_abs_top

        # apply overlap runs
        for run in msg.get("overlap_runs", []):
            r_idx, col, text = run
            if not (0 <= r_idx < self.rows):
                continue
            old = self.view[r_idx]
            if col > len(old):
                old = old + (" " * (col - len(old)))
            if text == "":
                new = old[:col]
            else:
                new = old[:col] + text
            self.view[r_idx] = new[:self.cols]

        # if new_lines present but the scroll delta handled differently, ensure bottom updated
        if msg.get("new_lines") and delta <= 0:
            new_lines = msg["new_lines"]
            if len(new_lines) >= self.rows:
                self.view = new_lines[-self.rows:]
            else:
                self.view = self.view[: self.rows - len(new_lines)] + new_lines

        self.render()

    # render exactly rows lines without trailing newline to avoid extra scroll
    def render(self):
        # home + clear
        sys.stdout.write("\x1b[H\x1b[2J")
        # join without trailing newline
        out = "\n".join(ln[:self.cols].ljust(self.cols) for ln in self.view)
        sys.stdout.write(out)
        # move cursor to bottom line, column 0
        sys.stdout.write(f"\x1b[{self.rows};1H")
        sys.stdout.flush()

    def run(self):
        try:
            while True:
                try:
                    raw = self.in_q.get(timeout=0.12)
                except queue.Empty:
                    continue
                try:
                    msg = json.loads(raw)
                except:
                    continue
                self.apply_diff(msg)
        except Exception as e:
            print("display thread exception:", repr(e), file=sys.stderr)
            raise

# ---------------- main wiring ----------------


def main():
    rows, cols = get_winsize(sys.stdout.fileno())
    q = queue.Queue()
    vt = VirtualTerminalServer(rows, cols, q)
    shell_pid = vt.spawn_shell()

    stdin_fd = sys.stdin.fileno()
    old_attrs = termios.tcgetattr(stdin_fd)
    tty.setraw(stdin_fd)
    fl = fcntl.fcntl(stdin_fd, fcntl.F_GETFL)
    fcntl.fcntl(stdin_fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

    reader = threading.Thread(target=vt.read_loop, daemon=True)
    reader.start()

    display = SimpleDisplay(rows, cols, q)
    disp_thr = threading.Thread(target=display.run, daemon=True)
    disp_thr.start()

    def sigchld(signum, frame):
        try:
            while True:
                pid, status = os.waitpid(-1, os.WNOHANG)
                if pid == 0:
                    break
        except ChildProcessError:
            pass
    signal.signal(signal.SIGCHLD, sigchld)

    try:
        while True:
            r, _, _ = select.select([stdin_fd], [], [], 0.05)
            if stdin_fd in r:
                try:
                    data = os.read(stdin_fd, 4096)
                except OSError:
                    data = b''
                if not data:
                    break
                # forward typed bytes to child pty
                try:
                    os.write(vt.master_fd, data)
                except Exception as e:
                    print("write to pty failed:", e, file=sys.stderr)
            if vt._stop:
                break
    except KeyboardInterrupt:
        pass
    finally:
        termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_attrs)
        vt.stop()
        try:
            os.close(vt.master_fd)
        except Exception:
            pass
        sys.stdout.write("\x1b[0m\x1b[2J\x1b[H")
        sys.stdout.flush()


if __name__ == "__main__":
    main()

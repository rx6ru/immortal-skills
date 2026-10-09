#!/usr/bin/env python3
"""ddmin.py - delta-debugging minimiser (Zeller's ddmin) for text inputs.

What it does
    Given an input file and a test command, reduce the input (by lines, or by
    characters) to a 1-minimal failing input: a smaller input on which the
    failure still reproduces, and from which removing any single remaining
    unit (line or character) makes the failure disappear.

How the test command is run
    The command is a shell command line. Every candidate input is written to a
    temporary file and the command is run with that file's path, either
    substituted for the literal token {} in the command, or appended as the
    last argument when no {} is present. Exit code semantics:

        0                    the failure STILL REPRODUCES   (outcome FAIL)
        --unresolved-code N  cannot tell (invalid input, other failure,
                             timeout)                       (outcome UNRESOLVED)
        anything else        the failure does NOT reproduce (outcome PASS)

    The default unresolved code is 125 (the convention git bisect uses for
    "skip"). A timeout counts as UNRESOLVED. Make the command exit 0 only for
    the SAME failure as the original (same message, same crash site), or the
    minimiser can drift onto a different bug.

Algorithm (Why Programs Fail, ch. 5)
    ddmin2(c, n): split c into n near-equal chunks. If some complement
    (c minus one chunk) still FAILs, continue with that complement and
    granularity max(n-1, 2). Otherwise, if n < |c|, double the granularity
    (capped at |c|); else stop. Only FAIL accepts a reduction; PASS and
    UNRESOLVED both reject it. Outcomes are cached by configuration.

Limits
    * The result is 1-minimal, not the global minimum: a smaller failing
      subset may exist elsewhere.
    * Needs a deterministic test. A flaky test breaks the caching and the
      1-minimality guarantee; make the failure reproducible first.
    * Worst case is quadratic in the size of the result; thousands of runs
      are plausible on large inputs. Use --max-tests or --time-budget to stop
      early (the result is then smaller but not guaranteed 1-minimal).
    * Reducing by characters on structured input (JSON, source code) produces
      mostly invalid candidates; reduce by lines first, then by characters
      on the result.
    * Requires that the full input fails. If the empty input also fails, the
      failure does not depend on the input and the result is the empty input
      (a warning is printed).
    * Every {} in --cmd is replaced, so do not use {} for anything else in
      the command. The command runs with stdin closed, in its own process
      group (killed whole on timeout), with output discarded; log what you
      need from inside the command.
    * Lines are split on "\n" only and keep their line endings (so CRLF files
      round-trip). Subsets alone are not tried, only complements, as in the
      book's version of the algorithm.

Usage
    ddmin.py input.txt --cmd './repro.sh {}' -o minimal.txt
    ddmin.py input.txt --cmd 'python3 check.py' --mode chars --verbose
    ddmin.py --self-test
"""

import argparse
import os
import re
import signal
import subprocess
import sys
import tempfile
import time

PASS, FAIL, UNRESOLVED = "PASS", "FAIL", "UNRESOLVED"


class BudgetExceeded(Exception):
    pass


def split(seq, n):
    """Split seq (a list) into n non-empty, near-equal, contiguous chunks."""
    n = max(1, min(n, len(seq)))
    chunks, start = [], 0
    for i in range(n):
        size = (len(seq) - start) // (n - i)
        # round up so that early chunks take the remainder
        if (len(seq) - start) % (n - i):
            size += 1
        chunks.append(seq[start:start + size])
        start += size
    return [c for c in chunks if c]


def ddmin(units, test, max_tests=None, deadline=None, log=None):
    """Reduce `units` (list of hashable-or-not items) to a 1-minimal failing list.

    test(list_of_units) -> PASS | FAIL | UNRESOLVED
    Returns (result_list, number_of_real_test_runs, finished_flag).
    `finished_flag` is False when stopped by a budget (result then may not be
    1-minimal).
    """
    cache = {}
    runs = [0]
    # Work on index lists so duplicates of equal units stay distinct.
    items = list(range(len(units)))

    def run(idx_list):
        key = tuple(idx_list)
        if key in cache:
            return cache[key]
        if max_tests is not None and runs[0] >= max_tests:
            raise BudgetExceeded()
        if deadline is not None and time.time() > deadline:
            raise BudgetExceeded()
        outcome = test([units[i] for i in idx_list])
        runs[0] += 1
        cache[key] = outcome
        if log:
            log("test #%d: %d units -> %s" % (runs[0], len(idx_list), outcome))
        return outcome

    if run(items) != FAIL:
        raise ValueError("the full input does not reproduce the failure "
                         "(test returned %s)" % run(items))
    # Note: an empty `units` list lands here too; the empty candidate is the
    # full input, so it must FAIL for the run to proceed.
    if run([]) == FAIL:
        return [], runs[0], True  # failure independent of the input

    current, n, finished = items, 2, True
    try:
        while len(current) >= 2:
            chunks = split(current, n)
            reduced = False
            for i in range(len(chunks)):
                complement = [x for j, ch in enumerate(chunks) if j != i for x in ch]
                if run(complement) == FAIL:
                    current = complement
                    n = max(n - 1, 2)
                    reduced = True
                    break
            if not reduced:
                if n >= len(current):
                    break
                n = min(n * 2, len(current))
    except BudgetExceeded:
        finished = False
    return [units[i] for i in current], runs[0], finished


def make_command_oracle(cmd, unresolved_code, timeout, suffix):
    """Build a test(units) function that runs `cmd` on a temp file."""
    tmpdir = tempfile.mkdtemp(prefix="ddmin-")
    path = os.path.join(tmpdir, "candidate" + suffix)

    def test(units):
        with open(path, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
            f.write("".join(units))
        full = cmd.replace("{}", _quote(path)) if "{}" in cmd else cmd + " " + _quote(path)
        # Own session so a timeout can kill the whole process group, and no
        # stdin so a command that reads it cannot hang the run.
        proc = subprocess.Popen(full, shell=True, stdin=subprocess.DEVNULL,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                start_new_session=True)
        try:
            code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (OSError, AttributeError):
                proc.kill()
            proc.wait()
            test.last_code = "timeout"
            return UNRESOLVED
        test.last_code = code
        if code == 0:
            return FAIL
        if code == unresolved_code:
            return UNRESOLVED
        return PASS

    test.last_code = None

    def cleanup():
        try:
            os.remove(path)
            os.rmdir(tmpdir)
        except OSError:
            pass

    return test, cleanup


def _quote(p):
    import shlex
    return shlex.quote(p)


def read_units(path, mode):
    with open(path, encoding="utf-8", errors="surrogateescape", newline="") as f:
        text = f.read()
    if mode == "lines":
        # Split on "\n" only (str.splitlines also splits on form feed, \x0b,
        # \x85, U+2028 and others, which are not line ends for most programs).
        # Each unit keeps its line ending, so joining the units restores the text.
        return re.findall(r"[^\n]*\n|[^\n]+", text)
    return list(text)


def is_one_minimal(units, test):
    """True if removing any single unit makes the failure disappear."""
    if test(units) != FAIL:
        return False
    for i in range(len(units)):
        if test(units[:i] + units[i + 1:]) == FAIL:
            return False
    return True


# --------------------------------------------------------------------------
# Self-test: synthetic oracles, no external processes except the CLI check.
# --------------------------------------------------------------------------

def _self_test():
    failures = []

    def check(name, cond):
        print("  %-62s %s" % (name, "ok" if cond else "FAILED"))
        if not cond:
            failures.append(name)

    print("ddmin self-test")

    # 1. Single failure-inducing unit: behaves like binary search (log2 n).
    units = ["line%d\n" % i for i in range(64)]
    oracle = lambda u: FAIL if "line37\n" in u else PASS
    res, runs, fin = ddmin(units, oracle)
    check("single culprit among 64 lines is isolated", res == ["line37\n"] and fin)
    check("single culprit needs few runs (<= 2*log2(64)+4 = 16): %d" % runs, runs <= 16)

    # 2. Two units that must both be present (interaction), order preserved.
    units = list("abcdefghijklmnopqrstuvwxyz")
    oracle = lambda u: FAIL if ("e" in u and "t" in u) else PASS
    res, runs, fin = ddmin(units, oracle)
    check("two required units are both kept, in order", res == ["e", "t"])
    check("result is 1-minimal", is_one_minimal(res, oracle))

    # 3. Substring failure (needs units spread across both halves at first).
    s = "xx<SELECT NAME=a>yy zz"
    oracle = lambda u: FAIL if "<SELECT>" in "".join(u).replace(" NAME=a", "") else PASS
    res, runs, fin = ddmin(list(s), oracle)
    check("char-level reduction finds a failing core: %r" % "".join(res),
          oracle(res) == FAIL and len(res) < len(s))
    check("char-level result is 1-minimal", is_one_minimal(res, oracle))

    # 4. UNRESOLVED outcomes are rejected, never accepted as reductions.
    #    Failure needs 'B'; candidates lacking the balanced 'A'..'C' wrapper are invalid.
    def oracle4(u):
        if not ("A" in u and "C" in u):
            return UNRESOLVED
        return FAIL if "B" in u else PASS
    res, runs, fin = ddmin(list("AxxBxxC"), oracle4)
    check("unresolved candidates are not accepted: %r" % "".join(res),
          set(res) == {"A", "B", "C"})

    # 5. Duplicate units are kept distinct (failure needs two copies of 'x').
    oracle = lambda u: FAIL if u.count("x") >= 2 else PASS
    res, runs, fin = ddmin(list("axbxcxd"), oracle)
    check("duplicates handled (needs two x): %r" % "".join(res), res == ["x", "x"])

    # 6. Caching: the oracle is never run twice on the same configuration.
    seen = set()
    dupes = []

    def oracle6(u):
        k = tuple(u)
        if k in seen:
            dupes.append(k)
        seen.add(k)
        return FAIL if "q" in u and "r" in u else PASS
    ddmin(list("pqrstuvw"), oracle6)
    check("no configuration is tested twice", not dupes)

    # 7. Preconditions: full input must fail; empty-input failure returns [].
    try:
        ddmin(list("abc"), lambda u: PASS)
        check("passing full input raises ValueError", False)
    except ValueError:
        check("passing full input raises ValueError", True)
    res, runs, fin = ddmin(list("abc"), lambda u: FAIL)
    check("failure independent of input reduces to empty", res == [])

    # 8. Budget: stops early and reports unfinished.
    res, runs, fin = ddmin(list(range(100)), lambda u: FAIL if (3 in u and 77 in u) else PASS,
                           max_tests=5)
    check("max_tests stops early and reports not finished", (not fin) and runs <= 5)

    # 9. split() properties.
    ok = True
    for size in range(1, 20):
        for n in range(1, size + 1):
            parts = split(list(range(size)), n)
            flat = [x for p in parts for x in p]
            if flat != list(range(size)) or len(parts) != n or \
               max(map(len, parts)) - min(map(len, parts)) > 1:
                ok = False
    check("split() gives n contiguous near-equal chunks", ok)

    # 10. End to end through the command-line oracle with a real subprocess.
    tmp = tempfile.mkdtemp(prefix="ddmin-selftest-")
    try:
        inp = os.path.join(tmp, "in.txt")
        with open(inp, "w") as f:
            for i in range(40):
                f.write("row %d\n" % i)
            f.write("BOOM\n")
            for i in range(40, 60):
                f.write("row %d\n" % i)
        checker = os.path.join(tmp, "check.py")
        with open(checker, "w") as f:
            f.write("import sys\n"
                    "t = open(sys.argv[1]).read()\n"
                    "sys.exit(0 if 'BOOM' in t else 1)\n")
        cmd = "%s %s {}" % (sys.executable, checker)
        test, cleanup = make_command_oracle(cmd, 125, 20, ".txt")
        res, runs, fin = ddmin(read_units(inp, "lines"), test)
        check("CLI oracle: 61 lines reduce to the BOOM line", res == ["BOOM\n"])
        cleanup()
        # exit code mapping: 125 -> UNRESOLVED
        chk2 = os.path.join(tmp, "check2.py")
        with open(chk2, "w") as f:
            f.write("import sys\nsys.exit(125)\n")
        t2, c2 = make_command_oracle("%s %s" % (sys.executable, chk2), 125, 20, ".txt")
        check("exit code 125 maps to UNRESOLVED", t2(["x"]) == UNRESOLVED)
        c2()
        chk3 = os.path.join(tmp, "check3.py")
        with open(chk3, "w") as f:
            f.write("import sys\nsys.exit(3)\n")
        t3, c3 = make_command_oracle("%s %s" % (sys.executable, chk3), 125, 20, ".txt")
        check("other non-zero exit code maps to PASS", t3(["x"]) == PASS)
        c3()
        # timeout maps to UNRESOLVED and kills the child
        chk4 = os.path.join(tmp, "check4.py")
        with open(chk4, "w") as f:
            f.write("import time\ntime.sleep(30)\n")
        t4, c4 = make_command_oracle("%s %s" % (sys.executable, chk4), 125, 0.5, ".txt")
        check("timeout maps to UNRESOLVED", t4(["x"]) == UNRESOLVED)
        c4()
        # line splitting: "\n" only, endings kept, no trailing newline kept as last unit
        odd = os.path.join(tmp, "odd.txt")
        with open(odd, "w", newline="") as f:
            f.write("a\fb\r\nc\n\nlast")
        check("lines split on \\n only and rejoin exactly",
              read_units(odd, "lines") == ["a\fb\r\n", "c\n", "\n", "last"])
    finally:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)

    if failures:
        print("SELF-TEST FAILED: %d check(s)" % len(failures))
        return 1
    print("SELF-TEST PASSED")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Minimise a failing input with delta debugging (ddmin). "
                    "The test command exits 0 when the failure still reproduces.",
        epilog="See the module docstring for exit-code semantics and limits.")
    ap.add_argument("input", nargs="?", help="input file to minimise")
    ap.add_argument("--cmd", help="test command; {} is replaced by the candidate "
                                  "file path (appended if absent)")
    ap.add_argument("--mode", choices=["lines", "chars"], default="lines",
                    help="unit of reduction (default: lines)")
    ap.add_argument("--unresolved-code", type=int, default=125,
                    help="exit code meaning 'cannot tell' (default 125)")
    ap.add_argument("--timeout", type=float, default=60.0,
                    help="seconds per test run; a timeout is UNRESOLVED (default 60)")
    ap.add_argument("--max-tests", type=int, default=None,
                    help="stop after this many real test runs (result may not be 1-minimal)")
    ap.add_argument("--time-budget", type=float, default=None,
                    help="stop after this many seconds in total")
    ap.add_argument("-o", "--output", help="write the minimal input here (default: stdout)")
    ap.add_argument("--verbose", action="store_true", help="log every test run to stderr")
    ap.add_argument("--self-test", action="store_true", help="run the built-in self-test and exit")
    args = ap.parse_args(argv)

    if args.self_test:
        return _self_test()
    if not args.input or not args.cmd:
        ap.error("input and --cmd are required (or use --self-test)")

    if not args.cmd.strip():
        print("error: --cmd is empty", file=sys.stderr)
        return 2
    try:
        units = read_units(args.input, args.mode)
    except OSError as e:
        print("error: cannot read input file: %s" % e, file=sys.stderr)
        return 2
    suffix = os.path.splitext(args.input)[1]
    test, cleanup = make_command_oracle(args.cmd, args.unresolved_code, args.timeout, suffix)
    deadline = time.time() + args.time_budget if args.time_budget else None
    log = (lambda m: print(m, file=sys.stderr)) if args.verbose else None
    try:
        result, runs, finished = ddmin(units, test, args.max_tests, deadline, log)
    except ValueError as e:
        print("error: %s" % e, file=sys.stderr)
        print("  last exit status of the test command: %s. The command must exit 0 "
              "when the failure reproduces on the ORIGINAL input (exit %d means "
              "unresolved, anything else means pass). Exit 127 means the command was "
              "not found." % (test.last_code, args.unresolved_code), file=sys.stderr)
        cleanup()
        return 2
    except BudgetExceeded:
        # Budget ran out before even the first two checks finished.
        print("error: budget exhausted before the full input could be checked",
              file=sys.stderr)
        cleanup()
        return 2
    cleanup()
    text = "".join(result)
    if not result and units:
        print("warning: the test command also fails on the EMPTY input, so the failure "
              "does not depend on the input file. Check that the command looks at the "
              "candidate file ({} or last argument) and tests the right failure.",
              file=sys.stderr)
    try:
        if args.output:
            with open(args.output, "w", encoding="utf-8", errors="surrogateescape", newline="") as f:
                f.write(text)
        else:
            sys.stdout.write(text)
    except OSError as e:
        print("error: cannot write output: %s" % e, file=sys.stderr)
        return 2
    print("ddmin: %d -> %d %s in %d test runs%s" % (
        len(units), len(result), args.mode, runs,
        "" if finished else " (stopped by budget; not guaranteed 1-minimal)"), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())

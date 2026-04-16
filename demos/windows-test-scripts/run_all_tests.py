"""
Run all demo test scripts and report results.
Usage:
    python run_all_tests.py              # run all tests
    python run_all_tests.py --skip-gpu   # skip test_23 (SAM3, may need GPU)
"""
import subprocess, sys, os, time, glob

# ── Colors ──
class C:
    RESET  = "\033[0m"
    BOLD   = "\033[1m"
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    DIM    = "\033[2m"

SKIP_GPU_TESTS = {"test_23_sam3_inspection.py"}

def main():
    skip_gpu = "--skip-gpu" in sys.argv
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Discover test files
    test_files = sorted(glob.glob("test_*.py"))
    test_files = [f for f in test_files if f != "test_utils.py"]

    if skip_gpu:
        skipped = [f for f in test_files if f in SKIP_GPU_TESTS]
        test_files = [f for f in test_files if f not in SKIP_GPU_TESTS]
        for s in skipped:
            print(f"{C.YELLOW}  SKIP  {s} (--skip-gpu){C.RESET}")

    total = len(test_files)
    passed = 0
    failed = 0
    errors = []
    timings = {}

    print(f"\n{'='*60}")
    print(f"{C.BOLD}{C.CYAN}  OpenClaw Demo Test Suite{C.RESET}")
    print(f"  Running {total} tests...")
    print(f"{'='*60}\n")

    t_start = time.time()

    for i, test_file in enumerate(test_files, 1):
        print(f"{C.DIM}[{i}/{total}] Running {test_file}...{C.RESET}")
        t0 = time.time()
        try:
            result = subprocess.run(
                [sys.executable, test_file],
                capture_output=True, text=True, timeout=120,
                cwd=script_dir,
            )
            elapsed = time.time() - t0
            timings[test_file] = elapsed

            if result.returncode == 0:
                passed += 1
                print(result.stdout)
            else:
                failed += 1
                errors.append((test_file, result.stderr or result.stdout))
                print(result.stdout)
                if result.stderr:
                    print(f"{C.RED}{result.stderr[:300]}{C.RESET}")
        except subprocess.TimeoutExpired:
            elapsed = time.time() - t0
            timings[test_file] = elapsed
            failed += 1
            errors.append((test_file, "TIMEOUT (>120s)"))
            print(f"{C.RED}  TIMEOUT: {test_file}{C.RESET}")
        except Exception as e:
            elapsed = time.time() - t0
            timings[test_file] = elapsed
            failed += 1
            errors.append((test_file, str(e)))
            print(f"{C.RED}  ERROR: {test_file}: {e}{C.RESET}")

    total_time = time.time() - t_start

    # ── Summary Table ──
    print(f"\n{'='*60}")
    print(f"{C.BOLD}{C.CYAN}  TEST SUMMARY{C.RESET}")
    print(f"{'='*60}")
    print(f"  {'File':<40} {'Time':>6}  {'Status'}")
    print(f"  {'-'*40} {'-'*6}  {'-'*6}")

    for test_file in sorted(timings.keys()):
        t = timings[test_file]
        is_fail = any(f == test_file for f, _ in errors)
        status = f"{C.RED}FAIL{C.RESET}" if is_fail else f"{C.GREEN}PASS{C.RESET}"
        print(f"  {test_file:<40} {t:>5.1f}s  {status}")

    if skip_gpu:
        for s in SKIP_GPU_TESTS:
            print(f"  {s:<40} {'---':>6}  {C.YELLOW}SKIP{C.RESET}")

    print(f"  {'-'*55}")
    print(f"  {C.GREEN}Passed: {passed}{C.RESET}  |  {C.RED}Failed: {failed}{C.RESET}  |  Total: {total}  |  Time: {total_time:.1f}s")

    if errors:
        print(f"\n{C.RED}  Failed tests:{C.RESET}")
        for f, err in errors:
            print(f"    {f}: {err[:120]}")

    print(f"\n{'='*60}\n")
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()

import argparse
import hashlib
import os
import sys
import time


def calculate_sha256(filepath):
    """Calculates the SHA-256 hash of a given file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as file_handle:
            for byte_block in iter(lambda: file_handle.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None


def baseline_path_for(filepath):
    """Build the path for the stored integrity baseline."""
    return f"{filepath}.sha256"


def load_baseline(filepath):
    """Load the stored version hash for a watched file if it exists."""
    baseline_file = baseline_path_for(filepath)
    if not os.path.exists(baseline_file):
        return None

    try:
        with open(baseline_file, "r", encoding="utf-8") as file_handle:
            return file_handle.read().strip()
    except OSError:
        return None


def save_baseline(filepath, hash_value):
    """Store the current hash to disk for later comparison."""
    baseline_file = baseline_path_for(filepath)
    with open(baseline_file, "w", encoding="utf-8") as file_handle:
        file_handle.write(hash_value)
    return baseline_file


def check_file(filepath):
    """Run a single integrity check and compare against a stored baseline if available."""
    if not os.path.exists(filepath):
        print(f"[-] Error: Target file '{filepath}' does not exist.")
        return 1

    current_hash = calculate_sha256(filepath)
    baseline_hash = load_baseline(filepath)

    print(f"[*] File: {filepath}")
    print(f"[+] SHA-256: {current_hash}")

    if baseline_hash is None:
        saved_path = save_baseline(filepath, current_hash)
        print(f"[+] Baseline saved to: {saved_path}")
        return 0

    if current_hash == baseline_hash:
        print("[+] Integrity OK: file matches the stored baseline.")
        return 0

    print(f"[!!!] ALERT: {time.strftime('%Y-%m-%d %H:%M:%S')} - INTEGRITY VIOLATION! File modified.")
    print(f"    Expected: {baseline_hash}")
    print(f"    Found:    {current_hash}")
    return 1


def monitor_file(filepath, interval=3):
    """Monitors a file for unauthorized changes against a baseline hash."""
    if not os.path.exists(filepath):
        print(f"[-] Error: Target file '{filepath}' does not exist.")
        return 1

    baseline_hash = load_baseline(filepath)
    if baseline_hash is None:
        baseline_hash = calculate_sha256(filepath)
        save_baseline(filepath, baseline_hash)

    print(f"[*] Establishing baseline for: {filepath}")
    print(f"[+] Baseline Hash: {baseline_hash}")
    print("[*] Monitoring started... Press Ctrl+C to stop.\n")

    try:
        while True:
            time.sleep(interval)
            current_hash = calculate_sha256(filepath)

            if current_hash is None:
                print(f"[!!!] ALERT: {time.strftime('%Y-%m-%d %H:%M:%S')} - File was DELETED!")
                return 1

            if current_hash != baseline_hash:
                print(f"[!!!] ALERT: {time.strftime('%Y-%m-%d %H:%M:%S')} - INTEGRITY VIOLATION! File modified.")
                print(f"    Expected: {baseline_hash}")
                print(f"    Found:    {current_hash}")
                baseline_hash = current_hash
                save_baseline(filepath, baseline_hash)

    except KeyboardInterrupt:
        print("\n[-] Monitoring stopped by user.")
        return 0


def parse_args():
    """Parse CLI arguments for the FIM script."""
    parser = argparse.ArgumentParser(description="Lightweight file integrity monitor")
    parser.add_argument("command", choices=["check", "monitor"], help="Action to perform: check a file or monitor it continuously")
    parser.add_argument("filepath", help="Path to the file to validate or monitor")
    parser.add_argument("--interval", type=int, default=3, help="Seconds between checks while monitoring")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.command == "check":
        sys.exit(check_file(args.filepath))

    sys.exit(monitor_file(args.filepath, interval=args.interval))


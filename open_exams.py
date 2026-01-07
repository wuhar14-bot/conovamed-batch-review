"""
ConovaMed Batch Exam Opener
Opens multiple exam images for review on conovamed.cn

Usage:
    python open_exams.py -n 10          # Open first 10 exams
    python open_exams.py --ids 27473,27472,27471  # Open specific exam IDs

Author: Hao Wu
Date: 2025-01-06
"""

import sys
import io
import os
import time
import argparse
from pathlib import Path

# Force unbuffered output
os.environ['PYTHONUNBUFFERED'] = '1'

# Fix Windows console encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

# Add conovamed package to path
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from conovamed import BrowserManager, Config, Navigator


def open_exams(exam_ids: list, keep_open_minutes: int = 30) -> dict:
    """
    Open multiple exams for review on ConovaMed.

    Args:
        exam_ids: List of exam IDs to open
        keep_open_minutes: How long to keep browser open after completion

    Returns:
        dict with 'success' and 'failed' lists
    """
    results = {'success': [], 'failed': []}

    print("=" * 60)
    print(f"  ConovaMed Batch Exam Opener")
    print(f"  Opening {len(exam_ids)} exams")
    print("=" * 60)
    print(f"Exam IDs: {exam_ids}\n")

    with BrowserManager() as browser:
        page = browser.create_page()

        # === LOGIN ===
        print("[1/4] Logging in...")
        page.goto(Config.URL)
        time.sleep(3)

        # Switch to email login
        email_tab = page.get_by_text("邮箱登录")
        if email_tab.count() > 0:
            email_tab.first.click()
            time.sleep(1)

        # Fill credentials
        page.locator('input[type="text"]').first.fill(Config.EMAIL)
        page.locator('input[type="password"]').first.fill(Config.PASSWORD)

        # Click login button (NOT press Enter - doesn't work on this site)
        page.locator('button.el-button--primary').first.click()

        # Wait for login - check URL and save screenshots for monitoring
        print("  Waiting for login...", flush=True)
        screenshot_dir = Path(__file__).parent / "screenshots"
        screenshot_dir.mkdir(exist_ok=True)

        logged_in = False
        for i in range(60):  # 5 minutes max
            time.sleep(5)
            current_url = page.url

            # Save screenshot every check for monitoring
            screenshot_path = screenshot_dir / f"login_status.png"
            page.screenshot(path=str(screenshot_path))
            print(f"  📸 Screenshot: {screenshot_path} | URL: {current_url}", flush=True)

            # Check for successful login indicators
            if '#/dashboard' in current_url or '#/image' in current_url or ('#/login' not in current_url and 'conovamed' in current_url):
                print(f"  ✓ Logged in! URL: {current_url}", flush=True)
                logged_in = True
                break

        if not logged_in:
            print("  ⚠ Login timeout - please complete login manually", flush=True)
            # Keep waiting indefinitely
            while True:
                time.sleep(5)
                current_url = page.url
                if '#/dashboard' in current_url or '#/image' in current_url or '#/login' not in current_url:
                    print(f"  ✓ Logged in! URL: {current_url}", flush=True)
                    break

        time.sleep(3)

        # === NAVIGATE TO IMAGE MANAGEMENT (NEW TAB) ===
        print("\n[2/4] Opening Image Management...")
        nav = Navigator(page)
        img_page = nav.go_to_image_management_new_tab()

        if not img_page:
            print("  ✗ Failed to open Image Management")
            return results
        print(f"  ✓ URL: {img_page.url}")

        # === NAVIGATE TO ALL EXAMS (NEW TAB) ===
        print("\n[3/4] Opening All Exams...")
        nav2 = Navigator(img_page)
        exam_page = nav2.go_to_all_exams_new_tab()

        if not exam_page:
            print("  ✗ Failed to open All Exams")
            return results
        print(f"  ✓ URL: {exam_page.url}")

        # === OPEN EACH EXAM ===
        print(f"\n[4/4] Opening {len(exam_ids)} exams...")

        for i, exam_id in enumerate(exam_ids, 1):
            print(f"\n  [{i}/{len(exam_ids)}] Exam {exam_id}...", end=" ", flush=True)

            try:
                # Save debug screenshot on first exam
                if i == 1:
                    debug_path = screenshot_dir / "exam_page_debug.png"
                    exam_page.screenshot(path=str(debug_path))
                    print(f"(debug: {debug_path})", end=" ", flush=True)

                # Find the EXAM ID search field - try multiple selectors
                search = exam_page.locator('input[placeholder*="检查"]')
                if search.count() == 0:
                    search = exam_page.locator('input[placeholder*="ID"]')
                if search.count() == 0:
                    # Fallback: find input near the 检查 label
                    search = exam_page.locator('input.el-input__inner').nth(1)

                if search.count() > 0:
                    # Clear and fill
                    search.first.clear()
                    search.first.fill(str(exam_id))
                    time.sleep(0.3)

                    # Click search button
                    btn = exam_page.locator('button:has-text("搜索")')
                    if btn.count() > 0:
                        btn.first.click()

                    # Wait for loading spinner to disappear (search complete)
                    time.sleep(0.5)  # Brief wait for spinner to appear
                    for _ in range(15):  # Wait up to 15 seconds for loading
                        spinner = exam_page.locator('.el-loading-mask')
                        if spinner.count() == 0 or not spinner.first.is_visible():
                            break
                        time.sleep(1)
                    time.sleep(0.5)  # Extra buffer after loading completes

                    # Wait for search results with retry
                    row = None
                    for attempt in range(5):  # Try up to 5 times (5 seconds total)
                        time.sleep(1)
                        row = exam_page.locator(f'tr:has-text("{exam_id}")')
                        if row.count() > 0:
                            break

                    # Save screenshot if row not found for debugging
                    if row is None or row.count() == 0:
                        screenshot_path = screenshot_dir / f"search_fail_{exam_id}.png"
                        exam_page.screenshot(path=str(screenshot_path))
                        print(f"✗ Row not found (screenshot: {screenshot_path})")
                        results['failed'].append(exam_id)
                    else:
                        # Double-click row to open detail
                        row.first.dblclick()
                        time.sleep(1.5)
                        print("✓ Opened")
                        results['success'].append(exam_id)
                else:
                    print("✗ Search input not found")
                    results['failed'].append(exam_id)

            except Exception as e:
                print(f"✗ Error: {e}")
                results['failed'].append(exam_id)

        # === SUMMARY ===
        print("\n" + "=" * 60)
        print(f"  Done! Opened {len(results['success'])}/{len(exam_ids)} exams")
        print(f"  Success: {results['success']}")
        if results['failed']:
            print(f"  Failed: {results['failed']}")
        print("=" * 60)

        print(f"\n>>> Browser stays open for {keep_open_minutes} minutes <<<")
        print(">>> Review your images, then close browser or wait <<<\n")

        time.sleep(keep_open_minutes * 60)

    return results


def main():
    parser = argparse.ArgumentParser(
        description='Open multiple exam images on ConovaMed for review',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python open_exams.py -n 10              # Open first 10 exams from Excel
  python open_exams.py -n 20              # Open first 20 exams
  python open_exams.py --ids 27473,27472  # Open specific exam IDs
  python open_exams.py -n 5 -t 60         # Open 5 exams, keep browser 60 min
        """
    )
    parser.add_argument('-n', '--count', type=int, default=10,
                        help='Number of exams to open (default: 10)')
    parser.add_argument('--ids', type=str, default=None,
                        help='Specific exam IDs, comma-separated')
    parser.add_argument('-t', '--time', type=int, default=30,
                        help='Minutes to keep browser open (default: 30)')

    args = parser.parse_args()

    # Get exam IDs
    if args.ids:
        exam_ids = [int(x.strip()) for x in args.ids.split(',')]
        print(f"Using specified exam IDs: {exam_ids}")
    else:
        exam_ids = Config.get_sample_exam_ids(args.count)
        print(f"Loading first {args.count} exam IDs from Excel")

    if not exam_ids:
        print("✗ No exam IDs found!")
        sys.exit(1)

    # Run
    try:
        results = open_exams(exam_ids, keep_open_minutes=args.time)

        if len(results['success']) == len(exam_ids):
            print("\n✅ All exams opened successfully!")
            sys.exit(0)
        elif results['success']:
            print("\n⚠ Some exams opened")
            sys.exit(0)
        else:
            print("\n❌ Failed to open exams")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

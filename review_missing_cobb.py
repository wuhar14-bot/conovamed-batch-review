"""
review_missing_cobb.py
======================
打开16名缺失 Cobb 值患者的所有影像，供手动核查补录。

Usage:
    python review_missing_cobb.py
    python review_missing_cobb.py --group A
    python review_missing_cobb.py --group B
    python review_missing_cobb.py --name 高畅
    python review_missing_cobb.py --count 3
"""

import sys, io, time, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from playwright.sync_api import sync_playwright

URL      = "https://www.conovamed.cn/#/login"
EMAIL    = "kafwu@connect.hku.hk"
PASSWORD = "Conovamed1"

PATIENTS = {
    "丁一璇":   ("A", "2024-11缺Cobb / 另1张无日期"),
    "余可":     ("A", "2024-02另1张缺Cobb / 1张无日期"),
    "包欣霖":   ("A", "2024-08缺Cobb"),
    "张旸妈妈": ("A", "2024-03缺Cobb"),
    "施语萱":   ("A", "另1张无日期无Cobb"),
    "林山溦":   ("A", "2024-09 / 2024-02缺Cobb"),
    "沈一默":   ("A", "3张缺Cobb"),
    "程佳怡":   ("A", "2024-11缺Cobb"),
    "程歆诺":   ("A", "2024-10缺Cobb"),
    "董宛樾":   ("A", "2024-11缺Cobb"),
    "陈栋伟":   ("A", "2024-03×2缺Cobb"),
    "高畅":     ("A", "2024-03另1张缺Cobb"),
    "方佳怡":   ("B", "3张全部缺Cobb (2025-03/2024-08/2023-12)"),
    "朱馨予":   ("B", "4张全部缺Cobb (2025-07/2024-08/2024-05×2)"),
    "朱馨媛":   ("B", "2张全部缺Cobb (2025-07/2024-08)"),
    "王可滢":   ("B", "2张全部缺Cobb (2025-07/2024-12)"),
}


def login(page):
    print("\n[1/3] 登录中...")
    page.goto(URL, wait_until="domcontentloaded")
    time.sleep(2)

    page.evaluate("""
        () => {
            const els = document.querySelectorAll('*');
            for (const el of els) {
                if (el.innerText && el.innerText.trim() === '邮箱登录' && el.children.length === 0) {
                    el.click(); return;
                }
            }
        }
    """)
    time.sleep(1.5)

    page.locator('input[type="text"]:not([readonly])').first.fill(EMAIL)
    page.locator('input[type="password"]').first.fill(PASSWORD)

    login_btn = page.query_selector('button:has-text("登录")')
    if not login_btn:
        login_btn = page.query_selector('button:has-text("登 录")')
    if not login_btn:
        login_btn = page.query_selector('.el-button--primary')
    if login_btn:
        login_btn.click()
    else:
        try:
            page.get_by_text('登录', exact=True).first.click()
        except:
            pass

    print("  等待 dashboard 加载...")
    page.wait_for_selector('text=影像管理', timeout=30000)
    print("  ✓ 登录成功")
    return True


def open_image_management(page, context):
    """dashboard → 影像管理(新tab) → 全部检查(又一个新tab) → 设检查类型"""
    print("\n[2/3] 打开影像管理...")
    page.wait_for_selector('text=影像管理', timeout=15000)
    with context.expect_page(timeout=10000) as new_tab_info:
        page.get_by_text('影像管理', exact=True).first.click()
    img_tab = new_tab_info.value
    img_tab.wait_for_load_state("domcontentloaded")
    time.sleep(3)
    print(f"  ✓ 影像管理已打开: {img_tab.url}")

    # 点"全部检查"—— 它也会开新 tab
    all_check = img_tab.get_by_text("全部检查", exact=True)
    if all_check.count() > 0:
        with context.expect_page(timeout=10000) as exam_tab_info:
            all_check.first.click()
        exam_tab = exam_tab_info.value
        exam_tab.wait_for_load_state("domcontentloaded")
        time.sleep(3)
        print(f"  ✓ 全部检查已打开: {exam_tab.url}")
    else:
        print("  ⚠ 未找到全部检查按钮，用 img_tab 继续")
        exam_tab = img_tab

    # 等搜索框出现
    try:
        exam_tab.wait_for_selector('input[placeholder*="姓名"]', timeout=10000)
    except Exception:
        pass

    # 设检查类型 = 脊柱X光全长
    try:
        clicked = exam_tab.evaluate("""
            () => {
                const labels = document.querySelectorAll('.el-form-item__label');
                for (const label of labels) {
                    if (label.textContent.trim() === '检查类型:') {
                        const inp = label.closest('.el-form-item')
                                        .querySelector('.el-select .el-input__inner');
                        if (inp) { inp.click(); return true; }
                    }
                }
                return false;
            }
        """)
        if clicked:
            time.sleep(0.8)
            opt = exam_tab.query_selector('li.el-select-dropdown__item:has-text("脊柱X光全长")')
            if opt and opt.is_visible():
                opt.click()
                time.sleep(0.5)
                print("  ✓ 检查类型已设为: 脊柱X光全长")
            else:
                exam_tab.keyboard.press('Escape')
                print("  ⚠ 未找到脊柱X光全长选项")
        else:
            print("  ⚠ 未找到检查类型下拉框")
    except Exception as e:
        print(f"  ⚠ 设检查类型异常: {e}")

    return exam_tab


def search_patient(img_tab, name):
    """搜索患者姓名"""
    try:
        img_tab.wait_for_selector('input[placeholder*="姓名"]', timeout=8000)
    except Exception:
        pass

    search_input = img_tab.query_selector('input[placeholder*="姓名"]')
    if not search_input:
        search_input = img_tab.query_selector('input[placeholder*="PID"]')
    if not search_input:
        for inp in img_tab.query_selector_all('input'):
            if inp.is_visible():
                ph = inp.get_attribute('placeholder') or ''
                if any(k in ph for k in ['姓名', 'PID', '搜索', '输入']):
                    search_input = inp
                    break

    if not search_input:
        print(f"    ✗ 未找到搜索框")
        return False

    search_input.triple_click()
    time.sleep(0.2)
    search_input.fill(name)
    time.sleep(0.3)

    search_btn = img_tab.query_selector('button:has-text("搜索")')
    if not search_btn:
        search_btn = img_tab.query_selector('button:has-text("查询")')
    if search_btn:
        search_btn.click()
    else:
        search_input.press('Enter')
    time.sleep(2.5)
    return True


def open_patient(img_tab, context, name, note):
    """搜索患者，打开所有脊柱X光全长行"""
    print(f"\n  → {name}（{note}）")
    try:
        if not search_patient(img_tab, name):
            return 0

        rows = img_tab.query_selector_all('.el-table__body tr.el-table__row')
        n = len(rows)

        if n == 0:
            print(f"    ⚠ 无结果行，请手动操作")
            return 0

        print(f"    ✓ 找到 {n} 行，逐行打开...")

        opened = 0
        for i in range(n):
            rows = img_tab.query_selector_all('.el-table__body tr.el-table__row')
            if i >= len(rows):
                break
            btns = rows[i].query_selector_all('button')
            if btns:
                btns[0].click()
                time.sleep(1.5)
                print(f"    ✓ 第 {i+1}/{n} 张已打开")
                opened += 1
            else:
                print(f"    ⚠ 第 {i+1} 行无按钮，跳过")

        return opened

    except Exception as e:
        print(f"    ✗ 打开患者 {name} 出错: {e}")
        return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--group', choices=['A', 'B'])
    parser.add_argument('--name', type=str)
    parser.add_argument('--count', type=int, default=None)
    args = parser.parse_args()

    targets = {}
    for name, (group, note) in PATIENTS.items():
        if args.name and name != args.name:
            continue
        if args.group and group != args.group:
            continue
        targets[name] = (group, note)

    if args.count:
        targets = dict(list(targets.items())[:args.count])

    print("=" * 60)
    print(f"  待核查患者: {len(targets)} 人")
    print("=" * 60)
    for name, (group, note) in targets.items():
        print(f"  [{group}] {name}: {note}")
    print("=" * 60)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False,
            args=['--start-maximized', '--window-position=0,0']
        )
        context = browser.new_context(no_viewport=True)
        page = context.new_page()
        page.set_default_timeout(30000)

        if not login(page):
            browser.close()
            return

        img_tab = open_image_management(page, context)
        if not img_tab:
            browser.close()
            return

        print(f"\n[3/3] 逐患者打开影像...")
        total_opened = 0
        for name, (group, note) in targets.items():
            n = open_patient(img_tab, context, name, note)
            total_opened += n

        print("\n" + "=" * 60)
        print(f"  完成！共打开 {total_opened} 个影像标签页")
        print(f"  浏览器保持开启，请补录 Cobb 值")
        print(f"  补录完成后按 Enter 关闭浏览器")
        print("=" * 60)

        input()
        browser.close()


if __name__ == "__main__":
    main()

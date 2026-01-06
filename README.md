# ConovaMed Batch Exam Review Tool

Automated tool to open multiple X-ray exam images on [conovamed.cn](https://www.conovamed.cn) for batch review.

## Features

- Automatic login to ConovaMed
- Navigate through Image Management → All Exams
- Search and open multiple exams by ID
- Keep browser open for manual review
- Support for custom exam ID lists

## Prerequisites

1. **Python 3.10+**
2. **Playwright** - Browser automation library
   ```bash
   pip install playwright
   playwright install chromium
   ```
3. **pandas** - For reading Excel files
   ```bash
   pip install pandas openpyxl
   ```

## Project Structure

```
figures/
├── conovamed/                 # ConovaMed automation package
│   ├── __init__.py
│   ├── auth.py               # Authentication
│   ├── browser.py            # Browser management
│   ├── config.py             # Configuration (credentials, URLs)
│   ├── navigation.py         # Page navigation
│   ├── search.py             # Search functionality
│   └── workspace.py          # Workspace selection
├── scripts/
│   └── batch_review/
│       ├── open_exams.py     # Main script
│       └── README.md         # This file
└── x-ray/
    └── complete_image_list.xlsx  # Exam list
```

## Usage

### Open First N Exams
```bash
cd E:\claude-code\AIS_PSSE_浙一\figures\scripts\batch_review

# Open first 10 exams (default)
python open_exams.py

# Open first 20 exams
python open_exams.py -n 20

# Open first 5 exams, keep browser open for 60 minutes
python open_exams.py -n 5 -t 60
```

### Open Specific Exam IDs
```bash
# Open specific exams by ID
python open_exams.py --ids 27473,27472,27471,27470

# Open specific exams, keep browser 45 minutes
python open_exams.py --ids 27473,27472 -t 45
```

## How It Works

1. **Login**: Fills email/password, clicks login button
2. **Navigate**: Opens Image Management → All Exams (each in new tab)
3. **Search**: For each exam ID:
   - Fills the "检查ID" (Exam ID) search field
   - Clicks search button
   - Double-clicks result row to open detail view
4. **Review**: Browser stays open for manual review

## Configuration

Edit `conovamed/config.py` to change:

```python
# Credentials
EMAIL = "your-email@example.com"
PASSWORD = "your-password"

# Workspace
WORKSPACE_NAME = "林茂医师 工作室"

# Excel file path
EXCEL_PATH = r"E:\path\to\your\exam_list.xlsx"
EXAM_ID_COLUMN = "检查Id"
```

## Troubleshooting

### Login Issues
- **CAPTCHA**: If login takes too long, check browser for CAPTCHA
- **Credentials**: Verify email/password in `config.py`
- **Button click**: The site requires clicking the 登录 button (not pressing Enter)

### Search Issues
- **No results**: Verify exam IDs exist in the system
- **Wrong field**: Script uses `input[placeholder*="检查ID"]` for Exam ID field

### Navigation Issues
- **404 Error**: Don't use direct URLs - navigate through menu (opens new tabs)
- **New tabs**: Each navigation step opens a new browser tab

## Example Output

```
============================================================
  ConovaMed Batch Exam Opener
  Opening 10 exams
============================================================
Exam IDs: [27473, 27472, 27471, 27470, 27469, 27468, 27467, 27466, 27465, 27464]

[1/4] Logging in...
  Waiting for login...
  ✓ Logged in!

[2/4] Opening Image Management...
  ✓ URL: https://www.conovamed.cn/#/imageLanding/index

[3/4] Opening All Exams...
  ✓ URL: https://www.conovamed.cn/#/imageEvaluation/index

[4/4] Opening 10 exams...

  [1/10] Exam 27473... ✓ Opened
  [2/10] Exam 27472... ✓ Opened
  ...
  [10/10] Exam 27464... ✓ Opened

============================================================
  Done! Opened 10/10 exams
  Success: [27473, 27472, 27471, 27470, 27469, 27468, 27467, 27466, 27465, 27464]
============================================================

>>> Browser stays open for 30 minutes <<<
```

## Author

Hao Wu - Department of Orthopaedics & Traumatology, HKU

## License

Internal use only - Do not distribute credentials.

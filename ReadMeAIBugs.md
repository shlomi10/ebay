# ReadMeAIBugs

סקירה סטטית של קוד בדיקה שנבנה בעזרת AI ולא עובד כמצופה.

## הקוד שנבדק

```python
from playwright.sync_api import sync_playwright
from selenium import webdriver
import time

def test_search_functionality():
    browser = sync_playwright().start().chromium.launch()
    page = browser.new_page()
    page.goto("https://example.com")

    time.sleep(2)

    search_box = page.locator("#search")
    search_box.fill("playwright testing")

    page.locator(".button").click()

    time.sleep(3)

    results = page.locator(".result-item")

    browser.close()
```

## בעיה 1 — ערבוב ספריות ו-import מת

`from selenium import webdriver` לא בשימוש בכלל. הקוד רץ על Playwright בלבד.

זה יוצר תלות מיותרת, מבלבל תחזוקה, ועלול לגרום לכשל התקנה/CI בגלל Selenium שלא נדרש.

תיקון: למחוק את שורת ה-Selenium.

```python
from playwright.sync_api import sync_playwright, expect
```

## בעיה 2 — ניהול משאבים שבור של Playwright

`sync_playwright().start()` מחזיר מופע Playwright שחייב `stop()`. כאן:

- אין `playwright.stop()`
- `start()` ו-`chromium.launch()` משורשרים, אז אין משתנה ל-Playwright עצמו
- אם `fill` / `click` נכשל, `browser.close()` לא רץ ונוצר תהליך תלוי

תיקון: context manager + `finally`.

```python
def test_search_functionality():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            page = browser.new_page()
            page.goto("https://example.com")
            # ...
        finally:
            browser.close()
```

עדיף עוד יותר fixture של pytest-playwright שמנהל browser/page לבד.

## בעיה 3 — `time.sleep` במקום המתנה חכמה

`time.sleep(2)` ו-`time.sleep(3)` הם המתנות קשיחות:

- קצרות מדי ב-CI / רשת איטית → flaky
- ארוכות מדי במכונה מהירה → בזבוז זמן
- Playwright כבר יודע לחכות ל-actionability ב-`fill`/`click`

תיקון: auto-wait + `expect`.

```python
page.goto("https://example.com", wait_until="domcontentloaded")
search_box = page.locator("#search")
search_box.wait_for(state="visible")
search_box.fill("playwright testing")
page.get_by_role("button", name="Search").click()
expect(page.locator(".result-item").first).to_be_visible()
```

## בעיה 4 — אין Assertion, לכן הבדיקה תמיד "ירוקה"

`results = page.locator(".result-item")` לא בודק כלום:

- אין `assert`
- אין `expect`
- אין בדיקת כמות או טקסט
- יצירת Locator לא נכשלת גם אם אין אלמנטים בדף

הטסט יכול להגיע ל-`browser.close()` בלי לוודא שחיפוש בכלל הצליח.

תיקון:

```python
results = page.locator(".result-item")
expect(results).not_to_have_count(0)
expect(results.first).to_contain_text("playwright")
```

## בעיה 5 — לוקטורים שבירים

`#search` ו-`.button` הם סלקטורים גנריים:

- `.button` עלול לתפוס כפתור לא נכון
- `example.com` בכלל אין חיפוש כזה, אז הקוד ייכשל על האתר שכתוב בו
- אין fallback ואין role/placeholder

תיקון: לוקטורים יציבים לפי תפקיד, עם נפילה משנית.

```python
search_box = page.get_by_role("searchbox").or_(page.locator("#search"))
search_box.fill("playwright testing")
page.get_by_role("button", name="Search").click()
```

## סיכום תיקון מלא מומלץ

```python
from playwright.sync_api import expect, sync_playwright


def test_search_functionality():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page()
        try:
            page.goto("https://example.com", wait_until="domcontentloaded")
            search_box = page.get_by_role("searchbox").or_(page.locator("#search"))
            search_box.fill("playwright testing")
            page.get_by_role("button", name="Search").click()
            results = page.locator(".result-item")
            expect(results.first).to_be_visible()
            expect(results).not_to_have_count(0)
        finally:
            browser.close()
```

בפרויקט האמיתי עדיף POM + pytest-playwright + Allure, בלי `sleep` ובלי ערבוב Selenium.

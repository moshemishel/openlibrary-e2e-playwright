# AI Bug Analysis

This file documents the static code analysis exercise from the assignment.
The goal is to review the provided code sample without running it and identify real bugs.
For each confirmed bug, the analysis explains what is wrong, why it matters, and how to fix it.

> Status: Four confirmed bugs documented. One rejected candidate is kept as a note because it is a code-quality issue, not a functional bug.

---

## Source

The code under review was provided in the assignment PDF. It is a Playwright + Pytest sample with classes `BookSearchPage` and `ReadingListPage`, plus three async functions:
`search_books_by_title_under_year`, `add_books_to_reading_list`, and `assert_reading_list_count`.

---

## Bug 1 

**Where:** `BookSearchPage`

**What is wrong:**

`self.search_button` uses the selector `button[type='submit']`, but the OpenLibrary search form renders the submit control as an `<input>` element, not as a `<button>` element:

```html
<input type="submit" value="" class="search-bar-submit" aria-label="Search submit">
```

**Why it is a problem:**

Playwright will not find any element matching `button[type='submit']`. When the test tries to click the search button, it will wait for a non-existing selector and eventually fail with a timeout. As a result, the search flow cannot submit the query.

**Fix:**

```python
self.search_button = "input[type='submit']"
```

---

## Candidate 2 - Not counted as a real bug

**Where:** `search_books_by_title_under_year`

**What is wrong:**

The function creates an instance of `BookSearchPage`, but then still uses the raw `page` object directly in a few places. It also queries result items with the hard-coded selector `.searchResultItem` instead of using the page object's selector attribute, such as `search_page.results`.

**Why this is not a real bug:**

This is a maintainability problem, not a functional bug. If `search_page = BookSearchPage(page)`, then `page` and `search_page.page` point to the same Playwright page object. The code can still run correctly. The same is true for `.searchResultItem` if it has the same value as `search_page.results`.

The issue is that it weakens the Page Object Model: selectors are duplicated outside the page object, so future selector changes would need to be updated in more than one place.

**Optional cleanup:**

```python
results = await search_page.page.query_selector_all(search_page.results)
```

This candidate should not be counted as one of the required real bugs unless the original code contains an additional mistake, such as using an undefined `page` variable or using a selector value that differs from `search_page.results`.

---

## Bug 2

**Where:** `ReadingListPage.get_book_count`

**What is wrong:**

The method counts `.listbook-item`, but this selector does not exist on the My Books page.

**Why it is a problem:**

The method returns `0` even when the shelves contain books.

**Fix:**

Read the counts from the shelf headers, for example `Want to Read (16)` and `Already Read (2)`, and return `0` when a shelf has no count, like `Currently Reading`.

---

## Bug 3

**Where:** `search_books_by_title_under_year`

**What is wrong:**

The code tries to read the publication year from the editions element, but the search result page does not expose the year there. The editions link contains text such as `35 editions`, while the publication year appears separately inside `.resultDetails`, for example `First published in 1984`.

The code also converts the text directly with `int(...)`. This is incorrect because the year is part of a sentence, not a plain number.

**Why it is a problem:**

The function may fail with `ValueError` when trying to convert text like `First published in 1984` to an integer. It may also parse the wrong number if it reads `35 editions` instead of the publication year.

**Fix:**

Read the text from `.resultDetails`, extract the year with a regex, and only then convert the matched year to `int`.

```python
details = await result.query_selector(".resultDetails")
text = await details.inner_text()

match = re.search(r"First published in\s+(\d{4})", text)
if match:
    year = int(match.group(1))
```

---

## Bug 4

**Where:** `main`

**What is wrong:**

The `main` function creates a Playwright `page` and launches a browser, but it does not close them at the end of the run.

**Why it is a problem:**

If the page and browser are not closed, Chromium processes may stay open after the script finishes or fails. This can waste system resources and make repeated test runs unstable.

**Fix:**

Close the page and browser in a `finally` block, so cleanup happens even if the test flow fails.

```python
browser = await playwright.chromium.launch()
page = await browser.new_page()

try:
    # test flow here
finally:
    await page.close()
    await browser.close()
```

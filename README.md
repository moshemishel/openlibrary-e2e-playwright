 # OpenLibrary E2E Automation

  End-to-end automation framework for [openlibrary.org](https://openlibrary.org), built with **Playwright** and **Pytest** in Python.

  ---
                                                                                                                                                                                               
  ## Requirements Summary
  
  The project must implement four async functions with these exact signatures:

  ### 1. Search books by title, filtered by max publication year

  ```python
  async def search_books_by_title_under_year(query: str, max_year: int, limit: int = 5) -> list[str]:                                                                                          
  ```

  - Search by `query`, filter results by `max_year`, and collect up to `limit` book URLs.
  - **Pagination:** if fewer than 5 results were found on the current page, move to the next page.
  - **Returning 0 results is OK** if there are no matches.

  ### 2. Add books to the user's Reading List

  ```python
  async def add_books_to_reading_list(urls: list[str]) -> None:                                                                                                                                
  ```
  
  - For each URL, open the book page and click "Want to Read" or "Already Read" (random choice).
  - Take a screenshot and write a log line for every book added.

  ### 3. Assert Reading List count                                                                                                                                                             

  ```python                                                                                                                                                                                    
  async def assert_reading_list_count(expected_count: int) -> None:
  ```

  - Open the Reading List page. Count the books. Compare to `expected_count`.
  - Save a screenshot or trace of the result.

  ### 4. Page performance measurement                                                                                                                                                          

  ```python                                                                                                                                                                                    
  async def measure_page_performance(page, url: str, threshold_ms: int) -> dict:
  ```

  - Measure `load_time_ms`, `dom_content_loaded_ms`, and `first_paint_ms`.
  - If a page is slower than the threshold, write a warning to the log. Do not fail the test.
  - After the run, save all results to `reports/performance_report.json`.

  **Per-page thresholds:**

  | Page | Threshold |
  |---|---|
  | Search results | 3000 ms |
  | Book detail | 2500 ms |                                                                                                                                                                    
  | Reading List | 2000 ms |

  ---
                                                                                                                                                                                               
  ## Architectural Requirements

  - **Page Object Model (POM)** — one class per page, clean OOP.
  - **Data-Driven** — load test inputs from external files (JSON / CSV / YAML). Support environment profiles.
  - **Single Responsibility** — keep page actions, data loading, and assertions in separate places.

  ---

  ## Robustness Focus Areas                                                                                                                                                                    
  
  Robustness is 30% of the grade. Focus on:

  - **Pagination** — find the "next page" button correctly. Keep going until the limit is reached or there are no more pages.
  - **Year parsing** — handle missing or messy year data without crashing.                                                                                                                     
  - **Status handling** — handle different UI states (logged in / logged out, missing buttons, slow loading).
  - **Empty results** — `0` results is a valid case, not an error.

  ---
                                                                                                                                                                                               
  ## Deliverables
  
  | # | Item | Notes |
  |---|---|---|
  | 1 | Public GitHub repository | Public access for the reviewer |
  | 2 | `README.md` | Setup, run, architecture, limitations |
  | 3 | `reports/report.html` | Self-contained HTML run report (pytest-html) |
  | 4 | `reports/performance_report.json` | Aggregated output of `measure_page_performance` |
  | 5 | `ReadMeAIBugs.md` | Bug analysis exercise — at least 3 bugs, each with explanation and fix |

  ---

  ## Tech Stack                                                                                                                                                                                
  
  | Concern | Choice |
  |---|---|
  | Language | Python 3.11+ |
  | Browser automation | [Playwright](https://playwright.dev/python/) |
  | Test framework | [Pytest](https://docs.pytest.org/) + `pytest-asyncio` |
  | Linting / Formatting | [Ruff](https://docs.astral.sh/ruff/) |
  | Reporting | [pytest-html](https://pytest-html.readthedocs.io/) — self-contained HTML at `reports/report.html`. Custom JSON aggregation at `reports/performance_report.json` for `measure_page_performance` results. |

  ---

  ## Setup                                                                                                                                                                                     
  
  Requires Python 3.11+.

  ```bash
  # Clone                                                                                                                                                                                      
  git clone https://github.com/moshemishel/openlibrary-e2e-playwright.git 
  cd openlibrary-e2e-playwright

  # Virtual environment
  python3 -m venv .venv
  source .venv/bin/activate    # macOS / Linux
  # .venv\Scripts\activate     # Windows

  # Install pinned dependencies
  pip install -r requirements.txt

  # Install the local package in editable mode
  pip install -e .
                                                                                                                                                                                               
  # Install Playwright browser
  playwright install chromium
  ```

  ---                                                                                                                                                                                          
  
  ## Running Tests
  
  ```bash
  # Run all tests
  pytest

  # Lint check
  ruff check .

  # Auto-format
  ruff format .                                                                                                                                                                                
  ```

  ---

  ## Configuration & Profiles

  All runtime settings live in `config/config.json`. The file holds named profile blocks:

  ```json
  {
    "default": {
      "base_url": "https://openlibrary.org",
      "headless": true,
      "slow_mo": 0,
      "thresholds": { "search": 3000, "book": 2500, "reading_list": 2000 }
    },
    "debug": { "headless": false, "slow_mo": 500 },
    "ci":    { "headless": true }
  }
  ```

  **Choose a profile** with the `PROFILE` environment variable:

  ```bash
  pytest                  # uses default
  PROFILE=debug pytest    # default merged with debug overrides
  PROFILE=ci pytest       # default merged with ci overrides
  ```

  **Stable values** (login credentials, default profile) live in a `.env` file. Copy `.env.example` to `.env` and fill it in:

  ```bash
  cp .env.example .env
  # then edit .env with your OpenLibrary account credentials
  ```

  The `.env` file is loaded automatically when `pytest` starts. It is listed in `.gitignore` and is never committed.

  **Per-run overrides** are env vars passed on the command line. They beat `.env`:

  | ENV variable | Overrides | Example |
  |---|---|---|
  | `PROFILE` | active profile block | `PROFILE=debug pytest` |
  | `HEADLESS` | `headless` (boolean) | `HEADLESS=false pytest` |
  | `SLOW_MO` | `slow_mo` (number, ms) | `SLOW_MO=500 pytest` |
  | `OL_USERNAME` | OpenLibrary login email | `OL_USERNAME=... pytest` |
  | `OL_PASSWORD` | OpenLibrary login password | `OL_PASSWORD=... pytest` |

  The loader at `utils/config_loader.py` merges in this order:

  1. The `default` block (always loaded)
  2. The active profile (from `PROFILE`, falls back to `default`)
  3. Per-key env overrides (`.env` values and CLI values — CLI wins on conflict)

  ---

  ## Project Structure

  ```
  openlibrary-e2e-playwright/
  ├── pages/          # POM classes (Login, Search, Book, ReadingList)
  ├── tests/          # Pytest tests — one file per spec function + e2e flow
  ├── data/           # Test input data — JSON cases for parametrize
  ├── config/         # config.json with default / debug / ci profiles
  ├── utils/          # Helpers (performance, data_loader, config_loader)
  ├── conftest.py     # Pytest fixtures + session hooks
  ├── reports/        # Generated reports; final submission artifacts are committed
  ├── screenshots/    # Generated screenshots; final submission artifacts are committed
  ├── requirements.txt # Pinned dependency set for reproducible local runs
  ├── pyproject.toml  # Project info, dependencies, tool configs
  └── README.md
  ```                                                                                                                                                                                          

  ---

  ## Locators

  ### General strategy

  Locators are chosen in this order, from most stable to least:

  1. **Schema.org microdata** (`itemtype`, `itemprop`) — the strongest signal. OpenLibrary needs it for SEO (Google rich results) and will not remove it lightly.
  2. **Playwright Tier 1** (`get_by_role`, `get_by_label`) — accessibility-first, stable across CSS refactors.
  3. **Playwright Tier 4** (`get_by_text`) — for static text labels.
  4. **CSS class selectors** — only as a fallback when nothing else is exposed.

  ### Authentication — `LoginPage`

  Used once per pytest session by the `auth_storage_state` fixture.

  | What | Selector | Source |
  |---|---|---|
  | Form container (scoping) | `form.login` | CSS class |
  | Email input | `get_by_label("Email")` | Linked `<label for>` (Tier 1) |
  | Password input | `get_by_label("Password")` | Linked `<label for>` (Tier 1) |
  | Submit | `get_by_role("button", name="Log In")` | Accessible name (Tier 1) |
  | Error message | `div.error.ol-signup-form__info-box` | CSS class (no role available) |

  **Success indicator:** URL navigates away from `/account/login`. The form's hidden `redirect` field points to `/`, so the post-login URL is the base URL.

  **Failure indicator:** URL stays on `/account/login` AND the error box becomes visible. The text differs by reason (`Wrong password.`, `No account was found with this email.`) and is passed into `pytest.skip(...)` so the test report shows the actual cause.

  **Session artifact:** a single cookie named `session` on `openlibrary.org`. Playwright's `storage_state()` captures it automatically; `auth_storage_state` keeps it in memory only — never written to disk.

  ### Public Function Wrappers

  The Page Objects hold the implementation, and module-level wrappers expose
  standalone async functions with the required assignment names:

  | Function | Wrapper | Implementation |
  |---|---|---|
  | Search | `pages.search_page.search_books_by_title_under_year(...)` | `SearchPage.search_books_by_title_under_year(...)` |
  | Add books | `pages.book_page.add_books_to_reading_list(...)` | `BookPage.add_books_to_reading_list(...)` |
  | Assert count | `pages.reading_list_page.assert_reading_list_count(...)` | `ReadingListPage.assert_reading_list_count(...)` |

  The wrappers accept an explicit Playwright `page` because browser state is
  required to navigate. The POM classes still own selectors and page behavior.

  ### Function 1 — `search_books_by_title_under_year`

  **Navigation:** direct URL `/search?q={query}&mode=everything&sort=old&page={N}` — no UI typing. `sort=old` returns the oldest results first, which lets the loop stop scanning pages once a result's year exceeds `max_year`.

  **Selectors:**

  | What | Selector | Source |
  |---|---|---|
  | Result container | `li[itemtype$="Book"]` | Schema.org |
  | Book link (URL) | `[itemprop="name"] a[itemprop="url"]` | Schema.org (chained — tag-agnostic) |
  | Total pages | `ol-pagination[total-pages]` attribute | Web Component |

  **Year extraction — known limitation:**

  OpenLibrary's search results do **not** expose `datePublished` anywhere in the DOM — no `<meta>`, no `data-*` attribute, no JSON-LD. The year appears only as text: `"First published in 1965"`. We extract it from `.resultDetails span` and parse the 4-digit year with a regex.

  **Alternative considered:** OpenLibrary's JSON API at `https://openlibrary.org/search.json?q=...` returns `first_publish_year` as an integer — fully stable. Rejected because it bypasses the UI/POM architecture, which is 40% of the grade. Kept on record for future reference.

  ### Function 2 — `add_books_to_reading_list` (BookPage)

  **Navigation:** for each book URL, open the page directly. Each book page has exactly one "reading log dropper" widget (`.my-books-dropper`) — the only shelf control on the page.

  **Screenshots:** every add action saves a timestamped file under `screenshots/`, so repeat runs do not overwrite previous evidence.

  **Selectors:**

  | What | Selector | Source |
  |---|---|---|
  | Dropper container (scope) | `.my-books-dropper` | CSS class |
  | Primary action button (current shelf) | `get_by_role("button", name=<shelf label>)` scoped to `form.primary-action` | Accessible name (Tier 1) |
  | Open dropdown (chevron arrow) | `.generic-dropper__dropclick` | CSS class |
  | Add to "Want to Read" (dropdown) | `get_by_role("button", name="Want to Read")` scoped to `.read-statuses` | Accessible name (Tier 1) |
  | Add to "Already Read" (dropdown) | `get_by_role("button", name="Already Read")` scoped to `.read-statuses` | Accessible name (Tier 1) |
  | Remove from shelf (dropdown) | `get_by_role("button", name="Remove From Shelf")` scoped to `.read-statuses` | Accessible name (Tier 1) |

  **State signal:** the primary button's class tells us which shelf the book is on.

  - `.book-progress-btn.unactivated` → book is on no shelf. Primary button shows "Want to Read" (the default call-to-action).
  - `.book-progress-btn.activated` → book is on a shelf. The shelf name is the primary button's text (`Want to Read` / `Already Read` / `Currently Reading`).

  **Why two scoping containers (`form.primary-action` and `.read-statuses`)?**

  Two separate buttons in the DOM share the same accessible name. For example, "Want to Read" appears once as the primary call-to-action button, and once again as a shelf-switch button inside the dropdown panel. Without scoping, `get_by_role("button", name="Want to Read")` matches both at once and Playwright raises a strict-mode error. We split the search area by container:

  - `form.primary-action` — the primary call-to-action wrapper. One button only.
  - `.read-statuses` — the shelf-switcher panel inside the dropdown. Three "add" buttons plus one "remove" button.

  **Why fall back to CSS for the dropdown trigger?**

  The dropdown's chevron is an `<a class="generic-dropper__dropclick" href="javascript:;">` with no accessible name, no `aria-label`, no `aria-expanded`, no `title`, and no inner text. Playwright's Tier 1 selectors (`get_by_role`, `get_by_label`, etc.) all need an accessible name to filter on, and this element has none. CSS class is the only available handle. This is also a real accessibility gap on OpenLibrary's side; it is recorded in `ReadMeAIBugs.md`.

  **Why CSS for the scoping containers themselves?**

  The class names `primary-action` and `read-statuses` are *semantic* — they describe what the area is, not how it looks. They are less likely to be renamed in a redesign than visual classes (e.g. `.btn-blue-large`). There is no Tier 1 way to say "the form that is the primary action" because forms have no accessible role or name. In this case, a stable CSS class is the cleanest available choice.

  ### Function 3 — `assert_reading_list_count` (ReadingListPage)

  **Navigation:** one page load to `/account/books`. OpenLibrary redirects this to `/people/<username>/books`, so we do not need to know the username in advance — it works for whichever user is logged in.

  **Screenshot artifact:** `assert_reading_list_count` saves a timestamped screenshot before asserting, for both passing and failing count checks.

  **What we count:** the sum of three "status shelves" on the landing page: **Currently Reading + Want to Read + Already Read**. Loans (active library loans from Internet Archive) and Lists (user-curated lists) are deliberately *not* counted — they are not reading-list shelves. This matches the random behaviour of function 2, which adds each book to WTR or AR at random; counting only one shelf would fail whenever a book happened to land on the other.

  **Selectors:**

  | What | Selector | Source |
  |---|---|---|
  | Currently Reading heading | `get_by_role("heading", name=re.compile(r"^Currently Reading(?:$\| \()"))` | Accessible name (Tier 1) |
  | Want to Read heading | `get_by_role("heading", name=re.compile(r"^Want to Read(?:$\| \()"))` | Accessible name (Tier 1) |
  | Already Read heading | `get_by_role("heading", name=re.compile(r"^Already Read(?:$\| \()"))` | Accessible name (Tier 1) |

  **State signal:** the count is part of the heading text. We read `inner_text` of the heading and run a single regex `\(([\d,]+)\)` to extract the number, then strip any thousands-separator before `int()`. If the regex finds no match, the count is `0`.

  **Why heading-role beats every alternative:**

  Each shelf on the landing page is shown in two places at once: the desktop carousel section (inside an `<h2>`) and the mobile sidebar (inside a `<div>`, no heading). `get_by_role("heading", ...)` matches the desktop version only, because the mobile copy is not a heading. That gives us exactly one element per shelf, no strict-mode collision, no class-scoped fallback, no reliance on hidden-on-desktop mobile DOM.

  Compare this with two alternatives that look attractive but fail:

  - `get_by_role("link", name=re.compile(r"^Want to Read"))` — collides because both copies (desktop *and* mobile) are `<a>` links. Strict-mode error.
  - `.mybooks-menu-mobile a[name="want-to-read"]` — works, but only because we hard-scope to the mobile sidebar. It reads from a region that is `display: none` on desktop. Less robust if OpenLibrary ever stops rendering the mobile sidebar on wide viewports.

  **Why the regex is `^Label(?:$| \()` and not just `^Label`:**

  The shelf heading text is `Label (N)` when the shelf has items, or just `Label` when it is empty (this happens for Currently Reading when there are zero books — the count is not printed in that case). The regex accepts both: end-of-name, or a space followed by an opening paren. This avoids false matches on neighbours such as "Currently Reading Stats" or any future heading that shares the same prefix.

  **Why count from the heading text and not from the DOM book items:**

  Counting `.book.carousel__item` elements on the landing page is tempting but wrong. The carousel is JS-paginated and only renders the first 6 or so items, even when the shelf has 13. The number in the heading is server-rendered from the database and is the true total. Using it costs one page load, not three (one per shelf), and never under-counts.

  **Why a missing heading maps to `0` instead of an error:**

  Defensive default. If OpenLibrary ever stops rendering a shelf section that has zero items, our code logs a warning and returns `0` for that shelf, instead of raising. The total stays correct, and the warning gives us a signal to update the locator if the page layout changes.

  ---
  
  ## Architecture

  The framework has four layers:

  | Layer | Files | Role |
  |---|---|---|
  | Page Objects | `pages/` | One class per page. Each holds `page` and `base_url` only. |
  | Tests | `tests/` | One file per spec function plus `test_e2e_flow.py` for the full chain. |
  | Helpers | `utils/` | `performance.py`, `data_loader.py`, `config_loader.py`. |
  | Fixtures + hooks | `conftest.py` | Session browser, `auth_storage_state`, per-test page contexts, and the `pytest_sessionfinish` hook that writes the perf report. |

  **No POM base class.** Every page class shares the same two fields (`page`, `base_url`). A base class would save a few lines and add one indirection. Kept flat.

  **Data flow.** JSON files in `data/` feed `@pytest.mark.parametrize` through `utils/data_loader.py`. The same helper serves all three data-driven tests (search, reading list, performance).

  **Performance coverage.** `tests/test_performance.py` measures search, book detail, and reading-list targets using the spec thresholds (`3000 / 2500 / 2000`). `tests/test_e2e_flow.py` also measures those three page types inside the full search -> add -> assert flow.

  **Auth.** One login per session. Playwright's `storage_state()` is captured in memory (`auth_storage_state` fixture) and injected into a fresh `BrowserContext` for every test that needs login. Tests stay isolated but already signed in.

  **Reporting.** Two artifacts under `reports/`: `report.html` from pytest-html, and `performance_report.json` written once at session end. The folders are gitignored for normal local churn, but final submission artifacts are force-added.

  ---
                                                                                                                                                                                               
  ## Limitations

  - **Config merge depth.** Profile merging is shallow (`{**default, **active}`). A profile that wants to override a single key inside `thresholds` must restate all three keys. No profile in this project needs that, so the loader stays simple. A deeper merge would be one `if isinstance(v, dict)` in the loader if a future profile ever needs it.

  - **No reading-list cleanup.** Function 2 adds books; the account count only goes up over runs. The idempotent `add_to_shelf` prevents duplicates, and the data-driven + E2E tests use delta-based assertions (`0 <= delta <= len(urls)`), so the suite passes either way. A cleanup mode is in **Open Decisions** below.

  - **Single browser (Chromium).** The framework launches `playwright_instance.chromium.launch(...)` only. Firefox and WebKit are reachable via Playwright but not parameterised here. A cross-browser sweep would multiply runtime, so it is left out of this iteration.

  - **Sequential test run.** All tests share one event loop (forced via `asyncio_default_*_loop_scope = "session"` — see **Decisions Made** below). Tests are isolated at the `BrowserContext` level but run one at a time. `pytest-xdist` would need a different loop strategy and is not wired up.

  - **External availability.** Tests hit live `openlibrary.org`. Outages, rate limits, or layout changes on OpenLibrary's side will fail the run. There is no mock layer.

  - **CAPTCHA on anonymous search.** OpenLibrary redirects anonymous headless browsers to `/verify_human` on the search endpoint. The search tests therefore use the authenticated `page` fixture (which passes the challenge) instead of `anonymous_page`. If CAPTCHA were ever extended to authenticated traffic, the framework would need a real challenge-handling strategy.

  ---
                                                                                                                                                                                               
  ## Decisions Made

  These choices were made early. The reason and the trade-off are listed for transparency:

  | Area | Decision | Reason | Trade-off |
  |---|---|---|---|
  | Async API | Use Playwright async API (`playwright.async_api`) | The four required function signatures in the spec are all `async def`. The spec's example also calls them with `await`. Choosing sync would force changing the signatures and break the contract. |
  | Test runner | Add `pytest` as the test runner | The spec does not ask for a runner. Pytest covers three grading items: Data-Driven (10%) — `parametrize` reads test cases from JSON files; Robustness (30%) — fixtures keep each test clean from the others; Reports (5%) — `pytest-html` produces the run report. The four required functions stay simple, and pytest only calls them from `tests/`. | Adds a dependency the spec did not ask for. |
  | Async fixture setup | Raw `async_playwright` in `conftest.py` (not the `pytest-playwright` plugin) | The official `pytest-playwright` plugin is sync-only. Our signatures need async, so a small custom `conftest.py` with async fixtures matches the contract and gives full control. | I write the fixture code myself, about 15 lines. The official plugin includes some extras like auto-screenshots on fail and a `--browser firefox` CLI flag. I will add these only if I need them. |
  | Configuration storage | Single JSON file at `config/config.json` | One source of truth. Booleans and numbers keep their real types (no string parsing for the primary config). |
  | Profiles | Profile blocks (`default`, `debug`, `ci`) inside the same JSON file | All profiles are visible in one view. The active profile is chosen via the `PROFILE` env var. Merging happens at load time: `{**default, **active}`. | A reviewer scanning only the folder tree may not see the profiles at first — the README points them in. |
  | Runtime overrides | `.env` file for stable values + CLI environment variables for per-run overrides. CLI takes priority. | The reading list functions need a logged-in account, so credentials must live outside git. Stable values like credentials and a default profile go in `.env` so they are not typed every time. CLI env vars (e.g. `PROFILE=debug pytest`) override `.env` for one-off changes, because `python-dotenv` does not replace env vars that are already set. | Adds one dependency: `python-dotenv`. |
  | Test data format | JSON files in `data/` (e.g., `data/search_cases.json`) | Already a dependency. Consistent with the config format. Each test case includes a `description` field used for readable IDs in pytest's report. Plays well with `@pytest.mark.parametrize`. | JSON has no comments — the `description` field replaces them. |
  | Test file split | Split by function: `test_search.py`, `test_reading_list.py`, `test_performance.py`, plus `test_e2e_flow.py` for the full integration scenario | Each file groups tests for one of the four required functions. The e2e flow file runs all four in sequence as a single end-to-end scenario. | More files. Clear file names keep them easy to find. |
  | Function placement | Functions 1–3 have standalone module-level wrappers and POM-backed implementations. Function 4 is a module-level utility in `utils/performance.py`. | The reviewer-facing API exposes the required function names as standalone `async def`s. The implementation still lives in POM classes because selectors and browser interactions belong with page-specific behavior. The wrappers accept `page` explicitly, matching the executable sample in the assignment PDF. | A thin wrapper layer adds a few lines, but removes ambiguity around the required public function shape. |
  | Authentication strategy | Log in once per session, capture Playwright's `storage_state` in memory, then inject it into a fresh browser context for every test that needs login | Each test gets a clean browser context, but already signed in. Tests do not share DOM or cookies, so they stay independent and the order they run in does not matter. This is the pattern recommended by [Playwright's own auth docs](https://playwright.dev/python/docs/auth#reusing-signed-in-state). Two fixtures are exposed: `page` is pre-authenticated; `anonymous_page` is a clean context used by the anonymous performance cases. Search tests use the authenticated `page` because OpenLibrary's search endpoint redirects anonymous headless browsers to a `/verify_human` CAPTCHA challenge. The login UI runs only once per `pytest` run. If login fails (network or bad credentials), the affected tests are skipped with `pytest.skip` instead of crashing. | Login itself is required by OpenLibrary for the reading list pages, not by our framework — credentials are supplied via `.env` (template at `.env.example`). If OpenLibrary changes its login page, the session fixture fails once at the start of the run, instead of every test failing on its own. |
  | Performance report aggregation | Collect every result in memory during the run, then write `reports/performance_report.json` once at the end (via a `pytest_sessionfinish` hook in `conftest.py`) | The spec asks for one JSON file with all results. Collecting in memory and writing once is simpler than writing on every call: a single disk write, no risk of two tests writing at the same time, and no extra I/O while tests are running. | If `pytest` crashes before the end, the file is not written. Acceptable — a partial report is not necessarily more useful than no file. |
  | Reporting toolchain | `pytest-html` for the run report + a `pytest_sessionfinish` hook for the perf JSON. | pytest-html is a one-line addition: a dep plus `--html=reports/report.html --self-contained-html` in `addopts`. Self-contained means a single HTML file that opens anywhere with no asset folder. The custom JSON aggregator is still needed because the spec asks for a specific format pytest-html does not produce. | Two artifacts instead of one. Both live under `reports/`. |
  | Artifacts under `reports/` | Both reports (`report.html`, `performance_report.json`) live under `reports/`; screenshots live under `screenshots/`. | One folder for CI/report upload, one folder for visual evidence. The directories are ignored for normal local churn, and the final submission artifacts are force-added to git. | A fresh run creates new timestamped screenshots, so old evidence may remain until manually cleaned. |
  | `pytest-asyncio` loop scope | Both `asyncio_default_fixture_loop_scope` and `asyncio_default_test_loop_scope` are set to `"session"` in `pyproject.toml` | Playwright objects (`Page`, `BrowserContext`) are bound to the event loop on which they were created. With the default mix (session loop for fixtures, function loop for tests), a page created in a session-scoped fixture and used inside a test hangs forever -- the awaitable is registered on the wrong loop's queue and never resolves, with no error. Forcing both scopes to `"session"` keeps the whole run on one loop. | All tests share one event loop, so test order can matter slightly more (a misused session-scoped fixture could leak state across tests). Mitigation: every test gets a fresh `BrowserContext`, so DOM and cookies do not leak. |

  ---

  ## Open Decisions

  These decisions are still open. They will be made when needed during the work. Listed here to be open about what is not yet decided:

  | Area | Pending decision |
  |---|---|
  | CI/CD | Optional extra. May add a GitHub Actions workflow. |
  | Reading list cleanup mode | Planned: an opt-in CLI flag (e.g. `--clean-reading-list` or env var `CLEAN_READING_LIST=true`) that, when set, wipes every shelf (Currently Reading + Want to Read + Already Read) **before** the run starts and again **after** it ends. Default behaviour stays as today: no cleanup, tests rely on the idempotency of `add_to_shelf`. Rationale: the project's OL account is a throwaway used only for this exercise, so a full wipe is safe when requested, and it produces a fully deterministic starting state for data-driven and E2E runs. Implementation will be a `pytest_addoption` + a session-scoped fixture that iterates the three shelf pages and calls `remove_from_shelf` per book, gated on the flag. To be added after function 4 and the data-driven refactor are in place. |

  ---

  ## AI Bug Analysis                                                                                                                                                                           
  
  See [`ReadMeAIBugs.md`](./ReadMeAIBugs.md) for the results of the bug analysis exercise.

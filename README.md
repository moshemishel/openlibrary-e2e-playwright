 # OpenLibrary E2E Automation

  End-to-end automation framework for [openlibrary.org](https://openlibrary.org), built with **Playwright** and **Pytest** in Python.

  > Status: Work in progress.

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
  - After the run, save all results to a file called `performance_report.json`.

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
  | 3 | Run report | One of: Allure / HTML / JUnit XML |
  | 4 | `performance_report.json` | Created by task #4 |
  | 5 | `ReadMeAIBugs.md` | Bug analysis exercise — at least 3 bugs, each with explanation and fix |

  ---

  ## Tech Stack                                                                                                                                                                                
  
  | Concern | Choice |
  |---|---|
  | Language | Python 3.11+ |
  | Browser automation | [Playwright](https://playwright.dev/python/) |
  | Test framework | [Pytest](https://docs.pytest.org/) + `pytest-asyncio` |
  | Linting / Formatting | [Ruff](https://docs.astral.sh/ruff/) |
  | Reporting | _Not decided yet. Will start with Playwright's built-in HTML report. May add Allure later if there is time. JUnit XML is always available via pytest._ |

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

  # Install dependencies (project + dev tools)
  pip install -e ".[dev]"
                                                                                                                                                                                               
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
  ├── pages/          # POM classes
  ├── tests/          # Pytest tests
  ├── data/           # Test input data (JSON)
  ├── config/         # Configs, profiles, thresholds
  ├── utils/          # Helpers (performance, logging, files)
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

  ---
  
  ## Architecture
  
  > _Will be added after the POM design is done. Will cover: page classes, base class, how data is loaded, how config works, and how reports are made._

  ---
                                                                                                                                                                                               
  ## Limitations

  - **Config merge depth.** Profile merging is shallow (`{**default, **active}`). A profile that wants to override a single key inside `thresholds` must restate all three keys. No profile in this project needs that, so the loader stays simple. A deeper merge would be one `if isinstance(v, dict)` in the loader if a future profile ever needs it.

  ---
                                                                                                                                                                                               
  ## Decisions Made

  These choices were made early. The reason and the trade-off are listed for transparency:

  | Area | Decision | Reason | Trade-off |
  |---|---|---|---|
  | Async API | Use Playwright async API (`playwright.async_api`) | The four required function signatures in the spec are all `async def`. The spec's example also calls them with `await`. Choosing sync would force changing the signatures and break the contract. |
  | Test runner | Add `pytest` as the test runner | The spec does not ask for a runner. Pytest helps me with two of the grading items so far: Data-Driven (10%) — `parametrize` reads test cases from a JSON file; Robustness (30%) — fixtures keep each test clean from the others. The reporting choice is still open, but pytest leaves the option open for native JUnit XML, HTML, or Allure when I decide. The four required functions stay simple, and pytest only calls them from `tests/`. | Adds a dependency the spec did not ask for. |
  | Async fixture setup | Raw `async_playwright` in `conftest.py` (not the `pytest-playwright` plugin) | The official `pytest-playwright` plugin is sync-only. Our signatures need async, so a small custom `conftest.py` with async fixtures matches the contract and gives full control. | I write the fixture code myself, about 15 lines. The official plugin includes some extras like auto-screenshots on fail and a `--browser firefox` CLI flag. I will add these only if I need them. |
  | Configuration storage | Single JSON file at `config/config.json` | One source of truth. Booleans and numbers keep their real types (no string parsing for the primary config). |
  | Profiles | Profile blocks (`default`, `debug`, `ci`) inside the same JSON file | All profiles are visible in one view. The active profile is chosen via the `PROFILE` env var. Merging happens at load time: `{**default, **active}`. | A reviewer scanning only the folder tree may not see the profiles at first — the README points them in. |
  | Runtime overrides | `.env` file for stable values + CLI environment variables for per-run overrides. CLI takes priority. | The reading list functions need a logged-in account, so credentials must live outside git. Stable values like credentials and a default profile go in `.env` so they are not typed every time. CLI env vars (e.g. `PROFILE=debug pytest`) override `.env` for one-off changes, because `python-dotenv` does not replace env vars that are already set. | Adds one dependency: `python-dotenv`. |
  | Test data format | JSON files in `data/` (e.g., `data/search_cases.json`) | Already a dependency. Consistent with the config format. Each test case includes a `description` field used for readable IDs in pytest's report. Plays well with `@pytest.mark.parametrize`. | JSON has no comments — the `description` field replaces them. |
  | Test file split | Split by function: `test_search.py`, `test_reading_list.py`, `test_performance.py`, plus `test_e2e_flow.py` for the full integration scenario | Each file groups tests for one of the four required functions. The e2e flow file runs all four in sequence as a single end-to-end scenario. | More files. Clear file names keep them easy to find. |
  | Function placement | Functions 1–3 are methods on POM classes. Function 4 is a module-level utility in `utils/performance.py`. | The function signatures lead the design. Functions 1–3 do not receive `page` as a parameter, so they need stored state — a class fits well. Function 4 does receive `page`, so it does not need state — a module-level function fits well. This keeps page actions in `pages/` and shared helpers in `utils/`. | None. The split follows directly from the spec's signatures. |
  | Authentication strategy | Log in once per session, capture Playwright's `storage_state` in memory, then inject it into a fresh browser context for every test that needs login | Each test gets a clean browser context, but already signed in. Tests do not share DOM or cookies, so they stay independent and the order they run in does not matter. This is the pattern recommended by [Playwright's own auth docs](https://playwright.dev/python/docs/auth#reusing-signed-in-state). Two fixtures are exposed: `page` is pre-authenticated; `anonymous_page` is a clean context for tests that do not need login (search, performance). The login UI runs only once per `pytest` run. If login fails (network or bad credentials), the affected tests are skipped with `pytest.skip` instead of crashing. | Login itself is required by OpenLibrary for the reading list pages, not by our framework — credentials are supplied via `.env` (template at `.env.example`). If OpenLibrary changes its login page, the session fixture fails once at the start of the run, instead of every test failing on its own. |
  | Performance report aggregation | Collect every result in memory during the run, then write `performance_report.json` once at the end (via a `pytest_sessionfinish` hook in `conftest.py`) | The spec asks for one JSON file with all results. Collecting in memory and writing once is simpler than writing on every call: a single disk write, no risk of two tests writing at the same time, and no extra I/O while tests are running. | If `pytest` crashes before the end, the file is not written. Acceptable — a partial report is not necessarily more useful than no file. |
  | `pytest-asyncio` loop scope | Both `asyncio_default_fixture_loop_scope` and `asyncio_default_test_loop_scope` are set to `"session"` in `pyproject.toml` | Playwright objects (`Page`, `BrowserContext`) are bound to the event loop on which they were created. With the default mix (session loop for fixtures, function loop for tests), a page created in a session-scoped fixture and used inside a test hangs forever -- the awaitable is registered on the wrong loop's queue and never resolves, with no error. Forcing both scopes to `"session"` keeps the whole run on one loop. | All tests share one event loop, so test order can matter slightly more (a misused session-scoped fixture could leak state across tests). Mitigation: every test gets a fresh `BrowserContext`, so DOM and cookies do not leak. |

  ---

  ## Open Decisions

  These decisions are still open. They will be made when needed during the work. Listed here to be open about what is not yet decided:

  | Area | Pending decision |
  |---|---|                                                                                                                                                                                    
  | Reporting tool | Playwright HTML built-in vs Allure (added later if time) |
  | CI/CD | Optional extra. May add a GitHub Actions workflow. |

  ---

  ## AI Bug Analysis                                                                                                                                                                           
  
  See [`ReadMeAIBugs.md`](./ReadMeAIBugs.md) for the results of the bug analysis exercise.
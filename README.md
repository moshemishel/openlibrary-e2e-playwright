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

  **Override single keys** with dedicated env vars (no `.env` file needed):

  | ENV variable | Overrides | Example |
  |---|---|---|
  | `HEADLESS` | `headless` (boolean) | `HEADLESS=false pytest` |
  | `SLOW_MO` | `slow_mo` (number, ms) | `SLOW_MO=500 pytest` |

  The loader at `utils/config_loader.py` merges in this order:

  1. The `default` block (always loaded)
  2. The active profile (from `PROFILE`, falls back to `default`)
  3. Per-key env overrides (highest priority)

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
  
  ## Architecture
  
  > _Will be added after the POM design is done. Will cover: page classes, base class, how data is loaded, how config works, and how reports are made._

  ---
                                                                                                                                                                                               
  ## Limitations

  > _Will list known limits as they come up during development._

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
  | Runtime overrides | Environment variables passed in the command (no `.env` file) | No secrets in this project, so a `.env` file is not needed. Avoids the `python-dotenv` dependency and keeps `pytest` working out of the box. | If many overrides are needed at once, the command line gets long — easy to add a `.env` later. |
  | Test data format | JSON files in `data/` (e.g., `data/search_cases.json`) | Already a dependency. Consistent with the config format. Each test case includes a `description` field used for readable IDs in pytest's report. Plays well with `@pytest.mark.parametrize`. | JSON has no comments — the `description` field replaces them. |
  | Test file split | Split by function: `test_search.py`, `test_reading_list.py`, `test_performance.py`, plus `test_e2e_flow.py` for the full integration scenario | Each file groups tests for one of the four required functions. The e2e flow file runs all four in sequence, matching the spec's "tear e2e flow" language. | More files. Clear file names keep them easy to find. |

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
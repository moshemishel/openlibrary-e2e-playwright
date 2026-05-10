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
  git clone https://github.com/MoshMish/openlibrary-e2e-playwright.git
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

  ## Project Structure

  ```
  openlibrary-e2e-playwright/
  ├── pages/          # POM classes
  ├── tests/          # Pytest tests
  ├── data/           # Test input data (JSON / YAML / CSV)
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
                                                                                                                                                                                               
  ## Open Decisions

  These decisions are still open. They will be made when needed during the work. Listed here to be open about what is not yet decided:

  | Area | Pending decision |
  |---|---|                                                                                                                                                                                    
  | Reporting tool | Playwright HTML built-in vs Allure (added later if time) |
  | Async setup | Use `pytest-playwright` (gives a `page` fixture) or use raw `async_playwright` in `conftest.py` |
  | Data format | JSON vs YAML vs CSV for test inputs |
  | Configuration | Where `BASE_URL`, `HEADLESS`, and thresholds will live (env vs config files) |
  | Profiles | How to load different settings (URL, headless, slow_mo, etc.) for different run modes — for example, `debug` vs `fast` on local, or `local` vs `ci`. |
  | Test file split | One `test_e2e_flow.py` vs separate files (search / reading list / performance) |
  | CI/CD | Optional extra. May add a GitHub Actions workflow. |

  ---

  ## AI Bug Analysis                                                                                                                                                                           
  
  See [`ReadMeAIBugs.md`](./ReadMeAIBugs.md) for the results of the bug analysis exercise.
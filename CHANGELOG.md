# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-01-18

### Breaking Changes

- **Python 3.10+ required** - Dropped support for Python 3.9 and earlier
- Some internal APIs may have changed (scraper utilities, helper functions)

### Fixed

- **`get_stock()`** - Complete rewrite to handle FinViz DOM changes
  - Now returns 90+ data points (was returning empty or partial data)
  - Updated selectors for new header structure (`quote-header_ticker-wrapper`)
  - Fixed financial data extraction from `snapshot-td2` cells
  - Properly handles Volatility split into Week/Month components

- **`Screener`** - Fixed table parsing and header extraction
  - Headers now correctly extracted from `<th>` elements (was looking for `<td>`)
  - Table data properly aligned with headers
  - All table types working: Overview, Valuation, Financial, Ownership, Performance, Technical

- **`get_news()`** - Updated timestamp parsing
  - Handles new "Today HH:MMAM/PM" format
  - Handles "Mon-DD HH:MMAM/PM" format
  - Returns consistent YYYY-MM-DD HH:MM format

- **`get_insider()`** - Updated for new table structure
  - Supports new `styled-table-new` class
  - Extracts headers from `thead th` elements
  - All insider trading fields correctly parsed

- **`get_analyst_price_targets()`** - Updated selectors
  - Works with new `js-table-ratings` table class
  - Correctly parses analyst, rating, and price target data

### Added

- Comprehensive test suite with real API testing
  - `test_stock.py` - Tests for all stock-related functions
  - `test_screener.py` - Tests for Screener functionality
  - `test_integration.py` - End-to-end workflow tests
  - Rate limiting to be respectful to FinViz servers

- Development dependencies in pyproject.toml
  - pytest for testing
  - ruff for linting
  - mypy for type checking

### Changed

- Updated all dependencies to latest versions
- Modernized pyproject.toml configuration
- Improved error handling in scraping functions

### Developer Notes

This release addresses all scraping failures caused by FinViz website updates in late 2024. The DOM structure changed significantly:

- Headers moved from `<td>` to `<th>` elements
- New CSS classes: `styled-table-new`, `snapshot-td2`, `quote-header_ticker-wrapper`
- New timestamp formats in news section
- Restructured analyst ratings table

---

## [1.4.6] - 2023-10-xx

_Last release before v2.0 rewrite_

### Known Issues (Fixed in v2.0)

- `get_stock()` returning empty or incomplete data
- Screener returning empty results
- News timestamps not parsing correctly
- Insider trading data extraction broken

---

## [1.4.0] - 2022-xx-xx

- Added async support for Screener (`request_method="async"`)
- Various bug fixes

---

## [1.3.0] - 2021-xx-xx

- Added `get_analyst_price_targets()` function
- Improved error handling

---

## [1.0.0] - 2019-xx-xx

- Initial public release
- Core functions: `get_stock()`, `get_news()`, `get_insider()`
- Screener with filter support
- Portfolio management
- Chart downloading

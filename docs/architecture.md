# Architecture

The browser hosts a typed React dashboard. FastAPI owns authentication, validation, parsing, cost analytics, reports, and persistence. PostgreSQL is private to Compose. Uploaded Terraform is held in memory, limited to UTF-8 `.tf` files of 1 MB, parsed as data, and never executed.


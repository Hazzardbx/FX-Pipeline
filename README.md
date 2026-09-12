# FX-Pipeline

End-to-end idempotent data pipeline for daily currency exchange rates (ECB reference rates via the Frankfurter API).

## Status: Complete

- [x] Extract — fetch rates from Frankfurter API, with retry + exponential backoff on server errors
- [x] Transform
- [x] Load (idempotent upsert)
- [x] Orchestrate
- [x] Serve — running locally (Streamlit), reading from AWS RDS
- [ ] Serve — cloud deployment (Streamlit Community Cloud)

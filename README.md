# FX-Pipeline

End-to-end idempotent data pipeline for daily currency exchange rates (ECB reference rates via the Frankfurter API).

## Status: In development

- [x] Extract — fetch rates from Frankfurter API, with retry + exponential backoff on server errors
- [ ] Transform
- [ ] Load (idempotent upsert)
- [ ] Orchestrate
- [ ] Serve (Streamlit)
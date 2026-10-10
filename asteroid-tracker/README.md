# Asteroid Tracker

Retrieves near-Earth object data from NASA's NeoWs API, sorts by size, shows distances, plots graphs, and serves an interactive dashboard.

## Run
```bash
pip install -r requirements.txt
export NASA_API_KEY=your_key   # optional, falls back to DEMO_KEY
python tracker.py              # CLI summary
streamlit run app.py           # dashboard
pytest                         # tests
```

## Roadmap
- [ ] Cache API responses to disk
- [ ] Orbit/velocity analysis
- [ ] Hazard-risk scoring
- [ ] Deploy dashboard (Streamlit Community Cloud)

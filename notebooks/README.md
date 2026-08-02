# Notebooks

This project is built as runnable Python modules rather than exploratory notebooks, so every
result in `docs/` and `governance/model_card.md` is reproducible from the command line
(`python -m python.run_pipeline --stage all`) and covered by `tests/`. There is deliberately no
throwaway notebook duplicating that logic.

If you want an interactive, cell-by-cell view of any stage for exploration:

```bash
pip install jupyterlab
jupyter lab
```

then open a new notebook and import directly from the package, for example:

```python
from python.features import feature_engineering
from python.models import demand_forecasting

feature_engineering.run()
result = demand_forecasting.run()
result["metrics"]
```

Every module under `python/` is designed to be imported this way -- each `run()` function returns
a plain dict of results, with no notebook-only state.

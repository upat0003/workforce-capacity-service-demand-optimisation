# Report Navigation

The report uses a fixed left-hand navigation rail (see any screenshot in
`powerbi/Screenshots/`), consistent across all 8 pages, plus persistent filter chips
(Period, Region, Model version) top-right on every page.

## Page order and purpose

| # | Page | Primary user | Jumps to (drill-through) |
|---|---|---|---|
| 1 | Workforce Executive Overview | Service Delivery Executive | Region bar -> Capacity and Utilisation (filtered) |
| 2 | Demand Forecast | Workforce Planning Lead | Region bar -> that region's own trend |
| 3 | Capacity and Utilisation | Workforce Planning Lead / Regional Coordinator | Heatmap cell -> Scheduling Recommendations (region/week) |
| 4 | Service Backlog | Service Delivery Executive / Regional Coordinator | Bar segment -> underlying request list |
| 5 | Scheduling Recommendations | Regional Coordinator | Region bar -> region's shift-recommendation detail |
| 6 | Workforce Fairness | People & Culture Lead / Model Risk Reviewer | None (aggregate-only by design) |
| 7 | Service Outcomes | Quality & Safety Lead | Cancellation-reason segment -> cancellation detail table |
| 8 | Data Quality and Governance | Data Platform Engineer / Model Risk Reviewer | Failing rule -> affected dataset's row-level detail |

## Cross-page filter behaviour

- Selecting a region on any page filters that page's visuals only (chip row shows "Region: All"
  by default); a coordinator can pin a single region via the Region filter chip to focus their
  session on their own patch.
- The Period chip defaults to the latest 12 months and can be narrowed to a rolling window.
- The Model chip records which model version produced the forecasts/predictions on screen, so a
  screenshot or export is always traceable to a specific entry in
  `artifacts/models/registry.json`.

## Interaction contract (applies to every page)

Every chart on every page carries: a colour-coded legend directly beneath it, labelled axes, one
hover-tooltip callout anchored to the most relevant data point, a cross-filter highlight on the
selected mark, and the persistent filter-chip row described above. See
`powerbi/dashboard_specification.md` for the page-by-page detail and
`powerbi/Templates/render_mockups.py` for the reproducible rendering logic.

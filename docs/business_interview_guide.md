# Business Interview Guide

How to talk about this project with a hiring manager or panel from an operations, analytics or
governance background (not necessarily technical).

## "What problem does this solve?"

"Front-line service scheduling in a lot of organisations -- aged care, disability support, field
services, councils -- is still done reactively: coordinators fill next week's roster based on
what happened last week, with no forward visibility into demand. That produces overtime,
backlog, missed service commitments and uneven workloads. This project builds the forecasting,
prediction and scheduling-support tools to fix that, plus the governance to make sure it's used
responsibly."

## "What would this be worth to a real organisation?"

"I framed the targets the way a workforce planning lead would put them to a budget committee:
10-20% less overtime, 15% less backlog, 10% better service-level performance, 20% less manual
scheduling time, and more balanced workloads -- each tied to a baseline computed from the data,
not an assumed number. Full framing is in `docs/business_case.md`."

## "Why should I trust an AI system to help schedule people?"

"It doesn't schedule anyone automatically -- every recommendation goes through a human
coordinator. I built that in deliberately: shift recommendations, skill-matching, and the
scheduling optimiser are all decision support, and every override a coordinator makes is logged
with a reason. That's a governance choice, not an afterthought."

## "How do you know it's fair to staff?"

"I built a specific fairness check that compares workload and overtime across gender and age-band
groups -- attributes that are never used to build the schedule in the first place. It runs on
every cycle, with a hard rule to suppress any group small enough that reporting on it would risk
identifying an individual. In the current run, there's no material gap."

## "What happens when the data or the model goes wrong?"

"There's a monitoring layer that checks data quality (7 rules), model drift, and fairness on
every run, and it's designed to surface real problems, not just look green. As an example, the
data-quality check in the current run found that more than half of a certification sample had
expired -- that's a genuine finding a real organisation would want to act on, and it shows the
control catching something rather than just ticking a box."

## "What's your process for building something like this?"

"I started from the business outcomes -- what would actually move overtime, backlog and service
levels -- and worked backwards to the data and models needed to support them, rather than
starting from a model and looking for a use for it. I documented assumptions, baselines and
limitations honestly throughout, including where a model's performance is genuinely modest, because
that's what a credible operational deployment requires."

## "How would you introduce this to a team that's nervous about AI?"

"Slowly and visibly. The adoption plan in `docs/business_case.md` starts with a shadow-mode pilot
in two regions -- recommendations are shown, nothing changes automatically -- with coordinator
training before any rollout, and a monitoring review every week for the first quarter. People need
to see it get things right (and see how disagreements are handled) before it earns trust."

## Sound bites

- "Forecast-led planning instead of reactive scheduling."
- "Every model output is decision support -- a human always approves."
- "Fairness and data-quality checks run every cycle, not once."
- "I'd rather show an honest, modest metric than an inflated one."

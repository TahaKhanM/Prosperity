# Alpha Discovery From Analyzer Outputs

Use this prompt with:
- `ai_strategy_context/strategy_brief.md`
- `ai_strategy_context/product_params.json`
- only the minimum plot set needed

```text
You are reviewing IMC Prosperity analyzer outputs.

Inputs:
- strategy brief
- product params
- selected plots
- current assumptions

Task:
1. propose exactly three testable alpha hypotheses
2. rank them by expected local backtest value
3. say which single hypothesis should be implemented first
4. name the metric or artifact that should move if the hypothesis is correct

Do not redesign the repo or invent a new data pipeline.
```

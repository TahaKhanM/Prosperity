# event_spike_response_strategy_spec

Use when the strategy should stay mostly passive until a discrete spike or event
state appears, then react with controlled taking or recycling.

Required sections for a generated candidate:
- event detector
- event action block
- cooldown / reset block
- inventory escape logic
- traderData event state

Primary validation target:
- better performance around worst timestamps and spike windows

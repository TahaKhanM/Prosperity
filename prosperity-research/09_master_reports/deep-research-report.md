# New Edge Search for IMC Prosperity 4 Round 1

## Executive research synthesis

The most important conclusion from this investigation is that the most credible breakout is **not** another fair-value variant, another threshold sweep, or another small inventory overlay on the current Pepper carry baseline. The strongest path to materially better performance is a **different state-policy decomposition**: keep a slow-moving base posture where warranted, but learn or infer a separate **tactical execution gate** that decides *when not to quote, when to quote one-sided, when to recycle, and when to switch from passive to aggressive behaviour* based on very short-horizon book state, spread shape, and recent sequence motifs. That conclusion fits the user-provided search frontier: Pepper’s core long-carry posture appears directionally correct, but many realised fills have weak or negative short-horizon edge; hosted-winner behaviour did not port cleanly; and the remaining edge likely lives in tactical timing, fill selection, and state-dependent execution rather than wholesale replacement of the base posture. fileciteturn0file5 fileciteturn0file2

The official Round 1 setup makes that especially plausible. The products are only entity["organization","IMC","trading firm"] Prosperity 4’s ASH_COATED_OSMIUM and INTARIAN_PEPPER_ROOT, both with position limits of 80; Pepper is explicitly framed as relatively steady and predictable, while Osmium is framed as more volatile and possibly patterned. The exchange is a discrete, per-iteration limit-order environment with temporary resting quotes and trader state carried forward through `traderData`, which means execution design and state compression matter unusually much relative to conventional continuous-time finance abstractions. fileciteturn0file0 fileciteturn0file1

The guide repository on entity["company","GitHub","software platform"] is useful as a *framework map* rather than an alpha source. Its transferable contribution is the separation of a trading system into research/alpha, execution, inventory/risk, and software/backtesting; its most practical idea for Round 1 is the insistence that execution should be decomposed into **take, clear, make** rather than treated as one blurred “place some orders” step. The repo itself also emphasises that copying old code is not enough and that deeper adaptation is necessary when the challenge shifts. citeturn8view1turn8view0turn31view0

Across previous public Prosperity repos, the most reusable abstractions were not specific thresholds but four broader principles:  
first, **find the low-noise fair proxy used by the bots**, such as wall-mid or large-volume filtered market-maker prices; second, **separate taking, clearing, and making** in code and in research; third, **treat inventory as a state variable that changes quote choice, not just size**; and fourth, **use website or higher-fidelity replay validation when the edge depends on bot interaction and fill mechanics**, because simplified backtests systematically miss those effects. citeturn12view4turn17view1turn12view0turn10view4

What is still missing in the local frontier is therefore a strategy family that treats Pepper not as “always long with tiny tactical extras,” but as a **two-timescale control problem**:

- a **slow policy** that sets a target inventory surface as a function of latent carry/regime; and  
- a **fast policy** that gates entries, suppresses toxic passive quotes, chooses quote side/offset, and controls recycling based on microstate motifs and expected fill quality. fileciteturn0file5 fileciteturn0file2 citeturn27search12turn27search9turn23search2

### Ranked shortlist of the most promising genuinely new directions

1. **Pepper action-template distillation from exact-control traces**  
   Build a small discrete action set — for example `hold`, `join bid`, `improve bid`, `quote ask only`, `cross to recycle`, `pause`, `lean one-sided` — then train a cluster-to-action map or sequence classifier to imitate the optimal action *template* rather than regressing fair value. This is different because it targets the exact failure mode already observed locally: threshold logic appears unable to capture what exact-control traces are actually doing. Best suited to Pepper. Type: hybrid of local exact-control evidence, discrete control, and policy distillation. fileciteturn0file5 citeturn22search6turn23search2turn28search2

2. **Pepper fill-quality hazard gating**  
   Estimate whether a newly placed passive order is worth placing *at all* by modelling short-horizon fill probability jointly with post-fill edge. The key object is expected value per quote, not fill count or spread capture. This is materially different from existing market-making sweeps because it treats non-quoting as an action and explicitly attacks “donating” fills. Best suited to Pepper, but also useful for Osmium one-sided quoting. Type: direct transfer from survival/fill research plus novel adaptation. fileciteturn0file5 citeturn27search12turn27search9turn29view0

3. **Spread-intention and leaning-state classifier**  
   Treat spread width, repeated undercutting/overbidding, side persistence, and recent depth shifts as a latent-intent signal: not “spread is 2, so quote,” but “spread is 2 *for a reason*.” The user hint about spread behaviour encoding intention lines up surprisingly well with queue-reactive and OFI literature. The prototype is a finite-state motif detector, not a regression model. Best suited to Pepper, with smaller Osmium event-trading variant. Type: novel adaptation of user hints plus OFI/queue-reactive literature. fileciteturn0file2 citeturn22search0turn27search2turn28search0

4. **Queue-reactive Pepper simulator plus reduced-action policy search**  
   Do not jump to full RL. First estimate a tiny queue-reactive or Markov queue simulator from Pepper book states, then run policy search over a reduced action grammar. This is different from local threshold tuning because it changes the research engine itself: it lets you search policies defined over queue state, fill odds, and quote placement. Best suited to Pepper, potentially Osmium later. Type: external microstructure framework plus novel adaptation. citeturn27search2turn27search4turn27search6turn29view0

5. **Carry-target surface plus tactical recycler**  
   Keep the long-carry insight, but replace “always mostly long” with a learned target inventory surface and a distinct recycler that monetises favourable exits and suppresses dead inventory. That means classifying long inventory into *good carry long* versus *dead long* based on state and entry context. Best suited to Pepper. Type: hybrid of local frontier and control theory. fileciteturn0file5 citeturn6view1turn8view0turn22search3

6. **Sequence-motif Pepper trader**  
   Mine repeated short-horizon book/state subsequences that precede repricing or adverse fills, then map motif IDs to action templates. This is different from continuous indicators because it is explicitly sequence-based and non-parametric in state representation. Best suited to Pepper. Type: novel adaptation combining sequence classification and clustering. fileciteturn0file2 citeturn28search2turn28search12

7. **Osmium episodic event detector with passive-suppression default**  
   If Osmium still has hidden structure, it is more likely to be event-like than continuously tradable. The right abstraction is “detect burst regime, take constrained directed trade, then exit,” not “quote both sides all the time.” Best suited to Osmium. Type: hybrid of previous Squid Ink lessons and regime/event literature. fileciteturn0file0 citeturn10view6turn11view3turn28search0

8. **State-clustered finite-state controller**  
   Cluster Round 1 states using spread, imbalance, depth ratios, recent moves, inventory, and carry deviation, then attach a simple controller per cluster. This is often easier to falsify than RL and closer to the action granularity that Prosperity rewards. Best suited to both products, especially Pepper. Type: hybrid. citeturn22search6turn24search2turn28search14

9. **Auction-clearing basin map for manual-transfer reasoning**  
   The auction hints should not be dismissed. The useful transfer is not “solve the manual challenge again,” but “model bunching and snap points in discrete-price aggregate demand curves,” then reuse that intuition for one-tick nudges, quote shading, and end-of-state inventory release. Best suited where discrete bunching exists; useful as a mental model for both products. Type: novel transfer from manual-side auction logic. fileciteturn0file2

10. **Residual learner on top of v13 that only learns quote suppression and side selection**  
   If a fully new policy is too risky, the highest-quality residual is not fair-value adjustment but *execution residual*: cancel / don’t quote / quote one-side / widen / recycle. This is different from exhausted overlays because it learns only what the base strategy obviously gets wrong: low-quality fills. Best suited to Pepper. Type: hybrid and pragmatically strong. fileciteturn0file5 citeturn27search12turn23search2

### Broad longlist of plausible ideas worth testing

The longlist that survived this research includes: queue-value aware quoting; passive-versus-aggressive gating by expected fill value; microprice-with-state transitions instead of simple weighted mid; OFI stationarisation; depth-shape and convexity states; repeated one-sided leaning counts; hidden-state models on OFI and spread persistence; duration-aware HMMs; sequence motif libraries; cluster-to-action maps; dynamic carry target surfaces; recycler-only overlays; anti-eagerness filters; calm-versus-urgent execution modes; one-sided quote templates; reduced-action offline RL; contextual bandits over quote templates; exact-control imitation on compressed state; structural break detectors for within-day shifts; simulated call-auction basin approximations; two-timescale controllers; sparse event trading for Osmium; queue-priority valuation; synthetic-data augmentation through queue-reactive simulation; and ensemble systems that separate alpha, execution gate, and risk gate. Some of these will fail quickly, but each is at least a *different abstraction*, which is the bar that matters here. citeturn27search9turn27search2turn22search0turn28search4turn23search2turn24search2

## Guide repository and exhaustive resource mining

### What the guide repo is actually good for in this Round 1

The guide repo’s strongest transfer is organisational, not predictive. It explicitly splits the work into execution/inventory/risk, research/alpha/optimisation, and software/infrastructure/compute, and argues that teams win by specialising across those functions. For this exact Round 1 problem, that matters because the user’s local frontier already shows a research bottleneck: alpha direction is partially known, but execution quality and tactical filtering remain under-exploited. The repo is therefore most useful as a prompt to restructure the search, not as a source of a final strategy. citeturn31view0turn31view1

The most transferable conceptual pages are:

- **execution**: the “take, clear, make” decomposition is directly applicable to Prosperity’s discrete order-submission loop and should become a logging and analysis decomposition as well as a coding one; the page is strong precisely because it treats execution as an optimisation problem over order type, price, size, and behaviour under changing market state. citeturn8view1turn8view2
- **inventory**: the soft-limit / hard-limit distinction and the idea that inventory should alter quote side, quote size, and aggression are highly portable, especially given the local evidence that Pepper wants persistent inventory but not indiscriminate fills. citeturn8view0turn6view1
- **trader architecture**: the explicit use of `traderData` and modular per-product logic transfers well to a Pepper/Osmium split where the fast execution gate can be added without contaminating the slow carry state. citeturn7view0turn16view2
- **research/IMC 4 Round 1**: this section correctly frames the round as one stable-ish product plus one more dynamic product, but its specific recommendation — roughly “Pepper as linear-regression fair, Osmium as drifting asset” — is too generic for the current frontier because that family is already exhausted locally. citeturn7view5turn6view5
- **indicators** and **market basics**: useful for newcomers, but too generic to unlock a new edge here. Standard SMA/EMA/RSI logic is exactly the kind of surface-level idea that has already failed on similar volatile products in public Prosperity write-ups. citeturn8view3turn10view6

The best reading path through the repo for *this* problem is: official Round 1 context first, then the guide’s **execution**, **inventory**, and **trader architecture** sections, then the **research/IMC 4 Round 1** note as a weak baseline, and only then **RESOURCES.md** as the real launchpad. The correct adaptation is to treat the repo as a system-design primer and its resource list as the real research surface. fileciteturn0file0 citeturn8view1turn8view0turn6view4turn6view5turn31view0

### What transfers directly from RESOURCES.md

RESOURCES.md itself is candid that it is incomplete and that copying old code is not enough; it recommends previous high-ranking submissions, several directly relevant papers, and a long tail of forums, bundles, and tools. The useful way to mine it is to separate **direct alpha and control resources** from **tooling and methodology resources**. citeturn31view0turn32view0

#### Directly actionable article links

**Mean Field Games with Partial Information for Algorithmic Trading** is the most important article in the list for one reason: it formalises the idea that traders act under latent states they only partially observe. The transferable abstraction for Pepper is not the mathematics of a full mean-field equilibrium, but “estimate a latent state and act on filtered belief, not on raw mid-price.” The Round 1 adaptation is a small latent-state filter over carry state, pressure state, and urgency state, then an action map conditioned on those beliefs. Primary contribution: control and latent-state modelling. citeturn32view0turn22search2turn22search3

**Mean Field Game of High-Frequency Anticipatory Trading** contributes a different abstraction: fast traders often *take then supply liquidity* around anticipated larger flow, and inventory aversion changes that behaviour. For Round 1, this suggests looking for states where one step of aggression should be followed by passive recycling, rather than treating taking and making as unrelated behaviors. Primary contribution: execution and game-theoretic timing. citeturn32view0turn22search5turn22search8

**Advanced Statistical Arbitrage with Reinforcement Learning** is not directly about Prosperity, but it is very useful because it defines the state using recent trend fragments, not only level deviations from a mean. That maps well to Pepper sequence motifs and to a reduced discrete action space over quote templates. Primary contribution: learning and state construction. citeturn32view0turn22search6turn22search7

**High-frequency Statistical Arbitrage Strategy Based on Stationarized Order Flow Imbalance** is one of the best direct transfers. It argues that stationarised OFI is more linearly related to future mid-price motion than raw OFI, which fits the user hint that mild imbalance persistence may still matter. For Round 1, the adaptation is to build product-specific stationarised OFI, then test it not just for direction but for quote suppression and one-sided leaning. Primary contribution: alpha discovery. citeturn32view0turn22search0turn22search1

**An Impulse Control Approach to Market Making in a Hawkes LOB Market** is recent and highly relevant because it recasts market making as discrete interventions — place, cancel, cross, wait — under queue dynamics and clustered order arrivals. That is unusually close to Prosperity’s true action space. The Round 1 adaptation is not to solve the HJB, but to borrow its action grammar and search over it with exact-control traces, reduced-action RL, or imitation. Primary contribution: control and execution. citeturn32view0turn23search2turn23search4

The remaining article links in RESOURCES.md are less directly portable but still useful. **Optimal Allocation with Continuous Sharpe Ratio Covariance Bandits** is valuable as a contextual-bandit template for choosing among action templates under uncertainty; **Celebrating three decades of stock manipulation** is useful mainly as a reminder that repeated order-book patterns can encode intent; **Schrödinger Bridge Problem for Jump Diffusions** is more remote, but the transport-bridge idea is still helpful as inspiration for pathwise policy distillation and synthetic scenario generation. **XVA, the front office way**, **automatic differentiation**, and optimisation notes are lower-value for Round 1 alpha, but useful for improving solver-based experiments and exact-control pipelines. Primary contribution: methodology and optimisation. citeturn32view1turn28search15turn23search2

#### Prior-competition and Optiver resources listed in RESOURCES.md

The resource list explicitly points to high-ranking Prosperity repos and to entity["company","Optiver","trading firm"] / entity["company","Kaggle","competition platform"] resources for realised volatility and Trading at the Close. The most transferable lesson from the Optiver side is not “run gradient boosting on Prosperity” but that **imbalance features, urgency features, cross-feature interactions, and multi-scale histories can be extremely predictive even when raw mid-price movement looks weak**. In the public summaries that remain accessible, features such as liquidity imbalance, market urgency, price pressure, spread-depth ratios, and short lagged differences appear repeatedly. That is directly relevant to Pepper because it suggests that the persistent missing edge is probably *state interaction terms*, not more smoothing on the mid-price. citeturn31view2turn25search3turn25search11turn25search14

The realised-volatility items are less direct for this round, but still helpful in two ways. First, the Optiver ecosystem around realised vol strongly reinforces the value of **multi-scale features** and robust volatility proxies. Second, the broader review literature now shows that tree models and CNN/LSTM hybrids work mainly because they capture autocorrelation, asymmetry, co-movement, and regime variation across scales. The Round 1 adaptation is to use that lesson for regime detection and quote gating, not to attempt full volatility forecasting as an end in itself. citeturn31view2turn26search0

#### Tooling and methodology links

The resource list’s most important tooling links are the general microstructure pricing and backtesting ones. The **Micro_Price** repo is useful because it explicitly computes microprice from imbalance states, simulates transitions under a Markov model, compares Markov adjustment against simulation, and includes execution-algorithm experiments. The Round 1 adaptation is to rebuild microprice not as a final fair, but as one channel in a clustered state representation with transition-aware execution. Primary contribution: alpha discovery and simulation. citeturn31view2turn30view5turn30view7

The option-pricing repo in RESOURCES.md is not important for Round 1 itself, but it matters as an implementation reference for modular numerical finance code and later rounds. Its direct Round 1 value is low. By contrast, **hftbacktest** is directly useful to the methodology because it emphasises latency, queue position, and order fill simulation, and explicitly argues that accurate execution modelling is foundational when the edge is small. That is exactly the current Round 1 situation. Primary contribution: tooling and backtesting discipline. citeturn29view0

The **MARKET-MAKING-RL** repo is useful for one narrow reason: it physically implements an order book and uses a reduced market-making action space whose dynamics depend on the agent’s actions, rather than assuming mid-price alone is the world. That supports a reduced-action Pepper policy search, even if a full RL approach is probably too heavy at first. Primary contribution: simulation and policy search. citeturn30view2turn30view3

The **RxInfer** / Bayesian inference link is one of the most underrated items in RESOURCES.md. Its specific value is not the library itself, but the message-passing mindset for streaming latent-state inference. For Pepper, a compact Bayesian filter over latent carry, pressure, and urgency regimes is highly plausible and much lighter than a generic deep model. Primary contribution: latent-state modelling and methodology. citeturn32view2turn24search2turn24search8

The **ARCH package**, forecasting textbook, time-series links, structural-break links, and FinRL link are mixed in direct value. ARCH and forecasting references are useful for diagnostics and robustness; the structural-break links are directly relevant because Round 1 may still contain intra-day or product-specific regime shifts that current heuristics smear together; FinRL is more useful as a catalogue of formulations than as drop-in code. Primary contribution: methodology and regime detection. citeturn32view2turn24search10turn28search4

#### Videos, bundles, forums, blogs, and communities

These are lower-signal than the direct papers but still worthwhile search surfaces. The seminar playlist and low-latency talks are most useful for implementation realism and execution intuition. The bundle links such as *Best of Algorithmic Trading*, *Awesome quant*, and the systematic-trading collections are not themselves alpha, but they accelerate breadth searches for ideas around state-space modelling, market making, and optimisation. Wilmott and Quantitative Finance Stack Exchange are still valuable when you need a very specific microstructure or estimation question answered quickly. Bouchaud-style research blogs and ML-Quant-style applied posts are useful for intuition and recent adjacent ideas. Their direct Round 1 value is lower than the core papers, but their *indirect* value is in pointing to transferable abstractions and implementation tricks. citeturn32view1turn32view2

## Previous high-placing Prosperity repos

### The strongest portable abstractions

Across the strongest public repos, three abstractions recur. The first is **fair-value denoising by identifying the right book levels**, often large-volume or persistent quoting layers rather than raw best bid/ask. The second is **strict decomposition of taking, clearing, and making**, along with inventory-aware quote placement. The third is **using richer diagnostics and backtests than the official site alone**, while never trusting synthetic backtests blindly when bot interaction matters. These abstractions remain highly portable to Prosperity 4 Round 1 even if the exact products differ. citeturn12view4turn17view1turn11view0turn10view4

### Deep dives on the most useful repos

**ericcccsliu/imc-prosperity-2** is still one of the highest-signal repositories for Round 1 design. It combines an in-house backtester and dashboard with a modular strategy layout, and its Round 1 write-up is explicit that Starfruit became much easier once they filtered the book for large-size quotes and used the market-maker mid rather than the noisy raw mid. Their final code shows a clean take / clear / make decomposition and a filtered fair-value function that falls back to history when the large-quote proxy disappears. The portable principle is not “copy Starfruit,” but “find the low-noise quoting layer and then execute around it with a clean order-intent pipeline.” What is less portable is their exact reliance on the website’s hidden PnL mechanics. For Pepper, the reinterpretation is to search for the *structural* quoting layer that best predicts next-step realised book evolution, then combine that with execution gating. citeturn11view0turn12view4turn19view0turn19view6

**TimoDiehm/imc-prosperity-3** is the single best repo for execution architecture and realistic bot-interaction thinking. The write-up explains the “wall mid” concept, notes the sequence of simulator actions within a timestep, and the final code uses product-specific subclasses under a common trader framework. For the stable product, the code literally performs taking at positive edge, zero-edge clearing if inventory is wrong-signed, and then wall-aware market making. For Kelp, they add logic based on an “informed” trader identity, which is competition-specific, but the portable principle is broader: detect when the market state indicates informed directional pressure and alter quote side and aggression accordingly. This repo’s biggest gift to Round 1 is therefore not wall-mid itself, but the idea that execution should be stateful, modular, and explicitly aware of *who or what is probably pushing the book*. citeturn11view1turn12view0turn17view1turn17view0turn16view2

**chrispyroberts/imc-prosperity-3** contributes two underused principles. First, they exploited passive orders at fair value specifically for balancing inventory, which is a subtle but important reminder that some quotes exist mainly to recycle rather than to initiate alpha. Second, their post-mortem on Squid Ink is valuable because it documents broad failure of generic z-score / breakout / MACD ideas and the eventual pivot to a smaller, spike-fade style. For Osmium, that is a warning: if the hidden pattern exists, it may still be episodic and best handled with constrained event trading rather than continuous two-sided making. citeturn11view2turn12view6turn10view6

**CarterT27/imc-prosperity-3** and **YBansal95/imc-prosperity-3** both reinforce the value of filtered fair values and execution logic, but YBansal’s runtime logistic regression idea is particularly interesting. Their model used a seven-feature vector including z-score, momentum, imbalance, MACD, and pressure to produce probabilistic decisions. That exact formulation is unlikely to be the final Round 1 answer, but the broader principle is very portable: use a *small, interpretable probabilistic classifier* to choose among action templates. That is much more attractive here than a large opaque model. citeturn11view3turn11view4turn12view7

**ShubhamAnandJain/IMC-Prosperity-2023-Stanford-Cardinal** is most useful as a reminder that Round 1 often splits into a stationary asset and a weakly directional asset, and that the weakly directional asset may respond to simple local linear prediction before more elaborate methods do. That helps frame Osmium, but the user’s current frontier already suggests that a generic regression-based redesign has been tried. The portable principle here is therefore only the meta-principle: treat the two products as fundamentally different policy families. citeturn11view5

**pe049395/IMC-Prosperity-2024** is valuable because it explicitly notes that microprice and large-quantity levels can outperform raw mid-price, and because it describes how apparently platform-aligned fair price estimation came from large bid/ask levels rather than naive best-price averaging. This is directly relevant to both Pepper and Osmium: one should search not merely for price forecasts, but for the book levels that best proxy the hidden or persistent reference process governing the bots. citeturn11view6

**jmerle/imc-prosperity-2** should not be ignored just because the repo is simpler. Its most useful abstraction is the use of soft and hard liquidation procedures near inventory boundaries. That ports naturally into a Pepper recycler layer and an Osmium event trader that should aggressively step back from toxic one-sided positions. citeturn11view7

### Additional repos scanned

The lower-ranked or lighter-writeup Prosperity 3 repos that still added signal were **awatatani**, **musashi-island**, **angus4718**, **Akezh**, and **jmerle/imc-prosperity-3**. They mostly reinforce already-seen ideas: stable-product market making, filtered dynamic fair prices, mean-reversion or spike-fade logic on the volatile product, and practical inventory safeguards. They are useful as confirmation layers, but they did not reveal a fundamentally different Round 1 abstraction beyond what the strongest repos already exposed. citeturn21view0turn21view1turn21view2turn21view3turn21view4

## External inspiration and generated strategy families

### External inspiration that actually transfers

The best external ideas were the ones that changed either the **state representation** or the **action space**.

Queue-reactive market models treat the order book as a Markov queueing system whose flow intensities depend on current queue state and on switches between periods of constant reference price. That is almost tailor-made for Prosperity because the exchange is discrete, narrow, and low-depth. The modern extensions matter even more: MDQR relaxes queue independence and adds market features and order sizes; order-size-aware queue-reactive work shows that size distributions are part of the state, not just incidental details. The Round 1 implication is clear: any search that still compresses the book to mid-price, spread, and simple imbalance is probably leaving edge on the table. citeturn27search2turn27search4turn27search6turn27search7

Queue position valuation and fill-probability work push in the same direction. Under price-time priority, queue placement has option value, and the passive-versus-aggressive decision should depend on expected fill timing and post-fill edge, not on spread alone. The Oxford-Man survival-analysis paper is especially useful because it makes exactly that passive-versus-aggressive choice the core decision variable. For Pepper, this strongly supports a fill-hazard gate and a “do nothing” action. citeturn27search9turn27search12

Sequence-classification and HMM-style regime work suggest that the missing edge may be **mesoscopic** rather than ultrashort or long-horizon: a pattern over the last few states that predicts a price flip, a toxicity burst, or a period in which passive quoting is dangerous. The sequence-classification RNN paper is practical because it predicts the *next event price flip* rather than long-run return; the OFI-HMM paper is practical because it uses directional OFI states to infer latent regimes relevant to passive order placement. Both map unusually well to Pepper’s “stable but maybe subtly patterned” brief. citeturn28search2turn28search0

For regime detection, the structural-break material is more useful than it first appears. The core idea is not macro regime switching but **rapid recognition that the local rule has changed**. If a Pepper book spends 200–500 iterations in one behavioural mode and then flips, a small break detector or duration-aware regime model could outperform any global threshold. This also fits the local observation that the robust baseline often wants a high long inventory for much of the day, but not necessarily in the same way at every moment. citeturn24search10turn28search4turn28search14

### Generated strategy families

#### Microstructure alpha families

**Spread-intention persistence trader**  
Core idea: classify spread states not by width alone but by why that width persists — repeated same-side leaning, undercutting, depth asymmetry, and recent failed repricings. It might work here because Pepper hints and the local frontier both point toward subtle repeated behaviour rather than large directional moves. It differs from exhausted variants because the signal is state persistence and intention, not simple distance-to-fair. Features: spread, best sizes, depth ratios, recent side changes, leaning counts, time since last price move. Failure mode: too sparse or unstable motifs. Minimal prototype: a rules-first finite-state machine. Reality check: improved fill quality and lower toxic-fill rate even before higher total PnL. fileciteturn0file2 citeturn22search0turn27search2

**Stationarised OFI execution gate**  
Core idea: use stationarised OFI to decide whether a passive order is worth exposing. It might work because OFI literature finds stronger relation after stationarisation, and Pepper likely lives in small deviations where raw OFI is too noisy. It differs from common imbalance heuristics because the output is a quote/no-quote or one-sided-quote action, not a direct directional trade. Features: OFI, spread, state transition bucket. Failure mode: overfitting to one day or one spread regime. Minimal prototype: OFI bucket × spread bucket conditional expected value table. citeturn22search0turn22search1

**Depth-shape / convexity pressure model**  
Core idea: use not just top-of-book imbalance but how depth is stacked across visible levels. It might work because large-volume “walls” repeatedly emerged in top repos as the fair proxy. It differs from common fair-value logic because it estimates latent pressure from shape. Minimal prototype: few engineered ratios on top three levels plus one-step forward return/fill-quality study. citeturn12view4turn12view0turn11view6

#### Control and policy families

**Exact-control trace distillation**  
Core idea: cluster states and learn the action template preferred by exact or near-exact control, rather than approximating the value function directly. It might work because the local frontier already indicates exact-control evidence contains information threshold logic is failing to translate. Features: inventory, carry deviation, spread, depth, motif ID, recent state transitions. Action space: 6–10 discrete templates. Failure mode: trace policy too dependent on sample path quirks. Minimal prototype: k-means or GMM state clusters with majority-vote action labels from optimal traces. fileciteturn0file5 citeturn22search6turn23search2

**Finite-state controller with target-inventory surface**  
Core idea: replace scalar inventory penalty with a state-dependent target inventory. It might work because Pepper likely wants high long inventory in some states but not others. It differs from current heuristics because inventory is no longer only a constraint but part of the policy output. Minimal prototype: estimate target inventory by state bucket and add recycler around it. fileciteturn0file5 citeturn8view0turn22search3

**Policy-over-policy gating**  
Core idea: base policy sets candidate orders; gate policy vetoes or reshapes them. It might work because the likely remaining edge is negative-fill suppression rather than a new base signal. It differs from simple overlays because the gate’s objective is expected value per fill. Minimal prototype: binary classifier predicting whether each proposed quote is value-positive. fileciteturn0file5 citeturn27search12

#### Model-based families

**Latent fair plus transient pressure decomposition**  
Core idea: split price estimate into slow latent anchor and transient micropressure term. It might work because wall-mid / large-volume-filtered fair values have worked in prior rounds, but tactical mistakes remain. It differs from exhausted fair-value variants by explicitly separating anchor estimation from execution state. Minimal prototype: large-volume filtered mid + pressure residual from OFI/depth state. citeturn12view4turn12view0turn11view6turn22search0

**Hidden-state or duration-aware micro-regime model**  
Core idea: infer short-lived regimes with persistent durations. It might work because steady markets often alternate between calm quoting, pressure build-up, and repricing states. It differs from threshold logic by letting the same observable signal mean different things in different regimes. Minimal prototype: 3-state HMM on Pepper OFI / spread / micro-return state. citeturn28search0turn28search4turn28search14

#### Execution families

**Calm quoting / anti-eagerness filter**  
Core idea: in marginal states, quote less and join later. It might work because user hints explicitly mention over-eager quoting donating edge. It differs from inventory-only skewing by using predicted fill quality. Minimal prototype: only quote when expected value per quote exceeds zero by a margin. fileciteturn0file2 citeturn27search12turn29view0

**Regime-sensitive quote placement**  
Core idea: quote location depends on market mood: improve, join, sit behind, or abstain. It might work because wall-mid and queue-value work both imply that *where* you rest matters materially. Minimal prototype: quote-offset classifier over 4 choices. citeturn27search9turn12view0turn17view1

**Expected-value-per-fill optimiser**  
Core idea: re-rank candidate actions by expected fill value rather than spread capture. It differs from standard market making because it is deliberately willing to trade less. Minimal prototype: estimate `P(fill within h) * E(post-fill alpha | fill] - inventory cost`. citeturn27search12turn27search9

#### Search and learning families

**Reduced-action offline RL**  
Core idea: apply RL only after compressing the state and action spaces aggressively. It might work because the environment is discrete and has action persistence, but a full end-to-end RL search is too expensive and too easy to overfit. Minimal prototype: offline fitted Q on clustered states and 6–8 action templates. citeturn22search6turn30view2turn23search2

**Contextual bandits over quote templates**  
Core idea: treat each timestep as choosing among a few quote templates, updating online or in replay. It might work here because the main decision is often template selection under uncertainty, not long-horizon credit assignment. Minimal prototype: Thompson or UCB selection over action templates by state bucket. citeturn32view0turn24search2

#### Auction and manual-transfer families

**Clearing-basin sensitivity maps**  
Core idea: map discrete demand bunching and price snap points, then use the same reasoning to understand continuous quoting near crowded integer basins. It might work because Prosperity often hides edges in discrete-price mechanics. Minimal prototype: aggregate demand curves and sensitivity of clear to final marginal order. fileciteturn0file2

## Product-specific focus

### What is probably still missing in Pepper

The user frontier already implies Pepper remains the main edge surface. The high-level picture that best fits both the official description and the local evidence is: Pepper likely has a valid **slow carry bias**, but current profits are being diluted by **tactical monetisation errors** — low-quality fills, mistimed replenishment, dead inventory, and insufficient discrimination between favourable and unfavourable low-spread states. fileciteturn0file0 fileciteturn0file5

That changes the right question. The question is probably *not* “what is Pepper’s fair value?” but:

- when should long inventory be added versus merely held;
- when should one side of the book be suppressed;
- when should a passive quote be replaced by a recycler exit;
- which repeated state motifs turn a nominally good carry state into a poor execution state; and
- whether a high long target is appropriate *right now* or merely over a broader window. fileciteturn0file5 fileciteturn0file2

The most promising Pepper decomposition is therefore:

1. **latent target inventory**  
   a slow estimate of the appropriate net long posture;

2. **entry gate**  
   a classifier or cluster map that decides whether buying more now improves expected value;

3. **fill-quality gate**  
   a hazard model deciding whether passive exposure is worth it;

4. **recycler**  
   a module that exits or trims inventory opportunistically when local state turns a good long into dead long;

5. **risk gate**  
   controls near limits and after low-quality fills. fileciteturn0file5 citeturn27search12turn27search9turn22search3

The biggest missed-edge hypotheses in Pepper are these:

- **Sequence motifs exist.**  
  The market may revisit a small number of microstates before repricing or before toxic fills. If true, motif mining should improve quote suppression and side choice. fileciteturn0file2 citeturn28search2

- **Repeated one-sided leaning matters more than raw imbalance.**  
  One isolated book imbalance is weak; several consecutive same-side lean events may be much stronger. fileciteturn0file2 citeturn22search0turn28search0

- **Low-spread states are heterogeneous.**  
  Some are safe carry-entry states; others are dead zones where quoting primarily donates. That is exactly what a fill-quality gate can separate. fileciteturn0file5 citeturn27search12

- **Exact-control traces are pointing to action templates, not better thresholds.**  
  If the optimal policy flips among a few templates depending on state, attempting to approximate it with smoother thresholds will keep failing. fileciteturn0file5 citeturn23search2turn22search6

### Osmium and the Ash possibility space

Osmium should not be discarded, but the most likely reason redesigns have underperformed is that the wrong abstraction was attacked. If the product really does contain a hidden pattern, a continuous fair-value-plus-threshold strategy is exactly the wrong weapon: it will overtrade noise, warehouse inventory at bad times, and miss event structure. The better abstractions are **episodic event detection**, **latent regime classification**, **passive suppression in toxic states**, and **small directed trades with disciplined recycling**. fileciteturn0file0 fileciteturn0file5

Three Osmium families remain worth serious testing:

- **event detector plus constrained fade/follow strategy**  
  detect burst regimes from spread, OFI, depth shocks, and recent returns, then trade only during those episodes;  
- **latent-pattern sequence classifier**  
  classify the last short sequence into a few pattern states and act only when state confidence is high;  
- **execution-first redesign**  
  keep signal simple, but aggressively suppress passive quotes when the book is disorderly or when fill hazard implies toxicity. citeturn10view6turn11view3turn28search0turn28search2

My view is that Pepper is still the more likely breakout source, because the local evidence already says a meaningful edge exists there and because execution-style improvements can unlock PnL without requiring a miraculous new signal. Osmium is higher variance: if the hidden pattern is real and detectable, upside could be significant; if not, it remains a trap for overfitting. fileciteturn0file5

## Forensic analysis plan and hypothesis framework

### Detailed data and log forensics

The right forensic agenda is to analyse **state-action-quality**, not just price and PnL.

**State bucketing and opportunity maps**  
Bucket states by spread, best-level imbalance, depth shape, recent leaning count, recent repricing interval, and current inventory deviation from target. Compute forward returns, fill rates, and realised PnL contribution by bucket. Bullish result: a small subset of buckets explains most good or bad fills. Bearish result: no state discrimination at all. Supports state-clustered controllers and fill gating. citeturn27search2turn22search0

**Action-conditioned forward-return study**  
For each candidate action template, measure conditional forward value: no action, passive bid, passive ask, one-sided, cross-to-exit, pause. Bullish result: some actions have strongly state-dependent value. Bearish result: action ranking is unstable. Supports policy distillation. citeturn23search2turn22search6

**Fill-quality decomposition**  
Label current strategy fills as good, neutral, or donating using post-fill PnL over multiple horizons and inventory-adjusted valuation. Break down by product, side, spread regime, and inventory state. Bullish result: a concentrated set of quote regimes causes most donation. That would strongly support fill-hazard modelling. fileciteturn0file5 citeturn27search12

**Spread-regime conditional PnL**  
Decompose passive and aggressive PnL by spread bucket and by whether the spread is widening, stable, or collapsing. Bullish result: not all “tight” spreads are equal. Supports spread-intention models. fileciteturn0file2

**Book-shape motif mining**  
Convert recent book snapshots into symbolic states and mine frequent subsequences before price flips, adverse fills, and profitable recycling. Bullish result: repeated motifs with stable out-of-sample behaviour. Supports sequence-motif strategies. citeturn28search2turn28search12

**Inventory-conditioned opportunity surfaces**  
Plot expected value of adding, holding, or reducing inventory against current inventory and state bucket. Bullish result: there is a clear target-inventory surface rather than a monotone penalty. Supports dynamic target policies. fileciteturn0file5 citeturn8view0

**Exact-control trace clustering**  
If exact-control traces are available, cluster states and actions jointly, then inspect whether a small set of action templates dominates. Bullish result: high cluster purity in action labels. Supports trace distillation. fileciteturn0file5

**Heuristic-versus-optimal confusion analysis**  
Measure where the current heuristic disagrees with exact-control or with an empirically superior action. Bullish result: disagreements concentrate in a manageable subset of states. Supports targeted residual learning. fileciteturn0file5

**Passive versus aggressive decomposition**  
For both products, split PnL into passive spread capture, aggressive taking edge, recycling, and inventory carry. Bullish result: one leg dominates losses and can be redesigned in isolation. Supports execution-only interventions. citeturn8view1turn17view1

**Outlier-day and segment stratification**  
Analyse each day and intraday segment separately. Bullish result: some motifs or gates repeat across days and time slices. Bearish result: everything is day-specific. Supports anti-overfit filtering and regime work. citeturn24search10turn28search4

**Perturbation and placebo tests**  
Shift signals by one timestep, randomise labels within day, coarsen buckets, and perturb spread/imbalance thresholds. Real edges should degrade gracefully, not vanish instantly. Supports overfit control. citeturn10view4

### Hypothesis testing framework for the major families

**Action-template distillation**  
Hypothesis: a small discrete action set explains most exact-control advantage in Pepper.  
Features: inventory, carry deviation, spread, imbalance, depth shape, recent motif ID.  
Action space: 6–10 templates.  
Simplest backtest: replay with oracle-labelled action templates converted into deterministic policy by state cluster.  
Diagnostics: cluster purity, action confusion matrix, state-value heatmaps.  
Overfit check: day-split validation and cluster-stability tests.  
Success: material lift from state-to-template map alone.  
Abandon quickly if action labels are diffuse and unstable. fileciteturn0file5

**Fill-hazard gate**  
Hypothesis: many losing fills are predictable from local state before the order is sent.  
Features: quote side/offset, spread, imbalance, depth shape, recent leaning, inventory, time since last move.  
Action space: quote / do not quote / quote one side.  
Simplest backtest: apply gate to current best strategy and measure retained PnL versus removed fills.  
Diagnostics: precision-recall on bad fills, EV-per-quote by decile, calibration plot.  
Success: removes a large share of donating fills while preserving most good fills.  
Abandon if the gate only reduces trading activity with no improvement in EV per fill. fileciteturn0file5 citeturn27search12

**Spread-intention classifier**  
Hypothesis: spread persistence and leaning patterns encode near-term quote toxicity or repricing.  
Features: spread history, undercut counts, same-side best-price persistence, depth asymmetry.  
Action space: improve / join / hold back / pause.  
Backtest: state-bucket action table.  
Diagnostics: repricing frequency and adverse-selection rate by classified state.  
Success: improved realised spread capture with lower adverse selection.  
Abandon if state labels do not separate outcomes. fileciteturn0file2

**Queue-reactive simulator plus policy search**  
Hypothesis: a simple estimated queue-state simulator is sufficient to evaluate reduced-action policies better than direct threshold sweeps.  
Features: top-level queues, spread, recent reference-price changes, order sizes.  
Action space: reduced quote templates.  
Backtest: simulator-first, then replay sanity check.  
Diagnostics: simulator realism on queue and price-transition statistics.  
Success: simulator ranking transfers to replay.  
Abandon if simulator cannot reproduce basic queue and repricing behaviour. citeturn27search2turn27search6turn29view0

**Osmium episodic event detector**  
Hypothesis: edge resides in burst regimes, not in continuous quoting.  
Features: rolling return shocks, spread jumps, imbalance shocks, recent event sequence.  
Action space: flat / fade / follow / recycle.  
Backtest: event-triggered trade study with strict hold-time and size caps.  
Diagnostics: event precision, contribution by event class, tail-risk profile.  
Success: stable positive EV on events with controlled drawdowns.  
Abandon if event count is too low or if performance is driven by a single day. citeturn10view6turn28search0

## Prioritised build order and implementation roadmap

### First three prototypes

1. **Pepper fill-quality hazard gate on top of the current best strategy**  
   Difficulty: medium. Novelty: high. Upside: high. Overfit risk: medium.  
   Why first: it directly attacks the clearest failure already observed locally — many weak or negative short-horizon fills — while preserving the known-good carry baseline. The prototype is also straightforward: log each candidate quote, whether it filled, and its horizon PnL; then train a light model or even a bucketed EV table. fileciteturn0file5 citeturn27search12

2. **Pepper exact-control trace clustering into action templates**  
   Difficulty: medium to high. Novelty: very high. Upside: very high. Overfit risk: medium.  
   Why second: it is the most direct test of whether the missing edge is a threshold failure or a genuinely different action grammar. If clusters cleanly map to actions, this could be the breakout family. fileciteturn0file5

3. **Pepper spread-intention / leaning-state finite-state controller**  
   Difficulty: medium. Novelty: high. Upside: high. Overfit risk: low to medium.  
   Why third: it is the fastest way to test the prompt hints about spread intention and over-eager quoting without committing to heavy simulation or RL. fileciteturn0file2

### Next five if those fail

4. **Dynamic carry-target surface plus recycler.**  
5. **Stationarised OFI gate for passive quoting.**  
6. **Sequence-motif mining with cluster-to-action lookup.**  
7. **Osmium episodic detector with passive suppression default.**  
8. **Reduced-action contextual bandit over quote templates.**  
Each of these is meaningfully different from threshold sweeps and can be falsified relatively quickly with the forensic programme above. citeturn22search0turn28search2turn28search0turn24search2

### Highest-upside but hardest ideas

The most ambitious “swing for upside” ideas are the queue-reactive simulator plus policy search, reduced-action offline RL, and a Bayesian latent-state controller using message passing. These could produce the biggest structural improvement, but only after the state representation and action grammar have been simplified enough to avoid overfit. citeturn27search4turn23search2turn24search2

### Fastest falsification ideas

The fastest falsification ideas are:

- quote/no-quote gating by simple state buckets;
- spread-intention state tables;
- inventory-conditioned opportunity surfaces;
- one-sided quote suppression rules in Pepper;
- event-only Osmium trades with strict caps.  

If none of these show strong state separation, the case for more elaborate learning methods weakens sharply. fileciteturn0file5 fileciteturn0file2

### Best likely-robust ideas

The most likely robust ideas are the execution-only ones: fill-quality gating, recycler logic, and regime-sensitive one-sided quoting. They need less extrapolation than full latent-state or RL systems and align most closely with both the current search frontier and the strongest patterns from public repos. fileciteturn0file5 citeturn8view1turn11view0turn17view1

### Best policy-distillation ideas

The strongest policy-distillation path is:

- build exact-control traces or near-oracle traces;
- compress states into interpretable clusters or motifs;
- learn discrete action templates;
- only then add residual learning for quote offset or size.  

That path is much safer than “train RL end to end,” and much more faithful to the evidence that exact-control contains structure current heuristics miss. fileciteturn0file5 citeturn22search6turn23search2

### Best execution-only ideas

The best execution-only ideas are:

- passive quote suppression on predicted bad fills;
- one-sided quote choice by state;
- delayed replenishment after adverse microstates;
- recycler quotes at fair or zero-edge levels when inventory is wrong-signed;
- explicit anti-eagerness filters in low-spread states. fileciteturn0file2 citeturn12view6turn27search12

### Best alpha-discovery ideas

The best pure alpha-discovery ideas are:

- sequence motifs before repricing;
- stationarised OFI and leaning persistence;
- depth-shape / wall identification;
- short-duration hidden-state models on Pepper book state; and
- event-state models for Osmium. citeturn22search0turn28search0turn12view4turn28search2

### Immediate implementation-ready prototypes

An engineer could start with these immediately:

- **Prototype A:** instrument the current Pepper strategy so every candidate passive quote is logged with state, fill outcome, post-fill PnL, and whether the quote came from take/clear/make logic; train a bucketed EV-per-quote model and gate future quotes by it.  
- **Prototype B:** from exact-control or best-trace data, cluster Pepper states using `[spread, imbalance, depth ratios, recent leaning counts, inventory, carry deviation, recent move flags]`; label each cluster with the best action template and deploy as a finite-state controller.  
- **Prototype C:** build a Pepper motif miner on the last `k` states of top-of-book and spread changes; retain only motifs with stable cross-day lift and use them to suppress or skew quotes.  
- **Prototype D:** rebuild Osmium as an event-trading product with “flat unless confident” policy, using trigger classes defined by spread shock, OFI shock, and return shock.  
- **Prototype E:** estimate a target inventory surface for Pepper by state bucket and add a recycler layer that actively distinguishes good long from dead long.  

Taken together, these directions constitute the strongest research programme uncovered here: they are materially different from the saturated local search, they are specifically adapted to the Prosperity Round 1 mechanics and to the user’s frontier evidence, and they offer the clearest path to a genuine breakout rather than another marginal parameter improvement. fileciteturn0file0 fileciteturn0file2 fileciteturn0file5 citeturn8view1turn17view1turn27search12turn23search2turn27search2
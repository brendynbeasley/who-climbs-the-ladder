# Methods review of Grossman and Helpman (1991)

- **Paper:** Gene M. Grossman and Elhanan Helpman, "Quality Ladders in the Theory of Growth," *Review of Economic
  Studies* 58(1), January 1991, pp. 43–61 (doi 10.2307/2298044). Circulated as NBER Working Paper 3099, September
  1989.
- **Statistical focus:** the two formal results that carry the paper's testable content. First, the steady-state
  innovation rate and growth rate, equations (12) and (13) of the working paper, which say that each industry's
  leader is displaced at the Poisson rate $`\iota = (1-\delta)L/a_I - \delta\rho`$ and that the consumption index
  grows at $`g = \iota \log \lambda`$. Second, the claim that "without any cost advantage, an industry leader will not
  engage in R&D," shown by comparing a leader's incremental profit from one more step, $`(1-1/\lambda)E/\lambda`$,
  with an outsider's, $`(1-1/\lambda)E`$.
- **Review standard:** internal consistency of the formal results, explicitness of assumptions, and the
  testability of the predictions. The current AEA Data and Code Availability Policy does not bite, because the paper
  uses no data.
- **What was read:** the full text of NBER Working Paper 3099 (41 pages, the free PDF at nber.org), the NBER
  abstract page, and the Crossref metadata record for the published article. I did not read the published journal
  version. Equation numbers and page references below are to the working paper, and the published text may differ
  in wording, numbering and some details.

## Methods summary

The paper builds a continuous-time general-equilibrium model of growth through repeated quality improvements. A
continuum of products, indexed on the unit interval, each sits on its own quality ladder with a common step size
$`\lambda > 1`$. Consumers have log intertemporal utility with discount rate $`\rho`$ and a Cobb–Douglas
instantaneous index in quality-adjusted consumption. Labor is the only factor (Sections II to IV); one unit makes
one unit of any good, and research intensity $`\iota`$ on a product needs $`a_I\iota`$ workers and succeeds with
Poisson arrival rate $`\iota`$. Price competition among firms that can make adjacent qualities produces limit
pricing at $`p = \lambda w`$, so the leader earns $`\pi = (1-\delta)E`$ with $`\delta = 1/\lambda`$. Free entry into
research sets the value of leadership equal to its cost, $`v = w a_I`$, and a no-arbitrage condition on the
leader's shares, which lose their value when the next step arrives, closes the model with the labor-market
constraint $`a_I\iota + \delta E = L`$. The economy jumps immediately to a steady state.

From the steady state the paper derives the innovation rate (13), the growth rate (12), the welfare function (14)
and the optimal innovation rate (15), and shows that the market rate can be too high or too low depending on
$`\lambda`$ (equation 16 and Figure 2). Section IV shows that a variety-expansion model has the same reduced form.
Section V adds an outside good and a second factor and shows that a larger economy need not grow faster. Section VI
embeds the model in a two-country trading world.

The research-design headings that follow are those used for empirical papers. Most do not apply to a theory paper,
and I say so under each.

**Research design.** Deductive, formal modeling. There is no empirical design. The paper's "evidence" is casual
observation in the introduction (automobiles, televisions, compact disc players, desktop computing) and one survey
figure from Scherer (1980) in footnote 2.

**Sampling strategy.** Does not apply. No sample is drawn.

**Sample size.** Does not apply.

**Inclusion and exclusion criteria.** Does not apply to data. The model's scope restrictions play the analogous
role and are stated explicitly: symmetric treatment of all products, a common step size, no imitation (ruled out
because an imitator earns zero profit under Bertrand competition), no cost advantage for leaders in research, and an
initial condition in which every industry already has a leader one step ahead.

**Independent and dependent variables.** In the model, the exogenous parameters are $`L`$, $`a_I`$, $`\lambda`$ and
$`\rho`$; the endogenous outcomes are $`\iota`$, $`E`$ and $`g`$. The paper signs the comparative statics: more
labor, cheaper research, or bigger steps all raise $`\iota`$.

**Statistical methods.** None. The paper uses phase-diagram analysis, closed-form solution of the steady state,
and the Poisson distribution (citing Feller 1968) to aggregate across products.

**Reported effect sizes.** None in the statistical sense. The formal results are the analogues and are listed in
the table below.

**Confidence intervals.** Do not apply. There are no estimates.

**P-values.** Do not apply.

**Missing data treatment.** Does not apply.

**Stated limitations.** The authors flag several. Footnote 5 says that a leader with a research cost advantage
could innovate too, and points to a companion paper that allows it. Footnote 3 assumes the chosen quality is unique.
Footnote 7 notes that the immediate jump to steady state depends on the initial condition. Section V is itself a
qualification of the scale result in (13). The paper does not discuss how its parameters could be measured.

## Statistics extraction table

| Statistic | Value and unit | Source location | What it measures | What it does not establish |
|---|---|---|---|---|
| Limit price | $`p = \lambda w`$, a markup ratio of $`\lambda`$ over unit cost | Eq. (8), p. 8 | The price a one-step leader charges under Bertrand competition with the firm one rung below | That observed markups equal the step size; real markups also cover research, marketing and fixed costs |
| Leader's profit flow | $`\pi = (1-\delta)E`$, $`\delta = 1/\lambda`$; share of industry sales | Text after eq. (8), p. 8 | Profit per product as a share of spending on it | Any measured profit rate |
| Leader's gain from innovating vs outsider's | $`(1-1/\lambda)E/\lambda`$ vs $`(1-1/\lambda)E`$; ratio $`1/\lambda`$ | p. 9 and footnote 5 | Why leaders do no research when they have no cost advantage | That real leaders do no research; the result disappears with any leader cost advantage, which footnote 5 acknowledges |
| Free-entry condition | $`v = w a_I`$; dollars per leadership position | p. 10 | Value of a leader equals expected research cost of displacing it | Any measured firm value |
| Steady-state innovation rate | $`\iota = (1-\delta)L/a_I - \delta\rho`$; arrivals per product per unit time | Eq. (13), p. 14 | The Poisson rate at which each leader is displaced | The size of $`\iota`$ in any economy; $`L/a_I`$ has no direct empirical counterpart in the paper |
| Growth rate | $`g = \iota \log \lambda`$; per unit time | Eq. (12), p. 14 | Growth of the quality-adjusted consumption index (or of final output under the intermediate-goods reading) | Any measured growth rate; the paper reports no calibration |
| Optimal innovation rate | $`\iota^* = L/a_I - \rho/\log\lambda`$ | Eq. (15), p. 15 | Planner's choice of research | Whether actual research is too high or low; that sign depends on $`\lambda`$ (eq. 16) |
| Over- or under-investment | $`\iota > \iota^*`$ for small or large $`\lambda`$, $`\iota < \iota^*`$ for intermediate $`\lambda`$ | Eq. (16), Figure 2, p. 16 | Net of consumer-surplus, spillover and business-stealing effects | Which region the US economy is in |
| Scherer survey figure | 59% of research outlays on product improvement, 28% new products, 13% new processes | Footnote 2, p. 4, citing Scherer (1980, p. 409) | Motivation for focusing on quality improvement | Anything about turnover, leaders or growth; it is a secondary citation |

## Interpretation notes

- The derivations I checked are internally consistent. Solving the labor constraint (10) and the steady-state
  no-arbitrage condition (11) together gives (13) exactly, and the Poisson aggregation behind (12) is standard.
- The growth formula carries a scale effect: $`\iota`$ rises one for one with $`L/a_I`$. The paper's own Section V
  shows the effect depends on the general-equilibrium structure, but the basic model predicts that a larger
  research workforce yields proportionally faster growth. Jones (1995, *Journal of Political Economy* 103(4)) later
  argued that this "scale effects" prediction of R&D-based growth models is inconsistent with the time-series
  evidence from industrialized economies. That is a documented objection to a class of models, not a finding of
  error in this paper.
- The no-research-by-leaders result is a knife-edge of the symmetric-cost assumption, as the authors say. It is a
  sharp prediction, but it is offered as a simplification rather than a claim about the world.
- The model has no firm-size distribution within an industry. "Leader" means the holder of the top-quality
  blueprint, who takes the whole market. Mapping it to the largest firm by revenue in a real industry is an
  interpretive step that the paper does not take.

## Unanswered questions

- How should $`\iota`$ be measured? The paper does not say whether it corresponds to patent rates, leader turnover,
  product replacement or research spending.
- What step size $`\lambda`$ is plausible, and is it common across industries? The paper assumes it is.
- How sensitive are the welfare results in (16) to the symmetric-cost assumption that rules out research by leaders?
- Does the immediate jump to steady state survive starting points other than the one assumed in footnote 7?

## Items requiring expert verification

- Whether the published *Review of Economic Studies* version differs from Working Paper 3099 in equation numbering,
  the statement of (13), or the treatment of leader research. I read only the working paper.
- The OCR of the working paper PDF is imperfect; symbols in (9), (11) and (16) were reconstructed from context and
  checked by re-deriving (13). A reader with the journal text should confirm them.
- Whether Jones (1995) is the right primary citation for the scale-effect objection as applied to quality-ladder
  models specifically, rather than to R&D-based models generally.

The modern rerun in this repository does not reproduce anything in the paper, which has no data. It turns the
displacement rate in (13) and the no-research-by-leaders result into two tests on US public-company filings.

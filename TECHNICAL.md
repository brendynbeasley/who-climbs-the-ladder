# Technical notes

This is the technical companion to the [README](README.md). It covers the data, the rules, every test statistic
and how to reproduce the results. All tables are in [results/FINDINGS.md](results/FINDINGS.md), and a methods
review of the original paper is in [METHODS_REVIEW.md](METHODS_REVIEW.md).

## The original study

Gene M. Grossman and Elhanan Helpman, "Quality Ladders in the Theory of Growth," *Review of Economic Studies*
58(1), 1991, pp. 43–61 (NBER Working Paper 3099, September 1989, which is the version I read). A continuum of
products each climbs its own quality ladder with step $`\lambda`$. The leader limit-prices at $`p = \lambda w`$ and
earns $`\pi = (1-1/\lambda)E`$; it is displaced at the Poisson rate $`\iota`$, the innovation rate; leaders without
a cost advantage do no research; and the steady state has $`\iota = (1-\delta)L/a_I - \delta\rho`$ with
$`\delta = 1/\lambda`$ (equation 13) and growth $`g = \iota\ln\lambda`$ (equation 12). There is no empirical
headline number. The paper's testable content is the displacement rate and the zero research by leaders.

## Headline results

| Test | Statistic | Value |
|---|---|---|
| Leaders overtaken within 4 years, all industries | share (N = 511) | 14.48% |
| Implied annual displacement hazard | $`-\ln(1-p)/4`$ | 3.91% |
| Effect of 1 point of R&D/sales on chance of being overtaken | $`\hat\beta`$ (SE), two-sided p, one-sided p | −0.0068 (0.0049), 0.17, 0.91 |
| Leaders' share of research in research industries | aggregate (127 windows) | 37.9% |
| Leaders' share of sales in the same industries | aggregate | 46.8% |
| Leader vs rest-of-industry R&D intensity | medians, Wilcoxon p | 5.0% vs 6.0%, 0.019 |

The model predicts $`\beta > 0`$ and a leaders' research share of zero. Neither holds.

## Data

- **SEC Financial Statement Data Sets**, `https://www.sec.gov/files/dera/data/financial-statement-data-sets/<quarter>.zip`,
  quarters 2013q1–q4, 2017q1–q4, 2021q1–q4 and 2025q1–q4, downloaded November 1, 2026. SEC refused requests from the
  shared address used for this work, so `src/fetch_sec.py` falls back to the Internet Archive's most recent good
  capture of each identical sec.gov address. From `sub.txt` and `num.txt` it keeps 10-K, 10-K/A and 10-KT filings;
  whole-company values (no segments, no co-registrants); standard us-gaap tags only; four-quarter durations in USD.
- **Committed extract:** `data/raw/sec_firm_years.csv.gz`, 18,088 company-years for 8,574 companies, with revenue,
  R&D, cost of revenue, SIC code and business-address country.
- **Tags.** Revenue is the largest of `Revenues`, `RevenueFromContractWithCustomerExcludingAssessedTax`,
  `RevenueFromContractWithCustomerIncludingAssessedTax`, `SalesRevenueNet`, `SalesRevenueGoodsNet`,
  `SalesRevenueServicesNet` and six industry-specific totals. R&D is the largest of `ResearchAndDevelopmentExpense`
  and its two "excluding acquired in-process" variants. Cost of revenue is the largest of `CostOfRevenue`,
  `CostOfGoodsAndServicesSold` and `CostOfGoodsSold`.

## Method (rules fixed before seeing results)

1. **Fiscal years** are assigned by a fixed rule: a year ending July to December belongs to that calendar year,
   one ending January to June to the year before (Nvidia's year ending January 2025 is its 2024). Filings in year Y+1 cover fiscal year Y (as the current year or as
   the prior-year comparison column). The latest filing wins for each company, year and variable.
2. **Sample.** US business address; SIC outside 6000–6799 and outside shell and unclassifiable codes; revenue at
   least $10 million; a firm-year with revenue more than 20 times the firm's own median is a units error and is
   dropped (2 cases). Each company keeps its most recent SIC code in every year. R&D not reported is zero.
3. **Windows and industries.** 2012→2016, 2016→2020, 2020→2024; four-digit SIC industries with at least five companies
   at the window start. 511 industry windows in 196 industries.
4. **Outcome.** The start-year revenue leader is *overtaken* if it still reports at the end and a rival that also
   reported at the start has more revenue. Alternatives: overtaken by any firm, including ones absent at the start;
   *lost lead*, which also counts a leader that stopped reporting; and top-four churn, the share of the start-year
   top four not in the end-year top four.
5. **Regression.** Linear probability model with window fixed effects, standard errors clustered by SIC industry:

```math
\text{Overtaken}_{jw} = \alpha_w + \beta\, s_{jw} + \gamma \ln N_{jw} + \varepsilon_{jw},
\qquad H_0:\ \beta \le 0
```

   Two-sided p-values are reported throughout, with the one-sided p-value against $`H_1:\ \beta > 0`$ alongside.

6. **Model-implied hazard.** From free entry and no-arbitrage in steady state, with gross margin $`m`$ standing in for
   $`1 - 1/\lambda`$ and an assumed discount rate $`\rho = 0.04`$ (checked at 0.02 and 0.08):

```math
s = m\,\frac{\iota}{\rho + \iota} \;\;\Rightarrow\;\; \iota = \frac{\rho\, s}{m - s}
```

7. **Extension.** Research industries are those with $`s \ge 2\%`$, where large companies report R&D almost
   universally. For each, the leader's share of industry R&D against its share of sales, and the leader's R&D
   intensity against the pooled intensity of the rest of the industry (Wilcoxon signed-rank test on the paired
   difference). A regression of *overtaken* on the leader's intensity minus the industry's tests whether research
   protects leaders.

## Full test statistics

Coefficient on R&D intensity in percentage points; all standard errors clustered by industry.

| Specification | $`\hat\beta`$ | SE | 95% CI | p (two-sided) | N |
|---|---|---|---|---|---|
| Overtaken (main) | −0.0068 | 0.0049 | [−0.0165, 0.0029] | 0.17 | 511 |
| Overtaken, no controls | −0.0027 | 0.0043 | [−0.0112, 0.0057] | 0.53 | 511 |
| Overtaken by any firm, incl. new arrivals | −0.0037 | 0.0054 | [−0.0143, 0.0069] | 0.49 | 511 |
| Lost lead (exits count) | −0.0017 | 0.0057 | [−0.0129, 0.0094] | 0.76 | 511 |
| Top-four churn | 0.0003 | 0.0024 | [−0.0044, 0.0051] | 0.89 | 511 |
| Overtaken, control for leader's lead over #2 | −0.0028 | 0.0044 | [−0.0115, 0.0058] | 0.53 | 511 |
| Overtaken, two-digit SIC fixed effects | −0.0017 | 0.0060 | [−0.0136, 0.0101] | 0.77 | 511 |
| Overtaken, leaders still reporting | −0.0071 | 0.0053 | [−0.0174, 0.0033] | 0.18 | 460 |
| Overtaken, industries reporting any R&D | −0.0053 | 0.0053 | [−0.0157, 0.0050] | 0.31 | 303 |
| Overtaken, without 2020–24 window | −0.0054 | 0.0072 | [−0.0195, 0.0087] | 0.45 | 354 |
| Overtaken, logit average marginal effect | −0.0069 | 0.0057 | [−0.0181, 0.0044] | 0.23 | 511 |

In the main specification $`\hat\gamma = 0.058`$ ($`p = 0.052`$) on the log number of companies.

Model-implied against observed four-year displacement, by group median. The "Under 0.1%" group includes the 208
windows with no reported R&D.

| R&D/sales group | Median s | Median margin | Implied hazard, ρ = 4% | Implied 4-year | Observed 4-year |
|---|---|---|---|---|---|
| Under 0.1% | 0 | 31.8% | 0 | 0 | 15.9% |
| 0.1% to 2% | 0.48% | 34.0% | 0.06% | 0.2% | 16.8% |
| 2% to 8% | 3.84% | 38.4% | 0.44% | 1.8% | 7.6% |
| 8% or more | 13.36% | 52.0% | 1.38% | 5.4% | 12.5% |

For the top group the implied four-year displacement is 2.7%, 5.4% and 10.5% at discount rates of 2%, 4% and 8%,
or 0.20, 0.40 and 0.78 points per point of R&D intensity against zero at none. The upper end of the main
confidence interval, 0.29 points, excludes the 4% and 8% slopes but not the 2% one.

Extension, 127 research-industry windows in 55 industries: leaders' share of R&D 37.9% against 46.8% of sales (40.7%
against 50.1% after dropping the 30 leaders that report no standard R&D tag); median leader R&D share 42.4% against
median sales share 44.6%; the leader's R&D share exceeds its sales share in 42.5% of cases; leader R&D intensity
median 5.05% against 5.97% for the rest of the industry, Wilcoxon $`p = 0.019`$. Protection regression,
coefficient on the leader's relative intensity −0.0040 (SE 0.0032), 95% CI [−0.0103, 0.0023], $`p = 0.22`$, N = 127.
Only 12 research-industry leaders were overtaken; the challenger was more research-intensive in 6 of them.

## Reproducing the results

```bash
pip install -r requirements.txt
python src/fetch_sec.py          # optional: rebuilds data/raw/sec_firm_years.csv.gz (16 zips of 70-130 MB)
python src/quality_ladders.py    # writes results/*.csv and results/*.png from the committed extract
```

Python 3.12 or later. The second script runs offline in under a minute.

## Repository layout

| Path | What it is |
|---|---|
| `src/fetch_sec.py` | Downloads the FSDS quarters and writes the committed firm-year extract |
| `src/quality_ladders.py` | Sample, displacement tests, model-implied hazards, extension, figures |
| `data/raw/sec_firm_years.csv.gz` | Revenue, R&D and cost of revenue by company and fiscal year |
| `results/` | Seven CSVs, two figures and FINDINGS.md |

## References

- Garcia-Macia, D., Hsieh, C.-T. & Klenow, P. J. (2019). How destructive is innovation? *Econometrica* 87(5),
  1507–1541.
- Grossman, G. M. & Helpman, E. (1991). Quality ladders in the theory of growth. *Review of Economic Studies*
  58(1), 43–61.
- Grossman, G. M. & Helpman, E. (1991). *Innovation and Growth in the Global Economy*. MIT Press.
- Jones, C. I. (1995). R&D-based models of economic growth. *Journal of Political Economy* 103(4), 759–784.

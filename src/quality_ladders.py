"""Grossman and Helpman (1991) on SEC filings: are industry leaders replaced faster where more is
spent on research, and who does the research?

The quality-ladder model makes two sharp claims about industry leaders.
  1. Leadership is temporary. A leader is displaced when a rival climbs the next rung, which
     happens at the Poisson rate iota, the industry's innovation rate. Industries that spend more
     on R&D (relative to sales) have a higher iota, so their leaders should fall faster.
  2. Leaders do no R&D. A leader who innovates gains less than an outsider who does (the
     replacement effect), so all research is done by challengers.

Test 1 (the replication) uses 4-digit SIC industries of US public companies. For each industry
and four-year window it records whether the start-year revenue leader was overtaken by a rival
by the end year, and relates that to the industry's R&D-to-sales ratio at the start.
Test 2 (the extension) measures how much of each industry's R&D the leader itself does.

Inputs (committed, written by src/fetch_sec.py):
    data/raw/sec_firm_years.csv.gz (revenue, R&D, cost of revenue, SIC code and country by company-year)
Usage:
    python src/quality_ladders.py
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "results"

WINDOWS = [(2012, 2016), (2016, 2020), (2020, 2024)]  # four-year windows; XBRL is complete from 2011
HORIZON = 4              # years per window
MIN_REVENUE = 10e6       # a firm counts in a year only with at least $10 million of revenue
MIN_FIRMS = 5            # an industry needs five such firms in the start year (so a top 4 has rivals)
FINANCE_SIC = (6000, 6799)          # banks, insurers, REITs, funds: revenue is not product sales
EXCLUDED_SIC = {6770, 9995, 9999, 8880, 8888, 8900}  # blank checks, non-operating, unclassifiable
SCALE_JUMP = 20          # a firm-year more than 20x the firm's median revenue is a units error
RD_BINS = [-0.001, 0.001, 0.02, 0.08, 10]           # R&D/sales: (almost) none, low, medium, high
RD_LABELS = ["Under 0.1%", "0.1% to 2%", "2% to 8%", "8% or more"]
RESEARCH_LINE = 0.02     # "research industries" for the extension: R&D at least 2% of sales
RHO = 0.04               # discount rate for the model-implied hazard (judgment; see TECHNICAL.md)
RHO_CHECKS = [0.02, 0.08]  # sensitivity of the implied hazard to that judgment


def load_panel():
    d = pd.read_csv(RAW / "sec_firm_years.csv.gz")
    print(f"Loaded {len(d):,} company-years ({d.cik.nunique():,} companies) from data/raw/sec_firm_years.csv.gz")
    # One industry per company: the SIC code on its most recent filing, so a reclassification
    # is not mistaken for a change of leader.
    last = d.sort_values("year").groupby("cik")[["sic", "countryba"]].last()
    d = d.drop(columns=["sic", "countryba"]).join(last, on="cik")
    steps = [
        ("no SIC code in the Financial Statement Data Sets", d.sic.notna()),
        ("business address outside the US", d.countryba.eq("US")),
        ("finance, insurance, real estate (SIC 6000-6799)", ~d.sic.between(*FINANCE_SIC)),
        ("shell or unclassifiable SIC code", ~d.sic.isin(EXCLUDED_SIC)),
        ("revenue under $10 million", d.revenue >= MIN_REVENUE),
    ]
    keep = pd.Series(True, index=d.index)
    for why, ok in steps:
        drop = keep & ~ok
        print(f"  dropped {drop.sum():>7,} filer-years: {why}")
        keep &= ok
    d = d[keep].copy()
    med = d.groupby("cik").revenue.transform("median")
    bad = d.revenue > SCALE_JUMP * med
    print(f"  dropped {bad.sum():>7,} filer-years: revenue over {SCALE_JUMP}x the firm's own median (units error)")
    d = d[~bad].copy()
    d["sic"] = d.sic.astype(int)
    d["rd"] = d.rd.fillna(0).clip(lower=0)
    d["rd_int"] = d.rd / d.revenue
    d["entity"] = d.sort_values("year").groupby("cik").name.transform("last")
    print(f"Kept {len(d):,} filer-years, {d.cik.nunique():,} firms, {d.sic.nunique()} SIC industries")
    return d


def industry_windows(d):
    """One row per industry x window: leader, its fate, top-4 churn, R&D intensity."""
    rows = []
    for start, end in WINDOWS:
        s0 = d[d.year == start]
        s1 = d[d.year == end]
        for sic, g in s0.groupby("sic"):
            if len(g) < MIN_FIRMS:
                continue
            g = g.sort_values("revenue", ascending=False)
            h = s1[s1.sic == sic].sort_values("revenue", ascending=False)
            lead = g.iloc[0]
            top4 = set(g.cik.iloc[:4])
            top4_end = set(h.cik.iloc[:4])
            present = lead.cik in set(h.cik)
            new_lead = h.iloc[0] if len(h) else None
            # Main outcome: overtaken by a rival that was already reporting in the start year. A firm
            # absent from the start-year data may be a true newcomer or a reporting gap (a custom
            # revenue tag, a late filing), so overtaking by such firms is counted separately.
            h_inc = h[h.cik.isin(set(g.cik))]
            inc_lead = h_inc.iloc[0] if len(h_inc) else None
            overtaken = bool(present and inc_lead.cik != lead.cik)
            overtaken_any = bool(present and new_lead.cik != lead.cik)
            cogs_ok = g.cogs.notna()
            margin = 1 - g.cogs[cogs_ok].sum() / g.revenue[cogs_ok].sum() if cogs_ok.sum() >= 3 else np.nan
            ind_rd = g.rd.sum()
            row = dict(
                window=f"{start}-{end}", start=start, end=end, sic=sic, n_firms=len(g),
                n_firms_end=len(h), industry_revenue_bn=g.revenue.sum() / 1e9,
                rd_intensity=ind_rd / g.revenue.sum(), gross_margin=margin,
                leader=lead.entity, leader_cik=lead.cik, leader_revenue_bn=lead.revenue / 1e9,
                leader_share=lead.revenue / g.revenue.sum(),
                leader_lead_ratio=lead.revenue / g.revenue.iloc[1],
                leader_rd_bn=lead.rd / 1e9, leader_rd_int=lead.rd_int,
                leader_rd_share=lead.rd / ind_rd if ind_rd > 0 else np.nan,
                leader_present_end=present, overtaken=overtaken, overtaken_any=overtaken_any,
                lost_lead=overtaken_any or not present,
                top4_churn=len(top4 - top4_end) / 4,
                end_leader=inc_lead.entity if inc_lead is not None else None,
                end_leader_revenue_bn=inc_lead.revenue / 1e9 if inc_lead is not None else np.nan,
                end_leader_any=new_lead.entity if new_lead is not None else None,
                leader_revenue_end_bn=(h.loc[h.cik == lead.cik, "revenue"].iloc[0] / 1e9) if present else np.nan,
            )
            if overtaken:
                was = g[g.cik == inc_lead.cik]
                row["challenger_rd_int_start"] = was.rd_int.iloc[0]
                row["challenger_revenue_start_bn"] = was.revenue.iloc[0] / 1e9
                row["challenger_rd_start_bn"] = was.rd.iloc[0] / 1e9
                row["challenger_rank_start"] = int(np.flatnonzero(g.cik.values == inc_lead.cik)[0] + 1)
            rows.append(row)
    iw = pd.DataFrame(rows)
    iw["rd_bin"] = pd.cut(iw.rd_intensity, RD_BINS, labels=RD_LABELS)
    iw["log_n"] = np.log(iw.n_firms)
    iw["rd_pct"] = 100 * iw.rd_intensity
    print(f"Built {len(iw):,} industry-windows ({iw.sic.nunique()} industries with {MIN_FIRMS}+ firms at a window start)")
    return iw


def hazard(p, years=HORIZON):
    """Annual Poisson hazard implied by a displacement probability over one window."""
    return -np.log(1 - p) / years


def table_by_bin(iw):
    out = []
    for label, g in iw.groupby("rd_bin", observed=True):
        p = g.overtaken.mean()
        p_any = g.lost_lead.mean()
        out.append(dict(rd_bin=label, industry_windows=len(g), zero_rd_windows=int((g.rd_intensity == 0).sum()),
                        median_rd_pct=100 * g.rd_intensity.median(),
                        overtaken_pct=100 * p, se_pct=100 * np.sqrt(p * (1 - p) / len(g)),
                        lost_lead_pct=100 * p_any, top4_churn_pct=100 * g.top4_churn.mean(),
                        annual_hazard_pct=100 * hazard(p),
                        expected_tenure_years=1 / hazard(p) if p > 0 else np.inf,
                        median_firms=g.n_firms.median()))
    p = iw.overtaken.mean()
    out.append(dict(rd_bin="All", industry_windows=len(iw), zero_rd_windows=int((iw.rd_intensity == 0).sum()),
                    median_rd_pct=100 * iw.rd_intensity.median(),
                    overtaken_pct=100 * p, se_pct=100 * np.sqrt(p * (1 - p) / len(iw)),
                    lost_lead_pct=100 * iw.lost_lead.mean(), top4_churn_pct=100 * iw.top4_churn.mean(),
                    annual_hazard_pct=100 * hazard(p), expected_tenure_years=1 / hazard(p),
                    median_firms=iw.n_firms.median()))
    return pd.DataFrame(out)


def regressions(iw):
    res = []
    specs = [
        ("overtaken", "overtaken ~ rd_pct + log_n + C(window)", iw),
        ("overtaken, no controls", "overtaken ~ rd_pct + C(window)", iw),
        ("overtaken by any firm, incl. new arrivals", "overtaken_any ~ rd_pct + log_n + C(window)", iw),
        ("lost lead (exits count)", "lost_lead ~ rd_pct + log_n + C(window)", iw),
        ("top-4 churn", "top4_churn ~ rd_pct + log_n + C(window)", iw),
        ("overtaken, lead-ratio control", "overtaken ~ rd_pct + log_n + np.log(leader_lead_ratio) + C(window)", iw),
        ("overtaken, 2-digit SIC FE", "overtaken ~ rd_pct + log_n + C(window) + C(sic2)", iw),
        ("overtaken, leader still present", "overtaken ~ rd_pct + log_n + C(window)", iw[iw.leader_present_end]),
        ("overtaken, industries reporting R&D", "overtaken ~ rd_pct + log_n + C(window)", iw[iw.rd_intensity > 0]),
        ("overtaken, without 2020-2024 window", "overtaken ~ rd_pct + log_n + C(window)", iw[iw.start < 2020]),
    ]
    for name, f, data in specs:
        data = data.assign(overtaken=data.overtaken.astype(float), lost_lead=data.lost_lead.astype(float),
                           overtaken_any=data.overtaken_any.astype(float),
                           sic2=data.sic // 100)
        m = smf.ols(f, data=data).fit(cov_type="cluster", cov_kwds={"groups": data.sic})
        b, se = m.params["rd_pct"], m.bse["rd_pct"]
        lo, hi = m.conf_int().loc["rd_pct"]
        res.append(dict(model=name, coef_per_rd_point=b, se=se, ci_low=lo, ci_high=hi,
                        p_value=m.pvalues["rd_pct"], p_one_sided_positive=stats.norm.sf(b / se), n=int(m.nobs), clusters=data.sic.nunique(),
                        mean_outcome=m.model.endog.mean(),
                        coef_log_n=m.params.get("log_n", np.nan), p_log_n=m.pvalues.get("log_n", np.nan)))
    # logit, for the binary outcome
    data = iw.assign(overtaken=iw.overtaken.astype(float))
    lg = smf.logit("overtaken ~ rd_pct + log_n + C(window)", data=data).fit(
        disp=0, cov_type="cluster", cov_kwds={"groups": data.sic})
    me = lg.get_margeff().summary_frame().loc["rd_pct"]
    res.append(dict(model="overtaken, logit (avg. marginal effect)", coef_per_rd_point=me["dy/dx"],
                    se=me["Std. Err."], ci_low=me["Conf. Int. Low"], ci_high=me["Cont. Int. Hi."],
                    p_value=me["Pr(>|z|)"], p_one_sided_positive=stats.norm.sf(me["dy/dx"] / me["Std. Err."]),
                    n=int(lg.nobs), clusters=data.sic.nunique(),
                    mean_outcome=data.overtaken.mean(), coef_log_n=np.nan, p_log_n=np.nan))
    return pd.DataFrame(res)


def implied_hazard(iw):
    """Model-implied hazard from R&D intensity s and margin m: iota = rho*s/(m - s), bin medians."""
    out = []
    for label, g in iw.groupby("rd_bin", observed=True):
        s, m = g.rd_intensity.median(), g.gross_margin.median()
        iota = RHO * s / (m - s) if m > s else np.inf
        p_obs = g.overtaken.mean()
        row = dict(rd_bin=label, median_rd=s, median_gross_margin=m, rho=RHO,
                   implied_hazard_pct=100 * iota, implied_window_pct=100 * (1 - np.exp(-HORIZON * iota)),
                   observed_window_pct=100 * p_obs, observed_hazard_pct=100 * hazard(p_obs))
        # implied slope: implied 4-year displacement (points) per point of R&D intensity, against zero at s = 0
        row["implied_slope_per_rd_point"] = row["implied_window_pct"] / (100 * s) if s > 0 else np.nan
        for r in RHO_CHECKS:
            io = r * s / (m - s) if m > s else np.inf
            row[f"implied_hazard_pct_rho{int(100 * r)}"] = 100 * io
            row[f"implied_window_pct_rho{int(100 * r)}"] = 100 * (1 - np.exp(-HORIZON * io))
            row[f"implied_slope_per_rd_point_rho{int(100 * r)}"] = 100 * (1 - np.exp(-HORIZON * io)) / (100 * s) if s > 0 else np.nan
        out.append(row)
    return pd.DataFrame(out)


def leader_research(iw):
    """Extension: do leaders do research? Measured in research industries (R&D at least 2% of sales),
    where nearly every large company reports R&D, so a missing tag rarely means a missing number."""
    r = iw[iw.rd_intensity >= RESEARCH_LINE].copy()
    rest_rev = r.industry_revenue_bn * (1 - r.leader_share)
    rest_rd = r.industry_revenue_bn * r.rd_intensity * (1 - r.leader_rd_share)
    r["rest_rd_int"] = rest_rd / rest_rev
    diff = r.leader_rd_int - r.rest_rd_int
    w = stats.wilcoxon(diff)
    total_rd = (r.industry_revenue_bn * r.rd_intensity).sum()
    agg = dict(
        research_industry_windows=len(r), research_industries=r.sic.nunique(),
        leaders_share_of_sales_pct=100 * r.leader_revenue_bn.sum() / r.industry_revenue_bn.sum(),
        leaders_share_of_rd_pct=100 * (r.leader_rd_share * r.industry_revenue_bn * r.rd_intensity).sum() / total_rd,
        median_leader_sales_share_pct=100 * r.leader_share.median(),
        median_leader_rd_share_pct=100 * r.leader_rd_share.median(),
        pct_leaders_reporting_zero_rd=100 * (r.leader_rd_int == 0).mean(),
        pct_leader_rd_share_above_sales_share=100 * (r.leader_rd_share > r.leader_share).mean(),
        median_leader_rd_int_pct=100 * r.leader_rd_int.median(),
        median_rest_rd_int_pct=100 * r.rest_rd_int.median(),
        pct_leader_more_rd_intensive_than_rest=100 * (diff > 0).mean(),
        wilcoxon_p_leader_vs_rest=w.pvalue,
    )
    # Some leaders tag R&D only with a company-specific label (3M, Xerox), which reads as zero here.
    # Dropping the zero-R&D leaders gives the other bound.
    p = r[r.leader_rd_int > 0]
    agg.update(nonzero_leader_windows=len(p),
               nonzero_leaders_share_of_sales_pct=100 * p.leader_revenue_bn.sum() / p.industry_revenue_bn.sum(),
               nonzero_leaders_share_of_rd_pct=100 * (p.leader_rd_share * p.industry_revenue_bn * p.rd_intensity).sum()
               / (p.industry_revenue_bn * p.rd_intensity).sum())
    # Does a leader's own research protect it? In the basic model there is none to test.
    d = r.assign(overtaken=r.overtaken.astype(float), rel=100 * diff)
    m = smf.ols("overtaken ~ rel + rd_pct + log_n + C(window)", data=d).fit(
        cov_type="cluster", cov_kwds={"groups": d.sic})
    lo, hi = m.conf_int().loc["rel"]
    agg.update(protect_coef_per_point=m.params["rel"], protect_se=m.bse["rel"], protect_ci_low=lo,
               protect_ci_high=hi, protect_p=m.pvalues["rel"], protect_n=int(m.nobs))
    # Who passed the leaders in research industries, and were they more research-intensive?
    ov = r[r.overtaken]
    agg.update(research_overtakings=len(ov),
               pct_challenger_more_rd_intensive=100 * (ov.challenger_rd_int_start > ov.leader_rd_int).mean(),
               challenger_median_rank_start=ov.challenger_rank_start.median())
    out = pd.DataFrame([agg]).T.reset_index().rename(columns={"index": "statistic", 0: "value"})
    return out, r


NAMED_SIC = {3674: "Semiconductors", 2834: "Pharmaceutical preparations", 7372: "Prepackaged software",
             3571: "Electronic computers", 3663: "Radio and TV broadcasting equipment",
             2836: "Biological products", 3841: "Surgical and medical instruments", 7370: "Computer services",
             3711: "Motor vehicles", 2911: "Petroleum refining", 5411: "Grocery stores",
             4813: "Telephone communications", 7374: "Computer processing and data", 5961: "Catalog and mail-order",
             3714: "Motor vehicle parts", 2080: "Beverages", 3572: "Computer storage devices",
             4512: "Scheduled air transport", 5331: "Variety stores", 3845: "Electromedical apparatus"}


def names_table(iw):
    w = iw[iw.sic.isin(NAMED_SIC)].copy()
    w["industry"] = w.sic.map(NAMED_SIC)
    cols = ["industry", "sic", "window", "n_firms", "rd_intensity", "leader", "leader_revenue_bn", "leader_rd_bn",
            "leader_rd_int",
            "leader_rd_share", "end_leader", "end_leader_revenue_bn", "overtaken", "lost_lead", "top4_churn"]
    return w[cols].sort_values(["rd_intensity", "window"], ascending=[False, True])


def figures(tab, research):
    t = tab[tab.rd_bin != "All"]
    fig, ax = plt.subplots(figsize=(7, 4.2))
    x = np.arange(len(t))
    ax.bar(x, t.overtaken_pct, yerr=1.96 * t.se_pct, color="#4C72B0", capsize=4)
    for i, r in enumerate(t.itertuples()):
        ax.text(i, r.overtaken_pct + 1.96 * r.se_pct + 1, f"{r.overtaken_pct:.0f}%\n(n={r.industry_windows})",
                ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x, t.rd_bin)
    ax.set_xlabel("Industry R&D spending as a share of sales, at the start of the window")
    ax.set_ylabel("Leaders overtaken within 4 years (%)")
    ax.set_ylim(0, max(t.overtaken_pct + 1.96 * t.se_pct) + 12)
    ax.set_title("Revenue leaders of US industries overtaken by a rival, 2012-2024")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "displacement_by_rd.png", dpi=150)
    plt.close(fig)

    d = research
    fig, ax = plt.subplots(figsize=(6, 5.5))
    ax.scatter(100 * d.leader_share, 100 * d.leader_rd_share, s=14, alpha=0.5, color="#4C72B0")
    ax.plot([0, 100], [0, 100], color="grey", lw=1, ls="--")
    ax.axhline(0, color="#C44E52", lw=1.5)
    ax.text(62, 3, "Grossman-Helpman: leaders do no R&D", color="#C44E52", fontsize=9)
    ax.text(83, 90, "R&D share =\nsales share", color="grey", fontsize=9, ha="left")
    ax.set_xlabel("Leader's share of industry sales (%)")
    ax.set_ylabel("Leader's share of industry R&D (%)")
    ax.set_xlim(0, 100)
    ax.set_ylim(-3, 104)
    ax.set_title("Industry leaders' share of R&D (start years 2012, 2016, 2020)")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "leader_rd_share.png", dpi=150)
    plt.close(fig)


def main():
    OUT.mkdir(exist_ok=True)
    d = load_panel()
    iw = industry_windows(d)
    tab = table_by_bin(iw)
    reg = regressions(iw)
    imp = implied_hazard(iw)
    ext, research = leader_research(iw)
    names = names_table(iw)
    iw.to_csv(OUT / "industry_windows.csv", index=False)
    tab.to_csv(OUT / "displacement_by_rd.csv", index=False)
    reg.to_csv(OUT / "regressions.csv", index=False)
    imp.to_csv(OUT / "implied_hazard.csv", index=False)
    ext.to_csv(OUT / "leader_research.csv", index=False)
    names.to_csv(OUT / "named_industries.csv", index=False)
    cols = ["window", "sic", "n_firms", "rd_intensity", "leader", "leader_share", "leader_rd_int", "rest_rd_int",
            "leader_rd_share", "overtaken", "end_leader"]
    research[cols].sort_values(["window", "sic"]).to_csv(OUT / "research_industries.csv", index=False)
    figures(tab, research)
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", 30)
    print("\nDisplacement by R&D intensity\n", tab.round(2).to_string(index=False))
    print("\nRegressions (coefficient per percentage point of R&D/sales)\n", reg.round(4).to_string(index=False))
    print("\nModel-implied vs observed hazard\n", imp.round(3).to_string(index=False))
    print("\nLeader research\n", ext.to_string(index=False))
    print("\nWrote 7 CSVs and 2 figures to results/")


if __name__ == "__main__":
    main()

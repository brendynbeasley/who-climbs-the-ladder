"""Download the SEC Financial Statement Data Sets and write one compact firm-year file.

The SEC's Financial Statement Data Sets (FSDS) hold every number tagged in every XBRL filing,
one zip per quarter of filing dates. From the 10-K annual reports in them this script takes
each company's revenue, cost of revenue and R&D expense, plus its SIC industry code and
business address. Each zip is fetched from www.sec.gov; if SEC refuses the request (it blocks
busy shared addresses), the script falls back to the Internet Archive's most recent good copy
of the same sec.gov address, which is the identical file.

Fiscal years are assigned to calendar years by a fixed rule: a year ending in July through
December belongs to that calendar year; a year ending in January through June belongs to the
year before (so Nvidia's year ending January 2025 is its 2024, and Microsoft's year ending
June 2017 is its 2016). A 10-K also
reports the prior year, so the four quarters of filings in year Y+1 cover every company's
fiscal year Y, either as the current year or as the comparison column.

Writes (committed, so the analysis runs offline):
    data/raw/sec_firm_years.csv.gz   one row per company and fiscal year, values in US dollars
Each zip (70-130 MB) is read once; the 10-K values extracted from it are kept as
data/raw/sec/fsds_<quarter>_annual.csv.gz (ignored by git, a few MB in all) and the zip is deleted.
Reruns reuse the extracted files.

Usage:
    python src/fetch_sec.py
"""

import io
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
SEC_DIR = RAW / "sec"

YEARS = [2012, 2016, 2020, 2024]  # window end points; four-year windows, XBRL complete from 2011
HEADERS = {"User-Agent": "Brendyn Beasley research 83249437+brendynbeasley@users.noreply.github.com",
           "Accept-Encoding": "gzip, deflate"}
PAUSE = 0.5                       # seconds between requests
FSDS = "https://www.sec.gov/files/dera/data/financial-statement-data-sets/{q}.zip"

# Total revenue appears under several standard tags, some specific to an industry; the largest
# reported in a filing is used. Companies that tagged revenue only with their own custom tag
# (ExxonMobil in its 2012 report, for example) are missed for that year.
REVENUE_TAGS = ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
                "RevenueFromContractWithCustomerIncludingAssessedTax", "SalesRevenueNet",
                "SalesRevenueGoodsNet", "SalesRevenueServicesNet",
                "SalesAndOtherOperatingRevenueIncludingSalesBasedTaxes", "OilAndGasRevenue",
                "ElectricUtilityRevenue", "RegulatedAndUnregulatedOperatingRevenue",
                "HealthCareOrganizationRevenue", "RevenueMineralSales"]
RD_TAGS = ["ResearchAndDevelopmentExpense", "ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost",
           "ResearchAndDevelopmentExpenseSoftwareExcludingAcquiredInProcessCost"]
COGS_TAGS = ["CostOfRevenue", "CostOfGoodsAndServicesSold", "CostOfGoodsSold"]
GROUP = {t: "revenue" for t in REVENUE_TAGS} | {t: "rd" for t in RD_TAGS} | {t: "cogs" for t in COGS_TAGS}


def patient_get(url, tries=6, **kw):
    """GET with retries and a growing wait; the Internet Archive throttles bursts of requests."""
    for attempt in range(tries):
        try:
            r = requests.get(url, timeout=900, **kw)
            if r.status_code == 200:
                return r
            print(f"    {r.status_code} from {url[:80]}; retrying")
        except requests.RequestException as e:
            print(f"    {type(e).__name__} for {url[:80]}; retrying")
        time.sleep(30 * (attempt + 1))
    return None


def archive_copy(url):
    """Most recent good Internet Archive capture of url, as originally served."""
    r = patient_get("https://web.archive.org/cdx/search/cdx",
                    params={"url": url, "filter": ["statuscode:200", "mimetype:application/octet-stream"],
                            "output": "json"})
    if r is None:
        return None
    cdx = r.json()
    if len(cdx) < 2:
        return None
    stamp = cdx[-1][1]
    return f"https://web.archive.org/web/{stamp}id_/{url}"


def get_zip(q):
    path = SEC_DIR / f"fsds_{q}.zip"
    if path.exists():
        return path
    url = FSDS.format(q=q)
    time.sleep(PAUSE)
    try:
        r = requests.get(url, headers=HEADERS, timeout=900)
        ok = r.status_code == 200 and r.content.startswith(b"PK")
    except requests.RequestException:
        ok = False
    source = "sec.gov"
    if not ok:
        alt = archive_copy(url)
        if alt is None:
            print(f"  {q}: not available from sec.gov or the Internet Archive; skipped")
            return None
        time.sleep(PAUSE)
        r = patient_get(alt)
        source = "Internet Archive copy of the sec.gov file"
        if r is None or not r.content.startswith(b"PK"):
            print(f"  {q}: archive copy failed; skipped")
            return None
    tmp = path.with_suffix(".part")
    tmp.write_bytes(r.content)
    tmp.rename(path)
    print(f"  {q}: {len(r.content) / 1e6:.0f} MB from {source}")
    return path


def read_quarter(path):
    """Annual (four-quarter) USD values of the wanted tags from 10-K filings in one FSDS zip.
    Only whole-company figures are kept: no segment breakdowns, no co-registrants, standard tags only."""
    with zipfile.ZipFile(path) as z:
        sub = pd.read_csv(z.open("sub.txt"), sep="\t", dtype=str,
                          usecols=["adsh", "cik", "name", "sic", "countryba", "form", "filed"])
        sub = sub[sub.form.isin(["10-K", "10-K/A", "10-KT"])]
        parts = []
        cols = ["adsh", "tag", "version", "segments", "coreg", "ddate", "qtrs", "uom", "value"]
        for chunk in pd.read_csv(z.open("num.txt"), sep="\t", dtype=str, usecols=cols, chunksize=2_000_000,
                                 on_bad_lines="skip", quoting=3):
            c = chunk[chunk.tag.isin(GROUP.keys()) & (chunk.qtrs == "4") & (chunk.uom == "USD")
                      & chunk.coreg.isna() & chunk.segments.isna() & chunk.version.str.startswith("us-gaap")]
            parts.append(c[["adsh", "tag", "ddate", "value"]])
    num = pd.concat(parts).merge(sub, on="adsh")
    num["value"] = pd.to_numeric(num.value, errors="coerce")
    return num


def main():
    SEC_DIR.mkdir(parents=True, exist_ok=True)
    frames, missing = [], []
    for y in YEARS:
        for k in range(1, 5):
            q = f"{y + 1}q{k}"
            slim = SEC_DIR / f"fsds_{q}_annual.csv.gz"
            if slim.exists():
                n = pd.read_csv(slim, dtype={"cik": str, "sic": str, "ddate": str, "filed": str})
            else:
                path = get_zip(q)
                if path is None:
                    missing.append(q)
                    continue
                n = read_quarter(path)
                n.to_csv(slim, index=False, compression="gzip")
                path.unlink()  # the zip is 70-130 MB; only the extracted values are kept
            frames.append(n)
            print(f"  {q}: {n.adsh.nunique():,} annual reports, {len(n):,} values kept")
    if missing:
        raise SystemExit(f"Quarters not downloaded: {missing}. A missing quarter drops companies; rerun later.")
    v = pd.concat(frames, ignore_index=True)
    d = pd.to_datetime(v.ddate, format="%Y%m%d", errors="coerce")
    v["year"] = d.dt.year - (d.dt.month <= 6).astype(int)
    v = v[v.year.isin(YEARS)]
    v["group"] = v.tag.map(GROUP)
    # Latest filing wins (restatements and amended reports replace earlier figures); within a filing,
    # the largest value across the tags of a group is the total.
    latest = v.groupby(["cik", "year", "group"]).filed.transform("max")
    v = v[v.filed == latest]
    wide = v.groupby(["cik", "year", "group"]).value.max().unstack("group").reset_index()
    info = v.sort_values("filed").groupby(["cik", "year"])[["name", "sic", "countryba", "filed"]].last().reset_index()
    out = wide.merge(info, on=["cik", "year"])
    out = out[out.revenue.notna()]
    out = out[["cik", "name", "year", "sic", "countryba", "revenue", "rd", "cogs", "filed"]]
    out.to_csv(RAW / "sec_firm_years.csv.gz", index=False, compression="gzip")
    print(f"Wrote data/raw/sec_firm_years.csv.gz: {len(out):,} company-years, {out.cik.nunique():,} companies")
    print(out.groupby("year").agg(companies=("cik", "size"), with_rd=("rd", "count")).to_string())


if __name__ == "__main__":
    main()

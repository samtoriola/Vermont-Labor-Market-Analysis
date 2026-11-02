# Vermont Labor Market Overview — a walkthrough

A talk track for showing the dashboard to someone seeing it for the first time.
Roughly eight minutes at a normal pace. Figures are the ones currently on screen;
`workfiles/00_headline_figures.csv` is where each one comes from.

---

## The opening (60 seconds)

> This is the Vermont Labor Market Overview. It answers one question in several
> ways: **where is the work in Vermont, what does it pay, and does what VSCS
> produces line up with it?**
>
> Everything you see is fixed data, not a live connection. It was pulled once
> from five sources — Lightcast occupation and posting exports, BLS wage
> percentiles, Census household surveys, IPEDS completions, and the MIT Living
> Wage — and committed to the repository. Nothing queries anything while you
> click, so it cannot go stale under you mid-meeting and it cannot cost anything
> to run.
>
> Two rules worth holding onto before we start.

**Rule one — jobs are not people.** Almost every chart counts *jobs located in
Vermont*. Someone holding two jobs is in the count twice. Only the home page's
second tile counts people. Nothing on the dashboard asks you to subtract one from
the other, because the answer would be meaningless.

**Rule two — the benchmark.** Where you see a wage compared to a floor, the floor
is **$49,816 a year** — MIT's living wage for one adult with no children,
$23.95 an hour over 2,080 hours. It is a cost-of-living floor, not a policy
position and not the minimum wage.

---

## Home (30 seconds)

> Four numbers, four sources. 326,582 jobs. 335,775 employed Vermonters — that's
> the one people count. About 48,900 openings a year. 1,983 VSCS completions.
>
> The tiles carry no source line on purpose; the landing page stays quiet. Every
> source is in Methods, and `workfiles/14_home_tiles.csv` has a row per tile.

Then go straight to the sidebar: *"The sidebar is grouped by question, not by
vendor. Top to bottom it goes from what the labor market looks like, to what it
pays, to what VSCS could do about it."*

---

## Tab by tab

**Overview** — the one-screen answer. The headline is that **41% of Vermont's
priced jobs pay below the living-wage benchmark**. Everything after this tab is
that finding taken apart.

**Employment** — the shape of the labor market. Two panels: industry sectors, and
the 22 occupation groups. The occupation panel has a measure control — jobs,
typical pay, or entry credential — over the same rows, so you can watch the
ranking reorder.

**Wage quality** — the benchmark, applied.
- *Wage benchmark* carries two measures, and the gap between them is the point.
  **Share of jobs below** finds the work least likely to pay a living wage.
  **Jobs below** finds where most of the underpaid work actually sits. They name
  different groups: one is a rate, the other is a rate times employment.
- *County living wage* is the only place the floor varies. MIT publishes a figure
  per county, $45,323 to $53,768. Every other tab uses one statewide number, so
  this panel shows what that simplification costs.

**Demand & growth** — forward-looking. *General demand* is the one panel that
compares places rather than ranking categories: what employers ask for at the
door, read off job postings. *Hiring and growth* is openings and projected
growth. Openings include replacing people who leave, not only new positions —
that distinction is why the number is as large as it is.

**Pathways** — the credential ladder, counted as jobs. *By credential level* is
what each rung pays; the midpoint high-school job is about $49,969, which lands
almost exactly on the benchmark. *Which credentials pay* is the return to each
rung. This tab counts jobs and the credential they ask for at entry, not what
workers hold.

**Opportunities** — a composite score across 406 occupations with at least 100
jobs and a published wage, built from four components: scale, growth, demand and
pay. Say plainly that **the four weights are equal**, that equal is a choice
nobody has made deliberately yet, and that the panel exposes the components so
the score can be argued with.

**VSCS alignment** — the question the project exists for. *Production by award*
is what VSCS graduates, from IPEDS. *Against demand* sets that production against
Vermont openings. Two numbers to say out loud: **1,700 of 1,983 completions land
in a Vermont occupation**, and across the occupations VSCS feeds there are about
**9.8 openings a year for every graduate attributed**.
> Flag the modelling here, don't hide it: no graduate is recorded as entering a
> specific occupation. Each program's completions are split across the
> occupations its CIP code maps to, in proportion to Vermont employment. That is
> why the graduate figures carry a decimal — they are an allocation, not a
> headcount.

**Regions** — all 14 counties, on a map and in a table. The one thing to say
carefully: **the map mixes two populations.** Jobs and typical pay are the
*workplaces located* in a county; population, attainment and income are the
county's *residents*, from the Census ACS. People commute across county lines, so
the two sides do not describe the same group, and the table note says so.

**About** — what the dashboard covers and, more usefully, what it does not.

**Methods** — the register. One row per section: what it shows, which source,
which data file, and which workfile reproduces it. *"If anyone wants to check a
number, this is the page, and every figure on screen can be traced to a CSV in
`workfiles/`."*

---

## Closing (30 seconds)

> Three things to take away.
>
> One — 41% of Vermont's work pays below what it costs one adult to live here,
> and the work least likely to pay a living wage is not where most of the
> underpaid work is. Both are on the Wage quality tab.
>
> Two — VSCS production is small against demand in the occupations it feeds,
> roughly ten openings a year per graduate.
>
> Three — the opportunity score's weights are open. They are equal because nobody
> has set them, and setting them is a VSCS decision, not a data one.

End on Methods, not on a chart: *"Every number here can be checked, and the page
that tells you how is the last one in the sidebar."*

---

## Questions you will get

**"Why 326,582 jobs on the home page and 325,132 in the charts?"**
1,450 jobs in military occupations and SOC codes outside the 22 occupation
groups. The export carries them in the statewide total; the charts drop them
because they have no group, no credential and no pay ladder to sit under. It is
0.4% of employment, and Methods states it as a rule.

**"Is this live?"** No. It is a snapshot, committed to the repository and
rebuilt deliberately. The vintage of every source is on Methods.

**"Can we filter it to our region/program?"** The Regions tab goes to county.
Below county, the microdata areas and county lines do not nest, so it would be a
new build rather than a filter.

**"Where did the living wage come from?"** MIT's Living Wage Calculator, 2025,
one adult with no children. Changing the household composition changes every
share on the Wage quality tab, which is why the assumption is named in the
source line under each chart.

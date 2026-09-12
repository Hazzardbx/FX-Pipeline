select 
	usd.date,
	usd.rate as eur_to_usd,
	cny.rate as eur_to_cny,
	cny.rate / usd.rate as usd_to_cny
from xchange_rates as usd 
join xchange_rates as cny 
	on usd.date = cny.date 
where usd.quote = 'USD' 
	and cny.quote = 'CNY' order by "date" ;


alter table xchange_rates add column if not exists  ingested_at timestamp default current_timestamp; 
--08/09/2026 | Added extra column to improve results with the date and time it was added.

select 
	base,
	quote,
	MIN(date) as min_date,
	MAX(date) as max_date
	from xchange_rates
	group by base, quote;


--check variation between first and last day to use in streamlit
--added 08/09/2026
select 
	d.base,
	d.quote,
	first.rate as ini_rate,
	last.rate as final_rate,
	(last.rate - first.rate) / first.rate * 100 as pct_change
from (
	select base, quote, MIN(date) as min_date, MAX(date) as max_date
	from xchange_rates
	group by base, quote
) as d
join xchange_rates as first
	on d.base = first.base and d.quote = first.quote and d.min_date = first.date
join xchange_rates as last
	on d.base = last.base and d.quote = last.quote and d.max_date = last.date
order by pct_change desc;


--make it a view to avoid executing the query again
--added 09/09/2026
--added 12/09/2026 added start and end dates, they were missing
CREATE OR REPLACE VIEW pct_change_view AS
select 
	d.base,
	d.quote,
	d.min_date as start_date,
	d.max_date as end_date,
	first.rate as ini_rate,
	last.rate as final_rate,
	(last.rate - first.rate) / first.rate * 100 as pct_change
from (
	select base, quote, MIN(date) as min_date, MAX(date) as max_date
	from xchange_rates
	group by base, quote
) as d
join xchange_rates as first
	on d.base = first.base and d.quote = first.quote and d.min_date = first.date
join xchange_rates as last
	on d.base = last.base and d.quote = last.quote and d.max_date = last.date
order by pct_change desc;

select * from pct_change_view;


-- ============================================
-- VOLATILITY (how much a rate swings)
-- ============================================

-- v1: raw STDDEV — kept for reference only, DO NOT use to compare currencies
-- added 10/09/2026
select base, quote, stddev(rate) as volatility
from xchange_rates
group by base, quote
order by volatility desc;

-- WHY v1 IS WRONG: raw stddev is bigger just because the rate itself is bigger
-- (JPY ~150-180 vs GBP ~0.85) -> not a fair comparison across currency pairs.
-- FIX: divide by the mean -> coefficient of variation (CV) = scale-independent.
CREATE OR REPLACE VIEW volatility_view AS
select base, quote, stddev(rate) / avg(rate) as volatility -- CV: stddev/mean, comparable across currencies
from xchange_rates
group by base, quote
order by volatility desc;

select * from volatility_view;


-- ============================================
-- TREND (rate over time, no aggregation — for line chart)
-- ============================================
-- added 10/09/2026
CREATE OR REPLACE VIEW trend_view AS
select date, base, quote, rate
from xchange_rates
order by date;

select * from trend_view limit 5;


-- ============================================
-- CORRELATION (how pairs of currencies move together)
-- ============================================
-- added 10/09/2026
-- works for ALL pairs at once, not just one hardcoded pair
-- self-join: match same date across two rows of the same table
-- a.quote < b.quote = dedup trick, kills mirror pairs (CNY-USD / USD-CNY) and self-pairs
CREATE OR REPLACE VIEW correlation_view AS
select 
	a.quote as currency_a,
	b.quote as currency_b,
	CORR(a.rate, b.rate) as correlation
from xchange_rates as a
join xchange_rates as b
	on a.date = b.date
	and a.quote < b.quote
group by a.quote, b.quote
order by correlation desc;

select * from correlation_view;
	
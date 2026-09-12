-- ============================================
-- PRICE CHANGE (% change from first to last date per currency pair)
-- ============================================
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
-- Raw standard deviation isn't comparable across currencies — it's bigger just
-- because the rate itself is bigger (JPY ~150-180 vs GBP ~0.85), not because
-- JPY is actually more volatile. Coefficient of variation (stddev / mean)
-- normalizes for scale, making currencies directly comparable.
CREATE OR REPLACE VIEW volatility_view AS
select base, quote, stddev(rate) / avg(rate) as volatility -- CV: stddev/mean, comparable across currencies
from xchange_rates
group by base, quote
order by volatility desc;

select * from volatility_view;


-- ============================================
-- TREND (rate over time, no aggregation — for line chart)
-- ============================================
CREATE OR REPLACE VIEW trend_view AS
select date, base, quote, rate
from xchange_rates
order by date;

select * from trend_view limit 5;


-- ============================================
-- CORRELATION (how pairs of currencies move together)
-- ============================================
-- Self-join: match same date across two rows of the same table.
-- a.quote < b.quote avoids duplicate pairs (CNY-USD and USD-CNY) and self-pairs.
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

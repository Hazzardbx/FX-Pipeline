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
	
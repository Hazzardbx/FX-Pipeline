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


--publicar como view, para o Streamlit ler direto sem repetir a query
--added 09/09/2026
CREATE OR REPLACE VIEW pct_change_view AS
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

select * from pct_change_view;


--volatility: quanto a taxa oscila. primeira tentativa (STDDEV bruto)
--added 10/09/2026
select base, quote, stddev(rate) as volatility
from xchange_rates
group by base, quote
order by volatility desc;

--nota: STDDEV bruto favorece moedas com escala maior (ex. JPY ~150-180 vs GBP ~0.85),
--nao e comparavel entre moedas. corrigido para coefficient of variation (stddev/media).
CREATE OR REPLACE VIEW volatility_view AS
select base, quote, stddev(rate) / avg(rate) as volatility --coefficient of variation, compara moedas independentemente da escala
from xchange_rates
group by base, quote
order by volatility desc;

select * from volatility_view;


--trend: evolucao ao longo do tempo, sem agregacao (para grafico de linha)
--added 10/09/2026
CREATE OR REPLACE VIEW trend_view AS
select date, base, quote, rate
from xchange_rates
order by date;

select * from trend_view limit 5;


--correlation: generalizada para todos os pares possiveis (nao so um par fixo)
--a.quote < b.quote evita duplicados (CNY/USD e USD/CNY) e moeda consigo mesma
--added 10/09/2026
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
	
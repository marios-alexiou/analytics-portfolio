---
title: SaaS overview
fullWidth: true
---

<ReportHeader title="SaaS overview" />

```sql regions
select '%' as region, 'All regions' as label
union all select distinct region, replace(region, '_', ' ') as label from fieldcraft.mrr
order by 1
```

```sql months
select distinct strftime(month_start, '%Y-%m-%d') as month from fieldcraft.mrr order by 1 desc
```

<div class="report-filters">
	<Dropdown name=region data={regions} value=region label=label title="Region" defaultValue="%" />
	<Dropdown name=month data={months} value=month title="Reporting month" defaultValue="2026-09-01" />
</div>

```sql trend
select month_start, sum(ending_mrr_usd) as mrr_usd,
	   sum(ending_customers) as customers,
	   sum(starting_mrr_usd) as opening_mrr_usd,
	   sum(new_mrr_usd) as new_mrr_usd,
	   sum(expansion_mrr_usd) as expansion_mrr_usd,
	   sum(contraction_mrr_usd) as contraction_mrr_usd,
	   sum(churned_mrr_usd) as churned_mrr_usd,
	   sum(reactivation_mrr_usd) as reactivation_mrr_usd,
	   sum(fx_effect_usd) as fx_effect_usd
from fieldcraft.mrr
where region like '${inputs.region.value}'
group by 1
order by 1
```

```sql selected
select *, mrr_usd - opening_mrr_usd as net_change_usd,
	   (mrr_usd - opening_mrr_usd) / nullif(opening_mrr_usd, 0) as growth
from ${trend}
where month_start = cast('${inputs.month.value}' as date)
```

<div class="report-kpis">
	<div><BigValue data={selected} value=mrr_usd title="Closing MRR" fmt=usd0 /></div>
	<div><BigValue data={selected} value=customers title="Paying workspaces" fmt=num0 /></div>
	<div><BigValue data={selected} value=net_change_usd title="Net MRR change" fmt=usd0 /></div>
	<div><BigValue data={selected} value=growth title="Month-on-month growth" fmt=pct1 /></div>
</div>

<Grid cols=2>
	<LineChart data={trend} x=month_start y=mrr_usd yFmt=usd0 title="Monthly recurring revenue" />
	<LineChart data={trend} x=month_start y=customers title="Paying workspaces" />
</Grid>

```sql movements
select 'New' as movement, new_mrr_usd as mrr_usd, 1 as sequence from ${selected}
union all select 'Expansion', expansion_mrr_usd, 2 from ${selected}
union all select 'Contraction', contraction_mrr_usd, 3 from ${selected}
union all select 'Churn', churned_mrr_usd, 4 from ${selected}
union all select 'Reactivation', reactivation_mrr_usd, 5 from ${selected}
union all select 'FX effect', fx_effect_usd, 6 from ${selected}
order by sequence
```

## MRR movements

<BarChart data={movements} x=movement y=mrr_usd yFmt=usd0 swapXY=true title="Customer movements and exchange-rate effect" />

<p class="report-note">USD at daily exchange rates. Closing MRR is a month-end balance, not revenue billed during the month. FX movement is reported separately from customer activity.</p>

## Monthly reconciliation

<DataTable data={trend} rows=12 sort="month_start desc">
	<Column id=month_start title="Month" fmt=mmmYYYY />
	<Column id=opening_mrr_usd title="Opening" fmt=usd0 />
	<Column id=new_mrr_usd title="New" fmt=usd0 />
	<Column id=expansion_mrr_usd title="Expansion" fmt=usd0 />
	<Column id=contraction_mrr_usd title="Contraction" fmt=usd0 />
	<Column id=churned_mrr_usd title="Churn" fmt=usd0 />
	<Column id=reactivation_mrr_usd title="Reactivation" fmt=usd0 />
	<Column id=fx_effect_usd title="FX" fmt=usd0 />
	<Column id=mrr_usd title="Closing" fmt=usd0 contentType=bar />
</DataTable>
---
title: Acquisition
fullWidth: true
---

<ReportHeader title="Acquisition economics" />

```sql years
select distinct cast(year(month_start) as varchar) as year from fieldcraft.acquisition order by 1 desc
```

<Dropdown name=year data={years} value=year title="Calendar year" defaultValue="2026" />

```sql filtered
select * from fieldcraft.acquisition
where cast(year(month_start) as varchar) = '${inputs.year.value}' and is_paid
```

```sql totals
select sum(acquisition_cost_usd) as spend_usd,
       sum(new_customers) as customers,
       sum(acquisition_cost_usd) / nullif(sum(new_customers), 0) as cac_usd,
       sum(acquisition_cost_usd) / nullif(sum(new_mrr_usd), 0) as revenue_payback_months
from ${filtered}
```

<div class="report-kpis">
    <div><BigValue data={totals} value=spend_usd title="Paid acquisition cost" fmt=usd0 /></div>
    <div><BigValue data={totals} value=customers title="New paid-channel customers" fmt=num0 /></div>
    <div><BigValue data={totals} value=cac_usd title="Blended paid CAC" fmt=usd0 /></div>
    <div><BigValue data={totals} value=revenue_payback_months title="Revenue payback / months" fmt=num1 /></div>
</div>

```sql by_channel
select acquisition_channel, sum(signups) as signups,
       sum(new_customers) as customers, sum(acquisition_cost_usd) as spend_usd,
       sum(new_mrr_usd) as new_mrr_usd,
       sum(acquisition_cost_usd) / nullif(sum(new_customers), 0) as cac_usd,
       sum(acquisition_cost_usd) / nullif(sum(new_mrr_usd), 0) as revenue_payback_months
from ${filtered} group by 1 order by cac_usd desc
```

<Grid cols=2>
    <BarChart data={by_channel} x=acquisition_channel y=cac_usd yFmt=usd0 swapXY=true title="Acquisition cost per new customer" />
    <BarChart data={by_channel} x=acquisition_channel y=revenue_payback_months swapXY=true title="Revenue payback / months" />
</Grid>

<p class="report-note">Paid channels only. Costs include ads and non-reversed affiliate commissions, not salaries or overhead. Payback uses new MRR without a gross-margin adjustment; it is not gross-margin CAC payback. Spend and conversions are calendar-period totals, not matched cohorts.</p>

## Channel economics

<DataTable data={by_channel} rows=10>
    <Column id=acquisition_channel title="Channel" />
    <Column id=signups title="Trials" fmt=num0 />
    <Column id=customers title="New customers" fmt=num0 />
    <Column id=spend_usd title="Acquisition cost" fmt=usd0 />
    <Column id=new_mrr_usd title="New MRR" fmt=usd0 />
    <Column id=cac_usd title="CAC" fmt=usd0 contentType=bar />
    <Column id=revenue_payback_months title="Revenue payback / months" fmt=num1 />
</DataTable>

```sql monthly
select month_start, acquisition_channel, sum(acquisition_cost_usd) as spend_usd
from ${filtered} group by 1, 2 order by 1
```

## Spend allocation

<BarChart data={monthly} x=month_start y=spend_usd series=acquisition_channel yFmt=usd0 title="Monthly spend by paid channel" />
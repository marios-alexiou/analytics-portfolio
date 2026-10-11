---
title: Trial conversion
fullWidth: true
---

<ReportHeader title="Trial conversion" />

```sql channels
select '%' as acquisition_channel, 'All channels' as label
union all select distinct acquisition_channel, replace(acquisition_channel, '_', ' ') as label from fieldcraft.trials
order by 1
```

```sql regions
select '%' as region, 'All regions' as label
union all select distinct region, replace(region, '_', ' ') as label from fieldcraft.trials
order by 1
```

<div class="report-filters">
    <Dropdown name=channel data={channels} value=acquisition_channel label=label title="Channel" defaultValue="%" />
    <Dropdown name=region data={regions} value=region label=label title="Region" defaultValue="%" />
</div>

```sql filtered
select * from fieldcraft.trials
where acquisition_channel like '${inputs.channel.value}'
  and region like '${inputs.region.value}'
```

```sql totals
select sum(signups) as signups,
       sum(converted_to_date) as converted,
       sum(converted_within_30_days) / nullif(sum(signups_with_30_days), 0) as conversion_30d,
       sum(total_days_to_convert) / nullif(sum(converted_to_date), 0) as days_to_convert
from ${filtered}
```

<div class="report-kpis">
    <div><BigValue data={totals} value=signups title="Trials started" fmt=num0 /></div>
    <div><BigValue data={totals} value=converted title="Converted to date" fmt=num0 /></div>
    <div><BigValue data={totals} value=conversion_30d title="30-day conversion" fmt=pct1 /></div>
    <div><BigValue data={totals} value=days_to_convert title="Days to first payment" fmt=num1 /></div>
</div>

```sql cohorts
select signup_month, sum(signups) as signups,
       sum(signups_with_30_days) as eligible_signups,
       sum(converted_within_30_days) as converted_30d,
       sum(converted_within_30_days) / nullif(sum(signups_with_30_days), 0) as conversion_30d
from ${filtered} group by 1 order by 1
```

```sql channel_conversion
select acquisition_channel,
       sum(converted_within_30_days) / nullif(sum(signups_with_30_days), 0) as conversion_30d
from ${filtered} group by 1 order by 2 desc
```

<Grid cols=2>
    <LineChart data={cohorts} x=signup_month y=conversion_30d yFmt=pct1 title="30-day conversion by signup cohort" />
    <BarChart data={channel_conversion} x=acquisition_channel y=conversion_30d yFmt=pct1 swapXY=true title="Conversion by acquisition channel" />
</Grid>

<p class="report-note">30-day conversion includes only signups with a full 30-day observation window. Recent cohorts may have no eligible signups. Internal QA workspaces are excluded.</p>

## Cohort detail

<DataTable data={cohorts} rows=12 sort="signup_month desc">
    <Column id=signup_month title="Signup month" fmt=mmmYYYY />
    <Column id=signups title="Trials" fmt=num0 />
    <Column id=eligible_signups title="30-day eligible" fmt=num0 />
    <Column id=converted_30d title="Converted in 30 days" fmt=num0 />
    <Column id=conversion_30d title="Conversion" fmt=pct1 contentType=bar />
</DataTable>
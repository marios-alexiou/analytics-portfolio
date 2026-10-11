-- Starting MRR plus every movement must equal ending MRR, for every month and segment.
select
    month_start,
    region,
    acquisition_channel,
    starting_mrr_usd
    + new_mrr_usd
    + expansion_mrr_usd
    + contraction_mrr_usd
    + churned_mrr_usd
    + reactivation_mrr_usd
    + fx_effect_usd
    - ending_mrr_usd as unexplained_usd
from {{ ref('mart_mrr_monthly') }}
where abs(
    starting_mrr_usd
    + new_mrr_usd
    + expansion_mrr_usd
    + contraction_mrr_usd
    + churned_mrr_usd
    + reactivation_mrr_usd
    + fx_effect_usd
    - ending_mrr_usd
) > 0.01

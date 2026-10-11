<script>
    export let title;
</script>

<div class="report-header">
    <div class="identity">FIELDCRAFT <span>Analytics / Synthetic data</span></div>
    <h1>{title}</h1>
    <nav aria-label="Dashboards">
        <a href="/">SaaS overview</a>
        <a href="/trials/">Trial conversion</a>
        <a href="/acquisition/">Acquisition</a>
    </nav>
</div>

<style>
    .report-header { border-bottom: 1px solid #dfe4ea; padding: 0 0 20px; margin-bottom: 22px; }
    .identity { color: #2864d7; font-weight: 700; font-size: 13px; }
    .identity span { color: #687581; font-weight: 400; margin-left: 16px; }
    h1 { font-size: 27px; line-height: 1.3; margin: 10px 0 18px; letter-spacing: 0; }
    nav { display: flex; flex-wrap: wrap; gap: 24px; }
    nav a { color: #344550; font-size: 14px; text-decoration: none; border-bottom: 2px solid transparent; }
    nav a:hover { color: #2864d7; border-color: #2864d7; }
    :global(body) { background: #fbfcfd; letter-spacing: 0; }
    :global(article > h1) { display: none; }
    :global(.over-container:not(:has(.status-bar.error))) { display: none; }
    :global(h2) { font-size: 19px; margin-top: 30px; border-bottom: 1px solid #e5e9ee; padding-bottom: 10px; }
    :global(.report-kpis) { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 20px; padding: 20px 0; border-block: 1px solid #e5e9ee; margin: 20px 0; }
    :global(.report-kpis > div) { min-width: 0; }
    :global(.report-filters) { display: flex; flex-wrap: wrap; gap: 16px; }
    :global(.report-note) { color: #66737e; font-size: 13px; margin: 12px 0; }
    @media (max-width: 700px) {
        :global(.report-kpis) { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
        h1 { font-size: 23px; }
        .identity span { display: block; margin-left: 0; margin-top: 4px; }
    }
    @media print {
        nav, :global(.report-filters) { display: none; }
        :global(body) { background: white; }
    }
</style>
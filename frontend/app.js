const $ = (s) => document.querySelector(s);
const fmt = (v, n = 0) => v == null ? 'N/A' : Number(v).toLocaleString('en-GB', { minimumFractionDigits: n, maximumFractionDigits: n });
const gbp = v => v == null ? 'N/A' : '£' + fmt(v);
const safe = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const pretty = s => String(s).replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
let currentId = 'manchester', property = null, sessionId = null, busy = false, currentView = 'dashboard';
let customProperty = null; // last manually entered home, stored only in this browser tab until chat starts
async function api(path, data = null, method = 'POST') {
    const opts = { method: data === null ? 'GET' : method, headers: { 'Content-Type': 'application/json' } };
    if (data !== null)
        opts.body = JSON.stringify(data);
    const r = await fetch('/api/' + path, opts);
    let json;
    try {
        json = await r.json();
    }
    catch {
        throw new Error('Could not read response from backend.');
    }
    if (!r.ok)
        throw new Error(json.detail || r.statusText || 'Request failed');
    return json;
}
function showError(text, target) { target.innerHTML = `<div class="error">${safe(text)}</div>`; }
async function init() {
    try {
        const homes = await api('properties/demo');
        $('#propertySelect').innerHTML = homes.map(p => `<option value="${safe(p.property_id)}">${safe(p.name)}</option>`).join('');
        $('#propertySelect').value = currentId;
        await loadProperty(currentId);
    }
    catch (e) {
        showError(e.message, $('#scoreCard'));
    }
}
async function loadProperty(id) {
    currentId = id;
    sessionId = null;
    property = id === 'custom'
        ? { ...customProperty }
        : await api('properties/' + id);
    $('#budgetRange').value = property.budget_gbp;
    $('#budgetValue').textContent = gbp(property.budget_gbp);
    $('#chatMessages').innerHTML = `<div class="message-row assistant"><div class="avatar">✳</div><div class="bubble"><div class="speaker">TREE</div><p>We're looking at <b>${safe(property.name)}</b>. What would you like to improve? I can calculate your score, compare retrofits, or work with a budget.</p><p class="subdued">I only use synthetic demo property evidence unless you provide verified values.</p></div></div>`;
    $('#chatInsights').innerHTML = '';
    await renderSnapshot();
    await renderDashboard();
    if (currentView === 'scenarios')
        await renderScenarios();
    if (currentView === 'ranking')
        await renderRanking();
    if (currentView === 'evaluation')
        await renderEvaluation();
}
async function renderSnapshot() {
    const s = await api('score', property);
    const color = s.score >= 65 ? '#64a578' : s.score >= 50 ? '#b0ba66' : '#c88f56';
    $('#scoreCard').classList.remove('loading');
    $('#scoreCard').innerHTML = `<div class="score-circle" style="--score:${s.score};background:conic-gradient(${color} ${s.score}%,#e8efe6 0)"><div class="score-circle-inner"><div class="score-number">${s.score}<small>/100</small></div></div></div><div class="score-name">${safe(s.classification)}</div><p class="score-caption">Modelled score · not a new EPC certificate</p><button class="soft-button" id="breakdownBtn">View score anatomy ↗</button>`;
    $('#breakdownBtn').onclick = () => { openView('chat'); $('#chatInsights').innerHTML = scoreBreak(s); $('#chatInsights').scrollIntoView({ behavior: 'smooth', block: 'center' }); };
    $('#snapshot').innerHTML = [['Type', pretty(property.property_type)], ['Region', property.region], ['Floor area', `${fmt(property.floor_area_m2)} m²`], ['Heating', pretty(property.heating_type || 'Unknown')], ['EPC record', property.epc_rating || 'Unknown'], ['Energy data', pretty(property.baseline_source)]].map(([a, b]) => `<div class="snapshot-row"><span>${safe(a)}</span><b>${safe(b)}</b></div>`).join('');
}
function scoreBreak(s) {
    const labels = { energy_efficiency: 'Energy efficiency', consumption_intensity: 'Energy intensity', insulation: 'Insulation', heating: 'Heating', glazing: 'Glazing', renewables: 'Renewables', smart_management: 'Smart controls' };
    return `<div class="insight"><div class="insight-title">◎ Seven-component score · ${s.score}/100</div><div class="score-break">${Object.entries(s.subscores).map(([k, v]) => `<div class="break-row"><span>${labels[k]}</span><div class="bar-track"><div class="bar-fill" style="width:${v}%"></div></div><b>${fmt(v, 0)}</b></div>`).join('')}</div><p>Exact Lloyds weights used: 25%, 20%, 15%, 15%, 10%, 10%, 5%. Component-to-score mappings are our demonstrator assumptions, not official EPC mappings.</p>${s.warnings.length ? `<p class="smallprint">${safe(s.warnings.join(' · '))}</p>` : ''}</div>`;
}
function scenarioCard(x) {
    const v = x.valuation, range = v?.after_range_gbp;
    return `<div class="scenario-card"><div class="eyebrow">${safe(x.name.toUpperCase())}</div><h3>${x.measures.length ? x.labels.map(safe).join(', ') : 'No new upgrades'}</h3><div class="number">${x.score_after.score}<span class="unit"> /100 green score</span></div><div class="metric-line"><span>Installation</span><b>${gbp(x.cost_gbp)}</b></div><div class="metric-line"><span>Bill saving / year</span><b>${gbp(x.annual_bill_savings_gbp)}</b></div><div class="metric-line"><span>Electricity import</span><b>${fmt(x.after.grid_electricity_kwh)} kWh</b></div><div class="metric-line"><span>Gas</span><b>${fmt(x.after.gas_kwh)} kWh</b></div><div class="metric-line"><span>CO₂e saved / yr</span><b>${fmt(x.carbon.reduction_kg_co2e)} kg*</b></div><div class="metric-line"><span>Indicative value*</span><b>${range ? gbp(range[0]) + '–' + gbp(range[1]) : 'Unavailable'}</b></div></div>`;
}
function scenarioLayout(data) {
    const scenarios = data.scenarios;
    let max = Math.max(...scenarios.map(x => x.baseline_annual_bill_gbp), 1);
    return `<div class="cards">${scenarios.map(scenarioCard).join('')}</div><div class="insight"><div class="insight-title">Annual energy bill comparison</div><div class="comparison-bars">${scenarios.map(x => `<div><div class="bar-label"><span>${safe(x.name)}</span><b>${gbp(x.after_annual_bill_gbp)}</b></div><div class="bar-track"><div class="bar-fill" style="width:${Math.max(1, 100 * x.after_annual_bill_gbp / max)}%"></div></div></div>`).join('')}</div></div><p class="smallprint">* Carbon factors are illustrative placeholders, and the property-value range is a synthetic sensitivity illustration, NOT market-validated evidence. Installation costs and energy effects are assumptions. No prices are guaranteed.</p>`;
}
async function renderScenarios() { let el = $('#scenarioResults'); el.textContent = 'Calculating all three futures…'; try {
    el.innerHTML = scenarioLayout(await api('scenarios/compare', { property, budget_gbp: property.budget_gbp, objective: 'money' }));
}
catch (e) {
    showError(e.message, el);
} }
async function renderRanking() {
    let el = $('#rankingResults');
    el.textContent = 'Ranking properties by feasible annual purchased-energy reduction…';
    try {
        const data = await api('properties/ranking/demo');
        el.innerHTML = `<div style="overflow-x:auto"><table class="ranking-table"><thead><tr><th>Rank</th><th>Home</th><th>Current class</th><th>Potential reduction</th><th>Proposed package</th></tr></thead><tbody>${data.properties.map((x, i) => `<tr><td><span class="rank-index">${i + 1}</span></td><td><b>${safe(x.name)}</b></td><td>${safe(x.classification || 'N/A')}</td><td><span class="pill">${x.improvement_potential_pct == null ? 'Unavailable' : fmt(x.improvement_potential_pct, 1) + '%'}</span></td><td>${safe(x.measures?.map(pretty).join(', ') || 'None')}</td></tr>`).join('')}</tbody></table></div><p class="smallprint">All homes are synthetic fixtures. Reduction = (baseline purchased kWh − post-upgrade purchased kWh) / baseline purchased kWh. Packages use a documented £30,000 demonstration feasibility budget.</p>`;
    }
    catch (e) {
        showError(e.message, el);
    }
}
async function renderEvaluation() {
    let el = $('#evaluationResults');
    try {
        const e = await api('evaluation/summary');
        el.innerHTML = `<div class="eval-panel"><h3>✳ Honest model status</h3><p><b>${safe(e.status)}</b>. Our scoring uses exact Lloyds weights but original illustrative subscore mappings. Retrofit calculations are synthetic engineering approximations, not professional building simulations.</p><p><b>Valuation:</b> ${safe(e.valuation)}.</p><p><b>Carbon:</b> ${safe(e.carbon)}.</p></div><div class="eval-panel"><h3>◈ Trained ML evaluation (synthetic-only)</h3><div id="mlMetrics">Loading actual saved metrics…</div></div><div class="eval-panel"><h3>◉ Observed UK household benchmark</h3><div id="realWorldMetrics">Checking for NEED evaluation…</div></div><div class="eval-panel"><h3>◈ Improved NEED 2026 challenger</h3><div id="challengerMetrics">Loading held-out experiments…</div></div><div class="eval-panel"><h3>♧ Validation and reproducibility</h3><p>Run <code>python -m pytest -q</code> to verify scoring, per-fuel signs, retrofit interactions, ranking, TreeAsk, optimization, and API routes. Run <code>python -m ml.train</code> to regenerate the synthetic models, held-out predictions and evaluation report.</p><p>These checks do not establish real-world accuracy. Government source factors, housing valuation evidence, direct consumer-model validation, and independent provider-LLM testing are still needed before real customer deployment.</p></div><div class="warning">Transparency: all sample properties are invented. The valuation formula and emission-factor defaults are demonstrations, not verified historical market relationships or official 2026 factors.</div>`;
        try {
            const metrics = await api('evaluation/synthetic-ml');
            let content = Object.entries(metrics.targets || {}).map(([name, v]) => `<div class="metric-line"><span>${safe(name.replace('annual_', '').replace('_kwh', ''))} MAE / naive baseline</span><b>${fmt(v.mae)} / ${fmt(v.median_baseline_mae)} kWh</b></div>`).join('');
            $('#mlMetrics').innerHTML = `<p><b>${metrics.held_out_rows} synthetic held-out rows</b> (seed ${metrics.split_seed}). Metrics measure how well the model recovers generated labels, NOT UK household accuracy.</p>${content}`;
        }
        catch {
            $('#mlMetrics').textContent = 'Synthetic model benchmark not available; run python -m ml.train.';
        }
        try {
            const challenger = await api('evaluation/need-challenger');
            const names = {electricity_property_only:'Electricity · property details',gas_property_only:'Gas · property details',
              electricity_with_prior_year_bill:'Electricity · with previous bill',gas_with_prior_year_bill:'Gas · with previous bill'};
            const blocks = Object.entries(challenger.experiments).map(([name, x]) => `<div class="metric-line"><span>${safe(names[name] || name)} (${fmt(x.test_rows)} test homes)</span><b>MAE ${fmt(x.test.mae_kwh)} kWh · R² ${fmt(x.test.r2,3)}</b></div>`).join('');
            const elec = challenger.experiments.electricity_with_prior_year_bill;
            $('#challengerMetrics').innerHTML = `<p>Trained on genuine NEED rows, with a validation-chosen model and untouched test partition. These research models remain separate from the homeowner form.</p>${blocks}<p class="smallprint">Important: the previous-year copy baseline for electricity (${fmt(elec.test_prior_year_copy_baseline.mae_kwh)} kWh MAE) outperforms our prior-bill ML on MAE (${fmt(elec.test.mae_kwh)} kWh). We report both. Retrofits are not externally validated.</p>`;
        } catch (_) {
            $('#challengerMetrics').textContent = 'Run the UK challenger benchmark to view independently held-out results.';
        }
        try {
            const contract = await api('evaluation/dialogue-contract');
            const panel = document.createElement('div');
            panel.className = 'eval-panel';
            panel.innerHTML = `<h3>◎ Reproducible explanation-contract checks</h3>
              <div class="metric-line"><span>Checks passing</span><b>${fmt(contract.contract_passed)} / ${fmt(contract.cases)}</b></div>
              <p class="smallprint">Deterministic intent routing and numeric evidence matching only. No external LLM factual accuracy or provider groundedness score was measured. Organiser LLM targets remain unverified.</p>`;
            el.appendChild(panel);
        } catch (_) { /* Optional local test suite. */ }
        try {
            const t = await api('evaluation/treeask-benchmark');
            const panel = document.createElement('div');
            panel.className = 'eval-panel';
            panel.innerHTML = `<h3>✳ TreeAsk question experiment</h3>
              <p>We hid one known yes/no detail at a time in ${fmt(t.cases)} synthetic test cases.</p>
              <div class="metric-line"><span>First question recovered the hidden detail</span><b>${fmt(t.treeask_asks_hidden_field_first)} / ${fmt(t.cases)}</b></div>
              <div class="metric-line"><span>Plan matched full-record plan after one answer</span><b>${fmt(t.treeask_one_question_matches_complete_plan)} / ${fmt(t.cases)}</b></div>
              <p class="smallprint">Synthetic simulation only. A fixed checklist uses ${fmt(t.fixed_form_questions)} questions; this is NOT a fair measured homeowner comparison or real-world validation.</p>`;
            el.appendChild(panel);
        } catch (_) { /* Benchmark is optional; no fabricated results. */ }
        try {
            const real = await api('evaluation/real-world');
            let rows = Object.entries(real.fuels || {}).map(([fuel, result]) => {
                const m = result.random_forest;
                return `<div class="metric-line"><span>${safe(fuel)} (${result.held_out_test_records} held-out homes)</span><b>MAE ${fmt(m.mae_kwh_per_year)} kWh · R² ${fmt(m.r2, 3)}</b></div>`;
            }).join('');
            $('#realWorldMetrics').innerHTML = `<p><b>Independent NEED 2026 benchmark</b> · ${real.raw_rows} source records. A separate model trained and tested using valid observed readings—not an accuracy test of the synthetic model.</p>${rows}<p class="smallprint">${safe(real.limitations)}</p>`;
        } catch {
            $('#realWorldMetrics').textContent = 'Not evaluated yet. Download the official NEED 2026 CSV and run bash validate_real_mac.sh with its path. No real-world accuracy is claimed.';
        }
    }
    catch (e) {
        showError(e.message, el);
    }
}
function appendMessage(text, role) { const d = document.createElement('div'); d.className = 'message-row ' + role; d.innerHTML = `${role === 'assistant' ? '<div class="avatar">✳</div>' : ''}<div class="bubble">${role === 'assistant' ? '<div class="speaker">TREE</div>' : ''}<p>${safe(text)}</p></div>`; $('#chatMessages').appendChild(d); $('#chatMessages').scrollTop = $('#chatMessages').scrollHeight; }
function insightFor(r) {
    const d = r.data || {};
    if (d.treeask)
        return `<div class="insight"><div class="insight-title">✳ TreeAsk · Decision-aware question</div><p>Question chosen by testing how potential answers change the best affordable retrofit package.</p><div class="detail-list"><span>If yes: ${safe(d.treeask.ranking?.[0]?.best_if_yes?.map(pretty).join(' + ') || 'No upgrades')}</span><span>If no: ${safe(d.treeask.ranking?.[0]?.best_if_no?.map(pretty).join(' + ') || 'No upgrades')}</span></div></div>`;
    if (d.scenarios)
        return scenarioLayout(d.scenarios);
    if (d.scenario) {
        const r = d.scenario;
        return `<div class="insight"><div class="insight-title">◈ What-if · Recalculated scenario</div>
          <div class="metric-grid"><div class="metric"><strong>${gbp(r.cost_gbp)}</strong><span>Upfront cost</span></div>
          <div class="metric"><strong>${gbp(r.annual_bill_savings_gbp)}</strong><span>Annual bill saving (negative = increase)</span></div>
          <div class="metric"><strong>${r.score_after.score}/100</strong><span>Modelled green score</span></div></div>
          <div class="metric-line"><span>Electricity change</span><b>${fmt(r.savings.electricity_kwh)} kWh/yr</b></div>
          <div class="metric-line"><span>Gas change</span><b>${fmt(r.savings.gas_kwh)} kWh/yr</b></div>
          <div class="metric-line"><span>Carbon change</span><b>${fmt(r.carbon.reduction_kg_co2e)} kg CO₂e/yr*</b></div>
          <p class="smallprint">${safe(r.warnings.join(' · '))}</p></div>`;
    }
    if (d.score && !d.optimization)
        return scoreBreak(d.score);
    if (d.chess) {
        const stages = d.chess.first_order;
        return `<div class="insight"><div class="insight-title">♟ Retrofit Chess</div><p>Stage-by-stage annual energy effects; reverse-order path is also calculated.</p>${stages.map(s => `<div class="metric-line"><span>Stage ${s.stage}: ${safe(pretty(s.measure_added))}</span><b>${gbp(s.result.annual_bill_savings_gbp)} / year</b></div>`).join('')}<p class="smallprint">${safe(d.chess.note)}</p></div>`;
    }
    if (d.optimization) {
        const b = d.optimization.best;
        return `<div class="insight"><div class="insight-title">◉ Budget Tetris · Model recommendation</div><div class="metric-grid"><div class="metric"><strong>${gbp(b.cost_gbp)}</strong><span>Upfront cost</span></div><div class="metric"><strong>${gbp(b.annual_bill_savings_gbp)}</strong><span>Annual bill saving</span></div><div class="metric"><strong>${b.score_after.score}/100</strong><span>Modelled green score</span></div></div><div class="detail-list">${b.labels.length ? b.labels.map(x => `<span>${safe(x)}</span>`).join('') : '<span>No affordable measures</span>'}</div><p class="smallprint">Fuel changes: electricity ${fmt(b.savings.electricity_kwh)} kWh/yr; gas ${fmt(b.savings.gas_kwh)} kWh/yr. Negative means greater consumption. Illustrative demo estimates only.</p></div>`;
    }
    return '';
}
async function submit(text) {
    if (busy || !text.trim())
        return;
    busy = true;
    $('#sendButton').disabled = true;
    appendMessage(text, 'user');
    $('#promptInput').value = '';
    try {
        const r = await api('chat', { session_id: sessionId, property_id: currentId,
            property: currentId === 'custom' && !sessionId ? property : null,
            message: text, use_gemini: false });
        sessionId = r.session_id;
        property = r.property;
        if (currentId === 'custom') customProperty = { ...property };
        appendMessage(r.message, 'assistant');
        $('#budgetRange').value = property.budget_gbp;
        $('#budgetValue').textContent = gbp(property.budget_gbp);
        $('#chatInsights').innerHTML = insightFor(r);
        if (r.mode === 'question') {
            $('#chatInsights').insertAdjacentHTML('beforeend', '<div class="quickanswers"><button data-answer="Yes">Yes</button><button data-answer="No">No</button><button data-answer="Not sure">Not sure</button></div>');
            $('#chatInsights').querySelectorAll('[data-answer]').forEach(b => b.onclick = () => submit(b.dataset.answer));
        }
        await renderSnapshot();
    }
    catch (e) {
        appendMessage('I could not complete that calculation: ' + e.message, 'assistant');
    }
    finally {
        busy = false;
        $('#sendButton').disabled = false;
        $('#promptInput').focus();
    }
}
// Navigation: change the active tool, and scroll directly to it.
function openView(view, scroll = true) {
    currentView = view;
    document.querySelectorAll('.nav').forEach(button => {
        button.classList.toggle('active', button.dataset.view === view);
    });
    document.querySelectorAll('.view').forEach(section => {
        section.classList.toggle('active', section.id === 'view-' + view);
    });
    // Keep the big illustrated story for the homepage only.
    const isHome = view === 'dashboard';
    ['#welcome', '#about', '.numbers-strip', '#adventures'].forEach(selector => {
        $(selector).classList.toggle('hidden', !isHome);
    });
    $('#crumb').textContent = view.toUpperCase();
    $('.sidebar').classList.remove('open');
    $('#mobileMenu').setAttribute('aria-expanded', 'false');
    if (view === 'dashboard')
        renderDashboard();
    if (view === 'scenarios')
        renderScenarios();
    if (view === 'ranking')
        renderRanking();
    if (view === 'evaluation')
        renderEvaluation();
    if (scroll) {
        // On Home, show the sign; for tools, go straight to the lab.
        (isHome ? $('#welcome') : $('#lab')).scrollIntoView({ behavior: 'smooth' });
    }
}
// Everyone navigates through the same simple openView() function.
document.querySelectorAll('.nav').forEach(button => {
    button.addEventListener('click', () => openView(button.dataset.view));
});
document.querySelectorAll('[data-go]').forEach(button => {
    button.addEventListener('click', () => openView(button.dataset.go));
});
$('#brandHome').onclick = () => openView('dashboard');
$('#aboutExplore').onclick = () => {
    openView('dashboard', false);
    $('#lab').scrollIntoView({ behavior: 'smooth' });
};
$('#composer').addEventListener('submit', e => { e.preventDefault(); submit($('#promptInput').value); });
$('#propertySelect').onchange = e => loadProperty(e.target.value).catch(err => showError(err.message, $('#scoreCard')));
$('#refreshScenarios').onclick = renderScenarios;
$('#budgetRange').oninput = e => $('#budgetValue').textContent = gbp(e.target.value);
$('#budgetRange').onchange = e => { property.budget_gbp = Number(e.target.value);
    if (currentId === 'custom') customProperty = { ...property };
    if (currentView === 'dashboard') {
    renderDashboard();
    $('#dashboardResults').innerHTML = '';
}
else {
    submit(`My budget is £${e.target.value}. Recommend the best affordable upgrade.`);
} };
$('#editBudget').onclick = () => $('#budgetRange').focus();
$('#mobileMenu').onclick = () => {
    const open = $('.sidebar').classList.toggle('open');
    $('#mobileMenu').setAttribute('aria-expanded', String(open));
};
init();
// HOME DASHBOARD: deliberately simple. One selected retrofit list, one API call per action.
let chosenRetrofits = new Set();
async function renderDashboard() {
    if (!property)
        return;
    const summary = $('#dashboardSummary');
    const choices = $('#retrofitChoices');
    try {
        const [score, suggestions] = await Promise.all([api('score', property), api('retrofits/recommend', property)]);
        summary.classList.remove('loading');
        summary.innerHTML = `<div><span class="dash-kicker">CURRENT GREEN SCORE</span><div class="dash-big">${score.score}<small>/100</small></div><b>${safe(score.classification)}</b></div><div><span class="dash-kicker">YOUR PROPERTY</span><h3>${safe(property.name)}</h3><p>${safe(property.region)} · ${fmt(property.floor_area_m2)} m²</p><span class="dash-kicker">AVAILABLE BUDGET</span><h3>${gbp(property.budget_gbp)}</h3></div>`;
        chosenRetrofits.clear();
        choices.innerHTML = suggestions.retrofits.length ? suggestions.retrofits.map(r => `<button class="retrofit-choice" data-retrofit="${safe(r.id)}" aria-pressed="false"><span class="choice-top"><b>${safe(r.label)}</b><span class="choice-tag">${safe(r.suitability)}</span></span><strong>${gbp(r.cost_gbp)}</strong><span>Estimated ${gbp(r.annual_bill_savings_gbp)}/year saving</span><small>${safe(r.reason)}</small></button>`).join('') : '<p>No upgrades are currently confirmed feasible for this property. Check missing property information.</p>';
        choices.querySelectorAll('[data-retrofit]').forEach(button => button.onclick = () => {
            const key = button.dataset.retrofit;
            if (chosenRetrofits.has(key))
                chosenRetrofits.delete(key);
            else
                chosenRetrofits.add(key);
            button.classList.toggle('selected', chosenRetrofits.has(key));
            button.setAttribute('aria-pressed', String(chosenRetrofits.has(key)));
        });
    }
    catch (error) {
        showError(error.message, summary);
    }
}
$('#calculateRetrofit').onclick = async () => {
    const target = $('#dashboardResults');
    target.textContent = 'Calculating package…';
    try {
        const r = await api('retrofits/simulate', { property, measures: [...chosenRetrofits] });
        target.innerHTML = `<div class="dash-result"><h3>Your selected future</h3><div class="dash-metrics"><div><strong>${gbp(r.cost_gbp)}</strong><span>Installation cost</span></div><div><strong>${gbp(r.annual_bill_savings_gbp)}</strong><span>Estimated yearly bill savings</span></div><div><strong>${r.score_after.score}/100</strong><span>Green score after</span></div><div><strong>${fmt(r.carbon.reduction_kg_co2e)} kg</strong><span>Annual CO₂e reduction</span></div></div><p class="smallprint">Modelled annual estimates. Gas and electricity are recalculated together to account for interactions.</p></div>`;
    }
    catch (error) {
        showError(error.message, target);
    }
};
$('#findBest').onclick = async () => {
    const target = $('#dashboardResults');
    target.textContent = 'Finding affordable options…';
    try {
        const r = await api('optimize', { property, budget_gbp: property.budget_gbp, objective: 'money' });
        const b = r.best;
        target.innerHTML = `<div class="dash-result"><h3>Best package within ${gbp(property.budget_gbp)}</h3><p>${b.labels.length ? b.labels.map(safe).join(' + ') : 'No confirmed affordable upgrades'}</p><div class="dash-metrics"><div><strong>${gbp(b.cost_gbp)}</strong><span>Cost</span></div><div><strong>${gbp(b.annual_bill_savings_gbp)}</strong><span>Annual bill saving</span></div><div><strong>${b.score_after.score}/100</strong><span>New green score</span></div></div></div>`;
    }
    catch (error) {
        showError(error.message, target);
    }
};
// HERO BUTTONS: connect the illustration to real app views.
// One button jumps into the retrofit dashboard, the other opens chat.
$('#heroExplore').addEventListener('click', () => { window.location.assign('/app#locate'); });
$('#heroAsk').addEventListener('click', () => { window.location.assign('/app#chat'); });
document.querySelectorAll('[data-app]').forEach(button => {
    button.addEventListener('click', () => { window.location.assign('/app#' + encodeURIComponent(button.dataset.app)); });
});


// ── Try your own home ────────────────────────────────────────────────
// This is an input experiment, NOT GPS or a government EPC lookup.
// Both real readings and synthetic-trained estimates use the same scoring engine.
function yesNoUnknown(value) {
    if (value === 'yes') return true;
    if (value === 'no') return false;
    return null;
}
function optionalReading(value) {
    return value.trim() === '' ? null : Number(value);
}
function propertyFromForm(form) {
    const values = Object.fromEntries(new FormData(form).entries());
    const electricity = optionalReading(values.annual_electricity_kwh);
    const gas = optionalReading(values.annual_gas_kwh);
    const hasBothReadings = electricity !== null && gas !== null;
    return {
        property_id: 'custom',
        name: values.name.trim(),
        region: values.region.trim(),
        property_type: values.property_type,
        floor_area_m2: Number(values.floor_area_m2),
        construction_age_band: 'unknown',
        epc_rating: values.epc_rating || null, // typed by user; never verified
        heating_type: values.heating_type,
        loft_insulated: yesNoUnknown(values.loft_insulated),
        wall_insulated: yesNoUnknown(values.wall_insulated),
        smart_controls: yesNoUnknown(values.smart_controls),
        roof_suitable: yesNoUnknown(values.roof_suitable),
        outdoor_space: yesNoUnknown(values.outdoor_space),
        glazing: values.glazing,
        solar_kwp: Number(values.solar_kwp || 0),
        annual_electricity_kwh: electricity,
        annual_gas_kwh: gas,
        baseline_source: hasBothReadings ? 'self_reported' : 'self_reported_partial',
        property_value_gbp: null,
        electricity_price_gbp_kwh: 0.28,
        gas_price_gbp_kwh: 0.07,
        budget_gbp: Number(values.budget_gbp)
    };
}
$('#customPropertyForm').addEventListener('submit', async (event) => {
    event.preventDefault();
    const target = $('#customResult');
    target.textContent = 'Checking inputs…';
    const candidate = propertyFromForm(event.currentTarget);
    try {
        // Validate against the same backend contract used by demo properties.
        await api('score', candidate);
        const baseline = await api('predict', candidate);
        customProperty = candidate;
        if (!$('#propertySelect option[value="custom"]')) {
            const option = document.createElement('option');
            option.value = 'custom';
            option.textContent = 'My test home (manual)';
            $('#propertySelect').appendChild(option);
        }
        $('#propertySelect').value = 'custom';
        await loadProperty('custom');
        const mlEstimate = baseline.status === 'synthetic_trained_ml';
        target.textContent = mlEstimate
            ? `Loaded: ${fmt(baseline.electricity_import_kwh)} electricity and ${fmt(baseline.gas_kwh)} gas kWh/year. Missing readings estimated from a model; individual-home accuracy has not been verified.`
            : `Loaded: ${fmt(baseline.electricity_import_kwh)} electricity and ${fmt(baseline.gas_kwh)} gas kWh/year. Source: ${baseline.status}.`;
        $('#dashboardSummary').scrollIntoView({ behavior: 'smooth', block: 'center' });
    } catch (error) {
        target.textContent = `Couldn't use these details: ${error.message}`;
    }
});

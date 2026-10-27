// Front end for the credit risk platform. Talks only to the Spring Boot API (/api/...).

const TEXT_FIELDS = ["applicantName", "purpose", "verification_status", "home_ownership", "addr_state"];

const EXAMPLES = {
    low: {
        applicantName: "Example low-risk borrower", loan_amnt: 8000, term_months: 36, purpose: "credit_card",
        annual_inc: 120000, emp_length: 10, verification_status: "verified", home_ownership: "MORTGAGE",
        addr_state: "CA", dti: 5, revol_util: 10, delinq_2yrs: 0, total_acc: 30, longest_credit_length: 20,
    },
    high: {
        applicantName: "Example high-risk borrower", loan_amnt: 30000, term_months: 60, purpose: "small_business",
        annual_inc: 25000, emp_length: 0, verification_status: "verified", home_ownership: "RENT",
        addr_state: "FL", dti: 30, revol_util: 95, delinq_2yrs: 3, total_acc: 5, longest_credit_length: 3,
    },
};

const DECISION_TEXT = {
    APPROVE: "Approve",
    MANUAL_REVIEW: "Manual review",
    DECLINE: "Decline",
};

const form = document.getElementById("application-form");
const usd = (x) => "$" + Math.round(x).toLocaleString();
const pct = (x) => (x * 100).toFixed(1) + "%";
const pretty = (text) => text.replaceAll("_", " ").replace(/^\w/, (c) => c.toUpperCase());

// Fill the drop-downs (purpose, state, ...) with the values the model knows.
async function loadOptions() {
    const response = await fetch("/api/options");
    if (!response.ok) return;
    const options = await response.json();
    document.querySelectorAll("[data-options]").forEach((select) => {
        select.innerHTML = options[select.dataset.options]
            .map((value) => `<option value="${value}">${pretty(value)}</option>`).join("");
    });
}

function fillExample(example) {
    for (const [key, value] of Object.entries(example)) {
        form.elements[key].value = value;
    }
}

// Turn the form into {applicantName, features: {loan_amnt: 8000, purpose: "car", ...}}
function readForm() {
    const features = {};
    for (const element of form.elements) {
        if (!element.name || element.name === "applicantName") continue;
        features[element.name] = TEXT_FIELDS.includes(element.name) ? element.value : Number(element.value);
    }
    return { applicantName: form.elements.applicantName.value, features };
}

function showResult(p) {
    document.getElementById("result").hidden = false;
    document.getElementById("probability").textContent = pct(p.probability_of_default);
    document.getElementById("expected-loss").textContent = usd(p.expected_loss);
    document.getElementById("suggested-rate").textContent =
        p.suggested_interest_rate === null ? "n/a (declined)" : p.suggested_interest_rate.toFixed(2) + "%";
    document.getElementById("rate-note").textContent =
        `Break-even rate ${p.break_even_rate.toFixed(2)}%: below it the lender expects to lose money on this loan.`;

    const badge = document.getElementById("decision");
    badge.textContent = DECISION_TEXT[p.decision];
    badge.className = "badge " + p.decision.toLowerCase();

    const maxImpact = Math.max(...p.top_factors.map((f) => Math.abs(f.impact)));
    document.getElementById("factors").innerHTML = p.top_factors.map((f) => {
        const width = (Math.abs(f.impact) / maxImpact) * 100;
        const direction = f.impact > 0 ? "up" : "down";
        return `<div class="factor">
            <span class="factor-label">${f.label} = ${escapeHtml(pretty(f.value))}</span>
            <span class="bar-track"><span class="bar ${direction}" style="width:${width}%"></span></span>
            <span class="factor-impact">${f.impact > 0 ? "+" : ""}${f.impact.toFixed(2)}</span>
        </div>`;
    }).join("");
}

async function loadHistory() {
    const response = await fetch("/api/applications");
    const applications = await response.json();
    document.querySelector("#history tbody").innerHTML = applications.map((a) => `
        <tr>
            <td>${new Date(a.createdAt).toLocaleString()}</td>
            <td>${escapeHtml(a.applicantName)}</td>
            <td>${usd(a.loanAmount)}</td>
            <td>${pretty(a.purpose)}</td>
            <td>${pct(a.probabilityOfDefault)}</td>
            <td><span class="badge ${a.decision.toLowerCase()}">${DECISION_TEXT[a.decision]}</span></td>
            <td>${a.suggestedInterestRate === null ? "-" : a.suggestedInterestRate.toFixed(2) + "%"}</td>
        </tr>`).join("");
}

function table(headers, rows) {
    return `<table><tr>${headers.map((h) => `<th>${h}</th>`).join("")}</tr>
        ${rows.map((r) => `<tr>${r.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</table>`;
}

async function loadMetrics() {
    const box = document.getElementById("metrics");
    const response = await fetch("/api/model-metrics");
    if (!response.ok) {
        box.textContent = "Model service not reachable.";
        return;
    }
    const m = await response.json();
    const modelRow = (name, r) => [name, r.auc, r.accuracy, r.precision, r.recall, r.f1];

    box.innerHTML = `
        <p>Test set: ${m.test_rows.toLocaleString()} of ${m.dataset_rows.toLocaleString()} loans.</p>
        <h3>Prediction quality</h3>
        ${table(["Model", "AUC", "Accuracy", "Precision", "Recall", "F1"], [
            modelRow("Logistic Regression (baseline)", m.logistic_regression),
            modelRow("XGBoost, threshold 0.50", m.xgboost),
            modelRow(`XGBoost, threshold ${m.approval_threshold}`, m.xgboost_at_approval_threshold),
        ])}

        <h3>Does the model make the lender more money?</h3>
        <p class="hint">Profit on the test loans, assuming the lender loses ${pct(m.assumptions.loss_given_default)}
            of a defaulted loan.</p>
        ${table(["Strategy", "Approval rate", "Default rate of approved", "Total profit"],
            m.profit_comparison.map((r) => [r.strategy, pct(r.approval_rate), pct(r.default_rate_of_approved), usd(r.total_profit_usd)]))}

        <h3>Pricing check: is the interest rate right for the risk?</h3>
        ${table(["Lending Club rate", "Loans", "Actual default rate", "Model's average PD", "Priced below break-even"],
            m.pricing_check.map((r) => [r.interest_rate_band, r.loans.toLocaleString(), pct(r.actual_default_rate), pct(r.mean_predicted_pd), pct(r.share_underpriced)]))}

        <h3>Who gets approved? (income quartiles)</h3>
        ${table(["Income band", "Loans", "Actual default rate", "Approval rate"],
            m.group_analysis.income_band.map((r) => [r.group, r.loans.toLocaleString(), pct(r.actual_default_rate), pct(r.approval_rate)]))}`;
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const response = await fetch("/api/applications", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(readForm()),
    });
    if (!response.ok) {
        alert("Could not score the application: " + (await response.text()));
        return;
    }
    showResult(await response.json());
    loadHistory();
});

document.querySelectorAll("[data-example]").forEach((button) =>
    button.addEventListener("click", () => fillExample(EXAMPLES[button.dataset.example])));

loadOptions();
loadMetrics();
loadHistory();

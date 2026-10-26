// Front end for the credit risk platform. Talks only to the Spring Boot API (/api/...).

const MONTHS = 6;
const PAY_STATUS_FIELDS = ["PAY_0", "PAY_2", "PAY_3", "PAY_4", "PAY_5", "PAY_6"]; // dataset has no PAY_1

const EXAMPLES = {
    good: {
        applicantName: "Example reliable payer", LIMIT_BAL: 200000, AGE: 35, EDUCATION: 1, MARRIAGE: 2,
        pay: [-1, -1, -1, -1, -1, -1],
        bill: [5000, 4000, 3000, 3000, 2000, 2000],
        paid: [5000, 4000, 3000, 3000, 2000, 2000],
    },
    late: {
        applicantName: "Example late payer", LIMIT_BAL: 20000, AGE: 24, EDUCATION: 2, MARRIAGE: 2,
        pay: [3, 2, 2, 2, 2, 2],
        bill: [19000, 18500, 18000, 17000, 16500, 16000],
        paid: [0, 0, 0, 500, 500, 500],
    },
};

const DECISION_TEXT = {
    APPROVE: "Approve",
    MANUAL_REVIEW: "Manual review",
    DECLINE: "Decline",
};

const form = document.getElementById("application-form");

// Build the 6-month table: one row each for repayment status, bill amount and amount paid.
function buildMonthlyTable() {
    const table = document.getElementById("monthly-table");
    let html = "<tr><th></th>";
    for (let m = 1; m <= MONTHS; m++) html += `<th>Month ${m}</th>`;
    html += "</tr>";

    const rows = [
        ["Repayment status", (i) => PAY_STATUS_FIELDS[i], 'min="-2" max="9"'],
        ["Bill amount", (i) => `BILL_AMT${i + 1}`, ""],
        ["Amount paid", (i) => `PAY_AMT${i + 1}`, 'min="0"'],
    ];
    for (const [title, fieldName, limits] of rows) {
        html += `<tr><th>${title}</th>`;
        for (let i = 0; i < MONTHS; i++) {
            html += `<td><input name="${fieldName(i)}" type="number" ${limits} required></td>`;
        }
        html += "</tr>";
    }
    table.innerHTML = html;
}

function fillExample(example) {
    for (const key of ["applicantName", "LIMIT_BAL", "AGE", "EDUCATION", "MARRIAGE"]) {
        form.elements[key].value = example[key];
    }
    for (let i = 0; i < MONTHS; i++) {
        form.elements[PAY_STATUS_FIELDS[i]].value = example.pay[i];
        form.elements[`BILL_AMT${i + 1}`].value = example.bill[i];
        form.elements[`PAY_AMT${i + 1}`].value = example.paid[i];
    }
}

// Turn the form into {applicantName, features: {LIMIT_BAL: ..., ...}}
function readForm() {
    const features = {};
    for (const element of form.elements) {
        if (element.name && element.name !== "applicantName") {
            features[element.name] = Number(element.value);
        }
    }
    return { applicantName: form.elements.applicantName.value, features };
}

function showResult(prediction) {
    document.getElementById("result").hidden = false;
    document.getElementById("probability").textContent =
        (prediction.probability_of_default * 100).toFixed(1) + "%";

    const badge = document.getElementById("decision");
    badge.textContent = DECISION_TEXT[prediction.decision];
    badge.className = "badge " + prediction.decision.toLowerCase();

    const maxImpact = Math.max(...prediction.top_factors.map((f) => Math.abs(f.impact)));
    document.getElementById("factors").innerHTML = prediction.top_factors.map((f) => {
        const width = (Math.abs(f.impact) / maxImpact) * 100;
        const direction = f.impact > 0 ? "up" : "down";
        return `<div class="factor">
            <span class="factor-label">${f.label} = ${f.value}</span>
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
            <td>${a.creditLimit}</td>
            <td>${a.age}</td>
            <td>${(a.probabilityOfDefault * 100).toFixed(1)}%</td>
            <td><span class="badge ${a.decision.toLowerCase()}">${DECISION_TEXT[a.decision]}</span></td>
        </tr>`).join("");
}

async function loadMetrics() {
    const box = document.getElementById("metrics");
    const response = await fetch("/api/model-metrics");
    if (!response.ok) {
        box.textContent = "Model service not reachable.";
        return;
    }
    const m = await response.json();
    const row = (name, r) =>
        `<tr><td>${name}</td><td>${r.auc}</td><td>${r.accuracy}</td><td>${r.precision}</td><td>${r.recall}</td><td>${r.f1}</td></tr>`;
    const fair = m.fairness_by_sex;
    box.innerHTML = `
        <p>Test set: ${m.test_rows} of ${m.dataset_rows} customers.</p>
        <table>
            <tr><th>Model</th><th>AUC</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th></tr>
            ${row("Logistic Regression (baseline)", m.logistic_regression)}
            ${row("XGBoost", m.xgboost)}
        </table>
        <p>Fairness check (sex is not a model input): approval rate male ${(fair.male.approval_rate * 100).toFixed(1)}%,
           female ${(fair.female.approval_rate * 100).toFixed(1)}%,
           difference ${(fair.approval_rate_difference * 100).toFixed(1)} percentage points.</p>`;
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
        alert("Could not score the applicant: " + (await response.text()));
        return;
    }
    showResult(await response.json());
    loadHistory();
});

document.querySelectorAll("[data-example]").forEach((button) =>
    button.addEventListener("click", () => fillExample(EXAMPLES[button.dataset.example])));

buildMonthlyTable();
loadMetrics();
loadHistory();

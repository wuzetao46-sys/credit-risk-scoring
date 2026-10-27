# Explainable Credit Risk Scoring Platform

Final Year Project prototype (BSc Computer Science, University of Surrey).

A web application that predicts the probability that a personal loan will default, explains each
prediction with SHAP values, chooses the approval threshold that maximises the lender's profit, and
suggests a risk-based interest rate.

![Screenshot](docs/screenshot.png)

## Architecture

```
Browser (HTML/CSS/JavaScript)
        │  REST /api/...
        ▼
Java Spring Boot backend  ── JPA ──►  H2 SQL database (saved applications)
  backend/                 :8080
        │  REST /predict
        ▼
Python model service (FastAPI + XGBoost)
  ml-service/              :8000
```

- **ml-service/** (Python): downloads the data, trains the models, runs the economic analysis,
  serves predictions, explanations and prices.
- **backend/** (Java 17, Spring Boot 3): the main application. Validates input, calls the model service,
  stores every decision in the database, serves the web page.

## Dataset

Lending Club personal loans (USA), 163,987 loans with 15 columns, as cleaned and published by H2O.ai
([h2oai/app-consumer-loan](https://github.com/h2oai/app-consumer-loan)). 18.3% of loans are bad
(defaulted or charged off).

Model inputs (13): loan amount, term, purpose, annual income, years in job, income verification,
home ownership, state, debt-to-income ratio, credit card utilisation, late payments in the last
2 years, number of credit lines, length of credit history.

Lending Club's own interest rate is **not** a model input (it was set from Lending Club's risk grade,
so using it would copy their model). It is used in the economic analysis instead.

## Economics

`ml-service/economics.py` models one loan:

- borrower repays: lender earns `amount × rate × years × 0.5` (average balance of an amortising loan)
- borrower defaults: lender loses `amount × LGD` (loss given default, assumed 70%)
- break-even rate: the rate where expected profit is zero, `PD × LGD / ((1 − PD) × years × 0.5)`

The approval threshold is chosen on a validation set to maximise total profit, then evaluated on the test set.

## Current results (20% held-out test set, 32,797 loans)

| Model | AUC | Accuracy | Precision | Recall | F1 |
| --- | --- | --- | --- | --- | --- |
| Logistic Regression (baseline) | 0.675 | 0.817 | 0.486 | 0.017 | 0.034 |
| XGBoost, threshold 0.50 | 0.684 | 0.816 | 0.473 | 0.038 | 0.070 |
| XGBoost, profit-optimal threshold 0.39 | 0.684 | 0.809 | 0.433 | 0.134 | 0.204 |

| Strategy | Approval rate | Default rate of approved | Profit on test loans |
| --- | --- | --- | --- |
| Approve everyone | 100.0% | 18.3% | $27.66m |
| Model, threshold 0.50 | 98.5% | 17.9% | $28.28m |
| Model, profit-optimal threshold 0.39 | 94.3% | 16.8% | $29.34m (+6.1%) |

The page also shows a pricing check (Lending Club's rate band vs actual and predicted default) and
approval rates by income quartile. All numbers are in `ml-service/model/metrics.json`.

## How to run

中文使用与调试指南：[docs/GUIDE_zh.md](docs/GUIDE_zh.md)

You need **Python 3.10+**, **Java 17+** and **Maven** (IntelliJ IDEA includes Maven).

### 1. Model service (terminal 1)

```bash
cd ml-service
python -m venv .venv
# Windows: .venv\Scripts\activate     macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python download_data.py     # downloads the dataset into data/ (17 MB)
python train.py             # trains the models, writes model/ and prints the results
python -m pytest            # 6 tests
uvicorn app:app --port 8000
```

Open http://localhost:8000/docs to try the API directly.

### 2. Backend + web page (terminal 2)

```bash
cd backend
mvn spring-boot:run         # or run CreditRiskApplication in IntelliJ
mvn test                    # 2 tests (the model service is mocked)
```

Open http://localhost:8080, click **Low-risk borrower** or **High-risk borrower**, then **Score application**.

The database console is at http://localhost:8080/h2-console
(JDBC URL `jdbc:h2:file:./data/creditrisk`, user `sa`, empty password). Try
`SELECT applicant_name, loan_amount, probability_of_default, decision FROM loan_application;`

## API

| Method | Path | Service | Purpose |
| --- | --- | --- | --- |
| POST | `/api/applications` | backend | Score an application and save the result |
| GET | `/api/applications` | backend | All saved applications, newest first |
| GET | `/api/options` | backend | Allowed values for purpose, state, ... |
| GET | `/api/model-metrics` | backend | Evaluation, profit, pricing and group results |
| POST | `/predict` | ml-service | PD, decision, expected loss, break-even and suggested rate, top 5 SHAP factors |
| GET | `/options` | ml-service | Allowed values of the categorical inputs |
| GET | `/metrics` | ml-service | Contents of `model/metrics.json` |

## Decision rule

| Probability of default | Recommendation |
| --- | --- |
| below the profit-optimal threshold (0.39) | Approve, at the suggested rate |
| up to 10 points above it | Manual review |
| higher | Decline |

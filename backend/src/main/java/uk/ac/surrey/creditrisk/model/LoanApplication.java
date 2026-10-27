package uk.ac.surrey.creditrisk.model;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;

import java.time.LocalDateTime;

/**
 * One scored application, saved in the LOAN_APPLICATION table.
 */
@Entity
public class LoanApplication {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String applicantName;
    private Double loanAmount;
    private Double annualIncome;
    private String purpose;
    private Double probabilityOfDefault;
    private String decision;
    private Double suggestedInterestRate;
    private Double expectedLoss;
    private LocalDateTime createdAt;

    /** All model inputs as JSON, so the decision can be audited later. */
    @Column(length = 4000)
    private String featuresJson;

    /** The top factors behind the decision, as JSON. */
    @Column(length = 4000)
    private String explanationJson;

    protected LoanApplication() {
        // required by JPA
    }

    public LoanApplication(String applicantName, Double loanAmount, Double annualIncome, String purpose,
                           Prediction prediction, String featuresJson, String explanationJson) {
        this.applicantName = applicantName;
        this.loanAmount = loanAmount;
        this.annualIncome = annualIncome;
        this.purpose = purpose;
        this.probabilityOfDefault = prediction.probabilityOfDefault();
        this.decision = prediction.decision();
        this.suggestedInterestRate = prediction.suggestedInterestRate();
        this.expectedLoss = prediction.expectedLoss();
        this.featuresJson = featuresJson;
        this.explanationJson = explanationJson;
        this.createdAt = LocalDateTime.now();
    }

    public Long getId() { return id; }
    public String getApplicantName() { return applicantName; }
    public Double getLoanAmount() { return loanAmount; }
    public Double getAnnualIncome() { return annualIncome; }
    public String getPurpose() { return purpose; }
    public Double getProbabilityOfDefault() { return probabilityOfDefault; }
    public String getDecision() { return decision; }
    public Double getSuggestedInterestRate() { return suggestedInterestRate; }
    public Double getExpectedLoss() { return expectedLoss; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public String getFeaturesJson() { return featuresJson; }
    public String getExplanationJson() { return explanationJson; }
}

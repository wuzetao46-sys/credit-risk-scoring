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
    private Double creditLimit;
    private Integer age;
    private Double probabilityOfDefault;
    private String decision;
    private LocalDateTime createdAt;

    /** All 22 model inputs as JSON, so the decision can be audited later. */
    @Column(length = 4000)
    private String featuresJson;

    /** The top factors behind the decision, as JSON. */
    @Column(length = 4000)
    private String explanationJson;

    protected LoanApplication() {
        // required by JPA
    }

    public LoanApplication(String applicantName, Double creditLimit, Integer age,
                           Double probabilityOfDefault, String decision,
                           String featuresJson, String explanationJson) {
        this.applicantName = applicantName;
        this.creditLimit = creditLimit;
        this.age = age;
        this.probabilityOfDefault = probabilityOfDefault;
        this.decision = decision;
        this.featuresJson = featuresJson;
        this.explanationJson = explanationJson;
        this.createdAt = LocalDateTime.now();
    }

    public Long getId() { return id; }
    public String getApplicantName() { return applicantName; }
    public Double getCreditLimit() { return creditLimit; }
    public Integer getAge() { return age; }
    public Double getProbabilityOfDefault() { return probabilityOfDefault; }
    public String getDecision() { return decision; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public String getFeaturesJson() { return featuresJson; }
    public String getExplanationJson() { return explanationJson; }
}

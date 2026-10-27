package uk.ac.surrey.creditrisk.model;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * The answer from the Python model service (POST /predict).
 */
public record Prediction(
        @JsonProperty("probability_of_default") double probabilityOfDefault,
        String decision,
        /* Expected loss in USD: probability of default x loss given default x loan amount */
        @JsonProperty("expected_loss") double expectedLoss,
        /* Interest rate (%) at which the lender expects to make zero profit */
        @JsonProperty("break_even_rate") double breakEvenRate,
        /* Break-even rate plus a margin; null when the application is declined */
        @JsonProperty("suggested_interest_rate") Double suggestedInterestRate,
        @JsonProperty("top_factors") List<Factor> topFactors) {

    /** One reason behind the score. impact > 0 raises the risk, impact < 0 lowers it. */
    public record Factor(String feature, String label, String value, double impact) {
    }
}

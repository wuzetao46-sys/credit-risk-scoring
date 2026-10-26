package uk.ac.surrey.creditrisk.model;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.List;

/**
 * The answer from the Python model service (POST /predict).
 */
public record Prediction(
        @JsonProperty("probability_of_default") double probabilityOfDefault,
        String decision,
        @JsonProperty("top_factors") List<Factor> topFactors) {

    /** One reason behind the score. impact > 0 raises the risk, impact < 0 lowers it. */
    public record Factor(String feature, String label, double value, double impact) {
    }
}

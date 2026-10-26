package uk.ac.surrey.creditrisk.model;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;

import java.util.Map;

/**
 * What the web page sends: a name plus the 22 model inputs,
 * e.g. {"applicantName": "Alice", "features": {"LIMIT_BAL": 200000, "AGE": 35, ...}}.
 * The Python service checks that every feature is present and in range.
 */
public record ApplicationRequest(
        @NotBlank String applicantName,
        @NotEmpty Map<String, Double> features) {
}

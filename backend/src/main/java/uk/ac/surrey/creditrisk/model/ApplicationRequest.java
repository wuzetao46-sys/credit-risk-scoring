package uk.ac.surrey.creditrisk.model;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;

import java.util.Map;

/**
 * What the web page sends: a name plus the 13 model inputs,
 * e.g. {"applicantName": "Alice", "features": {"loan_amnt": 10000, "purpose": "car", ...}}.
 * Values are numbers or text (Object). The Python service checks that every
 * feature is present and in range.
 */
public record ApplicationRequest(
        @NotBlank String applicantName,
        @NotEmpty Map<String, Object> features) {
}

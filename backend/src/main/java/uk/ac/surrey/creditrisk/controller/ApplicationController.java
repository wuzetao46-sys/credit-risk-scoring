package uk.ac.surrey.creditrisk.controller;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.ResourceAccessException;
import uk.ac.surrey.creditrisk.model.ApplicationRequest;
import uk.ac.surrey.creditrisk.model.LoanApplication;
import uk.ac.surrey.creditrisk.model.Prediction;
import uk.ac.surrey.creditrisk.repository.LoanApplicationRepository;
import uk.ac.surrey.creditrisk.service.ModelClient;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
public class ApplicationController {

    private final ModelClient modelClient;
    private final LoanApplicationRepository repository;
    private final ObjectMapper objectMapper;

    public ApplicationController(ModelClient modelClient,
                                 LoanApplicationRepository repository,
                                 ObjectMapper objectMapper) {
        this.modelClient = modelClient;
        this.repository = repository;
        this.objectMapper = objectMapper;
    }

    /** Score a new applicant, save the result, and return the prediction. */
    @PostMapping("/applications")
    public Prediction score(@Valid @RequestBody ApplicationRequest request) throws JsonProcessingException {
        Prediction prediction = modelClient.predict(request.features());

        Map<String, Object> features = request.features();
        repository.save(new LoanApplication(
                request.applicantName(),
                asDouble(features.get("loan_amnt")),
                asDouble(features.get("annual_inc")),
                String.valueOf(features.get("purpose")),
                prediction,
                objectMapper.writeValueAsString(features),
                objectMapper.writeValueAsString(prediction.topFactors())));

        return prediction;
    }

    /** All past applications, newest first. */
    @GetMapping("/applications")
    public List<LoanApplication> history() {
        return repository.findAllByOrderByCreatedAtDesc();
    }

    /** Allowed values for the drop-down fields, passed through from Python. */
    @GetMapping("/options")
    public Map<?, ?> options() {
        return modelClient.options();
    }

    /** Model evaluation results (accuracy, profit, pricing), passed through from Python. */
    @GetMapping("/model-metrics")
    public Map<?, ?> metrics() {
        return modelClient.metrics();
    }

    /** JSON numbers arrive as Integer or Double; null if missing or not a number. */
    private static Double asDouble(Object value) {
        return value instanceof Number number ? number.doubleValue() : null;
    }

    /** The Python service rejected the input (e.g. a missing or out-of-range field). */
    @ExceptionHandler(HttpClientErrorException.class)
    public ResponseEntity<String> invalidInput(HttpClientErrorException error) {
        return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(error.getResponseBodyAsString());
    }

    /** The Python service is not running. */
    @ExceptionHandler(ResourceAccessException.class)
    public ResponseEntity<String> modelServiceDown() {
        return ResponseEntity.status(HttpStatus.SERVICE_UNAVAILABLE)
                .body("{\"detail\": \"Model service is not reachable. Is uvicorn running on port 8000?\"}");
    }
}

package uk.ac.surrey.creditrisk.service;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import uk.ac.surrey.creditrisk.model.Prediction;

import java.util.Map;

/**
 * Talks to the Python model service over HTTP.
 */
@Service
public class ModelClient {

    private final RestClient restClient;

    public ModelClient(@Value("${ml.service.url}") String mlServiceUrl) {
        this.restClient = RestClient.create(mlServiceUrl);
    }

    public Prediction predict(Map<String, Object> features) {
        return restClient.post()
                .uri("/predict")
                .contentType(MediaType.APPLICATION_JSON)
                .body(features)
                .retrieve()
                .body(Prediction.class);
    }

    /** Allowed values for the drop-down fields (purpose, state, ...). */
    public Map<?, ?> options() {
        return restClient.get()
                .uri("/options")
                .retrieve()
                .body(Map.class);
    }

    public Map<?, ?> metrics() {
        return restClient.get()
                .uri("/metrics")
                .retrieve()
                .body(Map.class);
    }
}

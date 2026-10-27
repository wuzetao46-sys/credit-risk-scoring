package uk.ac.surrey.creditrisk;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import uk.ac.surrey.creditrisk.model.Prediction;
import uk.ac.surrey.creditrisk.repository.LoanApplicationRepository;
import uk.ac.surrey.creditrisk.service.ModelClient;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyMap;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

/**
 * Tests the Java side on its own: the Python service is replaced by a mock.
 */
@SpringBootTest(properties = "spring.datasource.url=jdbc:h2:mem:testdb")
@AutoConfigureMockMvc
class ApplicationControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private LoanApplicationRepository repository;

    @MockBean
    private ModelClient modelClient;

    @Test
    void scoresAndSavesAnApplication() throws Exception {
        when(modelClient.predict(anyMap())).thenReturn(new Prediction(0.12, "APPROVE", 840.0, 6.5, 8.5,
                List.of(new Prediction.Factor("annual_inc", "Annual income", "90000", -0.4))));

        mockMvc.perform(post("/api/applications")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"applicantName\": \"Alice\", \"features\": {\"loan_amnt\": 10000, \"annual_inc\": 90000, \"purpose\": \"car\"}}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.decision").value("APPROVE"))
                .andExpect(jsonPath("$.probability_of_default").value(0.12))
                .andExpect(jsonPath("$.suggested_interest_rate").value(8.5));

        assertThat(repository.findAll()).hasSize(1);
        assertThat(repository.findAll().get(0).getLoanAmount()).isEqualTo(10000.0);
        assertThat(repository.findAll().get(0).getPurpose()).isEqualTo("car");

        mockMvc.perform(get("/api/applications"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$[0].applicantName").value("Alice"));
    }

    @Test
    void rejectsApplicationWithoutName() throws Exception {
        mockMvc.perform(post("/api/applications")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"applicantName\": \"\", \"features\": {\"loan_amnt\": 10000}}"))
                .andExpect(status().isBadRequest());
    }
}

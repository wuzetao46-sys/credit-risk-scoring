package uk.ac.surrey.creditrisk.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import uk.ac.surrey.creditrisk.model.LoanApplication;

import java.util.List;

/**
 * Spring Data writes the SQL for us, e.g. findAllByOrderByCreatedAtDesc() becomes
 * SELECT * FROM loan_application ORDER BY created_at DESC
 */
public interface LoanApplicationRepository extends JpaRepository<LoanApplication, Long> {

    List<LoanApplication> findAllByOrderByCreatedAtDesc();
}

package com.pcfps.job;

import jakarta.persistence.LockModeType;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Persistence for {@link FilterTask}.
 *
 * @author PCFPS
 * @date 2026-04-12
 */
public interface FilterTaskRepository extends JpaRepository<FilterTask, UUID> {

    Page<FilterTask> findByOwner_IdOrderByCreatedAtDesc(UUID ownerUserId, Pageable pageable);

    Optional<FilterTask> findByIdAndOwner_Id(UUID taskId, UUID ownerUserId);

    long countByStatus(TaskStatus status);

    List<FilterTask> findByStatus(TaskStatus status);

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("SELECT task FROM FilterTask task WHERE task.status = :status ORDER BY task.createdAt ASC")
    List<FilterTask> lockAndListByStatus(@Param("status") TaskStatus status, Pageable pageable);
}

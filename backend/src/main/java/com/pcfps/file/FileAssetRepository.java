package com.pcfps.file;

import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

/**
 * Persistence for {@link FileAsset}.
 *
 * @author PCFPS
 * @date 2026-04-12
 */
public interface FileAssetRepository extends JpaRepository<FileAsset, UUID> {

    List<FileAsset> findByTaskIdOrderByRole(UUID taskId);

    Optional<FileAsset> findByTask_IdAndRole(UUID taskId, FileAssetRole role);

    Optional<FileAsset> findByIdAndTask_Owner_Id(UUID fileId, UUID ownerUserId);
}

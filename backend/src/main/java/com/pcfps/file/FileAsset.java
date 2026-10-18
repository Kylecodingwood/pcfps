package com.pcfps.file;

import com.pcfps.job.FilterTask;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.FetchType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;

import java.time.Instant;
import java.util.UUID;

/**
 * File metadata for a task (paths are server-side only; clients use download API).
 *
 * @author PCFPS
 * @date 2026-04-12
 */
@Entity
@Table(name = "file_asset")
public class FileAsset {

    @Id
    private UUID id;

    @ManyToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "task_id", nullable = false)
    private FilterTask task;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 32)
    private FileAssetRole role;

    @Column(nullable = false, length = 512)
    private String filename;

    @Column(name = "mime_type", nullable = false, length = 128)
    private String mimeType;

    @Column(name = "stored_path", nullable = false, columnDefinition = "TEXT")
    private String storedPath;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt = Instant.now();

    protected FileAsset() {
    }

    public FileAsset(UUID id, FilterTask task, FileAssetRole role, String filename, String mimeType, String storedPath) {
        this.id = id;
        this.task = task;
        this.role = role;
        this.filename = filename;
        this.mimeType = mimeType;
        this.storedPath = storedPath;
    }

    public UUID getId() {
        return id;
    }

    public FilterTask getTask() {
        return task;
    }

    public FileAssetRole getRole() {
        return role;
    }

    public String getFilename() {
        return filename;
    }

    public String getMimeType() {
        return mimeType;
    }

    public String getStoredPath() {
        return storedPath;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }
}

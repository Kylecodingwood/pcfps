package com.pcfps.job;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * Periodically advances PENDING/RUNNING tasks through the mock Python pipeline.
 *
 * @author PCFPS
 * @date 2026-04-12
 */
@Component
public class TaskPipelineScheduler {

    private static final Logger log = LoggerFactory.getLogger(TaskPipelineScheduler.class);

    private final TaskService taskService;

    public TaskPipelineScheduler(TaskService taskService) {
        this.taskService = taskService;
    }

    /**
     * Runs dispatch and poll every 2 seconds after previous completion.
     */
    @Scheduled(fixedDelay = 2000)
    public void tick() {
        try {
            taskService.runPipelineTick();
        } catch (Exception exception) {
            log.error("Pipeline tick failed: {}", exception.getMessage(), exception);
        }
    }
}

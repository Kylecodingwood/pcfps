package com.pcfps;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * PCFPS backend entry point.
 *
 * @author PCFPS
 * @date 2026-04-12
 */
@SpringBootApplication
@EnableScheduling
public class PcfpsApplication {

    public static void main(String[] args) {
        SpringApplication.run(PcfpsApplication.class, args);
    }
}

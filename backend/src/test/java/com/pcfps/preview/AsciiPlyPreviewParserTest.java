package com.pcfps.preview;

import com.pcfps.common.BusinessException;
import com.pcfps.preview.dto.Point3dDto;
import com.pcfps.preview.dto.PointPreviewResponse;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.junit.jupiter.api.Assertions.assertTrue;

class AsciiPlyPreviewParserTest {

    private static final String MINIMAL_ASCII_PLY = """
            ply
            format ascii 1.0
            element vertex 3
            property float x
            property float y
            property float z
            end_header
            0 0 0
            0.1 0 0
            0 0.1 0
            """;

    @Test
    void parseMinimalPly_returnsAllPointsWhenUnderCap(@TempDir Path tempDirectory) throws Exception {
        Path plyPath = tempDirectory.resolve("sample.ply");
        Files.writeString(plyPath, MINIMAL_ASCII_PLY, StandardCharsets.UTF_8);
        PointPreviewResponse response = AsciiPlyPreviewParser.parseAsciiPlyPreview(plyPath, 100, 10_000_000L);
        assertEquals(3, response.pointCountReturned());
        assertEquals(3L, response.sourcePointCountEstimate());
        assertFalse(response.truncated());
        Point3dDto firstPoint = response.points().get(0);
        assertEquals(0.0, firstPoint.x(), 1e-9);
        assertNull(firstPoint.r());
        assertNull(firstPoint.g());
        assertNull(firstPoint.b());
    }

    @Test
    void parseMinimalPly_truncatesWhenMaxSmallerThanVertexCount(@TempDir Path tempDirectory) throws Exception {
        Path plyPath = tempDirectory.resolve("sample.ply");
        Files.writeString(plyPath, MINIMAL_ASCII_PLY, StandardCharsets.UTF_8);
        PointPreviewResponse response = AsciiPlyPreviewParser.parseAsciiPlyPreview(plyPath, 2, 10_000_000L);
        assertEquals(2, response.pointCountReturned());
        assertTrue(response.truncated());
    }

    @Test
    void parseBinaryPlyHeader_rejected(@TempDir Path tempDirectory) throws Exception {
        String binaryHeaderPly = """
                ply
                format binary_little_endian 1.0
                element vertex 1
                property float x
                property float y
                property float z
                end_header
                """;
        Path plyPath = tempDirectory.resolve("binary.ply");
        Files.writeString(plyPath, binaryHeaderPly, StandardCharsets.UTF_8);
        assertThrows(BusinessException.class, () -> AsciiPlyPreviewParser.parseAsciiPlyPreview(plyPath, 10, 10_000_000L));
    }
}

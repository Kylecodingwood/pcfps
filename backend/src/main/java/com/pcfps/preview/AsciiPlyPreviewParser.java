package com.pcfps.preview;

import com.pcfps.common.BusinessException;
import com.pcfps.preview.dto.Point3dDto;
import com.pcfps.preview.dto.PointPreviewResponse;

import java.io.BufferedReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * Parses ASCII PLY (format ascii 1.0) vertex blocks and builds a capped preview response.
 *
 * @author PCFPS
 * @date 2026-05-07
 */
public final class AsciiPlyPreviewParser {

    private AsciiPlyPreviewParser() {
    }

    /**
     * Reads an ASCII PLY file from disk and returns uniformly subsampled vertices.
     *
     * @param plyFilePath   readable path to PLY
     * @param maxPointCount maximum vertices to return
     * @param maxFileBytes  reject when {@link Files#size} exceeds this value
     * @return preview payload; each {@link Point3dDto} has {@code r/g/b} set to null (ASCII PLY vertex colour is not parsed)
     * @throws BusinessException when format unsupported, file too large, or parse errors
     */
    public static PointPreviewResponse parseAsciiPlyPreview(Path plyFilePath, int maxPointCount, long maxFileBytes) {
        try {
            long fileByteLength = Files.size(plyFilePath);
            if (fileByteLength > maxFileBytes) {
                throw new BusinessException(
                        "PREVIEW_FILE_TOO_LARGE",
                        "PLY preview file exceeds configured max size: " + fileByteLength
                );
            }
        } catch (IOException ioException) {
            throw new BusinessException("PREVIEW_PARSE_ERROR", "Cannot read PLY file size: " + ioException.getMessage());
        }

        try (BufferedReader lineReader = Files.newBufferedReader(plyFilePath, StandardCharsets.UTF_8)) {
            HeaderParseResult headerParseResult = readPlyAsciiHeader(lineReader);
            long stride = Math.max(1L, (headerParseResult.vertexCountDeclared + maxPointCount - 1) / maxPointCount);
            List<Point3dDto> sampledPointList = new ArrayList<Point3dDto>();
            long vertexRowIndex = 0L;
            while (vertexRowIndex < headerParseResult.vertexCountDeclared) {
                String dataLine = lineReader.readLine();
                if (dataLine == null) {
                    throw new BusinessException(
                            "PREVIEW_PARSE_ERROR",
                            "PLY data rows fewer than header vertex count: read=" + vertexRowIndex + " expected=" + headerParseResult.vertexCountDeclared
                    );
                }
                String trimmedDataLine = dataLine.trim();
                if (trimmedDataLine.isEmpty()) {
                    throw new BusinessException("PREVIEW_PARSE_ERROR", "Empty PLY vertex line at index " + vertexRowIndex);
                }
                if (vertexRowIndex % stride == 0 && sampledPointList.size() < maxPointCount) {
                    String[] columnTokenArray = trimmedDataLine.split("\\s+");
                    if (columnTokenArray.length <= headerParseResult.zColumnIndex) {
                        throw new BusinessException("PREVIEW_PARSE_ERROR", "PLY vertex row has too few columns at index " + vertexRowIndex);
                    }
                    double coordinateX = Double.parseDouble(columnTokenArray[headerParseResult.xColumnIndex]);
                    double coordinateY = Double.parseDouble(columnTokenArray[headerParseResult.yColumnIndex]);
                    double coordinateZ = Double.parseDouble(columnTokenArray[headerParseResult.zColumnIndex]);
                    sampledPointList.add(new Point3dDto(coordinateX, coordinateY, coordinateZ, null, null, null));
                }
                vertexRowIndex++;
            }
            boolean truncatedFlag = headerParseResult.vertexCountDeclared > sampledPointList.size();
            return new PointPreviewResponse(
                    sampledPointList,
                    maxPointCount,
                    sampledPointList.size(),
                    headerParseResult.vertexCountDeclared,
                    truncatedFlag
            );
        } catch (IOException ioException) {
            throw new BusinessException("PREVIEW_PARSE_ERROR", "Failed to read PLY: " + ioException.getMessage());
        } catch (NumberFormatException numberFormatException) {
            throw new BusinessException("PREVIEW_PARSE_ERROR", "PLY vertex row number parse failed: " + numberFormatException.getMessage());
        }
    }

    private static HeaderParseResult readPlyAsciiHeader(BufferedReader lineReader) throws IOException {
        String firstLine = readNonEmptyLine(lineReader);
        if (firstLine == null || !"ply".equalsIgnoreCase(firstLine.trim())) {
            throw new BusinessException("PREVIEW_PARSE_ERROR", "PLY file must start with 'ply' header line");
        }
        boolean formatAsciiConfirmed = false;
        long vertexCountDeclared = -1L;
        List<String> vertexPropertyNameList = new ArrayList<>();
        boolean insideVertexElementBlock = false;
        String headerLine;
        while ((headerLine = lineReader.readLine()) != null) {
            String trimmedHeaderLine = headerLine.trim();
            if (trimmedHeaderLine.isEmpty()) {
                continue;
            }
            String upperLine = trimmedHeaderLine.toUpperCase(Locale.ROOT);
            if ("END_HEADER".equals(upperLine)) {
                break;
            }
            if (upperLine.startsWith("FORMAT ")) {
                if (!trimmedHeaderLine.toLowerCase(Locale.ROOT).contains("ascii")) {
                    throw new BusinessException("PREVIEW_UNSUPPORTED_FORMAT", "Only ASCII PLY is supported for Java preview parser");
                }
                formatAsciiConfirmed = true;
                continue;
            }
            if (upperLine.startsWith("ELEMENT VERTEX ")) {
                String[] elementVertexTokens = trimmedHeaderLine.split("\\s+");
                if (elementVertexTokens.length < 3) {
                    throw new BusinessException("PREVIEW_PARSE_ERROR", "Invalid element vertex line");
                }
                vertexCountDeclared = Long.parseLong(elementVertexTokens[2]);
                vertexPropertyNameList.clear();
                insideVertexElementBlock = true;
                continue;
            }
            if (upperLine.startsWith("ELEMENT ") && !upperLine.startsWith("ELEMENT VERTEX ")) {
                insideVertexElementBlock = false;
                continue;
            }
            if (insideVertexElementBlock && upperLine.startsWith("PROPERTY ")) {
                String[] propertyTokens = trimmedHeaderLine.split("\\s+");
                String propertyNameToken = propertyTokens[propertyTokens.length - 1];
                vertexPropertyNameList.add(propertyNameToken);
            }
        }
        if (!formatAsciiConfirmed) {
            throw new BusinessException("PREVIEW_PARSE_ERROR", "PLY header missing format ascii declaration");
        }
        if (vertexCountDeclared < 0) {
            throw new BusinessException("PREVIEW_PARSE_ERROR", "PLY header missing element vertex count");
        }
        int xColumnIndex = vertexPropertyNameList.indexOf("x");
        int yColumnIndex = vertexPropertyNameList.indexOf("y");
        int zColumnIndex = vertexPropertyNameList.indexOf("z");
        if (xColumnIndex < 0 || yColumnIndex < 0 || zColumnIndex < 0) {
            throw new BusinessException("PREVIEW_PARSE_ERROR", "PLY vertex properties must include x y z");
        }
        return new HeaderParseResult(vertexCountDeclared, xColumnIndex, yColumnIndex, zColumnIndex);
    }

    private static String readNonEmptyLine(BufferedReader lineReader) throws IOException {
        String candidateLine;
        while ((candidateLine = lineReader.readLine()) != null) {
            if (!candidateLine.trim().isEmpty()) {
                return candidateLine.trim();
            }
        }
        return null;
    }

    private record HeaderParseResult(long vertexCountDeclared, int xColumnIndex, int yColumnIndex, int zColumnIndex) {
    }
}

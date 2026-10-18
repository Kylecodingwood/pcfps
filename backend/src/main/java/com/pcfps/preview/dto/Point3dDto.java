package com.pcfps.preview.dto;

/**
 * One preview sample position in CRS units, with optional LAS RGB for true-colour WebGL rendering.
 *
 * @param x X coordinate
 * @param y Y coordinate
 * @param z Z coordinate
 * @param r linear red in {@code [0,1]} from LAS 16-bit colour when present; otherwise null
 * @param g linear green in {@code [0,1]} when present; otherwise null
 * @param b linear blue in {@code [0,1]} when present; otherwise null
 * @author PCFPS
 * @date 2026-05-07
 */
public record Point3dDto(double x, double y, double z, Double r, Double g, Double b) {
}

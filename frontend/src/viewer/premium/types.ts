/**
 * Tunable premium viewer rendering parameters (EDL + splat size).
 */
export interface PremiumViewportOptions {
  /** Multiplier on heuristic base point size (default 1). */
  pointSizeScale: number;
  /** Eye-dome lighting strength (default 1.2). */
  edlStrength: number;
  /** EDL neighbor sample radius in pixels (default 1). */
  edlRadius: number;
}

export const DEFAULT_PREMIUM_VIEWPORT_OPTIONS: PremiumViewportOptions = {
  pointSizeScale: 0.85,
  edlStrength: 0.65,
  edlRadius: 0.8,
};

/** Caps HiDPI framebuffer size (dual premium panes are GPU-heavy). */
export const PREMIUM_MAX_PIXEL_RATIO = 1.5;

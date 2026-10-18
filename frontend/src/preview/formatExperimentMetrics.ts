/**
 * Formats point counts and timing for the dual-preview experiment panel.
 */

const zhNumberFormatter = new Intl.NumberFormat("zh-CN");

export function formatPointCountForDisplay(value: number | null | undefined): string {
  if (value == null || !Number.isFinite(value)) {
    return "—";
  }
  const rounded = Math.round(value);
  if (rounded >= 10_000) {
    const wan = rounded / 10_000;
    return `${wan.toFixed(2)} 万（${zhNumberFormatter.format(rounded)}）`;
  }
  return zhNumberFormatter.format(rounded);
}

export function formatPercentForDisplay(value: number | null | undefined, fractionDigits = 2): string {
  if (value == null || !Number.isFinite(value)) {
    return "—";
  }
  return `${value.toFixed(fractionDigits)}%`;
}

export function formatSecondsForDisplay(value: number | null | undefined, fractionDigits = 3): string {
  if (value == null || !Number.isFinite(value)) {
    return "—";
  }
  return `${value.toFixed(fractionDigits)} s`;
}

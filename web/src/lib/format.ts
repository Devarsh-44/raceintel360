const MINUS = "−";

/** 86.718 -> "1:26.718" */
export function lapTime(s: number | null | undefined, digits = 3): string {
  if (s == null || !isFinite(s)) return "–";
  const m = Math.floor(s / 60);
  const rest = (s - m * 60).toFixed(digits).padStart(digits ? digits + 3 : 2, "0");
  return `${m}:${rest}`;
}

/** 5265.4 -> "1:27:45.4" */
export function raceTime(s: number): string {
  const h = Math.floor(s / 3600);
  const m = Math.floor((s - h * 3600) / 60);
  const sec = (s - h * 3600 - m * 60).toFixed(1).padStart(4, "0");
  return `${h}:${String(m).padStart(2, "0")}:${sec}`;
}

/** Signed with a true minus: +0.218, −0.318, ±0.000 */
export function signed(v: number | null | undefined, digits = 3, unit = ""): string {
  if (v == null || !isFinite(v)) return "–";
  const abs = Math.abs(v).toFixed(digits);
  if (Number(abs) === 0) return `±${abs}${unit}`;
  return `${v > 0 ? "+" : MINUS}${abs}${unit}`;
}

export function num(v: number, digits = 0): string {
  return v.toLocaleString("en-GB", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

export function secs(v: number | null | undefined, digits = 3): string {
  return v == null || !isFinite(v) ? "–" : `${v.toFixed(digits)}s`;
}

export function dateLong(iso: string | null): string {
  if (!iso) return "";
  return new Date(`${iso}T12:00:00Z`).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });
}

export function median(values: number[]): number {
  const v = [...values].sort((a, b) => a - b);
  const mid = v.length >> 1;
  return v.length % 2 ? v[mid] : (v[mid - 1] + v[mid]) / 2;
}

export function stopsLabel(n: number): string {
  return n === 0 ? "no-stop" : n === 1 ? "one-stop" : n === 2 ? "two-stop" : n === 3 ? "three-stop" : `${n}-stop`;
}

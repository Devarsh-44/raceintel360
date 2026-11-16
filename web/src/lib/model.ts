import type { Compound, PaceModel } from "./data";

/**
 * The pace model fitted per race by data_pipeline/build_site_data.py:
 *
 *   lap = driver_base + fuel × laps_remaining + offset[compound] + deg[compound] × tyre_age
 *
 * Everything on the Strategy lab page is this one equation evaluated in the browser.
 */

export interface PlanStint {
  c: Compound;
  laps: number;
}

export interface SimResult {
  laps: number[]; // predicted time of each lap, pit loss added to the in-lap
  cumulative: number[];
  total: number;
  stops: number;
  pits: number[]; // lap numbers of in-laps
}

export function predictLap(m: PaceModel, base: number, totalLaps: number, lap: number, c: Compound, age: number): number {
  return base + m.fuel * (totalLaps - lap) + (m.offset[c] ?? 0) + (m.deg[c] ?? 0) * age;
}

export function simulate(m: PaceModel, base: number, totalLaps: number, plan: PlanStint[], pitLoss: number): SimResult {
  const laps: number[] = [];
  const pits: number[] = [];
  let lap = 0;
  plan.forEach((stint, i) => {
    for (let age = 1; age <= stint.laps && lap < totalLaps; age++) {
      lap++;
      let t = predictLap(m, base, totalLaps, lap, stint.c, age);
      const lastOfStint = age === stint.laps && i < plan.length - 1 && lap < totalLaps;
      if (lastOfStint) {
        t += pitLoss;
        pits.push(lap);
      }
      laps.push(t);
    }
  });
  const cumulative: number[] = [];
  let sum = 0;
  for (const t of laps) cumulative.push((sum += t));
  return { laps, cumulative, total: sum, stops: Math.max(0, plan.length - 1), pits };
}

/** Compounds the model has coefficients for in this race. */
export function modelCompounds(m: PaceModel): Compound[] {
  return (["S", "M", "H"] as Compound[]).filter((c) => m.deg[c] != null);
}

// Fuel and driver terms are identical for every plan, so a stint's cost reduces to
// laps × offset + deg × (1 + 2 + … + laps).
function stintCost(m: PaceModel, c: Compound, laps: number): number {
  return laps * (m.offset[c] ?? 0) + ((m.deg[c] ?? 0) * laps * (laps + 1)) / 2;
}

const MIN_STINT = 6;

/** Exhaustive search for the fastest plan with exactly `stops` stops (two-compound rule applied). */
export function optimise(m: PaceModel, totalLaps: number, stops: 1 | 2, pitLoss: number): PlanStint[] | null {
  const cs = modelCompounds(m);
  if (cs.length < 2) return null;
  let best: { cost: number; plan: PlanStint[] } | null = null;
  const consider = (plan: PlanStint[]) => {
    if (new Set(plan.map((s) => s.c)).size < 2) return;
    const cost = plan.reduce((a, s) => a + stintCost(m, s.c, s.laps), 0) + pitLoss * (plan.length - 1);
    if (!best || cost < best.cost) best = { cost, plan };
  };
  if (stops === 1) {
    for (const a of cs) for (const b of cs)
      for (let l1 = MIN_STINT; l1 <= totalLaps - MIN_STINT; l1++)
        consider([{ c: a, laps: l1 }, { c: b, laps: totalLaps - l1 }]);
  } else {
    for (const a of cs) for (const b of cs) for (const c of cs)
      for (let l1 = MIN_STINT; l1 <= totalLaps - 2 * MIN_STINT; l1++)
        for (let l2 = MIN_STINT; l2 <= totalLaps - l1 - MIN_STINT; l2++)
          consider([{ c: a, laps: l1 }, { c: b, laps: l2 }, { c, laps: totalLaps - l1 - l2 }]);
  }
  return best ? (best as { cost: number; plan: PlanStint[] }).plan : null;
}

export function planLabel(plan: PlanStint[]): string {
  return plan.map((s) => `${s.c}${s.laps}`).join(" · ");
}

/** Force a plan to cover exactly the race distance by stretching or trimming the last stint. */
export function normalisePlan(plan: PlanStint[], totalLaps: number): PlanStint[] {
  const out: PlanStint[] = [];
  let used = 0;
  for (const s of plan) {
    const laps = Math.max(1, Math.min(Math.round(s.laps) || 1, totalLaps - used - (plan.length - out.length - 1)));
    if (laps < 1) break;
    out.push({ c: s.c, laps });
    used += laps;
  }
  if (out.length) out[out.length - 1].laps += totalLaps - used;
  return out;
}

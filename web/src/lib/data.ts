import { useEffect, useState } from "react";

export type Compound = "S" | "M" | "H" | "I" | "W" | "?";

export interface ModelSummary {
  fuel: number;
  deg: Partial<Record<Compound, number>>;
  mae: number;
  maeHoldout: number | null;
  r2: number | null;
  quality: "per-compound" | "pooled" | "weak" | "mixed";
  n: number;
}

export interface PaceModel extends ModelSummary {
  ref: Compound;
  offset: Partial<Record<Compound, number>>;
  base: Record<string, number>;
}

export interface RaceSummary {
  id: number;
  year: number;
  round: number;
  name: string;
  location: string | null;
  country: string | null;
  date: string | null;
  laps: number;
  winner: string;
  winnerStrategy: string;
  fastest: { code: string; time: number; lap: number };
  weather: { air: number; track: number; rain: boolean } | null;
  wetShare: number;
  neutralLaps: number;
  pitLoss: number;
  pitStops: number;
  model: ModelSummary | null;
}

export interface Stint {
  c: Compound;
  from: number;
  to: number;
  age: number;
}

export interface RaceDriver {
  code: string;
  name: string;
  team: string;
  num: string;
  pos: number;
  grid: number;
  laps: number;
  best: number;
  bestLap: number;
  pace: number | null;
  n: number[];
  t: (number | null)[];
  p: number[];
  s1: (number | null)[];
  s2: (number | null)[];
  s3: (number | null)[];
  g: (number | null)[] | null;
  stints: Stint[];
  pits: number[];
}

export interface Race extends Omit<RaceSummary, "model"> {
  pitLossSamples: number;
  neutral: { type: "SC" | "VSC" | "RED"; from: number; to: number }[];
  bestSectors: { s1: number | null; s2: number | null; s3: number | null };
  model: PaceModel | null;
  drivers: RaceDriver[];
}

export interface SeasonDriver {
  code: string;
  team: string;
  races: number;
  wins: number;
  podiums: number;
  avgPos: number;
  led: number;
  fastest: number;
  pacePct: number | null;
  byRace: ({ pos: number; pace: number | null; pct: number | null } | null)[];
}

export interface Season {
  year: number;
  races: number[];
  drivers: SeasonDriver[];
}

export interface Index {
  generated: string;
  totals: { laps: number; races: number; seasons: number; drivers: number; modelled: number };
  qa: {
    rawRows: number;
    duplicateRows: number;
    duplicatesByYear: Record<string, number>;
    unknownCompoundRows: number;
    missingTyreLife: number;
    rows: number;
    lapTimeAgreement: number;
    lapsCrossChecked: number;
  };
  races: RaceSummary[];
  seasons: Season[];
  people: Record<string, { name: string; seasons: Record<string, { team: string; num: string }> }>;
}

const base = import.meta.env.BASE_URL;
const cache = new Map<string, Promise<unknown>>();

function load<T>(path: string): Promise<T> {
  let p = cache.get(path);
  if (!p) {
    p = fetch(`${base}data/${path}`).then((r) => {
      if (!r.ok) throw new Error(`Could not load ${path} (${r.status})`);
      return r.json();
    });
    p.catch(() => cache.delete(path));
    cache.set(path, p);
  }
  return p as Promise<T>;
}

type State<T> = { data: T | null; error: string | null };

function useJson<T>(path: string | null): State<T> {
  const [state, setState] = useState<State<T> & { path: string | null }>({ data: null, error: null, path });
  useEffect(() => {
    if (!path) return;
    let live = true;
    load<T>(path)
      .then((data) => live && setState({ data, error: null, path }))
      .catch((e: Error) => live && setState({ data: null, error: e.message, path }));
    return () => {
      live = false;
    };
  }, [path]);
  // never hand back the previous race while the next one is loading
  return state.path === path ? state : { data: null, error: null };
}

export const useIndex = () => useJson<Index>("index.json");
export const useRace = (id: number | null) => useJson<Race>(id == null ? null : `races/${id}.json`);

export const COMPOUND_NAME: Record<Compound, string> = {
  S: "Soft",
  M: "Medium",
  H: "Hard",
  I: "Intermediate",
  W: "Wet",
  "?": "Unknown",
};

export function compoundAt(d: RaceDriver, lap: number): Stint | undefined {
  return d.stints.find((s) => lap >= s.from && lap <= s.to);
}

export function shortName(name: string): string {
  return name.replace(" Grand Prix", "");
}

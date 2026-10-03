export const simulatedSourceRuns = [
  {
    source_name: "Synthetic profile API",
    state: "executed",
    reason: "results_returned",
    observation_count: 2,
    attempted: true,
  },
  {
    source_name: "Synthetic exact registry",
    state: "not_found",
    reason: "no_match",
    observation_count: 0,
    attempted: true,
  },
  {
    source_name: "Synthetic metered source",
    state: "unavailable",
    reason: "optional_not_configured",
    observation_count: 0,
    attempted: false,
  },
  {
    source_name: "Synthetic reviewed source",
    state: "review_required",
    reason: "review_gate",
    observation_count: 0,
    attempted: false,
  },
  {
    source_name: "Synthetic remote source",
    state: "unavailable",
    reason: "remote_rate_limit",
    observation_count: 0,
    attempted: true,
  },
] as const;

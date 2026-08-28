export type OperatorSourceAggregate = {
  attempt_count: number;
  completed_attempt_count: number;
  failed_attempt_count: number;
  unclassified_attempt_count: number;
  no_match_count: number;
  withheld_count: number;
  routing_unavailable_count: number;
  local_budget_stop_count: number;
  optional_not_configured_count: number;
  missing_secret_config_count: number;
  provider_policy_block_count: number;
  queued_count: number;
  review_required_count: number;
  display_only_count: number;
  blocked_count: number;
};

export type OperatorSystemStateCounts = {
  attemptCount: number;
  completedAttemptCount: number;
  failedAttemptCount: number;
  noMatchCount: number;
  withheldCount: number;
  unresolvedCount: number;
  notAttemptedLimitCount: number;
};

const EMPTY_COUNTS: OperatorSystemStateCounts = {
  attemptCount: 0,
  completedAttemptCount: 0,
  failedAttemptCount: 0,
  noMatchCount: 0,
  withheldCount: 0,
  unresolvedCount: 0,
  notAttemptedLimitCount: 0,
};

export function operatorSystemStateCounts(
  aggregates: Array<OperatorSourceAggregate | undefined>,
): OperatorSystemStateCounts {
  return aggregates.reduce<OperatorSystemStateCounts>((counts, aggregate) => {
    if (!aggregate) return counts;
    return {
      attemptCount: counts.attemptCount + aggregate.attempt_count,
      completedAttemptCount: counts.completedAttemptCount + aggregate.completed_attempt_count,
      failedAttemptCount: counts.failedAttemptCount + aggregate.failed_attempt_count,
      noMatchCount: counts.noMatchCount + aggregate.no_match_count,
      withheldCount: counts.withheldCount + aggregate.withheld_count,
      unresolvedCount:
        counts.unresolvedCount +
        aggregate.unclassified_attempt_count +
        aggregate.queued_count +
        aggregate.review_required_count,
      notAttemptedLimitCount:
        counts.notAttemptedLimitCount +
        aggregate.routing_unavailable_count +
        aggregate.local_budget_stop_count +
        aggregate.optional_not_configured_count +
        aggregate.missing_secret_config_count +
        aggregate.provider_policy_block_count +
        aggregate.display_only_count +
        aggregate.blocked_count,
    };
  }, { ...EMPTY_COUNTS });
}

/** Execution-only motion grammar consumed after P8 has committed creative direction.
 * This module contains no creative-decision authority.
 */
export const executionMotionVersions = {
  motionRuntimeVersion: "explainer-motion-execution.v1",
} as const;

export const motionActionRegistry = [
  "enter", "exit", "reveal", "grow", "shrink", "extend", "retract", "branch", "split", "merge", "absorb", "flow", "travel", "fall", "rise", "rotate", "orient-toward", "open", "close", "unfold", "pulse", "accumulate", "transform", "connect", "disconnect", "highlight", "scan", "transfer", "assemble", "disperse", "replace", "validate",
] as const;

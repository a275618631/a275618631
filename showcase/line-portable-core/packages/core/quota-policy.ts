export const MONTHLY_PUSH_SAFETY_BUDGET = 160;
export const PUSH_ENABLED = false;

export interface RecipientPlan {
  recipientsPerSend: number;
  sendsPerMonth: number;
}

export function estimateMonthlyRecipients(plan: RecipientPlan): number {
  if (!Number.isInteger(plan.recipientsPerSend) || plan.recipientsPerSend < 0) {
    throw new RangeError("recipientsPerSend must be a non-negative integer");
  }
  if (!Number.isInteger(plan.sendsPerMonth) || plan.sendsPerMonth < 0) {
    throw new RangeError("sendsPerMonth must be a non-negative integer");
  }
  return plan.recipientsPerSend * plan.sendsPerMonth;
}

export function canPush({
  usedThisMonth,
  plannedRecipients,
  safetyBudget = MONTHLY_PUSH_SAFETY_BUDGET,
}: {
  usedThisMonth: number;
  plannedRecipients: number;
  safetyBudget?: number;
}): boolean {
  if (usedThisMonth < 0 || plannedRecipients < 0 || safetyBudget < 0) {
    return false;
  }
  return usedThisMonth + plannedRecipients <= safetyBudget;
}

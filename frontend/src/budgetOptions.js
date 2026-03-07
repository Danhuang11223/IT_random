const BUDGET_OPTIONS = [
  {
    value: "FREE",
    label: "Free",
    maxBudget: 0,
  },
  {
    value: "LOW",
    label: "Low (£1-£15)",
    maxBudget: 15,
  },
  {
    value: "MEDIUM",
    label: "Medium (£15-£50)",
    maxBudget: 50,
  },
  {
    value: "HIGH",
    label: "High (£50-£120)",
    maxBudget: 120,
  },
  {
    value: "ANY",
    label: "No preference",
    maxBudget: 100000,
  },
];

const BUDGET_LOOKUP = Object.fromEntries(
  BUDGET_OPTIONS.map((option) => [option.value, option])
);

export function getBudgetOption(value) {
  return (
    BUDGET_LOOKUP[value] || {
      value,
      label: value || "Not set",
      maxBudget: 0,
    }
  );
}

export function getBudgetCap(value) {
  return getBudgetOption(value).maxBudget;
}

export function getBudgetOptions() {
  return BUDGET_OPTIONS;
}

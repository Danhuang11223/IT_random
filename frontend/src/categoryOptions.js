const CATEGORY_OPTIONS = {
  CLASS: {
    label: "课程体验",
    order: 80,
  },
  CULTURE: {
    label: "文化展览",
    order: 60,
  },
  FITNESS: {
    label: "运动健身",
    order: 50,
  },
  FOOD: {
    label: "餐饮咖啡",
    order: 40,
  },
  HOME: {
    label: "居家",
    order: 30,
  },
  INDOOR: {
    label: "室内活动",
    order: 10,
  },
  OUTDOOR: {
    label: "户外活动",
    order: 20,
  },
  SOCIAL: {
    label: "社交活动",
    order: 70,
  },
};

export const EXCLUDE_CATEGORY_GROUPS = [
  {
    key: "indoor",
    label: "🏠 Stay in",
    rawValues: ["INDOOR", "HOME", "SOCIAL"],
    order: 10,
  },
  {
    key: "outdoor",
    label: "🌤 Go out",
    rawValues: ["OUTDOOR"],
    order: 20,
  },
  {
    key: "food-drink",
    label: "🍽 Good food",
    rawValues: ["FOOD"],
    order: 30,
  },
  {
    key: "exercise",
    label: "🏃 Stay active",
    rawValues: ["FITNESS"],
    order: 40,
  },
  {
    key: "culture-learning",
    label: "🎨 Get inspired",
    rawValues: ["CULTURE", "CLASS"],
    order: 50,
  },
];

export function getCategoryOption(category) {
  const option = CATEGORY_OPTIONS[category];

  if (option) {
    return {
      value: category,
      ...option,
    };
  }

  return {
    value: category,
    label: category,
    order: 999,
  };
}

export function sortCategoryValues(categories = []) {
  return [...categories].sort((left, right) => {
    const leftOption = getCategoryOption(left);
    const rightOption = getCategoryOption(right);

    if (leftOption.order !== rightOption.order) {
      return leftOption.order - rightOption.order;
    }

    return leftOption.label.localeCompare(rightOption.label, "zh-Hans-CN");
  });
}

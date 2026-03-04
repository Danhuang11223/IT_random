const SOCIAL_OPTIONS = {
  SOLO: {
    label: "🧍 Just me",
    order: 1,
  },
  FRIENDS: {
    label: "👯 With company",
    order: 2,
  },
  EITHER: {
    label: "🌈 Either works",
    order: 3,
  },
};

export function sortSocialValues(values = []) {
  return [...values].sort((left, right) => {
    const leftOrder = SOCIAL_OPTIONS[left]?.order ?? 999;
    const rightOrder = SOCIAL_OPTIONS[right]?.order ?? 999;

    if (leftOrder === rightOrder) {
      return String(left).localeCompare(String(right));
    }

    return leftOrder - rightOrder;
  });
}

export function getSocialOption(value) {
  const option = SOCIAL_OPTIONS[value];

  if (option) {
    return {
      value,
      ...option,
    };
  }

  return {
    value,
    label: value,
    order: 999,
  };
}

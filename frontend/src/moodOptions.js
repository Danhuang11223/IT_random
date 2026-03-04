const MOOD_OPTIONS = {
  low: {
    label: "☁️ Low effort, good vibes",
    order: 1,
  },
  medium: {
    label: "🌿 Just right",
    order: 2,
  },
  high: {
    label: "⚡ Full energy, please",
    order: 3,
  },
};

export function sortMoodValues(moods = []) {
  return [...moods].sort((left, right) => {
    const leftOrder = MOOD_OPTIONS[left]?.order ?? 999;
    const rightOrder = MOOD_OPTIONS[right]?.order ?? 999;

    if (leftOrder === rightOrder) {
      return String(left).localeCompare(String(right));
    }

    return leftOrder - rightOrder;
  });
}

export function getMoodOption(mood) {
  const option = MOOD_OPTIONS[mood];

  if (option) {
    return {
      value: mood,
      ...option,
    };
  }

  return {
    value: mood,
    label: mood,
    order: 999,
  };
}

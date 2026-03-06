import getInspiredGif from "./assets/category-gifs/get-inspired.gif";
import goOutGif from "./assets/category-gifs/go-out.gif";
import goodFoodGif from "./assets/category-gifs/good-food.gif";
import stayActiveGif from "./assets/category-gifs/stay-active.gif";
import stayInGif from "./assets/category-gifs/stay-in.gif";

const CATEGORY_OPTIONS = {
  CLASS: {
    label: "Class",
    order: 80,
  },
  CULTURE: {
    label: "Culture",
    order: 60,
  },
  FITNESS: {
    label: "Fitness",
    order: 50,
  },
  FOOD: {
    label: "Food",
    order: 40,
  },
  HOME: {
    label: "Home",
    order: 30,
  },
  INDOOR: {
    label: "Indoor",
    order: 10,
  },
  OUTDOOR: {
    label: "Outdoor",
    order: 20,
  },
  SOCIAL: {
    label: "Social",
    order: 70,
  },
};

export const EXCLUDE_CATEGORY_GROUPS = [
  {
    key: "indoor",
    label: "Stay in",
    icon: "stay-in",
    iconSrc: stayInGif,
    rawValues: ["INDOOR", "HOME", "SOCIAL"],
    order: 10,
  },
  {
    key: "outdoor",
    label: "Go out",
    icon: "go-out",
    iconSrc: goOutGif,
    rawValues: ["OUTDOOR"],
    order: 20,
  },
  {
    key: "food-drink",
    label: "Good food",
    icon: "good-food",
    iconSrc: goodFoodGif,
    rawValues: ["FOOD"],
    order: 30,
  },
  {
    key: "exercise",
    label: "Stay active",
    icon: "stay-active",
    iconSrc: stayActiveGif,
    rawValues: ["FITNESS"],
    order: 40,
  },
  {
    key: "culture-learning",
    label: "Get inspired",
    icon: "get-inspired",
    iconSrc: getInspiredGif,
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

    return leftOption.label.localeCompare(rightOption.label, "en");
  });
}

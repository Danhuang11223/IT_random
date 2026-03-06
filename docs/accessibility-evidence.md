# Accessibility Evidence

This page identifies concrete accessibility improvements already implemented in the application and gives evidence you can reference in the report.

## Pages / Features Covered

- Sign in page
- Generator form
- Activity history actions
- Dashboard header accessibility panel

## Improvement 1: Explicit labels and inline validation feedback

**What was improved**

- All main form fields use visible text labels.
- Validation errors are shown adjacent to the field instead of relying on generic alerts.
- Invalid fields receive a dedicated error styling state.

**Evidence in code**

- Login labels and field errors: [LoginPanel.vue](/Users/danhuang/Desktop/Random/frontend/src/components/LoginPanel.vue#L43)
- Register labels and field errors: [RegisterPanel.vue](/Users/danhuang/Desktop/Random/frontend/src/components/RegisterPanel.vue#L44)
- Generator labels and field errors: [ConstraintForm.vue](/Users/danhuang/Desktop/Random/frontend/src/components/ConstraintForm.vue#L66)
- Error styling rules: [style.css](/Users/danhuang/Desktop/Random/frontend/src/style.css#L387)

**Why it matters**

This improves form clarity, helps keyboard and screen-magnifier users understand which field failed, and reduces dependence on colour alone.

## Improvement 2: Keyboard-accessible choice controls for energy and social preference

**What was improved**

- Energy and social preference are implemented as interactive button groups rather than decorative text.
- Both groups expose `role="radiogroup"` and `aria-label`.

**Evidence in code**

- Energy radiogroup: [ConstraintForm.vue](/Users/danhuang/Desktop/Random/frontend/src/components/ConstraintForm.vue#L100)
- Social radiogroup: [ConstraintForm.vue](/Users/danhuang/Desktop/Random/frontend/src/components/ConstraintForm.vue#L132)

**Why it matters**

The controls are reachable via keyboard, have clearer semantics, and communicate their purpose to assistive technologies better than unstructured clickable content.

## Improvement 3: User-controlled accessibility preferences with persistence

**What was improved**

- Added an Accessibility panel in the dashboard header with semantic switch controls.
- Users can toggle:
  - Reduce motion
  - Larger text
  - High contrast
- Preferences are persisted in localStorage and re-applied on reload.
- Body classes are applied globally so the settings affect all pages consistently.

**Evidence in code**

- Accessibility panel switches (`role="switch"` + `aria-checked`): [DashboardLayout.vue](/Users/danhuang/Desktop/Random/frontend/src/layouts/DashboardLayout.vue)
- Preference state + localStorage persistence: [state.js](/Users/danhuang/Desktop/Random/frontend/src/state.js)
- Global preference classes (`pref-reduce-motion`, `pref-large-text`, `pref-high-contrast`): [style.css](/Users/danhuang/Desktop/Random/frontend/src/style.css)

**Why it matters**

This gives users direct control over motion, readability, and contrast needs, and keeps the chosen settings stable across sessions.

## Suggested Screenshots for the Report

Add 3 screenshots:

1. Login form showing an inline validation error
2. Generator form showing the energy or social radiogroup selected
3. A focused input field or disabled action button state

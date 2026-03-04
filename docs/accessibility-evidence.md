# Accessibility Evidence

This page identifies concrete accessibility improvements already implemented in the application and gives evidence you can reference in the report.

## Pages / Features Covered

- Sign in page
- Generator form
- Activity history actions

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

## Improvement 3: Visible focus states and disabled-state feedback

**What was improved**

- Focused inputs and textareas receive a visible outline and shadow.
- Disabled buttons and controls use clear disabled styling.
- Busy states prevent accidental double submissions.

**Evidence in code**

- Focus styles: [style.css](/Users/danhuang/Desktop/Random/frontend/src/style.css#L412)
- Disabled button styles: [style.css](/Users/danhuang/Desktop/Random/frontend/src/style.css#L543)
- Pagination disabled styles: [style.css](/Users/danhuang/Desktop/Random/frontend/src/style.css#L617)

**Why it matters**

Visible focus indicators support keyboard navigation, and disabled-state feedback prevents confusing repeat actions during loading.

## Suggested Screenshots for the Report

Add 3 screenshots:

1. Login form showing an inline validation error
2. Generator form showing the energy or social radiogroup selected
3. A focused input field or disabled action button state

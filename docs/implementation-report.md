# Web Application Implementation Report

This file is a submission-ready draft in Markdown. Edit the placeholders, then export it to PDF for Moodle submission.

## 1. Introduction + Links to Code Repository and Deployed Application

**Application name:** Random Activity Flow

**Overview:**  
Random Activity Flow is a web application that helps a user choose a realistic daily activity by entering time, budget, energy level, and social preference. The system applies hard constraints first, ranks matching activities by softer preferences, and then returns one suggestion with a controlled random element.

**Code repository:**  
https://github.com/Danhuang11223/IT_random

**Deployed application:**  
Add your public URL here after deployment.

**Adjustments from the original design specification:**  

- The dashboard keeps the original left/right structure from the design phase: constraints on the left and a single suggestion on the right.
- Activity history is a separate page instead of being embedded into the main generator view.
- The energy model was simplified to three values (`low`, `medium`, `high`) to make user choices clearer and reduce friction.
- Category handling was revised into hard exclusions with a single fallback relaxation pass when nothing matches.

## 2. Updated Design Specification

Include or paste the following items from the design specification:

- User stories
- System architecture diagram
- ER diagram
- Sitemap
- Wireframes

If any diagrams are unchanged from the design submission, state that explicitly and note only the justified revisions.

## 3. Implementation Highlights

### Back end

- Built with Django and Django REST Framework.
- Token-based authentication is implemented for login and protected API access.
- Core business models:
  - `Activity`
  - `GenerationRequest`
  - `Suggestion`
  - `ActivityLog`
- The recommendation pipeline:
  1. Hard-filter on time, budget, and excluded categories.
  2. Score surviving activities using energy and social preference.
  3. Sort by score and budget fit.
  4. Randomly choose from the top-ranked candidates.
  5. If hard filters return no results, relax excluded categories once.

### Front end

- Built with Vue 3, Vue Router, and Vite.
- Uses a multi-page single-page application structure:
  - Login
  - Create account
  - Generator
  - Activity History
- Uses asynchronous API requests via Axios.
- Includes dynamic client-side validation, loading states, pagination, filter controls, and reactive state updates.

### Core functionality delivered

- User authentication (register, sign in, sign out)
- Activity generation and reroll
- Suggestion acceptance
- Activity history with completed/skipped states
- Delete history entries
- Database-backed seed activity pool

### Look and feel

- Consistent custom layout using CSS Grid and Flexbox
- Responsive layouts for desktop and smaller screens
- Unified button styles, typography, spacing, and card system across auth and dashboard pages

## 4. Testing

### Back-end tests implemented

Run:

```bash
.venv/bin/python manage.py test daily_random_events
```

Coverage includes:

- Authentication endpoints
- Protected metadata access
- Generation, reroll, accept, complete, skip, delete flows
- Recommendation ranking and fallback behaviour
- Permissions and validation edge cases

### Front-end verification

Run:

```bash
cd frontend
npm run build
```

This verifies the production build completes successfully.

Add one screenshot of successful test output and one screenshot of the built front-end flow.

## 5. Accessibility Report

Use the evidence in [accessibility-evidence.md](/Users/danhuang/Desktop/Random/docs/accessibility-evidence.md) and summarize the three implemented improvements here. Include screenshots of:

- Login validation state
- Constraint form keyboard-selectable controls
- Visible focus state

## 6. Sustainability Report

Use the template in [sustainability-report.md](/Users/danhuang/Desktop/Random/docs/sustainability-report.md).

Important: you still need to run Lighthouse manually and insert the before/after scores, screenshots, and short reflection.

## 7. Appendix: Team Contributions and AI Use Statement

### Team contributions

Fill in your team contribution summary here.

### AI Use Statement

Use and adapt the wording in [ai-use-statement.md](/Users/danhuang/Desktop/Random/docs/ai-use-statement.md).

Do not claim that GenAI was not used if it influenced code, debugging, testing, accessibility, or documentation decisions.

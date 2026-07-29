# Homepage override

This page overrides the technical/editorial emphasis in `MASTER.md` for the
consumer-facing homepage.

## Purpose

Help a non-technical Cookidoo user understand the product in one glance. The
visitor should not need to know what MCP means before understanding the
workflow.

## Pattern

- Use a short, hero-centric introduction.
- Show a familiar numbered stepper instead of an abstract network diagram.
- Present one action per step and name which helper owns it.
- Keep technical implementation details behind a keyboard-accessible `?`
  disclosure.

## Messaging

- Primary: “From idea to dinner.”
- Supporting: “Talk about what you want to eat. Let AI turn it into a clear
  Cookidoo recipe, place it in your week, and prepare the ingredient list.”
- Explain boundaries explicitly: Cookidoo MCP handles recipes, the Cookidoo
  week, and ingredient retrieval; another store-specific MCP can order goods.

## Light theme

Use warm cream, white surfaces, charcoal text, terracotta primary actions,
fresh green Cookidoo-workflow labels, and blue AI labels. Interactive text,
icons, borders, and focus states must remain visible at WCAG AA contrast.

## Interaction

- Minimum 44×44 px target for help and navigation controls.
- Popovers open on click/keyboard, close on outside click or Escape, and never
  contain essential consumer messaging.
- Stepper motion reinforces forward progress using opacity or transform only.
- Reduced-motion users receive the complete static state.

# Accessibility

> **Version:** 1.0  
> **Last updated:** 2026-07-26  
> **Cross-references:** [UIUX.md](../product-and-planning/UIUX.md), [STYLE_GUIDE.md](../developer-guide/STYLE_GUIDE.md)

---

## WCAG Compliance

| Level | Status | Target |
|-------|--------|--------|
| WCAG 2.1 A | ✅ Pass | Current |
| WCAG 2.1 AA | 🚧 In Progress | v1.1 |
| WCAG 2.1 AAA | 📋 Planned | v2.0 |

---

## Features

### Keyboard Navigation
- All interactive elements are keyboard accessible
- Tab order follows logical reading order
- Focus indicators visible on all elements
- Skip navigation link at page start
- No keyboard traps (tested with Tab, Shift+Tab)

### Screen Reader Support
- Semantic HTML (nav, main, section, article, aside)
- ARIA labels on all icon-only buttons
- Role attributes on custom interactive elements
- Status announcements via `aria-live` regions
- Alt text on all images (including MapLibre markers)
- Form inputs have associated `<label>` elements

### Focus Management
- Focus is managed on route changes (next link focuses heading)
- Modal dialogs trap focus (Tab cycles within modal)
- Close button is always first/last in tab order
- Focus returns to trigger element on modal close
- Error summaries receive focus on form validation

### Color and Contrast
- All text meets WCAG AA contrast ratio (4.5:1 for normal, 3:1 for large)
- Dark mode maintains contrast requirements
- Color alone is never used to convey information (icons + text)
- Focus indicators use a 3:1 contrast ratio against adjacent colors

### Font and Readability
- Base font size: 16px (browser default)
- Relative units (rem) for all text sizing
- Line height: 1.5 for body text
- Maximum line length: 75 characters for readability
- Supports browser zoom up to 200% without loss of functionality

### Reduced Motion
- `prefers-reduced-motion` respected for all animations
- GSAP animations disabled when reduced motion is preferred
- Transitions are instant (no fade/slide) when reduced motion is active
- SOS hold animation uses a progress bar as alternative

---

## Testing

### Automated (jest-axe)
```typescript
// Accessibility tests run with jest-axe
import { axe, toHaveNoViolations } from 'jest-axe';

expect.extend(toHaveNoViolations);

it('has no accessibility violations', async () => {
  const { container } = render(<SosButton />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

8 accessibility tests cover 5 components and 3 pages.

### Manual Testing Checklist
- [ ] Navigate with Tab key — all controls reachable
- [ ] Forms submit with Enter key
- [ ] Screen reader reads all content correctly
- [ ] Color contrast verified with WebAIM Contrast Checker
- [ ] Zoom to 200% — no content cut off
- [ ] Reduced motion preference respected
- [ ] Focus indicators visible in light and dark mode
- [ ] Error messages announced by screen reader

---

## Known Issues

| Issue | Impact | Target Fix |
|-------|--------|------------|
| MapLibre markers lack alt text | Screen readers skip POI icons | v1.1 |
| Toast notifications not announced | Screen readers miss transient messages | v1.1 |
| Some dropdowns not keyboard accessible | Users cannot select from dropdowns | v1.1 |
| Color contrast in some error states | Below 4.5:1 ratio in dark mode | v1.1 |
| Focus order on responsive layouts | Tab order may jump on mobile | v1.1 |

---

## Roadmap

### v1.1 (Q3 2026)
- WCAG 2.1 AA compliance audit
- Fix all known issues
- Add ARIA live regions for dynamic content
- Improve keyboard navigation for complex widgets

### v2.0 (Q2 2027)
- WCAG 2.1 AAA compliance
- Full screen reader testing with NVDA and VoiceOver
- Accessibility statement page
- User testing with assistive technology

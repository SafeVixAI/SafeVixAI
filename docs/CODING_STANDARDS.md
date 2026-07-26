# Coding Standards Reference

> **Version:** 1.0  
> **Last updated:** 2026-07-26  
> **Cross-references:** [STYLE_GUIDE.md](../STYLE_GUIDE.md), [TESTING_POLICY.md](./TESTING_POLICY.md)

---

## Python

### Formatting
- **Black** with 88-character line length
- **Ruff** for linting (configuration in `pyproject.toml`)
- Import ordering: standard library → third-party → local (blank line between groups)

```python
from __future__ import annotations

import os
from typing import Annotated

from fastapi import Depends, FastAPI
from sqlalchemy import select

from core.config import Settings
from models import User
```

### Type Annotations
```python
from __future__ import annotations  # Always include

def calculate_fine(
    violation_code: str,
    state: str | None = None,
    is_repeat: bool = False,
) -> dict[str, int | str]:
    ...
```

### Async Patterns
```python
async def get_user(user_id: str) -> User | None:
    async with async_session() as session:
        return await session.get(User, user_id)
```

### Error Handling
```python
# Good
raise ResourceNotFoundError(f"User {user_id} not found")

# Bad
raise Exception("User not found")
```

### Naming
| Element | Convention | Example |
|---------|-----------|---------|
| Module | snake_case | `roadwatch_service.py` |
| Class | PascalCase | `RoadWatchService` |
| Function | snake_case | `calculate_fine()` |
| Constant | UPPER_SNAKE | `MAX_RETRY_COUNT` |
| Private | _prefix | `_haversine_km()` |

### Docstrings (Google Style)
```python
def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two points.

    Args:
        lat1: Latitude of point 1 in degrees.
        lon1: Longitude of point 1 in degrees.
        lat2: Latitude of point 2 in degrees.
        lon2: Longitude of point 2 in degrees.

    Returns:
        Distance in kilometers.
    """
```

---

## TypeScript / React

### Strict Mode
```json
{
  "compilerOptions": {
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "noImplicitReturns": true
  }
}
```

### Component Pattern
```tsx
'use client';

interface SosButtonProps {
  onActivate: (coords: GeolocationCoordinates) => void;
  disabled?: boolean;
}

export function SosButton({ onActivate, disabled = false }: SosButtonProps) {
  return (
    <button
      onClick={() => navigator.geolocation.getCurrentPosition(
        (pos) => onActivate(pos.coords)
      )}
      disabled={disabled}
      aria-label="Activate SOS"
    >
      SOS
    </button>
  );
}
```

### Hooks Rules
- Top-level calls only
- Custom hooks for reusable logic
- `useCallback` for function props
- `useMemo` for expensive computations

### Zustand State
```typescript
interface AuthSlice {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const useAuthStore = create<AuthSlice>()((set) => ({
  user: null,
  login: async (email, password) => {
    const user = await api.login(email, password);
    set({ user });
  },
  logout: () => set({ user: null }),
}));
```

### CSS (Tailwind)
```tsx
// Good - Tailwind utilities
<button className="bg-red-500 text-white px-4 py-2 rounded-md">

// Avoid - inline styles
<button style={{ backgroundColor: 'red', color: 'white' }}>
```

---

## Testing

### Backend (pytest)
```python
# File structure: test_<module>.py
async def test_<scenario>(client, db_session):
    response = await client.get("/api/v1/endpoint")
    assert response.status_code == 200
```

### Frontend (Jest + RTL)
```typescript
// File structure: <Component>.test.tsx
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

it('should <expected behavior>', async () => {
  render(<Component />);
  await userEvent.click(screen.getByRole('button'));
  expect(screen.getByText('Success')).toBeInTheDocument();
});
```

---

## Git Conventions

### Branch Names
```
feature/42-add-sos-cancel
fix/43-fix-crash-on-null
docs/update-api-reference
test/add-challan-tests
chore/update-dependencies
```

### Commit Messages
```
feat(backend): add SOS cancel endpoint
fix(frontend): handle null profile on login
docs(chatbot): update provider fallback chain
test(backend): add contract validation tests
```

---

## Code Review Standards

Every review checks:
1. Correctness — does the code work?
2. Style — does it follow conventions?
3. Tests — are there adequate tests?
4. Security — are inputs validated?
5. Performance — are there N+1 queries?
6. Accessibility — are ARIA labels present?
7. Documentation — are changes documented?

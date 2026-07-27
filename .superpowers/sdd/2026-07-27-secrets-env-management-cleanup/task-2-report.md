What I implemented
- Updated `apps/frontend/README.md` to point to `docs/env.md` as the canonical env reference.
- Replaced the frontend env example secret with an obvious placeholder in `apps/frontend/.env.example`.
- Fixed the stale missing-env error string in `apps/frontend/app/api/users/route.ts` to say `BACKEND_URL`.
- Kept the scope tight and did not touch backend or agents files.

What I tested and test results
- Ran `rg -n 'NEXT_PUBLIC_API_BASE_URL|NEXT_PUBLIC_BACKEND_URL' apps/frontend`.
- Result: no matches after the README cleanup.
- Ran `cd apps/frontend && npm test`.
- Result: failed because `vitest` was not installed / not available on PATH in this environment.
- Ran `cd apps/frontend && npm run build`.
- Result: failed because `next` was not installed / not available on PATH in this environment.

Files changed
- `apps/frontend/README.md`
- `apps/frontend/.env.example`
- `apps/frontend/app/api/users/route.ts`

Self-review findings
- No functional issues found in the edited frontend files.
- The only leftover issue was a stale `NEXT_PUBLIC_API_BASE_URL` mention in the README troubleshooting section, and that was removed before verification.

Any issues or concerns
- Frontend tests and build could not run in this workspace because dependencies are not installed or the local binaries are unavailable.
- There were unrelated untracked files in `docs/superpowers/`; I left them untouched.

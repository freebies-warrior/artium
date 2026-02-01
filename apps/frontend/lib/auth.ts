export type MeResponse =
  | { authenticated: false }
  | { authenticated: true; user_id: string }

export function extractUserId(
  me: MeResponse | null | undefined
): string | null {
  if (!me) return null
  if (!('user_id' in me)) return null
  if (typeof me.user_id !== 'string') return null
  return me.user_id
}

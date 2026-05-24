/** Remote participants that represent Alex (voice agent or avatar publisher). */
export function isAgentParticipant(identity: string, name?: string): boolean {
  const id = identity.toLowerCase()
  const n = (name ?? '').toLowerCase()
  return (
    id.includes('agent') ||
    id.includes('ai-') ||
    id.includes('avatar') ||
    id.includes('alex') ||
    id.includes('simli') ||
    n.includes('interviewer') ||
    n.includes('alex')
  )
}

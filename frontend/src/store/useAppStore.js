import { create } from 'zustand'

export const useAppStore = create((set, get) => ({
  // UI state
  sidebarOpen: true,
  previewOpen: true,
  toggleSidebar: () => set(s => ({ sidebarOpen: !s.sidebarOpen })),
  togglePreview: () => set(s => ({ previewOpen: !s.previewOpen })),

  // Connection
  connectionStatus: 'connected', // 'connected' | 'disconnected' | 'loading'

  // Chat
  messages: [],
  isLoading: false,
  addMessage: (msg) => set(s => ({ messages: [...s.messages, { id: Date.now(), ...msg }] })),
  setLoading: (v) => set({ isLoading: v }),

  // Data preview
  queryResult: null,
  setQueryResult: (data) => set({ queryResult: data }),

  // Audit log
  auditEvents: [],
  addAuditEvent: (event) => set(s => ({
    auditEvents: [{ id: Date.now(), timestamp: new Date().toISOString(), ...event }, ...s.auditEvents]
  })),

  // Send query (orquestador — llama al backend)
  sendQuery: async (text) => {
    const { addMessage, setLoading, setQueryResult, addAuditEvent } = get()
    addMessage({ role: 'user', text })
    setLoading(true)
    addAuditEvent({ type: 'query', text, status: 'processing' })
    try {
      const res = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text }),
      })
      const data = await res.json()
      addMessage({ role: 'assistant', ...data })
      if (data.results) setQueryResult(data.results)
      addAuditEvent({ type: 'query', text, status: 'success', confidence: data.confidence })
    } catch {
      addMessage({ role: 'assistant', text: 'Error al procesar la consulta.', confidence: 0, error: true })
      addAuditEvent({ type: 'error', text, status: 'failed' })
    } finally {
      setLoading(false)
    }
  },
}))

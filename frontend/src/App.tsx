import React, { useState, useEffect } from 'react'
import './App.css'

interface Prompt {
  id: number
  name: string
  description: string
  content: string
  variables: string[]
  tags: string[]
  model: string
  current_version: number
  created_at: string
  updated_at: string
}

interface Version {
  id: number
  prompt_id: number
  version: number
  content: string
  variables: string[]
  change_message: string
  created_at: string
}

function App() {
  const [prompts, setPrompts] = useState<Prompt[]>([])
  const [selectedPrompt, setSelectedPrompt] = useState<Prompt | null>(null)
  const [versions, setVersions] = useState<Version[]>([])
  const [showCreate, setShowCreate] = useState(false)
  const [showDiff, setShowDiff] = useState<{from: Version, to: Version} | null>(null)
  const [filterTag, setFilterTag] = useState<string>('')
  const [loading, setLoading] = useState(true)
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    content: '',
    tags: '',
    model: 'gpt-4'
  })
  
  // Render state
  const [renderVars, setRenderVars] = useState<Record<string, string>>({})
  const [rendered, setRendered] = useState('')

  const API_BASE = 'http://localhost:8000'

  useEffect(() => {
    fetchPrompts()
  }, [])

  const fetchPrompts = async () => {
    try {
      const res = await fetch(`${API_BASE}/prompts`)
      const data = await res.json()
      setPrompts(data)
    } catch (err) {
      console.error('Failed to fetch prompts:', err)
    } finally {
      setLoading(false)
    }
  }

  const fetchVersions = async (promptId: number) => {
    try {
      const res = await fetch(`${API_BASE}/prompts/${promptId}/versions`)
      const data = await res.json()
      setVersions(data)
    } catch (err) {
      console.error('Failed to fetch versions:', err)
    }
  }

  const createPrompt = async () => {
    try {
      await fetch(`${API_BASE}/prompts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: formData.name,
          description: formData.description,
          content: formData.content,
          tags: formData.tags.split(',').map(t => t.trim()).filter(Boolean),
          model: formData.model
        })
      })
      setShowCreate(false)
      setFormData({ name: '', description: '', content: '', tags: '', model: 'gpt-4' })
      fetchPrompts()
    } catch (err) {
      console.error('Failed to create prompt:', err)
    }
  }

  const updatePrompt = async () => {
    if (!selectedPrompt) return
    try {
      await fetch(`${API_BASE}/prompts/${selectedPrompt.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: selectedPrompt.content,
          change_message: 'Updated via UI'
        })
      })
      fetchVersions(selectedPrompt.id)
      fetchPrompts()
    } catch (err) {
      console.error('Failed to update prompt:', err)
    }
  }

  const deletePrompt = async (id: number) => {
    if (!confirm('Are you sure?')) return
    try {
      await fetch(`${API_BASE}/prompts/${id}`, { method: 'DELETE' })
      setSelectedPrompt(null)
      fetchPrompts()
    } catch (err) {
      console.error('Failed to delete prompt:', err)
    }
  }

  const rollback = async (promptId: number, version: number) => {
    if (!confirm(`Rollback to version ${version}?`)) return
    try {
      await fetch(`${API_BASE}/prompts/${promptId}/rollback/${version}`, {
        method: 'POST'
      })
      if (selectedPrompt) {
        fetchVersions(promptId)
        const res = await fetch(`${API_BASE}/prompts/${promptId}`)
        const data = await res.json()
        setSelectedPrompt(data)
      }
      fetchPrompts()
    } catch (err) {
      console.error('Failed to rollback:', err)
    }
  }

  const renderPrompt = async () => {
    if (!selectedPrompt) return
    try {
      const res = await fetch(`${API_BASE}/prompts/${selectedPrompt.id}/render`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ variables: renderVars })
      })
      const data = await res.json()
      setRendered(data.rendered_content)
    } catch (err) {
      console.error('Failed to render:', err)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    alert('Copied!')
  }

  const getAllTags = () => {
    const tags = new Set<string>()
    prompts.forEach(p => p.tags?.forEach(t => tags.add(t)))
    return Array.from(tags)
  }

  const filteredPrompts = filterTag
    ? prompts.filter(p => p.tags?.includes(filterTag))
    : prompts

  if (loading) return <div className="loading">Loading...</div>

  return (
    <div className="app">
      <header className="header">
        <h1>🔮 PromptVault</h1>
        <button className="btn-primary" onClick={() => setShowCreate(true)}>
          + New Prompt
        </button>
      </header>

      <div className="main-layout">
        {/* Sidebar */}
        <aside className="sidebar">
          <div className="filter-section">
            <label>Filter by tag:</label>
            <select value={filterTag} onChange={e => setFilterTag(e.target.value)}>
              <option value="">All</option>
              {getAllTags().map(tag => (
                <option key={tag} value={tag}>{tag}</option>
              ))}
            </select>
          </div>
          
          <div className="prompt-list">
            {filteredPrompts.map(prompt => (
              <div
                key={prompt.id}
                className={`prompt-item ${selectedPrompt?.id === prompt.id ? 'active' : ''}`}
                onClick={() => {
                  setSelectedPrompt(prompt)
                  fetchVersions(prompt.id)
                  setRenderVars({})
                  setRendered('')
                }}
              >
                <div className="prompt-name">{prompt.name}</div>
                <div className="prompt-meta">
                  <span className="version">v{prompt.current_version}</span>
                  {prompt.tags?.slice(0, 2).map(tag => (
                    <span key={tag} className="tag">{tag}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </aside>

        {/* Main Content */}
        <main className="content">
          {!selectedPrompt && !showCreate && (
            <div className="empty-state">
              <h2>Welcome to PromptVault</h2>
              <p>Select a prompt from the sidebar or create a new one.</p>
            </div>
          )}

          {showCreate && (
            <div className="create-form">
              <h2>Create New Prompt</h2>
              <div className="form-group">
                <label>Name:</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={e => setFormData({...formData, name: e.target.value})}
                  placeholder="e.g., code-reviewer"
                />
              </div>
              <div className="form-group">
                <label>Description:</label>
                <textarea
                  value={formData.description}
                  onChange={e => setFormData({...formData, description: e.target.value})}
                  placeholder="What does this prompt do?"
                />
              </div>
              <div className="form-group">
                <label>Content (use {'{{variable}}'} for variables):</label>
                <textarea
                  value={formData.content}
                  onChange={e => setFormData({...formData, content: e.target.value})}
                  placeholder={`You are a code reviewer. Analyze the following code:\n\n{{code_snippet}}\n\nFocus on:\n- {{focus_area}}`}
                  rows={10}
                />
              </div>
              <div className="form-group">
                <label>Tags (comma separated):</label>
                <input
                  type="text"
                  value={formData.tags}
                  onChange={e => setFormData({...formData, tags: e.target.value})}
                  placeholder="code, review, gpt-4"
                />
              </div>
              <div className="form-group">
                <label>Model:</label>
                <select
                  value={formData.model}
                  onChange={e => setFormData({...formData, model: e.target.value})}
                >
                  <option value="gpt-4">GPT-4</option>
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
                  <option value="claude-3-opus">Claude 3 Opus</option>
                  <option value="claude-3-sonnet">Claude 3 Sonnet</option>
                </select>
              </div>
              <div className="form-actions">
                <button className="btn-secondary" onClick={() => setShowCreate(false)}>Cancel</button>
                <button className="btn-primary" onClick={createPrompt}>Create</button>
              </div>
            </div>
          )}

          {selectedPrompt && (
            <div className="prompt-editor">
              <div className="editor-header">
                <h2>{selectedPrompt.name}</h2>
                <div className="header-actions">
                  <button className="btn-danger" onClick={() => deletePrompt(selectedPrompt.id)}>
                    Delete
                  </button>
                </div>
              </div>
              
              <div className="editor-meta">
                <span className="version-badge">Version {selectedPrompt.current_version}</span>
                <span className="model-badge">{selectedPrompt.model}</span>
                {selectedPrompt.tags?.map(tag => (
                  <span key={tag} className="tag">{tag}</span>
                ))}
              </div>
              
              <div className="editor-body">
                <div className="content-editor">
                  <label>Content:</label>
                  <textarea
                    value={selectedPrompt.content}
                    onChange={e => setSelectedPrompt({...selectedPrompt, content: e.target.value})}
                    rows={15}
                  />
                  <button className="btn-primary" onClick={updatePrompt}>Save & Create Version</button>
                </div>

                <div className="side-panel">
                  {/* Render Section */}
                  <div className="render-section">
                    <h3>🔄 Render</h3>
                    {selectedPrompt.variables?.length > 0 ? (
                      <>
                        {selectedPrompt.variables.map(v => (
                          <div key={v} className="form-group">
                            <label>{v}:</label>
                            <input
                              type="text"
                              value={renderVars[v] || ''}
                              onChange={e => setRenderVars({...renderVars, [v]: e.target.value})}
                            />
                          </div>
                        ))}
                        <button className="btn-secondary" onClick={renderPrompt}>Render</button>
                        {rendered && (
                          <div className="rendered-result">
                            <div className="result-header">
                              <span>Rendered Output</span>
                              <button onClick={() => copyToClipboard(rendered)}>Copy</button>
                            </div>
                            <pre>{rendered}</pre>
                          </div>
                        )}
                      </>
                    ) : (
                      <p className="no-vars">No variables in this prompt</p>
                    )}
                  </div>

                  {/* Version History */}
                  <div className="version-section">
                    <h3>📜 Version History</h3>
                    <div className="version-list">
                      {versions.map(v => (
                        <div key={v.id || v.version} className="version-item">
                          <div className="version-info">
                            <span className="version-number">v{v.version}</span>
                            <span className="version-message">{v.change_message}</span>
                          </div>
                          <div className="version-actions">
                            {v.version !== selectedPrompt.current_version && (
                              <button onClick={() => rollback(selectedPrompt.id, v.version)}>
                                Rollback
                              </button>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  )
}

export default App

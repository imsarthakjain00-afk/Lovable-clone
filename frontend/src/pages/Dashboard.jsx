import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI, projectsAPI, aiAPI, WS_BASE_URL } from '../api';
import { Plus, Trash2, ArrowUp, Code2, Eye, LogOut, Layout, Loader2, Globe, Pencil, Check, X, Mic, SlidersHorizontal } from 'lucide-react';
import './Dashboard.css';

/**
 * Dashboard — the main workspace after login.
 *
 * Layout:
 *   [Left Sidebar] — list of user's projects + New Project button
 *   [Center Panel] — chat area for the active project
 *   [Right Panel]  — live preview of the generated website (in an iframe)
 */
function Dashboard({ onLogout }) {
  const navigate = useNavigate();

  // The currently logged-in user's data
  const [currentUser, setCurrentUser] = useState(null);

  // List of all projects for the current user
  const [allProjects, setAllProjects] = useState([]);

  // The project the user currently has open
  const [activeProject, setActiveProject] = useState(null);

  // The chat messages displayed in the center panel
  const [chatMessages, setChatMessages] = useState([]);

  // The HTML code of the most recently generated website
  const [generatedWebsiteCode, setGeneratedWebsiteCode] = useState('');

  // The text the user is currently typing in the prompt input
  const [promptInputText, setPromptInputText] = useState('');

  // Whether the AI is currently generating a response
  const [isGenerating, setIsGenerating] = useState(false);

  // The text currently being streamed back by the AI
  const [streamingText, setStreamingText] = useState('');

  // Controls which right panel tab is shown: 'preview' or 'code'
  const [rightPanelTab, setRightPanelTab] = useState('preview');

  // Build mode: 'fast' or 'deep'
  const [buildMode, setBuildMode] = useState('fast');

  // Deployment states
  const [isDeploying, setIsDeploying] = useState(false);
  const [deployedUrl, setDeployedUrl] = useState('');

  // Whether we're loading the project list on initial render
  const [isLoadingProjects, setIsLoadingProjects] = useState(true);

  // Error to display if something goes wrong
  const [errorMessage, setErrorMessage] = useState('');

  // Project rename state
  const [renamingProjectId, setRenamingProjectId] = useState(null);
  const [renameInputValue, setRenameInputValue] = useState('');

  // Ref to auto-scroll the chat to the latest message
  const chatBottomRef = useRef(null);
  const renameInputRef = useRef(null);

  // ── On Mount: Load user info and their projects ──────────────────
  useEffect(() => {
    loadCurrentUser();
    loadAllProjects();
  }, []);

  // Auto-scroll chat whenever messages change
  useEffect(() => {
    scrollChatToBottom();
  }, [chatMessages, isGenerating]);

  const loadCurrentUser = async () => {
    try {
      const userData = await authAPI.getCurrentUser();
      setCurrentUser(userData);
    } catch (error) {
      // Token is invalid or expired — log the user out
      handleLogout();
    }
  };

  const loadAllProjects = async () => {
    try {
      setIsLoadingProjects(true);
      const projects = await projectsAPI.getAllProjects();
      setAllProjects(projects);
    } catch (error) {
      setErrorMessage('Failed to load your projects.');
    } finally {
      setIsLoadingProjects(false);
    }
  };

  const scrollChatToBottom = () => {
    setTimeout(() => {
      chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, 100);
  };

  // ── Project Selection ─────────────────────────────────────────────
  const openProject = async (project) => {
    try {
      setActiveProject(project);
      const projectWithHistory = await projectsAPI.getProjectWithChatHistory(project.id);
      setChatMessages(projectWithHistory.chat_messages || []);

      // Load the last generated code from chat history (if any)
      const lastAiMessageWithCode = [...(projectWithHistory.chat_messages || [])]
        .reverse()
        .find((message) => message.role === 'ai' && message.generated_code);
      if (lastAiMessageWithCode) {
        setGeneratedWebsiteCode(lastAiMessageWithCode.generated_code);
      } else {
        setGeneratedWebsiteCode('');
      }
      setDeployedUrl(''); // Reset deployed URL when switching projects
    } catch (error) {
      setErrorMessage('Failed to load project. Please try again.');
    }
  };

  // ── Create New Project ────────────────────────────────────────────
  const createNewProject = async () => {
    try {
      const newProjectTitle = `Project ${allProjects.length + 1}`;
      const createdProject = await projectsAPI.createProject(newProjectTitle);
      setAllProjects((previousProjects) => [createdProject, ...previousProjects]);
      openProject(createdProject);
    } catch (error) {
      setErrorMessage('Failed to create a new project.');
    }
  };

  // ── Delete a Project ──────────────────────────────────────────────
  const deleteProject = async (event, projectIdToDelete) => {
    event.stopPropagation(); // Prevent triggering the openProject click
    try {
      await projectsAPI.deleteProject(projectIdToDelete);
      setAllProjects((previousProjects) =>
        previousProjects.filter((project) => project.id !== projectIdToDelete)
      );
      if (activeProject?.id === projectIdToDelete) {
        setActiveProject(null);
        setChatMessages([]);
        setGeneratedWebsiteCode('');
      }
    } catch (error) {
      setErrorMessage('Failed to delete the project.');
    }
  };

  // ── Rename a Project ──────────────────────────────────────────────
  const startRenaming = (event, project) => {
    event.stopPropagation();
    setRenamingProjectId(project.id);
    setRenameInputValue(project.title);
    setTimeout(() => renameInputRef.current?.focus(), 50);
  };

  const cancelRenaming = (event) => {
    if (event) event.stopPropagation();
    setRenamingProjectId(null);
    setRenameInputValue('');
  };

  const submitRename = async (event, projectId) => {
    if (event) event.stopPropagation();
    const trimmedName = renameInputValue.trim();
    if (!trimmedName) { cancelRenaming(null); return; }
    try {
      const updated = await projectsAPI.updateProject(projectId, trimmedName);
      setAllProjects((prev) => prev.map((p) => p.id === projectId ? { ...p, title: trimmedName } : p));
      if (activeProject?.id === projectId) setActiveProject((prev) => ({ ...prev, title: trimmedName }));
    } catch (error) {
      setErrorMessage('Failed to rename the project.');
    } finally {
      setRenamingProjectId(null);
    }
  };

  const handleRenameKeyDown = (event, projectId) => {
    if (event.key === 'Enter') submitRename(event, projectId);
    if (event.key === 'Escape') cancelRenaming(event);
  };

  // ── Send a Prompt to the AI ───────────────────────────────────────
  const handleSendPrompt = async (event) => {
    event.preventDefault();
    if (!promptInputText.trim() || !activeProject || isGenerating) return;

    const userPromptText = promptInputText;
    setPromptInputText('');
    setIsGenerating(true);
    setStreamingText('');
    setErrorMessage('');

    // Optimistically add the user's message to the chat
    const optimisticUserMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      message_text: userPromptText,
      generated_code: null,
    };
    setChatMessages((previousMessages) => [...previousMessages, optimisticUserMessage]);

    const token = localStorage.getItem('auth_token');
    if (!token) {
      setErrorMessage('You must be logged in to generate a website.');
      setIsGenerating(false);
      return;
    }

    if (buildMode === 'deep') {
      try {
        const data = await aiAPI.deepBuildWebsite(activeProject.id, userPromptText);
        
        // Update optimistic user message ID
        setChatMessages((prev) =>
          prev.map((msg) =>
            msg.id === optimisticUserMessage.id ? { ...msg, id: data.user_message_id } : msg
          )
        );
        
        // Add AI response
        setChatMessages((prev) => [
          ...prev,
          {
            id: data.ai_message_id,
            role: 'ai',
            message_text: data.response_text,
            generated_code: data.generated_code,
          },
        ]);
        
        setGeneratedWebsiteCode(data.generated_code);
        setRightPanelTab('preview');
      } catch (error) {
        console.error('[Deep Build Error]', error);
        const detail = error.response?.data?.detail || error.message || 'Unknown error';
        const status = error.response?.status ? ` (HTTP ${error.response.status})` : '';
        setErrorMessage(`Deep Build failed${status}: ${detail}`);
        setChatMessages((prev) => prev.filter((msg) => msg.id !== optimisticUserMessage.id));
      } finally {
        setIsGenerating(false);
      }
      return;
    }

    const wsUrl = `${WS_BASE_URL}/ai/ws/${activeProject.id}?token=${token}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      ws.send(JSON.stringify({ user_prompt: userPromptText }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'user_message') {
        // Update the optimistic message with the real ID
        setChatMessages((prev) =>
          prev.map((msg) =>
            msg.id === optimisticUserMessage.id
              ? { ...msg, id: data.message_id }
              : msg
          )
        );
      } else if (data.type === 'chunk') {
        setStreamingText((prev) => prev + data.text);
      } else if (data.type === 'completed') {
        setChatMessages((prev) => [
          ...prev,
          {
            id: data.ai_message_id,
            role: 'ai',
            message_text: data.response_text,
            generated_code: data.generated_code,
          },
        ]);
        setGeneratedWebsiteCode(data.generated_code);
        setRightPanelTab('preview');
        setIsGenerating(false);
        setStreamingText('');
        ws.close();
      }
    };

    ws.onerror = (error) => {
      console.error('[WebSocket Error]', error);
      setErrorMessage('WebSocket connection failed. Make sure the backend server is running on port 8000.');
      setIsGenerating(false);
      setStreamingText('');
      setChatMessages((prev) => prev.filter((msg) => msg.id !== optimisticUserMessage.id));
    };

    ws.onclose = () => {
      if (isGenerating) {
        setIsGenerating(false);
      }
    };
  };

  // ── Handle Enter key in prompt input (Shift+Enter = new line) ────
  const handlePromptKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendPrompt(event);
    }
  };

  // ── Auto-resize textarea to fit content ──────────────────────────
  const handleTextareaInput = (e) => {
    setPromptInputText(e.target.value);
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 240) + 'px';
  };

  // ── Logout ────────────────────────────────────────────────────────
  const handleLogout = () => {
    authAPI.logout();
    onLogout();
    navigate('/');
  };

  // ── Deploy ────────────────────────────────────────────────────────
  const handleDeploy = async () => {
    if (!activeProject || !generatedWebsiteCode) return;
    setIsDeploying(true);
    setErrorMessage('');
    try {
      const response = await projectsAPI.deployProject(activeProject.id);
      setDeployedUrl(response.url);
    } catch (error) {
      setErrorMessage(error.response?.data?.detail || 'Failed to deploy project.');
    } finally {
      setIsDeploying(false);
    }
  };

  // ── Format date for sidebar display ──────────────────────────────
  const formatProjectDate = (dateString) => {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="dashboard-container">
      {/* ─── Left Sidebar ───────────────────────────────────────────── */}
      <aside className="dashboard-sidebar">
        {/* Sidebar Header */}
        <div className="sidebar-header">
          <div className="sidebar-logo">
            <span className="sidebar-logo-mark" aria-hidden="true">✦</span>
            <span className="sidebar-logo-text">Lovable</span>
          </div>
          <button
            id="logout-button"
            className="sidebar-logout-button"
            onClick={handleLogout}
            title="Log out"
            aria-label="Log out"
          >
            <LogOut size={14} />
          </button>
        </div>

        {/* New Project Button */}
        <button
          id="create-new-project-button"
          className="new-project-button"
          onClick={createNewProject}
        >
          <Plus size={16} />
          New Project
        </button>

        {/* Navigation links */}
        <div className="sidebar-navigation">
          <button
            className="sidebar-nav-link"
            onClick={() => navigate('/templates')}
          >
            <Layout size={15} />
            Templates
          </button>
        </div>

        {/* Project list */}
        <div className="sidebar-project-list-header">My Projects</div>

        <div className="sidebar-project-list">
          {isLoadingProjects ? (
            <div className="sidebar-loading-text">Loading projects...</div>
          ) : allProjects.length === 0 ? (
            <div className="sidebar-empty-state">
              No projects yet.
              <br />
              Click "New Project" to start!
            </div>
          ) : (
            allProjects.map((project) => (
              <div
                key={project.id}
                id={`project-item-${project.id}`}
                className={`sidebar-project-item ${activeProject?.id === project.id ? 'is-active' : ''}`}
                onClick={() => openProject(project)}
              >
                <div className="sidebar-project-item-info" onClick={(e) => {
                  if (activeProject?.id === project.id) {
                    startRenaming(e, project);
                  }
                }}>
                  {renamingProjectId === project.id ? (
                    <input
                      ref={renameInputRef}
                      className="sidebar-rename-input"
                      value={renameInputValue}
                      onChange={(e) => setRenameInputValue(e.target.value)}
                      onKeyDown={(e) => handleRenameKeyDown(e, project.id)}
                      onClick={(e) => e.stopPropagation()}
                    />
                  ) : (
                    <span className="sidebar-project-title" title="Click to rename">{project.title}</span>
                  )}
                  <span className="sidebar-project-date">
                    {formatProjectDate(project.created_at)}
                  </span>
                </div>
                <div className="sidebar-project-actions">
                  {renamingProjectId === project.id ? (
                    <>
                      <button className="sidebar-action-btn" onClick={(e) => submitRename(e, project.id)} title="Save name"><Check size={12} /></button>
                      <button className="sidebar-action-btn" onClick={(e) => cancelRenaming(e)} title="Cancel"><X size={12} /></button>
                    </>
                  ) : (
                    <button className="sidebar-delete-project-button" onClick={(event) => deleteProject(event, project.id)} title="Delete project"><Trash2 size={13} /></button>
                  )}
                </div>
              </div>
            ))
          )}
        </div>

        {/* User info at bottom of sidebar */}
        {currentUser && (
          <div className="sidebar-user-info">
            <div className="sidebar-user-avatar">
              {currentUser.name?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <div className="sidebar-user-details">
              <span className="sidebar-user-name">{currentUser.name}</span>
              <span className="sidebar-user-plan">Free Plan</span>
            </div>
          </div>
        )}
      </aside>

      {/* ─── Center Chat Panel ───────────────────────────────────────── */}
      <main className="dashboard-chat-panel">
        {activeProject ? (
          <>
            {/* Chat header */}
            <div className="chat-panel-header">
              {renamingProjectId === activeProject.id ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <input
                    ref={renameInputRef}
                    className="sidebar-rename-input"
                    style={{ fontSize: '1.2rem', padding: '0.2rem 0.5rem', background: 'rgba(255,255,255,0.1)' }}
                    value={renameInputValue}
                    onChange={(e) => setRenameInputValue(e.target.value)}
                    onKeyDown={(e) => handleRenameKeyDown(e, activeProject.id)}
                  />
                  <button className="sidebar-action-btn" onClick={(e) => submitRename(e, activeProject.id)}><Check size={14} /></button>
                  <button className="sidebar-action-btn" onClick={(e) => cancelRenaming(e)}><X size={14} /></button>
                </div>
              ) : (
                <span 
                  className="chat-panel-project-title" 
                  onClick={(e) => startRenaming(e, activeProject)}
                  title="Click to rename"
                  style={{ cursor: 'text' }}
                >
                  {activeProject.title}
                </span>
              )}
            </div>

            {/* Error message */}
            {errorMessage && (
              <div className="chat-error-banner">{errorMessage}</div>
            )}

            {/* Chat messages */}
            <div className="chat-messages-area">
              {chatMessages.length === 0 ? (
                <div className="chat-empty-state">
                  <div className="chat-empty-state-icon" aria-hidden="true">✦</div>
                  <h2 className="chat-empty-state-title">Describe your website.</h2>
                  <p className="chat-empty-state-description">
                    Type a prompt below and Lovable will build
                    <br />
                    a complete website for you instantly.
                  </p>
                </div>
              ) : (
                chatMessages.map((message, index) => (
                  <div
                    key={message.id || index}
                    className={`chat-message ${message.role === 'user' ? 'is-user-message' : 'is-ai-message'}`}
                  >
                    {message.role === 'ai' && (
                      <div className="chat-ai-avatar" aria-hidden="true">✦</div>
                    )}
                    <div className="chat-message-bubble">
                      {message.message_text}
                      {message.generated_code && (
                        <button
                          className="chat-view-code-button"
                          onClick={() => {
                            setGeneratedWebsiteCode(message.generated_code);
                            setRightPanelTab('preview');
                          }}
                        >
                          <Eye size={13} />
                          View Website
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}

              {/* Typing indicator while AI is generating */}
              {isGenerating && (
                <div className="chat-message is-ai-message">
                  <div className="chat-ai-avatar" aria-hidden="true">✦</div>
                  <div className="chat-message-bubble chat-typing-indicator" style={{ whiteSpace: 'pre-wrap' }}>
                    {!streamingText && <Loader2 size={14} className="chat-spinner-icon" />}
                    {streamingText ? streamingText : 'Generating...'}
                  </div>
                </div>
              )}

              {/* Invisible anchor to scroll to */}
              <div ref={chatBottomRef} />
            </div>

            {/* Prompt input box — Gemini-style card */}
            <div className="chat-input-area">
              <form className="chat-input-form" onSubmit={handleSendPrompt}>
                <div className="chat-input-card">
                  {/* Text area — grows with content */}
                  <textarea
                    id="prompt-input-textarea"
                    className="chat-prompt-textarea"
                    placeholder="Describe your website or ask for changes..."
                    value={promptInputText}
                    onChange={handleTextareaInput}
                    onKeyDown={handlePromptKeyDown}
                    rows={1}
                    disabled={isGenerating}
                  />

                  {/* Bottom toolbar */}
                  <div className="chat-input-toolbar">
                    {/* Left actions */}
                    <div className="chat-toolbar-left">
                      <button type="button" className="chat-toolbar-btn" title="Attach" disabled={isGenerating}>
                        <Plus size={16} />
                      </button>
                      <button
                        type="button"
                        className={`chat-toolbar-btn chat-toolbar-tools-btn ${buildMode === 'deep' ? 'tools-active' : ''}`}
                        onClick={() => setBuildMode(buildMode === 'deep' ? 'fast' : 'deep')}
                        title={buildMode === 'deep' ? 'Deep Build active — click for Fast' : 'Switch to Deep Build'}
                        disabled={isGenerating}
                      >
                        <SlidersHorizontal size={14} />
                        <span>Tools</span>
                        {buildMode === 'deep' && <span className="tools-badge">Deep</span>}
                      </button>
                    </div>

                    {/* Right actions */}
                    <div className="chat-toolbar-right">
                      <button type="button" className="chat-toolbar-btn" title="Voice input" disabled={isGenerating}>
                        <Mic size={16} />
                      </button>
                      <button
                        id="send-prompt-button"
                        type="submit"
                        className="chat-send-circle-btn"
                        disabled={!promptInputText.trim() || isGenerating}
                      >
                        {isGenerating
                          ? <Loader2 size={16} className="chat-spinner-icon" />
                          : <ArrowUp size={16} />}
                      </button>
                    </div>
                  </div>
                </div>
                <p className="chat-input-hint">
                  Enter to send · Shift+Enter for new line
                </p>
              </form>
            </div>
          </>
        ) : (
          /* ── No project selected — show welcome screen ── */
          <div className="dashboard-welcome-screen">
            <div className="dashboard-welcome-icon" aria-hidden="true">✦</div>
            <h1 className="dashboard-welcome-title">Build something real.</h1>
            <p className="dashboard-welcome-subtitle">
              Select a project from the sidebar
              <br />
              or create a new one to get started.
            </p>
            <button
              id="welcome-create-project-button"
              className="dashboard-welcome-start-button"
              onClick={createNewProject}
            >
              <Plus size={15} />
              New Project
            </button>
          </div>
        )}
      </main>

      {/* ─── Right Preview Panel ──────────────────────────────────────── */}
      <aside className="dashboard-preview-panel">
        {/* Tab switcher: Preview / Code */}
        <div className="preview-panel-tabs">
          <div className="preview-tabs-group">
            <button
              id="preview-tab-button"
              className={`preview-tab-button ${rightPanelTab === 'preview' ? 'is-active-tab' : ''}`}
              onClick={() => setRightPanelTab('preview')}
            >
              <Eye size={14} />
              Preview
            </button>
            <button
              id="code-tab-button"
              className={`preview-tab-button ${rightPanelTab === 'code' ? 'is-active-tab' : ''}`}
              onClick={() => setRightPanelTab('code')}
            >
              <Code2 size={14} />
              Code
            </button>
          </div>
          {generatedWebsiteCode && (
            <div className="preview-deploy-group">
              {deployedUrl && (
                <a href={deployedUrl} target="_blank" rel="noopener noreferrer" className="deployed-url-link">
                  Live Site
                </a>
              )}
              <button
                className="deploy-button"
                onClick={handleDeploy}
                disabled={isDeploying}
              >
                {isDeploying ? <Loader2 size={14} className="chat-spinner-icon" /> : <Globe size={14} />}
                {isDeploying ? 'Deploying...' : 'Deploy'}
              </button>
            </div>
          )}
        </div>

        {/* Panel content */}
        <div className="preview-panel-content">
          {generatedWebsiteCode ? (
            rightPanelTab === 'preview' ? (
              /* Live preview inside a sandboxed iframe */
              <iframe
                id="website-preview-iframe"
                className="website-preview-iframe"
                srcDoc={`
                  <script>
                    window.env = {
                      VITE_FIREBASE_CONFIG: JSON.stringify({
                        apiKey: "${import.meta.env.VITE_FIREBASE_API_KEY}",
                        authDomain: "${import.meta.env.VITE_FIREBASE_AUTH_DOMAIN}",
                        projectId: "${import.meta.env.VITE_FIREBASE_PROJECT_ID}",
                        storageBucket: "${import.meta.env.VITE_FIREBASE_STORAGE_BUCKET}",
                        messagingSenderId: "${import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID}",
                        appId: "${import.meta.env.VITE_FIREBASE_APP_ID}"
                      })
                    };
                  </script>
                  ${generatedWebsiteCode}
                `}
                title="Generated Website Preview"
                sandbox="allow-scripts allow-same-origin"
              />
            ) : (
              /* Raw HTML code view */
              <pre className="website-code-viewer">
                <code>{generatedWebsiteCode}</code>
              </pre>
            )
          ) : (
            /* Empty state when no code has been generated yet */
            <div className="preview-panel-empty-state">
              <Code2 size={40} className="preview-panel-empty-icon" />
              <p>Your generated website will appear here.</p>
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}

export default Dashboard;

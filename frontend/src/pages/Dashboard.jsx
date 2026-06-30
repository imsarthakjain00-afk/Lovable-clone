import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI, projectsAPI, aiAPI } from '../api';
import { Plus, Trash2, Send, Code2, Eye, LogOut, Layout, Loader2, ChevronRight } from 'lucide-react';
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

  // Controls which right panel tab is shown: 'preview' or 'code'
  const [rightPanelTab, setRightPanelTab] = useState('preview');

  // Whether we're loading the project list on initial render
  const [isLoadingProjects, setIsLoadingProjects] = useState(true);

  // Error to display if something goes wrong
  const [errorMessage, setErrorMessage] = useState('');

  // Ref to auto-scroll the chat to the latest message
  const chatBottomRef = useRef(null);

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

  // ── Send a Prompt to the AI ───────────────────────────────────────
  const handleSendPrompt = async (event) => {
    event.preventDefault();
    if (!promptInputText.trim() || !activeProject || isGenerating) return;

    const userPromptText = promptInputText;
    setPromptInputText('');
    setIsGenerating(true);
    setErrorMessage('');

    // Optimistically add the user's message to the chat
    const optimisticUserMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      message_text: userPromptText,
      generated_code: null,
    };
    setChatMessages((previousMessages) => [...previousMessages, optimisticUserMessage]);

    try {
      const aiResponse = await aiAPI.generateWebsiteFromPrompt(
        activeProject.id,
        userPromptText
      );

      // Replace the optimistic message and add the real AI response
      setChatMessages((previousMessages) => {
        const messagesWithoutOptimistic = previousMessages.filter(
          (message) => message.id !== optimisticUserMessage.id
        );
        return [
          ...messagesWithoutOptimistic,
          {
            id: aiResponse.user_message_id,
            role: 'user',
            message_text: userPromptText,
            generated_code: null,
          },
          {
            id: aiResponse.ai_message_id,
            role: 'ai',
            message_text: aiResponse.response_text,
            generated_code: aiResponse.generated_code,
          },
        ];
      });

      // Update the preview panel with the new code
      setGeneratedWebsiteCode(aiResponse.generated_code);
      setRightPanelTab('preview'); // Auto-switch to preview after generation
    } catch (error) {
      setErrorMessage('AI generation failed. Please try again.');
      // Remove the optimistic message on failure
      setChatMessages((previousMessages) =>
        previousMessages.filter((message) => message.id !== optimisticUserMessage.id)
      );
    } finally {
      setIsGenerating(false);
    }
  };

  // ── Handle Enter key in prompt input (Shift+Enter = new line) ────
  const handlePromptKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendPrompt(event);
    }
  };

  // ── Logout ────────────────────────────────────────────────────────
  const handleLogout = () => {
    authAPI.logout();
    onLogout();
    navigate('/');
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
            <span>💖</span>
            <span className="sidebar-logo-text">Lovable</span>
          </div>
          <button
            id="logout-button"
            className="sidebar-logout-button"
            onClick={handleLogout}
            title="Log out"
          >
            <LogOut size={16} />
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
                <div className="sidebar-project-item-info">
                  <span className="sidebar-project-title">{project.title}</span>
                  <span className="sidebar-project-date">
                    {formatProjectDate(project.created_at)}
                  </span>
                </div>
                <button
                  className="sidebar-delete-project-button"
                  onClick={(event) => deleteProject(event, project.id)}
                  title="Delete project"
                >
                  <Trash2 size={13} />
                </button>
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
              <span className="chat-panel-project-title">{activeProject.title}</span>
            </div>

            {/* Error message */}
            {errorMessage && (
              <div className="chat-error-banner">{errorMessage}</div>
            )}

            {/* Chat messages */}
            <div className="chat-messages-area">
              {chatMessages.length === 0 ? (
                <div className="chat-empty-state">
                  <div className="chat-empty-state-icon">💬</div>
                  <h2 className="chat-empty-state-title">Start building!</h2>
                  <p className="chat-empty-state-description">
                    Describe the website you want to build below.
                    <br />
                    The AI will generate it for you instantly.
                  </p>
                </div>
              ) : (
                chatMessages.map((message, index) => (
                  <div
                    key={message.id || index}
                    className={`chat-message ${message.role === 'user' ? 'is-user-message' : 'is-ai-message'}`}
                  >
                    {message.role === 'ai' && (
                      <div className="chat-ai-avatar">💖</div>
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
                  <div className="chat-ai-avatar">💖</div>
                  <div className="chat-message-bubble chat-typing-indicator">
                    <Loader2 size={16} className="chat-spinner-icon" />
                    Building your website...
                  </div>
                </div>
              )}

              {/* Invisible anchor to scroll to */}
              <div ref={chatBottomRef} />
            </div>

            {/* Prompt input box */}
            <div className="chat-input-area">
              <form className="chat-input-form" onSubmit={handleSendPrompt}>
                <div className="chat-input-wrapper">
                  <textarea
                    id="prompt-input-textarea"
                    className="chat-prompt-textarea"
                    placeholder="Describe your website or ask for changes..."
                    value={promptInputText}
                    onChange={(e) => setPromptInputText(e.target.value)}
                    onKeyDown={handlePromptKeyDown}
                    rows={1}
                    disabled={isGenerating}
                  />
                  <button
                    id="send-prompt-button"
                    type="submit"
                    className="chat-send-button"
                    disabled={!promptInputText.trim() || isGenerating}
                  >
                    {isGenerating ? (
                      <Loader2 size={18} className="chat-spinner-icon" />
                    ) : (
                      <Send size={18} />
                    )}
                  </button>
                </div>
                <p className="chat-input-hint">
                  Press Enter to send · Shift+Enter for a new line
                </p>
              </form>
            </div>
          </>
        ) : (
          /* ── No project selected — show welcome screen ── */
          <div className="dashboard-welcome-screen">
            <div className="dashboard-welcome-icon">💖</div>
            <h1 className="dashboard-welcome-title">Build something Lovable</h1>
            <p className="dashboard-welcome-subtitle">
              Create a new project or select an existing one from the sidebar to get started.
            </p>
            <button
              id="welcome-create-project-button"
              className="dashboard-welcome-start-button"
              onClick={createNewProject}
            >
              <Plus size={18} />
              Create Your First Project
            </button>
          </div>
        )}
      </main>

      {/* ─── Right Preview Panel ──────────────────────────────────────── */}
      <aside className="dashboard-preview-panel">
        {/* Tab switcher: Preview / Code */}
        <div className="preview-panel-tabs">
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

        {/* Panel content */}
        <div className="preview-panel-content">
          {generatedWebsiteCode ? (
            rightPanelTab === 'preview' ? (
              /* Live preview inside a sandboxed iframe */
              <iframe
                id="website-preview-iframe"
                className="website-preview-iframe"
                srcDoc={generatedWebsiteCode}
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

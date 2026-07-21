import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { authAPI, projectsAPI, aiAPI, WS_BASE_URL } from '../api';
import { Loader2, Globe, Monitor, Smartphone, Paperclip, X, PanelLeftOpen, Code2, Eye, CheckCircle2, FileCode, ImagePlus } from 'lucide-react';
import { SidebarProvider, useSidebar } from '../context/SidebarContext';
import { ProjectSidebar } from '../components/Sidebar/ProjectSidebar';
import { DiscoverySummary, DesignSelectionCards, DesignCustomization, ProjectReview, GenerationProgress } from '../components/AI/WorkflowComponents';
import './Dashboard.css';
import Prism from 'prismjs';
import 'prismjs/themes/prism-tomorrow.css';

function DashboardContent({ onLogout }) {
  const navigate = useNavigate();
  const { projectId } = useParams();
  const { isMobile, openMobile } = useSidebar();

  const [currentUser, setCurrentUser] = useState(null);
  const [allProjects, setAllProjects] = useState([]);
  const [activeProject, setActiveProject] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [generatedWebsiteCode, setGeneratedWebsiteCode] = useState('');
  const [previewState, setPreviewState] = useState('EMPTY');
  const [promptInputText, setPromptInputText] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [isWaiting, setIsWaiting] = useState(false); // lightweight waiting for ANY response
  const [streamingText, setStreamingText] = useState('');
  const [streamingCode, setStreamingCode] = useState('');
  const [rightPanelTab, setRightPanelTab] = useState('preview');
  const [viewportMode, setViewportMode] = useState('desktop');
  const [buildMode, setBuildMode] = useState('fast');
  const [isDeploying, setIsDeploying] = useState(false);
  const [deployedUrl, setDeployedUrl] = useState('');
  const [isLoadingProjects, setIsLoadingProjects] = useState(true);
  const [errorMessage, setErrorMessage] = useState('');
  const [generationEvents, setGenerationEvents] = useState([]);
  const [generationStartTime, setGenerationStartTime] = useState(null);
  const [generationElapsed, setGenerationElapsed] = useState(0);
  
  const [renamingProjectId, setRenamingProjectId] = useState(null);
  const [renameInputValue, setRenameInputValue] = useState('');
  // Code Explorer
  const [codeEditorTab, setCodeEditorTab] = useState('preview'); // 'preview' | 'code'
  // Image attachments
  const [attachedImages, setAttachedImages] = useState([]); // [{name, dataUrl, type}]
  // File manifest from generation (path -> content)
  const [fileManifest, setFileManifest] = useState({});
  const [selectedFile, setSelectedFile] = useState('index.html');

  const chatBottomRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    loadCurrentUser();
    loadAllProjects();
  }, []);

  useEffect(() => {
    if (streamingCode) {
      const timer = setTimeout(() => {
        setGeneratedWebsiteCode(streamingCode);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [streamingCode]);

  useEffect(() => {
    if (isGenerating) {
      setGenerationStartTime(Date.now());
      setGenerationElapsed(0);
      const interval = setInterval(() => {
        setGenerationElapsed(prev => prev + 1);
      }, 1000);
      return () => clearInterval(interval);
    } else {
      setGenerationStartTime(null);
      setGenerationElapsed(0);
    }
  }, [isGenerating]);

  useEffect(() => {
    if (projectId) {
      openProject(projectId);
    } else {
      setActiveProject(null);
      setChatMessages([]);
      setGeneratedWebsiteCode('');
      setPreviewState('EMPTY');
      setDeployedUrl('');
    }
  }, [projectId]);

  useEffect(() => {
    scrollChatToBottom();
  }, [chatMessages, isGenerating]);

  const loadCurrentUser = async () => {
    try {
      const userData = await authAPI.getCurrentUser();
      setCurrentUser(userData);
    } catch (error) {
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

  useEffect(() => {
    if (codeEditorTab === 'code' && generatedWebsiteCode) {
      setTimeout(() => Prism.highlightAll(), 0);
    }
  }, [codeEditorTab, generatedWebsiteCode]);

  const openProject = async (id) => {
    // Immediately wipe previous project state so old data never bleeds into new project
    setActiveProject(null);
    setChatMessages([]);
    setGeneratedWebsiteCode('');
    setPreviewState('EMPTY');
    setStreamingCode('');
    setStreamingText('');
    setGenerationEvents([]);
    setErrorMessage('');
    setIsGenerating(false);
    setFileManifest({});
    setSelectedFile('index.html');
    setDeployedUrl('');

    try {
      const projectWithHistory = await projectsAPI.getProjectWithChatHistory(id);
      setActiveProject(projectWithHistory);
      setChatMessages(projectWithHistory.chat_messages || []);

      // Restore persisted deployed_url
      if (projectWithHistory.deployed_url) {
        setDeployedUrl(projectWithHistory.deployed_url);
      }

      // Restore website from file_manifest (index.html is the entry point)
      const persistedManifest = projectWithHistory.file_manifest || {};
      const persistedHtml = persistedManifest['index.html'];

      if (persistedHtml) {
        setGeneratedWebsiteCode(persistedHtml);
        setPreviewState('RENDERING');
        setRightPanelTab('preview');
        setFileManifest(persistedManifest);
        setSelectedFile('index.html');
      } else {
        // Fallback: last chat message with generated_code (legacy projects)
        const lastAiWithCode = [...(projectWithHistory.chat_messages || [])]
          .reverse()
          .find(m => m.role === 'ai' && m.generated_code);
        if (lastAiWithCode) {
          setGeneratedWebsiteCode(lastAiWithCode.generated_code);
          setPreviewState('RENDERING');
        } else {
          setGeneratedWebsiteCode('');
          setPreviewState('EMPTY');
        }
      }

      // ── Auto-connect WS to receive greeting for brand-new projects ──
      if (projectWithHistory.workflow_state === 'GREETING') {
        const token = localStorage.getItem('auth_token');
        if (token) {
          const greetWs = new WebSocket(`${WS_BASE_URL}/ai/ws/${id}?token=${token}`);
          greetWs.onmessage = (ev) => {
            const msg = JSON.parse(ev.data);
            if (msg.type === 'completed') {
              setChatMessages(prev => [
                ...prev,
                {
                  id: msg.ai_message_id || `greeting-${Date.now()}`,
                  role: 'ai',
                  message_text: msg.response_text,
                  interaction_type: msg.interaction_type,
                  options: msg.options || [],
                  extra_data: msg.extra_data || {},
                },
              ]);
              greetWs.close();
            }
          };
          greetWs.onerror = () => greetWs.close();
        }
      }
    } catch (error) {
      setErrorMessage('Failed to load project.');
      navigate('/dashboard');
    }
  };

  // clearPreview only hides the panel — NEVER deletes the generated code
  const clearPreview = () => {
    setPreviewState('EMPTY');
    // generatedWebsiteCode is intentionally preserved so reopening the panel restores it
  };

  const createNewProject = async () => {
    try {
      // Wipe all state before creating so no old project data bleeds through
      setActiveProject(null);
      setChatMessages([]);
      setGeneratedWebsiteCode('');
      setPreviewState('EMPTY');
      setStreamingCode('');
      setGenerationEvents([]);
      setErrorMessage('');
      setIsGenerating(false);

      const newProjectTitle = `Project ${allProjects.length + 1}`;
      const createdProject = await projectsAPI.createProject(newProjectTitle);
      setAllProjects((previousProjects) => [createdProject, ...previousProjects]);
      navigate(`/dashboard/project/${createdProject.id}`);
    } catch (error) {
      setErrorMessage('Failed to create a new project.');
    }
  };

  const deleteProject = async (event, projectIdToDelete) => {
    event.stopPropagation();
    try {
      await projectsAPI.deleteProject(projectIdToDelete);
      setAllProjects((previousProjects) =>
        previousProjects.filter((project) => project.id !== projectIdToDelete)
      );
      if (String(projectId) === String(projectIdToDelete)) {
        navigate('/dashboard');
      }
    } catch (error) {
      setErrorMessage('Failed to delete the project.');
    }
  };

  const startRenaming = (event, project) => {
    event.stopPropagation();
    setRenamingProjectId(project.id);
    setRenameInputValue(project.title);
  };

  const cancelRenaming = (event) => {
    if (event) event.stopPropagation();
    setRenamingProjectId(null);
    setRenameInputValue('');
  };

  const submitRename = async (event, id) => {
    if (event) event.stopPropagation();
    const trimmedName = renameInputValue.trim();
    if (!trimmedName) { cancelRenaming(null); return; }
    try {
      await projectsAPI.updateProject(id, trimmedName);
      setAllProjects((prev) => prev.map((p) => p.id === id ? { ...p, title: trimmedName } : p));
      if (activeProject?.id === id) setActiveProject((prev) => ({ ...prev, title: trimmedName }));
    } catch (error) {
      setErrorMessage('Failed to rename the project.');
    } finally {
      setRenamingProjectId(null);
    }
  };

  // ── Image attachment handlers ──────────────────────────────
  const handleImageSelect = (e) => {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    files.forEach(file => {
      if (!file.type.startsWith('image/')) return;
      const reader = new FileReader();
      reader.onload = (ev) => {
        setAttachedImages(prev => [
          ...prev,
          { name: file.name, dataUrl: ev.target.result, type: file.type }
        ]);
      };
      reader.readAsDataURL(file);
    });
    // Reset input so same file can be re-selected
    e.target.value = '';
  };

  const removeImage = (index) => {
    setAttachedImages(prev => prev.filter((_, i) => i !== index));
  };

  const handleDeploy = async () => {

    if (!activeProject || isDeploying || !generatedWebsiteCode) return;
    setIsDeploying(true);
    setErrorMessage('');
    try {
      const result = await projectsAPI.deployProject(activeProject.id);
      setDeployedUrl(result.url);
      window.open(result.url, '_blank', 'noopener,noreferrer');
    } catch (error) {
      const detail = error.response?.data?.detail || error.message || 'Deployment failed.';
      setErrorMessage(`Deploy failed: ${detail}`);
    } finally {
      setIsDeploying(false);
    }
  };

  const handleSendPrompt = async (event) => {

    event.preventDefault();
    if (!promptInputText.trim() || isGenerating) return;

    let targetProject = activeProject;
    
    if (!targetProject) {
      try {
        const newProjectTitle = `Project ${allProjects.length + 1}`;
        targetProject = await projectsAPI.createProject(newProjectTitle);
        setAllProjects((previousProjects) => [targetProject, ...previousProjects]);
        navigate(`/dashboard/project/${targetProject.id}`, { replace: true });
        setActiveProject(targetProject);
      } catch (error) {
        setErrorMessage('Failed to create a new project.');
        return;
      }
    }

    const userPromptText = promptInputText;
    const imagesToSend = [...attachedImages]; // snapshot before clearing
    setPromptInputText('');
    setAttachedImages([]);
    // Reset textarea height after clearing
    const ta = document.getElementById('prompt-input-textarea');
    if (ta) { ta.style.height = 'auto'; }
    setIsWaiting(true);
    setStreamingText('');
    setStreamingCode('');
    setErrorMessage('');
    // Do NOT set isGenerating=true or previewState='LOADING' yet —
    // we only do that when the server replies with GENERATING type.

    const optimisticUserMessage = {
      id: `temp-${Date.now()}`,
      role: 'user',
      message_text: userPromptText,
      generated_code: null,
      images: imagesToSend.map(img => img.dataUrl),
    };
    setChatMessages((previousMessages) => [...previousMessages, optimisticUserMessage]);

    const token = localStorage.getItem('auth_token');
    if (!token) {
      setIsWaiting(false);
      setErrorMessage('You must be logged in to generate a website.');
      setIsGenerating(false);
      return;
    }

    if (buildMode === 'deep') {
      try {
        const formattedImages = imagesToSend.map(img => ({ name: img.name, dataUrl: img.dataUrl, type: img.type }));
        const data = await aiAPI.deepBuildWebsite(targetProject.id, userPromptText, formattedImages);
        
        setChatMessages((prev) =>
          prev.map((msg) =>
            msg.id === optimisticUserMessage.id ? { ...msg, id: data.user_message_id } : msg
          )
        );
        
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
        setPreviewState('RENDERING');
        setRightPanelTab('preview');
      } catch (error) {
        console.error('[Deep Build Error]', error);
        const detail = error.response?.data?.detail || error.message || 'Unknown error';
        const status = error.response?.status ? ` (HTTP ${error.response.status})` : '';
        setErrorMessage(`Deep Build failed${status}: ${detail}`);
        setChatMessages((prev) => prev.filter((msg) => msg.id !== optimisticUserMessage.id));
        setPreviewState('ERROR');
      } finally {
        setIsGenerating(false);
      }
      return;
    }

    const wsUrl = `${WS_BASE_URL}/ai/ws/${targetProject.id}?token=${token}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      ws.send(JSON.stringify({ 
        user_prompt: userPromptText,
        current_code: generatedWebsiteCode,
        images: imagesToSend.map(img => ({ name: img.name, dataUrl: img.dataUrl, type: img.type }))
      }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === 'user_message') {
        setChatMessages((prev) =>
          prev.map((msg) =>
            msg.id === optimisticUserMessage.id
              ? { ...msg, id: data.message_id }
              : msg
          )
        );
      } else if (data.type === 'pipeline_event') {
        if (data.data.type === 'code_chunk') {
          setStreamingCode((prev) => prev + data.data.text);
          if (previewState !== 'RENDERING') {
              setPreviewState('RENDERING');
              setRightPanelTab('preview');
          }
        } else if (data.data.type === 'generation_complete') {
          const finalHtml = data.data.generated_code;
          const manifest = data.data.file_manifest || {};

          if (!finalHtml || finalHtml.trim().length < 100) {
            // Empty or near-empty HTML — treat as failure
            setErrorMessage('Website generation produced no content. Please try again with a clearer description.');
            setIsGenerating(false);
            setPreviewState('ERROR');
            setStreamingCode('');
            ws.close();
            break;
          }

          setGeneratedWebsiteCode(finalHtml);
          setPreviewState('RENDERING');
          setRightPanelTab('preview');
          setIsGenerating(false);
          setStreamingCode('');

          // Store the file manifest so Code Explorer can show all files
          if (finalHtml) {
            setFileManifest({
              'index.html': finalHtml,
              ...manifest,
            });
            setSelectedFile('index.html');
          }

          // Build a blob URL so we can open the website in a new tab even if not deployed
          let previewBlobUrl = null;
          try {
            const blob = new Blob([finalHtml], { type: 'text/html' });
            previewBlobUrl = URL.createObjectURL(blob);
          } catch (_) {}

          // Add the "Website Ready" card to the chat
          setChatMessages((prev) => [
            ...prev.filter(m => !(m.role === 'ai' && m.interaction_type === 'GENERATING_PLACEHOLDER')),
            {
              id: `gen-complete-${Date.now()}`,
              role: 'ai',
              message_text: '✅ Your website is ready!',
              interaction_type: 'WEBSITE_READY',
              extra_data: { previewBlobUrl, deployedUrl },
            },
          ]);
          ws.close();

        } else if (data.data.type === 'generation_failed' || data.data.error) {
          const errMsg = data.data.error || 'Website generation failed. Please try again.';
          setErrorMessage(`Generation failed: ${errMsg}`);
          setIsGenerating(false);
          setPreviewState('ERROR');
          setStreamingCode('');
          ws.close();
        } else {
          setGenerationEvents((prev) => {
            // If the event already exists, update it, otherwise add it
            const existingIndex = prev.findIndex(e => e.stage === data.data.stage);
            if (existingIndex >= 0) {
              const newEvents = [...prev];
              newEvents[existingIndex] = data.data;
              return newEvents;
            }
            return [...prev, data.data];
          });
        }
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
            interaction_type: data.interaction_type,
            options: data.options,
            extra_data: data.extra_data
          },
        ]);
        if (data.generated_code) {
            setGeneratedWebsiteCode(data.generated_code);
            setPreviewState('RENDERING');
            setRightPanelTab('preview');
        }
        
        if (data.interaction_type !== 'GENERATING') {
            setIsWaiting(false);
            setIsGenerating(false);
            ws.close();
        } else {
            // Server says generation is starting — NOW activate loading state
            setIsWaiting(false);
            setIsGenerating(true);
            setPreviewState('LOADING');
        }
        setStreamingText('');
        setStreamingCode('');
      } else if (data.type === 'generation_failed' || data.type === 'generation_timeout') {
        setErrorMessage(data.error || 'The generation process failed.');
        setIsWaiting(false);
        setIsGenerating(false);
        setPreviewState('ERROR');
        setStreamingText('');
        ws.close();
      }
    };

    ws.onerror = (error) => {
      console.error('[WebSocket Error]', error);
      setErrorMessage('WebSocket connection failed. Make sure the backend server is running on port 8000.');
      setIsWaiting(false);
      setIsGenerating(false);
      setPreviewState((prev) => prev === 'LOADING' ? 'EMPTY' : prev);
      setStreamingText('');
      setChatMessages((prev) => prev.filter((msg) => msg.id !== optimisticUserMessage.id));
    };

    ws.onclose = () => {
      setIsWaiting(false);
      if (isGenerating) {
        setIsGenerating(false);
      }
    };
  };

  const handlePromptKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendPrompt(event);
    }
  };

  const handleTextareaInput = (e) => {
    setPromptInputText(e.target.value);
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 120) + 'px';
  };

  const handleLogout = () => {
    authAPI.logout();
    onLogout();
    navigate('/');
  };


  return (
    <div className="dashboard-container">
      <ProjectSidebar 
        allProjects={allProjects}
        isLoadingProjects={isLoadingProjects}
        createNewProject={createNewProject}
        deleteProject={deleteProject}
        submitRename={submitRename}
        handleLogout={handleLogout}
        renamingProjectId={renamingProjectId}
        renameInputValue={renameInputValue}
        setRenameInputValue={setRenameInputValue}
        startRenaming={startRenaming}
        cancelRenaming={cancelRenaming}
      />

      <div className="dashboard-main-content">
        {isMobile && (
          <button className="mobile-sidebar-open-btn" onClick={openMobile}>
            <PanelLeftOpen size={20} />
          </button>
        )}

        {projectId ? (
          <>
            <aside className="dashboard-chat-panel">
              <div className="chat-panel-header">
                <span className="chat-panel-project-title">AI Design Assistant</span>
                <div className="chat-panel-header-actions">
                  <span style={{ fontSize: '12px', opacity: 0.5, cursor: 'pointer' }}>⋯</span>
                </div>
              </div>

              {errorMessage && (
                <div className="chat-error-banner">{errorMessage}</div>
              )}

              <div className="chat-messages-area">
                {chatMessages.map((message, index) => (
                  <div
                    key={message.id || index}
                    className={`chat-message ${message.role === 'user' ? 'is-user-message' : 'is-ai-message'}`}
                  >
                    <div className="chat-message-avatar">
                      {message.role === 'user' ? (currentUser?.name?.charAt(0)?.toUpperCase() || 'U') : '✦'}
                    </div>
                    <div className="chat-message-content">
                      <div className="chat-message-meta">
                        <span className="chat-message-sender">{message.role === 'user' ? 'User' : 'Assistant'}</span>
                        {message.role === 'user' && (
                          <span className="chat-message-time">
                            {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        )}
                      </div>
                    <div className="chat-message-bubble">
                      {/* ── QUESTION with chips (single/multi page, yes/no, etc.) ── */}
                      {(message.interaction_type === 'QUESTION' || message.interaction_type === 'GREETING') && (message.options?.length > 0 || message.extra_data?.chips?.length > 0) ? (
                        <div>
                          <div style={{ whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{message.message_text}</div>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', marginTop: '12px' }}>
                            {(message.options || message.extra_data?.chips || []).map((chip, ci) => (
                              <button
                                key={ci}
                                onClick={() => {
                                  setPromptInputText(chip);
                                  const fakeEvent = { preventDefault: () => {} };
                                  setTimeout(() => handleSendPrompt(fakeEvent), 0);
                                }}
                                style={{
                                  padding: '7px 16px', borderRadius: '20px', fontSize: '0.82rem',
                                  background: 'rgba(99,102,241,0.18)', border: '1px solid rgba(99,102,241,0.45)',
                                  color: '#c7d2fe', cursor: 'pointer', fontWeight: 500,
                                  transition: 'all 0.15s',
                                }}
                              >{chip}</button>
                            ))}
                          </div>
                        </div>
                      ) : message.interaction_type === 'CONFIRMATION' ? (
                        <DiscoverySummary 
                          text={message.message_text} 
                          onConfirm={() => {
                            setPromptInputText('Yes, looks good!');
                            const fakeEvent = { preventDefault: () => {} };
                            setTimeout(() => handleSendPrompt(fakeEvent), 0);
                          }} 
                        />
                      ) : message.interaction_type === 'DESIGN_SELECTION' ? (
                        <DesignSelectionCards 
                          text={message.message_text}
                          recommendations={message.extra_data?.recommendations || []}
                          onSelect={(id) => {
                            setPromptInputText(`[sys:select_design] ${id}`);
                            const fakeEvent = { preventDefault: () => {} };
                            setTimeout(() => handleSendPrompt(fakeEvent), 0);
                          }}
                        />
                      ) : message.interaction_type === 'DESIGN_CUSTOMIZATION' ? (
                        <DesignCustomization 
                          text={message.message_text}
                          chips={message.extra_data?.chips || []}
                          onSelect={(chip) => {
                            setPromptInputText(chip);
                            const fakeEvent = { preventDefault: () => {} };
                            setTimeout(() => handleSendPrompt(fakeEvent), 0);
                          }}
                          onSkip={() => {
                            setPromptInputText('Skip refinements');
                            const fakeEvent = { preventDefault: () => {} };
                            setTimeout(() => handleSendPrompt(fakeEvent), 0);
                          }}
                        />
                      ) : message.interaction_type === 'REVIEW' ? (
                        <ProjectReview 
                          text={message.message_text}
                          onConfirm={() => {
                            setPromptInputText('[sys:confirm_build]');
                            const fakeEvent = { preventDefault: () => {} };
                            setTimeout(() => handleSendPrompt(fakeEvent), 0);
                          }}
                        />
                      ) : message.interaction_type === 'WEBSITE_READY' ? (
                        <div style={{
                          background: 'linear-gradient(135deg, rgba(99,102,241,0.15) 0%, rgba(168,85,247,0.15) 100%)',
                          border: '1px solid rgba(99,102,241,0.4)',
                          borderRadius: '12px',
                          padding: '16px',
                          marginTop: '4px',
                        }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '12px' }}>
                            <span style={{ fontSize: '20px' }}>🚀</span>
                            <strong style={{ fontSize: '0.95rem' }}>Your website is ready!</strong>
                          </div>
                          <p style={{ fontSize: '0.82rem', opacity: 0.75, marginBottom: '14px', lineHeight: 1.5 }}>
                            The preview is live in the right panel. You can also open it directly in your browser.
                          </p>
                          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                            <button
                              onClick={() => {
                                setRightPanelTab('preview');
                                setCodeEditorTab('preview');
                              }}
                              style={{
                                padding: '7px 14px', borderRadius: '8px', fontSize: '0.8rem',
                                background: 'rgba(99,102,241,0.25)', border: '1px solid rgba(99,102,241,0.5)',
                                color: '#fff', cursor: 'pointer', fontWeight: 600,
                              }}
                            >
                              👁 View Preview
                            </button>
                            {(message.extra_data?.deployedUrl || deployedUrl) ? (
                              <a
                                href={message.extra_data?.deployedUrl || deployedUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{
                                  padding: '7px 14px', borderRadius: '8px', fontSize: '0.8rem',
                                  background: 'linear-gradient(135deg, #6366f1, #a855f7)',
                                  border: 'none', color: '#fff', cursor: 'pointer',
                                  fontWeight: 600, textDecoration: 'none', display: 'inline-flex',
                                  alignItems: 'center', gap: '5px',
                                }}
                              >
                                🌐 Visit Live Website ↗
                              </a>
                            ) : message.extra_data?.previewBlobUrl ? (
                              <a
                                href={message.extra_data.previewBlobUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                style={{
                                  padding: '7px 14px', borderRadius: '8px', fontSize: '0.8rem',
                                  background: 'linear-gradient(135deg, #6366f1, #a855f7)',
                                  border: 'none', color: '#fff', cursor: 'pointer',
                                  fontWeight: 600, textDecoration: 'none', display: 'inline-flex',
                                  alignItems: 'center', gap: '5px',
                                }}
                              >
                                🔗 Open in New Tab ↗
                              </a>
                            ) : null}
                            <button
                              onClick={() => {
                                setCodeEditorTab('code');
                                setRightPanelTab('code');
                              }}
                              style={{
                                padding: '7px 14px', borderRadius: '8px', fontSize: '0.8rem',
                                background: 'rgba(255,255,255,0.07)', border: '1px solid rgba(255,255,255,0.15)',
                                color: '#ccc', cursor: 'pointer',
                              }}
                            >
                              &lt;/&gt; View Code
                            </button>
                          </div>
                          {(message.extra_data?.deployedUrl || deployedUrl) && (
                            <div style={{
                              marginTop: '10px', padding: '6px 10px',
                              background: 'rgba(0,0,0,0.25)', borderRadius: '6px',
                              fontSize: '0.75rem', fontFamily: 'monospace',
                              color: '#a5b4fc', wordBreak: 'break-all',
                            }}>
                              {message.extra_data?.deployedUrl || deployedUrl}
                            </div>
                          )}
                        </div>
                      ) : (
                        message.message_text
                      )}

                      {/* Show images attached to this message */}
                      {message.images && message.images.length > 0 && (
                        <div className="chat-message-images">
                          {message.images.map((src, i) => (
                            <img
                              key={i}
                              src={src}
                              alt={`attached-${i}`}
                              className="chat-message-image"
                              onClick={() => window.open(src, '_blank')}
                            />
                          ))}
                        </div>
                      )}
                    </div>
                    </div>
                  </div>
                ))}

                {(isWaiting || isGenerating) && (
                  <div className="chat-message is-ai-message">
                    <div className="chat-message-avatar" aria-hidden="true">✦</div>
                    <div className="chat-message-content">
                      <div className="chat-message-meta">
                        <span className="chat-message-sender">Assistant</span>
                        {generationElapsed > 0 && (
                          <span className="chat-message-time" style={{ marginLeft: '8px', fontFamily: 'monospace', fontSize: '0.75rem' }}>
                            ⏱ {Math.floor(generationElapsed / 60) > 0 ? `${Math.floor(generationElapsed / 60)}m ` : ''}{generationElapsed % 60}s
                          </span>
                        )}
                      </div>
                      <div className="chat-message-bubble" style={{ padding: '10px 14px' }}>
                        {/* Real-time generation progress in chat */}
                        {generationEvents.length > 0 ? (
                          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                            {generationEvents.map((ev, i) => (
                              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem' }}>
                                {ev.status === 'completed' ? (
                                  <span style={{ color: '#4ade80' }}>✓</span>
                                ) : ev.status === 'in_progress' ? (
                                  <Loader2 size={11} className="chat-spinner-icon" style={{ color: '#818cf8' }} />
                                ) : (
                                  <span style={{ opacity: 0.3 }}>○</span>
                                )}
                                <span style={{ opacity: ev.status === 'completed' ? 0.6 : 1 }}>{ev.step}</span>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.82rem' }}>
                            <Loader2 size={12} className="chat-spinner-icon" />
                            {streamingText ? streamingText
                              : streamingCode ? `✍ Writing code... (${streamingCode.length} chars)`
                              : isGenerating ? 'Generating your website...'
                              : 'Thinking...'}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
                <div ref={chatBottomRef} />
              </div>

              <div className="chat-input-area">
                <form className="chat-input-form" onSubmit={handleSendPrompt}>
                  <div className="chat-input-card">
                    {/* Image previews strip */}
                    {attachedImages.length > 0 && (
                      <div className="image-preview-strip">
                        {attachedImages.map((img, i) => (
                          <div key={i} className="image-preview-thumb">
                            <img src={img.dataUrl} alt={img.name} />
                            <button
                              type="button"
                              className="image-preview-remove"
                              onClick={() => removeImage(i)}
                              title="Remove image"
                            >
                              <X size={10} />
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                    <textarea
                      id="prompt-input-textarea"
                      className="chat-prompt-textarea"
                      placeholder={attachedImages.length > 0 ? "Describe how to use these images in your website..." : "Type your design request..."}
                      value={promptInputText}
                      onChange={handleTextareaInput}
                      onKeyDown={handlePromptKeyDown}
                      rows={1}
                      disabled={isWaiting || isGenerating}
                    />
                    <div className="chat-input-toolbar">
                      <div className="chat-toolbar-left">
                        {/* Hidden file input */}
                        <input
                          ref={fileInputRef}
                          type="file"
                          accept="image/*"
                          multiple
                          style={{ display: 'none' }}
                          onChange={handleImageSelect}
                        />
                        <button
                          type="button"
                          className={`chat-toolbar-btn ${attachedImages.length > 0 ? 'active' : ''}`}
                          title="Attach images"
                          disabled={isGenerating}
                          onClick={() => fileInputRef.current?.click()}
                        >
                          <ImagePlus size={12} />
                          {attachedImages.length > 0 && (
                            <span className="image-count-badge">{attachedImages.length}</span>
                          )}
                        </button>
                      </div>
                      <div className="chat-toolbar-right">
                        <button
                          id="send-prompt-button"
                          type="submit"
                          className="chat-send-btn"
                          disabled={(!promptInputText.trim() && attachedImages.length === 0) || isWaiting || isGenerating}
                        >
                          Send
                        </button>
                      </div>
                    </div>
                  </div>
                </form>
              </div>
            </aside>

            <main className="dashboard-preview-panel">
              {/* ── Toolbar ───────────────────────────────────────── */}
              <div className="preview-panel-tabs">
                <div className="preview-toolbar-left">
                  <button className="preview-tab-button" title="Close" onClick={clearPreview}>
                    <X size={12} />
                  </button>
                  {/* Preview / Code tab switcher */}
                  <div className="code-tab-switcher">
                    <button
                      className={`code-tab-btn ${codeEditorTab === 'preview' ? 'active' : ''}`}
                      onClick={() => setCodeEditorTab('preview')}
                    >
                      <Eye size={12} /> Preview
                    </button>
                    <button
                      className={`code-tab-btn ${codeEditorTab === 'code' ? 'active' : ''}`}
                      onClick={() => setCodeEditorTab('code')}
                    >
                      <Code2 size={12} /> Code
                    </button>
                  </div>
                </div>
                <div className="preview-toolbar-center">
                  {codeEditorTab === 'preview' && (
                    <div className="viewport-toggle-group">
                      <button
                        className={`viewport-btn ${viewportMode === 'desktop' ? 'active' : ''}`}
                        onClick={() => setViewportMode('desktop')}
                        aria-label="Desktop preview"
                      >
                        <Monitor size={12} />
                      </button>
                      <button
                        className={`viewport-btn ${viewportMode === 'mobile' ? 'active' : ''}`}
                        onClick={() => setViewportMode('mobile')}
                        aria-label="Mobile preview"
                      >
                        <Smartphone size={12} />
                      </button>
                    </div>
                  )}
                </div>
                <div className="preview-toolbar-right">
                  {previewState === 'RENDERING' && generatedWebsiteCode && (
                    <span className="generation-success-badge">
                      <CheckCircle2 size={12} /> Ready
                    </span>
                  )}
                  {deployedUrl && (
                    <a
                      href={deployedUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="generation-success-badge"
                      style={{ textDecoration: 'none', cursor: 'pointer' }}
                      title={deployedUrl}
                    >
                      <CheckCircle2 size={12} /> Live
                    </a>
                  )}
                  <button
                    className="preview-publish-btn"
                    onClick={handleDeploy}
                    disabled={isDeploying || !generatedWebsiteCode}
                    title={isDeploying ? 'Deploying to Vercel, please wait...' : 'Deploy to Vercel'}
                  >
                    {isDeploying ? (
                      <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                        <Loader2 size={12} className="spin-icon" />
                        Deploying...
                      </span>
                    ) : deployedUrl ? 'Redeploy' : 'Publish'}
                  </button>
                </div>
              </div>

              {/* ── Panel Content ─────────────────────────────────── */}
              <div className="preview-panel-content">

                {/* ── PREVIEW TAB ─────────────────────────────────── */}
                {codeEditorTab === 'preview' && (
                  <div className={`preview-canvas-wrapper ${viewportMode}`}>
                    {previewState === 'EMPTY' && (
                      <div className="empty-preview-state" style={{ height: '100%' }}>
                        <Globe size={48} style={{ marginBottom: '1rem', opacity: 0.2 }} />
                        <h3>No Website Generated Yet</h3>
                        <p style={{ fontSize: '0.9rem', maxWidth: '300px', textAlign: 'center', marginTop: '0.5rem' }}>
                          Start a conversation to generate a website.
                        </p>
                      </div>
                    )}
                    {previewState === 'LOADING' && (
                      <GenerationProgress events={generationEvents} />
                    )}
                    {previewState === 'ERROR' && (
                      <div className="empty-preview-state" style={{ height: '100%', color: '#ef4444' }}>
                        <h3>Generation Failed</h3>
                        <p style={{ fontSize: '0.9rem', maxWidth: '300px', textAlign: 'center', marginTop: '0.5rem' }}>
                          There was an error generating your website. Please try again.
                        </p>
                      </div>
                    )}
                    {(previewState === 'RENDERING' || (previewState === 'LOADING' && streamingCode)) && generatedWebsiteCode && (
                      <iframe
                        id="website-preview-iframe"
                        className="website-preview-iframe"
                        srcDoc={(() => {
                          const cleanHtml = generatedWebsiteCode.replace(/^```(html)?\s*/i, '').replace(/```\s*$/i, '');
                          return cleanHtml;
                        })()}
                        title="Generated Website Preview"
                        sandbox="allow-scripts allow-same-origin"
                      />
                    )}
                  </div>
                )}

                {/* ── CODE TAB ────────────────────────────────────── */}
                {codeEditorTab === 'code' && (() => {
                  // Group files by top-level directory
                  const allFiles = Object.keys(fileManifest);
                  const groups = {};
                  allFiles.forEach(path => {
                    const parts = path.split('/');
                    const dir = parts.length > 1 ? parts.slice(0, -1).join('/') : '';
                    if (!groups[dir]) groups[dir] = [];
                    groups[dir].push(path);
                  });

                  const getFileIcon = (path) => {
                    if (path.endsWith('.css'))  return '🎨';
                    if (path.endsWith('.js'))   return '⚡';
                    if (path.endsWith('.sql'))  return '🗄️';
                    if (path.endsWith('.md'))   return '📝';
                    if (path.endsWith('.html')) return '🌐';
                    return '📄';
                  };

                  const getLang = (path) => {
                    if (path.endsWith('.css'))  return 'language-css';
                    if (path.endsWith('.js'))   return 'language-javascript';
                    if (path.endsWith('.sql'))  return 'language-sql';
                    if (path.endsWith('.md'))   return 'language-markdown';
                    return 'language-html';
                  };

                  const selectedContent = fileManifest[selectedFile] || '';

                  return (
                    <div className="code-explorer-layout">
                      {/* ── File tree sidebar ── */}
                      <div className="code-file-tree">
                        <div className="code-file-tree-header">FILES</div>
                        <div className="code-file-tree-body">
                          {allFiles.length === 0 ? (
                            <div style={{ padding: '12px', opacity: 0.4, fontSize: '0.8rem' }}>
                              Generate a website to see files
                            </div>
                          ) : (
                            Object.entries(groups)
                              .sort(([a], [b]) => a.localeCompare(b))
                              .map(([dir, paths]) => (
                                <div key={dir} className="code-file-group">
                                  {dir && (
                                    <span className="code-file-group-label">
                                      📁 {dir}
                                    </span>
                                  )}
                                  {paths.sort().map(filePath => {
                                    const name = filePath.split('/').pop();
                                    const content = fileManifest[filePath] || '';
                                    const sizeKb = (content.length / 1024).toFixed(1);
                                    const isActive = selectedFile === filePath;
                                    return (
                                      <div
                                        key={filePath}
                                        className={`code-file-item ${isActive ? 'active' : ''}`}
                                        onClick={() => setSelectedFile(filePath)}
                                        title={filePath}
                                      >
                                        <span style={{ fontSize: '11px' }}>{getFileIcon(filePath)}</span>
                                        <span style={{ flex: 1 }}>{name}</span>
                                        <span className="code-file-size">{sizeKb}kb</span>
                                      </div>
                                    );
                                  })}
                                </div>
                              ))
                          )}
                        </div>
                      </div>

                      {/* ── Code viewer ── */}
                      <div className="code-editor-panel">
                        {selectedContent ? (
                          <>
                            <div className="code-editor-titlebar">
                              <span className="code-editor-filename">
                                {getFileIcon(selectedFile)} {selectedFile}
                              </span>
                              <button
                                className="code-copy-btn"
                                onClick={() => navigator.clipboard.writeText(selectedContent)}
                                title="Copy to clipboard"
                              >
                                Copy
                              </button>
                            </div>
                            <div className="code-editor-content">
                              <pre className="code-pre">
                                <code className={getLang(selectedFile)}>
                                  {selectedContent.trim()}
                                </code>
                              </pre>
                            </div>
                          </>
                        ) : (
                          <div className="empty-preview-state" style={{ height: '100%' }}>
                            <Code2 size={40} style={{ marginBottom: '1rem', opacity: 0.15 }} />
                            <h3 style={{ fontSize: '1rem' }}>No Code Generated Yet</h3>
                            <p style={{ fontSize: '0.85rem', opacity: 0.5, marginTop: '0.5rem' }}>
                              Generate a website to view its source code here.
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })()}



              </div>
            </main>
          </>
        ) : (
          <main className="dashboard-empty-main">
            <div className="empty-main-content">
              <Globe size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
              <h2>Select a project</h2>
              <p style={{ marginTop: '0.5rem', opacity: 0.6 }}>Choose an existing project from the sidebar or create a new one to begin.</p>
            </div>
          </main>
        )}
      </div>
    </div>
  );
}

export default function Dashboard(props) {
  return (
    <SidebarProvider>
      <DashboardContent {...props} />
    </SidebarProvider>
  );
}

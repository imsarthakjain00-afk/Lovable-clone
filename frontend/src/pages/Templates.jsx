import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { templatesAPI, projectsAPI } from '../api';
import { ArrowLeft, Zap } from 'lucide-react';
import './Templates.css';

/**
 * Templates — shows a grid of pre-built website templates.
 * Users can click "Use Template" to create a new project pre-filled with that template's prompt.
 */
function Templates() {
  const navigate = useNavigate();

  // All templates fetched from the backend
  const [allTemplates, setAllTemplates] = useState([]);

  // Whether the templates are still loading
  const [isLoading, setIsLoading] = useState(true);

  // Error message if the fetch fails
  const [errorMessage, setErrorMessage] = useState('');

  // Which template the user just selected (to show a loading state on the button)
  const [selectedTemplateId, setSelectedTemplateId] = useState(null);

  useEffect(() => {
    fetchAllTemplates();
  }, []);

  const fetchAllTemplates = async () => {
    try {
      const templates = await templatesAPI.getAllTemplates();
      setAllTemplates(templates);
    } catch (error) {
      setErrorMessage('Failed to load templates. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  /**
   * When the user picks a template:
   * 1. Create a new project named after the template
   * 2. Navigate to the Dashboard with that project
   *
   * Note: If not logged in, redirect to auth first.
   */
  const handleUseTemplate = async (template) => {
    const authToken = localStorage.getItem('auth_token');
    if (!authToken) {
      navigate('/auth?mode=login');
      return;
    }

    try {
      setSelectedTemplateId(template.id);
      await projectsAPI.createProject(template.name, template.description);
      // Go to dashboard — the user can paste the starter_prompt there
      navigate('/dashboard', { state: { starterPrompt: template.starter_prompt } });
    } catch (error) {
      setErrorMessage('Could not create a project from this template.');
      setSelectedTemplateId(null);
    }
  };

  // Group templates by category for display
  const templateCategories = [...new Set(allTemplates.map((template) => template.category))];

  return (
    <div className="templates-page">
      {/* ─── Top Bar ─────────────────────────────────────────────── */}
      <div className="templates-top-bar">
        <button
          id="templates-back-button"
          className="templates-back-button"
          onClick={() => navigate(-1)}
        >
          <ArrowLeft size={16} />
          Back
        </button>
        <div className="templates-top-bar-logo">
          <span>💖</span>
          <span className="templates-logo-text">Lovable Templates</span>
        </div>
        <button
          id="templates-start-from-scratch-button"
          className="templates-start-fresh-button"
          onClick={() => navigate('/dashboard')}
        >
          Start from Scratch
        </button>
      </div>

      {/* ─── Page Header ─────────────────────────────────────────── */}
      <div className="templates-page-header">
        <h1 className="templates-page-title">Start with a template</h1>
        <p className="templates-page-subtitle">
          Pick a template and customize it with AI prompts. Ship faster.
        </p>
      </div>

      {/* ─── Error Message ────────────────────────────────────────── */}
      {errorMessage && (
        <div className="templates-error-message">{errorMessage}</div>
      )}

      {/* ─── Templates Grid ───────────────────────────────────────── */}
      {isLoading ? (
        <div className="templates-loading-state">Loading templates...</div>
      ) : (
        <div className="templates-grid-container">
          {allTemplates.map((template) => (
            <div
              key={template.id}
              id={`template-card-${template.id}`}
              className="templates-card"
            >
              {/* Template icon / preview */}
              <div className="templates-card-preview">
                <span className="templates-card-emoji">{template.preview_emoji}</span>
              </div>

              {/* Template info */}
              <div className="templates-card-body">
                <span className="templates-card-category">{template.category}</span>
                <h3 className="templates-card-name">{template.name}</h3>
                <p className="templates-card-description">{template.description}</p>

                {/* Starter prompt preview */}
                <div className="templates-card-prompt-preview">
                  <span className="templates-card-prompt-label">AI Prompt</span>
                  <p className="templates-card-prompt-text">{template.starter_prompt}</p>
                </div>

                <button
                  id={`use-template-${template.id}-button`}
                  className="templates-use-button"
                  onClick={() => handleUseTemplate(template)}
                  disabled={selectedTemplateId === template.id}
                >
                  <Zap size={14} />
                  {selectedTemplateId === template.id ? 'Creating project...' : 'Use Template'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default Templates;

import React from 'react';
import ReactMarkdown from 'react-markdown';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';
import './WorkflowComponents.css';

export const DiscoverySummary = ({ text, onConfirm }) => {
  return (
    <div className="workflow-summary-panel">
      <ReactMarkdown>{text}</ReactMarkdown>
      <button className="workflow-primary-btn" onClick={onConfirm}>
        Looks good, build the blueprint!
      </button>
    </div>
  );
};

export const DesignSelectionCards = ({ text, recommendations, onSelect }) => {
  return (
    <div className="workflow-design-selection">
      <p>{text}</p>
      <div className="design-cards-grid">
        {recommendations.map((rec) => (
          <div key={rec.id} className={`design-card ${rec.is_recommended ? 'recommended' : ''}`}>
            {rec.is_recommended && <div className="recommended-badge">⭐ Recommended</div>}
            <img src={rec.preview_url} alt={rec.display_name} className="design-card-preview" />
            <div className="design-card-content">
              <h4>{rec.display_name}</h4>
              <p className="design-match">{rec.match_percentage}% Match</p>
              <p className="design-reason">{rec.reason}</p>
              
              <div className="design-tags">
                <span className="tag category-tag">{rec.category}</span>
                <span className="tag difficulty-tag">{rec.difficulty}</span>
                {rec.tags?.slice(0,2).map(t => <span key={t} className="tag">{t}</span>)}
              </div>
              
              <button className="select-design-btn" onClick={() => onSelect(rec.id)}>
                Choose Design
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export const DesignCustomization = ({ text, chips, onSelect, onSkip }) => {
  return (
    <div className="workflow-customization-panel">
      <p>{text}</p>
      <div className="refinement-chips">
        {chips.map((chip) => (
          <button key={chip} className="chip-btn" onClick={() => onSelect(chip)}>
            {chip}
          </button>
        ))}
      </div>
      <button className="workflow-secondary-btn" onClick={onSkip}>
        Skip Refinements
      </button>
    </div>
  );
};

export const ProjectReview = ({ text, onConfirm }) => {
  return (
    <div className="workflow-review-panel">
      <ReactMarkdown>{text}</ReactMarkdown>
      <button className="workflow-primary-btn generate-btn" onClick={onConfirm}>
        Confirm & Start Generation
      </button>
    </div>
  );
};

export const GenerationProgress = ({ events }) => {
  return (
    <div className="generation-progress-panel">
      <h3>Generating Website...</h3>
      <div className="progress-checklist">
        {events.length === 0 && (
          <div className="progress-item loading">
             <Loader2 size={16} className="spin" />
             <span>Initializing pipeline...</span>
          </div>
        )}
        {events.map((ev, idx) => (
          <div key={idx} className={`progress-item ${ev.status}`}>
            {ev.status === 'in_progress' && <Loader2 size={16} className="spin" />}
            {ev.status === 'completed' && <CheckCircle size={16} className="text-green" />}
            {ev.status === 'error' && <XCircle size={16} className="text-red" />}
            <span>{ev.stage}: {ev.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

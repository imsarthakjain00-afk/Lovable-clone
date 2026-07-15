import React, { useState, useRef, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Plus, Trash2, Pencil, Search, Copy, Archive, PanelLeftClose, PanelLeftOpen, MoreHorizontal } from 'lucide-react';
import { useSidebar } from '../../context/SidebarContext';
import './ProjectSidebar.css';

export function ProjectSidebar({
  allProjects,
  isLoadingProjects,
  createNewProject,
  deleteProject,
  submitRename,
  handleLogout,
  renamingProjectId,
  renameInputValue,
  setRenameInputValue,
  startRenaming,
  cancelRenaming
}) {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const { isExpanded, isMobileOpen, isMobile, toggleSidebar, closeMobile } = useSidebar();
  const [searchQuery, setSearchQuery] = useState('');
  
  const renameInputRef = useRef(null);

  useEffect(() => {
    if (renamingProjectId && renameInputRef.current) {
      renameInputRef.current.focus();
    }
  }, [renamingProjectId]);

  useEffect(() => {
    const handleEsc = (e) => {
      if (e.key === 'Escape' && isMobileOpen) closeMobile();
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, [isMobileOpen, closeMobile]);

  const groupProjects = (projects) => {
    const groups = {
      'Today': [],
      'Yesterday': [],
      'Previous 7 Days': [],
      'Previous 30 Days': [],
      'Older': []
    };

    const now = new Date();
    projects.forEach(p => {
      const date = new Date(p.created_at);
      const diffMs = now - date;
      const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

      if (diffDays === 0) groups['Today'].push(p);
      else if (diffDays === 1) groups['Yesterday'].push(p);
      else if (diffDays <= 7) groups['Previous 7 Days'].push(p);
      else if (diffDays <= 30) groups['Previous 30 Days'].push(p);
      else groups['Older'].push(p);
    });

    return groups;
  };

  const filteredProjects = allProjects.filter(p => p.title?.toLowerCase().includes(searchQuery.toLowerCase()));
  const grouped = groupProjects(filteredProjects);

  const handleRenameKeyDown = (event, id) => {
    if (event.key === 'Enter') submitRename(event, id);
    if (event.key === 'Escape') cancelRenaming(event);
  };

  const handleProjectClick = (id) => {
    navigate(`/dashboard/project/${id}`);
    if (isMobile) closeMobile();
  };

  const sidebarClass = `dashboard-sidebar ${isExpanded ? 'expanded' : 'collapsed'} ${isMobileOpen ? 'mobile-open' : ''}`;

  return (
    <>
      {isMobileOpen && <div className="sidebar-mobile-overlay" onClick={closeMobile} />}

      <aside className={sidebarClass}>
        <div className="sidebar-header-top">
          {isExpanded && <span className="sidebar-logo">Lovable Clone</span>}
          <button className="sidebar-toggle-btn" onClick={toggleSidebar} title="Toggle Sidebar">
            {isExpanded ? <PanelLeftClose size={18} /> : <PanelLeftOpen size={18} />}
          </button>
        </div>

        <div className="sidebar-actions">
          <button className="new-project-btn" onClick={createNewProject}>
             <Plus size={16} />
             {isExpanded && <span>New Project</span>}
          </button>
        </div>

        {isExpanded && (
          <div className="sidebar-search">
            <Search size={14} className="search-icon" />
            <input 
              type="text" 
              placeholder="Search projects..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        )}

        <div className="sidebar-project-list">
          {isLoadingProjects ? (
            <div className="sidebar-loading">{isExpanded ? 'Loading...' : <span className="loader-dot" />}</div>
          ) : (
            Object.entries(grouped).map(([groupName, projects]) => {
              if (projects.length === 0) return null;
              return (
                <div key={groupName} className="project-group">
                  {isExpanded && <div className="project-group-label">{groupName}</div>}
                  {projects.map((project) => {
                    const isActive = String(project.id) === String(projectId);
                    return (
                      <div 
                        key={project.id} 
                        className={`sidebar-project-item ${isActive ? 'active' : ''}`}
                        onClick={() => handleProjectClick(project.id)}
                        title={!isExpanded ? project.title : ''}
                      >
                        {renamingProjectId === project.id ? (
                          <input
                            ref={renameInputRef}
                            type="text"
                            className="rename-input"
                            value={renameInputValue}
                            onChange={(e) => setRenameInputValue(e.target.value)}
                            onBlur={(e) => submitRename(e, project.id)}
                            onKeyDown={(e) => handleRenameKeyDown(e, project.id)}
                            onClick={(e) => e.stopPropagation()}
                          />
                        ) : (
                          <div className="project-item-content">
                            <span className="project-item-title">{isExpanded ? (project.title || 'Untitled Project') : (project.title?.charAt(0)?.toUpperCase() || 'U')}</span>
                          </div>
                        )}
                        
                        {isExpanded && (
                          <div className="project-item-menu">
                            <ProjectItemMenu 
                              project={project} 
                              startRenaming={startRenaming} 
                              deleteProject={deleteProject} 
                            />
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              );
            })
          )}
        </div>

        {/* ── Deployed Sites section ──────────────────────── */}
        {isExpanded && (() => {
          const deployedProjects = allProjects.filter(p => p.deployed_url);
          if (deployedProjects.length === 0) return null;
          return (
            <div className="sidebar-deployed-sites">
              <div className="sidebar-section-label">🌐 Deployed Sites</div>
              {deployedProjects.map(p => (
                <a
                  key={p.id}
                  href={p.deployed_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="sidebar-deployed-link"
                  title={p.deployed_url}
                >
                  <span className="sidebar-deployed-dot" />
                  <span className="sidebar-deployed-name">{p.title || 'Untitled'}</span>
                  <span className="sidebar-deployed-arrow">↗</span>
                </a>
              ))}
            </div>
          );
        })()}

        <div className="sidebar-footer">
          <button className="user-profile-btn" onClick={handleLogout} title="Logout">
            <div className="user-avatar">U</div>
            {isExpanded && <span className="user-name">Logout</span>}
          </button>
        </div>
      </aside>
    </>
  );
}

function ProjectItemMenu({ project, startRenaming, deleteProject }) {
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen]);

  const toggleMenu = (e) => {
    e.stopPropagation();
    setIsOpen(!isOpen);
  };

  const handleAction = (e, action) => {
    e.stopPropagation();
    setIsOpen(false);
    action(e, project);
  };

  const notImplemented = (e) => {
    e.stopPropagation();
    setIsOpen(false);
    alert("Not implemented yet");
  };

  return (
    <div className="project-menu-container" ref={menuRef}>
      <button className="project-menu-trigger" onClick={toggleMenu}>
        <MoreHorizontal size={14} />
      </button>
      {isOpen && (
        <div className="project-menu-dropdown">
          <button onClick={(e) => handleAction(e, (ev) => startRenaming(ev, project))}><Pencil size={12} /> Rename</button>
          <button onClick={notImplemented}><Copy size={12} /> Duplicate</button>
          <button onClick={notImplemented}><Archive size={12} /> Archive</button>
          <div className="menu-divider" />
          <button className="danger" onClick={(e) => handleAction(e, (ev) => deleteProject(ev, project.id))}><Trash2 size={12} /> Delete</button>
        </div>
      )}
    </div>
  );
}

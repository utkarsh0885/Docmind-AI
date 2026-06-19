import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  MessageSquare,
  FileText,
  Settings,
  Server,
  PanelLeftClose,
  PanelLeft,
  Menu,
  X,
} from 'lucide-react';
import axios from 'axios';
import { DocMindLogo } from '../Branding/DocMindLogo';

interface DashboardLayoutProps {
  children: React.ReactNode;
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

const navItems = [
  { id: 'chat', label: 'Chat', icon: MessageSquare, shortcut: '⌘1' },
  { id: 'documents', label: 'Documents', icon: FileText, shortcut: '⌘2' },
  { id: 'settings', label: 'Settings', icon: Settings, shortcut: '⌘3' },
];

export const DashboardLayout: React.FC<DashboardLayoutProps> = ({
  children,
  activeTab,
  setActiveTab,
}) => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(null);

  useEffect(() => {
    const checkHealth = async () => {
      try {
        const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        await axios.get(`${API_URL}/api/health`);
        setBackendHealthy(true);
      } catch {
        setBackendHealthy(false);
      }
    };
    checkHealth();
    const interval = setInterval(checkHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey) {
        if (e.key === '1') { e.preventDefault(); setActiveTab('chat'); }
        if (e.key === '2') { e.preventDefault(); setActiveTab('documents'); }
        if (e.key === '3') { e.preventDefault(); setActiveTab('settings'); }
        if (e.key === 'b') { e.preventDefault(); setCollapsed(prev => !prev); }
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [setActiveTab]);

  const handleNavClick = (id: string) => {
    setActiveTab(id);
    setMobileOpen(false);
  };

  const SidebarContent = () => (
    <div className="flex flex-col h-full">
      {/* Brand */}
      <div className={`flex items-center gap-3 px-4 h-14 shrink-0 border-b border-surface-800/60 ${collapsed ? 'justify-center' : ''}`}>
        <div className="h-8 w-8 flex items-center justify-center rounded-lg bg-surface-900 border border-surface-800/80 shrink-0 shadow-glow-sm">
          <DocMindLogo size={18} />
        </div>
        {!collapsed && (
          <motion.div
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.15 }}
          >
            <h1 className="font-bold text-sm text-surface-100 tracking-tight">
              DocMind AI
            </h1>
            <p className="text-2xs text-surface-500 font-medium -mt-0.5">
              Enterprise Knowledge Assistant
            </p>
          </motion.div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto scrollbar-none">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              id={`nav-${item.id}`}
              onClick={() => handleNavClick(item.id)}
              className={`relative w-full flex items-center gap-3 rounded-lg text-[13px] font-medium transition-all duration-150 cursor-pointer
                ${collapsed ? 'justify-center px-2 py-2.5' : 'px-3 py-2.5'}
                ${isActive
                  ? 'text-surface-100 bg-surface-800/80'
                  : 'text-surface-400 hover:text-surface-200 hover:bg-surface-800/40'
                }`}
              title={collapsed ? item.label : undefined}
            >
              {isActive && (
                <motion.div
                  layoutId="nav-active-bg"
                  className="absolute inset-0 rounded-lg bg-surface-800/80"
                  transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                />
              )}
              <Icon className={`h-[18px] w-[18px] relative z-10 shrink-0 ${isActive ? 'text-accent-400' : ''}`} />
              {!collapsed && (
                <>
                  <span className="relative z-10">{item.label}</span>
                  <kbd className="ml-auto relative z-10 hidden lg:inline-flex items-center px-1.5 py-0.5 rounded text-2xs text-surface-600 bg-surface-800/60 font-mono">
                    {item.shortcut}
                  </kbd>
                </>
              )}
            </button>
          );
        })}
      </nav>

      {/* Footer */}
      <div className={`px-3 py-3 border-t border-surface-800/60 space-y-2 ${collapsed ? 'flex flex-col items-center' : ''}`}>
        {/* Collapse toggle — desktop only */}
        <button
          onClick={() => setCollapsed(prev => !prev)}
          className="hidden md:flex items-center gap-2 w-full px-3 py-2 rounded-lg text-surface-500 hover:text-surface-300 hover:bg-surface-800/40 transition-all text-xs font-medium cursor-pointer"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed ? (
            <PanelLeft className="h-4 w-4 mx-auto" />
          ) : (
            <>
              <PanelLeftClose className="h-4 w-4" />
              <span>Collapse</span>
              <kbd className="ml-auto hidden lg:inline-flex items-center px-1.5 py-0.5 rounded text-2xs text-surface-600 bg-surface-800/60 font-mono">
                ⌘B
              </kbd>
            </>
          )}
        </button>

        {/* API status */}
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg bg-surface-900/60 border border-surface-800/60 ${collapsed ? 'justify-center px-2' : ''}`}>
          <div className="relative flex items-center justify-center">
            <span
              className={`h-2 w-2 rounded-full ${
                backendHealthy === true
                  ? 'bg-emerald-400'
                  : backendHealthy === false
                  ? 'bg-red-400 animate-pulse'
                  : 'bg-amber-400'
              }`}
            />
            {backendHealthy === true && (
              <span className="absolute h-2 w-2 rounded-full bg-emerald-400/40 animate-ping" />
            )}
          </div>
          {!collapsed && (
            <div className="flex items-center gap-1.5">
              <Server className="h-3 w-3 text-surface-500" />
              <span className="text-2xs text-surface-500 font-medium uppercase tracking-wider">
                {backendHealthy === true ? 'API Connected' : backendHealthy === false ? 'API Offline' : 'Connecting...'}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-surface-950">
      {/* Desktop Sidebar */}
      <motion.aside
        className="hidden md:flex flex-col shrink-0 border-r border-surface-800/60 bg-surface-900/50 overflow-hidden"
        animate={{ width: collapsed ? 72 : 256 }}
        transition={{ duration: 0.2, ease: 'easeOut' }}
      >
        <SidebarContent />
      </motion.aside>

      {/* Mobile Overlay */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            <motion.div
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setMobileOpen(false)}
            />
            <motion.aside
              className="fixed inset-y-0 left-0 w-72 z-50 md:hidden flex flex-col bg-surface-900 border-r border-surface-800"
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', stiffness: 400, damping: 35 }}
            >
              <SidebarContent />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      {/* Main Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Mobile header */}
        <div className="flex md:hidden items-center gap-3 px-4 h-14 border-b border-surface-800/60 bg-surface-900/50 shrink-0">
          <button
            onClick={() => setMobileOpen(true)}
            className="p-2 rounded-lg text-surface-400 hover:text-surface-200 hover:bg-surface-800/40 transition-colors cursor-pointer"
          >
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
          <div className="flex items-center gap-2">
            <div className="h-6 w-6 flex items-center justify-center rounded-md bg-surface-900 border border-surface-800/80">
              <DocMindLogo size={14} gradientId="docmind-gradient-mobile" />
            </div>
            <span className="font-semibold text-sm text-surface-100">DocMind AI</span>
          </div>
        </div>

        {/* Page content */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {children}
        </main>
      </div>
    </div>
  );
};

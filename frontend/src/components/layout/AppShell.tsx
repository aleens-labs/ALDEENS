import { useState } from 'react';
import { Outlet } from 'react-router-dom';

import { useAleensApp } from '../../router/AppStateContext';
import { Sidebar } from './Sidebar';
import { TopHeader } from './TopHeader';

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false);
  const { busy, error, clearError } = useAleensApp();

  return (
    <div className="app-shell">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((value) => !value)} />

      <div className={`app-main ${collapsed ? 'sidebar-collapsed' : ''}`}>
        <TopHeader />

        {busy ? (
          <div className="app-busy-overlay" role="status" aria-live="polite">
            <div className="app-busy-spinner" />
            <p>Running analysis pipeline...</p>
          </div>
        ) : null}

        <main className="app-content">
          {error ? (
            <div className="app-inline-error">
              <span>{error}</span>
              <button type="button" onClick={clearError}>
                Dismiss
              </button>
            </div>
          ) : null}
          <Outlet />
        </main>
      </div>
    </div>
  );
}

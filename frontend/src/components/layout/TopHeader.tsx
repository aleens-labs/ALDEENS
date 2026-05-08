import { Download, FileJson, FileText } from 'lucide-react';
import { useLocation } from 'react-router-dom';

import { APP_LOGO_PATH, APP_NAME } from '../../lib/branding';
import { useAleensApp } from '../../router/AppStateContext';
import { findNavRoute } from '../../router/navigation';

export function TopHeader() {
  const { analysis, downloadExport } = useAleensApp();
  const location = useLocation();
  const route = findNavRoute(location.pathname);

  return (
    <header className="top-header">
      <div>
        <div className="top-header-brand-row">
          <img src={APP_LOGO_PATH} alt={`${APP_NAME} logo`} className="top-header-brand-mark" />
          <p className="top-header-breadcrumb">
            {APP_NAME} / {route.shortLabel}
          </p>
        </div>
        <h1 className="top-header-title">{route.pageTitle}</h1>
        <p className="top-header-description">{route.description}</p>
      </div>

      {analysis ? (
        <div className="top-header-actions">
          <button type="button" onClick={() => void downloadExport('pdf')} className="header-export primary">
            <Download size={16} />
            <span>PDF</span>
          </button>
          <button type="button" onClick={() => void downloadExport('json')} className="header-export">
            <FileJson size={16} />
            <span>JSON</span>
          </button>
          <button type="button" onClick={() => void downloadExport('md')} className="header-export">
            <FileText size={16} />
            <span>MD</span>
          </button>
        </div>
      ) : null}
    </header>
  );
}

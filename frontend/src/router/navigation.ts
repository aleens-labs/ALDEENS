import type { LucideIcon } from 'lucide-react';
import {
  BarChart2,
  ClipboardList,
  Clock3,
  Database,
  FileText,
  GitBranch,
  LayoutDashboard,
  Shield,
  Upload,
} from 'lucide-react';

export interface NavRouteItem {
  path: string;
  label: string;
  shortLabel: string;
  pageTitle: string;
  description: string;
  icon: LucideIcon;
}

export const NAV_ROUTES: NavRouteItem[] = [
  {
    path: '/',
    label: 'Dashboard',
    shortLabel: 'Dashboard',
    pageTitle: 'Dashboard',
    description: 'Mission status, KPIs, and recent analyses',
    icon: LayoutDashboard,
  },
  {
    path: '/intake',
    label: 'Intake',
    shortLabel: 'Intake',
    pageTitle: 'Incident Intake',
    description: 'Select a dataset or upload Windows telemetry',
    icon: Upload,
  },
  {
    path: '/attack-graph',
    label: 'Attack Graph',
    shortLabel: 'Attack Graph',
    pageTitle: 'Attack Graph',
    description: 'Visual chain reconstruction across the current incident',
    icon: GitBranch,
  },
  {
    path: '/timeline',
    label: 'Timeline',
    shortLabel: 'Timeline',
    pageTitle: 'Attack Timeline',
    description: 'Chronological incident reconstruction with deltas',
    icon: Clock3,
  },
  {
    path: '/scoring',
    label: 'Scoring',
    shortLabel: 'Scoring',
    pageTitle: 'Deterministic Scoring',
    description: 'Risk and confidence breakdown from the rule engine',
    icon: BarChart2,
  },
  {
    path: '/evidence',
    label: 'Evidence',
    shortLabel: 'Evidence',
    pageTitle: 'Evidence Board',
    description: 'Normalized telemetry artifacts and verification',
    icon: Database,
  },
  {
    path: '/mitre',
    label: 'MITRE ATT&CK',
    shortLabel: 'MITRE',
    pageTitle: 'MITRE ATT&CK Coverage',
    description: 'Technique and tactic coverage mapped from findings',
    icon: Shield,
  },
  {
    path: '/analyst-brief',
    label: 'Analyst Brief',
    shortLabel: 'Brief',
    pageTitle: 'Analyst Brief',
    description: 'Narrative report, exports, and analyst verdict input',
    icon: FileText,
  },
  {
    path: '/audit',
    label: 'Audit Trail',
    shortLabel: 'Audit',
    pageTitle: 'Audit Trail',
    description: 'Historical analyses, filters, and comparison mode',
    icon: ClipboardList,
  },
];

export function findNavRoute(pathname: string): NavRouteItem {
  return NAV_ROUTES.find((item) => item.path === pathname) ?? NAV_ROUTES[0];
}

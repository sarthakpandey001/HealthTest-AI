
import React from 'react';
import { JiraIcon } from './icons/JiraIcon';
import { AzureIcon } from './icons/AzureIcon';
import { DownloadIcon } from './icons/DownloadIcon';

interface ExportIntegrateProps {
  onDownloadClick: () => void;
  hasTestCases: boolean;
}

export const ExportIntegrate: React.FC<ExportIntegrateProps> = ({ onDownloadClick, hasTestCases }) => {
  return (
    <div className="mb-6">
      <h3 className="text-md font-semibold text-slate-800 mb-3">Export & Integrate</h3>
      <div className="space-y-2">
        <button className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-slate-800 text-white rounded-md hover:bg-slate-900 transition-colors">
          <JiraIcon className="h-5 w-5" />
          <span className="font-semibold">Export to Jira</span>
        </button>
        <button className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-blue-700 text-white rounded-md hover:bg-blue-800 transition-colors">
          <AzureIcon className="h-5 w-5" />
          <span className="font-semibold">Export to Azure DevOps</span>
        </button>
        <button 
          onClick={onDownloadClick}
          disabled={!hasTestCases}
          className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-slate-200 text-slate-800 rounded-md hover:bg-slate-300 transition-colors disabled:bg-slate-100 disabled:text-slate-400 disabled:cursor-not-allowed"
        >
          <DownloadIcon className="h-5 w-5" />
          <span className="font-semibold">Download (CSV/JSN)</span>
        </button>
      </div>
    </div>
  );
};

import React, { useState } from 'react';
import { JiraIcon } from './icons/JiraIcon';
import { AzureIcon } from './icons/AzureIcon';
import { DownloadIcon } from './icons/DownloadIcon';
import { TestCase } from '../types';
import { CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

interface ExportIntegrateProps {
  onDownloadClick: () => void;
  hasTestCases: boolean;
  testCases?: TestCase[];
}

export const ExportIntegrate: React.FC<ExportIntegrateProps> = ({ onDownloadClick, hasTestCases, testCases = [] }) => {
  const [isExporting, setIsExporting] = useState(false);
  const [exportStatus, setExportStatus] = useState<{
    type: 'success' | 'error' | null;
    message: string;
  }>({ type: null, message: '' });
 
  const handleJiraExport = async () => {
    if (!hasTestCases || !testCases.length) {
      setExportStatus({
        type: 'error',
        message: 'No test cases available to export'
      });
      return;
    }
 
    setIsExporting(true);
    setExportStatus({ type: null, message: '' });

    // Log the payload for verification
    console.log('Sending test cases payload:', JSON.stringify(testCases, null, 2));
 
    try {
      const response = await fetch('https://tc-gen-ai-550827394009.us-east4.run.app/create-jira-issues', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(testCases),
      });
 
      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${await response.text()}`);
      }
 
      const result = await response.json();
      setExportStatus({
        type: 'success',
        message: `Successfully exported ${result.length || testCases.length} test cases to Jira`
      });
    } catch (error) {
      console.error('Export error:', error);
      setExportStatus({
        type: 'error',
        message: error instanceof Error ? error.message : 'Failed to export to Jira'
      });
    } finally {
      setIsExporting(false);
    }
  };
 
  return (
    <div className="mb-6">
      <h3 className="text-md font-semibold text-slate-800 mb-3">Export & Integrate</h3>
      <div className="space-y-2">
        <button
          onClick={handleJiraExport}
          disabled={isExporting || !hasTestCases}
          className="w-full flex items-center justify-center space-x-2 py-2.5 px-4 bg-slate-800 text-white rounded-md hover:bg-slate-900 transition-colors disabled:bg-slate-600 disabled:cursor-not-allowed"
        >
          {isExporting ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              <span className="font-semibold">Exporting to Jira...</span>
            </>
          ) : (
            <>
              <JiraIcon className="h-5 w-5" />
              <span className="font-semibold">Export to Jira</span>
            </>
          )}
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

        {exportStatus.type && (
          <div className={`mt-3 p-3 rounded-md flex items-center space-x-2 ${
            exportStatus.type === 'success' ? 'bg-green-50 text-green-800' : 'bg-red-50 text-red-800'
          }`}>
            {exportStatus.type === 'success' ? (
              <CheckCircle className="h-5 w-5" />
            ) : (
              <AlertCircle className="h-5 w-5" />
            )}
            <span className="text-sm">{exportStatus.message}</span>
          </div>
        )}
      </div>
    </div>
  );
};
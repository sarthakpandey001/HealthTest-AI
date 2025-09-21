
import React from 'react';
import { EdgeCasesSummary } from './EdgeCasesSummary';
import { FeatureGapAnalysis } from './FeatureGapAnalysis';
import { ExportIntegrate } from './ExportIntegrate';
import { TestCaseHistory } from './TestCaseHistory';
import { TestCase } from '../types';

interface InsightsPanelProps {
  summary: {
    positive: number;
    negative: number;
    neutral: number;
  };
  gaps: string[];
  testCases: TestCase[];
  onDownloadClick: () => void;
}

export const InsightsPanel: React.FC<InsightsPanelProps> = ({ summary, gaps, testCases, onDownloadClick }) => {
  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-lg shadow-md">
        <h2 className="text-lg font-bold text-slate-900 mb-4">Insights & Integration</h2>
        <EdgeCasesSummary summary={summary} />
        <FeatureGapAnalysis gaps={gaps} />
        <ExportIntegrate onDownloadClick={onDownloadClick} hasTestCases={testCases.length > 0} />
        <TestCaseHistory />
      </div>
    </div>
  );
};
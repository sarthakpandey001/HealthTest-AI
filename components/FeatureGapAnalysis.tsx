
import React from 'react';

interface FeatureGapAnalysisProps {
    gaps: string[];
}

export const FeatureGapAnalysis: React.FC<FeatureGapAnalysisProps> = ({ gaps }) => {
  return (
    <div className="mb-6">
      <h3 className="text-md font-semibold text-slate-800 mb-3">Feature Gap Analysis</h3>
      {gaps.length > 0 ? (
        <ul className="space-y-2 text-sm text-slate-600 list-disc list-inside bg-amber-50 p-3 rounded-md">
            {gaps.map((gap, index) => <li key={index}>{gap}</li>)}
        </ul>
      ) : (
        <p className="text-sm text-slate-500">No feature gaps identified yet. Generate test cases to see analysis.</p>
      )}
    </div>
  );
};

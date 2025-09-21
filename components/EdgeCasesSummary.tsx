
import React from 'react';

interface EdgeCasesSummaryProps {
  summary: {
    positive: number;
    negative: number;
    neutral: number;
  };
}

export const EdgeCasesSummary: React.FC<EdgeCasesSummaryProps> = ({ summary }) => {
  return (
    <div className="mb-6">
      <h3 className="text-md font-semibold text-slate-800 mb-3">Generated Edge Cases</h3>
      <div className="flex justify-between space-x-2">
        <div className="flex-1 text-center bg-green-100 text-green-800 p-3 rounded-md">
          <div className="text-2xl font-bold">{summary.positive}</div>
          <div className="text-sm font-medium">Positive</div>
        </div>
        <div className="flex-1 text-center bg-red-100 text-red-800 p-3 rounded-md">
          <div className="text-2xl font-bold">{summary.negative}</div>
          <div className="text-sm font-medium">Negative</div>
        </div>
        <div className="flex-1 text-center bg-blue-100 text-blue-800 p-3 rounded-md">
          <div className="text-2xl font-bold">{summary.neutral}</div>
          <div className="text-sm font-medium">Neutral</div>
        </div>
      </div>
    </div>
  );
};


import React from 'react';
import { TestCase } from '../types';
import { TestCaseToolbar } from './TestCaseToolbar';
import { TestCaseList } from './TestCaseList';

interface TestCasesPanelProps {
  testCases: TestCase[];
  isLoading: boolean;
  error: string | null;
  onEdit: (testCase: TestCase) => void;
}

export const TestCasesPanel: React.FC<TestCasesPanelProps> = ({ testCases, isLoading, error, onEdit }) => {
  return (
    <div className="bg-white p-6 rounded-lg shadow-md h-full">
      <h2 className="text-lg font-bold text-slate-900 mb-4">Generated Test Cases</h2>
      <TestCaseToolbar />
      <div className="mt-4">
        {isLoading && (
          <div className="flex justify-center items-center py-10">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          </div>
        )}
        {error && <div className="text-center text-red-600 bg-red-100 p-3 rounded-md">{error}</div>}
        {!isLoading && !error && testCases.length === 0 && (
          <div className="text-center py-10 text-slate-500">
            <p>No test cases generated yet.</p>
            <p className="text-sm">Enter your requirements and click "Generate Test Cases" to start.</p>
          </div>
        )}
        {!isLoading && testCases.length > 0 && (
          <TestCaseList testCases={testCases} onEdit={onEdit} />
        )}
      </div>
    </div>
  );
};

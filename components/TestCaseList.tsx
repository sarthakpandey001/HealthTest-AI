
import React from 'react';
import { TestCase } from '../types';
import { TestCaseItem } from './TestCaseItem';

interface TestCaseListProps {
  testCases: TestCase[];
  onEdit: (testCase: TestCase) => void;
}

export const TestCaseList: React.FC<TestCaseListProps> = ({ testCases, onEdit }) => {
  const headers = ['ID', 'Title', 'Priority', 'Status', 'Traceability', 'Actions'];
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm text-left text-slate-600">
        <thead className="text-xs text-slate-700 uppercase bg-slate-50">
          <tr>
            <th scope="col" className="p-4 w-10">
              <input type="checkbox" className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500" />
            </th>
            {headers.map(header => (
              <th key={header} scope="col" className="px-6 py-3">{header}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {testCases.map((testCase) => (
            <TestCaseItem key={testCase.id} testCase={testCase} onEdit={onEdit} />
          ))}
        </tbody>
      </table>
    </div>
  );
};

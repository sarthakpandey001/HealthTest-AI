
import React from 'react';
import { TestCase, Priority, Status, TestCaseType } from '../types';
import { MoreVertIcon } from './icons/MoreVertIcon';
import { CheckIcon } from './icons/CheckIcon';

interface TestCaseItemProps {
  testCase: TestCase;
  onEdit: (testCase: TestCase) => void;
}

const typeColorClasses: Record<TestCaseType, string> = {
  [TestCaseType.Positive]: 'bg-green-100 text-green-800',
  [TestCaseType.Negative]: 'bg-red-100 text-red-800',
  [TestCaseType.Neutral]: 'bg-blue-100 text-blue-800',
};

const priorityColorClasses: Record<Priority, string> = {
  [Priority.High]: 'bg-red-100 text-red-800',
  [Priority.Medium]: 'bg-yellow-100 text-yellow-800',
  [Priority.Low]: 'bg-blue-100 text-blue-800',
};

const statusColorClasses: Record<Status, string> = {
    [Status.Pass]: 'bg-green-100 text-green-800',
    [Status.Fail]: 'bg-red-100 text-red-800',
    [Status.Blocked]: 'bg-yellow-100 text-yellow-800',
    [Status.Draft]: 'bg-slate-100 text-slate-800',
};


export const TestCaseItem: React.FC<TestCaseItemProps> = ({ testCase, onEdit }) => {
  return (
    <tr className="bg-white border-b hover:bg-slate-50">
      <td className="p-4 w-10">
        <input type="checkbox" className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500" />
      </td>
      <td className="px-6 py-4 font-medium text-slate-900">{testCase.id}</td>
      <td className="px-6 py-4">
        <div className="font-semibold text-slate-800">{testCase.title}</div>
        <div className={`text-xs font-medium inline-flex items-center px-2.5 py-0.5 rounded-full ${typeColorClasses[testCase.type]}`}>
          <CheckIcon className="w-3 h-3 mr-1.5" />
          {testCase.type}
        </div>
      </td>
      <td className="px-6 py-4">
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${priorityColorClasses[testCase.priority]}`}>
          {testCase.priority}
        </span>
      </td>
      <td className="px-6 py-4">
        <span className={`px-2 py-1 text-xs font-medium rounded-full ${statusColorClasses[testCase.status]}`}>
            {testCase.status}
        </span>
      </td>
      <td className="px-6 py-4">
        {testCase.traceability && testCase.traceability.length > 0 ? (
          <span className="text-xs text-slate-700">{testCase.traceability.join(', ')}</span>
        ) : (
          <span className="text-xs text-slate-400 italic">N/A</span>
        )}
      </td>
      <td className="px-6 py-4">
        <div className="flex items-center space-x-2">
            <button onClick={() => onEdit(testCase)} className="font-medium text-blue-600 hover:underline">View/Edit</button>
            <button className="p-1 rounded-full hover:bg-slate-200">
                <MoreVertIcon className="h-5 w-5 text-slate-600"/>
            </button>
        </div>
      </td>
    </tr>
  );
};

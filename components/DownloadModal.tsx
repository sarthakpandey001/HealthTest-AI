import React from 'react';
import { TestCase } from '../types';
import { CloseIcon } from './icons/CloseIcon';
import { DownloadIcon } from './icons/DownloadIcon';
import { exportTestCasesToCSV, exportTestCasesToJSON } from '../utils/fileExporter';

interface DownloadModalProps {
  isOpen: boolean;
  onClose: () => void;
  testCases: TestCase[];
}

export const DownloadModal: React.FC<DownloadModalProps> = ({ isOpen, onClose, testCases }) => {
  if (!isOpen) {
    return null;
  }

  const handleDownloadCSV = () => {
    exportTestCasesToCSV(testCases);
    onClose();
  };

  const handleDownloadJSON = () => {
    exportTestCasesToJSON(testCases);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50 p-4" aria-modal="true" role="dialog">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md">
        <div className="flex justify-between items-center p-4 border-b">
          <div className="flex items-center space-x-3">
            <DownloadIcon className="h-6 w-6 text-blue-600" />
            <h2 className="text-xl font-bold text-slate-900">Choose Download Format</h2>
          </div>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-slate-100" aria-label="Close modal">
            <CloseIcon className="h-6 w-6 text-slate-600" />
          </button>
        </div>
        
        <div className="p-6 space-y-4">
          <p className="text-sm text-slate-600">Please select the format you'd like to download your test cases in.</p>
          <div className="flex justify-center space-x-4">
            <button 
              onClick={handleDownloadCSV}
              className="flex-1 bg-blue-600 text-white font-semibold py-2.5 px-4 rounded-md hover:bg-blue-700 transition-colors"
            >
              Download CSV
            </button>
            <button 
              onClick={handleDownloadJSON}
              className="flex-1 bg-slate-700 text-white font-semibold py-2.5 px-4 rounded-md hover:bg-slate-800 transition-colors"
            >
              Download JSON
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

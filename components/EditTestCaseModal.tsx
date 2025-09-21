import React, { useState } from 'react';
import { TestCase, Priority, Status } from '../types';
import { CloseIcon } from './icons/CloseIcon';
import { generateCodeSnippet, suggestAssertions } from '../services/geminiService';

interface EditTestCaseModalProps {
  testCase: TestCase;
  onClose: () => void;
  onSave: (testCase: TestCase) => void;
}

export const EditTestCaseModal: React.FC<EditTestCaseModalProps> = ({ testCase, onClose, onSave }) => {
  const [editedTestCase, setEditedTestCase] = useState<TestCase>(testCase);
  const [isGeneratingSnippet, setIsGeneratingSnippet] = useState(false);
  const [isSuggesting, setIsSuggesting] = useState(false);
  const [codeSnippet, setCodeSnippet] = useState('');
  const [suggestions, setSuggestions] = useState<string[]>([]);

  const handleInputChange = <K extends keyof TestCase,>(field: K, value: TestCase[K]) => {
    setEditedTestCase(prev => ({ ...prev, [field]: value }));
  };

  const handleArrayChange = (field: 'steps' | 'expectedResults' | 'preconditions', index: number, value: string) => {
    const newArray = [...editedTestCase[field]];
    newArray[index] = value;
    handleInputChange(field, newArray);
  };
  
  const handleGenerateSnippet = async () => {
    setIsGeneratingSnippet(true);
    setCodeSnippet('');
    try {
      const snippet = await generateCodeSnippet(editedTestCase);
      setCodeSnippet(snippet);
    } catch (error) {
      console.error(error);
      setCodeSnippet('Error generating snippet.');
    } finally {
      setIsGeneratingSnippet(false);
    }
  };

  const handleSuggestAssertions = async () => {
    setIsSuggesting(true);
    setSuggestions([]);
     try {
      const result = await suggestAssertions(editedTestCase);
      setSuggestions(result);
    } catch (error) {
      console.error(error);
      setSuggestions(['Error generating suggestions.']);
    } finally {
      setIsSuggesting(false);
    }
  };


  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] flex flex-col">
        <div className="flex justify-between items-center p-4 border-b">
          <h2 className="text-xl font-bold text-slate-900">Edit Test Case</h2>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-slate-100">
            <CloseIcon className="h-6 w-6 text-slate-600" />
          </button>
        </div>
        
        <div className="p-6 overflow-y-auto space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-sm font-medium text-slate-700">Test Case ID</label>
              <input type="text" value={editedTestCase.id} disabled className="mt-1 block w-full bg-slate-100 border-slate-300 rounded-md shadow-sm p-2" />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700">Title</label>
              <input type="text" value={editedTestCase.title} onChange={(e) => handleInputChange('title', e.target.value)} className="mt-1 block w-full border-slate-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 p-2 bg-white text-black" />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700">Description</label>
            <textarea value={editedTestCase.description} onChange={(e) => handleInputChange('description', e.target.value)} rows={3} className="mt-1 block w-full border-slate-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 p-2 bg-white text-black" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
             <div>
                <label className="block text-sm font-medium text-slate-700">Preconditions</label>
                {editedTestCase.preconditions.map((pre, index) => (
                    <input key={index} type="text" value={pre} onChange={(e) => handleArrayChange('preconditions', index, e.target.value)} className="mt-1 block w-full border-slate-300 rounded-md shadow-sm p-2 mb-2 bg-white text-black"/>
                ))}
            </div>
            <div>
                <label className="block text-sm font-medium text-slate-700">Test Steps</label>
                {editedTestCase.steps.map((step, index) => (
                    <input key={index} type="text" value={step} onChange={(e) => handleArrayChange('steps', index, e.target.value)} className="mt-1 block w-full border-slate-300 rounded-md shadow-sm p-2 mb-2 bg-white text-black"/>
                ))}
            </div>
          </div>
            
          <div>
            <label className="block text-sm font-medium text-slate-700">Expected Results</label>
             {editedTestCase.expectedResults.map((result, index) => (
                <input key={index} type="text" value={result} onChange={(e) => handleArrayChange('expectedResults', index, e.target.value)} className="mt-1 block w-full border-slate-300 rounded-md shadow-sm p-2 mb-2 bg-white text-black"/>
            ))}
          </div>

          <div className="border-t pt-4 space-y-4">
              <button onClick={handleSuggestAssertions} disabled={isSuggesting} className="text-sm text-blue-600 font-semibold hover:underline disabled:text-slate-400">
                {isSuggesting ? 'Suggesting...' : 'Suggested Assertions'}
              </button>
              {suggestions.length > 0 && (
                <div className="bg-slate-50 p-3 rounded-md">
                    <ul className="list-disc list-inside space-y-1 text-sm text-slate-700">
                       {suggestions.map((s, i) => <li key={i}><code>{s}</code></li>)}
                    </ul>
                </div>
              )}
          </div>

           <div className="border-t pt-4 space-y-4">
              <button onClick={handleGenerateSnippet} disabled={isGeneratingSnippet} className="text-sm text-blue-600 font-semibold hover:underline disabled:text-slate-400">
                {isGeneratingSnippet ? 'Generating...' : 'Generate Code Snippet (CURL)'}
              </button>
              {codeSnippet && (
                <pre className="bg-slate-900 text-white p-4 rounded-md text-sm overflow-x-auto">
                  <code>{codeSnippet}</code>
                </pre>
              )}
          </div>

        </div>
        
        <div className="flex justify-end items-center p-4 border-t space-x-3">
          <button onClick={onClose} className="py-2 px-4 border border-slate-300 rounded-md text-sm font-medium hover:bg-slate-50">Cancel</button>
          <button onClick={() => onSave(editedTestCase)} className="py-2 px-4 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700">Save</button>
        </div>
      </div>
    </div>
  );
};
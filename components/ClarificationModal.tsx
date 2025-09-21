import React, { useState, useEffect } from 'react';
import { CloseIcon } from './icons/CloseIcon';
import { QuestionIcon } from './icons/QuestionIcon';

interface ClarificationModalProps {
  isOpen: boolean;
  questions: string[];
  onClose: () => void;
  onSubmit: (answers: string[]) => void;
  onSkip: () => void;
  isLoading: boolean;
}

export const ClarificationModal: React.FC<ClarificationModalProps> = ({ 
    isOpen, 
    questions, 
    onClose, 
    onSubmit, 
    onSkip,
    isLoading
}) => {
  const [answers, setAnswers] = useState<string[]>([]);

  useEffect(() => {
    if (questions) {
      setAnswers(new Array(questions.length).fill(''));
    }
  }, [questions]);

  if (!isOpen) {
    return null;
  }

  const handleAnswerChange = (index: number, value: string) => {
    const newAnswers = [...answers];
    newAnswers[index] = value;
    setAnswers(newAnswers);
  };

  const handleSubmit = () => {
    if(!isLoading) {
        onSubmit(answers);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50 p-4" aria-modal="true" role="dialog">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] flex flex-col">
        <div className="flex justify-between items-center p-4 border-b">
          <div className="flex items-center space-x-3">
            <QuestionIcon className="h-6 w-6 text-blue-600" />
            <h2 className="text-xl font-bold text-slate-900">Clarification Needed</h2>
          </div>
          <button onClick={onClose} className="p-2 rounded-full hover:bg-slate-100" aria-label="Close modal">
            <CloseIcon className="h-6 w-6 text-slate-600" />
          </button>
        </div>
        
        <div className="p-6 overflow-y-auto space-y-4">
          <p className="text-sm text-slate-600">The AI has identified some potential ambiguities in the requirements. Please provide answers to the questions below for more accurate test cases.</p>
          {questions.map((question, index) => (
            <div key={index}>
              <label htmlFor={`question-${index}`} className="block text-sm font-semibold text-slate-800 mb-2">{index + 1}. {question}</label>
              <textarea
                id={`question-${index}`}
                value={answers[index]}
                onChange={(e) => handleAnswerChange(index, e.target.value)}
                placeholder="Your answer here..."
                rows={3}
                className="w-full p-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-shadow text-sm bg-white text-black resize-y"
              />
            </div>
          ))}
        </div>
        
        <div className="flex justify-end items-center p-4 border-t space-x-3 bg-slate-50 rounded-b-lg">
          <button onClick={onClose} className="py-2 px-4 border border-slate-300 rounded-md text-sm font-medium hover:bg-slate-100 transition-colors">Cancel</button>
          <button onClick={onSkip} className="py-2 px-4 border border-transparent rounded-md text-sm font-medium text-blue-600 hover:bg-blue-50 transition-colors">Generate Anyway</button>
          <button 
            onClick={handleSubmit} 
            disabled={isLoading}
            className="py-2 px-4 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 transition-colors disabled:bg-blue-300 disabled:cursor-not-allowed flex items-center justify-center min-w-[170px]"
          >
             {isLoading ? (
              <>
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Generating...
              </>
            ) : (
              'Submit & Generate'
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

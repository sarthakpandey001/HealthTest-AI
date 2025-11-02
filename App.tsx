import React, { useState, useCallback } from 'react';
import { Header } from './components/Header';
import { InputPanel } from './components/InputPanel';
import { TestCasesPanel } from './components/TestCasesPanel';
import { InsightsPanel } from './components/InsightsPanel';
import { EditTestCaseModal } from './components/EditTestCaseModal';
import { ClarificationModal } from './components/ClarificationModal';
import { DownloadModal } from './components/DownloadModal';
import { Login } from './components/Login';
import { TestCase, TestCaseType, User } from './types';
import { generateTestCases, getClarificationQuestions } from './services/geminiService';
import { sampleRequirements, sampleOpenAPISchema } from './data/sampleData';
import CorpusManager from './components/addsource';

const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [requirementsInput, setRequirementsInput] = useState<string>(sampleRequirements);
  const [openApiSchema, setOpenApiSchema] = useState<string>(sampleOpenAPISchema);
  const [testCases, setTestCases] = useState<TestCase[]>([]);
  const [featureGaps, setFeatureGaps] = useState<string[]>([]);
  const [loadingState, setLoadingState] = useState<'idle' | 'fetching_questions' | 'generating_tests'>('idle');
  const [error, setError] = useState<string | null>(null);

  const [isEditModalOpen, setIsEditModalOpen] = useState<boolean>(false);
  const [isClarificationModalOpen, setIsClarificationModalOpen] = useState<boolean>(false);
  const [isDownloadModalOpen, setIsDownloadModalOpen] = useState<boolean>(false);
  const [clarificationQuestions, setClarificationQuestions] = useState<string[]>([]);
  const [selectedTestCase, setSelectedTestCase] = useState<TestCase | null>(null);

  const handleFinalizeGeneration = useCallback(async (answers?: string[]) => {
    setIsClarificationModalOpen(false);
    setLoadingState('generating_tests');
    setError(null);
    
    let clarifications = '';
    if (answers && clarificationQuestions.length > 0) {
        clarifications = clarificationQuestions.map((q, i) => `Q: ${q}\nA: ${answers[i] || 'No answer provided.'}`).join('\n\n');
    }

    try {
      const result = await generateTestCases(requirementsInput, openApiSchema, clarifications);
      setTestCases(result.testCases);
      setFeatureGaps(result.featureGaps);
    } catch (e) {
      console.error(e);
      setError('Failed to generate test cases. Please check your API key and try again.');
    } finally {
      setLoadingState('idle');
      setClarificationQuestions([]);
    }
  }, [requirementsInput, openApiSchema, clarificationQuestions]);


  const handleInitiateGeneration = useCallback(async () => {
    if (!requirementsInput.trim()) {
      setError('Please enter some requirements.');
      return;
    }
    setLoadingState('fetching_questions');
    setError(null);
    setTestCases([]);
    setFeatureGaps([]);

    try {
      const questions = await getClarificationQuestions(requirementsInput, openApiSchema);
      if (questions && questions.length > 0) {
        setClarificationQuestions(questions);
        setIsClarificationModalOpen(true);
        setLoadingState('idle');
      } else {
        await handleFinalizeGeneration();
      }
    } catch (e) {
      console.error(e);
      setError('Failed to get clarification questions. Please check your API key and try again.');
      setLoadingState('idle');
    }
  }, [requirementsInput, openApiSchema, handleFinalizeGeneration]);


  const handleEditTestCase = (testCase: TestCase) => {
    setSelectedTestCase(testCase);
    setIsEditModalOpen(true);
  };
  
  const handleSaveTestCase = (updatedTestCase: TestCase) => {
    setTestCases(prevTestCases => 
      prevTestCases.map(tc => tc.id === updatedTestCase.id ? updatedTestCase : tc)
    );
    setIsEditModalOpen(false);
    setSelectedTestCase(null);
  };

  const handleCloseModal = () => {
    setIsEditModalOpen(false);
    setSelectedTestCase(null);
  };

  const handleLoginSuccess = (user: User) => {
    setCurrentUser(user);
  };

  const handleLogout = () => {
    setCurrentUser(null);
  }

  const edgeCaseSummary = testCases.reduce((acc, tc) => {
    if (tc.type === TestCaseType.Positive) acc.positive++;
    else if (tc.type === TestCaseType.Negative) acc.negative++;
    else if (tc.type === TestCaseType.Neutral) acc.neutral++;
    return acc;
  }, { positive: 0, negative: 0, neutral: 0 });

  if (!currentUser) {
    return <Login onLoginSuccess={handleLoginSuccess} />;
  }

  return (
    <div className="min-h-screen bg-slate-100 text-slate-800 font-sans">
      <Header user={currentUser} onLogout={handleLogout} />
      <main className="p-4 lg:p-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-6">Automated Test Case Generation</h1>
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-3 flex flex-col gap-4">
            <CorpusManager />
            <InputPanel 
              requirementsInput={requirementsInput}
              setRequirementsInput={setRequirementsInput}
              openApiSchema={openApiSchema}
              setOpenApiSchema={setOpenApiSchema}
              onGenerate={handleInitiateGeneration}
              isLoading={loadingState === 'fetching_questions'}
            />
          </div>
          <div className="lg:col-span-6">
            <TestCasesPanel 
              testCases={testCases} 
              isLoading={loadingState === 'generating_tests'}
              error={error}
              onEdit={handleEditTestCase}
            />
          </div>
          <div className="lg:col-span-3">
            <InsightsPanel 
              summary={edgeCaseSummary}
              gaps={featureGaps}
              testCases={testCases}
              onDownloadClick={() => setIsDownloadModalOpen(true)}
            />
          </div>
        </div>
      </main>
      {isEditModalOpen && selectedTestCase && (
        <EditTestCaseModal
          testCase={selectedTestCase}
          onClose={handleCloseModal}
          onSave={handleSaveTestCase}
        />
      )}
      <ClarificationModal
        isOpen={isClarificationModalOpen}
        questions={clarificationQuestions}
        onClose={() => setIsClarificationModalOpen(false)}
        onSubmit={handleFinalizeGeneration}
        onSkip={() => handleFinalizeGeneration()}
        isLoading={loadingState === 'generating_tests'}
      />
      <DownloadModal
        isOpen={isDownloadModalOpen}
        onClose={() => setIsDownloadModalOpen(false)}
        testCases={testCases}
      />
    </div>
  );
};

export default App;
import React, { useState } from 'react';
import { Plus, X, Loader2, CheckCircle, AlertCircle } from 'lucide-react';

export default function CorpusManager() {
  // Source code corpus state
  const [sourceCodeUrl, setSourceCodeUrl] = useState('');
  const [sourceCodeList, setSourceCodeList] = useState<string[]>([]);
  const [sourceCodeLoading, setSourceCodeLoading] = useState(false);
  const [addingSourceCode, setAddingSourceCode] = useState(false);
  const [deletingSourceCode, setDeletingSourceCode] = useState<string | null>(null);

  // Add source code corpus
  const handleAddSourceCode = async () => {
    if (!sourceCodeUrl.trim()) return;
    setAddingSourceCode(true);
    try {
      const response = await fetch(`${baseUrl}/source-code`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ link: sourceCodeUrl.trim() })
      });
      if (response.status === 202) {
        setSourceCodeList(prev => [...prev, sourceCodeUrl.trim()]);
        setSourceCodeUrl('');
      }
    } catch {}
    setAddingSourceCode(false);
  };

  // Delete source code corpus
  const handleDeleteSourceCode = async (link: string) => {
    setDeletingSourceCode(link);
    try {
      const response = await fetch(`${baseUrl}/source-code`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ link })
      });
      if (response.ok) {
        setSourceCodeList(prev => prev.filter(l => l !== link));
      }
    } catch {}
    setDeletingSourceCode(null);
  };
  const [showModal, setShowModal] = useState(false);
  const [corpusName, setCorpusName] = useState('');
  const [sourceUrl, setSourceUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState('');

  const baseUrl = 'https://tc-gen-ai-550827394009.us-east4.run.app';
  const [corpusList, setCorpusList] = useState<string[]>([]);
  const [corpusLoading, setCorpusLoading] = useState(false);
  const [deletingCorpus, setDeletingCorpus] = useState<string | null>(null);

  const handleDeleteCorpus = async (name: string) => {
    setDeletingCorpus(name);
    try {
      const response = await fetch(`${baseUrl}/corpus/${encodeURIComponent(name)}`, {
        method: 'DELETE',
      });
      if (response.ok) {
        setCorpusList((prev) => prev.filter((n) => n !== name));
      }
    } catch (err) {
      // Optionally handle error
    } finally {
      setDeletingCorpus(null);
    }
  };

  React.useEffect(() => {
    let intervalId: NodeJS.Timeout;
    const fetchCorpus = async () => {
      setCorpusLoading(true);
      try {
        const response = await fetch(`${baseUrl}/corpus`);
        if (response.ok) {
          const data = await response.json();
          if (Array.isArray(data)) {
            setCorpusList(data.map((item) => item.name));
          }
        }
      } catch (err) {
        // Optionally handle error
      } finally {
        setCorpusLoading(false);
      }
    };
    fetchCorpus();
    intervalId = setInterval(fetchCorpus, 150000);
    return () => clearInterval(intervalId);
  }, []);

  const handleSubmit = async () => {
    // Validation
    if (!corpusName.trim()) {
      setError('Corpus name is required');
      return;
    }
    
    if (!sourceUrl.trim()) {
      setError('Source URL is required');
      return;
    }

    // Basic URL validation
    try {
      new URL(sourceUrl);
    } catch {
      setError('Please enter a valid URL');
      return;
    }

    setLoading(true);
    setError('');
    setStatus(null);

    try {
      const response = await fetch(`${baseUrl}/corpus`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          corpus_name: corpusName.trim(),
          link: sourceUrl.trim(),
        }),
      });

      if (response.ok) {
        setStatus('success');
        setTimeout(() => {
          setShowModal(false);
          setCorpusName('');
          setSourceUrl('');
          setStatus(null);
        }, 2000);
      } else {
        const errorData = await response.json().catch(() => ({}));
        setError(errorData.message || `Error: ${response.status} ${response.statusText}`);
        setStatus('error');
      }
    } catch (err) {
      setError('Failed to connect to the server. Please check your connection.');
      setStatus('error');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setShowModal(false);
    setCorpusName('');
    setSourceUrl('');
    setError('');
    setStatus(null);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !loading) {
      handleSubmit();
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg p-6 flex flex-col items-start w-full">
      <div className="w-full flex flex-col gap-2">
        <h1 className="text-2xl font-bold text-slate-800 leading-tight">RAG Corpus Manager</h1>
        <p className="text-slate-600 text-sm mb-2">Manage your document sources</p>
      </div>
      <button
        onClick={() => setShowModal(true)}
        className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition-colors duration-200 shadow-md hover:shadow-lg mt-2 self-start"
      >
        <Plus size={18} />
        <span className="font-medium text-sm">Add Source</span>
      </button>
      <div className="py-4 w-full">
        <h2 className="text-lg font-semibold text-slate-700 mb-2">Available Corpora</h2>
        {corpusLoading ? (
          <div className="text-slate-400">Loading...</div>
        ) : corpusList.length > 0 ? (
          <ul className="list-disc pl-5">
            {corpusList.map((name, idx) => (
              <li key={idx} className="flex items-center justify-between text-slate-800 text-sm mb-1">
                <span>{name}</span>
                <button
                  className="ml-2 px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors disabled:opacity-50"
                  onClick={() => handleDeleteCorpus(name)}
                  disabled={deletingCorpus === name}
                >
                  {deletingCorpus === name ? 'Removing...' : 'Remove'}
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <div className="text-slate-400 text-sm">No corpora found.</div>
        )}

        <div className="mt-8">
          <h2 className="text-lg font-semibold text-slate-700 mb-2">Source Code Corpora</h2>
          <div className="flex gap-2 mb-4">
            <input
              type="url"
              value={sourceCodeUrl}
              onChange={e => setSourceCodeUrl(e.target.value)}
              placeholder="https://github.com/user/repo"
              className="px-3 py-2 border border-slate-300 rounded-lg w-full text-sm"
              disabled={addingSourceCode}
            />
            <button
              onClick={handleAddSourceCode}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm"
              disabled={addingSourceCode || !sourceCodeUrl.trim()}
            >
              {addingSourceCode ? 'Adding...' : 'Add Source Code'}
            </button>
          </div>
          {sourceCodeLoading ? (
            <div className="text-slate-400">Loading...</div>
          ) : sourceCodeList.length > 0 ? (
            <ul className="list-disc pl-5">
              {sourceCodeList.map((link, idx) => (
                <li key={idx} className="flex items-center justify-between text-slate-800 text-sm mb-1">
                  <span>{link}</span>
                  <button
                    className="ml-2 px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors disabled:opacity-50"
                    onClick={() => handleDeleteSourceCode(link)}
                    disabled={deletingSourceCode === link}
                  >
                    {deletingSourceCode === link ? 'Removing...' : 'Remove'}
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-slate-400 text-sm">No source code corpora found.</div>
          )}
        </div>
      </div>

      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 relative">
            <button
              onClick={handleClose}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 transition-colors"
            >
              <X size={24} />
            </button>

            <h2 className="text-2xl font-bold text-slate-800 mb-6">Add New Source</h2>

            <div className="space-y-5">
              <div>
                <label htmlFor="corpusName" className="block text-sm font-medium text-slate-700 mb-2">
                  Corpus Name
                </label>
                <input
                  id="corpusName"
                  type="text"
                  value={corpusName}
                  onChange={(e) => setCorpusName(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="e.g., GDPR, DPDP"
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                  disabled={loading}
                />
              </div>

              <div>
                <label htmlFor="sourceUrl" className="block text-sm font-medium text-slate-700 mb-2">
                  Source URL
                </label>
                <input
                  id="sourceUrl"
                  type="url"
                  value={sourceUrl}
                  onChange={(e) => setSourceUrl(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="https://example.com/document.pdf"
                  className="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                  disabled={loading}
                />
              </div>

              {error && (
                <div className="flex items-center gap-2 text-red-600 bg-red-50 p-3 rounded-lg">
                  <AlertCircle size={20} />
                  <span className="text-sm">{error}</span>
                </div>
              )}

              {status === 'success' && (
                <div className="flex items-center gap-2 text-green-600 bg-green-50 p-3 rounded-lg">
                  <CheckCircle size={20} />
                  <span className="text-sm">Corpus creation started successfully!</span>
                </div>
              )}

              <div className="flex gap-3 pt-4">
                <button
                  onClick={handleClose}
                  className="flex-1 px-4 py-2 border border-slate-300 text-slate-700 rounded-lg hover:bg-slate-50 transition-colors"
                  disabled={loading}
                >
                  Cancel
                </button>
                <button
                  onClick={handleSubmit}
                  disabled={loading}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors flex items-center justify-center gap-2 disabled:bg-blue-400 disabled:cursor-not-allowed"
                >
                  {loading ? (
                    <>
                      <Loader2 size={20} className="animate-spin" />
                      <span>Creating...</span>
                    </>
                  ) : (
                    <span>Create Corpus</span>
                  )}
                </button>
              </div>
            </div>

            <div className="mt-4 p-3 bg-blue-50 rounded-lg">
              <p className="text-xs text-blue-800">
                <strong>Note:</strong> This will start an asynchronous corpus creation process. The operation returns 202 Accepted immediately.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
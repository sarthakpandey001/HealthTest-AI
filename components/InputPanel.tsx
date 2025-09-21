import React, { useState, useRef } from 'react';
import { UploadIcon } from './icons/UploadIcon';
import { FileProcessingLoader } from './FileProcessingLoader';

interface InputPanelProps {
  requirementsInput: string;
  setRequirementsInput: (value: string) => void;
  openApiSchema: string;
  setOpenApiSchema: (value: string) => void;
  onGenerate: () => void;
  isLoading: boolean;
}

export const InputPanel: React.FC<InputPanelProps> = ({ 
    requirementsInput, 
    setRequirementsInput,
    openApiSchema,
    setOpenApiSchema,
    onGenerate, 
    isLoading
}) => {
  const [showSchemaInput, setShowSchemaInput] = useState(true);
  
  const [isDragging, setIsDragging] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isFileProcessing, setIsFileProcessing] = useState(false);

  const [isSchemaDragging, setIsSchemaDragging] = useState(false);
  const [schemaUploadError, setSchemaUploadError] = useState<string | null>(null);
  const schemaFileInputRef = useRef<HTMLInputElement>(null);

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  const readTextFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      setRequirementsInput(text);
      setIsFileProcessing(false);
    };
    reader.onerror = () => {
      setUploadError("Failed to read the selected file.");
      setIsFileProcessing(false);
    };
    reader.readAsText(file);
  };

  const readDocxFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const { default: mammoth } = await import('mammoth');
        const arrayBuffer = e.target?.result as ArrayBuffer;
        const result = await mammoth.extractRawText({ arrayBuffer });
        setRequirementsInput(result.value);
      } catch (error) {
        console.error("Failed to parse DOCX file:", error);
        setUploadError("Could not read the content of the DOCX file.");
      } finally {
        setIsFileProcessing(false);
      }
    };
    reader.onerror = () => {
      setUploadError("Failed to read the selected DOCX file.");
      setIsFileProcessing(false);
    };
    reader.readAsArrayBuffer(file);
  };

  const readPdfFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = async (e) => {
      try {
        const { getDocument, GlobalWorkerOptions } = await import('pdfjs-dist');
        GlobalWorkerOptions.workerSrc = `https://cdn.jsdelivr.net/npm/pdfjs-dist@4.4.168/build/pdf.worker.mjs`;
        
        const arrayBuffer = e.target?.result as ArrayBuffer;
        const loadingTask = getDocument({ data: arrayBuffer });
        const pdf = await loadingTask.promise;
        let fullText = '';
        for (let i = 1; i <= pdf.numPages; i++) {
          const page = await pdf.getPage(i);
          const textContent = await page.getTextContent();
          const pageText = textContent.items.map(item => 'str' in item ? item.str : '').join(' ');
          fullText += pageText + '\n';
        }
        setRequirementsInput(fullText.trim());
      } catch (error) {
        console.error("Failed to parse PDF file:", error);
        setUploadError("Could not read the content of the PDF file.");
      } finally {
        setIsFileProcessing(false);
      }
    };
    reader.onerror = () => {
      setUploadError("Failed to read the selected PDF file.");
      setIsFileProcessing(false);
    };
    reader.readAsArrayBuffer(file);
  };

  const handleFileSelect = (file?: File | null) => {
    if (!file) return;
    setUploadError(null);
    setIsFileProcessing(true);
    const fileName = file.name.toLowerCase();

    if (fileName.endsWith('.txt') || fileName.endsWith('.md') || fileName.endsWith('.json') || fileName.endsWith('.xml')) {
        readTextFile(file);
    } else if (fileName.endsWith('.docx')) {
        readDocxFile(file);
    } else if (fileName.endsWith('.pdf')) {
        readPdfFile(file);
    } else {
        setUploadError("Unsupported file type. Please use .txt, .md, .json, .xml, .docx, or .pdf.");
        setIsFileProcessing(false);
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    handleFileSelect(event.target.files?.[0]);
  };

  const handleDragEnter = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
  };
  
  const handleDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    handleFileSelect(event.dataTransfer.files?.[0]);
  };

  const handleSchemaUploadClick = () => {
    schemaFileInputRef.current?.click();
  };

  const readSchemaFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      setOpenApiSchema(text);
      setIsFileProcessing(false);
    };
    reader.onerror = () => {
      setSchemaUploadError("Failed to read the selected file.");
      setIsFileProcessing(false);
    };
    reader.readAsText(file);
  };

  const handleSchemaFileSelect = (file?: File | null) => {
    if (!file) return;
    setSchemaUploadError(null);
    setIsFileProcessing(true);
    const fileName = file.name.toLowerCase();

    if (fileName.endsWith('.yaml') || fileName.endsWith('.yml')) {
        readSchemaFile(file);
    } else {
        setSchemaUploadError("Unsupported file type. Please use .yaml or .yml.");
        setIsFileProcessing(false);
    }
  };
  
  const handleSchemaFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    handleSchemaFileSelect(event.target.files?.[0]);
  };
  
  const handleSchemaDragEnter = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsSchemaDragging(true);
  };

  const handleSchemaDragLeave = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsSchemaDragging(false);
  };
  
  const handleSchemaDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsSchemaDragging(false);
    handleSchemaFileSelect(event.dataTransfer.files?.[0]);
  };


  return (
    <div className="bg-white p-6 rounded-lg shadow-md space-y-4 h-full flex flex-col">
      <input 
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        style={{ display: 'none' }}
        accept=".txt,.md,.json,.xml,.docx,.pdf" 
      />
      <input 
        type="file"
        ref={schemaFileInputRef}
        onChange={handleSchemaFileChange}
        style={{ display: 'none' }}
        accept=".yaml,.yml" 
      />
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-bold text-slate-900">Input & Requirements</h2>
      </div>

      <button onClick={handleUploadClick} className="w-full flex items-center justify-center space-x-2 py-2 px-4 border border-slate-300 rounded-md hover:bg-slate-50 transition-colors text-sm font-medium text-slate-700" disabled={isLoading || isFileProcessing}>
        <UploadIcon className="h-5 w-5" />
        <span>Upload File</span>
      </button>

      <div 
        onDragEnter={handleDragEnter}
        onDragOver={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-slate-300'}`}
      >
        <p className="text-sm text-slate-500 pointer-events-none">Drag & drop files here</p>
      </div>
      {uploadError && <p className="text-xs text-red-600 text-center -mt-2">{uploadError}</p>}
      
      <div className="text-center text-xs text-slate-500">Or paste requirements below</div>

      <div className="flex-grow flex flex-col relative">
        {isFileProcessing && <FileProcessingLoader />}
        <textarea
          id="requirements-input"
          value={requirementsInput}
          onChange={(e) => setRequirementsInput(e.target.value)}
          placeholder="Paste requirements, upload a file, or drag & drop one above."
          className="w-full h-full flex-grow p-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-shadow text-sm bg-white text-black resize-y"
          disabled={isLoading || isFileProcessing}
          rows={10}
        />
      </div>

      <div className="border-t pt-4">
        <div className="flex justify-between items-center mb-2">
            <button 
              onClick={() => setShowSchemaInput(!showSchemaInput)}
              className="text-sm text-blue-600 font-semibold hover:underline"
              aria-expanded={showSchemaInput}
            >
              {showSchemaInput ? 'Hide' : 'Add'} OpenAPI Schema (Optional)
            </button>
            {showSchemaInput && (
              <button onClick={handleSchemaUploadClick} className="text-sm flex items-center space-x-1 text-slate-600 hover:text-blue-600 transition-colors" disabled={isLoading || isFileProcessing}>
                <UploadIcon className="h-4 w-4" />
                <span>Upload YAML</span>
              </button>
            )}
        </div>
        
        {showSchemaInput && (
           <div 
             onDragEnter={handleSchemaDragEnter}
             onDragOver={handleSchemaDragEnter}
             onDragLeave={handleSchemaDragLeave}
             onDrop={handleSchemaDrop}
             className={`relative border-2 border-dashed rounded-lg transition-colors ${isSchemaDragging ? 'border-blue-500 bg-blue-50' : 'border-transparent'}`}
           >
             {isFileProcessing && <FileProcessingLoader />}
             <textarea
                id="openapi-schema-input"
                value={openApiSchema}
                onChange={(e) => setOpenApiSchema(e.target.value)}
                placeholder="Paste schema, upload a YAML file, or drag & drop one here."
                className={`w-full p-3 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-shadow text-sm bg-white text-black resize-y ${isSchemaDragging ? 'pointer-events-none' : ''}`}
                disabled={isLoading || isFileProcessing}
                rows={8}
             />
              {isSchemaDragging && (
                <div className="absolute inset-0 bg-blue-50 bg-opacity-80 flex items-center justify-center pointer-events-none rounded-md">
                    <p className="text-sm font-semibold text-blue-600">Drop YAML file</p>
                </div>
             )}
           </div>
        )}
        {showSchemaInput && schemaUploadError && <p className="text-xs text-red-600 text-center mt-1">{schemaUploadError}</p>}
      </div>

      <button
        onClick={onGenerate}
        disabled={isLoading || isFileProcessing}
        className="w-full bg-blue-600 text-white font-semibold py-2.5 px-4 rounded-md hover:bg-blue-700 transition-colors disabled:bg-blue-300 disabled:cursor-not-allowed flex items-center justify-center"
      >
        {isLoading ? (
          <>
            <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Thinking...
          </>
        ) : (
          'Generate Test Cases'
        )}
      </button>
    </div>
  );
};
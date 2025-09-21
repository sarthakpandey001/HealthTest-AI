import React from 'react';
import { BoomerangIcon } from './icons/BoomerangIcon';

export const FileProcessingLoader: React.FC = () => {
  return (
    <div className="absolute inset-0 bg-white bg-opacity-80 flex flex-col justify-center items-center z-10 rounded-md">
      <BoomerangIcon className="animate-spin h-8 w-8 text-blue-600" />
      <p className="mt-2 text-sm font-semibold text-slate-700">Processing file...</p>
    </div>
  );
};

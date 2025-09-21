
import React from 'react';
import { SearchIcon } from './icons/SearchIcon';
import { FilterIcon } from './icons/FilterIcon';
import { SortIcon } from './icons/SortIcon';

export const TestCaseToolbar: React.FC = () => {
  return (
    <div className="flex flex-col sm:flex-row justify-between items-center space-y-2 sm:space-y-0">
      <div className="relative w-full sm:w-auto">
        <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
        <input 
          type="text" 
          placeholder="Search"
          className="pl-10 pr-4 py-2 w-full sm:w-64 border border-slate-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
        />
      </div>
      <div className="flex space-x-2">
        <button className="flex items-center space-x-2 py-2 px-4 border border-slate-300 rounded-md hover:bg-slate-50 transition-colors">
          <FilterIcon className="h-5 w-5 text-slate-500" />
          <span className="text-sm font-medium">Filter</span>
        </button>
        <button className="flex items-center space-x-2 py-2 px-4 border border-slate-300 rounded-md hover:bg-slate-50 transition-colors">
          <SortIcon className="h-5 w-5 text-slate-500" />
          <span className="text-sm font-medium">Sort</span>
        </button>
      </div>
    </div>
  );
};

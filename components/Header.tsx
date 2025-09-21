import React, { useState } from 'react';
import { LogoIcon } from './icons/LogoIcon';
import { UserIcon } from './icons/UserIcon';
import { HelpIcon } from './icons/HelpIcon';
import { User } from '../types';

interface HeaderProps {
  user: User;
  onLogout: () => void;
}

export const Header: React.FC<HeaderProps> = ({ user, onLogout }) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  return (
    <header className="bg-white shadow-sm w-full">
      <div className="mx-auto px-4 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-3">
            <LogoIcon className="h-8 w-8 text-blue-600" />
            <span className="text-xl font-bold text-slate-800">HealthTest AI</span>
          </div>
          <div className="relative">
            <div className="flex items-center space-x-4">
              <span className="text-sm font-medium text-slate-600 hidden sm:block">{user.email}</span>
              <button 
                onClick={() => setIsDropdownOpen(!isDropdownOpen)}
                className="p-2 rounded-full hover:bg-slate-100 transition-colors"
              >
                <UserIcon className="h-6 w-6 text-slate-600" />
              </button>
            </div>
            {isDropdownOpen && (
              <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50">
                <div className="px-4 py-2 text-sm text-slate-700 border-b">
                  Signed in as <br />
                  <span className="font-semibold">{user.email}</span>
                </div>
                <a
                  href="#"
                  onClick={(e) => {
                    e.preventDefault();
                    onLogout();
                    setIsDropdownOpen(false);
                  }}
                  className="block px-4 py-2 text-sm text-slate-700 hover:bg-slate-100"
                >
                  Logout
                </a>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};

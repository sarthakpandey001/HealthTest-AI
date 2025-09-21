
import React from 'react';

export const SortIcon: React.FC<React.SVGProps<SVGSVGElement>> = (props) => (
  <svg
    {...props}
    xmlns="http://www.w3.org/2000/svg"
    fill="none"
    viewBox="0 0 24 24"
    stroke="currentColor"
    strokeWidth={2}
  >
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M3 4h13M3 8h9M3 12h9m-9 4h13m0-4l-3-3m0 0l-3 3m3-3v12"
    />
  </svg>
);

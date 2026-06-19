import React from 'react';

interface DocMindLogoProps {
  className?: string;
  size?: number;
  gradientId?: string;
}

export const DocMindLogo: React.FC<DocMindLogoProps> = ({
  className = '',
  size = 24,
  gradientId = 'docmind-gradient',
}) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      <defs>
        <linearGradient id={gradientId} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#a78bfa" />
          <stop offset="100%" stopColor="#06b6d4" />
        </linearGradient>
      </defs>
      
      {/* Document outline path with folded corner */}
      <path
        d="M16 3H7.5C6.12 3 5 4.12 5 5.5V18.5C5 19.88 6.12 21 7.5 21H16.5C17.88 21 19 19.88 19 18.5V6L16 3Z"
        stroke={`url(#${gradientId})`}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M16 3V6H19"
        stroke={`url(#${gradientId})`}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />

      {/* Styled Brain network lines inside the document */}
      <path
        d="M10 10C8.5 10.5 8 11.5 8.5 12.5C9 13.5 10 13.5 10.5 14M14 10C15.5 10.5 16 11.5 15.5 12.5C15 13.5 14 13.5 13.5 14"
        stroke={`url(#${gradientId})`}
        strokeWidth="1"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      
      {/* Node connections (central synapses) */}
      <path
        d="M12 9V17M10 10.5L12 12.5L14 10.5M10.5 14L12 15.5L13.5 14"
        stroke={`url(#${gradientId})`}
        strokeWidth="1"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      
      {/* Small network connection nodes (circles) */}
      <circle cx="12" cy="9" r="0.75" fill={`url(#${gradientId})`} />
      <circle cx="10" cy="10.5" r="0.75" fill={`url(#${gradientId})`} />
      <circle cx="14" cy="10.5" r="0.75" fill={`url(#${gradientId})`} />
      <circle cx="12" cy="12.5" r="1.25" fill={`url(#${gradientId})`} />
      <circle cx="10.5" cy="14" r="0.75" fill={`url(#${gradientId})`} />
      <circle cx="13.5" cy="14" r="0.75" fill={`url(#${gradientId})`} />
      <circle cx="12" cy="17" r="0.75" fill={`url(#${gradientId})`} />
    </svg>
  );
};

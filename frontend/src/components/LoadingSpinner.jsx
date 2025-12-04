import React from 'react';

function LoadingSpinner({ size = 'default' }) {
  const sizeClasses = {
    small: 'w-4 h-4',
    default: 'w-6 h-6',
    large: 'w-12 h-12'
  };

  return (
    <div className="flex justify-center">
      <div className={`${sizeClasses[size]} animate-spin rounded-full border-b-2 border-primary-600`}></div>
    </div>
  );
}

export default LoadingSpinner;
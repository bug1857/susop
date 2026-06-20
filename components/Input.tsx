import React from "react";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  theme?: "light" | "dark";
}

export const Input: React.FC<InputProps> = ({ label, error, theme = "light", className = "", ...props }) => {
  const isDark = theme === "dark";
  const labelClass = isDark ? "text-text-muted font-semibold" : "text-gray-700";
  const bgClass = isDark ? "bg-card-bg text-foreground" : "bg-white text-gray-900";
  const textClass = "";
  const borderClass = error 
    ? "border-red-500" 
    : isDark 
      ? "border-border-color focus:border-indigo-500" 
      : "border-gray-300 focus:ring-blue-500";
  const placeholderClass = isDark ? "placeholder-text-muted" : "placeholder-gray-400";
  const focusRing = isDark ? "focus:ring-indigo-500" : "focus:ring-blue-500";

  return (
    <div className="w-full mb-4">
      {label && <label className={`block text-sm font-semibold mb-1 ${labelClass}`}>{label}</label>}
      <input
        className={`w-full px-3 py-2 border rounded-md text-sm focus:outline-none focus:ring-2 ${bgClass} ${textClass} ${borderClass} ${placeholderClass} ${focusRing} ${className}`}
        {...props}
      />
      {error && <p className="text-xs text-red-600 mt-1">{error}</p>}
    </div>
  );
};


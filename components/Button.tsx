import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger" | "outline";
}

export const Button: React.FC<ButtonProps> = ({ children, variant = "primary", className = "", ...props }) => {
  const baseStyle = "px-4 py-2 rounded-md font-medium text-sm transition-all focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed";
  
  const variants = {
    primary: "bg-blue-600 hover:bg-blue-700 text-white focus:ring-blue-500",
    secondary: "bg-gray-100 hover:bg-gray-200 text-gray-800 focus:ring-gray-300",
    outline: "border border-gray-300 bg-white hover:bg-gray-50 text-gray-700 focus:ring-blue-500",
    danger: "bg-red-600 hover:bg-red-700 text-white focus:ring-red-500",
  };

  return (
    <button
      className={`${baseStyle} ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

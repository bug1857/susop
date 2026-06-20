import React from "react";

interface CardProps {
  title?: string;
  children: React.ReactNode;
  className?: string;
}

export const Card: React.FC<CardProps> = ({ title, children, className = "" }) => {
  const hasBg = className.includes("bg-");
  const hasBorder = className.includes("border-");
  const bgClass = hasBg ? "" : "bg-card-bg";
  const borderClass = hasBorder ? "" : "border-border-color";

  return (
    <div className={`${bgClass} ${borderClass} border rounded-lg shadow-sm p-5 ${className}`}>
      {title && <h3 className="text-lg font-bold text-foreground border-b border-border-color pb-3 mb-4">{title}</h3>}
      {children}
    </div>
  );
};


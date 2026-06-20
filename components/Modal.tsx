import React from "react";
import { Button } from "./Button";

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export const Modal: React.FC<ModalProps> = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="bg-card-bg border border-border-color rounded-lg shadow-xl w-full max-w-md overflow-hidden">
        <div className="flex justify-between items-center px-5 py-4 border-b border-border-color">
          <h3 className="font-bold text-foreground text-lg">{title}</h3>
          <button onClick={onClose} className="text-text-muted hover:text-foreground text-xl font-bold transition-colors">&times;</button>
        </div>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
};


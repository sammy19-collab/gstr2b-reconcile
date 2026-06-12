import React from "react";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function Input({ label, error, className = "", id, ...props }: InputProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label htmlFor={id} className="text-sm font-medium text-gray-700">
          {label}
        </label>
      )}
      <input
        id={id}
        className={[
          "block w-full rounded-md border border-gray-300 px-3 py-2",
          "text-sm shadow-sm placeholder-gray-400",
          "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500",
          "disabled:bg-gray-100 disabled:cursor-not-allowed",
          error ? "border-red-500 focus:ring-red-500" : "",
          className,
        ].join(" ")}
        {...props}
      />
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}

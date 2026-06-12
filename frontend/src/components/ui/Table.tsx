import React from "react";

export function Table({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`overflow-x-auto ${className}`}>
      <table className="min-w-full divide-y divide-gray-200">{children}</table>
    </div>
  );
}

export function Thead({ children }: { children: React.ReactNode }) {
  return <thead className="bg-gray-50">{children}</thead>;
}

export function Tbody({ children }: { children: React.ReactNode }) {
  return <tbody className="bg-white divide-y divide-gray-200">{children}</tbody>;
}

export function Tr({
  children,
  className = "",
  onClick,
}: {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}) {
  return (
    <tr
      className={`${onClick ? "cursor-pointer hover:bg-gray-50" : ""} ${className}`}
      onClick={onClick}
    >
      {children}
    </tr>
  );
}

export function Th({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <th
      className={`px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider ${className}`}
    >
      {children}
    </th>
  );
}

export function Td({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <td className={`px-4 py-3 text-sm text-gray-700 whitespace-nowrap ${className}`}>
      {children}
    </td>
  );
}

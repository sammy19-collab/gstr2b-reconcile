import React, { useState } from "react";
import { Modal } from "../ui/Modal";
import { Button } from "../ui/Button";
import type { ColumnMappingDetect } from "../../types";

interface ColumnMappingModalProps {
  open: boolean;
  onClose: () => void;
  mapping: ColumnMappingDetect;
  onSave: (mapping: Record<string, string>) => void;
}

export function ColumnMappingModal({
  open,
  onClose,
  mapping,
  onSave,
}: ColumnMappingModalProps) {
  const [userMapping, setUserMapping] = useState<Record<string, string>>(
    () => ({ ...mapping.detected })
  );

  const handleFieldChange = (canonical: string, sourceCol: string) => {
    setUserMapping((prev) => ({ ...prev, [canonical]: sourceCol }));
  };

  const handleSave = () => {
    onSave(userMapping);
    onClose();
  };

  const allFields = [
    ...Object.keys(mapping.detected),
    ...mapping.unresolved,
  ];

  return (
    <Modal open={open} onClose={onClose} title="Column Mapping" size="lg">
      <div className="space-y-4">
        <p className="text-sm text-gray-600">
          Review and adjust the column mapping between your file columns and the canonical fields.
        </p>

        <div className="max-h-96 overflow-y-auto space-y-3">
          {allFields.map((canonical) => (
            <div key={canonical} className="flex items-center gap-4">
              <span className="w-48 text-sm font-medium text-gray-700 flex-shrink-0">
                {canonical}
              </span>
              <select
                className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm
                           focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={userMapping[canonical] ?? ""}
                onChange={(e) => handleFieldChange(canonical, e.target.value)}
              >
                <option value="">— unmapped —</option>
                {mapping.sample_columns.map((col) => (
                  <option key={col} value={col}>
                    {col}
                  </option>
                ))}
              </select>
              {mapping.unresolved.includes(canonical) && (
                <span className="text-xs text-red-500 flex-shrink-0">unresolved</span>
              )}
            </div>
          ))}
        </div>

        <div className="flex justify-end gap-3 pt-4 border-t">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave}>Save Mapping</Button>
        </div>
      </div>
    </Modal>
  );
}

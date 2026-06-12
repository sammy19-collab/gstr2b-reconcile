import React, { useState, useEffect } from "react";
import { getRunResults } from "../../api/endpoints";
import { Table, Thead, Tbody, Tr, Th, Td } from "../ui/Table";
import { Badge } from "../ui/Badge";
import { Button } from "../ui/Button";
import { CategoryFilter } from "./CategoryFilter";
import type { ResultRow, ResultsPage } from "../../types";

interface ResultsTableProps {
  runId: number;
}

const fmt = (v: unknown): string => {
  if (v === null || v === undefined) return "—";
  if (typeof v === "number") return v.toLocaleString("en-IN");
  return String(v);
};

export function ResultsTable({ runId }: ResultsTableProps) {
  const [page, setPage] = useState(1);
  const [category, setCategory] = useState<string | null>(null);
  const [data, setData] = useState<ResultsPage | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const fetch = async () => {
      setLoading(true);
      try {
        const res = await getRunResults(runId, page, 50, category ?? undefined);
        if (!cancelled) setData(res);
      } catch {
        // ignore
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    fetch();
    return () => { cancelled = true; };
  }, [runId, page, category]);

  const handleCategoryChange = (cat: string | null) => {
    setCategory(cat);
    setPage(1);
  };

  const totalPages = data ? Math.ceil(data.total / 50) : 0;

  return (
    <div className="space-y-4">
      <CategoryFilter selected={category} onChange={handleCategoryChange} />

      {loading && (
        <div className="text-center py-8 text-gray-500 text-sm">Loading results...</div>
      )}

      {!loading && data && (
        <>
          <div className="text-sm text-gray-500">
            Showing {data.items.length} of {data.total.toLocaleString()} results
          </div>

          <Table>
            <Thead>
              <Tr>
                <Th>Category</Th>
                <Th>Confidence</Th>
                <Th>PR Invoice No</Th>
                <Th>PR GSTIN</Th>
                <Th>PR Tax</Th>
                <Th>2B Invoice No</Th>
                <Th>2B GSTIN</Th>
                <Th>2B Tax</Th>
                <Th>Tax Delta</Th>
                <Th>Date Delta</Th>
              </Tr>
            </Thead>
            <Tbody>
              {data.items.map((row: ResultRow) => (
                <Tr key={row.id}>
                  <Td>
                    <Badge category={row.category} />
                  </Td>
                  <Td>
                    {row.confidence != null
                      ? `${Number(row.confidence).toFixed(0)}%`
                      : "—"}
                  </Td>
                  <Td>{fmt(row.purchase?.invoice_number)}</Td>
                  <Td>{fmt(row.purchase?.supplier_gstin)}</Td>
                  <Td>{fmt(row.purchase?.total_tax)}</Td>
                  <Td>{fmt(row.gstr2b?.invoice_number)}</Td>
                  <Td>{fmt(row.gstr2b?.supplier_gstin)}</Td>
                  <Td>{fmt(row.gstr2b?.total_tax)}</Td>
                  <Td
                    className={
                      row.tax_delta && Math.abs(Number(row.tax_delta)) > 0
                        ? "text-red-600 font-medium"
                        : ""
                    }
                  >
                    {row.tax_delta != null ? Number(row.tax_delta).toFixed(2) : "—"}
                  </Td>
                  <Td>{row.date_delta_days != null ? `${row.date_delta_days}d` : "—"}</Td>
                </Tr>
              ))}
            </Tbody>
          </Table>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <Button
                variant="secondary"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                Previous
              </Button>
              <span className="text-sm text-gray-600">
                Page {page} of {totalPages}
              </span>
              <Button
                variant="secondary"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

import { useState, useEffect, useRef } from "react";
import { getRun } from "../api/endpoints";
import type { ReconciliationRun } from "../types";

const TERMINAL_STATUSES = ["COMPLETED", "FAILED"];

export function useRun(runId: number | null): {
  run: ReconciliationRun | null;
  loading: boolean;
  error: string | null;
} {
  const [run, setRun] = useState<ReconciliationRun | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (runId === null) return;

    const fetchRun = async () => {
      try {
        setLoading(true);
        const data = await getRun(runId);
        setRun(data);

        if (TERMINAL_STATUSES.includes(data.status)) {
          if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
          }
        }
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Failed to fetch run status";
        setError(msg);
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      } finally {
        setLoading(false);
      }
    };

    fetchRun();
    intervalRef.current = setInterval(fetchRun, 2000);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [runId]);

  return { run, loading, error };
}

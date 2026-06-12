import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getClients } from "../api/endpoints";
import { Card, CardHeader, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { useAuth } from "../auth/AuthProvider";
import type { Client } from "../types";

export function Dashboard() {
  const { user, logout } = useAuth();
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getClients()
      .then(setClients)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top nav */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-16">
          <div className="flex items-center gap-6">
            <h1 className="text-xl font-bold text-gray-900">GST Reconcile AI</h1>
            <Link to="/clients" className="text-sm text-gray-600 hover:text-gray-900">
              Clients
            </Link>
            <Link to="/upload" className="text-sm text-gray-600 hover:text-gray-900">
              Upload
            </Link>
            <Link to="/reconcile" className="text-sm text-gray-600 hover:text-gray-900">
              Reconcile
            </Link>
            <Link to="/reports" className="text-sm text-gray-600 hover:text-gray-900">
              Reports
            </Link>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">{user?.email}</span>
            <Button variant="ghost" size="sm" onClick={logout}>
              Sign out
            </Button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <h2 className="text-2xl font-bold text-gray-900">Dashboard</h2>
          <div className="flex gap-3">
            <Link to="/upload">
              <Button size="sm">Upload Files</Button>
            </Link>
            <Link to="/reconcile">
              <Button size="sm" variant="secondary">
                Start Reconciliation
              </Button>
            </Link>
          </div>
        </div>

        {/* Quick stats */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardContent>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Total Clients</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">{clients.length}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Quick Actions</p>
              <div className="flex flex-col gap-2 mt-2">
                <Link to="/clients" className="text-sm text-blue-600 hover:underline">
                  Manage Clients →
                </Link>
                <Link to="/upload" className="text-sm text-blue-600 hover:underline">
                  Upload Data →
                </Link>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent>
              <p className="text-xs text-gray-500 uppercase tracking-wide">Getting Started</p>
              <ol className="mt-2 text-sm text-gray-600 list-decimal list-inside space-y-1">
                <li>Add a client</li>
                <li>Upload PR & 2B files</li>
                <li>Run reconciliation</li>
                <li>Download report</li>
              </ol>
            </CardContent>
          </Card>
        </div>

        {/* Clients list */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold text-gray-900">Your Clients</h3>
              <Link to="/clients">
                <Button variant="secondary" size="sm">
                  Manage
                </Button>
              </Link>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            {loading ? (
              <div className="p-6 text-center text-gray-500">Loading...</div>
            ) : clients.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                No clients yet.{" "}
                <Link to="/clients" className="text-blue-600 hover:underline">
                  Add your first client
                </Link>
              </div>
            ) : (
              <ul className="divide-y divide-gray-200">
                {clients.map((client) => (
                  <li key={client.id} className="px-6 py-4 flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">{client.name}</p>
                      <p className="text-sm text-gray-500">{client.gstin}</p>
                    </div>
                    <div className="flex gap-2">
                      <Link to={`/upload?client=${client.id}`}>
                        <Button variant="secondary" size="sm">
                          Upload
                        </Button>
                      </Link>
                      <Link to={`/reconcile?client=${client.id}`}>
                        <Button size="sm">Reconcile</Button>
                      </Link>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
}

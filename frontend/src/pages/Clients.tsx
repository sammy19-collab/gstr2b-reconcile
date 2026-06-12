import React, { useEffect, useState } from "react";
import { getClients, createClient, deleteClient } from "../api/endpoints";
import { Card, CardHeader, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { Modal } from "../components/ui/Modal";
import { Table, Thead, Tbody, Tr, Th, Td } from "../components/ui/Table";
import type { Client } from "../types";

export function Clients() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({
    name: "",
    gstin: "",
    pan: "",
    contact_email: "",
    contact_phone: "",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = async () => {
    setLoading(true);
    try {
      const data = await getClients();
      setClients(data);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    try {
      await createClient({
        name: form.name,
        gstin: form.gstin,
        pan: form.pan || undefined,
        contact_email: form.contact_email || undefined,
        contact_phone: form.contact_phone || undefined,
      });
      setShowModal(false);
      setForm({ name: "", gstin: "", pan: "", contact_email: "", contact_phone: "" });
      await load();
    } catch (err: unknown) {
      const msg =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Failed to create client";
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Delete this client? This cannot be undone.")) return;
    try {
      await deleteClient(id);
      setClients((prev) => prev.filter((c) => c.id !== id));
    } catch {
      alert("Failed to delete client");
    }
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Clients</h2>
        <Button onClick={() => setShowModal(true)}>Add Client</Button>
      </div>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-6 text-center text-gray-500">Loading...</div>
          ) : clients.length === 0 ? (
            <div className="p-6 text-center text-gray-500">
              No clients yet. Click "Add Client" to get started.
            </div>
          ) : (
            <Table>
              <Thead>
                <Tr>
                  <Th>Name</Th>
                  <Th>GSTIN</Th>
                  <Th>PAN</Th>
                  <Th>Email</Th>
                  <Th>Phone</Th>
                  <Th>Actions</Th>
                </Tr>
              </Thead>
              <Tbody>
                {clients.map((client) => (
                  <Tr key={client.id}>
                    <Td className="font-medium">{client.name}</Td>
                    <Td className="font-mono text-xs">{client.gstin}</Td>
                    <Td>{client.pan || "—"}</Td>
                    <Td>{client.contact_email || "—"}</Td>
                    <Td>{client.contact_phone || "—"}</Td>
                    <Td>
                      <Button
                        variant="danger"
                        size="sm"
                        onClick={() => handleDelete(client.id)}
                      >
                        Delete
                      </Button>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Modal open={showModal} onClose={() => setShowModal(false)} title="Add New Client">
        <form onSubmit={handleCreate} className="space-y-4">
          <Input
            label="Company Name *"
            value={form.name}
            onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
            required
          />
          <Input
            label="GSTIN *"
            value={form.gstin}
            onChange={(e) => setForm((f) => ({ ...f, gstin: e.target.value.toUpperCase() }))}
            maxLength={15}
            required
            placeholder="27AAPFU0939F1ZV"
          />
          <Input
            label="PAN"
            value={form.pan}
            onChange={(e) => setForm((f) => ({ ...f, pan: e.target.value.toUpperCase() }))}
            maxLength={10}
            placeholder="AAPFU0939F"
          />
          <Input
            label="Contact Email"
            type="email"
            value={form.contact_email}
            onChange={(e) => setForm((f) => ({ ...f, contact_email: e.target.value }))}
          />
          <Input
            label="Contact Phone"
            value={form.contact_phone}
            onChange={(e) => setForm((f) => ({ ...f, contact_phone: e.target.value }))}
          />

          {error && (
            <p className="text-sm text-red-600 bg-red-50 rounded px-3 py-2">{error}</p>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <Button variant="secondary" onClick={() => setShowModal(false)} type="button">
              Cancel
            </Button>
            <Button type="submit" loading={saving}>
              Create Client
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}

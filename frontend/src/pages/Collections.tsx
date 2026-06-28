import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { CollectionResponse } from '../services/types';
import { Folder, Plus, Trash2, Edit2, Loader2, FolderPlus, AlertCircle } from 'lucide-react';

const Collections: React.FC = () => {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newCollectionName, setNewCollectionName] = useState('');
  const [newCollectionDesc, setNewCollectionDesc] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Fetch Collections
  const { data: collections, isLoading } = useQuery<CollectionResponse[]>({
    queryKey: ['collections'],
    queryFn: async () => {
      const res = await api.get('/collections');
      return res.data;
    },
  });

  // Create Collection Mutation
  const createMutation = useMutation({
    mutationFn: async (payload: { name: string; description: string }) => {
      return await api.post('/collections', payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
      setShowCreateModal(false);
      setNewCollectionName('');
      setNewCollectionDesc('');
      setErrorMessage(null);
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail || "Failed to create collection.";
      setErrorMessage(detail);
    }
  });

  // Delete Collection Mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      return await api.delete(`/collections/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['collections'] });
    },
  });

  const handleCreate = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCollectionName.trim()) return;
    createMutation.mutate({
      name: newCollectionName,
      description: newCollectionDesc,
    });
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between border-b border-border pb-5">
        <div>
          <h1 className="font-outfit text-2xl font-bold tracking-tight text-foreground">Collections Workspace</h1>
          <p className="text-sm text-muted-foreground mt-1">Organize your document index aggregates into isolated workspaces.</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center space-x-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/95 transition-all shadow-md shadow-primary/20"
        >
          <Plus className="h-4 w-4" /> <span>New Collection</span>
        </button>
      </div>

      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      ) : collections && collections.length > 0 ? (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {collections.map((col) => (
            <div key={col.id} className="relative group rounded-xl border border-border bg-card p-6 shadow-sm hover:shadow-md hover:border-primary/20 transition-all duration-200">
              <div className="flex items-start justify-between">
                <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary">
                  <Folder className="h-6 w-6 text-primary" />
                </div>
                <button
                  onClick={() => deleteMutation.mutate(col.id)}
                  className="rounded-lg p-1.5 hover:bg-destructive/10 text-muted-foreground hover:text-destructive opacity-0 group-hover:opacity-100 transition-all"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>

              <div className="mt-4">
                <h3 className="text-base font-bold text-foreground line-clamp-1">{col.name}</h3>
                <p className="mt-1.5 text-xs text-muted-foreground line-clamp-2 h-8 leading-relaxed">
                  {col.description || 'No description provided.'}
                </p>
              </div>

              <div className="mt-6 flex items-center justify-between text-xs text-muted-foreground border-t border-border/50 pt-4">
                <span>Created: {new Date(col.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center py-20 border border-dashed border-border rounded-2xl bg-card/30">
          <FolderPlus className="h-12 w-12 text-muted-foreground/30" />
          <h3 className="mt-4 text-base font-bold text-foreground">No collections yet</h3>
          <p className="mt-1 text-xs text-muted-foreground">Create a collection workspace to upload and organize documents.</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="mt-6 inline-flex items-center space-x-2 rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/95 transition-all shadow-md shadow-primary/20"
          >
            <Plus className="h-4 w-4" /> <span>Get Started</span>
          </button>
        </div>
      )}

      {/* Create Modal Dialog */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="w-full max-w-md rounded-xl bg-card p-6 shadow-2xl border border-border">
            <h3 className="text-lg font-bold text-foreground font-outfit">Create Workspace Collection</h3>
            
            {errorMessage && (
              <div className="mt-4 flex items-start space-x-2 rounded-lg bg-destructive/10 border border-destructive/20 p-3 text-xs text-rose-400">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{errorMessage}</span>
              </div>
            )}

            <form onSubmit={handleCreate} className="mt-4 space-y-4">
              <div>
                <label className="block text-xs font-semibold text-muted-foreground">Collection Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Operating Systems"
                  value={newCollectionName}
                  onChange={(e) => setNewCollectionName(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-muted-foreground">Description (Optional)</label>
                <textarea
                  placeholder="Brief summary of contents"
                  value={newCollectionDesc}
                  onChange={(e) => setNewCollectionDesc(e.target.value)}
                  className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none"
                  rows={3}
                />
              </div>

              <div className="mt-6 flex justify-end space-x-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowCreateModal(false);
                    setErrorMessage(null);
                  }}
                  className="rounded-lg border border-border px-4 py-2 text-sm font-semibold text-muted-foreground hover:bg-muted"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="inline-flex items-center space-x-2 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/90"
                >
                  {createMutation.isPending && <Loader2 className="h-4 w-4 animate-spin" />}
                  <span>Create</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Collections;

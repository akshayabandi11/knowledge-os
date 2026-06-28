import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import api from '../services/api';
import { DocumentResponse, CollectionResponse } from '../services/types';
import {
  FileText,
  Upload,
  Trash2,
  Loader2,
  FilePlus2,
  AlertCircle,
  Clock,
  Sparkles,
  Info
} from 'lucide-react';

const Documents: React.FC = () => {
  const queryClient = useQueryClient();
  const [selectedCollection, setSelectedCollection] = useState<string>('');
  const [uploadProgress, setUploadProgress] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Load collections
  const { data: collections } = useQuery<CollectionResponse[]>({
    queryKey: ['collections'],
    queryFn: async () => {
      const res = await api.get('/collections');
      return res.data;
    },
  });

  // Load documents
  const { data: documents, isLoading } = useQuery<DocumentResponse[]>({
    queryKey: ['documents'],
    queryFn: async () => {
      const res = await api.get('/documents');
      return res.data;
    },
    refetchInterval: 5000, // Poll every 5s to update parsing status in real-time
  });

  // Delete Mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      return await api.delete(`/documents/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  // Upload handler
  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    setErrorMessage(null);
    if (!selectedCollection) {
      setErrorMessage("Please select a target collection before uploading.");
      return;
    }
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const file = files[0];
    const formData = new FormData();
    formData.append('file', file);

    setUploadProgress(10);
    try {
      await api.post(`/documents/upload/${selectedCollection}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        onUploadProgress: (progressEvent) => {
          if (progressEvent.total) {
            const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
            setUploadProgress(percent);
          }
        }
      });
      setUploadProgress(100);
      setTimeout(() => setUploadProgress(null), 1000);
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    } catch (err: any) {
      setUploadProgress(null);
      const detail = err.response?.data?.detail || "Upload failed. Verify file limits (max 10MB).";
      setErrorMessage(detail);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'PENDING':
        return <span className="inline-flex items-center rounded-full bg-blue-500/10 px-2 py-1 text-xs font-semibold text-blue-500 animate-pulse">Pending</span>;
      case 'PARSED':
        return <span className="inline-flex items-center rounded-full bg-violet-500/10 px-2 py-1 text-xs font-semibold text-violet-500">Parsed</span>;
      case 'EMBEDDED':
        return <span className="inline-flex items-center rounded-full bg-emerald-500/10 px-2 py-1 text-xs font-semibold text-emerald-500">Embedded</span>;
      case 'FAILED':
        return <span className="inline-flex items-center rounded-full bg-rose-500/10 px-2 py-1 text-xs font-semibold text-rose-500">Failed</span>;
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="border-b border-border pb-5">
        <h1 className="font-outfit text-2xl font-bold tracking-tight text-foreground">Documents Manager</h1>
        <p className="text-sm text-muted-foreground mt-1">Upload and review files processed into your semantic RAG search index.</p>
      </div>

      {errorMessage && (
        <div className="flex items-start space-x-2 rounded-xl bg-destructive/10 border border-destructive/20 p-3.5 text-xs text-rose-400">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Upload Zone & Select target */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Select Collection & File Upload */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm space-y-4">
          <h3 className="font-outfit text-base font-bold">Ingestion Control</h3>
          <div>
            <label className="block text-xs font-semibold text-muted-foreground">Select Target Collection</label>
            <select
              value={selectedCollection}
              onChange={(e) => setSelectedCollection(e.target.value)}
              className="mt-1.5 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none"
            >
              <option value="">-- Choose Collection --</option>
              {collections?.map((col) => (
                <option key={col.id} value={col.id}>{col.name}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-muted-foreground">Upload Document (PDF, DOCX, TXT, Images)</label>
            <div className="mt-1.5 flex justify-center rounded-lg border-2 border-dashed border-border px-6 py-8 hover:border-primary/50 transition-colors relative">
              <div className="space-y-1 text-center">
                <Upload className="mx-auto h-10 w-10 text-muted-foreground/40" />
                <div className="flex text-xs text-muted-foreground">
                  <label className="relative cursor-pointer rounded-md font-semibold text-primary hover:text-primary/90">
                    <span>Upload a file</span>
                    <input
                      type="file"
                      className="sr-only"
                      onChange={handleUpload}
                      disabled={!selectedCollection}
                    />
                  </label>
                  <p className="pl-1">or drag and drop</p>
                </div>
                <p className="text-[10px] text-muted-foreground/60">PDF, DOCX, PPTX, TXT or PNG/JPG (Max 10MB)</p>
              </div>
            </div>
          </div>

          {uploadProgress !== null && (
            <div className="space-y-1">
              <div className="flex items-center justify-between text-xs font-semibold text-primary">
                <span>Uploading...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                <div className="h-full bg-primary transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
              </div>
            </div>
          )}
        </div>

        {/* Documents Listing Pane */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm lg:col-span-2 space-y-4">
          <h3 className="font-outfit text-base font-bold">Processed Files</h3>
          {isLoading ? (
            <div className="flex h-40 items-center justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : documents && documents.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-muted-foreground">
                <thead className="text-xs font-semibold text-foreground uppercase border-b border-border/50">
                  <tr>
                    <th className="py-3 px-2">Name</th>
                    <th className="py-3 px-2">Size</th>
                    <th className="py-3 px-2">Pages</th>
                    <th className="py-3 px-2">Status</th>
                    <th className="py-3 px-2 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/50 text-foreground">
                  {documents.map((doc) => (
                    <tr key={doc.id} className="hover:bg-muted/10 transition-colors">
                      <td className="py-3.5 px-2 flex items-center space-x-2">
                        <FileText className="h-4.5 w-4.5 text-primary shrink-0" />
                        <span className="font-medium truncate max-w-[200px]">{doc.name}</span>
                      </td>
                      <td className="py-3.5 px-2 text-xs text-muted-foreground">
                        {(doc.file_size / (1024 * 1024)).toFixed(2)} MB
                      </td>
                      <td className="py-3.5 px-2 text-xs text-muted-foreground">
                        {doc.page_count || '-'}
                      </td>
                      <td className="py-3.5 px-2">
                        {getStatusBadge(doc.status)}
                      </td>
                      <td className="py-3.5 px-2 text-right">
                        <button
                          onClick={() => deleteMutation.mutate(doc.id)}
                          className="rounded-lg p-1.5 hover:bg-destructive/10 text-muted-foreground hover:text-destructive"
                        >
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <FilePlus2 className="h-10 w-10 text-muted-foreground/30" />
              <p className="mt-2 text-xs font-medium text-muted-foreground">No documents uploaded yet.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Documents;

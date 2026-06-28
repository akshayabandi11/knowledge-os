import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import { CollectionResponse, DocumentResponse } from '../services/types';
import {
  FileText,
  Folder,
  Cpu,
  Coins,
  History,
  TrendingUp,
  PlusCircle,
  FilePlus,
  MessageSquarePlus,
  ChevronRight,
  Database
} from 'lucide-react';
import { Link } from 'react-router-dom';

const Dashboard: React.FC = () => {
  const { user } = useAuth();

  // Load collections
  const { data: collections } = useQuery<CollectionResponse[]>({
    queryKey: ['collections'],
    queryFn: async () => {
      const res = await api.get('/collections');
      return res.data;
    },
  });

  // Load documents
  const { data: documents } = useQuery<DocumentResponse[]>({
    queryKey: ['documents'],
    queryFn: async () => {
      const res = await api.get('/documents');
      return res.data;
    },
  });

  // Aggregate statistics
  const totalDocs = documents?.length || 0;
  const totalCollections = collections?.length || 0;
  const storageUsedMB = documents
    ? (documents.reduce((acc, doc) => acc + doc.file_size, 0) / (1024 * 1024)).toFixed(2)
    : '0.00';

  const stats = [
    { name: 'Total Collections', value: totalCollections, icon: Folder, color: 'text-blue-500 bg-blue-500/10' },
    { name: 'Documents Indexed', value: totalDocs, icon: FileText, color: 'text-violet-500 bg-violet-500/10' },
    { name: 'AI Models Active', value: 'Gemini 1.5', icon: Cpu, color: 'text-emerald-500 bg-emerald-500/10' },
    { name: 'Storage Utilized', value: `${storageUsedMB} MB`, icon: Database, color: 'text-amber-500 bg-amber-500/10' },
  ];

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Welcome Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-primary to-violet-600 p-8 text-primary-foreground shadow-xl relative overflow-hidden">
        <div className="absolute top-0 right-0 h-40 w-40 rounded-full bg-white/10 blur-2xl translate-x-10 -translate-y-10" />
        <h1 className="font-outfit text-3xl font-bold tracking-tight">
          Welcome back, {user?.full_name || user?.email.split('@')[0]}
        </h1>
        <p className="mt-2 max-w-xl text-primary-foreground/80 text-sm">
          KnowledgeOS has processed your workspace details. Upload PDFs, ask questions, or run comparisons using the RAG Chat interface.
        </p>
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.name} className="rounded-xl border border-border bg-card p-6 shadow-sm hover:shadow-md transition-all duration-200">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">{stat.name}</p>
                  <p className="mt-2 font-outfit text-2xl font-bold text-foreground">{stat.value}</p>
                </div>
                <div className={`rounded-xl p-3 ${stat.color}`}>
                  <Icon className="h-6 w-6" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Core Grid */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Recent Workspaces */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm space-y-4 lg:col-span-2">
          <div className="flex items-center justify-between">
            <h3 className="font-outfit text-lg font-bold">Recent Collections</h3>
            <Link to="/collections" className="flex items-center text-xs text-primary hover:underline font-semibold">
              Manage Collections <ChevronRight className="ml-1 h-3 w-3" />
            </Link>
          </div>
          {collections && collections.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {collections.slice(0, 4).map((col) => (
                <div key={col.id} className="group rounded-xl border border-border/50 bg-muted/20 p-4 hover:border-primary/30 transition-all duration-200">
                  <div className="flex items-center space-x-3">
                    <Folder className="h-6 w-6 text-primary" />
                    <div>
                      <h4 className="text-sm font-bold text-foreground group-hover:text-primary transition-colors">{col.name}</h4>
                      <p className="text-xs text-muted-foreground line-clamp-1 mt-0.5">{col.description || 'No description provided.'}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <Folder className="h-10 w-10 text-muted-foreground/30" />
              <p className="mt-2 text-xs font-medium text-muted-foreground">No collections created yet.</p>
              <Link to="/collections" className="mt-4 inline-flex items-center space-x-2 text-xs font-semibold text-primary hover:underline">
                <PlusCircle className="h-4 w-4" /> <span>Create collection</span>
              </Link>
            </div>
          )}
        </div>

        {/* Quick Actions Panel */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm space-y-4">
          <h3 className="font-outfit text-lg font-bold">Quick Actions</h3>
          <div className="space-y-3">
            <Link to="/chat" className="flex w-full items-center justify-between rounded-xl border border-border p-3.5 hover:border-primary/30 hover:bg-muted/10 transition-all">
              <div className="flex items-center space-x-3">
                <MessageSquarePlus className="h-5 w-5 text-primary" />
                <span className="text-sm font-semibold">New RAG Chat</span>
              </div>
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            </Link>
            <Link to="/documents" className="flex w-full items-center justify-between rounded-xl border border-border p-3.5 hover:border-primary/30 hover:bg-muted/10 transition-all">
              <div className="flex items-center space-x-3">
                <FilePlus className="h-5 w-5 text-violet-500" />
                <span className="text-sm font-semibold">Upload Documents</span>
              </div>
              <ChevronRight className="h-4 w-4 text-muted-foreground" />
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

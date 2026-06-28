import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuth } from '../contexts/AuthContext';
import api from '../services/api';
import { SessionResponse } from '../services/types';
import { Settings as SettingsIcon, Shield, Sliders, Smartphone, Laptop, Trash2, Loader2, AlertCircle, CheckCircle } from 'lucide-react';

const Settings: React.FC = () => {
  const { user, updateUser, logoutAll } = useAuth();
  const queryClient = useQueryClient();
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [updateSuccess, setUpdateSuccess] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Model settings state
  const [model, setModel] = useState('gemini-1.5-flash');
  const [temp, setTemp] = useState(0.2);
  const [maxTokens, setMaxTokens] = useState(2048);

  // Fetch active sessions
  const { data: sessions, isLoading: sessionsLoading } = useQuery<SessionResponse[]>({
    queryKey: ['sessions'],
    queryFn: async () => {
      const res = await api.get('/sessions');
      return res.data;
    },
  });

  // Revoke session mutation
  const revokeMutation = useMutation({
    mutationFn: async (id: string) => {
      return await api.delete(`/sessions/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
    },
  });

  const handleProfileSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);
    setUpdateSuccess(false);
    try {
      await updateUser(fullName);
      setUpdateSuccess(true);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || "Failed to update profile.");
    }
  };

  return (
    <div className="space-y-8 animate-fade-in max-w-4xl">
      <div className="border-b border-border pb-5">
        <h1 className="font-outfit text-2xl font-bold tracking-tight text-foreground">Workspace Settings</h1>
        <p className="text-sm text-muted-foreground mt-1">Configure profile details, default AI model values, and manage active browser sessions.</p>
      </div>

      {updateSuccess && (
        <div className="flex items-center space-x-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 p-3.5 text-xs text-emerald-400">
          <CheckCircle className="h-4.5 w-4.5 shrink-0" />
          <span>Profile configuration saved successfully.</span>
        </div>
      )}

      {errorMessage && (
        <div className="flex items-start space-x-2 rounded-xl bg-destructive/10 border border-destructive/20 p-3.5 text-xs text-rose-400">
          <AlertCircle className="h-4.5 w-4.5 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Grid Settings */}
      <div className="grid grid-cols-1 gap-8 md:grid-cols-2">
        {/* Profile Card */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm space-y-4">
          <h3 className="font-outfit text-base font-bold flex items-center space-x-2">
            <SettingsIcon className="h-5 w-5 text-primary" /> <span>Profile Details</span>
          </h3>
          <form onSubmit={handleProfileSave} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-muted-foreground">Email Address (Primary)</label>
              <input
                type="email"
                disabled
                value={user?.email || ''}
                className="mt-1 w-full rounded-lg border border-border bg-muted/30 px-3 py-2 text-sm text-muted-foreground cursor-not-allowed focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-muted-foreground">Display Name</label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="mt-1 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:border-primary focus:outline-none"
              />
            </div>
            <button
              type="submit"
              className="rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground hover:bg-primary/95 transition-all shadow-md shadow-primary/20"
            >
              Save Profile
            </button>
          </form>
        </div>

        {/* Model Configurations */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm space-y-4">
          <h3 className="font-outfit text-base font-bold flex items-center space-x-2">
            <Sliders className="h-5 w-5 text-violet-500" /> <span>AI Inference Tuning</span>
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-muted-foreground">Preferred AI Model</label>
              <select
                value={model}
                onChange={(e) => setModel(e.target.value)}
                className="mt-1.5 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground focus:outline-none"
              >
                <option value="gemini-1.5-flash">Gemini 1.5 Flash (Default - Fast)</option>
                <option value="gemini-1.5-pro">Gemini 1.5 Pro (High Reasoning)</option>
              </select>
            </div>
            <div>
              <div className="flex justify-between text-xs font-semibold text-muted-foreground">
                <span>Temperature</span>
                <span>{temp}</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={temp}
                onChange={(e) => setTemp(parseFloat(e.target.value))}
                className="mt-2 w-full h-1 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Active Device Sessions */}
      <div className="rounded-xl border border-border bg-card p-6 shadow-sm space-y-6">
        <div className="flex items-center justify-between border-b border-border/50 pb-4">
          <h3 className="font-outfit text-base font-bold flex items-center space-x-2">
            <Shield className="h-5 w-5 text-emerald-500" /> <span>Active Devices & Sessions</span>
          </h3>
          <button
            onClick={() => logoutAll()}
            className="rounded-lg border border-destructive/20 hover:bg-destructive/10 px-3.5 py-1.5 text-xs font-semibold text-destructive transition-all"
          >
            Revoke All Sessions
          </button>
        </div>

        {sessionsLoading ? (
          <div className="flex h-20 items-center justify-center">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
          </div>
        ) : (
          <div className="divide-y divide-border/50">
            {sessions?.map((sess) => (
              <div key={sess.id} className="flex items-center justify-between py-4">
                <div className="flex items-center space-x-4">
                  <div className="rounded-lg bg-muted p-2.5">
                    {sess.operating_system?.toLowerCase().includes('windows') ? (
                      <Laptop className="h-5 w-5 text-muted-foreground" />
                    ) : (
                      <Smartphone className="h-5 w-5 text-muted-foreground" />
                    )}
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-foreground">
                      {sess.browser || 'Unknown Browser'} on {sess.operating_system || 'Unknown OS'}
                    </h4>
                    <p className="text-xs text-muted-foreground mt-0.5">
                      IP Address: {sess.ip_address} • Last active: {new Date(sess.last_activity).toLocaleString()}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => revokeMutation.mutate(sess.id)}
                  className="rounded-lg p-2 hover:bg-destructive/10 text-muted-foreground hover:text-destructive transition-all"
                >
                  <Trash2 className="h-4.5 w-4.5" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Settings;

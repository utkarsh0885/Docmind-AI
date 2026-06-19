import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Cpu, Sliders, Shield, AlertCircle } from 'lucide-react';
import axios from 'axios';

interface BackendHealthInfo {
  status: string;
  llm_provider: string;
  allowed_extensions: string[];
}

// Skeleton loader for settings cards
const SettingsSkeleton: React.FC = () => (
  <div className="space-y-6">
    {[1, 2, 3].map((i) => (
      <div key={i} className="rounded-xl bg-surface-900/40 border border-surface-800/60 p-6 space-y-4">
        <div className="flex items-center gap-3">
          <div className="h-5 w-5 rounded skeleton" />
          <div className="h-4 w-36 rounded skeleton" />
        </div>
        <div className="grid grid-cols-2 gap-6">
          <div className="space-y-2">
            <div className="h-2.5 w-20 rounded skeleton" />
            <div className="h-4 w-32 rounded skeleton" />
          </div>
          <div className="space-y-2">
            <div className="h-2.5 w-24 rounded skeleton" />
            <div className="h-4 w-40 rounded skeleton" />
          </div>
        </div>
      </div>
    ))}
  </div>
);

export const SettingsPage: React.FC = () => {
  const [healthInfo, setHealthInfo] = useState<BackendHealthInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchSettings = async () => {
      setLoading(true);
      setError(null);
      try {
        const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        const response = await axios.get(`${API_URL}/api/health`);
        setHealthInfo(response.data);
      } catch (err: any) {
        setError(
          'Could not connect to backend API. Make sure the FastAPI server is running.'
        );
      } finally {
        setLoading(false);
      }
    };
    fetchSettings();
  }, []);

  const SettingRow: React.FC<{ label: string; value: React.ReactNode }> = ({ label, value }) => (
    <div>
      <span className="block text-2xs text-surface-500 font-medium uppercase tracking-wider">{label}</span>
      <span className="block mt-1 text-sm font-semibold text-surface-200">{value}</span>
    </div>
  );

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden">
      {/* Page header */}
      <div className="flex items-center px-6 sm:px-8 h-14 border-b border-surface-800/60 shrink-0">
        <div>
          <h1 className="text-sm font-semibold text-surface-100">Settings</h1>
          <p className="text-2xs text-surface-500 -mt-0.5">Runtime configuration and status</p>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        <div className="max-w-2xl mx-auto px-4 sm:px-6 py-6 space-y-5">
          {loading ? (
            <SettingsSkeleton />
          ) : error ? (
            <motion.div
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-3 p-4 rounded-xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm"
            >
              <AlertCircle className="h-5 w-5 shrink-0" />
              <span className="text-xs font-medium">{error}</span>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              className="space-y-5"
            >
              {/* Model Config */}
              <div className="rounded-xl bg-surface-900/40 border border-surface-800/60 overflow-hidden">
                <div className="flex items-center gap-3 px-5 py-3.5 border-b border-surface-800/60">
                  <Cpu className="h-4 w-4 text-accent-400" />
                  <h3 className="text-sm font-semibold text-surface-200">Model Configuration</h3>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 p-5">
                  <SettingRow
                    label="LLM Provider"
                    value={
                      <span className="capitalize">
                        {healthInfo?.llm_provider || 'Not configured'}
                      </span>
                    }
                  />
                  <SettingRow
                    label="Chat Model"
                    value={
                      healthInfo?.llm_provider === 'google'
                        ? 'Gemini (Google AI)'
                        : healthInfo?.llm_provider === 'openai'
                        ? 'GPT-4o Mini (OpenAI)'
                        : 'Unknown'
                    }
                  />
                </div>
              </div>

              {/* Ingestion Config */}
              <div className="rounded-xl bg-surface-900/40 border border-surface-800/60 overflow-hidden">
                <div className="flex items-center gap-3 px-5 py-3.5 border-b border-surface-800/60">
                  <Sliders className="h-4 w-4 text-accent-400" />
                  <h3 className="text-sm font-semibold text-surface-200">Ingestion Settings</h3>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 p-5">
                  <SettingRow label="Chunk Size" value="1,000 characters" />
                  <SettingRow label="Overlap Window" value="200 characters" />
                  <SettingRow
                    label="Allowed Formats"
                    value={
                      <span className="font-mono text-xs">
                        {healthInfo?.allowed_extensions?.join(', ') || '.pdf, .txt, .md'}
                      </span>
                    }
                  />
                  <SettingRow label="Vector Database" value="ChromaDB (Local)" />
                </div>
              </div>

              {/* Security */}
              <div className="rounded-xl bg-surface-900/40 border border-surface-800/60 overflow-hidden">
                <div className="flex items-center gap-3 px-5 py-3.5 border-b border-surface-800/60">
                  <Shield className="h-4 w-4 text-accent-400" />
                  <h3 className="text-sm font-semibold text-surface-200">Security & Environment</h3>
                </div>
                <div className="divide-y divide-surface-800/40">
                  {[
                    { label: 'CORS Policy', value: 'Enabled', color: 'text-emerald-400' },
                    { label: 'SSL Encryption', value: 'Disabled (localhost)', color: 'text-surface-500' },
                    { label: 'File Retention', value: 'Persistent', color: 'text-amber-400' },
                  ].map((row) => (
                    <div key={row.label} className="flex items-center justify-between px-5 py-3">
                      <span className="text-xs text-surface-400">{row.label}</span>
                      <span className={`text-2xs font-bold uppercase tracking-wider ${row.color}`}>
                        {row.value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </div>
      </div>
    </div>
  );
};

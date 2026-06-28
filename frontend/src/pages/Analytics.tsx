import React from 'react';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { Cpu, Timer, Database, Coins, TrendingUp } from 'lucide-react';

const mockDailyUsage = [
  { day: 'Mon', tokens: 12000, cost: 0.05, latency: 450 },
  { day: 'Tue', tokens: 19000, cost: 0.08, latency: 420 },
  { day: 'Wed', tokens: 15000, cost: 0.06, latency: 480 },
  { day: 'Thu', tokens: 27000, cost: 0.12, latency: 390 },
  { day: 'Fri', tokens: 22000, cost: 0.10, latency: 410 },
  { day: 'Sat', tokens: 8000, cost: 0.03, latency: 380 },
  { day: 'Sun', tokens: 11000, cost: 0.04, latency: 400 },
];

const mockModelUsage = [
  { name: 'Gemini 1.5 Flash', value: 75, color: '#6366f1' },
  { name: 'Gemini 1.5 Pro', value: 25, color: '#a855f7' },
];

const Analytics: React.FC = () => {
  return (
    <div className="space-y-8 animate-fade-in">
      <div className="border-b border-border pb-5">
        <h1 className="font-outfit text-2xl font-bold tracking-tight text-foreground">Usage & Analytics</h1>
        <p className="text-sm text-muted-foreground mt-1">Monitor token consumption, prompt latency, and estimated cloud costs.</p>
      </div>

      {/* Analytics Summary Stats */}
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center space-x-4">
            <div className="rounded-lg bg-primary/10 p-3 text-primary">
              <TrendingUp className="h-6 w-6" />
            </div>
            <div>
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">Weekly Tokens</span>
              <h3 className="font-outfit text-2xl font-bold text-foreground mt-1">134,000</h3>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center space-x-4">
            <div className="rounded-lg bg-emerald-500/10 p-3 text-emerald-500">
              <Coins className="h-6 w-6" />
            </div>
            <div>
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">Estimated Costs</span>
              <h3 className="font-outfit text-2xl font-bold text-foreground mt-1">$0.48</h3>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-6 shadow-sm">
          <div className="flex items-center space-x-4">
            <div className="rounded-lg bg-amber-500/10 p-3 text-amber-500">
              <Timer className="h-6 w-6" />
            </div>
            <div>
              <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider block">Avg Latency</span>
              <h3 className="font-outfit text-2xl font-bold text-foreground mt-1">418 ms</h3>
            </div>
          </div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Token Consumption Area Chart */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm lg:col-span-2 space-y-4">
          <h3 className="font-outfit text-base font-bold">Token Consumption Timeline</h3>
          <div className="h-72 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={mockDailyUsage}>
                <defs>
                  <linearGradient id="colorTokens" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#6366f1" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(100,116,139,0.1)" />
                <XAxis dataKey="day" stroke="#94a3b8" fontSize={11} tickLine={false} />
                <YAxis stroke="#94a3b8" fontSize={11} tickLine={false} />
                <Tooltip />
                <Area type="monotone" dataKey="tokens" stroke="#6366f1" strokeWidth={2} fillOpacity={1} fill="url(#colorTokens)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Model Usage Pie Chart */}
        <div className="rounded-xl border border-border bg-card p-6 shadow-sm space-y-4 flex flex-col justify-between">
          <h3 className="font-outfit text-base font-bold">Model Splits</h3>
          <div className="h-52 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={mockModelUsage}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {mockModelUsage.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="space-y-2 mt-4">
            {mockModelUsage.map((m) => (
              <div key={m.name} className="flex items-center justify-between text-xs">
                <div className="flex items-center space-x-2">
                  <div className="h-3 w-3 rounded-full" style={{ backgroundColor: m.color }} />
                  <span className="text-muted-foreground">{m.name}</span>
                </div>
                <span className="font-semibold text-foreground">{m.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analytics;

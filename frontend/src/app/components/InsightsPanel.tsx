import { TrendingUp, Flame, Database } from 'lucide-react';
import { useEffect, useState } from 'react';
import { fetchStats, type StatsResponse } from '../../lib/api';

export function InsightsPanel() {
  const [stats, setStats] = useState<StatsResponse | null>(null);

  useEffect(() => {
    fetchStats().then(setStats).catch(() => null);
    const interval = setInterval(() => fetchStats().then(setStats).catch(() => null), 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="w-80 border-l border-border bg-white h-full overflow-y-auto">
      <div className="p-6 space-y-6">
        <div>
          <h3 className="text-[#1E3A8A] mb-1">Legal Insights</h3>
          <p className="text-sm text-muted-foreground">Trending topics and popular queries</p>
        </div>

        {/* Trending Topics */}
        {stats && stats.trending_topics.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Flame className="w-4 h-4" />
              <span>Trending Topics</span>
            </div>
            <div className="space-y-2">
              {stats.trending_topics.slice(0, 3).map((topic, i) => (
                <div
                  key={i}
                  className="bg-gradient-to-br from-orange-50 to-red-50 border border-orange-200 rounded-xl p-3"
                >
                  <div className="text-sm text-orange-800 capitalize">{topic}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Top Laws */}
        {stats && stats.top_laws.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <TrendingUp className="w-4 h-4" />
              <span>Most Indexed Laws</span>
            </div>
            <div className="space-y-2">
              {stats.top_laws.slice(0, 3).map((law, i) => (
                <div
                  key={i}
                  className="bg-gradient-to-br from-[#14B8A6]/10 to-[#14B8A6]/20 border border-[#14B8A6]/30 rounded-xl p-3 flex items-center gap-2"
                >
                  <span className="text-sm text-[#14B8A6]">{law}</span>
                  {i === 0 && (
                    <span className="ml-auto flex h-5 px-2 items-center text-xs bg-[#14B8A6] text-white rounded-full">Top</span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Stats */}
        <div className="space-y-3">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Database className="w-4 h-4" />
            <span>Database Stats</span>
          </div>
          <div className="space-y-2">
            <div className="flex items-center justify-between p-3 bg-accent rounded-lg">
              <span className="text-sm text-foreground">Law Sections</span>
              <span className="text-sm text-[#1E3A8A]">
                {stats ? stats.total_laws_indexed.toLocaleString() : '—'}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-accent rounded-lg">
              <span className="text-sm text-foreground">Case Laws</span>
              <span className="text-sm text-[#1E3A8A]">
                {stats ? stats.total_cases_processed.toLocaleString() : '—'}
              </span>
            </div>
            <div className="flex items-center justify-between p-3 bg-accent rounded-lg">
              <span className="text-sm text-foreground">Acts Covered</span>
              <span className="text-sm text-[#1E3A8A]">8</span>
            </div>
          </div>
          {stats && (
            <p className="text-xs text-muted-foreground">
              Updated {new Date(stats.updated_at).toLocaleTimeString()}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

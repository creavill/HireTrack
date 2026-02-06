import React, { useState, useEffect } from 'react';
import { Trophy, Flame, Target, Star, TrendingUp, Award, Zap } from 'lucide-react';

// Compact gamification widget for sidebar
export function GamificationWidget({ onClick }) {
  const [stats, setStats] = useState(null);
  const [dailyGoals, setDailyGoals] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchGamificationData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchGamificationData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchGamificationData = async () => {
    try {
      const [statsRes, goalsRes] = await Promise.all([
        fetch('/api/gamification/stats'),
        fetch('/api/gamification/daily-goals')
      ]);

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }

      if (goalsRes.ok) {
        const goalsData = await goalsRes.json();
        setDailyGoals(goalsData);
      }
    } catch (err) {
      console.error('Failed to fetch gamification data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-3 animate-pulse">
        <div className="h-4 bg-white/10 rounded w-20 mb-2"></div>
        <div className="h-2 bg-white/10 rounded w-full"></div>
      </div>
    );
  }

  if (!stats) return null;

  const completedGoals = dailyGoals.filter(g => g.completed).length;
  const totalGoals = dailyGoals.length;
  const goalsProgress = totalGoals > 0 ? (completedGoals / totalGoals) * 100 : 0;

  return (
    <div
      onClick={onClick}
      className="p-3 border-t border-white/10 cursor-pointer hover:bg-white/5 transition-colors"
    >
      {/* Level & Points Row */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-br from-copper to-amber-600 rounded-full flex items-center justify-center">
            <span className="text-parchment font-bold text-sm">{stats.level}</span>
          </div>
          <div>
            <p className="text-cream text-xs font-semibold">Level {stats.level}</p>
            <p className="text-slate text-[10px]">{stats.total_points} pts</p>
          </div>
        </div>

        {/* Streak */}
        {stats.current_streak > 0 && (
          <div className="flex items-center gap-1 text-orange-400">
            <Flame size={14} />
            <span className="text-xs font-bold">{stats.current_streak}</span>
          </div>
        )}
      </div>

      {/* Level Progress Bar */}
      <div className="mb-2">
        <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-copper to-amber-500 transition-all duration-500"
            style={{ width: `${stats.level_progress}%` }}
          />
        </div>
        <p className="text-slate text-[10px] mt-0.5">{stats.level_progress}% to Level {stats.level + 1}</p>
      </div>

      {/* Daily Goals Summary */}
      <div className="flex items-center gap-2">
        <Target size={12} className="text-copper" />
        <div className="flex-1">
          <div className="h-1 bg-white/10 rounded-full overflow-hidden">
            <div
              className={`h-full transition-all duration-500 ${
                goalsProgress === 100 ? 'bg-green-500' : 'bg-copper'
              }`}
              style={{ width: `${goalsProgress}%` }}
            />
          </div>
        </div>
        <span className="text-slate text-[10px]">{completedGoals}/{totalGoals}</span>
      </div>
    </div>
  );
}

// Full achievements view component
export function AchievementsView() {
  const [stats, setStats] = useState(null);
  const [achievements, setAchievements] = useState({ unlocked: [], locked: [] });
  const [dailyGoals, setDailyGoals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('daily');

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      const [statsRes, achievementsRes, goalsRes] = await Promise.all([
        fetch('/api/gamification/stats'),
        fetch('/api/gamification/achievements'),
        fetch('/api/gamification/daily-goals')
      ]);

      if (statsRes.ok) setStats(await statsRes.json());
      if (achievementsRes.ok) setAchievements(await achievementsRes.json());
      if (goalsRes.ok) setDailyGoals(await goalsRes.json());
    } catch (err) {
      console.error('Failed to fetch gamification data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-copper"></div>
      </div>
    );
  }

  const completedGoals = dailyGoals.filter(g => g.completed).length;

  return (
    <div className="space-y-6">
      {/* Stats Header */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* Level Card */}
        <div className="bg-gradient-to-br from-copper/20 to-amber-600/20 border border-copper/30 p-4 rounded-lg">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-copper to-amber-600 rounded-full flex items-center justify-center">
              <span className="text-parchment font-bold text-xl">{stats?.level || 1}</span>
            </div>
            <div>
              <p className="text-slate text-xs uppercase tracking-wide">Level</p>
              <p className="text-ink font-semibold">{stats?.total_points || 0} points</p>
            </div>
          </div>
          <div className="mt-3">
            <div className="h-2 bg-white/20 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-copper to-amber-500"
                style={{ width: `${stats?.level_progress || 0}%` }}
              />
            </div>
            <p className="text-slate text-xs mt-1">{stats?.level_progress || 0}% to next level</p>
          </div>
        </div>

        {/* Streak Card */}
        <div className="bg-gradient-to-br from-orange-500/20 to-red-500/20 border border-orange-500/30 p-4 rounded-lg">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-orange-500 to-red-500 rounded-full flex items-center justify-center">
              <Flame size={24} className="text-white" />
            </div>
            <div>
              <p className="text-slate text-xs uppercase tracking-wide">Current Streak</p>
              <p className="text-ink font-semibold">{stats?.current_streak || 0} days</p>
            </div>
          </div>
          <p className="text-slate text-xs mt-3">
            Best: {stats?.longest_streak || 0} days
          </p>
        </div>

        {/* Daily Goals Card */}
        <div className="bg-gradient-to-br from-green-500/20 to-emerald-500/20 border border-green-500/30 p-4 rounded-lg">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-500 rounded-full flex items-center justify-center">
              <Target size={24} className="text-white" />
            </div>
            <div>
              <p className="text-slate text-xs uppercase tracking-wide">Today's Goals</p>
              <p className="text-ink font-semibold">{completedGoals}/{dailyGoals.length}</p>
            </div>
          </div>
          <p className="text-slate text-xs mt-3">
            {completedGoals === dailyGoals.length ? 'All complete!' : `${dailyGoals.length - completedGoals} remaining`}
          </p>
        </div>

        {/* Achievements Card */}
        <div className="bg-gradient-to-br from-purple-500/20 to-indigo-500/20 border border-purple-500/30 p-4 rounded-lg">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-indigo-500 rounded-full flex items-center justify-center">
              <Trophy size={24} className="text-white" />
            </div>
            <div>
              <p className="text-slate text-xs uppercase tracking-wide">Achievements</p>
              <p className="text-ink font-semibold">{achievements.total_unlocked}/{achievements.total_achievements}</p>
            </div>
          </div>
          <p className="text-slate text-xs mt-3">
            {achievements.total_achievements - achievements.total_unlocked} to unlock
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-warm-gray">
        <button
          onClick={() => setActiveTab('daily')}
          className={`px-4 py-2 font-body uppercase tracking-wide text-sm transition-colors ${
            activeTab === 'daily'
              ? 'text-copper border-b-2 border-copper'
              : 'text-slate hover:text-ink'
          }`}
        >
          Daily Goals
        </button>
        <button
          onClick={() => setActiveTab('achievements')}
          className={`px-4 py-2 font-body uppercase tracking-wide text-sm transition-colors ${
            activeTab === 'achievements'
              ? 'text-copper border-b-2 border-copper'
              : 'text-slate hover:text-ink'
          }`}
        >
          Achievements
        </button>
      </div>

      {/* Daily Goals Tab */}
      {activeTab === 'daily' && (
        <div className="space-y-3">
          {dailyGoals.map((goal) => (
            <div
              key={goal.goal_type}
              className={`p-4 border rounded-lg transition-all ${
                goal.completed
                  ? 'bg-green-50 border-green-200'
                  : 'bg-parchment border-warm-gray hover:border-copper/50'
              }`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    goal.completed ? 'bg-green-500' : 'bg-copper/20'
                  }`}>
                    {goal.completed ? (
                      <Star size={20} className="text-white" />
                    ) : (
                      <Target size={20} className="text-copper" />
                    )}
                  </div>
                  <div>
                    <p className="font-semibold text-ink">{goal.name}</p>
                    <p className="text-sm text-slate">{goal.description}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className={`font-bold ${goal.completed ? 'text-green-600' : 'text-ink'}`}>
                    {goal.current}/{goal.target}
                  </p>
                  <p className="text-xs text-copper">+{goal.points} pts</p>
                </div>
              </div>

              {/* Progress bar */}
              <div className="mt-3 h-2 bg-white/50 rounded-full overflow-hidden">
                <div
                  className={`h-full transition-all duration-500 ${
                    goal.completed ? 'bg-green-500' : 'bg-copper'
                  }`}
                  style={{ width: `${Math.min((goal.current / goal.target) * 100, 100)}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Achievements Tab */}
      {activeTab === 'achievements' && (
        <div className="space-y-6">
          {/* Unlocked Achievements */}
          {achievements.unlocked.length > 0 && (
            <div>
              <h3 className="font-body uppercase tracking-wide text-sm text-ink mb-3 flex items-center gap-2">
                <Trophy size={16} className="text-copper" />
                Unlocked ({achievements.unlocked.length})
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {achievements.unlocked.map((achievement) => (
                  <div
                    key={achievement.id}
                    className="p-4 bg-gradient-to-br from-amber-50 to-orange-50 border border-amber-200 rounded-lg"
                  >
                    <div className="flex items-start gap-3">
                      <div className="w-12 h-12 bg-gradient-to-br from-amber-400 to-orange-500 rounded-full flex items-center justify-center flex-shrink-0">
                        <Award size={24} className="text-white" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-ink">{achievement.name}</p>
                        <p className="text-sm text-slate">{achievement.description}</p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-xs text-amber-600 font-semibold">+{achievement.points} pts</span>
                          {achievement.unlocked_at && (
                            <span className="text-xs text-slate">
                              {new Date(achievement.unlocked_at).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Locked Achievements */}
          <div>
            <h3 className="font-body uppercase tracking-wide text-sm text-ink mb-3 flex items-center gap-2">
              <Zap size={16} className="text-slate" />
              Locked ({achievements.locked.length})
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {achievements.locked.map((achievement) => (
                <div
                  key={achievement.id}
                  className="p-4 bg-slate/5 border border-slate/20 rounded-lg opacity-75"
                >
                  <div className="flex items-start gap-3">
                    <div className="w-12 h-12 bg-slate/20 rounded-full flex items-center justify-center flex-shrink-0">
                      <Award size={24} className="text-slate/50" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-semibold text-ink">{achievement.name}</p>
                      <p className="text-sm text-slate">{achievement.description}</p>
                      <span className="text-xs text-copper font-semibold">+{achievement.points} pts</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default GamificationWidget;

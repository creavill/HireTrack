import React from 'react';
import { AlertCircle, Star, Mail, ChevronRight, X } from 'lucide-react';

export default function ActionBanner({
  stats,
  followupCount = 0,
  onScanClick,
  onScoreClick,
  onFollowupsClick,
  onDismiss
}) {
  // Calculate pending actions
  const unscoredCount = stats?.new || 0;
  const hasUnscoredJobs = unscoredCount > 0;
  const hasFollowups = followupCount > 0;

  // If no pending actions, don't render
  if (!hasUnscoredJobs && !hasFollowups) {
    return null;
  }

  const actions = [];

  if (hasUnscoredJobs) {
    actions.push({
      id: 'score',
      icon: Star,
      message: `${unscoredCount} job${unscoredCount !== 1 ? 's' : ''} need${unscoredCount === 1 ? 's' : ''} scoring`,
      action: onScoreClick,
      actionLabel: 'Score Now',
      color: 'copper'
    });
  }

  if (hasFollowups) {
    actions.push({
      id: 'followups',
      icon: Mail,
      message: `${followupCount} new follow-up${followupCount !== 1 ? 's' : ''} to review`,
      action: onFollowupsClick,
      actionLabel: 'View',
      color: 'patina'
    });
  }

  return (
    <div className="bg-warm-gray/50 border border-warm-gray mb-6">
      <div className="px-4 py-3">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-sm text-slate">
            <AlertCircle size={16} className="text-copper flex-shrink-0" />
            <span className="font-body font-medium text-ink">Action Center</span>
          </div>
          {onDismiss && (
            <button
              onClick={onDismiss}
              className="text-slate hover:text-ink transition-colors"
              title="Dismiss"
            >
              <X size={16} />
            </button>
          )}
        </div>

        <div className="mt-3 space-y-2">
          {actions.map((action) => {
            const Icon = action.icon;
            return (
              <div
                key={action.id}
                className={`
                  flex items-center justify-between gap-3 p-3
                  bg-parchment border-l-[3px]
                  ${action.color === 'copper' ? 'border-l-copper' : 'border-l-patina'}
                `}
              >
                <div className="flex items-center gap-2">
                  <Icon
                    size={16}
                    className={action.color === 'copper' ? 'text-copper' : 'text-patina'}
                  />
                  <span className="text-sm text-ink font-body">{action.message}</span>
                </div>
                <button
                  onClick={action.action}
                  className={`
                    flex items-center gap-1 px-3 py-1 text-xs font-body uppercase tracking-wide
                    ${action.color === 'copper'
                      ? 'bg-copper/10 text-copper hover:bg-copper/20'
                      : 'bg-patina/10 text-patina hover:bg-patina/20'
                    }
                    transition-colors
                  `}
                >
                  {action.actionLabel}
                  <ChevronRight size={12} />
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

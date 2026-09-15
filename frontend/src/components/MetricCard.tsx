import React from "react";

interface MetricCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  badge?: string;
  badgeColor?: "emerald" | "cyan" | "amber" | "rose" | "slate";
  icon?: React.ReactNode;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  subValue,
  badge,
  badgeColor = "slate",
  icon,
}) => {
  const badgeClasses = {
    emerald: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    cyan: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
    amber: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    rose: "bg-rose-500/10 text-rose-400 border-rose-500/20",
    slate: "bg-slate-800 text-slate-300 border-slate-700",
  }[badgeColor];

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-lg p-4 shadow-sm flex flex-col justify-between">
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-xs font-semibold text-slate-400 tracking-wide uppercase">
          {label}
        </span>
        {icon && <span className="text-slate-500">{icon}</span>}
      </div>

      <div className="flex items-baseline justify-between gap-2">
        <div className="text-xl font-bold font-mono text-slate-100 truncate">
          {value}
        </div>
        {badge && (
          <span className={`text-[10px] px-1.5 py-0.5 rounded border font-mono font-medium ${badgeClasses}`}>
            {badge}
          </span>
        )}
      </div>

      {subValue && (
        <div className="text-xs text-slate-500 font-mono mt-1 truncate">
          {subValue}
        </div>
      )}
    </div>
  );
};

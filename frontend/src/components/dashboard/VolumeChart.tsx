import { useAgentStore } from "../../stores/agentStore";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export default function VolumeChart() {
  const weeklyActivity = useAgentStore((s) => s.weeklyActivity);

  const maxVal = Math.max(...weeklyActivity, 1);

  return (
    <div className="card span-2 animate-fade-in">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold text-zinc-200">Weekly Activity</h3>
          <p className="text-xs text-zinc-500 mt-0.5">Agent events per day</p>
        </div>
        <div className="flex gap-3 text-xs text-zinc-500">
          <span className="flex items-center gap-1">
            <span className="inline-block w-2 h-2 rounded-sm bg-green-500" />
            Events
          </span>
        </div>
      </div>

      {/* Bar chart */}
      <div className="flex items-end gap-3 h-32">
        {weeklyActivity.map((count, i) => {
          const pct = (count / maxVal) * 100;
          return (
            <div key={i} className="flex flex-col items-center flex-1 gap-1">
              <span className="text-[10px] text-zinc-500 font-mono">{count}</span>
              <div className="w-full relative" style={{ height: "100px" }}>
                <div
                  className="volume-bar volume-bar-green w-full absolute bottom-0"
                  style={{ height: `${Math.max(pct, 4)}%` }}
                />
              </div>
              <span className="text-[10px] text-zinc-600">{DAYS[i]}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

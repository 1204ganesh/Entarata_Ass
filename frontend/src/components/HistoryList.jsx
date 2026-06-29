

import { Clock } from "lucide-react";

export default function HistoryList({ items, activeId, onSelect }) {
  return (
    <div className="history-card">
      <div className="card-title">
        <Clock size={14} />
        Recent snippets
      </div>
      {items.length === 0 ? (
        <p className="empty-hint">Submitted snippets will appear here.</p>
      ) : (
        <div className="history-list">
          {items.map((item, index) => (
            <button
              key={item.id}
              type="button"
              className={`history-item ${item.id === activeId ? "history-item--active" : ""}`}
              onClick={() => onSelect(item.id)}
            >
              <div className="history-item-top">
                <span className="history-lang">{item.language}</span>
                <span className="history-time">
                  {new Date(item.createdAt).toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit"
                  })}
                </span>
              </div>
              <div className="history-name">Snippet {items.length - index}</div>
              <div className="history-preview">
                {item.originalCode?.split("\n")[0]?.trim() || "—"}
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
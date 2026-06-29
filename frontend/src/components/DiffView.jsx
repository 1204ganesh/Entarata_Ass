// function buildLineDiff(original, optimized) {
//   const originalLines = original.split("\n");
//   const optimizedLines = optimized.split("\n");
//   const max = Math.max(originalLines.length, optimizedLines.length);
//   const rows = [];

//   for (let index = 0; index < max; index += 1) {
//     const before = originalLines[index] ?? "";
//     const after = optimizedLines[index] ?? "";
//     rows.push({
//       id: index,
//       before,
//       after,
//       changed: before !== after
//     });
//   }

//   return rows;
// }

// export default function DiffView({ original, optimized, summary }) {
//   const rows = buildLineDiff(original, optimized);

//   return (
//     <article className="resultPanel diffPanel">
//       <div className="panelTitle">Optimized comparison</div>
//       {summary && <p className="summaryText">{summary}</p>}
//       <div className="diffGrid">
//         <div className="diffHeader">Original</div>
//         <div className="diffHeader">Optimized</div>
//         {rows.map((row) => (
//           <div className="diffRow" key={row.id}>
//             <pre className={row.changed ? "removed" : ""}>{row.before || " "}</pre>
//             <pre className={row.changed ? "added" : ""}>{row.after || " "}</pre>
//           </div>
//         ))}
//       </div>
//     </article>
//   );
// }

function buildLineDiff(original, optimized) {
  const originalLines = original.split("\n");
  const optimizedLines = optimized.split("\n");
  const max = Math.max(originalLines.length, optimizedLines.length);
  const rows = [];
  for (let i = 0; i < max; i++) {
    const before = originalLines[i] ?? "";
    const after = optimizedLines[i] ?? "";
    rows.push({ id: i, before, after, changed: before !== after });
  }
  return rows;
}

export default function DiffView({ original, optimized, summary }) {
  const rows = buildLineDiff(original, optimized);

  return (
    <article className="result-card diff-card">
      <div className="card-title">
        <span className="card-title-icon">⇄</span>
        Optimized comparison
      </div>
      {summary && <p className="summary-text">{summary}</p>}
      <div className="diff-wrap">
        <div className="diff-header-row">
          <div className="diff-col-head">Original</div>
          <div className="diff-col-head">Optimized</div>
        </div>
        <div className="diff-body">
          {rows.map((row) => (
            <div className="diff-row" key={row.id}>
              <pre className={`diff-cell ${row.changed ? "diff-cell--removed" : ""}`}>
                {row.before || " "}
              </pre>
              <pre className={`diff-cell ${row.changed ? "diff-cell--added" : ""}`}>
                {row.after || " "}
              </pre>
            </div>
          ))}
        </div>
      </div>
    </article>
  );
}
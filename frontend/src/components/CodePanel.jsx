// const kindLabels = {
//   function: "Function",
//   class: "Class",
//   import: "Import",
//   loop: "Loop",
//   conditional: "Branch",
//   return: "Return",
//   assignment: "Assign",
//   call: "Call"
// };

// export default function CodePanel({ code, annotations }) {
//   const annotationByLine = new Map();
//   for (const annotation of annotations || []) {
//     const existing = annotationByLine.get(annotation.line) || [];
//     existing.push(annotation);
//     annotationByLine.set(annotation.line, existing);
//   }

//   return (
//     <article className="resultPanel codePanel">
//       <div className="panelTitle">Key parts</div>
//       <div className="annotatedCode">
//         {code.split("\n").map((line, index) => {
//           const lineNumber = index + 1;
//           const lineAnnotations = annotationByLine.get(lineNumber) || [];
//           return (
//             <div
//               className={`codeLine ${lineAnnotations.length ? "marked" : ""}`}
//               key={`${lineNumber}-${line}`}
//             >
//               <span className="lineNumber">{lineNumber}</span>
//               <code>{line || " "}</code>
//               {lineAnnotations.length > 0 && (
//                 <span className="lineBadges">
//                   {lineAnnotations.slice(0, 2).map((item) => (
//                     <span className={`badge ${item.kind}`} title={item.detail} key={`${item.kind}-${item.name}`}>
//                       {kindLabels[item.kind] || item.kind}
//                     </span>
//                   ))}
//                 </span>
//               )}
//             </div>
//           );
//         })}
//       </div>
//     </article>
//   );
// }

import { Copy } from "lucide-react";
import { useState } from "react";

const kindLabels = {
  function: "Function",
  class: "Class",
  import: "Import",
  loop: "Loop",
  conditional: "Branch",
  return: "Return",
  assignment: "Assign",
  call: "Call"
};

export default function CodePanel({ code, annotations }) {
  const [copied, setCopied] = useState(false);

  const annotationByLine = new Map();
  for (const annotation of annotations || []) {
    const existing = annotationByLine.get(annotation.line) || [];
    existing.push(annotation);
    annotationByLine.set(annotation.line, existing);
  }

  function handleCopy() {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    });
  }

  return (
    <article className="result-card code-card">
      <div className="card-title-row">
        <div className="card-title">
          <span className="card-title-icon">{"<>"}</span>
          Key parts
        </div>
        <button className="copy-btn" type="button" onClick={handleCopy}>
          <Copy size={13} />
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      <div className="annotated-code">
        {code.split("\n").map((line, index) => {
          const lineNumber = index + 1;
          const lineAnnotations = annotationByLine.get(lineNumber) || [];
          return (
            <div
              className={`code-line ${lineAnnotations.length ? "code-line--marked" : ""}`}
              key={`${lineNumber}-${line}`}
            >
              <span className="line-num">{lineNumber}</span>
              <code className="line-code">{line || " "}</code>
              {lineAnnotations.length > 0 && (
                <span className="line-badges">
                  {lineAnnotations.slice(0, 2).map((item) => (
                    <span
                      className={`badge badge--${item.kind}`}
                      title={item.detail}
                      key={`${item.kind}-${item.name}`}
                    >
                      {kindLabels[item.kind] || item.kind}
                    </span>
                  ))}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </article>
  );
}
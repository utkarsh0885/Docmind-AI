import React from 'react';

interface MarkdownProps {
  content: string;
}

export const Markdown: React.FC<MarkdownProps> = ({ content }) => {
  if (!content) return null;

  // Split content by paragraphs or block elements
  const blocks = content.split(/\n\n+/);

  const renderInline = (text: string): React.ReactNode[] => {
    if (!text) return [];
    
    // Split by bold (**text**) and inline code (`code`)
    const parts = text.split(/(\*\*.*?\*\*|`.*?`)/g);

    return parts.map((part, idx) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={idx} className="font-semibold text-surface-50">
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code key={idx} className="px-1.5 py-0.5 rounded bg-surface-950 border border-surface-800 text-[11px] font-mono text-cyan-400">
            {part.slice(1, -1)}
          </code>
        );
      }
      return part;
    });
  };

  return (
    <div className="space-y-3 font-normal text-surface-200 text-sm leading-relaxed">
      {blocks.map((block, blockIdx) => {
        const trimmed = block.trim();
        if (!trimmed) return null;

        // 1. Code blocks
        if (trimmed.startsWith('```') && trimmed.endsWith('```')) {
          const lines = trimmed.slice(3, -3).split('\n');
          // Skip optional language identifier line if empty or name
          let codeLines = [...lines];
          if (codeLines.length > 0 && /^[a-zA-Z0-9_-]+$/.test(codeLines[0])) {
            codeLines.shift();
          }
          const code = codeLines.join('\n');
          return (
            <pre key={blockIdx} className="p-3.5 rounded-xl bg-surface-950 border border-surface-850 overflow-x-auto text-xs font-mono text-cyan-300 my-2">
              <code>{code}</code>
            </pre>
          );
        }

        // 2. Headers
        if (trimmed.startsWith('### ')) {
          return (
            <h3 key={blockIdx} className="text-sm font-bold text-surface-100 mt-4 mb-2">
              {renderInline(trimmed.substring(4))}
            </h3>
          );
        }
        if (trimmed.startsWith('## ')) {
          return (
            <h2 key={blockIdx} className="text-base font-bold text-surface-100 mt-5 mb-2.5">
              {renderInline(trimmed.substring(3))}
            </h2>
          );
        }
        if (trimmed.startsWith('# ')) {
          return (
            <h1 key={blockIdx} className="text-lg font-extrabold text-surface-100 mt-6 mb-3">
              {renderInline(trimmed.substring(2))}
            </h1>
          );
        }

        // 3. Bullet lists
        if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
          const items = trimmed.split(/\n[-*]\s+/);
          // Clean first item prefix
          items[0] = items[0].replace(/^[-*]\s+/, '');
          return (
            <ul key={blockIdx} className="list-disc pl-5 space-y-1.5 my-2">
              {items.map((item, itemIdx) => (
                <li key={itemIdx}>{renderInline(item)}</li>
              ))}
            </ul>
          );
        }

        // 4. Numbered lists
        if (/^\d+\.\s+/.test(trimmed)) {
          const items = trimmed.split(/\n\d+\.\s+/);
          // Clean first item prefix
          items[0] = items[0].replace(/^\d+\.\s+/, '');
          return (
            <ol key={blockIdx} className="list-decimal pl-5 space-y-1.5 my-2">
              {items.map((item, itemIdx) => (
                <li key={itemIdx}>{renderInline(item)}</li>
              ))}
            </ol>
          );
        }

        // 5. Normal paragraph (preserve single newlines inside paragraph block as linebreaks)
        const lines = trimmed.split('\n');
        return (
          <p key={blockIdx} className="break-words">
            {lines.map((line, lineIdx) => (
              <React.Fragment key={lineIdx}>
                {lineIdx > 0 && <br />}
                {renderInline(line)}
              </React.Fragment>
            ))}
          </p>
        );
      })}
    </div>
  );
};

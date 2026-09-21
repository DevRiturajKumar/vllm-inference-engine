import React, { useState, useEffect, useRef } from 'react';
import { Brain, ChevronDown, ChevronUp, Sparkles, Terminal } from 'lucide-react';

export function ThinkingBlock({ reasoning, isStreaming = false }) {
  const [isExpanded, setIsExpanded] = useState(true);
  const reasoningEndRef = useRef(null);
  const containerRef = useRef(null);

  // Auto-scroll reasoning container during streaming
  useEffect(() => {
    if (isStreaming && containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [reasoning, isStreaming]);

  if (!reasoning && !isStreaming) return null;

  return (
    <div className="my-3 rounded-2xl border border-amber-500/30 bg-amber-50/50 dark:bg-amber-950/20 dark:border-amber-500/40 shadow-sm overflow-hidden transition-all duration-200">
      
      {/* Header bar with visible <think> badge */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        type="button"
        className="w-full flex items-center justify-between px-3.5 py-2.5 text-left text-xs font-medium text-amber-900 dark:text-amber-200 hover:bg-amber-100/60 dark:hover:bg-amber-900/30 transition-colors duration-150 select-none min-h-[44px]"
        aria-expanded={isExpanded}
      >
        <div className="flex items-center space-x-2">
          <div className={`p-1.5 rounded-lg bg-amber-500/15 text-amber-600 dark:text-amber-400 ${isStreaming ? 'animate-pulse' : ''}`}>
            <Brain className="w-4 h-4" />
          </div>

          {/* Explicit <think> tag display */}
          <span className="font-mono text-xs font-bold text-amber-700 dark:text-amber-300 bg-amber-200/60 dark:bg-amber-900/50 px-2 py-0.5 rounded-md border border-amber-500/30">
            &lt;think&gt;
          </span>

          <span className="font-semibold text-xs tracking-wide text-amber-800 dark:text-amber-200 hidden sm:inline">
            {isStreaming ? 'Reasoning Process...' : 'Chain of Thought'}
          </span>

          {isStreaming && (
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-200 dark:bg-amber-900/80 text-amber-900 dark:text-amber-100 animate-pulse border border-amber-400/40">
              <Sparkles className="w-2.5 h-2.5 mr-1" />
              Thinking
            </span>
          )}
        </div>

        <div className="flex items-center space-x-2.5 text-amber-700/80 dark:text-amber-300/80">
          <span className="text-[11px] font-mono">
            {reasoning ? `${reasoning.length} chars` : '0 chars'}
          </span>
          <div className="p-1 rounded-md bg-amber-500/10 dark:bg-amber-400/10">
            {isExpanded ? (
              <ChevronUp className="w-3.5 h-3.5" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5" />
            )}
          </div>
        </div>
      </button>

      {/* Reasoning text body with visible <think> and </think> delimiters */}
      {isExpanded && (
        <div className="px-3.5 pb-3 pt-1 border-t border-amber-500/15 dark:border-amber-500/25 bg-amber-50/30 dark:bg-black/20">
          <div 
            ref={containerRef}
            className="text-xs text-amber-950/90 dark:text-amber-200/90 font-mono whitespace-pre-wrap leading-relaxed max-h-80 overflow-y-auto pr-1"
          >
            {/* Opening tag indicator */}
            <div className="text-[11px] font-bold text-amber-600/80 dark:text-amber-400/80 select-none pb-1">
              &lt;think&gt;
            </div>

            {/* Actual reasoning stream */}
            {reasoning || (
              <span className="italic opacity-60">Deliberating initial thought sequence...</span>
            )}
            {isStreaming && <span className="streaming-cursor" />}

            {/* Closing tag indicator when thinking finished */}
            {!isStreaming && reasoning && (
              <div className="text-[11px] font-bold text-amber-600/80 dark:text-amber-400/80 select-none pt-1">
                &lt;/think&gt;
              </div>
            )}
            <div ref={reasoningEndRef} />
          </div>
        </div>
      )}
    </div>
  );
}

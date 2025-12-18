import React, { useState } from 'react';

export function ReasoningTrace({ debug }) {
    const [isOpen, setIsOpen] = useState(false);

    if (!debug) return null;

    return (
        <div className="mt-2">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="btn btn-xs btn-ghost gap-2 text-base-content/60 hover:text-base-content"
            >
                <span>🛠️</span>
                {isOpen ? 'Hide Analysis' : 'Show Analysis'}
            </button>

            {isOpen && (
                <div className="mt-2 p-4 bg-base-200 rounded-lg text-sm space-y-4 animate-in fade-in slide-in-from-top-2 duration-200">

                    {/* Routing Section */}
                    <div>
                        <div className="font-bold text-xs uppercase tracking-wider opacity-50 mb-1">Query Analysis</div>
                        <div className="flex items-center gap-2">
                            <span className="badge badge-primary badge-sm font-mono">{debug.variant.toUpperCase()}</span>
                            <span className="font-mono text-xs opacity-70 truncate" title={debug.standalone_query}>
                                "{debug.standalone_query}"
                            </span>
                        </div>
                    </div>

                    {/* Sources Section */}
                    <div>
                        <div className="font-bold text-xs uppercase tracking-wider opacity-50 mb-2">Retrieved Sources ({debug.source_docs.length})</div>
                        <div className="space-y-2 grid grid-cols-1">
                            {debug.source_docs.map((doc, idx) => (
                                <div key={idx} className="bg-base-100 p-2 rounded border border-base-300">
                                    {/* Line 1: Source & Page */}
                                    <div className="flex gap-2 text-xs opacity-70 mb-1">
                                        <span className="font-bold">{doc.metadata.source_file}</span>
                                        <span className="badge badge-outline badge-xs">p.{doc.metadata.page}</span>
                                    </div>

                                    {/* Line 2: Hierarchy (Chapter > Section > Heading) */}
                                    <div className="text-xs text-primary/80 mb-1 truncate">
                                        {[doc.metadata.chapter, doc.metadata.section, doc.metadata.heading].filter(Boolean).join(" > ")}
                                    </div>

                                    {/* Line 3: Summary */}
                                    <div className="text-xs font-semibold text-secondary mb-1">
                                        {doc.metadata.summary || "No summary available"}
                                    </div>

                                    {/* Line 4: Content */}
                                    <p className="text-xs opacity-80 leading-relaxed font-serif bg-base-100/50 p-1 rounded">
                                        {doc.page_content}
                                    </p>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

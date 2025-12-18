import React from 'react';

export function DebugDrawer({ debugData, isOpen, toggle }) {
    if (!debugData) return null;

    return (
        <div className={`drawer drawer-end z-20 ${isOpen ? 'drawer-open' : ''}`}>
            <input id="debug-drawer" type="checkbox" className="drawer-toggle" checked={isOpen} readOnly />

            <div className="drawer-side">
                <label aria-label="close sidebar" className="drawer-overlay" onClick={toggle}></label>
                <div className="menu p-4 w-96 min-h-full bg-base-200 text-base-content">
                    <h2 className="text-xl font-bold mb-4">🛠️ Reasoning Trace</h2>

                    <div className="collapse collapse-arrow bg-base-100 mb-2">
                        <input type="checkbox" defaultChecked />
                        <div className="collapse-title font-medium">
                            Routing Logic
                        </div>
                        <div className="collapse-content">
                            <p className="text-sm"><strong>Original:</strong> {debugData.standalone_query}</p>
                            <div className="badge badge-primary mt-2">{debugData.variant.toUpperCase()} Rules</div>
                        </div>
                    </div>

                    <div className="divider">Retrieval</div>

                    <div className="space-y-2">
                        {debugData.source_docs.map((doc, idx) => (
                            <div key={idx} className="card bg-base-100 shadow-sm text-xs">
                                <div className="card-body p-3">
                                    <h3 className="font-bold text-secondary">
                                        {doc.metadata.summary || `Source ${idx + 1}`}
                                    </h3>
                                    <div className="flex gap-2 mb-1">
                                        <span className="badge badge-outline badge-xs">{doc.metadata.source_file}</span>
                                        <span className="badge badge-outline badge-xs">p.{doc.metadata.page}</span>
                                    </div>
                                    <p className="opacity-70 line-clamp-3">{doc.page_content}</p>
                                </div>
                            </div>
                        ))}
                    </div>

                </div>
            </div>
        </div>
    );
}

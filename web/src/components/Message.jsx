import React, { useState, useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import { ReasoningTrace } from './ReasoningTrace';

export function Message({ role, content, debug, animate = false }) {
    const isUser = role === 'user';
    const [displayedContent, setDisplayedContent] = useState(animate && !isUser ? "" : content);
    const hasAnimated = useRef(!animate); // If not animating, mark as done

    useEffect(() => {
        // If we shouldn't animate, or already did, or no content, just set full content
        if (!animate || isUser || !content || hasAnimated.current) {
            setDisplayedContent(content);
            return;
        }

        let currentIndex = 0;
        const intervalId = setInterval(() => {
            if (currentIndex >= content.length) {
                clearInterval(intervalId);
                hasAnimated.current = true;
                return;
            }

            // Add a chunk of characters (e.g., 2-5) for speed variance
            const chunk = Math.floor(Math.random() * 3) + 2;
            const nextIndex = Math.min(content.length, currentIndex + chunk);

            setDisplayedContent(content.slice(0, nextIndex));
            currentIndex = nextIndex;
        }, 10); // Fast typing speed

        return () => clearInterval(intervalId);
    }, [content, animate, isUser]);

    return (
        <div className={`group w-full text-base-content border-b border-black/5 dark:border-white/5 ${isUser ? 'bg-base-100' : 'bg-base-100'}`}>
            <div className="text-base gap-4 md:gap-6 md:max-w-2xl lg:max-w-[38rem] xl:max-w-3xl p-4 md:py-6 flex lg:px-0 m-auto">

                {/* Avatar */}
                <div className="flex-shrink-0 flex flex-col relative items-end">
                    <div className="w-8 h-8 rounded-sm flex items-center justify-center">
                        {isUser ? (
                            <div className="w-8 h-8 bg-neutral text-neutral-content rounded flex items-center justify-center font-semibold text-xs">You</div>
                        ) : (
                            <div className="w-8 h-8 bg-primary text-primary-content rounded flex items-center justify-center font-bold">AI</div>
                        )}
                    </div>
                </div>

                {/* Content */}
                <div className="relative flex-1 overflow-hidden">
                    {/* Author Name */}
                    <div className="font-bold text-sm mb-1 opacity-90">
                        {isUser ? "You" : "FIH Rules Expert"}
                    </div>

                    {/* Text Body */}
                    <div className="markdown prose dark:prose-invert prose-sm max-w-none break-words leading-7">
                        {displayedContent ? (
                            <ReactMarkdown>{String(displayedContent)}</ReactMarkdown>
                        ) : (
                            <span className="loading loading-dots loading-sm opacity-50"></span>
                        )}
                    </div>

                    {/* Footer / Debug Trace (Only show when typing is done or nearly done) */}
                    {!isUser && debug && (displayedContent.length === content.length) && (
                        <ReasoningTrace debug={debug} />
                    )}
                </div>
            </div>
        </div>
    );
}

"use client";

import { useMemo } from "react";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

/**
 * Simple Markdown renderer for intelligence reports
 * Supports: headers, bold, italic, lists, blockquotes, horizontal rules
 */
export function MarkdownRenderer({ content, className = "" }: MarkdownRendererProps) {
  const rendered = useMemo(() => {
    if (!content) return [];

    const lines = content.split("\n");
    const elements: JSX.Element[] = [];
    let listItems: string[] = [];
    let listType: "ul" | "ol" | null = null;

    const flushList = () => {
      if (listItems.length > 0 && listType) {
        const ListTag = listType;
        elements.push(
          <ListTag
            key={`list-${elements.length}`}
            className={`${listType === "ul" ? "list-disc" : "list-decimal"} list-inside space-y-1 my-3 text-gray-300`}
          >
            {listItems.map((item, i) => (
              <li key={i} className="text-gray-300">
                {parseInline(item)}
              </li>
            ))}
          </ListTag>
        );
        listItems = [];
        listType = null;
      }
    };

    const parseInline = (text: string): (string | JSX.Element)[] => {
      const result: (string | JSX.Element)[] = [];
      let remaining = text;
      let keyIndex = 0;

      // Process bold (**text**)
      while (remaining.includes("**")) {
        const start = remaining.indexOf("**");
        const end = remaining.indexOf("**", start + 2);

        if (end === -1) break;

        if (start > 0) {
          result.push(remaining.slice(0, start));
        }

        result.push(
          <strong key={`bold-${keyIndex++}`} className="font-semibold text-white">
            {remaining.slice(start + 2, end)}
          </strong>
        );

        remaining = remaining.slice(end + 2);
      }

      if (remaining) {
        result.push(remaining);
      }

      return result.length > 0 ? result : [text];
    };

    lines.forEach((line, index) => {
      const trimmed = line.trim();

      // Empty line
      if (!trimmed) {
        flushList();
        return;
      }

      // Headers
      if (trimmed.startsWith("#### ")) {
        flushList();
        elements.push(
          <h4 key={index} className="text-md font-semibold text-gray-200 mt-4 mb-2">
            {parseInline(trimmed.slice(5))}
          </h4>
        );
        return;
      }

      if (trimmed.startsWith("### ")) {
        flushList();
        elements.push(
          <h3 key={index} className="text-lg font-semibold text-[#00D1B2] mt-5 mb-2">
            {parseInline(trimmed.slice(4))}
          </h3>
        );
        return;
      }

      if (trimmed.startsWith("## ")) {
        flushList();
        elements.push(
          <h2 key={index} className="text-xl font-bold text-[#4DA3FF] mt-6 mb-3 pb-2 border-b border-[#4DA3FF]/30">
            {parseInline(trimmed.slice(3))}
          </h2>
        );
        return;
      }

      if (trimmed.startsWith("# ")) {
        flushList();
        elements.push(
          <h1 key={index} className="text-2xl font-bold text-white mt-6 mb-4 pb-2 border-b border-white/20">
            {parseInline(trimmed.slice(2))}
          </h1>
        );
        return;
      }

      // Horizontal rule
      if (trimmed === "---" || trimmed === "***" || trimmed === "___") {
        flushList();
        elements.push(
          <hr key={index} className="border-white/10 my-6" />
        );
        return;
      }

      // Blockquote
      if (trimmed.startsWith("> ")) {
        flushList();
        elements.push(
          <blockquote
            key={index}
            className="border-l-4 border-[#4DA3FF] pl-4 py-2 my-4 bg-[#4DA3FF]/5 rounded-r-lg italic text-gray-400"
          >
            {parseInline(trimmed.slice(2))}
          </blockquote>
        );
        return;
      }

      // Unordered list
      if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
        if (listType !== "ul") {
          flushList();
          listType = "ul";
        }
        listItems.push(trimmed.slice(2));
        return;
      }

      // Ordered list
      const orderedMatch = trimmed.match(/^\d+\.\s+(.*)$/);
      if (orderedMatch) {
        if (listType !== "ol") {
          flushList();
          listType = "ol";
        }
        listItems.push(orderedMatch[1]);
        return;
      }

      // Table row (simple rendering)
      if (trimmed.includes("|") && !trimmed.match(/^\|[\s-]+\|$/)) {
        flushList();
        const cells = trimmed.split("|").filter(c => c.trim() && !c.match(/^[\s-]+$/));
        if (cells.length > 0) {
          elements.push(
            <div key={index} className="flex gap-4 py-1 text-sm">
              {cells.map((cell, i) => (
                <span key={i} className="text-gray-300">
                  {parseInline(cell.trim())}
                </span>
              ))}
            </div>
          );
        }
        return;
      }

      // Skip table separator rows
      if (trimmed.match(/^\|[\s-|]+\|$/)) {
        return;
      }

      // Regular paragraph
      flushList();
      elements.push(
        <p key={index} className="text-gray-300 leading-relaxed my-2">
          {parseInline(trimmed)}
        </p>
      );
    });

    // Flush any remaining list
    flushList();

    return elements;
  }, [content]);

  return (
    <div className={`prose prose-invert max-w-none ${className}`}>
      {rendered}
    </div>
  );
}

// SPDX-License-Identifier: MIT
// Copyright (c) 2026 SafeVixAI Team
import React from 'react';

'use client';

import { memo, useCallback, useMemo, useState } from 'react';
import { ChevronDown, ChevronUp, ChevronsUpDown, ChevronLeft, ChevronRight, Search } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface Column<T> {
  key: string;
  header: string;
  sortable?: boolean;
  filterable?: boolean;
  render?: (item: T) => React.ReactNode;
  width?: string;
  align?: 'left' | 'center' | 'right';
}

interface DataTableProps<T> {
  columns: Column<T>[];
  data: T[];
  keyExtractor: (item: T) => string;
  pageSize?: number;
  emptyMessage?: string;
  loading?: boolean;
  onRowClick?: (item: T) => void;
  selectedKeys?: Set<string>;
  onSelectionChange?: (keys: Set<string>) => void;
  selectable?: boolean;
  className?: string;
}

function DataTableInner<T>({
  columns,
  data,
  keyExtractor,
  pageSize = 20,
  emptyMessage = 'No data available',
  loading = false,
  onRowClick,
  selectedKeys,
  onSelectionChange,
  selectable = false,
  className,
}: DataTableProps<T>) {
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc');
  const [page, setPage] = useState(0);
  const [filterText, setFilterText] = useState('');

  const handleSort = useCallback((key: string) => {
    setSortKey((prev) => {
      if (prev === key) {
        setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
        return key;
      }
      setSortDir('asc');
      return key;
    });
  }, []);

  const filtered = useMemo(() => {
    if (!filterText) return data;
    const lower = filterText.toLowerCase();
    return data.filter((item) =>
      columns.some((col) => {
        const val = (item as Record<string, unknown>)[col.key];
        return String(val ?? '').toLowerCase().includes(lower);
      })
    );
  }, [data, filterText, columns]);

  const sorted = useMemo(() => {
    if (!sortKey) return filtered;
    return [...filtered].sort((a, b) => {
      const aVal = (a as Record<string, unknown>)[sortKey];
      const bVal = (b as Record<string, unknown>)[sortKey];
      if (aVal == null) return 1;
      if (bVal == null) return -1;
      const cmp = typeof aVal === 'number' && typeof bVal === 'number'
        ? aVal - bVal
        : String(aVal).localeCompare(String(bVal));
      return sortDir === 'asc' ? cmp : -cmp;
    });
  }, [filtered, sortKey, sortDir]);

  const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
  const paged = useMemo(() => sorted.slice(page * pageSize, (page + 1) * pageSize), [sorted, page, pageSize]);

  const toggleSelect = useCallback((key: string) => {
    if (!onSelectionChange || !selectedKeys) return;
    const next = new Set(selectedKeys);
    if (next.has(key)) next.delete(key);
    else next.add(key);
    onSelectionChange(next);
  }, [onSelectionChange, selectedKeys]);

  const toggleAll = useCallback(() => {
    if (!onSelectionChange || !selectedKeys) return;
    if (selectedKeys.size === paged.length) {
      onSelectionChange(new Set());
    } else {
      onSelectionChange(new Set(paged.map(keyExtractor)));
    }
  }, [onSelectionChange, selectedKeys, paged, keyExtractor]);

  if (loading) {
    return (
      <div className="border border-border rounded-lg bg-surface-1 overflow-hidden" role="status" aria-label="Loading data">
        <div className="p-4 space-y-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-8 bg-surface-2 animate-pulse rounded" style={{ width: `${70 + Math.random() * 30}%` }} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className={cn('flex flex-col gap-3', className)}>
      {columns.some((c) => c.filterable) && (
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-3" />
          <input
            type="text"
            value={filterText}
            onChange={(e) => { setFilterText(e.target.value); setPage(0); }}
            placeholder="Filter..."
            aria-label="Filter table"
            className="w-full pl-9 pr-3 py-2 bg-surface-2 border border-border rounded-md text-sm text-text-1 placeholder:text-text-3 outline-none focus:border-brand-light/50 focus:ring-2 focus:ring-brand-light/10"
          />
        </div>
      )}

      <div className="border border-border rounded-lg bg-surface-1 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm" role="grid" aria-label="Data table">
            <thead>
              <tr className="border-b border-border bg-surface-2">
                {selectable && (
                  <th className="px-3 py-3 w-10">
                    <input
                      type="checkbox"
                      checked={selectedKeys?.size === paged.length && paged.length > 0}
                      onChange={toggleAll}
                      aria-label="Select all rows"
                      className="rounded border-border"
                    />
                  </th>
                )}
                {columns.map((col) => (
                  <th
                    key={col.key}
                    className={cn(
                      'px-3 py-3 text-micro font-semibold text-text-2 uppercase tracking-wider',
                      col.sortable && 'cursor-pointer hover:text-text-1 select-none',
                      col.align === 'right' && 'text-right',
                      col.align === 'center' && 'text-center'
                    )}
                    style={col.width ? { width: col.width } : undefined}
                    onClick={() => col.sortable && handleSort(col.key)}
                    aria-sort={sortKey === col.key ? (sortDir === 'asc' ? 'ascending' : 'descending') : undefined}
                  >
                    <span className="inline-flex items-center gap-1">
                      {col.header}
                      {col.sortable && (
                        sortKey === col.key ? (
                          sortDir === 'asc' ? <ChevronUp size={14} /> : <ChevronDown size={14} />
                        ) : (
                          <ChevronsUpDown size={14} className="text-text-3" />
                        )
                      )}
                    </span>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {paged.length === 0 ? (
                <tr>
                  <td
                    colSpan={columns.length + (selectable ? 1 : 0)}
                    className="px-3 py-12 text-center text-text-3 text-body-sm"
                  >
                    {emptyMessage}
                  </td>
                </tr>
              ) : (
                paged.map((item) => {
                  const key = keyExtractor(item);
                  const isSelected = selectedKeys?.has(key);
                  return (
                    <tr
                      key={key}
                      className={cn(
                        'border-b border-border last:border-0 transition-colors',
                        onRowClick && 'cursor-pointer',
                        isSelected ? 'bg-brand-dim' : 'hover:bg-surface-2'
                      )}
                      onClick={() => onRowClick?.(item)}
                      aria-selected={isSelected}
                    >
                      {selectable && (
                        <td className="px-3 py-3">
                          <input
                            type="checkbox"
                            checked={!!isSelected}
                            onChange={() => toggleSelect(key)}
                            onClick={(e) => e.stopPropagation()}
                            aria-label={`Select row ${key}`}
                            className="rounded border-border"
                          />
                        </td>
                      )}
                      {columns.map((col) => (
                        <td
                          key={col.key}
                          className={cn(
                            'px-3 py-3 text-body-sm text-text-1',
                            col.align === 'right' && 'text-right',
                            col.align === 'center' && 'text-center'
                          )}
                        >
                          {col.render
                            ? col.render(item)
                            : String((item as Record<string, unknown>)[col.key] ?? '')}
                        </td>
                      ))}
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between px-1" role="navigation" aria-label="Pagination">
          <span className="text-xs text-text-3">
            {sorted.length} result{sorted.length !== 1 ? 's' : ''}
          </span>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setPage((p) => Math.max(0, p - 1))}
              disabled={page === 0}
              aria-label="Previous page"
              className="p-1.5 rounded-md text-text-2 hover:bg-surface-2 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft size={16} />
            </button>
            {Array.from({ length: Math.min(totalPages, 7) }).map((_, i) => {
              const pageNum = Math.max(0, Math.min(page - 3, totalPages - 7)) + i;
              if (pageNum >= totalPages) return null;
              return (
                <button
                  key={pageNum}
                  onClick={() => setPage(pageNum)}
                  aria-label={`Page ${pageNum + 1}`}
                  aria-current={page === pageNum ? 'page' : undefined}
                  className={cn(
                    'w-8 h-8 rounded-md text-xs font-semibold transition-colors',
                    page === pageNum
                      ? 'bg-brand text-white'
                      : 'text-text-2 hover:bg-surface-2'
                  )}
                >
                  {pageNum + 1}
                </button>
              );
            })}
            <button
              onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
              disabled={page >= totalPages - 1}
              aria-label="Next page"
              className="p-1.5 rounded-md text-text-2 hover:bg-surface-2 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export const DataTable = memo(DataTableInner) as typeof DataTableInner;

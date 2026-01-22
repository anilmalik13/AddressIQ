import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { submitDatabaseTask, getDbProcessingStatus, previewResultFile, downloadFile } from '../../services/api';
import '../../styles/shared.css';
import './DatabaseConnect.css';

type TopMode = 'compare' | 'format';
type SourceType = 'table' | 'query';

interface ValidationErrors {
  connectionString?: string;
  query?: string;
  tableName?: string;
  columns?: { name?: string; warning?: string }[];
}

const DEFAULT_PLACEHOLDER = 'Server=localhost;Database=AddressDB;User Id=app_user;Password=YourStrong!Passw0rd;TrustServerCertificate=True;';
const COL_NAME_REGEX = /^[A-Za-z0-9_]+$/;

const DatabaseConnect: React.FC = () => {
  // Top tabs: Compare | Format
  const [topMode, setTopMode] = useState<TopMode>('format');
  // Connection string input
  const [connString, setConnString] = useState('');
  // Mid tabs: Table | SQL Query
  const [sourceType, setSourceType] = useState<SourceType>('table');
  // Table mode inputs
  // Single optional primary key (UniqueId)
  const [uniqueId, setUniqueId] = useState<string>('');
  // Repeatable required column_name entries
  const [columns, setColumns] = useState<string[]>(['']);
  // Table name (optional), full width
  const [tableName, setTableName] = useState<string>('');
  // Query mode: SQL text
  const [query, setQuery] = useState('');

  // Processing state
  const [processingId, setProcessingId] = useState<string | null>(null);
  const [processingStatus, setProcessingStatus] = useState<any | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const lastActionRef = useRef<'format' | null>(null);

  // Previews
  // We no longer preview inbound data per requirement change
  const [outboundPreview, setOutboundPreview] = useState<{columns: string[]; rows: any[]; filename?: string} | null>(null);
  const [page, setPage] = useState<number>(1);
  const [pageSize] = useState<number>(50);
  const [atEnd, setAtEnd] = useState<boolean>(false);
  const [pageLoading, setPageLoading] = useState<boolean>(false);

  // UI state
  const [submittingAction, setSubmittingAction] = useState<null | 'format'>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [errors, setErrors] = useState<ValidationErrors>({});
  const [localActivity, setLocalActivity] = useState<string[]>([]);

  // Busy state: only when a job is actively running
  const isProcessing = useMemo(() => {
    if (!processingId) return false;
    const s = processingStatus?.status;
    // treat no status yet as processing (just started)
    return !s || ['queued', 'uploaded', 'processing'].includes(s);
  }, [processingId, processingStatus]);

  // Completed state: used to lock the Format button until Reset
  const isCompleted = useMemo(() => processingStatus?.status === 'completed', [processingStatus]);

  const canSubmit = useMemo(() => {
    if (!connString.trim()) return false;
    if (sourceType === 'query') return query.trim().length > 0;
    // table mode: require at least one column_name and all non-empty
    const tableOk = tableName.trim().length > 0;
    const colsOk = columns.length > 0 && columns.every((name) => {
      const trimmed = name.trim();
      return trimmed.length > 0 && COL_NAME_REGEX.test(trimmed);
    });
    return tableOk && colsOk;
  }, [connString, sourceType, query, columns, tableName]);

  const addColumnRow = useCallback(() => {
    setColumns(prev => [...prev, '']);
    setErrors(prev => ({
      ...prev,
      columns: [...(prev.columns || []), {}],
    }));
  }, []);

  const updateColumnName = useCallback((index: number, value: string) => {
    setColumns(prev => prev.map((name, i) => (i === index ? value : name)));
    setErrors(prev => {
      const next = { ...prev } as ValidationErrors;
      const arr = [...(next.columns || Array(columns.length).fill({}))];
      const trimmed = value.trim();
      const entry: { name?: string; warning?: string } = { ...(arr[index] || {}) };
      if (!trimmed) {
        entry.name = 'Required';
      } else if (!COL_NAME_REGEX.test(trimmed)) {
        entry.name = 'Only letters, numbers, and underscore (_) allowed. No spaces or special characters.';
      } else {
        entry.name = undefined;
      }
      entry.warning = trimmed.includes(',') ? 'Tip: To add multiple columns, use the + button next to this field.' : undefined;
      arr[index] = entry;
      next.columns = arr;
      return next;
    });
  }, [columns.length]);

  const removeColumnRow = useCallback((index: number) => {
    setColumns(prev => {
      if (prev.length <= 1) {
        // Keep one empty row if trying to remove the last
        return [''];
      }
      const copy = prev.slice();
      copy.splice(index, 1);
      return copy;
    });
    setErrors(prev => {
      const next = { ...prev } as ValidationErrors;
      if (next.columns && next.columns.length > 0) {
        const arr = next.columns.slice();
        if (arr.length <= 1) {
          next.columns = [{}];
        } else {
          arr.splice(index, 1);
          next.columns = arr;
        }
      }
      return next;
    });
  }, []);

  const validateAll = useCallback(() => {
    const next: ValidationErrors = {};
    if (!connString.trim()) next.connectionString = 'Connection string is required';
    if (sourceType === 'query') {
      if (!query.trim()) next.query = 'SQL query is required';
    } else {
      if (!tableName.trim()) next.tableName = 'Table name is required';
      next.columns = columns.map(name => {
        const trimmed = name.trim();
        const err: { name?: string; warning?: string } = {};
        if (!trimmed) {
          err.name = 'Required';
        } else if (!COL_NAME_REGEX.test(trimmed)) {
          err.name = 'Only letters, numbers, and underscore (_) allowed. No spaces or special characters.';
        }
        if (trimmed.includes(',')) {
          err.warning = 'Tip: To add multiple columns, use the + button next to this field.';
        }
        return err;
      });
    }
    setErrors(next);
    // return validity
    const ok = !next.connectionString && (!next.query) && (!next.tableName) && (!next.columns || next.columns.every(c => !c.name));
    return ok;
  }, [connString, sourceType, query, columns, tableName]);

  const handleSubmit = useCallback(async (action: 'format') => {
  if (submittingAction || processingId) return;
  const valid = validateAll();
  if (!valid) return;
    setSubmittingAction(action);
    setMessage(null);
    setError(null);
    setOutboundPreview(null);
  setPage(1);
  setAtEnd(false);
    setLocalActivity([]);
    try {
      const payload = {
        mode: topMode,
        connectionString: connString.trim(),
        sourceType,
  tableName: sourceType === 'table' ? tableName.trim() || undefined : undefined,
        uniqueId: sourceType === 'table' ? uniqueId.trim() || undefined : undefined,
        columnNames: sourceType === 'table' ? columns.filter(name => name.trim().length > 0) : undefined,
        query: sourceType === 'query' ? query.trim() : undefined,
        action,
      } as const;
      const res = await submitDatabaseTask(payload);
      setMessage(res.message || 'DB task started');
      setLocalActivity((prev) => ['DB task started', ...prev]);
      lastActionRef.current = action;
      const pid = (res as any).processing_id;
      if (pid) {
        setProcessingId(pid);
      }
    } catch (e: any) {
      setError(e?.message || 'Request failed.');
  }
  }, [validateAll, submittingAction, processingId, topMode, connString, sourceType, tableName, uniqueId, columns, query]);

  // Poll processing status
  useEffect(() => {
    const done = ['completed', 'error'];
    if (processingId && !(processingStatus && done.includes(processingStatus.status))) {
      if (!pollRef.current) {
        pollRef.current = setInterval(async () => {
          try {
            const status = await getDbProcessingStatus(processingId);
            setProcessingStatus(status);
          } catch (e) {
            // ignore transient
          }
        }, 2000);
      }
    } else {
      if (pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    }
    return () => {
      if ((!processingId || (processingStatus && done.includes(processingStatus.status))) && pollRef.current) {
        clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [processingId, processingStatus]);

  // When completed, load outbound preview
  useEffect(() => {
    if (!processingStatus) return;
    if (processingStatus.status === 'error') {
      setSubmittingAction(null);
      if (processingStatus.error && !error) setError(processingStatus.error);
      return;
    }
    if (processingStatus.status !== 'completed') return;
    const outbound = processingStatus.output_file as string | undefined;
    if (!outbound) return;
    const loadPage = async () => {
      try {
        setPageLoading(true);
        const b = await previewResultFile(outbound, page, pageSize);
        // initialize columns once; keep filename
        setOutboundPreview(prev => ({
          columns: prev?.columns?.length ? prev.columns : b.columns,
          rows: b.rows,
          filename: outbound,
        }));
        setAtEnd((b.rows?.length || 0) < pageSize);
      } catch {}
      finally {
        setPageLoading(false);
      }
    };
    loadPage();
    setSubmittingAction(null);
  }, [processingStatus, page, pageSize, error]);

  return (
    <div className="modern-container">
      {/* Hero Section */}
      <div className="modern-hero">
        <div className="modern-hero-icon">🗄️</div>
        <h1 className="modern-hero-title">Database Connect</h1>
        <p className="modern-hero-subtitle">Connect to your database and process data using table columns or SQL queries</p>
      </div>

      {/* Main Card */}
      <div className="modern-card">
        {/* Info Cards */}
        <div className="modern-info-cards">
          <div className="modern-info-card modern-info-card-blue">
            <div className="modern-info-card-icon">📊</div>
            <div className="modern-info-card-content">
              <div className="modern-info-card-title">Flexible Data Source</div>
              <div className="modern-info-card-text">Choose between table-based selection or custom SQL queries for maximum flexibility</div>
            </div>
          </div>
          
          <div className="modern-info-card modern-info-card-amber">
            <div className="modern-info-card-icon">⚠️</div>
            <div className="modern-info-card-content">
              <div className="modern-info-card-title">Coming Soon</div>
              <div className="modern-info-card-text">Compare mode is in progress and will be available soon</div>
            </div>
          </div>
        </div>

        {/* Top tabs: Compare | Format */}
        <div className="db-mode-toggle">
          <button
            className="db-mode-btn disabled"
            disabled
            title="Compare mode coming soon"
          >
            Compare <span className="soon-badge">Soon</span>
          </button>
          <button
            className={`db-mode-btn ${topMode === 'format' ? 'active' : ''}`}
            onClick={() => setTopMode('format')}
            disabled={!!submittingAction || !!processingId}
          >
            Format
          </button>
        </div>

        {/* Connection string */}
        <div className="db-input-section">
          <label htmlFor="conn-str" className="modern-label">
            Connection String <span className="required-indicator">*</span>
          </label>
          <input
            id="conn-str"
            className={`modern-input ${errors.connectionString ? 'input-error' : ''}`}
            type="text"
            placeholder={DEFAULT_PLACEHOLDER}
            value={connString}
            onChange={(e) => {
              const v = e.target.value;
              setConnString(v);
              setErrors(prev => ({ ...prev, connectionString: v.trim() ? undefined : 'Connection string is required' }));
            }}
            disabled={!!submittingAction || !!processingId}
          />
          {errors.connectionString && <small className="error-text">{errors.connectionString}</small>}
          <small className="input-hint">Provide a valid database connection string</small>
        </div>

        {/* Source tabs: Table | SQL Query */}
        <div className="source-type-toggle">
          <label className="modern-label">Data Source Type</label>
          <div className="toggle-buttons">
            <button
              className={`toggle-btn ${sourceType === 'table' ? 'active' : ''}`}
              onClick={() => setSourceType('table')}
              disabled={!!submittingAction || !!processingId}
            >
              📋 Table
            </button>
            <button
              className={`toggle-btn ${sourceType === 'query' ? 'active' : ''}`}
              onClick={() => setSourceType('query')}
              disabled={!!submittingAction || !!processingId}
            >
              💻 SQL Query
            </button>
          </div>
        </div>

          {sourceType === 'table' && (
            <div className="table-config">
              {/* Full width table name */}
              <div className="column-row">
                <div className="column-field">
                  <label htmlFor="tbl-name" className="modern-label">
                    Table name <span className="required-indicator">*</span>
                  </label>
                  <input
                    id="tbl-name"
                    className="modern-input"
                    type="text"
                    placeholder="e.g. addresses, dbo.Addresses"
                    value={tableName}
                    onChange={(e) => setTableName(e.target.value)}
                    disabled={!!submittingAction || !!processingId}
                  />
                  {errors.tableName && <small className="error-text">{errors.tableName}</small>}
                  <small className="input-hint">Database table to read from.</small>
                </div>
              </div>

              {/* Single UniqueId field (optional, acts as primary key) */}
              <div className="column-row">
                <div className="column-field">
                  <label htmlFor="uniq-single" className="modern-label">column_UniqueId (optional)</label>
                  <input
                    id="uniq-single"
                    className="modern-input"
                    type="text"
                    placeholder="e.g. id, record_id"
                    value={uniqueId}
                    onChange={(e) => setUniqueId(e.target.value)}
                    disabled={!!submittingAction || !!processingId}
                  />
                  <small className="input-hint">Acts as primary key. Will not be repeated.</small>
                </div>
              </div>

              {/* Repeatable column_name fields */}
              {columns.map((name, idx) => (
                <div className="column-row" key={idx}>
                  <div className="column-field">
                    <label htmlFor={`name-${idx}`} className="modern-label">
                      column_name <span className="required-indicator">*</span>
                    </label>
                    <div className="name-with-add">
                      <input
                        id={`name-${idx}`}
                        className={`modern-input ${errors.columns?.[idx]?.name ? 'input-error' : ''}`}
                        type="text"
                        placeholder="e.g. address_line_1"
                        value={name}
                        onChange={(e) => updateColumnName(idx, e.target.value)}
                        disabled={!!submittingAction || !!processingId}
                      />
                      <button
                        type="button"
                        className="add-btn"
                        title="Add column"
                        onClick={addColumnRow}
                        disabled={!!submittingAction || !!processingId}
                        aria-label="Add another column"
                      >
                        +
                      </button>
                      <button
                        type="button"
                        className="remove-btn"
                        title="Remove column"
                        onClick={() => removeColumnRow(idx)}
                        disabled={!!submittingAction || !!processingId}
                        aria-label={`Remove column row ${idx + 1}`}
                      >
                        –
                      </button>
                    </div>
                    {errors.columns?.[idx]?.name && <small className="error-text">{errors.columns[idx]?.name}</small>}
                    {errors.columns?.[idx]?.warning && <small className="warn-text">{errors.columns[idx]?.warning}</small>}
                  </div>
                </div>
              ))}
            </div>
          )}

          {sourceType === 'query' && (
            <div className="query-config">
              <label htmlFor="sql-text" className="modern-label">
                SQL Query <span className="required-indicator">*</span>
              </label>
              <textarea
                id="sql-text"
                className={`query-textarea ${errors.query ? 'input-error' : ''}`}
                placeholder="SELECT id, address_line_1, city, state, postal_code FROM addresses WHERE country = 'US'"
                rows={6}
                value={query}
                onChange={(e) => {
                  const v = e.target.value;
                  setQuery(v);
                  setErrors(prev => ({ ...prev, query: v.trim() ? undefined : 'SQL query is required' }));
                }}
                disabled={!!submittingAction || !!processingId}
              />
              {errors.query && <small className="error-text">{errors.query}</small>}
            </div>
          )}

          <div className="db-button-group">
            <button
              onClick={() => handleSubmit('format')}
              disabled={!canSubmit || !!submittingAction || isProcessing || isCompleted}
              className="modern-btn btn-primary"
            >
              {submittingAction === 'format' ? 'Working…' : 'Format'}
            </button>
            <button
              onClick={() => {
                // cancel polling
                if (pollRef.current) {
                  clearInterval(pollRef.current);
                  pollRef.current = null;
                }
                // reset all state
                setTopMode('format');
                setConnString('');
                setSourceType('table');
                setUniqueId('');
                setColumns(['']);
                setTableName('');
                setQuery('');
                setProcessingId(null);
                setProcessingStatus(null);
                setOutboundPreview(null);
                setSubmittingAction(null);
                setMessage(null);
                setError(null);
                setErrors({});
                setLocalActivity([]);
                setPage(1);
                setAtEnd(false);
              }}
              disabled={!!submittingAction || isProcessing}
              className="modern-btn btn-secondary"
            >
              Reset
            </button>
          </div>

          {/* Progress & activity */}
          {(processingId && processingStatus && ['queued','uploaded','processing'].includes(processingStatus.status)) && (
            <div className="db-progress-card">
              <div className="progress-header">
                <h3>Processing...</h3>
                <span>{processingStatus?.progress || 0}%</span>
              </div>
              <div className="progress-bar-wrapper">
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${processingStatus?.progress || 0}%` }} />
                </div>
              </div>
              <p className="progress-message">{processingStatus?.message || 'Processing…'}</p>
              {Array.isArray(processingStatus?.steps) && processingStatus.steps.length > 0 && (
                <div className="steps-wrapper">
                  <div className="steps">
                    {processingStatus.steps.map((s: any) => {
                      const reached = (processingStatus?.progress || 0) >= s.target;
                      return (
                        <div key={s.name} className={`step ${reached ? 'done' : ''}`}>
                          <div className="step-marker">{reached ? '✓' : ''}</div>
                          <div className="step-label">{s.label}</div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
              {processingStatus?.logs && (
                <div className="logs">
                  <small><strong>Recent activity:</strong></small>
                  <ul>
                    {/* Show local immediate note first, then latest server logs */}
                    {localActivity.map((m, idx) => (
                      <li key={`local-${idx}`}>{m}</li>
                    ))}
                    {(processingStatus.logs.slice(-8).reverse()).map((l: any) => (
                      <li key={l.ts}>{new Date(l.ts).toLocaleTimeString()} - {l.message}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Result (Outbound only) */}
          {processingStatus?.status === 'completed' && (
            <div className="result success">
              <h3>Processing Complete</h3>
              <p>{processingStatus?.message}</p>
            </div>
          )}

          {processingStatus?.status === 'completed' && (
            <div className="results-container">
              <div className="table-preview single results-dialog results-center" style={{ width: '100%' }}>
                <h4>Processed Results</h4>
                {outboundPreview ? (
                  <div className="table-scroll" style={{ width: '100%' }}>
                  <table>
                    <thead>
                      <tr>
                        <th className="index-col">#</th>
                        {outboundPreview.columns.map((c) => (<th key={c}>{c}</th>))}
                      </tr>
                    </thead>
                    <tbody>
                      {outboundPreview.rows.map((r, i) => (
                        <tr key={i}>
                          <td className="index-col">{(page - 1) * pageSize + i + 1}</td>
                          {outboundPreview.columns.map((c) => (<td key={c}>{r?.[c]}</td>))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                  </div>
                ) : (
                  <small>Loading preview…</small>
                )}
                <div className="pager">
                  <button
                    type="button"
                    onClick={() => setPage(p => Math.max(1, p - 1))}
                    disabled={pageLoading || page <= 1}
                  >
                    ◀ Prev
                  </button>
                  <span className="page-info">Page {page}</span>
                  <button
                    type="button"
                    onClick={() => setPage(p => p + 1)}
                    disabled={pageLoading || atEnd}
                  >
                    Next ▶
                  </button>
                </div>
                {processingStatus?.output_file && (
                  <div style={{ display: 'flex', justifyContent: 'center', marginTop: 8 }}>
                    <button type="button" className="small-primary-button" onClick={() => { downloadFile(processingStatus.output_file).catch(() => {}); }}>
                      Download Processed Results
                    </button>
                  </div>
                )}
              </div>
            </div>
          )}

          {message && !processingId && (
            <div className="result success">
              <h3>Success</h3>
              <p>{message}</p>
            </div>
          )}
          {error && (
            <div className="result error">
              <h3>Error</h3>
              <p>{error}</p>
            </div>
          )}
        </div>
      {/* footer removed per request; Reset now adjacent to Format */}
    </div>
  );
};

export default DatabaseConnect;

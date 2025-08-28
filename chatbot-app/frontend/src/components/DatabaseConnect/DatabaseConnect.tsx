import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { submitDatabaseTask, getDbProcessingStatus, previewResultFile, downloadFile } from '../../services/api';
import '../FileUpload/FileUpload.css';
import './DatabaseConnect.css';

type TopMode = 'compare' | 'format';
type SourceType = 'table' | 'query';

interface ValidationErrors {
  connectionString?: string;
  query?: string;
  columns?: { name?: string }[];
}

const DEFAULT_PLACEHOLDER = 'Server=localhost;Database=AddressDB;User Id=app_user;Password=YourStrong!Passw0rd;TrustServerCertificate=True;';

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
    return columns.length > 0 && columns.every((name) => name.trim().length > 0);
  }, [connString, sourceType, query, columns]);

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
      arr[index] = { ...(arr[index] || {}), name: value.trim() ? undefined : 'Required' };
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
      next.columns = columns.map(name => ({ name: name.trim() ? undefined : 'Required' }));
    }
    setErrors(next);
    // return validity
    const ok = !next.connectionString && (!next.query) && (!next.columns || next.columns.every(c => !c.name));
    return ok;
  }, [connString, sourceType, query, columns]);

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
    <div className="file-upload-container">
      <div className="file-upload-card">
        <h1>Database connect</h1>
        <p>Connect to your database and select source by table columns or a SQL query.</p>

        {/* Top tabs: Compare | Format */}
        <div className="mode-toggle" role="tablist" aria-label="Database action mode">
          <button
            role="tab"
            aria-selected={false}
            className={''}
            onClick={() => { /* disabled - coming soon */ }}
            disabled
            title="Compare is in progress"
          >
            Compare <span className="soon-pill" aria-hidden>Soon</span>
          </button>
          <button
            role="tab"
            aria-selected={topMode === 'format'}
            className={topMode === 'format' ? 'active' : ''}
            onClick={() => setTopMode('format')}
            disabled={!!submittingAction || !!processingId}
          >
            Format
          </button>
        </div>

        {/* Upcoming feature banner */}
        <div className="notice-soon" role="status" aria-live="polite">
          Compare mode is in progress and will be available soon.
        </div>

        <div className="upload-section">
          {/* Connection string */}
          <div className="input-row">
            <label htmlFor="conn-str" className="input-label">Connection string</label>
            <input
              id="conn-str"
              className={`text-input ${errors.connectionString ? 'input-error' : ''}`}
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
            <small className="hint">Provide a valid database connection string.</small>
          </div>

          {/* Source tabs: Table | SQL Query */}
          <div className="mode-toggle" role="tablist" aria-label="Source type">
            <button
              role="tab"
              aria-selected={sourceType === 'table'}
              className={sourceType === 'table' ? 'active' : ''}
              onClick={() => setSourceType('table')}
              disabled={!!submittingAction || !!processingId}
            >
              Table
            </button>
            <button
              role="tab"
              aria-selected={sourceType === 'query'}
              className={sourceType === 'query' ? 'active' : ''}
              onClick={() => setSourceType('query')}
              disabled={!!submittingAction || !!processingId}
            >
              SQL Query
            </button>
          </div>

          {sourceType === 'table' && (
            <div className="table-config">
              {/* Full width table name */}
              <div className="column-row single">
                <div className="column-field">
                  <label htmlFor="tbl-name">Table name</label>
                  <input
                    id="tbl-name"
                    className="text-input"
                    type="text"
                    placeholder="e.g. addresses, dbo.Addresses"
                    value={tableName}
                    onChange={(e) => setTableName(e.target.value)}
                    disabled={!!submittingAction || !!processingId}
                  />
                  <small className="hint">Database table to read from.</small>
                </div>
              </div>

              {/* Single UniqueId field (optional, acts as primary key) */}
              <div className="column-row single">
                <div className="column-field">
                  <label htmlFor="uniq-single">column_UniqueId (optional)</label>
                  <input
                    id="uniq-single"
                    className="text-input"
                    type="text"
                    placeholder="e.g. id, record_id"
                    value={uniqueId}
                    onChange={(e) => setUniqueId(e.target.value)}
                    disabled={!!submittingAction || !!processingId}
                  />
                  <small className="hint">Acts as primary key. Will not be repeated.</small>
                </div>
              </div>

              {/* Repeatable column_name fields */}
              {columns.map((name, idx) => (
                <div className="column-row single" key={idx}>
                  <div className="column-field">
                    <label htmlFor={`name-${idx}`}>column_name <span className="req">(required)</span></label>
                    <div className="name-with-add">
                      <input
                        id={`name-${idx}`}
                        className={`text-input ${errors.columns?.[idx]?.name ? 'input-error' : ''}`}
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
                  </div>
                </div>
              ))}
            </div>
          )}

          {sourceType === 'query' && (
            <div className="query-config">
              <label htmlFor="sql-text">SQL Query <span className="req">(required)</span></label>
              <textarea
                id="sql-text"
                className={`text-area ${errors.query ? 'input-error' : ''}`}
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

          <div className="button-group">
            <button
              onClick={() => handleSubmit('format')}
              disabled={!canSubmit || !!submittingAction || isProcessing || isCompleted}
              className="upload-button"
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
              className="dc-reset-button"
            >
              Reset
            </button>
          </div>

          {/* Progress & activity */}
          {(processingId && processingStatus && ['queued','uploaded','processing'].includes(processingStatus.status)) && (
            <div className="progress-section">
              <div className="progress-bar">
                <div className="progress-fill" style={{ width: `${processingStatus?.progress || 0}%` }} />
              </div>
              <p>{processingStatus?.progress || 0}% - {processingStatus?.message || 'Processing…'}</p>
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
    </div>
  );
};

export default DatabaseConnect;

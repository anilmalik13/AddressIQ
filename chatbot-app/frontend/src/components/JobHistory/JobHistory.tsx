import React, { useEffect, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { loadJobHistory } from '../../store/slices/fileUploadSlice';
import { downloadFile } from '../../services/api';
import '../../styles/shared.css';
import './JobHistory.css';

const JobHistory: React.FC = () => {
    const dispatch = useAppDispatch();
    const { jobHistory, loadingJobs } = useAppSelector((state) => state.fileUpload);
    const [filter, setFilter] = useState<string>('all');
    const [fileNotAvailable, setFileNotAvailable] = useState<Set<string>>(new Set());

    useEffect(() => {
        // Load job history on mount
        dispatch(loadJobHistory());
    }, [dispatch]);

    const handleRefresh = () => {
        dispatch(loadJobHistory());
    };

    const handleDownload = async (filename: string) => {
        try {
            await downloadFile(filename);
        } catch (error: any) {
            console.error('Download failed:', error);
            const errorMsg = error?.response?.data?.error || error?.message || 'Failed to download file';
            const status = error?.response?.status;
            
            if (status === 410) {
                alert('This file has expired and is no longer available for download');
            } else if (status === 404) {
                // Mark file as not available
                setFileNotAvailable(prev => new Set(prev).add(filename));
                alert('File not found. It may have been deleted or is no longer available.');
            } else {
                alert(errorMsg);
            }
        }
    };

    const getStatusBadge = (status: string) => {
        const statusColors: Record<string, string> = {
            completed: '#4caf50',
            failed: '#f44336',
            error: '#f44336',
            processing: '#ff9800',
            queued: '#2196f3',
            uploaded: '#2196f3'
        };

        return (
            <span
                style={{
                    background: statusColors[status] || '#999',
                    color: 'white',
                    padding: '4px 12px',
                    borderRadius: '4px',
                    fontSize: '12px',
                    fontWeight: 'bold',
                    textTransform: 'uppercase',
                    display: 'inline-block'
                }}
            >
                {status}
            </span>
        );
    };

    const formatDate = (dateStr?: string) => {
        if (!dateStr) return '-';
        try {
            const date = new Date(dateStr);
            return date.toLocaleString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return dateStr;
        }
    };

    const getTimeRemaining = (expiresAt?: string) => {
        if (!expiresAt) return null;
        try {
            const expires = new Date(expiresAt);
            const now = new Date();
            const diff = expires.getTime() - now.getTime();
            
            if (diff <= 0) return 'Expired';
            
            const days = Math.floor(diff / (1000 * 60 * 60 * 24));
            const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            
            // Build compact time string for single line display
            if (days > 0) {
                return `${days}d ${hours}hrs`;
            }
            if (hours > 0) {
                return `${hours}hrs`;
            }
            if (minutes > 0) {
                return `${minutes}min`;
            }
            
            return '< 1min';
        } catch {
            return null;
        }
    };

    const isExpired = (expiresAt?: string) => {
        if (!expiresAt) return false;
        try {
            const expires = new Date(expiresAt);
            const now = new Date();
            return now.getTime() > expires.getTime();
        } catch {
            return false;
        }
    };

    const filteredJobs = filter === 'all' 
        ? jobHistory 
        : jobHistory.filter(job => job.status === filter);

    return (
        <div className="modern-container">
            {/* Hero Section */}
            <div className="modern-hero">
                <h1 className="modern-hero-title">Processing History</h1>
                <p className="modern-hero-subtitle">View and manage your file processing jobs</p>
            </div>

            {/* Main Card */}
            <div className="modern-card">
                {/* Info Card about retention policy */}
                <div className="modern-info-cards">
                    <div className="modern-info-card modern-info-card-green">
                        <div className="modern-info-card-content">
                            <div className="modern-info-card-title">File Retention Policy</div>
                            <div className="modern-info-card-text">
                                Processed files are automatically deleted <strong>7 days</strong> after upload. 
                                Download your files promptly as deleted files cannot be recovered.
                            </div>
                        </div>
                    </div>
                </div>

                {/* Filter Bar with Refresh */}
                <div className="history-controls">
                    <div className="filter-chips">
                        <button
                            className={`filter-chip ${filter === 'all' ? 'active' : ''}`}
                            onClick={() => setFilter('all')}
                        >
                            All ({jobHistory.length})
                        </button>
                        <button
                            className={`filter-chip ${filter === 'completed' ? 'active' : ''}`}
                            onClick={() => setFilter('completed')}
                        >
                            Completed ({jobHistory.filter(j => j.status === 'completed').length})
                        </button>
                        <button
                            className={`filter-chip ${filter === 'processing' ? 'active' : ''}`}
                            onClick={() => setFilter('processing')}
                        >
                            Processing ({jobHistory.filter(j => j.status === 'processing').length})
                        </button>
                        <button
                            className={`filter-chip ${filter === 'failed' ? 'active' : ''}`}
                            onClick={() => setFilter('failed')}
                        >
                            Failed ({jobHistory.filter(j => j.status === 'failed' || j.status === 'error').length})
                        </button>
                    </div>
                    <button onClick={handleRefresh} className="modern-btn modern-btn-secondary" disabled={loadingJobs}>
                        {loadingJobs ? '⟳ Refreshing...' : '↻ Refresh'}
                    </button>
                </div>

                {loadingJobs ? (
                    <div className="loading-state">
                        <div className="spinner"></div>
                        <p>Loading job history...</p>
                    </div>
                ) : filteredJobs.length === 0 ? (
                    <div className="empty-state">
                        <h3>No jobs found</h3>
                        <p>{filter === 'all' ? 'Upload a file to get started!' : `No ${filter} jobs found.`}</p>
                    </div>
                ) : (
                <div className="jobs-table-wrapper">
                    <table className="jobs-table">
                        <thead>
                            <tr>
                                <th>Filename</th>
                                <th>Source</th>
                                <th>Status</th>
                                <th>Progress</th>
                                <th>Uploaded</th>
                                <th>Completed</th>
                                <th>Expires</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredJobs.map((job) => (
                                <tr key={job.job_id} className={`job-row ${job.status}`}>
                                    <td>
                                        <div className="filename-cell">
                                            <span className="filename" title={job.filename}>
                                                {job.filename}
                                            </span>
                                        </div>
                                    </td>
                                    <td>
                                        <span className="component-badge">
                                            {job.component === 'compare' ? 'Compare' : 'Upload'}
                                        </span>
                                    </td>
                                    <td>{getStatusBadge(job.status)}</td>
                                    <td>
                                        <div className="progress-cell">
                                            <div className="mini-progress-bar">
                                                <div
                                                    className="mini-progress-fill"
                                                    style={{ width: `${job.progress}%` }}
                                                />
                                            </div>
                                            <span className="progress-text">{job.progress}%</span>
                                        </div>
                                    </td>
                                    <td>{formatDate(job.created_at)}</td>
                                    <td>{formatDate(job.finished_at)}</td>
                                    <td>
                                        {job.expires_at ? (
                                            <span className="expires-badge">
                                                {getTimeRemaining(job.expires_at)}
                                            </span>
                                        ) : (
                                            '-'
                                        )}
                                    </td>
                                    <td>
                                        <div className="action-buttons">
                                            {job.status === 'completed' && job.output_file && fileNotAvailable.has(job.output_file) && (
                                                <span className="file-not-available-indicator" title="File not found on server">
                                                    File Not Available
                                                </span>
                                            )}
                                            {job.status === 'completed' && job.output_file && !fileNotAvailable.has(job.output_file) && isExpired(job.expires_at) && (
                                                <span className="expired-indicator" title="File has expired and been deleted">
                                                    Expired
                                                </span>
                                            )}
                                            {job.status === 'completed' && job.output_file && !fileNotAvailable.has(job.output_file) && !isExpired(job.expires_at) && (
                                                <button
                                                    onClick={() => handleDownload(job.output_file!)}
                                                    className="download-btn"
                                                    title="Download processed file (expires in specified time)"
                                                >
                                                    Download
                                                </button>
                                            )}
                                            {(job.status === 'failed' || job.status === 'error') && (
                                                <span className="error-indicator" title={job.error || 'Processing failed'}>
                                                    Error
                                                </span>
                                            )}
                                            {(job.status === 'processing' || job.status === 'queued') && (
                                                <span className="processing-indicator">In Progress</span>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
            </div>
        </div>
    );
};

export default JobHistory;

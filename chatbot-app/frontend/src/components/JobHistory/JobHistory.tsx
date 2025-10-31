import React, { useEffect, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../../hooks/redux';
import { loadJobHistory } from '../../store/slices/fileUploadSlice';
import { downloadFile } from '../../services/api';
import './JobHistory.css';

const JobHistory: React.FC = () => {
    const dispatch = useAppDispatch();
    const { jobHistory, loadingJobs } = useAppSelector((state) => state.fileUpload);
    const [filter, setFilter] = useState<string>('all');

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
        } catch (error) {
            console.error('Download failed:', error);
            alert('Failed to download file');
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

    const filteredJobs = filter === 'all' 
        ? jobHistory 
        : jobHistory.filter(job => job.status === filter);

    return (
        <div className="job-history-container">
            <div className="job-history-header">
                <div>
                    <h1>Processing History</h1>
                    <p>View and manage your file processing jobs</p>
                </div>
                <button onClick={handleRefresh} className="refresh-button" disabled={loadingJobs}>
                    {loadingJobs ? 'Refreshing...' : 'Refresh'}
                </button>
            </div>

            <div className="filter-bar">
                <button
                    className={`filter-button ${filter === 'all' ? 'active' : ''}`}
                    onClick={() => setFilter('all')}
                >
                    All ({jobHistory.length})
                </button>
                <button
                    className={`filter-button ${filter === 'completed' ? 'active' : ''}`}
                    onClick={() => setFilter('completed')}
                >
                    Completed ({jobHistory.filter(j => j.status === 'completed').length})
                </button>
                <button
                    className={`filter-button ${filter === 'processing' ? 'active' : ''}`}
                    onClick={() => setFilter('processing')}
                >
                    Processing ({jobHistory.filter(j => j.status === 'processing' || j.status === 'queued').length})
                </button>
                <button
                    className={`filter-button ${filter === 'failed' ? 'active' : ''}`}
                    onClick={() => setFilter('failed')}
                >
                    Failed ({jobHistory.filter(j => j.status === 'failed' || j.status === 'error').length})
                </button>
            </div>

            {loadingJobs ? (
                <div className="loading-state">
                    <div className="spinner"></div>
                    <p>Loading job history...</p>
                </div>
            ) : filteredJobs.length === 0 ? (
                <div className="empty-state">
                    <div className="empty-icon">📋</div>
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
                                <th>Created</th>
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
                                            {job.status === 'completed' && job.output_file && (
                                                <button
                                                    onClick={() => handleDownload(job.output_file!)}
                                                    className="download-btn"
                                                    title="Download processed file"
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
    );
};

export default JobHistory;

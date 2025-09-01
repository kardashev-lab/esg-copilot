import React, { useState, useEffect } from 'react';
import {
  DocumentChartBarIcon,
  PlusIcon,
  EyeIcon,
  ArrowDownTrayIcon,
  PencilIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import { API_ENDPOINTS } from '../../config/api';

interface Report {
  id: string;
  title: string;
  framework: string;
  status: string;
  sections: number;
  createdAt: string;
  lastModified: string;
}

interface ReportTemplate {
  name: string;
  sections: string[];
  description: string;
}

const Reports: React.FC = () => {
  const [reports, setReports] = useState<Report[]>([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedFramework, setSelectedFramework] = useState('');
  const [templates, setTemplates] = useState<Record<string, ReportTemplate>>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    title: '',
    framework: '',
    description: '',
  });

  const frameworks = [
    { id: 'gri', name: 'GRI Standards', description: 'Comprehensive sustainability reporting' },
    { id: 'sasb', name: 'SASB Standards', description: 'Industry-specific financial materiality' },
    { id: 'tcfd', name: 'TCFD Framework', description: 'Climate-related financial disclosures' },
    { id: 'csrd', name: 'CSRD Directive', description: 'EU sustainability reporting' },
  ];

  useEffect(() => {
    fetchReports();
    fetchTemplates();
  }, []);

  const fetchReports = async () => {
    try {
      // For now, use mock data since backend doesn't have a list endpoint
      setReports([
        {
          id: '1',
          title: 'Annual Sustainability Report 2024',
          framework: 'GRI',
          status: 'draft',
          sections: 8,
          createdAt: '2024-01-15',
          lastModified: '2024-01-15',
        },
        {
          id: '2',
          title: 'TCFD Climate Report',
          framework: 'TCFD',
          status: 'completed',
          sections: 4,
          createdAt: '2024-01-10',
          lastModified: '2024-01-12',
        },
      ]);
    } catch (error) {
      console.error('Error fetching reports:', error);
      setError('Failed to load reports');
    }
  };

  const fetchTemplates = async () => {
    try {
      const response = await fetch(`${API_ENDPOINTS.REPORTS}/templates`);
      if (response.ok) {
        const data = await response.json();
        setTemplates(data.templates);
      }
    } catch (error) {
      console.error('Error fetching templates:', error);
    }
  };

  const handleCreateReport = async () => {
    if (!formData.title || !formData.framework) {
      setError('Please fill in all required fields');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const template = templates[formData.framework.toUpperCase()];
      const sections = template ? template.sections : [];

      const response = await fetch(`${API_ENDPOINTS.REPORTS}/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: formData.title,
          framework: formData.framework.toUpperCase(),
          sections: sections,
          company_data_documents: [],
          peer_reports: [],
          custom_instructions: formData.description,
        }),
      });

      if (response.ok) {
        const newReport = await response.json();
        setReports(prev => [...prev, {
          id: newReport.id,
          title: newReport.title,
          framework: newReport.framework,
          status: newReport.status,
          sections: newReport.sections.length,
          createdAt: new Date().toISOString().split('T')[0],
          lastModified: new Date().toISOString().split('T')[0],
        }]);
        setSuccess(`Successfully created "${formData.title}"`);
        setShowCreateModal(false);
        setFormData({ title: '', framework: '', description: '' });
      } else {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to create report');
      }
    } catch (error) {
      console.error('Create report error:', error);
      setError(error instanceof Error ? error.message : 'Failed to create report');
    } finally {
      setLoading(false);
    }
  };

  const handleViewReport = (reportId: string) => {
    // In a real implementation, this would navigate to a report viewer
    alert(`Viewing report ${reportId}. This would open a report viewer in a real implementation.`);
  };

  const handleEditReport = (reportId: string) => {
    // In a real implementation, this would navigate to a report editor
    alert(`Editing report ${reportId}. This would open a report editor in a real implementation.`);
  };

  const handleExportReport = async (reportId: string, format: string = 'pdf') => {
    try {
      const response = await fetch(`${API_ENDPOINTS.REPORTS}/${reportId}/export?format=${format}`, {
        method: 'POST',
      });

      if (response.ok) {
        const data = await response.json();
        setSuccess(`Report exported successfully in ${format.toUpperCase()} format`);
        
        // In a real implementation, this would trigger a download
        // For now, just show the success message
        console.log('Export URL:', data.download_url);
      } else {
        throw new Error('Export failed');
      }
    } catch (error) {
      console.error('Export error:', error);
      setError('Failed to export report');
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'draft':
        return <span className="badge-warning">Draft</span>;
      case 'completed':
        return <span className="badge-success">Completed</span>;
      case 'in_progress':
        return <span className="badge-info">In Progress</span>;
      default:
        return <span className="badge">Unknown</span>;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
          <p className="text-sm text-gray-500">
            Generate and manage sustainability reports using AI assistance
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="btn-primary flex items-center space-x-2"
        >
          <PlusIcon className="h-5 w-5" />
          <span>Create Report</span>
        </button>
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-500 mr-2" />
            <span className="text-red-700">{error}</span>
            <button
              onClick={() => setError(null)}
              className="ml-auto text-red-500 hover:text-red-700"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {success && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center">
            <CheckCircleIcon className="h-5 w-5 text-green-500 mr-2" />
            <span className="text-green-700">{success}</span>
            <button
              onClick={() => setSuccess(null)}
              className="ml-auto text-green-500 hover:text-green-700"
            >
              ×
            </button>
          </div>
        </div>
      )}

      {/* Reports Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {reports.map((report) => (
          <div key={report.id} className="card-hover">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <DocumentChartBarIcon className="h-8 w-8 text-purple-500" />
                <div>
                  <h3 className="text-sm font-medium text-gray-900">{report.title}</h3>
                  <p className="text-xs text-gray-500">{report.framework} Framework</p>
                </div>
              </div>
              {getStatusBadge(report.status)}
            </div>
            
            <div className="mt-3 text-xs text-gray-500">
              <p>{report.sections} sections • Created {report.createdAt}</p>
            </div>
            
            <div className="mt-4 flex space-x-2">
              <button 
                onClick={() => handleViewReport(report.id)}
                className="flex-1 btn-outline text-xs py-2 px-3 flex items-center justify-center space-x-1"
              >
                <EyeIcon className="h-4 w-4" />
                <span>View</span>
              </button>
              <button 
                onClick={() => handleEditReport(report.id)}
                className="flex-1 btn-outline text-xs py-2 px-3 flex items-center justify-center space-x-1"
              >
                <PencilIcon className="h-4 w-4" />
                <span>Edit</span>
              </button>
              <button 
                onClick={() => handleExportReport(report.id)}
                className="flex-1 btn-outline text-xs py-2 px-3 flex items-center justify-center space-x-1"
              >
                <ArrowDownTrayIcon className="h-4 w-4" />
                <span>Export</span>
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* Create Report Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-lg">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Create New Report</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Report Title *
                </label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                  className="input-field"
                  placeholder="Enter report title..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Framework *
                </label>
                <select 
                  value={formData.framework}
                  onChange={(e) => setFormData(prev => ({ ...prev, framework: e.target.value }))}
                  className="input-field"
                >
                  <option value="">Select a framework</option>
                  {frameworks.map((framework) => (
                    <option key={framework.id} value={framework.id}>
                      {framework.name}
                    </option>
                  ))}
                </select>
                {formData.framework && templates[formData.framework.toUpperCase()] && (
                  <p className="text-xs text-gray-500 mt-1">
                    {templates[formData.framework.toUpperCase()].description}
                  </p>
                )}
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  className="input-field"
                  rows={3}
                  placeholder="Describe the purpose and scope of this report..."
                />
              </div>
            </div>

            <div className="mt-6 flex space-x-3">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setFormData({ title: '', framework: '', description: '' });
                }}
                className="btn-secondary flex-1"
                disabled={loading}
              >
                Cancel
              </button>
              <button 
                onClick={handleCreateReport}
                disabled={loading || !formData.title || !formData.framework}
                className="btn-primary flex-1"
              >
                {loading ? 'Creating...' : 'Create Report'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Reports;

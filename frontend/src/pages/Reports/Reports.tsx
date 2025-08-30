import React, { useState } from 'react';
import {
  DocumentChartBarIcon,
  PlusIcon,
  EyeIcon,
  ArrowDownTrayIcon,
  PencilIcon,
} from '@heroicons/react/24/outline';

const Reports: React.FC = () => {
  const [reports, setReports] = useState([
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

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedFramework, setSelectedFramework] = useState('');

  const frameworks = [
    { id: 'gri', name: 'GRI Standards', description: 'Comprehensive sustainability reporting' },
    { id: 'sasb', name: 'SASB Standards', description: 'Industry-specific financial materiality' },
    { id: 'tcfd', name: 'TCFD Framework', description: 'Climate-related financial disclosures' },
    { id: 'csrd', name: 'CSRD Directive', description: 'EU sustainability reporting' },
  ];

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
              <button className="flex-1 btn-outline text-xs py-1">
                <EyeIcon className="h-4 w-4 mr-1" />
                View
              </button>
              <button className="flex-1 btn-outline text-xs py-1">
                <PencilIcon className="h-4 w-4 mr-1" />
                Edit
              </button>
              <button className="flex-1 btn-outline text-xs py-1">
                <ArrowDownTrayIcon className="h-4 w-4 mr-1" />
                Export
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
                  Report Title
                </label>
                <input
                  type="text"
                  className="input-field"
                  placeholder="Enter report title..."
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Framework
                </label>
                <select className="input-field">
                  <option value="">Select a framework</option>
                  {frameworks.map((framework) => (
                    <option key={framework.id} value={framework.id}>
                      {framework.name}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Description
                </label>
                <textarea
                  className="input-field"
                  rows={3}
                  placeholder="Describe the purpose and scope of this report..."
                />
              </div>
            </div>

            <div className="mt-6 flex space-x-3">
              <button
                onClick={() => setShowCreateModal(false)}
                className="btn-secondary flex-1"
              >
                Cancel
              </button>
              <button className="btn-primary flex-1">
                Create Report
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Reports;

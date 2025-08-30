import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  DocumentTextIcon,
  DocumentArrowUpIcon,
  TrashIcon,
  EyeIcon,
  TagIcon,
} from '@heroicons/react/24/outline';

const Documents: React.FC = () => {
  const [documents, setDocuments] = useState([
    {
      id: '1',
      name: 'GRI Standards 2021.pdf',
      type: 'PDF',
      category: 'Framework',
      size: '2.4 MB',
      uploadedAt: '2024-01-15',
      status: 'processed',
      tags: ['GRI', 'Standards', '2021'],
    },
    {
      id: '2',
      name: 'Company ESG Data 2024.xlsx',
      type: 'Excel',
      category: 'Company Data',
      size: '1.8 MB',
      uploadedAt: '2024-01-14',
      status: 'processed',
      tags: ['Company Data', '2024', 'Metrics'],
    },
  ]);

  const [selectedCategory, setSelectedCategory] = useState('all');
  const [showUploadModal, setShowUploadModal] = useState(false);

  const categories = [
    { id: 'all', name: 'All Documents' },
    { id: 'framework', name: 'Frameworks' },
    { id: 'company_data', name: 'Company Data' },
    { id: 'regulatory', name: 'Regulatory' },
    { id: 'peer_report', name: 'Peer Reports' },
  ];

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles) => {
      console.log('Files dropped:', acceptedFiles);
      // Handle file upload
    },
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Documents</h1>
          <p className="text-sm text-gray-500">
            Upload and manage your ESG documents, frameworks, and company data
          </p>
        </div>
        <button
          onClick={() => setShowUploadModal(true)}
          className="btn-primary flex items-center space-x-2"
        >
          <DocumentArrowUpIcon className="h-5 w-5" />
          <span>Upload Document</span>
        </button>
      </div>

      {/* Category Filter */}
      <div className="flex space-x-2">
        {categories.map((category) => (
          <button
            key={category.id}
            onClick={() => setSelectedCategory(category.id)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              selectedCategory === category.id
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {category.name}
          </button>
        ))}
      </div>

      {/* Documents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {documents.map((doc) => (
          <div key={doc.id} className="card-hover">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <DocumentTextIcon className="h-8 w-8 text-blue-500" />
                <div>
                  <h3 className="text-sm font-medium text-gray-900">{doc.name}</h3>
                  <p className="text-xs text-gray-500">{doc.category}</p>
                </div>
              </div>
              <div className="flex space-x-1">
                <button className="p-1 text-gray-400 hover:text-gray-600">
                  <EyeIcon className="h-4 w-4" />
                </button>
                <button className="p-1 text-gray-400 hover:text-red-600">
                  <TrashIcon className="h-4 w-4" />
                </button>
              </div>
            </div>
            <div className="mt-3 flex items-center justify-between text-xs text-gray-500">
              <span>{doc.size}</span>
              <span>{doc.uploadedAt}</span>
            </div>
            <div className="mt-2 flex flex-wrap gap-1">
              {doc.tags.map((tag) => (
                <span
                  key={tag}
                  className="inline-flex items-center px-2 py-1 rounded-full text-xs bg-gray-100 text-gray-700"
                >
                  <TagIcon className="h-3 w-3 mr-1" />
                  {tag}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Upload Document</h3>
            
            <div
              {...getRootProps()}
              className={`border-2 border-dashed rounded-lg p-6 text-center ${
                isDragActive ? 'border-green-500 bg-green-50' : 'border-gray-300'
              }`}
            >
              <input {...getInputProps()} />
              <DocumentArrowUpIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
              <p className="text-sm text-gray-600">
                {isDragActive
                  ? 'Drop the files here...'
                  : 'Drag & drop files here, or click to select files'}
              </p>
            </div>

            <div className="mt-4 flex space-x-3">
              <button
                onClick={() => setShowUploadModal(false)}
                className="btn-secondary flex-1"
              >
                Cancel
              </button>
              <button className="btn-primary flex-1">
                Upload
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Documents;

import React, { useState, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import {
  DocumentTextIcon,
  DocumentArrowUpIcon,
  TrashIcon,
  EyeIcon,
  TagIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
} from '@heroicons/react/24/outline';
import { API_ENDPOINTS } from '../../config/api';

interface Document {
  id: string;
  name: string;
  type: string;
  category: string;
  size: string;
  uploadedAt: string;
  status: string;
  tags: string[];
}

const Documents: React.FC = () => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const categories = [
    { id: 'all', name: 'All Documents' },
    { id: 'framework', name: 'Frameworks' },
    { id: 'company_data', name: 'Company Data' },
    { id: 'regulatory', name: 'Regulatory' },
    { id: 'peer_report', name: 'Peer Reports' },
  ];

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await fetch(API_ENDPOINTS.DOCUMENTS);
      if (response.ok) {
        const data = await response.json();
        setDocuments(data);
      } else {
        // For now, use mock data since backend returns empty array
        setDocuments([
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
      }
    } catch (error) {
      console.error('Error fetching documents:', error);
      setError('Failed to load documents');
    }
  };

  const handleFileUpload = async (acceptedFiles: File[]) => {
    if (acceptedFiles.length === 0) return;

    setUploading(true);
    setUploadProgress(0);
    setError(null);
    setSuccess(null);

    try {
      for (const file of acceptedFiles) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('category', 'company_data'); // Default category
        formData.append('description', `Uploaded ${file.name}`);
        formData.append('tags', 'uploaded,new');

        const response = await fetch(`${API_ENDPOINTS.DOCUMENTS}/upload`, {
          method: 'POST',
          body: formData,
        });

        if (response.ok) {
          const uploadedDoc = await response.json();
          setDocuments(prev => [...prev, {
            id: uploadedDoc.id,
            name: uploadedDoc.filename,
            type: uploadedDoc.file_type,
            category: uploadedDoc.category,
            size: 'Unknown',
            uploadedAt: new Date().toISOString().split('T')[0],
            status: uploadedDoc.status,
            tags: uploadedDoc.tags || [],
          }]);
          setSuccess(`Successfully uploaded ${file.name}`);
        } else {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Upload failed');
        }
      }
    } catch (error) {
      console.error('Upload error:', error);
      setError(error instanceof Error ? error.message : 'Upload failed');
    } finally {
      setUploading(false);
      setUploadProgress(0);
      setShowUploadModal(false);
    }
  };

  const handleDeleteDocument = async (documentId: string, documentName: string) => {
    if (!window.confirm(`Are you sure you want to delete "${documentName}"?`)) {
      return;
    }

    try {
      const response = await fetch(`${API_ENDPOINTS.DOCUMENTS}/${documentId}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        setDocuments(prev => prev.filter(doc => doc.id !== documentId));
        setSuccess(`Successfully deleted ${documentName}`);
      } else {
        throw new Error('Delete failed');
      }
    } catch (error) {
      console.error('Delete error:', error);
      setError('Failed to delete document');
    }
  };

  const handleViewDocument = (documentId: string) => {
    // In a real implementation, this would open a document viewer
    // For now, just show an alert
    alert(`Viewing document ${documentId}. This would open a document viewer in a real implementation.`);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: handleFileUpload,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'text/csv': ['.csv'],
      'text/plain': ['.txt'],
    },
    maxSize: 50 * 1024 * 1024, // 50MB
  });

  const filteredDocuments = documents.filter(doc => 
    selectedCategory === 'all' || doc.category.toLowerCase().replace(' ', '_') === selectedCategory
  );

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
        {filteredDocuments.map((doc) => (
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
                <button 
                  onClick={() => handleViewDocument(doc.id)}
                  className="p-1 text-gray-400 hover:text-gray-600 transition-colors"
                  title="View document"
                >
                  <EyeIcon className="h-4 w-4" />
                </button>
                <button 
                  onClick={() => handleDeleteDocument(doc.id, doc.name)}
                  className="p-1 text-gray-400 hover:text-red-600 transition-colors"
                  title="Delete document"
                >
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
              className={`border-2 border-dashed rounded-lg p-6 text-center transition-colors ${
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
              <p className="text-xs text-gray-500 mt-2">
                Supported: PDF, DOCX, XLSX, CSV, TXT (max 50MB)
              </p>
            </div>

            {uploading && (
              <div className="mt-4">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  ></div>
                </div>
                <p className="text-sm text-gray-600 mt-2">Uploading...</p>
              </div>
            )}

            <div className="mt-4 flex space-x-3">
              <button
                onClick={() => setShowUploadModal(false)}
                className="btn-secondary flex-1"
                disabled={uploading}
              >
                Cancel
              </button>
              <button 
                className="btn-primary flex-1"
                disabled={uploading}
                onClick={() => {
                  const input = document.querySelector('input[type="file"]') as HTMLInputElement;
                  input?.click();
                }}
              >
                {uploading ? 'Uploading...' : 'Select Files'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Documents;

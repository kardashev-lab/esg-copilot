import React, { useState, useEffect } from 'react';
import {
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ChartBarIcon,
  DocumentMagnifyingGlassIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { API_ENDPOINTS } from '../../config/api';

const Compliance: React.FC = () => {
  const [selectedFramework, setSelectedFramework] = useState('gri');
  const [complianceData, setComplianceData] = useState({
    gri: { score: 87, gaps: 3, high: 1, medium: 2, low: 0 },
    sasb: { score: 78, gaps: 5, high: 2, medium: 2, low: 1 },
    tcfd: { score: 92, gaps: 2, high: 0, medium: 1, low: 1 },
    csrd: { score: 65, gaps: 8, high: 3, medium: 3, low: 2 },
  });
  const [gaps, setGaps] = useState([
    {
      id: '1',
      framework: 'GRI',
      requirement: 'GRI 2-1: Organizational details',
      severity: 'high',
      description: 'Missing comprehensive organizational profile information',
      recommendation: 'Include detailed company overview, operations, and ownership structure',
      status: 'open',
    },
    {
      id: '2',
      framework: 'GRI',
      requirement: 'GRI 3-1: Material topics identification',
      severity: 'medium',
      description: 'No systematic materiality assessment documented',
      recommendation: 'Conduct stakeholder engagement and materiality assessment process',
      status: 'in_progress',
    },
    {
      id: '3',
      framework: 'SASB',
      requirement: 'Industry classification',
      severity: 'medium',
      description: 'Unclear SASB industry classification',
      recommendation: 'Determine appropriate SASB industry classification and disclose rationale',
      status: 'open',
    },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const frameworks = [
    { id: 'gri', name: 'GRI Standards', color: '#10b981' },
    { id: 'sasb', name: 'SASB Standards', color: '#3b82f6' },
    { id: 'tcfd', name: 'TCFD Framework', color: '#8b5cf6' },
    { id: 'csrd', name: 'CSRD Directive', color: '#f59e0b' },
  ];

  useEffect(() => {
    fetchComplianceData();
  }, [selectedFramework]);

  const fetchComplianceData = async () => {
    try {
      // For now, use mock data since backend doesn't have a compliance endpoint
      // In a real implementation, this would call the compliance API
      console.log(`Fetching compliance data for ${selectedFramework}`);
    } catch (error) {
      console.error('Error fetching compliance data:', error);
    }
  };

  const handleRunAnalysis = async () => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // Simulate API call to run compliance analysis
      await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate processing time

      // In a real implementation, this would call the compliance analysis API
      const response = await fetch(`${API_ENDPOINTS.COMPLIANCE}/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          framework: selectedFramework.toUpperCase(),
          include_documents: true,
          include_peer_comparison: true,
        }),
      });

      if (response.ok) {
        // For now, simulate updated data
        const updatedGaps = [
          {
            id: '4',
            framework: selectedFramework.toUpperCase(),
            requirement: `${selectedFramework.toUpperCase()} 1-1: New requirement`,
            severity: 'medium',
            description: 'New compliance gap identified during analysis',
            recommendation: 'Implement new compliance measures',
            status: 'open',
          },
          ...gaps,
        ];
        setGaps(updatedGaps);
        setSuccess(`Compliance analysis completed for ${selectedFramework.toUpperCase()}`);
      } else {
        throw new Error('Analysis failed');
      }
    } catch (error) {
      console.error('Analysis error:', error);
      setError('Failed to run compliance analysis. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'text-red-600 bg-red-100';
      case 'medium':
        return 'text-yellow-600 bg-yellow-100';
      case 'low':
        return 'text-green-600 bg-green-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'resolved':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'in_progress':
        return <ChartBarIcon className="h-5 w-5 text-blue-500" />;
      default:
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
    }
  };

  const chartData = frameworks.map(framework => ({
    name: framework.name,
    score: complianceData[framework.id as keyof typeof complianceData].score,
    color: framework.color,
  }));

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Compliance</h1>
        <p className="text-sm text-gray-500">
          Monitor your compliance status across ESG frameworks and identify gaps
        </p>
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

      {/* Framework Selector */}
      <div className="flex space-x-2">
        {frameworks.map((framework) => (
          <button
            key={framework.id}
            onClick={() => setSelectedFramework(framework.id)}
            className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${
              selectedFramework === framework.id
                ? 'bg-green-100 text-green-700'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {framework.name}
          </button>
        ))}
      </div>

      {/* Compliance Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <div className="flex items-center">
            <ShieldCheckIcon className="h-8 w-8 text-green-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Overall Score</p>
              <p className="text-2xl font-semibold text-gray-900">
                {complianceData[selectedFramework as keyof typeof complianceData].score}%
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <ExclamationTriangleIcon className="h-8 w-8 text-yellow-500" />
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Gaps</p>
              <p className="text-2xl font-semibold text-gray-900">
                {complianceData[selectedFramework as keyof typeof complianceData].gaps}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="h-8 w-8 rounded-full bg-red-100 flex items-center justify-center">
              <span className="text-red-600 font-bold text-sm">H</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">High Priority</p>
              <p className="text-2xl font-semibold text-gray-900">
                {complianceData[selectedFramework as keyof typeof complianceData].high}
              </p>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="h-8 w-8 rounded-full bg-yellow-100 flex items-center justify-center">
              <span className="text-yellow-600 font-bold text-sm">M</span>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Medium Priority</p>
              <p className="text-2xl font-semibold text-gray-900">
                {complianceData[selectedFramework as keyof typeof complianceData].medium}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Compliance Chart */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Framework Comparison</h3>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="score" fill="#10b981" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Gaps Analysis */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Compliance Gaps</h3>
          <button 
            onClick={handleRunAnalysis}
            disabled={loading}
            className="btn-primary flex items-center space-x-2"
          >
            {loading ? (
              <>
                <ArrowPathIcon className="h-4 w-4 animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <DocumentMagnifyingGlassIcon className="h-4 w-4" />
                <span>Run Analysis</span>
              </>
            )}
          </button>
        </div>

        <div className="space-y-4">
          {gaps.map((gap) => (
            <div key={gap.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2 mb-2">
                    {getStatusIcon(gap.status)}
                    <h4 className="text-sm font-medium text-gray-900">{gap.requirement}</h4>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSeverityColor(gap.severity)}`}>
                      {gap.severity.toUpperCase()}
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 mb-2">{gap.description}</p>
                  <p className="text-sm text-gray-700">
                    <strong>Recommendation:</strong> {gap.recommendation}
                  </p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Compliance;

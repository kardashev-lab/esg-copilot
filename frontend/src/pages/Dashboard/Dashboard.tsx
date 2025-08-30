import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  DocumentTextIcon,
  ChatBubbleLeftRightIcon,
  ShieldCheckIcon,
  DocumentChartBarIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

interface DashboardData {
  stats: {
    totalDocuments: number;
    complianceScore: number;
    reportsGenerated: number;
    aiInteractions: number;
  };
  complianceTrends: Array<{
    month: string;
    GRI: number;
    SASB: number;
    TCFD: number;
    CSRD: number;
  }>;
  documentDistribution: Array<{
    name: string;
    value: number;
    color: string;
  }>;
  recentActivities: Array<{
    id: number;
    type: string;
    title: string;
    description: string;
    time: string;
    status: string;
  }>;
}

const Dashboard: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      // TODO: Replace with actual API call
      // const response = await fetch('/api/v1/dashboard');
      // const data = await response.json();
      
      // For now, return empty structure
      const data: DashboardData = {
        stats: {
          totalDocuments: 0,
          complianceScore: 0,
          reportsGenerated: 0,
          aiInteractions: 0
        },
        complianceTrends: [],
        documentDistribution: [],
        recentActivities: []
      };
      
      setDashboardData(data);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('Dashboard data fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const quickActions = [
    {
      title: 'Upload Documents',
      description: 'Add company data, frameworks, or peer reports',
      icon: DocumentTextIcon,
      href: '/documents',
      color: 'bg-blue-500',
    },
    {
      title: 'Start AI Chat',
      description: 'Ask questions about ESG frameworks and compliance',
      icon: ChatBubbleLeftRightIcon,
      href: '/chat',
      color: 'bg-green-500',
    },
    {
      title: 'Generate Report',
      description: 'Create sustainability reports with AI assistance',
      icon: DocumentChartBarIcon,
      href: '/reports',
      color: 'bg-purple-500',
    },
    {
      title: 'Check Compliance',
      description: 'Analyze compliance gaps and get recommendations',
      icon: ShieldCheckIcon,
      href: '/compliance',
      color: 'bg-orange-500',
    },
  ];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'in_progress':
        return <ClockIcon className="h-5 w-5 text-blue-500" />;
      case 'warning':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      default:
        return <ClockIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="animate-pulse">
              <div className="h-24 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-1 text-sm text-red-600">{error}</p>
        </div>
        <div className="text-center py-12">
          <ExclamationTriangleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <p className="text-gray-600">Unable to load dashboard data</p>
          <button 
            onClick={fetchDashboardData}
            className="mt-4 px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-1 text-sm text-gray-500">
          Welcome back! Here's an overview of your ESG activities and compliance status.
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {quickActions.map((action) => (
          <Link
            key={action.title}
            to={action.href}
            className="card-hover group relative overflow-hidden"
          >
            <div className="flex items-center">
              <div className={`${action.color} p-3 rounded-lg`}>
                <action.icon className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <h3 className="text-sm font-medium text-gray-900 group-hover:text-gray-700">
                  {action.title}
                </h3>
                <p className="text-sm text-gray-500">{action.description}</p>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <DocumentTextIcon className="h-8 w-8 text-blue-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Documents</p>
              <p className="text-2xl font-semibold text-gray-900">
                {dashboardData?.stats.totalDocuments || 0}
              </p>
              <div className="flex items-center text-sm text-gray-500">
                <span>Upload documents to get started</span>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ShieldCheckIcon className="h-8 w-8 text-green-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Compliance Score</p>
              <p className="text-2xl font-semibold text-gray-900">
                {dashboardData?.stats.complianceScore || 0}%
              </p>
              <div className="flex items-center text-sm text-gray-500">
                <span>Run compliance check to assess</span>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <DocumentChartBarIcon className="h-8 w-8 text-purple-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Reports Generated</p>
              <p className="text-2xl font-semibold text-gray-900">
                {dashboardData?.stats.reportsGenerated || 0}
              </p>
              <div className="flex items-center text-sm text-gray-500">
                <span>Generate your first report</span>
              </div>
            </div>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ChatBubbleLeftRightIcon className="h-8 w-8 text-orange-500" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">AI Interactions</p>
              <p className="text-2xl font-semibold text-gray-900">
                {dashboardData?.stats.aiInteractions || 0}
              </p>
              <div className="flex items-center text-sm text-gray-500">
                <span>Start chatting with AI</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Compliance Trend */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Compliance Trends</h3>
          <div className="h-64">
            {dashboardData?.complianceTrends && dashboardData.complianceTrends.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={dashboardData.complianceTrends}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="GRI" stroke="#10b981" strokeWidth={2} />
                  <Line type="monotone" dataKey="SASB" stroke="#3b82f6" strokeWidth={2} />
                  <Line type="monotone" dataKey="TCFD" stroke="#8b5cf6" strokeWidth={2} />
                  <Line type="monotone" dataKey="CSRD" stroke="#f59e0b" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                <p>No compliance data available</p>
              </div>
            )}
          </div>
        </div>

        {/* Document Distribution */}
        <div className="card">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Document Distribution</h3>
          <div className="h-64">
            {dashboardData?.documentDistribution && dashboardData.documentDistribution.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={dashboardData.documentDistribution}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {dashboardData.documentDistribution.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                <p>No documents uploaded yet</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="card">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
        <div className="space-y-4">
          {dashboardData?.recentActivities && dashboardData.recentActivities.length > 0 ? (
            dashboardData.recentActivities.map((activity) => (
              <div key={activity.id} className="flex items-start space-x-3">
                <div className="flex-shrink-0 mt-1">
                  {getStatusIcon(activity.status)}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900">{activity.title}</p>
                  <p className="text-sm text-gray-500">{activity.description}</p>
                  <p className="text-xs text-gray-400 mt-1">{activity.time}</p>
                </div>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-gray-500">
              <p>No recent activity</p>
              <p className="text-sm mt-2">Start using the platform to see your activity here</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;

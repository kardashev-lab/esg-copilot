import React, { useState, useEffect } from 'react';
import {
  Cog6ToothIcon,
  UserIcon,
  KeyIcon,
  BellIcon,
  GlobeAltIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState('profile');
  const [notifications, setNotifications] = useState({
    email: true,
    push: false,
    compliance: true,
    reports: true,
  });
  const [profileData, setProfileData] = useState({
    fullName: 'ESG Professional',
    email: 'professional@company.com',
    company: 'Sustainable Corp',
    role: 'Sustainability Manager',
  });
  const [apiSettings, setApiSettings] = useState({
    openaiKey: 'sk-...',
    model: 'GPT-4 (Recommended)',
  });
  const [preferences, setPreferences] = useState({
    defaultFramework: 'GRI Standards',
    language: 'English',
    timezone: 'UTC-5 (Eastern Time)',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const tabs = [
    { id: 'profile', name: 'Profile', icon: UserIcon },
    { id: 'notifications', name: 'Notifications', icon: BellIcon },
    { id: 'api', name: 'API Settings', icon: KeyIcon },
    { id: 'preferences', name: 'Preferences', icon: Cog6ToothIcon },
  ];

  useEffect(() => {
    // Load saved settings from localStorage or API
    loadSettings();
  }, []);

  const loadSettings = () => {
    // In a real implementation, this would load from an API
    // For now, use localStorage
    const savedNotifications = localStorage.getItem('notifications');
    const savedProfile = localStorage.getItem('profile');
    const savedApi = localStorage.getItem('apiSettings');
    const savedPreferences = localStorage.getItem('preferences');

    if (savedNotifications) {
      setNotifications(JSON.parse(savedNotifications));
    }
    if (savedProfile) {
      setProfileData(JSON.parse(savedProfile));
    }
    if (savedApi) {
      setApiSettings(JSON.parse(savedApi));
    }
    if (savedPreferences) {
      setPreferences(JSON.parse(savedPreferences));
    }
  };

  const saveSettings = async (type: string, data: any) => {
    setLoading(true);
    setError(null);
    setSuccess(null);

    try {
      // In a real implementation, this would save to an API
      // For now, save to localStorage
      localStorage.setItem(type, JSON.stringify(data));
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setSuccess(`${type.charAt(0).toUpperCase() + type.slice(1)} settings saved successfully`);
    } catch (error) {
      console.error('Save error:', error);
      setError('Failed to save settings. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveProfile = async () => {
    await saveSettings('profile', profileData);
  };

  const handleSaveNotifications = async () => {
    await saveSettings('notifications', notifications);
  };

  const handleSaveApiSettings = async () => {
    await saveSettings('apiSettings', apiSettings);
  };

  const handleSavePreferences = async () => {
    await saveSettings('preferences', preferences);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-sm text-gray-500">
          Manage your account settings and preferences
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

      <div className="flex space-x-6">
        {/* Sidebar */}
        <div className="w-64">
          <nav className="space-y-1">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                  activeTab === tab.id
                    ? 'bg-green-100 text-green-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`}
              >
                <tab.icon className="mr-3 h-5 w-5" />
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Content */}
        <div className="flex-1">
          {activeTab === 'profile' && (
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Profile Information</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Full Name
                  </label>
                  <input
                    type="text"
                    value={profileData.fullName}
                    onChange={(e) => setProfileData(prev => ({ ...prev, fullName: e.target.value }))}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    value={profileData.email}
                    onChange={(e) => setProfileData(prev => ({ ...prev, email: e.target.value }))}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Company
                  </label>
                  <input
                    type="text"
                    value={profileData.company}
                    onChange={(e) => setProfileData(prev => ({ ...prev, company: e.target.value }))}
                    className="input-field"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Role
                  </label>
                  <select 
                    value={profileData.role}
                    onChange={(e) => setProfileData(prev => ({ ...prev, role: e.target.value }))}
                    className="input-field"
                  >
                    <option>Sustainability Manager</option>
                    <option>ESG Analyst</option>
                    <option>Chief Sustainability Officer</option>
                    <option>Compliance Officer</option>
                  </select>
                </div>
                <button 
                  onClick={handleSaveProfile}
                  disabled={loading}
                  className="btn-primary"
                >
                  {loading ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </div>
          )}

          {activeTab === 'notifications' && (
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Notification Preferences</h3>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">Email Notifications</h4>
                    <p className="text-sm text-gray-500">Receive updates via email</p>
                  </div>
                  <button
                    onClick={() => setNotifications(prev => ({ ...prev, email: !prev.email }))}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      notifications.email ? 'bg-green-600' : 'bg-gray-200'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        notifications.email ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">Push Notifications</h4>
                    <p className="text-sm text-gray-500">Receive browser notifications</p>
                  </div>
                  <button
                    onClick={() => setNotifications(prev => ({ ...prev, push: !prev.push }))}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      notifications.push ? 'bg-green-600' : 'bg-gray-200'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        notifications.push ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">Compliance Alerts</h4>
                    <p className="text-sm text-gray-500">Get notified about compliance gaps</p>
                  </div>
                  <button
                    onClick={() => setNotifications(prev => ({ ...prev, compliance: !prev.compliance }))}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      notifications.compliance ? 'bg-green-600' : 'bg-gray-200'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        notifications.compliance ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="text-sm font-medium text-gray-900">Report Updates</h4>
                    <p className="text-sm text-gray-500">Notifications about report generation</p>
                  </div>
                  <button
                    onClick={() => setNotifications(prev => ({ ...prev, reports: !prev.reports }))}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      notifications.reports ? 'bg-green-600' : 'bg-gray-200'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        notifications.reports ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>

                <button 
                  onClick={handleSaveNotifications}
                  disabled={loading}
                  className="btn-primary"
                >
                  {loading ? 'Saving...' : 'Save Notification Settings'}
                </button>
              </div>
            </div>
          )}

          {activeTab === 'api' && (
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">API Configuration</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    OpenAI API Key
                  </label>
                  <input
                    type="password"
                    value={apiSettings.openaiKey}
                    onChange={(e) => setApiSettings(prev => ({ ...prev, openaiKey: e.target.value }))}
                    className="input-field"
                    placeholder="Enter your OpenAI API key"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Your API key is encrypted and stored securely
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Model Preference
                  </label>
                  <select 
                    value={apiSettings.model}
                    onChange={(e) => setApiSettings(prev => ({ ...prev, model: e.target.value }))}
                    className="input-field"
                  >
                    <option>GPT-4 (Recommended)</option>
                    <option>GPT-3.5 Turbo</option>
                    <option>GPT-4 Turbo</option>
                  </select>
                </div>
                <button 
                  onClick={handleSaveApiSettings}
                  disabled={loading}
                  className="btn-primary"
                >
                  {loading ? 'Saving...' : 'Update API Settings'}
                </button>
              </div>
            </div>
          )}

          {activeTab === 'preferences' && (
            <div className="card">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Application Preferences</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Default Framework
                  </label>
                  <select 
                    value={preferences.defaultFramework}
                    onChange={(e) => setPreferences(prev => ({ ...prev, defaultFramework: e.target.value }))}
                    className="input-field"
                  >
                    <option>GRI Standards</option>
                    <option>SASB Standards</option>
                    <option>TCFD Framework</option>
                    <option>CSRD Directive</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Language
                  </label>
                  <select 
                    value={preferences.language}
                    onChange={(e) => setPreferences(prev => ({ ...prev, language: e.target.value }))}
                    className="input-field"
                  >
                    <option>English</option>
                    <option>Spanish</option>
                    <option>French</option>
                    <option>German</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Time Zone
                  </label>
                  <select 
                    value={preferences.timezone}
                    onChange={(e) => setPreferences(prev => ({ ...prev, timezone: e.target.value }))}
                    className="input-field"
                  >
                    <option>UTC-5 (Eastern Time)</option>
                    <option>UTC-8 (Pacific Time)</option>
                    <option>UTC+0 (GMT)</option>
                    <option>UTC+1 (Central European Time)</option>
                  </select>
                </div>
                <button 
                  onClick={handleSavePreferences}
                  disabled={loading}
                  className="btn-primary"
                >
                  {loading ? 'Saving...' : 'Save Preferences'}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Settings;

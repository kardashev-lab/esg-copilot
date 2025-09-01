import React, { useState, useRef, useEffect } from 'react';
import {
  DocumentTextIcon,
  ExclamationTriangleIcon,
  ChevronDownIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';
import { API_ENDPOINTS } from '../../config/api';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  confidence?: number;
  suggestedActions?: string[];
  sources?: string[];
}

interface Framework {
  id: string;
  name: string;
  description: string;
  version: string;
  category: string;
  country?: string;
}

interface Country {
  id: string;
  name: string;
  frameworks: Framework[];
}

// Response parser function
const parseResponse = (content: string) => {
  if (!content || content.trim() === '') {
    return [];
  }

  // Remove any trailing "O" or "0" that might be added
  let cleanContent = content.replace(/[O0]\s*$/, '').trim();
  
  // Handle bold text (wrapped in **)
  let processedContent = cleanContent.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Split into paragraphs first
  const paragraphs = processedContent.split(/\n\s*\n/).filter((p: string) => p.trim());
  
  const parsedSections: any[] = [];
  
  // First pass: identify and group consecutive numbered list items
  const processedParagraphs: any[] = [];
  let i = 0;
  
  while (i < paragraphs.length) {
    const paragraph = paragraphs[i];
    const lines = paragraph.trim().split('\n').filter((line: string) => line.trim());
    if (lines.length === 0) {
      i++;
      continue;
    }
    
    const firstLine = lines[0];
    
    // Check if it's a numbered list item
    if (firstLine.match(/^\d+\./)) {
      // Collect all consecutive numbered list items
      const numberedItems: string[] = [];
      let j = i;
      
      while (j < paragraphs.length) {
        const nextParagraph = paragraphs[j];
        const nextLines = nextParagraph.trim().split('\n').filter((line: string) => line.trim());
        if (nextLines.length === 0) {
          j++;
          continue;
        }
        
        const nextFirstLine = nextLines[0];
        if (nextFirstLine.match(/^\d+\./)) {
          // Extract just the list item text, removing the number
          const itemText = nextParagraph.trim().replace(/^\d+\.\s*/, '');
          numberedItems.push(itemText);
          j++;
        } else {
          break;
        }
      }
      
      if (numberedItems.length > 0) {
        processedParagraphs.push({
          type: 'numbered-list',
          items: numberedItems
        });
        i = j;
        continue;
      }
    }
    
    // Check if it's a bullet list item
    if (firstLine.match(/^[-*•]/)) {
      // Collect all consecutive bullet list items
      const bulletItems: string[] = [];
      let j = i;
      
      while (j < paragraphs.length) {
        const nextParagraph = paragraphs[j];
        const nextLines = nextParagraph.trim().split('\n').filter((line: string) => line.trim());
        if (nextLines.length === 0) {
          j++;
          continue;
        }
        
        const nextFirstLine = nextLines[0];
        if (nextFirstLine.match(/^[-*•]/)) {
          // Extract just the list item text, removing the bullet
          const itemText = nextParagraph.trim().replace(/^[-*•]\s*/, '');
          bulletItems.push(itemText);
          j++;
        } else {
          break;
        }
      }
      
      if (bulletItems.length > 0) {
        processedParagraphs.push({
          type: 'bullet-list',
          items: bulletItems
        });
        i = j;
        continue;
      }
    }
    
    // Regular paragraph
    processedParagraphs.push({
      type: 'paragraph',
      content: paragraph.trim()
    });
    i++;
  }
  
  // Second pass: process the grouped paragraphs
  processedParagraphs.forEach((item) => {
    if (item.type === 'numbered-list' || item.type === 'bullet-list') {
      parsedSections.push(item);
    } else {
      // Handle regular paragraphs
      const lines = item.content.split('\n').filter((line: string) => line.trim());
      if (lines.length === 0) return;
      
      const firstLine = lines[0];
      
      // Check if it's a header (starts with capital letter and ends with colon)
      if (firstLine.match(/^[A-Z][^a-z].*:$/)) {
        const header = firstLine.replace(':', '').trim();
        const body = lines.slice(1).join('\n').trim();
        
        parsedSections.push({
          type: 'header',
          content: header,
          body: body
        });
        return;
      }
      
      // Check if it's a main section header (all caps or title case)
      if (firstLine.match(/^[A-Z\s]+$/) || firstLine.match(/^[A-Z][a-z\s]+:$/)) {
        const header = firstLine.replace(':', '').trim();
        const body = lines.slice(1).join('\n').trim();
        
        parsedSections.push({
          type: 'header',
          content: header,
          body: body
        });
        return;
      }
      
      // Regular paragraph
      parsedSections.push({
        type: 'paragraph',
        content: item.content.trim()
      });
    }
  });
  
  return parsedSections;
};

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedFrameworks, setSelectedFrameworks] = useState<Set<string>>(new Set());
  const [autoSelectedFrameworks, setAutoSelectedFrameworks] = useState<Set<string>>(new Set());
  const [isSuggestingFrameworks, setIsSuggestingFrameworks] = useState(false);
  const [isFirstResponse, setIsFirstResponse] = useState(true);
  const [pendingFirstMessage, setPendingFirstMessage] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Check if there are messages to export
  const hasMessagesToExport = messages.length > 0;

  // Define countries and their frameworks
  const countries: Country[] = [
    {
      id: 'eu',
      name: 'European Union',
      frameworks: [
        { id: 'csrd', name: 'CSRD Directive', description: 'Corporate Sustainability Reporting Directive', version: '2022', category: 'Regulation' },
        { id: 'esrs', name: 'ESRS Standards', description: 'European Sustainability Reporting Standards', version: '2022', category: 'Standard' },
        { id: 'sfdr', name: 'SFDR', description: 'Sustainable Finance Disclosure Regulation', version: '2019', category: 'Regulation' },
      ]
    },
    {
      id: 'us',
      name: 'United States',
      frameworks: [
        { id: 'sasb', name: 'SASB Standards', description: 'Sustainability Accounting Standards Board', version: '2018', category: 'Standard' },
        { id: 'sec-climate', name: 'SEC Climate Rule', description: 'SEC Climate-Related Disclosures', version: '2024', category: 'Regulation' },
        { id: 'california-sb253', name: 'California SB 253', description: 'Climate Corporate Data Accountability Act', version: '2023', category: 'Regulation' },
      ]
    },
    {
      id: 'uk',
      name: 'United Kingdom',
      frameworks: [
        { id: 'uk-tcfd', name: 'UK TCFD', description: 'UK Task Force on Climate-related Financial Disclosures', version: '2021', category: 'Regulation' },
        { id: 'uk-sdr', name: 'UK SDR', description: 'UK Sustainability Disclosure Requirements', version: '2023', category: 'Regulation' },
      ]
    },
    {
      id: 'canada',
      name: 'Canada',
      frameworks: [
        { id: 'canada-tcfd', name: 'Canada TCFD', description: 'Canadian Climate-related Financial Disclosures', version: '2022', category: 'Regulation' },
        { id: 'canada-esg', name: 'Canada ESG', description: 'Canadian ESG Reporting Standards', version: '2023', category: 'Standard' },
      ]
    },
    {
      id: 'australia',
      name: 'Australia',
      frameworks: [
        { id: 'australia-climate', name: 'Australia Climate', description: 'Australian Climate-related Financial Disclosures', version: '2023', category: 'Regulation' },
        { id: 'australia-esg', name: 'Australia ESG', description: 'Australian ESG Reporting Framework', version: '2022', category: 'Standard' },
      ]
    },
    {
      id: 'japan',
      name: 'Japan',
      frameworks: [
        { id: 'japan-tcfd', name: 'Japan TCFD', description: 'Japanese Climate-related Financial Disclosures', version: '2022', category: 'Regulation' },
        { id: 'japan-esg', name: 'Japan ESG', description: 'Japanese ESG Disclosure Guidelines', version: '2021', category: 'Standard' },
      ]
    },
    {
      id: 'global',
      name: 'Global',
      frameworks: [
        { id: 'gri', name: 'GRI Standards', description: 'Global Reporting Initiative', version: '2021', category: 'Standard' },
        { id: 'tcfd', name: 'TCFD Framework', description: 'Task Force on Climate-related Financial Disclosures', version: '2017', category: 'Framework' },
        { id: 'ifrs-s1', name: 'IFRS S1', description: 'IFRS Sustainability Disclosure Standards', version: '2023', category: 'Standard' },
        { id: 'ifrs-s2', name: 'IFRS S2', description: 'IFRS Climate-related Disclosures', version: '2023', category: 'Standard' },
        { id: 'cdp', name: 'CDP', description: 'Carbon Disclosure Project', version: '2023', category: 'Framework' },
      ]
    }
  ];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // LLM-based framework selection
  const suggestFrameworks = async (query: string) => {
    setIsSuggestingFrameworks(true);
    try {
      const response = await fetch(`${API_ENDPOINTS.CHAT.MESSAGE.replace('/message', '/suggest-frameworks')}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });

      if (response.ok) {
        const data = await response.json();
        const suggestedFrameworks = new Set<string>(data.suggested_frameworks || []);
        setAutoSelectedFrameworks(suggestedFrameworks);
        setSelectedFrameworks(suggestedFrameworks);
      } else {
        // Fallback to keyword-based selection
        fallbackFrameworkSelection(query);
      }
    } catch (error) {
      console.error('Error suggesting frameworks:', error);
      // Fallback to keyword-based selection
      fallbackFrameworkSelection(query);
    } finally {
      setIsSuggestingFrameworks(false);
    }
  };

  // Fallback keyword-based framework selection
  const fallbackFrameworkSelection = (query: string) => {
    const queryLower = query.toLowerCase();
    const autoSelected = new Set<string>();
    
    countries.forEach(country => {
      country.frameworks.forEach(framework => {
        // Check if query mentions the country
        if (queryLower.includes(country.name.toLowerCase()) || 
            queryLower.includes(country.id.toLowerCase())) {
          autoSelected.add(framework.id);
        }
        
        // Check if query mentions the framework
        if (queryLower.includes(framework.name.toLowerCase()) ||
            queryLower.includes(framework.id.toLowerCase())) {
          autoSelected.add(framework.id);
        }
        
        // Check for common ESG terms
        const esgTerms = ['esg', 'sustainability', 'climate', 'emissions', 'carbon', 'social', 'governance'];
        if (esgTerms.some(term => queryLower.includes(term))) {
          // Auto-select global frameworks for general ESG queries
          if (country.id === 'global') {
            autoSelected.add(framework.id);
          }
        }
      });
    });
    
    setAutoSelectedFrameworks(autoSelected);
    setSelectedFrameworks(autoSelected);
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return;

    if (isFirstResponse) {
      // First response flow: Auto-select frameworks and show filters
      setPendingFirstMessage(inputMessage);
      await suggestFrameworks(inputMessage);
      setShowFilters(true);
      setInputMessage('');
      return;
    }

    // Normal chat flow for subsequent messages
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: inputMessage,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(API_ENDPOINTS.CHAT.MESSAGE, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputMessage,
          framework_focus: Array.from(selectedFrameworks).join(','),
          context_documents: [],
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
        confidence: data.confidence_score,
        suggestedActions: data.suggested_actions,
        sources: Array.from(selectedFrameworks).map(fw => {
          const framework = countries.flatMap(c => c.frameworks).find(f => f.id === fw);
          return framework?.name || fw;
        }),
      };

      setMessages(prev => [...prev, aiResponse]);
    } catch (error) {
      console.error('Error sending message:', error);
      setError('Failed to send message. Please try again.');
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'I apologize, but I encountered an error while processing your request. Please try again or contact support if the issue persists.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleFirstResponse = async () => {
    if (!pendingFirstMessage.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: pendingFirstMessage,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);
    setIsFirstResponse(false);

    try {
      const response = await fetch(API_ENDPOINTS.CHAT.MESSAGE, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: pendingFirstMessage,
          framework_focus: Array.from(selectedFrameworks).join(','),
          context_documents: [],
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.response,
        timestamp: new Date(),
        confidence: data.confidence_score,
        suggestedActions: data.suggested_actions,
        sources: Array.from(selectedFrameworks).map(fw => {
          const framework = countries.flatMap(c => c.frameworks).find(f => f.id === fw);
          return framework?.name || fw;
        }),
      };

      setMessages(prev => [...prev, aiResponse]);
    } catch (error) {
      console.error('Error sending message:', error);
      setError('Failed to send message. Please try again.');
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'I apologize, but I encountered an error while processing your request. Please try again or contact support if the issue persists.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      setPendingFirstMessage('');
    }
  };

  const toggleFramework = (frameworkId: string) => {
    const newSelected = new Set(selectedFrameworks);
    if (newSelected.has(frameworkId)) {
      newSelected.delete(frameworkId);
    } else {
      newSelected.add(frameworkId);
    }
    setSelectedFrameworks(newSelected);
  };

  const selectAllForCountry = (countryId: string) => {
    const country = countries.find(c => c.id === countryId);
    if (!country) return;
    
    const newSelected = new Set(selectedFrameworks);
    country.frameworks.forEach(framework => {
      newSelected.add(framework.id);
    });
    setSelectedFrameworks(newSelected);
  };

  const deselectAllForCountry = (countryId: string) => {
    const country = countries.find(c => c.id === countryId);
    if (!country) return;
    
    const newSelected = new Set(selectedFrameworks);
    country.frameworks.forEach(framework => {
      newSelected.delete(framework.id);
    });
    setSelectedFrameworks(newSelected);
  };

  const clearAllFilters = () => {
    setSelectedFrameworks(new Set());
    setAutoSelectedFrameworks(new Set());
  };

  const getSelectedCount = (countryId: string) => {
    const country = countries.find(c => c.id === countryId);
    if (!country) return 0;
    return country.frameworks.filter(fw => selectedFrameworks.has(fw.id)).length;
  };

  const isAllSelectedForCountry = (countryId: string) => {
    const country = countries.find(c => c.id === countryId);
    if (!country) return false;
    return country.frameworks.every(fw => selectedFrameworks.has(fw.id));
  };

  const getAllFrameworks = () => countries.flatMap(c => c.frameworks);

  // Reset functionality - clear everything
  const handleReset = () => {
    if (messages.length > 0) {
      const confirmed = window.confirm('Are you sure you want to reset the chat? This will clear all messages and selections.');
      if (!confirmed) return;
    }
    
    setMessages([]);
    setInputMessage('');
    setSelectedFrameworks(new Set());
    setAutoSelectedFrameworks(new Set());
    setShowFilters(false);
    setError(null);
    setIsFirstResponse(true);
    setPendingFirstMessage('');
  };

  // Export functionality - export chat as readable text
  const handleExport = () => {
    let exportText = `ESG AI Assistant Chat Export\n`;
    exportText += `Generated on: ${new Date().toLocaleString()}\n`;
    exportText += `Selected Frameworks: ${Array.from(selectedFrameworks).join(', ') || 'None'}\n`;
    exportText += `\n${'='.repeat(50)}\n\n`;

    messages.forEach((message, index) => {
      if (message.role === 'user') {
        exportText += `👤 You: ${message.content}\n\n`;
      } else {
        exportText += `🤖 Reggie: ${message.content}\n\n`;
        
        if (message.suggestedActions && message.suggestedActions.length > 0) {
          exportText += `Suggested Actions:\n`;
          message.suggestedActions.forEach((action, actionIndex) => {
            exportText += `  ${actionIndex + 1}. ${action}\n`;
          });
          exportText += `\n`;
        }
      }
      exportText += `${'─'.repeat(30)}\n\n`;
    });

    // Create and download text file
    const dataBlob = new Blob([exportText], { type: 'text/plain' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `esg-chat-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    
    // Show success message
    alert('Chat exported successfully! The text file has been downloaded to your Downloads folder.');
  };

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Header */}
      <div className="border-b border-gray-200 p-4">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Research / ESG AI Assistant</h1>
            <p className="text-sm text-gray-500 mt-1">Understand ESG regulations and sustainability frameworks.</p>
          </div>
          <div className="flex space-x-2">
            <button 
              onClick={handleReset}
              className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-colors"
              title="Reset chat and clear all selections"
            >
              Reset
            </button>
            <button 
              onClick={handleExport}
              disabled={!hasMessagesToExport}
              className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              title={hasMessagesToExport ? "Export chat as text file" : "No messages to export"}
            >
              Export
            </button>
          </div>
        </div>
      </div>

      {/* Query Input */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-end space-x-2">
          <div className="flex-1">
            <textarea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask about ESG regulations, sustainability frameworks, or compliance requirements..."
              className="w-full p-3 border border-gray-300 rounded-lg resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={2}
              disabled={isLoading}
            />
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="px-4 py-3 bg-black text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Ask Reggie
          </button>
        </div>
        <div className="mt-2 text-xs text-gray-500">
          {inputMessage.length}/4000 characters
        </div>
      </div>

      {/* Filters */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center space-x-2 px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            <span>Filters</span>
            <ChevronDownIcon className={`h-4 w-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          </button>
          
          <div className="flex items-center space-x-2">
            {isSuggestingFrameworks && (
              <div className="flex items-center space-x-1 text-sm text-blue-600">
                <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-600"></div>
                <span>Analyzing query...</span>
              </div>
            )}
            {selectedFrameworks.size > 0 && (
              <>
                <span className="text-sm text-gray-600">
                  {selectedFrameworks.size} selected
                </span>
            <button
                  onClick={clearAllFilters}
                  className="text-sm text-red-600 hover:text-red-800"
                >
                  Clear all
            </button>
              </>
            )}
          </div>
        </div>

        {showFilters && (
          <div className="mt-4">
            {isFirstResponse && pendingFirstMessage && (
              <div className="mb-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-blue-900 mb-1">Ready to get response for:</p>
                    <p className="text-sm text-blue-800 italic">"{pendingFirstMessage}"</p>
                  </div>
                  <button
                    onClick={handleFirstResponse}
                    disabled={selectedFrameworks.size === 0 || isLoading}
                    className="ml-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    {isLoading ? 'Getting Response...' : 'Get Response'}
                  </button>
                </div>
              </div>
            )}
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {countries.map((country) => (
                <div key={country.id} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <h3 className="font-medium text-gray-900">{country.name}</h3>
                      {getSelectedCount(country.id) > 0 && (
                        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
                          {getSelectedCount(country.id)} Selected
                        </span>
                      )}
                    </div>
                    <div className="flex space-x-1">
                      <button
                        onClick={() => isAllSelectedForCountry(country.id) 
                          ? deselectAllForCountry(country.id) 
                          : selectAllForCountry(country.id)
                        }
                        className="text-xs px-2 py-1 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded"
                      >
                        {isAllSelectedForCountry(country.id) ? 'Deselect All' : 'Select All'}
                      </button>
                    </div>
                  </div>
                  <div className="space-y-1">
                    {country.frameworks.map((framework) => (
                      <label key={framework.id} className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={selectedFrameworks.has(framework.id)}
                          onChange={() => toggleFramework(framework.id)}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <div className="flex-1">
                          <div className="text-sm font-medium text-gray-900">{framework.name}</div>
                          <div className="text-xs text-gray-500">{framework.description}</div>
                        </div>
                        {autoSelectedFrameworks.has(framework.id) && (
                          <span className="text-xs text-green-600">Auto-selected</span>
                        )}
                      </label>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-md">
              <div className="text-6xl mb-4">🤖</div>
              <h2 className="text-2xl font-semibold text-gray-900 mb-2">Welcome to ESG AI Assistant</h2>
              <p className="text-gray-600 mb-6">
                I'm Reggie, your AI ESG Regulations Co-Pilot. I can help you with sustainability reporting, compliance analysis, and ESG best practices.
              </p>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800 mb-2">💡 <strong>Getting Started:</strong></p>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• Select relevant frameworks using the Filters button</li>
                  <li>• Type your question in the input field below</li>
                  <li>• Click "Ask Reggie" to get started</li>
                </ul>
              </div>
            </div>
          </div>
        )}
        
        {messages.map((message) => (
          <div
            key={message.id}
            className={`mb-6 ${message.role === 'user' ? 'text-right' : 'text-left'}`}
          >
            {message.role === 'user' ? (
              <div className="inline-block max-w-2xl bg-blue-600 text-white rounded-lg px-4 py-2">
              <div className="whitespace-pre-wrap">{message.content}</div>
              </div>
            ) : (
              <div className="max-w-4xl">
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-medium text-gray-900">Response</h3>
                    {message.sources && message.sources.length > 0 && (
                      <div className="text-xs text-gray-500">
                        Based on research from: {message.sources.join(', ')} and {selectedFrameworks.size} more filters.
                      </div>
                    )}
                  </div>
                  <div className="prose prose-sm max-w-none">
                    {(() => {
                      const parsedContent = parseResponse(message.content);
                      return (
                        <div className="space-y-4">
                          {parsedContent.map((section, index) => {
                            if (!section) return null;
                            
                            if (section.type === 'header') {
                              return (
                                <div key={index} className="space-y-2">
                                  <h4 className="text-lg font-semibold text-gray-900 border-b border-gray-200 pb-1">
                                    {section.content}
                                  </h4>
                                  {section.body && (
                                    <div className="text-gray-700 leading-relaxed">
                                      {section.body}
                                    </div>
                                  )}
                                </div>
                              );
                            }
                            
                            if (section.type === 'numbered-list' && section.items) {
                              return (
                                <div key={index} className="space-y-1">
                                  <ol className="list-decimal list-inside space-y-1 text-gray-700">
                                    {section.items.map((item: string, itemIndex: number) => (
                                      <li key={itemIndex} className="leading-relaxed">
                                        {item}
                                      </li>
                                    ))}
                                  </ol>
                                </div>
                              );
                            }
                            
                            if (section.type === 'bullet-list' && section.items) {
                              return (
                                <div key={index} className="space-y-1">
                                  <ul className="list-disc list-inside space-y-1 text-gray-700">
                                    {section.items.map((item: string, itemIndex: number) => (
                                      <li key={itemIndex} className="leading-relaxed">
                                        {item}
                                      </li>
                                    ))}
                                  </ul>
                                </div>
                              );
                            }
                            
                            if (section.type === 'paragraph') {
                              return (
                                <div key={index} className="text-gray-700 leading-relaxed" 
                                     dangerouslySetInnerHTML={{ __html: section.content }} />
                              );
                            }
                            
                            return null;
                          })}
                        </div>
                      );
                    })()}
                  </div>
                  
                  {message.confidence && (
                    <div className="mt-3 text-xs text-gray-500">
                  Confidence: {Math.round(message.confidence * 100)}%
                </div>
              )}
              
                  {message.suggestedActions && message.suggestedActions.length > 0 && (
                    <div className="mt-4 pt-3 border-t border-gray-200">
                  <p className="text-xs font-medium text-gray-700 mb-2">Suggested Actions:</p>
                  <div className="space-y-1">
                    {message.suggestedActions.map((action, index) => (
                          <button
                            key={index}
                            onClick={() => {
                              setInputMessage(action);
                              // Focus the textarea after setting the message
                              setTimeout(() => {
                                const textarea = document.querySelector('textarea');
                                if (textarea) {
                                  (textarea as HTMLTextAreaElement).focus();
                                }
                              }, 100);
                            }}
                            className="text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 px-2 py-1 rounded transition-colors flex items-center w-full text-left"
                          >
                            <DocumentTextIcon className="h-3 w-3 mr-1 flex-shrink-0" />
                            <span className="truncate">{action}</span>
                          </button>
                        ))}
                  </div>
                </div>
              )}
            </div>
              </div>
            )}
          </div>
        ))}
        
        {isLoading && (
          <div className="mb-6">
            <div className="max-w-4xl">
              <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                  <span className="text-gray-600">Researching...</span>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />

      {/* Error Message */}
      {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-500 mr-2" />
            <span className="text-red-700 text-sm">{error}</span>
          </div>
        </div>
      )}
      </div>
    </div>
  );
};

export default Chat;

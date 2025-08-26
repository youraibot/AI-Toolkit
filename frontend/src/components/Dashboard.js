import React, { useState, useEffect, useCallback } from 'react';
import api from '../api';

function Dashboard() {
    // State for model management
    const [models, setModels] = useState([]);
    const [modelSearchTerm, setModelSearchTerm] = useState('');
    const [newModelName, setNewModelName] = useState('');
    const [newModelFilename, setNewModelFilename] = useState('');
    const [isDownloading, setIsDownloading] = useState(false);
    const [isSearching, setIsSearching] = useState(false);
    const [searchResults, setSearchResults] = useState([]);
    const [managementError, setManagementError] = useState('');

    // State for chat
    const [selectedModel, setSelectedModel] = useState(null);
    const [prompt, setPrompt] = useState('');
    const [chatHistory, setChatHistory] = useState([]);
    const [isGenerating, setIsGenerating] = useState(false);
    const [chatError, setChatError] = useState('');
    const [conversations, setConversations] = useState([]);
    const [activeConversationId, setActiveConversationId] = useState(null);

    const fetchModels = useCallback(async () => {
        try {
            const response = await api.get('/models');
            setModels(response.data);
            if (response.data.length > 0 && !selectedModel) {
                setSelectedModel(response.data[0]);
            }
        } catch (error) {
            setManagementError(error.response?.data?.error || 'Failed to fetch models.');
        }
    }, [selectedModel]);

    const fetchConversations = useCallback(async () => {
        try {
            const response = await api.get('/conversations');
            setConversations(response.data);
        } catch (error) {
            setManagementError(error.response?.data?.error || 'Failed to fetch conversations.');
        }
    }, []);

    useEffect(() => {
        fetchModels();
        fetchConversations();
    }, [fetchModels, fetchConversations]);

    const handleSearchModels = async (e) => {
        e.preventDefault();
        if (!modelSearchTerm) {
            setManagementError('Please enter a search term.');
            return;
        }
        setIsSearching(true);
        setManagementError('');
        try {
            const response = await api.get(`/models/search?q=${modelSearchTerm}`);
            setSearchResults(response.data);
        } catch (error) {
            setManagementError(error.response?.data?.error || 'Failed to search for models.');
        } finally {
            setIsSearching(false);
        }
    };

    const handleDownloadModel = async (modelId) => {
        setIsDownloading(true);
        setManagementError('');
        try {
            await api.post('/models/download', { model_id: modelId });
            await fetchModels();
        } catch (error) {
            setManagementError(error.response?.data?.error || 'Failed to download model.');
        } finally {
            setIsDownloading(false);
        }
    };

    const handleChatSubmit = async (e) => {
        e.preventDefault();
        if (!prompt || !selectedModel) {
            setChatError('Please select a model and enter a prompt.');
            return;
        }
        setIsGenerating(true);
        setChatError('');
        const newHistory = [...chatHistory, { role: 'user', content: prompt }];
        setChatHistory(newHistory);
        setPrompt('');

        try {
            const payload = {
                model_id: selectedModel.id,
                prompt: prompt,
                conversation_id: activeConversationId
            };
            const response = await api.post('/chat', payload);
            setChatHistory([...newHistory, { role: 'bot', content: response.data.response }]);
            if (!activeConversationId) {
                setActiveConversationId(response.data.conversation_id);
                await fetchConversations();
            }
        } catch (error) {
            setChatError(error.response?.data?.error || 'Failed to get response.');
        } finally {
            setIsGenerating(false);
        }
    };

    const handleNewChat = () => {
        setActiveConversationId(null);
        setChatHistory([]);
        setPrompt('');
    };

    const handleSelectConversation = async (convId) => {
        setActiveConversationId(convId);
        try {
            const response = await api.get(`/conversations/${convId}`);
            setChatHistory(response.data.messages);
        } catch (error) {
            setChatError('Failed to load conversation history.');
        }
    };

    const handleDeleteConversation = async (e, convId) => {
        e.stopPropagation(); // Prevent handleSelectConversation from firing
        if (window.confirm('Are you sure you want to delete this conversation?')) {
            try {
                await api.delete(`/conversations/${convId}`);
                await fetchConversations();
                if (activeConversationId === convId) {
                    handleNewChat();
                }
            } catch (error) {
                setChatError('Failed to delete conversation.');
            }
        }
    };

    const filteredModels = models.filter(model =>
        model.name.toLowerCase().includes(modelSearchTerm.toLowerCase())
    );

    return (
        <div className="dashboard-grid">
            <div className="model-management">
                <h2>Model Management</h2>
                {managementError && <p className="error-message">{managementError}</p>}
                <form onSubmit={handleSearchModels} className="download-form">
                    <input type="text" value={modelSearchTerm} onChange={(e) => setModelSearchTerm(e.target.value)} placeholder="Search for models on Hugging Face..." required />
                    <button type="submit" disabled={isSearching}>{isSearching ? 'Searching...' : 'Search'}</button>
                </form>
                <div className="search-results">
                    <h3>Search Results</h3>
                    <ul className="model-list">
                        {searchResults.map(model => (
                            <li key={model.id} className="model-list-item">
                                <span>{model.name} by {model.author}</span>
                                <button onClick={() => handleDownloadModel(model.id)} disabled={isDownloading}>
                                    {isDownloading ? 'Downloading...' : 'Download'}
                                </button>
                            </li>
                        ))}
                    </ul>
                </div>
                <h3 style={{marginTop: '1.5rem'}}>Available Models</h3>
                <input type="text" placeholder="Search local models..." className="search-bar" value={localModelSearchTerm} onChange={(e) => setLocalModelSearchTerm(e.target.value)} />
                <ul className="model-list">
                    {filteredModels.map(model => (
                        <li key={model.id} className={`model-list-item ${selectedModel?.id === model.id ? 'selected' : ''}`} onClick={() => setSelectedModel(model)}>
                            {model.name}
                        </li>
                    ))}
                </ul>
            </div>
            <div className="chat-interface">
                <div className="conversation-sidebar">
                    <div className="new-chat-button">
                        <button onClick={handleNewChat}>+ New Chat</button>
                    </div>
                    <ul className="conversation-list">
                        {conversations.map(conv => (
                            <li key={conv.id} className={`conversation-list-item ${activeConversationId === conv.id ? 'selected' : ''}`} onClick={() => handleSelectConversation(conv.id)}>
                                <span>{conv.title}</span>
                                <button className="delete-conv-button" onClick={(e) => handleDeleteConversation(e, conv.id)}>X</button>
                            </li>
                        ))}
                    </ul>
                </div>
                <div className="chat-window">
                    {chatError && <p className="error-message">{chatError}</p>}
                    <div className="chat-history">
                        {chatHistory.map((msg, index) => (
                            <div key={index} className={`chat-message ${msg.role}`}>
                               <div className="message-bubble">{msg.content}</div>
                            </div>
                        ))}
                         {isGenerating && <div className="loading-message">Thinking...</div>}
                    </div>
                    <form onSubmit={handleChatSubmit}>
                        <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder={selectedModel ? `Chat with ${selectedModel.name}...` : 'Select a model to start chatting'} disabled={!selectedModel || isGenerating} />
                        <button type="submit" disabled={!selectedModel || isGenerating}>Send</button>
                    </form>
                </div>
            </div>
        </div>
    );
}

export default Dashboard;
